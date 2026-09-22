# -*- coding: utf-8 -*-
"""Estado do projeto aberto no app."""


class EstadoProjeto:
    """Midias (imagens e videos) e audios do projeto, como dicts no mesmo
    formato salvo no project.json, e o ultimo video base salvo."""

    def __init__(self):
        self.imagens = []
        self.audios = []
        self.video_atual = None
