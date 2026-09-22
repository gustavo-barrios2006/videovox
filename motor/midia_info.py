# -*- coding: utf-8 -*-
"""Leitura de informacoes dos arquivos de midia (duracao)."""
from moviepy import AudioFileClip, VideoFileClip


def duracao_video(caminho):
    video = VideoFileClip(caminho)
    duracao = video.duration
    video.close()
    return duracao


def duracao_audio(caminho):
    audio = AudioFileClip(caminho)
    duracao = audio.duration
    audio.close()
    return duracao
