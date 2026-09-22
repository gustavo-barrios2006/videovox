# -*- coding: utf-8 -*-
"""Pastas usadas pelo app.

A pasta do programa e informada pelo lancador (videovox.pyw) com a pasta dele
mesmo. No executavel do PyInstaller (onefile) essa pasta e a de extracao
temporaria (_MEIxxxx), que o PyInstaller apaga ao fechar o app.
"""
import os
import shutil
import sys

_pasta_programa = None


def definir_pasta_programa(pasta):
    global _pasta_programa
    _pasta_programa = pasta


def pasta_programa():
    if _pasta_programa is not None:
        return _pasta_programa
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def pasta_do_executavel():
    """Pasta visivel ao usuario onde o app esta: a do videovox.exe no
    executavel do PyInstaller, ou a do lancador ao rodar pelo codigo-fonte."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return pasta_programa()


def pasta_dados_usuario():
    """Pasta sempre gravavel do usuario (%LOCALAPPDATA%\\VideoVox)."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "VideoVox")


def pasta_temp_projetos():
    return os.path.join(pasta_programa(), "temp_projects")


def limpar_arquivos_temporarios():
    try:
        temp_root = pasta_temp_projetos()
        if os.path.exists(temp_root):
            for item in os.listdir(temp_root):
                item_path = os.path.join(temp_root, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
    except Exception as e:
        print(f"Erro ao limpar temporarios: {e}")


def remover_pastas(pastas):
    try:
        for temp_dir in pastas:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    except:
        pass
