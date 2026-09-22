# -*- coding: utf-8 -*-
"""Janela principal: menu, abas, e salvar/carregar projeto."""
import wx

from core.opcoes import indice_tamanho_quadro
from core.projeto import EstadoProjeto
from infra import caminhos
from servicos import projeto_io
from ui.abas.aba_criar import AbaCriar
from ui.abas.aba_editar import AbaEditar
from ui.tarefas import executar_em_segundo_plano


class MainFrame(wx.Frame):

    def __init__(self):
        super().__init__(
            None,
            title="Editor e Criador de Vídeos",
            size=(800, 700)
        )

        self.estado = EstadoProjeto()
        self.temp_session_dirs = []
        caminhos.limpar_arquivos_temporarios()

        # Bind close event
        self.Bind(wx.EVT_CLOSE, self.on_close)

        # Menu Bar
        menu_bar = wx.MenuBar()
        menu_arquivo = wx.Menu()

        item_carregar = menu_arquivo.Append(wx.ID_ANY, "Carregar &Projeto...\tCtrl+O", "Carregar um projeto existente")
        item_salvar = menu_arquivo.Append(wx.ID_ANY, "&Salvar Projeto...\tCtrl+S", "Salvar o projeto atual")
        menu_arquivo.AppendSeparator()
        item_sair = menu_arquivo.Append(wx.ID_EXIT, "Sai&r", "Fechar o programa")

        menu_bar.Append(menu_arquivo, "&Arquivo")
        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.on_carregar_projeto, item_carregar)
        self.Bind(wx.EVT_MENU, self.on_salvar_projeto, item_salvar)
        self.Bind(wx.EVT_MENU, self.on_sair_comp, item_sair)

        # Notebook para abas
        self.notebook = wx.Notebook(self)

        # Aba 1: Criar Videoclipe
        self.aba_criar = AbaCriar(self.notebook, self, self.estado)
        self.notebook.AddPage(self.aba_criar, "&Criar Videoclipe")

        # Aba 2: Editar Video
        self.aba_editar = AbaEditar(self.notebook, self)
        self.notebook.AddPage(self.aba_editar, "&Editar Vídeo")

        self.Centre()

    def on_sair_comp(self, event):
        self.Close()

    def on_close(self, event):
        caminhos.remover_pastas(self.temp_session_dirs)
        event.Skip()

    # ------------------------------------------------------------------
    # Salvar projeto
    # ------------------------------------------------------------------

    def on_salvar_projeto(self, event):
        estado = self.estado
        if not estado.imagens and not estado.audios:
            wx.MessageBox("O projeto está vazio. Adicione mídias ou áudios antes de salvar.", "Aviso")
            return

        with wx.FileDialog(
            self,
            "Salvar projeto",
            wildcard="Projeto de Vídeo (*.wvp)|*.wvp",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            destino = dlg.GetPath()

        self.aba_criar.bloquear_acoes()

        # Lidos na thread principal (wx nao e thread-safe).
        fps_texto = self.aba_criar.obter_fps_texto()
        tamanho_quadro = self.aba_criar.obter_tamanho_quadro()
        imagens = estado.imagens
        audios = estado.audios

        def salvar():
            try:
                projeto_io.salvar_projeto(
                    destino, imagens, audios, fps_texto, tamanho_quadro
                )
                wx.CallAfter(self.finalizar_salvar_projeto, True, "Projeto salvo com sucesso.")
            except Exception as e:
                wx.CallAfter(self.finalizar_salvar_projeto, False, str(e))

        executar_em_segundo_plano(salvar)

    def finalizar_salvar_projeto(self, sucesso, mensagem):
        self.aba_criar.liberar_acoes()
        if sucesso:
            wx.MessageBox(mensagem, "Sucesso")
        else:
            wx.MessageBox(f"Erro ao salvar projeto: {mensagem}", "Erro")

    # ------------------------------------------------------------------
    # Carregar projeto
    # ------------------------------------------------------------------

    def on_carregar_projeto(self, event):
        if self.estado.imagens or self.estado.audios:
            confirm = wx.MessageBox(
                "Deseja carregar o projeto? As mídias e áudios atuais serão substituídos.",
                "Confirmar Carregamento",
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION
            )
            if confirm != wx.YES:
                return

        with wx.FileDialog(
            self,
            "Carregar projeto",
            wildcard="Projeto de Vídeo (*.wvp)|*.wvp",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            caminho_projeto = dlg.GetPath()

        self.aba_criar.bloquear_acoes()

        pasta_temp_projetos = caminhos.pasta_temp_projetos()

        def carregar():
            try:
                projeto = projeto_io.carregar_projeto(
                    caminho_projeto, pasta_temp_projetos
                )

                if projeto.temp_dir is not None:
                    self.temp_session_dirs.append(projeto.temp_dir)

                def apply_changes():
                    self.estado.imagens = projeto.imagens
                    self.estado.audios = projeto.audios
                    self.aba_criar.aplicar_configuracoes(
                        str(projeto.fps),
                        indice_tamanho_quadro(projeto.tamanho_quadro)
                    )
                    self.aba_criar.atualizar_listas()
                    self.finalizar_carregar_projeto(True, "Projeto carregado com sucesso.")

                wx.CallAfter(apply_changes)

            except Exception as e:
                wx.CallAfter(self.finalizar_carregar_projeto, False, str(e))

        executar_em_segundo_plano(carregar)

    def finalizar_carregar_projeto(self, sucesso, mensagem):
        self.aba_criar.liberar_acoes()
        if sucesso:
            wx.MessageBox(mensagem, "Sucesso")
        else:
            wx.MessageBox(f"Erro ao carregar projeto: {mensagem}", "Erro")
