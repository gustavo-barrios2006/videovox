# -*- coding: utf-8 -*-
"""Caso de uso "Salvar Vídeo Base": monta o videoclipe a partir da lista de
midias (imagens e videos) e exporta o arquivo."""
from core.layout import calcular_quadro, normalizar_fps
from core.linha_do_tempo import duracao_midia
from motor import moviepy_adapter as motor


def criar_video(destino, itens, fps_valor, modo_quadro, ao_progredir=None):
    """`ao_progredir(Progresso)`, opcional, acompanha a exportacao."""

    clips = []
    tamanhos = []
    inicio_destino = 0
    duracao_total = 0

    fps_valor = normalizar_fps(fps_valor)
    if modo_quadro is None:
        modo_quadro = "maior_altura_largura"

    for item in itens:

        clip = motor.abrir_clipe_midia(item, fps_valor)
        clip = motor.ajustar_dimensoes_pares(clip)

        if item.get("inicio_destino") is not None:
            inicio_item_destino = item["inicio_destino"]
        else:
            inicio_item_destino = inicio_destino

        clip = motor.com_inicio(clip, inicio_item_destino)
        fim_destino = inicio_item_destino + duracao_midia(item)
        inicio_destino = max(inicio_destino, fim_destino)
        duracao_total = max(duracao_total, fim_destino)
        tamanhos.append(motor.tamanho(clip))

        clips.append(clip)

    largura, altura = calcular_quadro(tamanhos, modo_quadro)

    clips = [
        motor.ajustar_ao_quadro(
            clip, item.get("ajuste_imagem", "preencher"), largura, altura
        )
        for item, clip in zip(itens, clips)
    ]

    motor.exportar_composicao(
        clips, largura, altura, duracao_total, fps_valor, destino,
        ao_progredir
    )
