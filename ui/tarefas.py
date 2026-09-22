# -*- coding: utf-8 -*-
"""Execucao de tarefas demoradas fora da thread da interface.

A funcao executada nao deve mexer em widgets: para atualizar a interface ao
terminar, ela deve usar wx.CallAfter.
"""
import threading


def executar_em_segundo_plano(funcao):
    thread = threading.Thread(target=funcao)
    thread.start()
    return thread
