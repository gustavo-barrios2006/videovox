# -*- coding: utf-8 -*-
"""Consultas sobre os arquivos de midia usadas pela interface."""
from core.linha_do_tempo import duracao_recorte_audio
from motor import midia_info


def duracao_video(caminho):
    return midia_info.duracao_video(caminho)


def duracao_audio(caminho):
    return midia_info.duracao_audio(caminho)


def obter_duracao_recorte_audio(item):
    # A duracao original fica guardada no proprio item para nao reabrir o
    # arquivo a cada atualizacao da lista.
    duracao_original = item.get("duracao_original")
    if duracao_original is None:
        try:
            duracao_original = midia_info.duracao_audio(item["arquivo"])
            item["duracao_original"] = duracao_original
        except Exception:
            duracao_original = 0.0

    return duracao_recorte_audio(item, duracao_original)
