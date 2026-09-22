# -*- coding: utf-8 -*-
"""Secao "Configurações de Áudio (Mixagem)" da aba Criar Videoclipe."""
import os

import wx

from core.linha_do_tempo import descrever_audios
from core.validacao import validar_numero
from servicos import midias
from ui.dialogos.editar_item import EditFrame


class SecaoAudios:
    """Cria os controles no proprio painel da aba (e nao num subpainel), para
    manter a mesma ordem de tabulacao da aba inteira."""

    def __init__(self, janela, painel, estado):
        self.janela = janela
        self.painel = painel
        self.estado = estado

    def criar_controles(self, sizer_principal):
        painel = self.painel

        box_audio = wx.StaticBox(painel, label="&Configurações de Áudio (Mixagem)")
        sizer_audio = wx.StaticBoxSizer(box_audio, wx.VERTICAL)

        # 1. Campo de edicao com o caminho do Áudio
        linha_arq_audio = wx.BoxSizer(wx.HORIZONTAL)
        lbl_audio_path = wx.StaticText(painel, label="Caminho do &Áudio:")
        self.txt_audio = wx.TextCtrl(painel)
        linha_arq_audio.Add(lbl_audio_path, 0, wx.ALL | wx.CENTER, 5)
        linha_arq_audio.Add(self.txt_audio, 1, wx.EXPAND | wx.ALL, 5)

        # 2. Botao selecionar Áudio
        self.btn_procurar_audio = wx.Button(painel, label="Selecionar Á&udio")
        linha_arq_audio.Add(self.btn_procurar_audio, 0, wx.ALL, 5)
        sizer_audio.Add(linha_arq_audio, 0, wx.EXPAND)

        # 3. Campos: inicio e fim do Áudio, inicio no video
        linha_audio_tempos = wx.BoxSizer(wx.HORIZONTAL)
        lbl_audio_inicio = wx.StaticText(painel, label="&Início do Áudio (seg):")
        self.txt_audio_inicio = wx.TextCtrl(painel, value="0")
        lbl_audio_fim = wx.StaticText(painel, label="&Fim do Áudio (seg):")
        self.txt_audio_fim = wx.TextCtrl(painel, value="")
        lbl_video_pos = wx.StaticText(painel, label="Início no &Vídeo (seg):")
        self.txt_video_pos = wx.TextCtrl(painel, value="")

        linha_audio_tempos.Add(lbl_audio_inicio, 0, wx.ALL | wx.CENTER, 5)
        linha_audio_tempos.Add(self.txt_audio_inicio, 1, wx.ALL, 5)
        linha_audio_tempos.Add(lbl_audio_fim, 0, wx.ALL | wx.CENTER, 5)
        linha_audio_tempos.Add(self.txt_audio_fim, 1, wx.ALL, 5)
        linha_audio_tempos.Add(lbl_video_pos, 0, wx.ALL | wx.CENTER, 5)
        linha_audio_tempos.Add(self.txt_video_pos, 1, wx.ALL, 5)
        sizer_audio.Add(linha_audio_tempos, 0, wx.EXPAND)

        # 4. Botao de adicionar Áudio
        self.btn_add_audio = wx.Button(painel, label="&Adicionar Áudio à Lista")
        sizer_audio.Add(self.btn_add_audio, 0, wx.ALL | wx.CENTER, 5)

        # 5. Lista de Áudios
        lbl_lista_audio = wx.StaticText(painel, label="&Lista de Áudios para Mixar:")
        self.lista_audio = wx.ListBox(painel)
        sizer_audio.Add(lbl_lista_audio, 0, wx.ALL, 5)
        sizer_audio.Add(self.lista_audio, 1, wx.EXPAND | wx.ALL, 5)

        # 6. Botoes de remover e editar Áudio
        linha_botoes_audio = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_remover_audio = wx.Button(painel, label="Remover Áu&dio")
        self.btn_editar_audio = wx.Button(painel, label="Ed&itar Áudio")
        linha_botoes_audio.Add(self.btn_remover_audio, 0, wx.ALL, 5)
        linha_botoes_audio.Add(self.btn_editar_audio, 0, wx.ALL, 5)
        sizer_audio.Add(linha_botoes_audio, 0, wx.ALL | wx.CENTER, 5)

        sizer_principal.Add(sizer_audio, 1, wx.EXPAND | wx.ALL, 5)

    def vincular_eventos(self):
        self.btn_procurar_audio.Bind(wx.EVT_BUTTON, self.on_procurar_audio)
        self.btn_add_audio.Bind(wx.EVT_BUTTON, self.on_adicionar_audio)
        self.btn_remover_audio.Bind(wx.EVT_BUTTON, self.on_remover_audio)
        self.btn_editar_audio.Bind(wx.EVT_BUTTON, self.on_editar_audio)

    def atualizar_lista_audios(self):
        self.lista_audio.Clear()
        for descricao in descrever_audios(
            self.estado.audios, midias.obter_duracao_recorte_audio
        ):
            self.lista_audio.Append(descricao)

    def on_editar_audio(self, event):
        indice = self.lista_audio.GetSelection()
        if indice == wx.NOT_FOUND:
            wx.MessageBox("Selecione um áudio na lista para editar.", "Aviso")
            return

        item = self.estado.audios[indice]
        frame_edicao = EditFrame(
            self.janela, item, indice, "audio",
            ao_salvar=self.atualizar_lista_audios,
            lista_foco=self.lista_audio
        )
        frame_edicao.Show()

    def on_remover_audio(self, event):
        indice = self.lista_audio.GetSelection()
        if indice != wx.NOT_FOUND:
            del self.estado.audios[indice]
            self.lista_audio.Delete(indice)

    def on_procurar_audio(self, event):
        with wx.FileDialog(
            self.janela,
            "Escolha o Áudio",
            wildcard="Áudio (*.mp3;*.wav;*.aac)|*.mp3;*.wav;*.aac",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.txt_audio.SetValue(dlg.GetPath())

    def on_adicionar_audio(self, event):
        caminho = self.txt_audio.GetValue().strip()
        inicio_audio_str = self.txt_audio_inicio.GetValue().strip()
        fim_audio_str = self.txt_audio_fim.GetValue().strip()
        pos_video_str = self.txt_video_pos.GetValue().strip()

        if not caminho:
            wx.MessageBox("Selecione ou cole o caminho do Áudio.", "Erro")
            return

        if not os.path.exists(caminho):
            wx.MessageBox("O arquivo de Áudio não existe.", "Erro")
            return

        if not validar_numero(inicio_audio_str):
            wx.MessageBox("Início do Áudio deve ser um número.", "Erro")
            return
        if fim_audio_str and not validar_numero(fim_audio_str):
            wx.MessageBox("Fim do Áudio deve ser um número ou vazio.", "Erro")
            return
        if pos_video_str and not validar_numero(pos_video_str):
            wx.MessageBox("Início no vídeo deve ser um número ou vazio.", "Erro")
            return

        pos_video = float(pos_video_str) if pos_video_str else None

        if pos_video is not None and pos_video < 0:
            wx.MessageBox("O início no vídeo não pode ser negativo.", "Erro")
            return

        try:
            duracao_original = midias.duracao_audio(caminho)
        except Exception as e:
            wx.MessageBox(f"Não foi possível abrir o áudio: {e}", "Erro")
            return

        info = {
            "arquivo": caminho,
            "inicio": float(inicio_audio_str),
            "fim": float(fim_audio_str) if fim_audio_str else None,
            "pos": pos_video,
            "duracao_original": duracao_original
        }

        self.estado.audios.append(info)
        self.atualizar_lista_audios()

        # Limpar campos apos adicionar
        self.txt_audio.Clear()
        self.txt_audio_inicio.SetValue("0")
        self.txt_audio_fim.Clear()
        self.txt_video_pos.Clear()
