# -*- coding: utf-8 -*-
"""Aba "Editar Vídeo": remove trechos de um video existente."""
import wx

from core.opcoes import PRESETS_QUALIDADE
from core.validacao import validar_numero
from servicos.cortes import processar_cortes
from ui.tarefas import executar_em_segundo_plano


class AbaEditar(wx.Panel):

    def __init__(self, notebook, janela):
        super().__init__(notebook)
        self.janela = janela
        self.video_para_editar = None
        self.cortes = []
        self.criar_controles()

    def criar_controles(self):
        painel = self
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Selecao de Video
        linha_arq = wx.BoxSizer(wx.HORIZONTAL)
        lbl_video = wx.StaticText(painel, label="&Vídeo para Editar:")
        self.txt_video_editar = wx.TextCtrl(painel, style=wx.TE_READONLY)
        self.btn_abrir_video = wx.Button(painel, label="&Abrir Vídeo")
        linha_arq.Add(lbl_video, 0, wx.ALL | wx.CENTER, 5)
        linha_arq.Add(self.txt_video_editar, 1, wx.EXPAND | wx.ALL, 5)
        linha_arq.Add(self.btn_abrir_video, 0, wx.ALL, 5)
        sizer.Add(linha_arq, 0, wx.EXPAND)

        # Controles de Corte
        box_corte = wx.StaticBox(painel, label="Definir Pedaço para Remover")
        sizer_corte = wx.StaticBoxSizer(box_corte, wx.VERTICAL)

        linha_tempos = wx.BoxSizer(wx.HORIZONTAL)
        lbl_inicio = wx.StaticText(painel, label="&Início (seg):")
        self.txt_inicio_corte = wx.TextCtrl(painel)
        lbl_fim = wx.StaticText(painel, label="&Fim (seg):")
        self.txt_fim_corte = wx.TextCtrl(painel)
        self.btn_add_corte = wx.Button(painel, label="Adicionar &Corte")

        linha_tempos.Add(lbl_inicio, 0, wx.ALL | wx.CENTER, 5)
        linha_tempos.Add(self.txt_inicio_corte, 1, wx.ALL, 5)
        linha_tempos.Add(lbl_fim, 0, wx.ALL | wx.CENTER, 5)
        linha_tempos.Add(self.txt_fim_corte, 1, wx.ALL, 5)
        linha_tempos.Add(self.btn_add_corte, 0, wx.ALL, 5)
        sizer_corte.Add(linha_tempos, 0, wx.EXPAND)

        sizer.Add(sizer_corte, 0, wx.EXPAND | wx.ALL, 5)

        # Lista de Cortes
        lbl_lista_cortes = wx.StaticText(painel, label="Cortes a serem &Removidos:")
        self.lista_cortes = wx.ListBox(painel)
        sizer.Add(lbl_lista_cortes, 0, wx.ALL, 5)
        sizer.Add(self.lista_cortes, 1, wx.EXPAND | wx.ALL, 5)

        # Configuracoes de Qualidade
        linha_qualidade = wx.BoxSizer(wx.HORIZONTAL)
        lbl_qualidade = wx.StaticText(painel, label="&Qualidade:")
        self.choice_qualidade = wx.Choice(painel, choices=["Alta (Lento / Arquivo Menor)", "Média", "Baixa (Rápido / Arquivo Maior)"])
        self.choice_qualidade.SetSelection(1) # Media por padrao
        linha_qualidade.Add(lbl_qualidade, 0, wx.ALL | wx.CENTER, 5)
        linha_qualidade.Add(self.choice_qualidade, 1, wx.ALL, 5)
        sizer.Add(linha_qualidade, 0, wx.EXPAND)

        # Acoes
        linha_acoes = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_remover_corte = wx.Button(painel, label="&Excluir Corte Selecionado")
        self.btn_processar_cortes = wx.Button(painel, label="&Processar e Salvar")
        linha_acoes.Add(self.btn_remover_corte, 0, wx.ALL, 5)
        linha_acoes.Add(self.btn_processar_cortes, 0, wx.ALL, 5)
        sizer.Add(linha_acoes, 0, wx.CENTER)

        painel.SetSizer(sizer)

        # Binds
        self.btn_abrir_video.Bind(wx.EVT_BUTTON, self.on_abrir_video_editar)
        self.btn_add_corte.Bind(wx.EVT_BUTTON, self.on_adicionar_corte)
        self.btn_remover_corte.Bind(wx.EVT_BUTTON, self.on_remover_corte)
        self.btn_processar_cortes.Bind(wx.EVT_BUTTON, self.on_processar_cortes)

    def on_abrir_video_editar(self, event):
        with wx.FileDialog(
            self.janela,
            "Selecione um vídeo",
            wildcard="Vídeos (*.mp4;*.avi;*.mkv;*.mov)|*.mp4;*.avi;*.mkv;*.mov",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                caminho = dlg.GetPath()
                self.txt_video_editar.SetValue(caminho)
                self.video_para_editar = caminho
                self.cortes = []
                self.lista_cortes.Clear()

    def on_adicionar_corte(self, event):
        if not self.video_para_editar:
            wx.MessageBox("Abra um vídeo primeiro.", "Erro")
            return

        inicio_str = self.txt_inicio_corte.GetValue().strip()
        fim_str = self.txt_fim_corte.GetValue().strip()

        if not validar_numero(inicio_str) or not validar_numero(fim_str):
            wx.MessageBox("Informe tempos válidos (números).", "Erro")
            return

        inicio = float(inicio_str)
        fim = float(fim_str)

        if inicio >= fim:
            wx.MessageBox("O início deve ser menor que o fim.", "Erro")
            return

        self.cortes.append((inicio, fim))
        self.lista_cortes.Append(f"Remover de {inicio}s até {fim}s")
        self.txt_inicio_corte.Clear()
        self.txt_fim_corte.Clear()

    def on_remover_corte(self, event):
        indice = self.lista_cortes.GetSelection()
        if indice != wx.NOT_FOUND:
            del self.cortes[indice]
            self.lista_cortes.Delete(indice)

    def on_processar_cortes(self, event):
        if not self.video_para_editar:
            wx.MessageBox("Nenhum vídeo selecionado.", "Erro")
            return

        qualidade_idx = self.choice_qualidade.GetSelection()
        preset_escolhido = PRESETS_QUALIDADE[qualidade_idx]

        with wx.FileDialog(
            self.janela,
            "Salvar vídeo editado",
            wildcard="MP4 (*.mp4)|*.mp4",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            destino = dlg.GetPath()

        # Desabilitar botao para evitar cliques duplos
        self.btn_processar_cortes.Disable()
        wx.BeginBusyCursor()

        video_para_editar = self.video_para_editar
        cortes = self.cortes

        def processar():
            try:
                if not processar_cortes(
                    video_para_editar, cortes, destino, preset_escolhido
                ):
                    wx.CallAfter(wx.MessageBox, "O vídeo resultante ficaria vazio!", "Erro")
                    return

                wx.CallAfter(self.finalizar_processamento, True, "Vídeo processado com sucesso.")

            except Exception as e:
                wx.CallAfter(self.finalizar_processamento, False, str(e))

        executar_em_segundo_plano(processar)

    def finalizar_processamento(self, sucesso, mensagem):
        if wx.IsBusy():
            wx.EndBusyCursor()
        self.btn_processar_cortes.Enable()

        if sucesso:
            wx.MessageBox(mensagem, "Sucesso")
        else:
            wx.MessageBox(f"Erro ao processar: {mensagem}", "Erro")
