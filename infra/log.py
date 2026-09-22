# -*- coding: utf-8 -*-
"""Registro de erros para diagnostico."""
import traceback


def registrar_erro_atual():
    """Grava o traceback da excecao em tratamento no erro.txt da pasta atual.
    Deve ser chamada de dentro de um bloco except."""
    with open("erro.txt", "w", encoding="utf-8") as f:
        f.write(traceback.format_exc())
