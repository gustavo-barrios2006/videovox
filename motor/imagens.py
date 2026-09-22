# -*- coding: utf-8 -*-
"""Leitura do tamanho e reducao de arquivos de imagem (Pillow)."""
import contextlib

from PIL import Image


@contextlib.contextmanager
def _sem_limite_de_pixels():
    # O Pillow recusa imagens acima de ~179 megapixels (protecao contra
    # "decompression bomb"). Aqui as imagens grandes sao justamente o alvo.
    anterior = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = None
    try:
        yield
    finally:
        Image.MAX_IMAGE_PIXELS = anterior


def tamanho_imagem(caminho):
    """(largura, altura) lidos do cabecalho, sem carregar os pixels."""
    with _sem_limite_de_pixels(), Image.open(caminho) as imagem:
        return imagem.size


def _tem_transparencia(imagem):
    return imagem.mode in ("RGBA", "LA", "PA") or "transparency" in imagem.info


def reduzir_imagem(origem, destino, tamanho):
    """Grava em `destino` a imagem redimensionada para `tamanho`, no mesmo
    formato, preservando transparencia, perfil de cor e EXIF."""
    with _sem_limite_de_pixels(), Image.open(origem) as imagem:
        formato = imagem.format
        extras = {}
        for chave in ("exif", "icc_profile"):
            if imagem.info.get(chave):
                extras[chave] = imagem.info[chave]

        if imagem.mode not in ("RGB", "RGBA", "L", "LA", "CMYK", "I", "F"):
            imagem = imagem.convert("RGBA" if _tem_transparencia(imagem) else "RGB")
        reduzida = imagem.resize(tamanho, Image.Resampling.LANCZOS)

        if formato == "JPEG":
            if reduzida.mode not in ("RGB", "L", "CMYK"):
                reduzida = reduzida.convert("RGB")
            extras["quality"] = 95
        reduzida.save(destino, format=formato, **extras)
