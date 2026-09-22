# -*- coding: utf-8 -*-
"""Adaptador do MoviePy: unico modulo do VideoVox que monta e exporta clipes.

Mantenha aqui qualquer detalhe especifico da biblioteca (API, contornos de
bugs, parametros do ffmpeg), para que o resto do app nao dependa dela.
"""
from moviepy import (
    ImageClip,
    ColorClip,
    AudioFileClip,
    VideoFileClip,
    concatenate_videoclips,
    CompositeVideoClip,
    CompositeAudioClip
)

from core.opcoes import POSICAO_AJUSTE_IMAGEM
from motor.progresso import logger_para


# ---------------------------------------------------------------------------
# Videoclipe (imagens e videos na linha do tempo)
# ---------------------------------------------------------------------------

def abrir_clipe_midia(item, fps_valor):
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

    return clip


def ajustar_dimensoes_pares(clip):
    # Garante que as dimensoes sejam pares para o codec libx264 (yuv420p).
    w, h = clip.size
    new_w = w if w % 2 == 0 else w - 1
    new_h = h if h % 2 == 0 else h - 1

    if new_w != w or new_h != h:
        return clip.resized(new_size=(new_w, new_h))

    return clip


def com_inicio(clip, inicio):
    return clip.with_start(inicio)


def tamanho(clip):
    return clip.w, clip.h


def ajustar_ao_quadro(clip, chave_ajuste, largura, altura):
    # Midias com ajuste "preencher" (padrao) sao esticadas ate ocupar todo o
    # quadro, em qualquer modo de tamanho do quadro. As demais opcoes mantem a
    # midia no tamanho original, apenas posicionando-a (centro, cantos ou
    # bordas). Sem isso, midias menores ficam presas no canto sobre o fundo
    # preto.
    if chave_ajuste != "preencher":
        posicao = POSICAO_AJUSTE_IMAGEM.get(chave_ajuste, "center")
        clip = clip.with_position(posicao)
    else:
        # "Preencher" estica a midia para ocupar todo o quadro final.
        if (clip.w, clip.h) != (largura, altura):
            clip = clip.resized(new_size=(largura, altura))
        clip = clip.with_position("center")
    return clip


def exportar_composicao(clips, largura, altura, duracao_total, fps_valor,
                        destino, ao_progredir=None):
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
        audio_codec="aac",
        logger=logger_para(ao_progredir, com_audio=bool(clips_audio))
    )

    video.close()
    fundo.close()

    for clip in clips:
        clip.close()


# ---------------------------------------------------------------------------
# Mixagem de audios sobre um video ja salvo
# ---------------------------------------------------------------------------

def mixar_audios(video_atual, audios, destino, ao_progredir=None):
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
        ffmpeg_params=["-pix_fmt", "yuv420p"],
        logger=logger_para(ao_progredir, com_audio=True)
    )

    # Cleanup
    # Nota: Fechar os AudioFileClips criados no loop se necessario,
    # mas o video_final.close() costuma lidar com a arvore de clips.
    video.close()
    video_final.close()
    for audio in audio_clips_abertos:
        audio.close()


# ---------------------------------------------------------------------------
# Remocao de trechos (aba Editar)
# ---------------------------------------------------------------------------

def abrir_video(caminho):
    return VideoFileClip(caminho)


def exportar_trechos(video, mantidos, destino, preset):
    # Criar os subclips
    clips = [video.subclipped(s, e) for s, e in mantidos]

    video_final = concatenate_videoclips(clips)

    video_final.write_videofile(
        destino,
        codec="libx264",
        ffmpeg_params=["-pix_fmt", "yuv420p", "-c:a", "copy"],
        threads=4,
        preset=preset,
        logger=None
    )

    # Cleanup
    video_final.close()
    for c in clips:
        c.close()
    video.close()
