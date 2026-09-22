# -*- coding: utf-8 -*-
"""Aba "Criar Videoclipe": lista de midias, audios para mixar e geracao do
video base e do video final."""
import os

import wx

from core.linha_do_tempo import descrever_midias
from core.opcoes import (
    CHAVES_AJUSTE_IMAGEM,
    CHAVES_TAMANHO_QUADRO,
    ROTULOS_AJUSTE_IMAGEM,
    ROTULOS_TAMANHO_QUADRO,
)
from core.validacao import validar_numero
from infra.log import mensagem_com_registro, registrar_erro
from servicos import midias
from servicos.mixagem import gerar_video_final
from servicos.renderizacao import criar_video
from ui.abas.secao_audios import SecaoAudios
from ui.dialogos.editar_item import EditFrame
from ui.tarefas import executar_em_segundo_plano


class AbaCriar(wx.Panel):
    """`janela` e a janela principal: dona do estado do projeto e das acoes
    de salvar/carregar projeto (que tambem ficam no menu)."""

    def __init__(self, notebook, janela, estado):
        super().__init__(notebook)
        self.janela = janela
        self.estado = estado
        self.secao_audios = SecaoAudios(janela, self, estado)
        self.criar_controles()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def criar_controles(self):
        painel = self
        sizer_principal = wx.BoxSizer(wx.VERTICAL)

        # --- Secao de Imagens ---
        linha_img = wx.BoxSizer(wx.HORIZONTAL)
        lbl_img = wx.StaticText(painel, label="&Caminho da Imagem:")
        self.txt_imagem = wx.TextCtrl(painel)
        linha_img.Add(lbl_img, 0, wx.ALL | wx.CENTER, 5)
        linha_img.Add(self.txt_imagem, 1, wx.EXPAND | wx.ALL, 5)

        self.btn_procurar = wx.Button(painel, label="&Selecionar Imagem")
        linha_img.Add(self.btn_procurar, 0, wx.ALL, 5)
        sizer_principal.Add(linha_img, 0, wx.EXPAND)

        linha_tempo = wx.BoxSizer(wx.HORIZONTAL)
        lbl_tempo = wx.StaticText(painel, label="&Duração (segundos):")
        self.txt_tempo = wx.TextCtrl(painel)
        lbl_imagem_destino = wx.StaticText(painel, label="Início no vídeo destino (seg):")
        self.txt_imagem_destino = wx.TextCtrl(painel)
        linha_tempo.Add(lbl_tempo, 0, wx.ALL | wx.CENTER, 5)
        linha_tempo.Add(self.txt_tempo, 1, wx.ALL, 5)
        linha_tempo.Add(lbl_imagem_destino, 0, wx.ALL | wx.CENTER, 5)
        linha_tempo.Add(self.txt_imagem_destino, 1, wx.ALL, 5)

        self.btn_adicionar = wx.Button(painel, label="&Adicionar à Lista")
        linha_tempo.Add(self.btn_adicionar, 0, wx.ALL, 5)
        sizer_principal.Add(linha_tempo, 0, wx.EXPAND)

        self.radio_ajuste_imagem = wx.RadioBox(
            painel,
            label="A&juste da Imagem no quadro",
            choices=ROTULOS_AJUSTE_IMAGEM,
            majorDimension=5,
            style=wx.RA_SPECIFY_COLS
        )
        self.radio_ajuste_imagem.SetSelection(0)
        # Coloca o ajuste na ordem de tabulacao antes do botao "Adicionar a
        # Lista", para que faca parte das configuracoes daquela midia.
        self.radio_ajuste_imagem.MoveBeforeInTabOrder(self.btn_adicionar)
        sizer_principal.Add(self.radio_ajuste_imagem, 0, wx.EXPAND | wx.ALL, 5)

        # --- Secao de Videos ---
        linha_video = wx.BoxSizer(wx.HORIZONTAL)
        lbl_video_fluxo = wx.StaticText(painel, label="Caminho do &Vídeo:")
        self.txt_video_fluxo = wx.TextCtrl(painel)
        linha_video.Add(lbl_video_fluxo, 0, wx.ALL | wx.CENTER, 5)
        linha_video.Add(self.txt_video_fluxo, 1, wx.EXPAND | wx.ALL, 5)

        self.btn_procurar_video_fluxo = wx.Button(painel, label="Selecionar Ví&deo")
        linha_video.Add(self.btn_procurar_video_fluxo, 0, wx.ALL, 5)
        sizer_principal.Add(linha_video, 0, wx.EXPAND)

        linha_video_tempos = wx.BoxSizer(wx.HORIZONTAL)
        lbl_video_inicio_fluxo = wx.StaticText(painel, label="Início no vídeo original (seg):")
        self.txt_video_inicio_fluxo = wx.TextCtrl(painel, value="0")
        lbl_video_fim_fluxo = wx.StaticText(painel, label="Fim no vídeo original (seg):")
        self.txt_video_fim_fluxo = wx.TextCtrl(painel)
        lbl_video_destino_fluxo = wx.StaticText(painel, label="Início no vídeo destino (seg):")
        self.txt_video_destino_fluxo = wx.TextCtrl(painel)

        linha_video_tempos.Add(lbl_video_inicio_fluxo, 0, wx.ALL | wx.CENTER, 5)
        linha_video_tempos.Add(self.txt_video_inicio_fluxo, 1, wx.ALL, 5)
        linha_video_tempos.Add(lbl_video_fim_fluxo, 0, wx.ALL | wx.CENTER, 5)
        linha_video_tempos.Add(self.txt_video_fim_fluxo, 1, wx.ALL, 5)
        linha_video_tempos.Add(lbl_video_destino_fluxo, 0, wx.ALL | wx.CENTER, 5)
        linha_video_tempos.Add(self.txt_video_destino_fluxo, 1, wx.ALL, 5)

        self.btn_adicionar_video_fluxo = wx.Button(painel, label="Adicionar Vídeo à Lista")
        linha_video_tempos.Add(self.btn_adicionar_video_fluxo, 0, wx.ALL, 5)
        sizer_principal.Add(linha_video_tempos, 0, wx.EXPAND)

        self.radio_ajuste_video = wx.RadioBox(
            painel,
            label="Ajuste do Víde&o no quadro",
            choices=ROTULOS_AJUSTE_IMAGEM,
            majorDimension=5,
            style=wx.RA_SPECIFY_COLS
        )
        self.radio_ajuste_video.SetSelection(0)
        # Coloca o ajuste na ordem de tabulacao antes do botao "Adicionar Video
        # a Lista", para que faca parte das configuracoes daquela midia.
        self.radio_ajuste_video.MoveBeforeInTabOrder(self.btn_adicionar_video_fluxo)
        sizer_principal.Add(self.radio_ajuste_video, 0, wx.EXPAND | wx.ALL, 5)

        lbl_lista = wx.StaticText(painel, label="&Lista de Mídias:")
        self.lista = wx.ListBox(painel)
        sizer_principal.Add(lbl_lista, 0, wx.ALL, 5)
        sizer_principal.Add(self.lista, 1, wx.EXPAND | wx.ALL, 5)

        linha_botoes_midia = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_remover = wx.Button(painel, label="&Remover Mídia")
        self.btn_editar = wx.Button(painel, label="&Editar Mídia")
        self.btn_silenciar = wx.Button(painel, label="&Silenciar Vídeo")
        self.btn_silenciar.Hide()
        linha_botoes_midia.Add(self.btn_remover, 0, wx.ALL, 5)
        linha_botoes_midia.Add(self.btn_editar, 0, wx.ALL, 5)
        linha_botoes_midia.Add(self.btn_silenciar, 0, wx.ALL, 5)
        sizer_principal.Add(linha_botoes_midia, 0, wx.ALL | wx.CENTER, 5)

        linha_fps = wx.BoxSizer(wx.HORIZONTAL)
        lbl_fps = wx.StaticText(painel, label="&FPS do Vídeo Final:")
        self.txt_fps = wx.TextCtrl(painel, value="30", size=(50, -1))
        linha_fps.Add(lbl_fps, 0, wx.ALL | wx.CENTER, 5)
        linha_fps.Add(self.txt_fps, 0, wx.ALL, 5)
        sizer_principal.Add(linha_fps, 0, wx.CENTER)

        # --- Secao de Áudio ---
        self.secao_audios.criar_controles(sizer_principal)

        # --- Tamanho do quadro do vídeo final ---
        linha_tamanho_quadro = wx.BoxSizer(wx.HORIZONTAL)
        lbl_tamanho_quadro = wx.StaticText(painel, label="Tamanho do &Quadro:")
        self.combo_tamanho_quadro = wx.Choice(
            painel,
            choices=ROTULOS_TAMANHO_QUADRO
        )
        self.combo_tamanho_quadro.SetSelection(0)
        linha_tamanho_quadro.Add(lbl_tamanho_quadro, 0, wx.ALL | wx.CENTER, 5)
        linha_tamanho_quadro.Add(self.combo_tamanho_quadro, 0, wx.ALL, 5)
        sizer_principal.Add(linha_tamanho_quadro, 0, wx.CENTER)

        # --- Ações Finais ---
        linha_final = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_carregar_projeto = wx.Button(painel, label="Carregar &Projeto")
        self.btn_salvar_projeto = wx.Button(painel, label="Salvar P&rojeto")
        self.btn_salvar_video = wx.Button(painel, label="&Salvar Vídeo Base")
        self.btn_gerar_final = wx.Button(painel, label="Gerar Vídeo &Final (Com Áudios)")
        linha_final.Add(self.btn_carregar_projeto, 0, wx.ALL, 5)
        linha_final.Add(self.btn_salvar_projeto, 0, wx.ALL, 5)
        linha_final.Add(self.btn_salvar_video, 0, wx.ALL, 5)
        linha_final.Add(self.btn_gerar_final, 0, wx.ALL, 5)
        sizer_principal.Add(linha_final, 0, wx.CENTER)

        # Coloca a selecao de tamanho do quadro na ordem de tabulacao logo antes
        # do botao "Gerar Vídeo Final", logo apos o grupo de áudio.
        self.combo_tamanho_quadro.MoveBeforeInTabOrder(self.btn_salvar_video)

        painel.SetSizer(sizer_principal)

        # Binds
        self.btn_procurar.Bind(wx.EVT_BUTTON, self.on_procurar_imagem)
        self.btn_adicionar.Bind(wx.EVT_BUTTON, self.on_adicionar)
        self.btn_procurar_video_fluxo.Bind(wx.EVT_BUTTON, self.on_procurar_video_fluxo)
        self.btn_adicionar_video_fluxo.Bind(wx.EVT_BUTTON, self.on_adicionar_video_fluxo)
        self.btn_remover.Bind(wx.EVT_BUTTON, self.on_remover)
        self.btn_editar.Bind(wx.EVT_BUTTON, self.on_editar_midia)
        self.btn_silenciar.Bind(wx.EVT_BUTTON, self.on_silenciar_video)
        self.lista.Bind(wx.EVT_LISTBOX, self.on_lista_select)
        self.secao_audios.vincular_eventos()
        self.btn_carregar_projeto.Bind(wx.EVT_BUTTON, self.janela.on_carregar_projeto)
        self.btn_salvar_projeto.Bind(wx.EVT_BUTTON, self.janela.on_salvar_projeto)
        self.btn_salvar_video.Bind(wx.EVT_BUTTON, self.on_salvar_video)
        self.btn_gerar_final.Bind(wx.EVT_BUTTON, self.on_gerar_video_final)

    # ------------------------------------------------------------------
    # Acesso usado pela janela principal (salvar/carregar projeto)
    # ------------------------------------------------------------------

    def bloquear_acoes(self):
        self.btn_salvar_video.Disable()
        self.btn_gerar_final.Disable()
        self.btn_salvar_projeto.Disable()
        self.btn_carregar_projeto.Disable()
        wx.BeginBusyCursor()

    def liberar_acoes(self):
        if wx.IsBusy():
            wx.EndBusyCursor()

        self.btn_salvar_video.Enable()
        self.btn_gerar_final.Enable()
        self.btn_salvar_projeto.Enable()
        self.btn_carregar_projeto.Enable()

    def obter_fps_texto(self):
        return self.txt_fps.GetValue().strip()

    def obter_tamanho_quadro(self):
        return CHAVES_TAMANHO_QUADRO[self.combo_tamanho_quadro.GetSelection()]

    def aplicar_configuracoes(self, fps_texto, indice_quadro):
        self.txt_fps.SetValue(fps_texto)
        self.combo_tamanho_quadro.SetSelection(indice_quadro)

    def atualizar_listas(self):
        self.atualizar_lista_midias()
        self.secao_audios.atualizar_lista_audios()
        self.atualizar_estado_botoes()

    # ------------------------------------------------------------------
    # Lista de midias
    # ------------------------------------------------------------------

    def on_editar_midia(self, event):
        indice = self.lista.GetSelection()
        if indice == wx.NOT_FOUND:
            wx.MessageBox("Selecione uma mídia na lista para editar.", "Aviso")
            return

        item = self.estado.imagens[indice]
        frame_edicao = EditFrame(
            self.janela, item, indice, item["tipo"],
            ao_salvar=self.atualizar_lista_midias,
            lista_foco=self.lista
        )
        frame_edicao.Show()

    def on_procurar_imagem(self, event):

        with wx.FileDialog(
            self.janela,
            "Selecione uma imagem",
            wildcard=(
                "Imagens (*.jpg;*.jpeg;*.png;*.bmp)|"
                "*.jpg;*.jpeg;*.png;*.bmp"
            ),
            style=wx.FD_OPEN
        ) as dlg:

            if dlg.ShowModal() == wx.ID_OK:
                self.txt_imagem.SetValue(
                    dlg.GetPath()
                )

    def on_procurar_video_fluxo(self, event):
        with wx.FileDialog(
            self.janela,
            "Selecione um vídeo",
            wildcard="Vídeos (*.mp4;*.avi;*.mkv;*.mov)|*.mp4;*.avi;*.mkv;*.mov",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.txt_video_fluxo.SetValue(dlg.GetPath())

    def on_adicionar(self, event):

        caminho = self.txt_imagem.GetValue().strip()
        tempo = self.txt_tempo.GetValue().strip()
        destino_str = self.txt_imagem_destino.GetValue().strip()

        if not caminho:
            wx.MessageBox(
                "Selecione uma imagem.",
                "Erro"
            )
            return

        if not os.path.exists(caminho):
            wx.MessageBox(
                "Arquivo inexistente.",
                "Erro"
            )
            return

        if not validar_numero(tempo):
            wx.MessageBox(
                "Informe apenas um número inteiro ou real.",
                "Erro"
            )
            return

        if destino_str and not validar_numero(destino_str):
            wx.MessageBox(
                "O início no vídeo destino deve ser um número ou vazio.",
                "Erro"
            )
            return

        duracao = float(tempo)
        inicio_destino = float(destino_str) if destino_str else None

        if duracao <= 0:
            wx.MessageBox(
                "A duração deve ser maior que zero.",
                "Erro"
            )
            return

        if inicio_destino is not None and inicio_destino < 0:
            wx.MessageBox(
                "O início no vídeo destino não pode ser negativo.",
                "Erro"
            )
            return

        ajuste_imagem = CHAVES_AJUSTE_IMAGEM[self.radio_ajuste_imagem.GetSelection()]

        self.estado.imagens.append(
            {
                "tipo": "imagem",
                "arquivo": caminho,
                "duracao": duracao,
                "inicio_destino": inicio_destino,
                "ajuste_imagem": ajuste_imagem
            }
        )

        self.atualizar_lista_midias()

        self.txt_imagem.Clear()
        self.txt_tempo.Clear()
        self.txt_imagem_destino.Clear()
        self.radio_ajuste_imagem.SetSelection(0)

    def on_adicionar_video_fluxo(self, event):
        caminho = self.txt_video_fluxo.GetValue().strip()
        inicio_str = self.txt_video_inicio_fluxo.GetValue().strip()
        fim_str = self.txt_video_fim_fluxo.GetValue().strip()
        destino_str = self.txt_video_destino_fluxo.GetValue().strip()

        if not caminho:
            wx.MessageBox("Selecione um vídeo.", "Erro")
            return

        if not os.path.exists(caminho):
            wx.MessageBox("Arquivo inexistente.", "Erro")
            return

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

        ajuste_video = CHAVES_AJUSTE_IMAGEM[self.radio_ajuste_video.GetSelection()]

        self.estado.imagens.append(
            {
                "tipo": "video",
                "arquivo": caminho,
                "inicio": inicio,
                "fim": fim,
                "inicio_destino": inicio_destino,
                "ajuste_imagem": ajuste_video
            }
        )

        self.atualizar_lista_midias()

        self.txt_video_fluxo.Clear()
        self.txt_video_inicio_fluxo.SetValue("0")
        self.txt_video_fim_fluxo.Clear()
        self.txt_video_destino_fluxo.Clear()
        self.radio_ajuste_video.SetSelection(0)

    def on_remover(self, event):

        indice = self.lista.GetSelection()

        if indice == wx.NOT_FOUND:
            return

        del self.estado.imagens[indice]

        self.atualizar_lista_midias()

    def atualizar_lista_midias(self):
        self.lista.Clear()

        for descricao in descrever_midias(self.estado.imagens):
            self.lista.Append(descricao)

        self.atualizar_estado_botoes()

    def on_lista_select(self, event):
        self.atualizar_estado_botoes()

    def on_silenciar_video(self, event):
        indice = self.lista.GetSelection()
        if indice == wx.NOT_FOUND:
            return
        item = self.estado.imagens[indice]
        if item.get("tipo", "imagem") == "video":
            item["silenciado"] = not item.get("silenciado", False)
            self.atualizar_lista_midias()
            self.lista.SetSelection(indice)
            self.atualizar_estado_botoes()

    def atualizar_estado_botoes(self):
        indice = self.lista.GetSelection()
        if indice == wx.NOT_FOUND:
            self.btn_silenciar.Hide()
        else:
            item = self.estado.imagens[indice]
            if item.get("tipo", "imagem") == "video":
                if item.get("silenciado"):
                    self.btn_silenciar.SetLabel("&Voltar Áudio")
                else:
                    self.btn_silenciar.SetLabel("&Silenciar Vídeo")
                self.btn_silenciar.Show()
            else:
                self.btn_silenciar.Hide()
        self.Layout()

    # ------------------------------------------------------------------
    # Salvar video base
    # ------------------------------------------------------------------

    def on_salvar_video(self, event):

        if not self.estado.imagens:

            wx.MessageBox(
                "Nenhuma mídia adicionada.",
                "Erro"
            )

            return

        with wx.FileDialog(
            self.janela,
            "Salvar vídeo",
            wildcard="MP4 (*.mp4)|*.mp4",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dlg:

            if dlg.ShowModal() != wx.ID_OK:
                return

            destino = dlg.GetPath()

        try:
            fps_valor = int(self.txt_fps.GetValue().strip())
            if fps_valor <= 0:
                fps_valor = 30
        except:
            fps_valor = 30

        imagens = [item.copy() for item in self.estado.imagens]

        # Captura na thread principal (wx nao e thread-safe): modo do quadro
        # repassado para a geracao em segundo plano.
        modo_quadro = CHAVES_TAMANHO_QUADRO[
            self.combo_tamanho_quadro.GetSelection()
        ]

        self.bloquear_acoes()

        def salvar():
            try:
                criar_video(
                    destino,
                    imagens,
                    fps_valor,
                    modo_quadro
                )
                wx.CallAfter(
                    self.finalizar_salvar_video,
                    True,
                    destino,
                    "Vídeo criado com sucesso."
                )
            except Exception as e:
                registro = registrar_erro("Salvar vídeo base")
                wx.CallAfter(
                    self.finalizar_salvar_video,
                    False,
                    None,
                    mensagem_com_registro(str(e), registro)
                )

        executar_em_segundo_plano(salvar)

    def finalizar_salvar_video(self, sucesso, destino, mensagem):
        self.liberar_acoes()

        if sucesso:
            self.estado.video_atual = destino
            wx.MessageBox(mensagem, "Sucesso")
        else:
            wx.MessageBox(mensagem, "Erro")

    # ------------------------------------------------------------------
    # Gerar video final (mixagem dos audios)
    # ------------------------------------------------------------------

    def on_gerar_video_final(self, event):
        if not self.estado.video_atual:
            wx.MessageBox("Salve um vídeo sem as mixagens primeiro.", "Erro")
            return

        if not self.estado.audios:
            wx.MessageBox("Adicione pelo menos um Áudio à lista.", "Erro")
            return

        with wx.FileDialog(
            self.janela,
            "Salvar vídeo final",
            wildcard="MP4 (*.mp4)|*.mp4",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            destino = dlg.GetPath()

        self.bloquear_acoes()

        video_atual = self.estado.video_atual
        audios = [item.copy() for item in self.estado.audios]

        def gerar():
            try:
                gerar_video_final(video_atual, audios, destino)

                wx.CallAfter(self.finalizar_gerar_video, True, "Vídeo final com mixagem concluído!")

            except Exception as e:
                registro = registrar_erro("Gerar vídeo final")
                wx.CallAfter(
                    self.finalizar_gerar_video,
                    False,
                    mensagem_com_registro(str(e), registro)
                )

        executar_em_segundo_plano(gerar)

    def finalizar_gerar_video(self, sucesso, mensagem):
        self.liberar_acoes()

        if sucesso:
            wx.MessageBox(mensagem, "Sucesso")
        else:
            wx.MessageBox(mensagem, "Erro")
