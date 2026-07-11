# -*- coding: utf-8 -*-
import wx
import os
import re
import io
import sys

if sys.stdout is None:
    sys.stdout = io.StringIO()

if sys.stderr is None:
    sys.stderr = io.StringIO()

from moviepy import (
    ImageClip,
    ColorClip,
    AudioFileClip,
    VideoFileClip,
    concatenate_videoclips,
    CompositeVideoClip,
    CompositeAudioClip
)

# Opcoes de ajuste de imagem no quadro final.
# (rotulo exibido, chave salva no item, posicao do MoviePy)
# "preencher" (padrao) redimensiona a imagem mantendo a proporcao para
# preencher o quadro e a centraliza. As demais opcoes mantem a imagem no
# tamanho original, apenas posicionando-a no quadro.
OPCOES_AJUSTE_IMAGEM = [
    ("Preencher quadro", "preencher", None),
    ("Centralizar", "centralizar", "center"),
    ("Superior esquerdo", "sup_esq", ("left", "top")),
    ("Superior centro", "sup_centro", ("center", "top")),
    ("Superior direito", "sup_dir", ("right", "top")),
    ("Centro esquerdo", "centro_esq", ("left", "center")),
    ("Centro direito", "centro_dir", ("right", "center")),
    ("Inferior esquerdo", "inf_esq", ("left", "bottom")),
    ("Inferior centro", "inf_centro", ("center", "bottom")),
    ("Inferior direito", "inf_dir", ("right", "bottom")),
]

ROTULOS_AJUSTE_IMAGEM = [op[0] for op in OPCOES_AJUSTE_IMAGEM]
CHAVES_AJUSTE_IMAGEM = [op[1] for op in OPCOES_AJUSTE_IMAGEM]
POSICAO_AJUSTE_IMAGEM = {op[1]: op[2] for op in OPCOES_AJUSTE_IMAGEM}


# Opcoes de tamanho do quadro (resolucao) do video final.
# (rotulo exibido, chave)
# "maior_altura_largura": o quadro usa a maior largura e a maior
#   altura encontradas entre as midias, calculadas de forma independente (pode
#   nao corresponder a resolucao de nenhuma midia individual).
# "maior_midia": o quadro usa a resolucao exata da maior midia (por area). Com
#   o ajuste "Preencher quadro" a midia e esticada ate o tamanho da maior midia.
# "tela_inteira": o quadro usa a resolucao da tela. Com o ajuste "Preencher
#   quadro" a midia e esticada ate ocupar a tela inteira.
OPCOES_TAMANHO_QUADRO = [
    ("Maior largura e maior altura entre as mídias", "maior_altura_largura"),
    ("Tamanho da maior mídia", "maior_midia"),
    ("Tela inteira", "tela_inteira"),
]

ROTULOS_TAMANHO_QUADRO = [op[0] for op in OPCOES_TAMANHO_QUADRO]
CHAVES_TAMANHO_QUADRO = [op[1] for op in OPCOES_TAMANHO_QUADRO]


def indice_ajuste_imagem(chave):
    try:
        return CHAVES_AJUSTE_IMAGEM.index(chave)
    except ValueError:
        return 0


class EditFrame(wx.Frame):

    def __init__(self, parent, item, index, item_type):
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
        if self.item_type == "audio":
            self.parent.lista_audio.SetFocus()
        else:
            self.parent.lista.SetFocus()
        self.Destroy()

    def on_salvar(self, event):
        caminho = self.item["arquivo"]

        if self.item_type == "video":
            inicio_str = self.inputs["inicio"].GetValue().strip()
            fim_str = self.inputs["fim"].GetValue().strip()
            destino_str = self.inputs["inicio_destino"].GetValue().strip()

            if not self.parent.validar_numero(inicio_str):
                wx.MessageBox("O início do vídeo deve ser um número.", "Erro")
                return

            if fim_str and not self.parent.validar_numero(fim_str):
                wx.MessageBox("O fim do vídeo deve ser um número ou vazio.", "Erro")
                return

            if destino_str and not self.parent.validar_numero(destino_str):
                wx.MessageBox("O início no vídeo destino deve ser um número ou vazio.", "Erro")
                return

            inicio = float(inicio_str)
            fim = float(fim_str) if fim_str else None
            inicio_destino = float(destino_str) if destino_str else None

            try:
                video = VideoFileClip(caminho)
                duracao_video = video.duration
                video.close()
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

            if not self.parent.validar_numero(tempo):
                wx.MessageBox("Informe apenas um número inteiro ou real.", "Erro")
                return

            if destino_str and not self.parent.validar_numero(destino_str):
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

            if not self.parent.validar_numero(inicio_audio_str):
                wx.MessageBox("Início do Áudio deve ser um número.", "Erro")
                return
            if fim_audio_str and not self.parent.validar_numero(fim_audio_str):
                wx.MessageBox("Fim do Áudio deve ser um número ou vazio.", "Erro")
                return
            if pos_video_str and not self.parent.validar_numero(pos_video_str):
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
        if self.item_type == "audio":
            self.parent.atualizar_lista_audios()
        else:
            self.parent.atualizar_lista_midias()

        self.Close()


