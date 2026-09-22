# -*- coding: utf-8 -*-
"""Dialogo que lista as imagens grandes demais e pergunta se devem ser
reduzidas antes de gerar o video.

A lista e a nativa do Windows com caixas de selecao (SysListView32): o Espaco
marca e desmarca, e o leitor de tela anuncia "marcado"/"nao marcado". A
wx.CheckListBox e desenhada pelo wx e nao informa esse estado.
"""
import os

import wx

from core.imagens import (
    CAIXAS_REDUCAO,
    INDICE_REDUCAO_PADRAO,
    LIMITE_IMAGEM_GRANDE,
    ROTULOS_REDUCAO,
    tamanho_reduzido,
)

REDUZIR = wx.ID_YES
MANTER = wx.ID_NO

_COLUNA_NOME, _COLUNA_ATUAL, _COLUNA_FICARA = 0, 1, 2


def _dimensao(tamanho):
    return f"{tamanho[0]} × {tamanho[1]}"


class DialogoImagensGrandes(wx.Dialog):
    """`imagens`: [(caminho, (largura, altura)), ...]."""

    def __init__(self, parent, imagens):
        super().__init__(
            parent,
            title="Imagens muito grandes",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.imagens = imagens
        sizer = wx.BoxSizer(wx.VERTICAL)

        limite = _dimensao(LIMITE_IMAGEM_GRANDE)
        explicacao = wx.StaticText(self, label=(
            f"Estas imagens são maiores que 4K ({limite}) e podem deixar a "
            "geração do vídeo lenta ou esgotar a memória. Marque as que deseja "
            "reduzir (Espaço marca ou desmarca). As imagens originais não são "
            "alteradas: é criada uma cópia reduzida ao lado de cada uma."
        ))
        explicacao.Wrap(560)
        sizer.Add(explicacao, 0, wx.ALL, 10)

        lbl_lista = wx.StaticText(self, label="&Imagens:")
        self.lista = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.lista.EnableCheckBoxes(True)
        self.lista.InsertColumn(_COLUNA_NOME, "Imagem")
        self.lista.InsertColumn(_COLUNA_ATUAL, "Dimensão atual")
        self.lista.InsertColumn(_COLUNA_FICARA, "Ficará com")
        for indice, (caminho, tamanho) in enumerate(imagens):
            self.lista.InsertItem(indice, os.path.basename(caminho))
            self.lista.SetItem(indice, _COLUNA_ATUAL, _dimensao(tamanho))
            self.lista.CheckItem(indice, True)
        sizer.Add(lbl_lista, 0, wx.LEFT | wx.RIGHT, 10)
        sizer.Add(self.lista, 1, wx.EXPAND | wx.ALL, 10)

        linha_tamanho = wx.BoxSizer(wx.HORIZONTAL)
        lbl_tamanho = wx.StaticText(self, label="Reduzir &para:")
        self.escolha_tamanho = wx.Choice(self, choices=ROTULOS_REDUCAO)
        self.escolha_tamanho.SetSelection(INDICE_REDUCAO_PADRAO)
        linha_tamanho.Add(lbl_tamanho, 0, wx.ALL | wx.CENTER, 5)
        linha_tamanho.Add(self.escolha_tamanho, 0, wx.ALL, 5)
        sizer.Add(linha_tamanho, 0, wx.LEFT | wx.RIGHT, 5)

        linha_botoes = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_reduzir = wx.Button(self, REDUZIR, label="&Reduzir as marcadas")
        self.btn_manter = wx.Button(self, MANTER, label="&Manter todas como estão")
        linha_botoes.Add(self.btn_reduzir, 0, wx.ALL, 5)
        linha_botoes.Add(self.btn_manter, 0, wx.ALL, 5)
        sizer.Add(linha_botoes, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.btn_reduzir.SetDefault()
        # Esc ou fechar a janela cancela a geracao do video. (SetEscapeId nao
        # serve aqui: ele so simula o clique num botao Cancelar, que este
        # dialogo nao tem; fechar pela janela ja devolve wx.ID_CANCEL.)
        self.Bind(wx.EVT_CHAR_HOOK, self._ao_teclar)

        self.SetSizerAndFit(sizer)
        self.SetSize((max(self.GetSize()[0], 620), max(self.GetSize()[1], 420)))

        self.btn_reduzir.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(REDUZIR))
        self.btn_manter.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(MANTER))
        self.escolha_tamanho.Bind(wx.EVT_CHOICE, lambda e: self.atualizar_coluna_ficara())
        self.lista.Bind(wx.EVT_LIST_ITEM_CHECKED, lambda e: self.atualizar_coluna_ficara())
        self.lista.Bind(wx.EVT_LIST_ITEM_UNCHECKED, lambda e: self.atualizar_coluna_ficara())

        self.atualizar_coluna_ficara()
        for coluna in (_COLUNA_NOME, _COLUNA_ATUAL, _COLUNA_FICARA):
            self.lista.SetColumnWidth(coluna, wx.LIST_AUTOSIZE_USEHEADER)

        # Foco no primeiro item da lista, para o leitor de tela anuncia-lo.
        if imagens:
            self.lista.Select(0)
            self.lista.Focus(0)
        self.lista.SetFocus()
        self.CentreOnParent()

    def _ao_teclar(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            event.Skip()

    def caixa_escolhida(self):
        return CAIXAS_REDUCAO[self.escolha_tamanho.GetSelection()]

    def caminhos_marcados(self):
        return [
            caminho for indice, (caminho, _) in enumerate(self.imagens)
            if self.lista.IsItemChecked(indice)
        ]

    def atualizar_coluna_ficara(self):
        caixa = self.caixa_escolhida()
        for indice, (_, tamanho) in enumerate(self.imagens):
            if self.lista.IsItemChecked(indice):
                texto = _dimensao(tamanho_reduzido(tamanho, caixa))
            else:
                texto = "sem alteração"
            self.lista.SetItem(indice, _COLUNA_FICARA, texto)


def perguntar_reducao(parent, imagens):
    """Mostra o dialogo. Devolve (caminhos_a_reduzir, caixa) para reduzir,
    ([], None) para manter todas, ou None se a geracao foi cancelada."""
    with DialogoImagensGrandes(parent, imagens) as dialogo:
        resposta = dialogo.ShowModal()
        if resposta == REDUZIR:
            return dialogo.caminhos_marcados(), dialogo.caixa_escolhida()
        if resposta == MANTER:
            return [], None
        return None
