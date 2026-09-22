# -*- coding: utf-8 -*-
"""Validacao dos campos numericos digitados pelo usuario."""
import re


def validar_numero(texto):

    texto = texto.strip()

    padrao = r'^\d+(\.\d+)?$'

    return re.match(padrao, texto) is not None
