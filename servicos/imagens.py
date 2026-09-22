# -*- coding: utf-8 -*-
"""Deteccao e reducao das imagens grandes demais da lista de midias.

As imagens originais nunca sao alteradas: a versao reduzida e gravada ao lado
da original, com a dimensao no nome (ex.: "foto (1920x1280).jpg"), ou, se a
pasta nao permitir escrita, em %LOCALAPPDATA%\\VideoVox\\imagens_reduzidas.
"""
import os

from core.imagens import excede, tamanho_reduzido
from core.progresso import ETAPA_IMAGENS, Progresso
from infra import caminhos
from motor import imagens as motor_imagens


def imagens_grandes(itens):
    """Imagens (sem repetir arquivos) que excedem o limite, na ordem da lista:
    [(caminho, (largura, altura)), ...]. Arquivos ilegiveis sao ignorados
    aqui; a geracao do video informa o erro."""
    grandes = []
    vistos = set()
    for item in itens:
        if item.get("tipo", "imagem") != "imagem":
            continue
        caminho = item["arquivo"]
        if caminho in vistos:
            continue
        vistos.add(caminho)
        try:
            tamanho = motor_imagens.tamanho_imagem(caminho)
        except Exception:
            continue
        if excede(tamanho):
            grandes.append((caminho, tamanho))
    return grandes


def _reservar_arquivo(pasta, nome, extensao):
    """Cria (vazio) e devolve um arquivo novo na pasta, sem sobrescrever."""
    os.makedirs(pasta, exist_ok=True)
    candidato = os.path.join(pasta, nome + extensao)
    numero = 2
    while True:
        try:
            with open(candidato, "xb"):
                return candidato
        except FileExistsError:
            candidato = os.path.join(pasta, f"{nome} ({numero}){extensao}")
            numero += 1


def caminho_reduzido(origem, tamanho):
    base, extensao = os.path.splitext(os.path.basename(origem))
    nome = f"{base} ({tamanho[0]}x{tamanho[1]})"
    try:
        return _reservar_arquivo(os.path.dirname(origem), nome, extensao)
    except OSError:
        pasta = os.path.join(caminhos.pasta_dados_usuario(), "imagens_reduzidas")
        return _reservar_arquivo(pasta, nome, extensao)


def reduzir_imagens(caminhos_imagens, caixa, ao_progredir=None, ao_reduzir=None):
    """Reduz cada imagem para caber em `caixa`. `ao_reduzir(origem, nova)` e
    chamado a cada imagem concluida (util se uma imagem seguinte falhar);
    `ao_progredir(Progresso)` acompanha o andamento."""
    total = len(caminhos_imagens)
    for feitos, origem in enumerate(caminhos_imagens):
        if ao_progredir:
            ao_progredir(Progresso(ETAPA_IMAGENS, 1, 1, feitos, total))
        tamanho = tamanho_reduzido(motor_imagens.tamanho_imagem(origem), caixa)
        destino = caminho_reduzido(origem, tamanho)
        try:
            motor_imagens.reduzir_imagem(origem, destino, tamanho)
        except Exception:
            try:
                os.remove(destino)
            except OSError:
                pass
            raise
        if ao_reduzir:
            ao_reduzir(origem, destino)
    if ao_progredir:
        ao_progredir(Progresso(ETAPA_IMAGENS, 1, 1, total, total))