class MainFrame(wx.Frame):

    def __init__(self):
        super().__init__(
            None,
            title="Editor e Criador de Vídeos",
            size=(800, 700)
        )

        self.imagens = []
        self.audios = []
        self.video_atual = None
        self.video_para_editar = None
        self.cortes = []
        self.temp_session_dirs = []
        self.limpar_arquivos_temporarios()

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
        self.aba_imagens = wx.Panel(self.notebook)
        self.setup_aba_imagens()
        self.notebook.AddPage(self.aba_imagens, "&Criar Videoclipe")

        # Aba 2: Editar Video
        self.aba_editar = wx.Panel(self.notebook)
        self.setup_aba_editar()
        self.notebook.AddPage(self.aba_editar, "&Editar Vídeo")

        self.Centre()

    def setup_aba_imagens(self):
        painel = self.aba_imagens
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
        self.btn_procurar_audio.Bind(wx.EVT_BUTTON, self.on_procurar_audio)
        self.btn_add_audio.Bind(wx.EVT_BUTTON, self.on_adicionar_audio)
        self.btn_remover_audio.Bind(wx.EVT_BUTTON, self.on_remover_audio)
        self.btn_editar_audio.Bind(wx.EVT_BUTTON, self.on_editar_audio)
        self.btn_carregar_projeto.Bind(wx.EVT_BUTTON, self.on_carregar_projeto)
        self.btn_salvar_projeto.Bind(wx.EVT_BUTTON, self.on_salvar_projeto)
        self.btn_salvar_video.Bind(wx.EVT_BUTTON, self.on_salvar_video)
        self.btn_gerar_final.Bind(wx.EVT_BUTTON, self.on_gerar_video_final)

    def setup_aba_editar(self):
        painel = self.aba_editar
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
            self,
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

        if not self.validar_numero(inicio_str) or not self.validar_numero(fim_str):
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
        
        # Mapeamento de qualidade para presets e bitrates
        # 0: Alta (veryslow / compressao maxima)
        # 1: Media (medium)
        # 2: Baixa (ultrafast / compressao minima)
        presets = ["veryslow", "medium", "ultrafast"]
        preset_escolhido = presets[qualidade_idx]

        with wx.FileDialog(
            self,
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

        import threading

        def processar():
            try:
                video = VideoFileClip(self.video_para_editar)
                duracao_total = video.duration
                
                # Ordenar cortes
                cortes_ordenados = sorted(self.cortes)
                
                # Definir intervalos a MANTER
                mantidos = []
                atual = 0
                
                for inicio, fim in cortes_ordenados:
                    if inicio > atual:
                        mantidos.append((atual, inicio))
                    atual = max(atual, fim)
                
                if atual < duracao_total:
                    mantidos.append((atual, duracao_total))
                
                if not mantidos:
                    wx.CallAfter(wx.MessageBox, "O vídeo resultante ficaria vazio!", "Erro")
                    video.close()
                    return

                # Criar os subclips
                clips = [video.subclipped(s, e) for s, e in mantidos]
                
                video_final = concatenate_videoclips(clips)

                video_final.write_videofile(
                    destino,
                    codec="libx264",
                    ffmpeg_params=["-pix_fmt", "yuv420p", "-c:a", "copy"],
                    threads=4,
                    preset=preset_escolhido,
                    logger=None
                )

                # Cleanup
                video_final.close()
                for c in clips:
                    c.close()
                video.close()

                wx.CallAfter(self.finalizar_processamento, True, "Vídeo processado com sucesso.")

            except Exception as e:
                wx.CallAfter(self.finalizar_processamento, False, str(e))

        thread = threading.Thread(target=processar)
        thread.start()

    def finalizar_processamento(self, sucesso, mensagem):
        if wx.IsBusy():
            wx.EndBusyCursor()
        self.btn_processar_cortes.Enable()
        
        if sucesso:
            wx.MessageBox(mensagem, "Sucesso")
        else:
            wx.MessageBox(f"Erro ao processar: {mensagem}", "Erro")

    def validar_numero(self, texto):

        texto = texto.strip()

        padrao = r'^\d+(\.\d+)?$'

        return re.match(padrao, texto) is not None

    def atualizar_lista_audios(self):
        self.lista_audio.Clear()
        posicao_atual = 0
        for info in self.audios:
            nome = os.path.basename(info["arquivo"])
            fim_desc = f"{info['fim']}s" if info['fim'] is not None else "Fim"
            
            if info["pos"] is not None:
                pos_calculada = info["pos"]
            else:
                pos_calculada = posicao_atual
            
            duracao_recorte = self.obter_duracao_recorte_audio(info)
            posicao_atual = pos_calculada + duracao_recorte
            
            if info["pos"] is not None:
                pos_desc = f"{pos_calculada}s"
            else:
                pos_desc = f"{pos_calculada}s (sequência)"
            
            self.lista_audio.Append(f"{nome} ({info['inicio']}s-{fim_desc}) em {pos_desc} no vídeo")

    def on_editar_midia(self, event):
        indice = self.lista.GetSelection()
        if indice == wx.NOT_FOUND:
            wx.MessageBox("Selecione uma mídia na lista para editar.", "Aviso")
            return

        item = self.imagens[indice]
        frame_edicao = EditFrame(self, item, indice, item["tipo"])
        frame_edicao.Show()

    def on_editar_audio(self, event):
        indice = self.lista_audio.GetSelection()
        if indice == wx.NOT_FOUND:
            wx.MessageBox("Selecione um áudio na lista para editar.", "Aviso")
            return

        item = self.audios[indice]
        frame_edicao = EditFrame(self, item, indice, "audio")
        frame_edicao.Show()

    def on_procurar_imagem(self, event):

        with wx.FileDialog(
            self,
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
            self,
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

        if not self.validar_numero(tempo):
            wx.MessageBox(
                "Informe apenas um número inteiro ou real.",
                "Erro"
            )
            return

        if destino_str and not self.validar_numero(destino_str):
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

        self.imagens.append(
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

        if not self.validar_numero(inicio_str):
            wx.MessageBox("O início do vídeo deve ser um número.", "Erro")
            return

        if fim_str and not self.validar_numero(fim_str):
            wx.MessageBox("O fim do vídeo deve ser um número ou vazio.", "Erro")
            return

        if destino_str and not self.validar_numero(destino_str):
            wx.MessageBox("O início no vídeo destino deve ser um número ou vazio.", "Erro")
            return

        inicio = float(inicio_str)
        fim = float(fim_str) if fim_str else None
        inicio_destino = float(destino_str) if destino_str else None

        try:
            video = VideoFileClip(caminho)
            duracao_video = video.duration
            video.close()
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

        self.imagens.append(
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

        del self.imagens[indice]

        self.atualizar_lista_midias()

    def duracao_midia(self, item):
        if item.get("tipo", "imagem") == "video":
            return item["fim"] - item["inicio"]

        return item["duracao"]

    def obter_duracao_recorte_audio(self, item):
        duracao_original = item.get("duracao_original")
        if duracao_original is None:
            try:
                audio = AudioFileClip(item["arquivo"])
                duracao_original = audio.duration
                audio.close()
                item["duracao_original"] = duracao_original
            except Exception:
                duracao_original = 0.0

        t_inicio = item["inicio"]
        t_fim = item["fim"] if item["fim"] is not None else duracao_original
        return max(0.0, min(t_fim, duracao_original) - t_inicio)

    def atualizar_lista_midias(self):
        self.lista.Clear()
        inicio_destino = 0

        for item in self.imagens:
            duracao = self.duracao_midia(item)
            if item.get("inicio_destino") is not None:
                inicio_item_destino = item["inicio_destino"]
            else:
                inicio_item_destino = inicio_destino

            fim_destino = inicio_item_destino + duracao
            nome = os.path.basename(item["arquivo"])

            if item.get("tipo", "imagem") == "video":
                silenciado_str = " (Silenciado)" if item.get("silenciado") else ""
                descricao = (
                    f"Vídeo: {nome}{silenciado_str} "
                    f"original {item['inicio']}s-{item['fim']}s "
                    f"-> final {inicio_item_destino}s-{fim_destino}s"
                )
            else:
                descricao = (
                    f"Imagem: {nome} "
                    f"duração {item['duracao']}s "
                    f"-> final {inicio_item_destino}s-{fim_destino}s"
                )

            self.lista.Append(descricao)
            inicio_destino = max(inicio_destino, fim_destino)
        
        self.atualizar_estado_botoes()

    def on_lista_select(self, event):
        self.atualizar_estado_botoes()

    def on_silenciar_video(self, event):
        indice = self.lista.GetSelection()
        if indice == wx.NOT_FOUND:
            return
        item = self.imagens[indice]
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
            item = self.imagens[indice]
            if item.get("tipo", "imagem") == "video":
                if item.get("silenciado"):
                    self.btn_silenciar.SetLabel("&Voltar Áudio")
                else:
                    self.btn_silenciar.SetLabel("&Silenciar Vídeo")
                self.btn_silenciar.Show()
            else:
                self.btn_silenciar.Hide()
        self.aba_imagens.Layout()

    def ajustar_dimensoes_pares(self, clip):
        # Garante que as dimensoes sejam pares para o codec libx264 (yuv420p).
        w, h = clip.size
        new_w = w if w % 2 == 0 else w - 1
        new_h = h if h % 2 == 0 else h - 1

        if new_w != w or new_h != h:
            return clip.resized(new_size=(new_w, new_h))

        return clip

    def ajustar_ao_quadro(self, clip, largura, altura):
        # Redimensiona o clipe para caber no quadro (largura x altura)
        # preservando a proporcao e o centraliza. Sem isso, midias menores
        # que o quadro final ficam ancoradas no canto superior esquerdo
        # (posicao padrao do CompositeVideoClip) sobre o fundo preto.
        escala = min(largura / clip.w, altura / clip.h)
        novo_w = max(2, int(round(clip.w * escala)))
        novo_h = max(2, int(round(clip.h * escala)))
        # Dimensoes pares para o codec libx264 (yuv420p).
        novo_w -= novo_w % 2
        novo_h -= novo_h % 2

        if (novo_w, novo_h) != (clip.w, clip.h):
            clip = clip.resized(new_size=(novo_w, novo_h))

        return clip.with_position("center")

    def criar_video(self, destino, imagens=None, fps_valor=None,
                    modo_quadro=None, tamanho_tela=None):

        clips = []
        inicio_destino = 0
        duracao_total = 0
        largura = 0
        altura = 0
        # Resolucao da maior midia (por area), usada no modo "maior_midia".
        maior_area = 0
        maior_largura = 0
        maior_altura = 0
        itens = imagens if imagens is not None else self.imagens

        # Modo de tamanho do quadro. Se nao informado (chamada fora da GUI),
        # le a selecao atual do combo na thread chamadora.
        if modo_quadro is None:
            try:
                modo_quadro = CHAVES_TAMANHO_QUADRO[
                    self.combo_tamanho_quadro.GetSelection()
                ]
            except Exception:
                modo_quadro = "maior_altura_largura"

        # Obtem FPS da interface
        if fps_valor is None:
            try:
                fps_valor = int(self.txt_fps.GetValue().strip())
                if fps_valor <= 0:
                    fps_valor = 30
            except:
                fps_valor = 30
        elif fps_valor <= 0:
            fps_valor = 30

        for item in itens:

            if item.get("tipo", "imagem") == "video":
                clip = (
                    VideoFileClip(item["arquivo"])
                    .subclipped(item["inicio"], item["fim"])
                    .with_fps(fps_valor)
                )
                if item.get("silenciado"):
                    clip = clip.without_audio()
            else:
                clip = ImageClip(
                    item["arquivo"],
                    duration=item["duracao"]
                ).with_fps(fps_valor)

            clip = self.ajustar_dimensoes_pares(clip)

            if item.get("inicio_destino") is not None:
                inicio_item_destino = item["inicio_destino"]
            else:
                inicio_item_destino = inicio_destino

            clip = clip.with_start(inicio_item_destino)
            fim_destino = inicio_item_destino + self.duracao_midia(item)
            inicio_destino = max(inicio_destino, fim_destino)
            duracao_total = max(duracao_total, fim_destino)
            largura = max(largura, clip.w)
            altura = max(altura, clip.h)

            area = clip.w * clip.h
            if area > maior_area:
                maior_area = area
                maior_largura = clip.w
                maior_altura = clip.h

            clips.append(clip)

        # Define a resolucao do quadro final conforme o modo escolhido. O modo
        # padrao ("maior_altura_largura") mantem a maior largura x maior altura calculadas
        # de forma independente no laco acima.
        if modo_quadro == "maior_midia":
            largura, altura = maior_largura, maior_altura
        elif modo_quadro == "tela_inteira" and tamanho_tela:
            largura, altura = int(tamanho_tela[0]), int(tamanho_tela[1])

        # Garante dimensoes pares para o codec libx264 (yuv420p).
        largura = max(2, largura - (largura % 2))
        altura = max(2, altura - (altura % 2))

        # Normaliza cada clipe ao tamanho do quadro final. Midias (imagens ou
        # videos) com ajuste "preencher" (padrao) sao redimensionadas mantendo
        # a proporcao para preencher o quadro. As demais opcoes mantem a midia
        # no tamanho original, apenas posicionando-a (centro, cantos ou bordas).
        # Sem isso, midias menores ficam presas no canto sobre o fundo preto.
        clips_ajustados = []
        for item, clip in zip(itens, clips):
            chave_ajuste = item.get("ajuste_imagem", "preencher")
            if chave_ajuste != "preencher":
                posicao = POSICAO_AJUSTE_IMAGEM.get(chave_ajuste, "center")
                clip = clip.with_position(posicao)
            elif modo_quadro in ("maior_midia", "tela_inteira"):
                # "Preencher" nestes modos estica a midia para ocupar todo o
                # quadro (ate o tamanho da maior midia ou a tela inteira).
                if (clip.w, clip.h) != (largura, altura):
                    clip = clip.resized(new_size=(largura, altura))
                clip = clip.with_position("center")
            else:
                clip = self.ajustar_ao_quadro(clip, largura, altura)
            clips_ajustados.append(clip)
        clips = clips_ajustados

        fundo = ColorClip(
            size=(largura, altura),
            color=(0, 0, 0),
            duration=duracao_total
        ).with_fps(fps_valor)

        video = CompositeVideoClip(
            [fundo] + clips,
            size=(largura, altura)
        ).with_duration(duracao_total)

        clips_audio = [
            clip.audio
            for clip in clips
            if clip.audio is not None
        ]

        if clips_audio:
            video = video.with_audio(CompositeAudioClip(clips_audio))

        # Usando ffmpeg_params para pix_fmt em versoes que nao aceitam pix_fmt direto
        video.write_videofile(
            destino,
            fps=fps_valor,
            codec="libx264",
            ffmpeg_params=["-pix_fmt", "yuv420p"],
            audio_codec="aac"
        )

        video.close()
        fundo.close()

        for clip in clips:
            clip.close()

    def on_salvar_video(self, event):

        if not self.imagens:

            wx.MessageBox(
                "Nenhuma mídia adicionada.",
                "Erro"
            )

            return

        with wx.FileDialog(
            self,
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

        imagens = [item.copy() for item in self.imagens]

        # Captura na thread principal (wx nao e thread-safe): modo do quadro e
        # a resolucao da tela, repassados para a geracao em segundo plano.
        modo_quadro = CHAVES_TAMANHO_QUADRO[
            self.combo_tamanho_quadro.GetSelection()
        ]
        tamanho_tela = tuple(wx.GetDisplaySize())

        self.btn_salvar_video.Disable()
        self.btn_gerar_final.Disable()
        self.btn_salvar_projeto.Disable()
        self.btn_carregar_projeto.Disable()
        wx.BeginBusyCursor()

        import threading

        def salvar():
            try:
                self.criar_video(
                    destino,
                    imagens=imagens,
                    fps_valor=fps_valor,
                    modo_quadro=modo_quadro,
                    tamanho_tela=tamanho_tela
                )
                wx.CallAfter(
                    self.finalizar_salvar_video,
                    True,
                    destino,
                    "Vídeo criado com sucesso."
                )
            except Exception as e:
                import traceback
                with open("erro.txt", "w", encoding="utf-8") as f:
                    f.write(traceback.format_exc())
                wx.CallAfter(
                    self.finalizar_salvar_video,
                    False,
                    None,
                    str(e)
                )

        thread = threading.Thread(target=salvar)
        thread.start()

    def finalizar_salvar_video(self, sucesso, destino, mensagem):
        if wx.IsBusy():
            wx.EndBusyCursor()

        self.btn_salvar_video.Enable()
        self.btn_gerar_final.Enable()
        self.btn_salvar_projeto.Enable()
        self.btn_carregar_projeto.Enable()

        if sucesso:
            self.video_atual = destino
            wx.MessageBox(mensagem, "Sucesso")
        else:
            wx.MessageBox(mensagem, "Erro")

    def on_remover_audio(self, event):
        indice = self.lista_audio.GetSelection()
        if indice != wx.NOT_FOUND:
            del self.audios[indice]
            self.lista_audio.Delete(indice)

    def on_procurar_audio(self, event):
        with wx.FileDialog(
            self,
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

        if not self.validar_numero(inicio_audio_str):
            wx.MessageBox("Início do Áudio deve ser um número.", "Erro")
            return
        if fim_audio_str and not self.validar_numero(fim_audio_str):
            wx.MessageBox("Fim do Áudio deve ser um número ou vazio.", "Erro")
            return
        if pos_video_str and not self.validar_numero(pos_video_str):
            wx.MessageBox("Início no vídeo deve ser um número ou vazio.", "Erro")
            return

        pos_video = float(pos_video_str) if pos_video_str else None

        if pos_video is not None and pos_video < 0:
            wx.MessageBox("O início no vídeo não pode ser negativo.", "Erro")
            return

        try:
            audio = AudioFileClip(caminho)
            duracao_original = audio.duration
            audio.close()
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
        
        self.audios.append(info)
        self.atualizar_lista_audios()

        # Limpar campos apos adicionar
        self.txt_audio.Clear()
        self.txt_audio_inicio.SetValue("0")
        self.txt_audio_fim.Clear()
        self.txt_video_pos.Clear()

    def on_gerar_video_final(self, event):
        if not self.video_atual:
            wx.MessageBox("Salve um vídeo sem as mixagens primeiro.", "Erro")
            return
        
        if not self.audios:
            wx.MessageBox("Adicione pelo menos um Áudio à lista.", "Erro")
            return

        with wx.FileDialog(
            self,
            "Salvar vídeo final",
            wildcard="MP4 (*.mp4)|*.mp4",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            destino = dlg.GetPath()

        self.btn_salvar_video.Disable()
        self.btn_gerar_final.Disable()
        self.btn_salvar_projeto.Disable()
        self.btn_carregar_projeto.Disable()
        wx.BeginBusyCursor()

        video_atual = self.video_atual
        audios = [item.copy() for item in self.audios]

        import threading

        def gerar():
            try:
                video = VideoFileClip(video_atual)
                clips_audio = []
                audio_clips_abertos = []
                duracao_audio_total = video.duration

                # Se o video original tiver Áudio, inclua-lo
                if video.audio is not None:
                    clips_audio.append(video.audio)

                posicao_atual = 0
                for item in audios:
                    audio = AudioFileClip(item["arquivo"])
                    audio_clips_abertos.append(audio)
                    
                    t_inicio = item["inicio"]
                    t_fim = item["fim"] if item["fim"] is not None else audio.duration
                    
                    # Recortar e posicionar
                    recorte = audio.subclipped(t_inicio, min(t_fim, audio.duration))
                    
                    if item["pos"] is not None:
                        pos_video = item["pos"]
                    else:
                        pos_video = posicao_atual
                    
                    posicionado = recorte.with_start(pos_video)
                    
                    clips_audio.append(posicionado)
                    duracao_audio_total = max(duracao_audio_total, pos_video + recorte.duration)
                    posicao_atual = pos_video + recorte.duration

                audio_final = CompositeAudioClip(clips_audio).with_duration(duracao_audio_total)
                video_final = video.with_audio(audio_final)

                video_final.write_videofile(
                    destino,
                    fps=video.fps or 30,
                    codec="libx264",
                    audio_codec="aac",
                    ffmpeg_params=["-pix_fmt", "yuv420p"]
                )

                # Cleanup
                # Nota: Fechar os AudioFileClips criados no loop se necessario, 
                # mas o video_final.close() costuma lidar com a arvore de clips.
                video.close()
                video_final.close()
                for audio in audio_clips_abertos:
                    audio.close()

                wx.CallAfter(self.finalizar_gerar_video, True, "Vídeo final com mixagem concluído!")

            except Exception as e:
                wx.CallAfter(self.finalizar_gerar_video, False, str(e))

        thread = threading.Thread(target=gerar)
        thread.start()

    def finalizar_gerar_video(self, sucesso, mensagem):
        if wx.IsBusy():
            wx.EndBusyCursor()

        self.btn_salvar_video.Enable()
        self.btn_gerar_final.Enable()
        self.btn_salvar_projeto.Enable()
        self.btn_carregar_projeto.Enable()

        if sucesso:
            wx.MessageBox(mensagem, "Sucesso")
        else:
            wx.MessageBox(mensagem, "Erro")

    def on_sair_comp(self, event):
        self.Close()

    def on_close(self, event):
        try:
            import shutil
            for temp_dir in self.temp_session_dirs:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass
        event.Skip()

    def limpar_arquivos_temporarios(self):
        try:
            import shutil
            program_dir = os.path.dirname(os.path.abspath(__file__))
            temp_root = os.path.join(program_dir, "temp_projects")
            if os.path.exists(temp_root):
                for item in os.listdir(temp_root):
                    item_path = os.path.join(temp_root, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
        except Exception as e:
            print(f"Erro ao limpar temporarios: {e}")

    def on_salvar_projeto(self, event):
        if not self.imagens and not self.audios:
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

        self.btn_salvar_video.Disable()
        self.btn_gerar_final.Disable()
        self.btn_salvar_projeto.Disable()
        self.btn_carregar_projeto.Disable()
        wx.BeginBusyCursor()

        import threading
        def salvar():
            try:
                import zipfile
                import json
                
                # Check if all files exist
                for item in self.imagens:
                    if not os.path.exists(item["arquivo"]):
                        raise FileNotFoundError(f"Arquivo não encontrado: {item['arquivo']}")
                for item in self.audios:
                    if not os.path.exists(item["arquivo"]):
                        raise FileNotFoundError(f"Arquivo não encontrado: {item['arquivo']}")

                with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    imagens_copy = []
                    audios_copy = []
                    path_to_zip_name = {}
                    used_zip_names = set()

                    for item in self.imagens:
                        orig_path = item["arquivo"]
                        if orig_path not in path_to_zip_name:
                            base_name = os.path.basename(orig_path)
                            name, ext = os.path.splitext(base_name)
                            zip_name = f"media/{base_name}"
                            counter = 1
                            while zip_name in used_zip_names:
                                zip_name = f"media/{name}({counter}){ext}"
                                counter += 1
                            used_zip_names.add(zip_name)
                            path_to_zip_name[orig_path] = zip_name
                            zip_file.write(orig_path, zip_name)
                        
                        item_data = item.copy()
                        item_data["zip_path"] = path_to_zip_name[orig_path]
                        imagens_copy.append(item_data)

                    for item in self.audios:
                        orig_path = item["arquivo"]
                        if orig_path not in path_to_zip_name:
                            base_name = os.path.basename(orig_path)
                            name, ext = os.path.splitext(base_name)
                            zip_name = f"media/{base_name}"
                            counter = 1
                            while zip_name in used_zip_names:
                                zip_name = f"media/{name}({counter}){ext}"
                                counter += 1
                            used_zip_names.add(zip_name)
                            path_to_zip_name[orig_path] = zip_name
                            zip_file.write(orig_path, zip_name)
                        
                        item_data = item.copy()
                        item_data["zip_path"] = path_to_zip_name[orig_path]
                        audios_copy.append(item_data)

                    project_data = {
                        "version": 1,
                        "fps": self.txt_fps.GetValue().strip(),
                        "tamanho_quadro": CHAVES_TAMANHO_QUADRO[
                            self.combo_tamanho_quadro.GetSelection()
                        ],
                        "imagens": imagens_copy,
                        "audios": audios_copy
                    }

                    zip_file.writestr("project.json", json.dumps(project_data, indent=4, ensure_ascii=False))

                wx.CallAfter(self.finalizar_salvar_projeto, True, "Projeto salvo com sucesso.")
            except Exception as e:
                wx.CallAfter(self.finalizar_salvar_projeto, False, str(e))

        thread = threading.Thread(target=salvar)
        thread.start()

    def finalizar_salvar_projeto(self, sucesso, mensagem):
        if wx.IsBusy():
            wx.EndBusyCursor()
        self.btn_salvar_video.Enable()
        self.btn_gerar_final.Enable()
        self.btn_salvar_projeto.Enable()
        self.btn_carregar_projeto.Enable()
        if sucesso:
            wx.MessageBox(mensagem, "Sucesso")
        else:
            wx.MessageBox(f"Erro ao salvar projeto: {mensagem}", "Erro")

    def on_carregar_projeto(self, event):
        if self.imagens or self.audios:
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

        self.btn_salvar_video.Disable()
        self.btn_gerar_final.Disable()
        self.btn_salvar_projeto.Disable()
        self.btn_carregar_projeto.Disable()
        wx.BeginBusyCursor()

        import threading
        def carregar():
            try:
                import zipfile
                import json
                import uuid
                
                program_dir = os.path.dirname(os.path.abspath(__file__))
                session_id = uuid.uuid4().hex
                temp_dir = os.path.join(program_dir, "temp_projects", session_id)
                
                with zipfile.ZipFile(caminho_projeto, 'r') as zip_file:
                    project_json = zip_file.read("project.json").decode('utf-8')
                    project_data = json.loads(project_json)
                    
                    fps_val = project_data.get("fps", "30")
                    tamanho_quadro_val = project_data.get(
                        "tamanho_quadro", "maior_altura_largura"
                    )
                    imagens_raw = project_data.get("imagens", [])
                    audios_raw = project_data.get("audios", [])
                    
                    novas_imagens = []
                    novos_audios = []
                    extracted_any = False
                    
                    for item in imagens_raw:
                        orig_file = item.get("arquivo")
                        zip_path = item.get("zip_path")
                        
                        if orig_file and os.path.exists(orig_file):
                            resolved_path = orig_file
                        elif zip_path:
                            if not os.path.exists(temp_dir):
                                os.makedirs(temp_dir, exist_ok=True)
                            resolved_path = zip_file.extract(zip_path, temp_dir)
                            extracted_any = True
                        else:
                            raise FileNotFoundError(f"Não foi possível encontrar o arquivo original ou zip_path.")
                        
                        item_copy = item.copy()
                        item_copy["arquivo"] = resolved_path
                        item_copy.pop("zip_path", None)
                        novas_imagens.append(item_copy)
                        
                    for item in audios_raw:
                        orig_file = item.get("arquivo")
                        zip_path = item.get("zip_path")
                        
                        if orig_file and os.path.exists(orig_file):
                            resolved_path = orig_file
                        elif zip_path:
                            if not os.path.exists(temp_dir):
                                os.makedirs(temp_dir, exist_ok=True)
                            resolved_path = zip_file.extract(zip_path, temp_dir)
                            extracted_any = True
                        else:
                            raise FileNotFoundError(f"Não foi possível encontrar o arquivo original ou zip_path.")
                            
                        item_copy = item.copy()
                        item_copy["arquivo"] = resolved_path
                        item_copy.pop("zip_path", None)
                        novos_audios.append(item_copy)

                if extracted_any:
                    self.temp_session_dirs.append(temp_dir)
                
                def apply_changes():
                    self.imagens = novas_imagens
                    self.audios = novos_audios
                    self.txt_fps.SetValue(str(fps_val))
                    try:
                        idx_quadro = CHAVES_TAMANHO_QUADRO.index(tamanho_quadro_val)
                    except ValueError:
                        idx_quadro = 0
                    self.combo_tamanho_quadro.SetSelection(idx_quadro)
                    self.atualizar_lista_midias()
                    self.atualizar_lista_audios()
                    self.atualizar_estado_botoes()
                    self.finalizar_carregar_projeto(True, "Projeto carregado com sucesso.")
                
                wx.CallAfter(apply_changes)

            except Exception as e:
                wx.CallAfter(self.finalizar_carregar_projeto, False, str(e))

        thread = threading.Thread(target=carregar)
        thread.start()

    def finalizar_carregar_projeto(self, sucesso, mensagem):
        if wx.IsBusy():
            wx.EndBusyCursor()
        self.btn_salvar_video.Enable()
        self.btn_gerar_final.Enable()
        self.btn_salvar_projeto.Enable()
        self.btn_carregar_projeto.Enable()
        if sucesso:
            wx.MessageBox(mensagem, "Sucesso")
        else:
            wx.MessageBox(f"Erro ao carregar projeto: {mensagem}", "Erro")


class App(wx.App):

    def OnInit(self):

        frame = MainFrame()

        frame.Show()

        return True

if __name__ == "__main__":

    app = App(False)

    app.MainLoop()
