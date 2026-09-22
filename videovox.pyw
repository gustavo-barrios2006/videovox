# -*- coding: utf-8 -*-
"""Lancador do VideoVox. O codigo do app fica nos pacotes core, motor,
servicos, infra e ui (veja app.py)."""
import io
import os
import sys

# Sem console (.pyw ou executavel windowed), stdout/stderr sao None e o
# MoviePy/proglog falhariam ao escrever neles.
if sys.stdout is None:
    sys.stdout = io.StringIO()

if sys.stderr is None:
    sys.stderr = io.StringIO()

# Pasta deste arquivo: base da pasta temp_projects. No executavel onefile do
# PyInstaller e a pasta de extracao temporaria (_MEIxxxx).
PASTA_PROGRAMA = os.path.dirname(os.path.abspath(__file__))

# Garante que os pacotes do app (ao lado deste arquivo) sejam importaveis mesmo
# quando o lancador e executado por ferramentas que nao poem a pasta do script
# no sys.path (runpy, alguns depuradores e executores de IDE).
if PASTA_PROGRAMA not in sys.path:
    sys.path.insert(0, PASTA_PROGRAMA)

from app import main  # noqa: E402

if __name__ == "__main__":

    main(PASTA_PROGRAMA)
