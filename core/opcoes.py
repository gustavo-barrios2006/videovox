# -*- coding: utf-8 -*-
"""Opcoes fixas do VideoVox (ajuste da midia e tamanho do quadro)."""

# Opcoes de ajuste de imagem no quadro final.
# (rotulo exibido, chave salva no item, posicao do MoviePy)
# "preencher" (padrao) redimensiona a imagem mantendo a proporcao para
# preencher o quadro e a centraliza. As demais opcoes mantem a imagem no
# tamanho original, apenas posicionando-a no quadro.
OPCOES_AJUSTE_IMAGEM = [
    ("Preencher quadro", "preencher", None),
    ("Centralizar", "centralizar", "center"),
    ("Superior esquerdo", "sup_esq", ("left", "top")),
    ("Superior centro", "sup_centro", ("center", "top")),
    ("Superior direito", "sup_dir", ("right", "top")),
    ("Centro esquerdo", "centro_esq", ("left", "center")),
    ("Centro direito", "centro_dir", ("right", "center")),
    ("Inferior esquerdo", "inf_esq", ("left", "bottom")),
    ("Inferior centro", "inf_centro", ("center", "bottom")),
    ("Inferior direito", "inf_dir", ("right", "bottom")),
]

ROTULOS_AJUSTE_IMAGEM = [op[0] for op in OPCOES_AJUSTE_IMAGEM]
CHAVES_AJUSTE_IMAGEM = [op[1] for op in OPCOES_AJUSTE_IMAGEM]
POSICAO_AJUSTE_IMAGEM = {op[1]: op[2] for op in OPCOES_AJUSTE_IMAGEM}


# Opcoes de tamanho do quadro (resolucao) do video final.
# (rotulo exibido, chave)
# "maior_altura_largura": o quadro usa a maior largura e a maior
#   altura encontradas entre as midias, calculadas de forma independente (pode
#   nao corresponder a resolucao de nenhuma midia individual).
# "maior_midia": o quadro usa a resolucao exata da maior midia (por area).
# "full_hd_horizontal"/"full_hd_vertical": o quadro usa uma resolucao padrao de
#   proporcao 16:9 (1920x1080) ou 9:16 (1080x1920). Diferente da resolucao da
#   tela de quem gera, essas proporcoes padrao fazem o video cobrir a area de
#   exibicao na maioria dos dispositivos (o player escala o arquivo na
#   reproducao), como os videos comuns.
# Em qualquer modo, o ajuste "Preencher quadro" estica a midia ate ocupar todo
# o quadro final.
OPCOES_TAMANHO_QUADRO = [
    ("Maior largura e maior altura entre as mídias", "maior_altura_largura"),
    ("Tamanho da maior mídia", "maior_midia"),
    ("Full HD horizontal (1920×1080)", "full_hd_horizontal"),
    ("Full HD vertical (1080×1920)", "full_hd_vertical"),
]

ROTULOS_TAMANHO_QUADRO = [op[0] for op in OPCOES_TAMANHO_QUADRO]
CHAVES_TAMANHO_QUADRO = [op[1] for op in OPCOES_TAMANHO_QUADRO]

# Resolucoes fixas (largura, altura) dos modos de proporcao padrao.
RESOLUCOES_PADRAO = {
    "full_hd_horizontal": (1920, 1080),
    "full_hd_vertical": (1080, 1920),
}

# Presets do libx264 por indice da escolha de qualidade na aba Editar.
# 0: Alta (veryslow / compressao maxima)
# 1: Media (medium)
# 2: Baixa (ultrafast / compressao minima)
PRESETS_QUALIDADE = ["veryslow", "medium", "ultrafast"]


def indice_ajuste_imagem(chave):
    try:
        return CHAVES_AJUSTE_IMAGEM.index(chave)
    except ValueError:
        return 0


def indice_tamanho_quadro(chave):
    try:
        return CHAVES_TAMANHO_QUADRO.index(chave)
    except ValueError:
        return 0
