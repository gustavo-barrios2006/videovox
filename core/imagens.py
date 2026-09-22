# -*- coding: utf-8 -*-
"""Regras de tamanho das imagens: quando uma imagem e grande demais para gerar
o video com seguranca, e para que tamanho reduzi-la.

As caixas de tamanho sao orientadas como a imagem: uma imagem em pe (retrato)
e comparada com 2160 x 3840, e nao com 3840 x 2160.
"""

# Acima disso (4K UHD) a geracao do video pede varios GiB de memoria.
LIMITE_IMAGEM_GRANDE = (3840, 2160)

# (rotulo exibido, caixa (largura, altura) em paisagem)
OPCOES_REDUCAO = [
    ("HD (1280 × 720)", (1280, 720)),
    ("Full HD (1920 × 1080)", (1920, 1080)),
    ("2K (2560 × 1440)", (2560, 1440)),
    ("4K (3840 × 2160)", (3840, 2160)),
]
ROTULOS_REDUCAO = [op[0] for op in OPCOES_REDUCAO]
CAIXAS_REDUCAO = [op[1] for op in OPCOES_REDUCAO]
INDICE_REDUCAO_PADRAO = 1  # Full HD


def _caixa_orientada(tamanho, caixa):
    largura, altura = tamanho
    maior, menor = max(caixa), min(caixa)
    if altura > largura:
        return menor, maior
    return maior, menor


def excede(tamanho, limite=LIMITE_IMAGEM_GRANDE):
    """True se a imagem nao cabe na caixa `limite` (na mesma orientacao)."""
    largura, altura = tamanho
    limite_largura, limite_altura = _caixa_orientada(tamanho, limite)
    return largura > limite_largura or altura > limite_altura


def tamanho_reduzido(tamanho, caixa):
    """Maior tamanho que cabe na `caixa` mantendo a proporcao. Nunca amplia."""
    largura, altura = tamanho
    caixa_largura, caixa_altura = _caixa_orientada(tamanho, caixa)
    escala = min(caixa_largura / largura, caixa_altura / altura, 1)
    return max(1, round(largura * escala)), max(1, round(altura * escala))
