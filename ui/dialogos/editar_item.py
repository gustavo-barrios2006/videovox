# -*- coding: utf-8 -*-
"""Janela de edicao de uma midia (imagem ou video) ou de um audio."""
import os

import wx

from core.opcoes import (
    CHAVES_AJUSTE_IMAGEM,
    ROTULOS_AJUSTE_IMAGEM,
    indice_ajuste_imagem,
)
from core.validacao import validar_numero
from servicos import midias


class EditFrame(wx.Frame):
    """`parent` e a janela principal, bloqueada enquanto a edicao esta aberta.
    `ao_salvar` atualiza a lista correspondente e `lista_foco` recebe o foco
    ao fechar."""

    def __init__(self, parent, item, index, item_type, ao_salvar, lista_foco):
        if item_type == "imagem":
            altura_frame = 460
        elif item_type == "video":
            altura_frame = 500
        else:
            altura_frame = 250
        super().__init__(
            parent,
            title=f"Editar Mídia - {os.path.basename(item['arquivo'])}",
            size=(460, altura_frame),
            style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT
        )
        self.parent = parent
        self.item = item
        self.index = index
        self.item_type = item_type
        self.ao_salvar = ao_salvar
        self.lista_foco = lista_foco

        # Disable main window to block input
        self.parent.Disable()

        # Keyboard bindings
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_char_hook)

        # Panel and Layout
        panel = wx.Panel(self)
        sizer_principal = wx.BoxSizer(wx.VERTICAL)

        grid = wx.FlexGridSizer(cols=2, hgap=10, vgap=10)
        grid.AddGrowableCol(1, 1)

        self.inputs = {}

        if self.item_type == "video":
            fields = [
                ("inicio", "Início no vídeo original (seg):"),
                ("fim", "Fim no vídeo original (seg):"),
                ("inicio_destino", "Início no vídeo destino (seg):")
            ]
        elif self.item_type == "imagem":
            fields = [
                ("duracao", "Duração (segundos):"),
                ("inicio_destino", "Início no vídeo destino (seg):")
            ]
        elif self.item_type == "audio":
            fields = [
                ("inicio", "Início do áudio (seg):"),
                ("fim", "Fim do áudio (seg):"),
                ("pos", "Início no Vídeo (seg):")
            ]

        for key, label_text in fields:
            lbl = wx.StaticText(panel, label=label_text)
            val = self.item.get(key)
            val_str = "" if val is None else str(val)
            txt = wx.TextCtrl(panel, value=val_str)
            grid.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
            grid.Add(txt, 1, wx.EXPAND | wx.ALL, 5)
            self.inputs[key] = txt

        sizer_principal.Add(grid, 1, wx.EXPAND | wx.ALL, 15)

        if self.item_type in ("imagem", "video"):
            rotulo_ajuste = (
                "A&juste da Imagem no quadro"
                if self.item_type == "imagem"
                else "A&juste do Vídeo no quadro"
            )
            self.radio_ajuste = wx.RadioBox(
                panel,
                label=rotulo_ajuste,
                choices=ROTULOS_AJUSTE_IMAGEM,
                majorDimension=2,
                style=wx.RA_SPECIFY_COLS
            )
            ajuste_atual = self.item.get("ajuste_imagem", "preencher")
            self.radio_ajuste.SetSelection(indice_ajuste_imagem(ajuste_atual))
            sizer_principal.Add(
                self.radio_ajuste, 0,
                wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15
            )

        # Buttons
        linha_botoes = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_salvar = wx.Button(panel, label="&Salvar")
        self.btn_cancelar = wx.Button(panel, label="&Cancelar")
        linha_botoes.Add(self.btn_salvar, 0, wx.ALL, 5)
        linha_botoes.Add(self.btn_cancelar, 0, wx.ALL, 5)
        sizer_principal.Add(linha_botoes, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        panel.SetSizer(sizer_principal)

        self.btn_salvar.Bind(wx.EVT_BUTTON, self.on_salvar)
        self.btn_cancelar.Bind(wx.EVT_BUTTON, self.on_cancelar)

        # Focus on the first input field for better accessibility
        if fields:
            self.inputs[fields[0][0]].SetFocus()

        self.CentreOnParent()

    def on_char_hook(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
        else:
            event.Skip()

    def on_cancelar(self, event):
        self.Close()

    def on_close(self, event):
        self.parent.Enable()
        self.parent.Raise()
        # Restore focus to the corresponding list
        self.lista_foco.SetFocus()
        self.Destroy()

    def on_salvar(self, event):
        caminho = self.item["arquivo"]

        if self.item_type == "video":
            inicio_str = self.inputs["inicio"].GetValue().strip()
            fim_str = self.inputs["fim"].GetValue().strip()
            destino_str = self.inputs["inicio_destino"].GetValue().strip()

            if not validar_numero(inicio_str):
                wx.MessageBox("O início do vídeo deve ser um número.", "Erro")
                return

            if fim_str and not validar_numero(fim_str):
                wx.MessageBox("O fim do vídeo deve ser um número ou vazio.", "Erro")
                return

            if destino_str and not validar_numero(destino_str):
                wx.MessageBox("O início no vídeo destino deve ser um número ou vazio.", "Erro")
                return

            inicio = float(inicio_str)
            fim = float(fim_str) if fim_str else None
            inicio_destino = float(destino_str) if destino_str else None

            try:
                duracao_video = midias.duracao_video(caminho)
            except Exception as e:
                wx.MessageBox(f"Não foi possível abrir o vídeo: {e}", "Erro")
                return

            if inicio >= duracao_video:
                wx.MessageBox("O início deve ser menor que a duração do vídeo.", "Erro")
                return

            if inicio < 0:
                wx.MessageBox("O início do vídeo não pode ser negativo.", "Erro")
                return

            if fim is None:
                fim = duracao_video

            if inicio >= fim:
                wx.MessageBox("O início deve ser menor que o fim.", "Erro")
                return

            if fim > duracao_video:
                wx.MessageBox("O fim deve ser menor ou igual à duração do vídeo.", "Erro")
                return

            if inicio_destino is not None and inicio_destino < 0:
                wx.MessageBox("O início no vídeo destino não pode ser negativo.", "Erro")
                return

            self.item["inicio"] = inicio
            self.item["fim"] = fim
            self.item["inicio_destino"] = inicio_destino
            self.item["ajuste_imagem"] = CHAVES_AJUSTE_IMAGEM[
                self.radio_ajuste.GetSelection()
            ]

        elif self.item_type == "imagem":
            tempo = self.inputs["duracao"].GetValue().strip()
            destino_str = self.inputs["inicio_destino"].GetValue().strip()

            if not validar_numero(tempo):
                wx.MessageBox("Informe apenas um número inteiro ou real.", "Erro")
                return

            if destino_str and not validar_numero(destino_str):
                wx.MessageBox("O início no vídeo destino deve ser um número ou vazio.", "Erro")
                return

            duracao = float(tempo)
            inicio_destino = float(destino_str) if destino_str else None

            if duracao <= 0:
                wx.MessageBox("A duração deve ser maior que zero.", "Erro")
                return

            if inicio_destino is not None and inicio_destino < 0:
                wx.MessageBox("O início no vídeo destino não pode ser negativo.", "Erro")
                return

            self.item["duracao"] = duracao
            self.item["inicio_destino"] = inicio_destino
            self.item["ajuste_imagem"] = CHAVES_AJUSTE_IMAGEM[
                self.radio_ajuste.GetSelection()
            ]

        elif self.item_type == "audio":
            inicio_audio_str = self.inputs["inicio"].GetValue().strip()
            fim_audio_str = self.inputs["fim"].GetValue().strip()
            pos_video_str = self.inputs["pos"].GetValue().strip()

            if not validar_numero(inicio_audio_str):
                wx.MessageBox("Início do Áudio deve ser um número.", "Erro")
                return
            if fim_audio_str and not validar_numero(fim_audio_str):
                wx.MessageBox("Fim do Áudio deve ser um número ou vazio.", "Erro")
                return
            if pos_video_str and not validar_numero(pos_video_str):
                wx.MessageBox("Início no vídeo deve ser um número ou vazio.", "Erro")
                return

            inicio = float(inicio_audio_str)
            fim = float(fim_audio_str) if fim_audio_str else None
            pos = float(pos_video_str) if pos_video_str else None

            if pos is not None and pos < 0:
                wx.MessageBox("O início no vídeo não pode ser negativo.", "Erro")
                return

            if fim is not None and inicio >= fim:
                wx.MessageBox("O início do áudio deve ser menor que o fim.", "Erro")
                return

            self.item["inicio"] = inicio
            self.item["fim"] = fim
            self.item["pos"] = pos

        # Update visual representation
        self.ao_salvar()

        self.Close()
