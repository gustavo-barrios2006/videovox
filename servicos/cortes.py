# -*- coding: utf-8 -*-
"""Caso de uso da aba Editar: remove trechos de um video."""
from core.cortes import intervalos_mantidos
from motor import moviepy_adapter as motor


def processar_cortes(caminho_video, cortes, destino, preset):
    """Exporta o video sem os trechos em `cortes`. Devolve False, sem gerar
    arquivo, quando nao sobraria nenhum trecho do video."""
    video = motor.abrir_video(caminho_video)
    duracao_total = video.duration

    mantidos = intervalos_mantidos(cortes, duracao_total)

    if not mantidos:
        video.close()
        return False

    motor.exportar_trechos(video, mantidos, destino, preset)
    return True
