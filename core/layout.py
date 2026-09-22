# -*- coding: utf-8 -*-
"""Calculo do tamanho do quadro do video final."""
from core.opcoes import RESOLUCOES_PADRAO


def normalizar_fps(fps_valor):
    if fps_valor is None or fps_valor <= 0:
        return 30
    return fps_valor


def calcular_quadro(tamanhos, modo_quadro):
    """Recebe os tamanhos (largura, altura) das midias, na ordem da lista, e
    devolve o tamanho (largura, altura) do quadro final, sempre com dimensoes
    pares para o codec libx264 (yuv420p)."""
    largura = 0
    altura = 0
    # Resolucao da maior midia (por area), usada no modo "maior_midia".
    maior_area = 0
    maior_largura = 0
    maior_altura = 0

    for w, h in tamanhos:
        largura = max(largura, w)
        altura = max(altura, h)

        area = w * h
        if area > maior_area:
            maior_area = area
            maior_largura = w
            maior_altura = h

    # Define a resolucao do quadro final conforme o modo escolhido. O modo
    # padrao ("maior_altura_largura") mantem a maior largura x maior altura calculadas
    # de forma independente no laco acima.
    if modo_quadro == "maior_midia":
        largura, altura = maior_largura, maior_altura
    elif modo_quadro in RESOLUCOES_PADRAO:
        largura, altura = RESOLUCOES_PADRAO[modo_quadro]

    # Garante dimensoes pares para o codec libx264 (yuv420p).
    largura = max(2, largura - (largura % 2))
    altura = max(2, altura - (altura % 2))

    return largura, altura
