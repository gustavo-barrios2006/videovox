# -*- coding: utf-8 -*-
"""Calculo dos trechos mantidos ao remover cortes de um video."""


def intervalos_mantidos(cortes, duracao_total):
    """Recebe os cortes (inicio, fim) a remover e devolve os intervalos
    (inicio, fim) que permanecem no video, em ordem."""
    # Ordenar cortes
    cortes_ordenados = sorted(cortes)

    # Definir intervalos a MANTER
    mantidos = []
    atual = 0

    for inicio, fim in cortes_ordenados:
        if inicio > atual:
            mantidos.append((atual, inicio))
        atual = max(atual, fim)

    if atual < duracao_total:
        mantidos.append((atual, duracao_total))

    return mantidos
