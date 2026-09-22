# -*- coding: utf-8 -*-
"""Caso de uso "Gerar Vídeo Final": mixa a lista de audios sobre o video base
salvo anteriormente."""
from motor import moviepy_adapter as motor


def gerar_video_final(video_atual, audios, destino):
    motor.mixar_audios(video_atual, audios, destino)
