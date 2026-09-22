# -*- coding: utf-8 -*-
"""Testes da deteccao e reducao de imagens grandes."""
import os

import pytest
from PIL import Image

from core.imagens import CAIXAS_REDUCAO, INDICE_REDUCAO_PADRAO, excede, tamanho_reduzido
from core.progresso import ETAPA_IMAGENS
from motor import imagens as motor_imagens
from servicos import imagens as servico_imagens

FULL_HD = CAIXAS_REDUCAO[INDICE_REDUCAO_PADRAO]


# --- core -------------------------------------------------------------------

@pytest.mark.parametrize("tamanho, grande", [
    ((3840, 2160), False), ((3841, 2160), True), ((3840, 2161), True),
    ((2160, 3840), False), ((2160, 3841), True),   # retrato: caixa 2160 x 3840
    ((3000, 3000), True),                          # quadrada: nao cabe em 2160 de altura
    ((5538, 3812), True), ((14028, 9829), True), ((1920, 1080), False),
])
def test_excede_4k_considerando_orientacao(tamanho, grande):
    assert excede(tamanho) is grande


@pytest.mark.parametrize("tamanho, esperado", [
    ((5538, 3812), (1569, 1080)),    # limitada pela altura
    ((14028, 9829), (1541, 1080)),
    ((8000, 2000), (1920, 480)),     # limitada pela largura
    ((3812, 5538), (1080, 1569)),    # retrato cabe em 1080 x 1920
    ((4000, 4000), (1080, 1080)),
    ((1280, 720), (1280, 720)),      # menor que a caixa: nao amplia
])
def test_tamanho_reduzido_full_hd(tamanho, esperado):
    assert tamanho_reduzido(tamanho, FULL_HD) == esperado


def test_tamanho_reduzido_sempre_cabe_na_caixa():
    for largura in range(3000, 9000, 137):
        for altura in (2001, 3333, 4999, 7777):
            w, h = tamanho_reduzido((largura, altura), FULL_HD)
            caixa = (1920, 1080) if largura >= altura else (1080, 1920)
            assert w <= caixa[0] and h <= caixa[1]
            assert w == caixa[0] or h == caixa[1]


# --- deteccao ---------------------------------------------------------------

def _imagem(caminho, tamanho, modo="RGB", **salvar):
    Image.new(modo, tamanho, 128 if modo in ("L", "P") else (10, 20, 30, 40)[:len(modo)]).save(caminho, **salvar)
    return str(caminho)


def test_imagens_grandes_so_imagens_grandes_sem_repetir(tmp_path):
    grande = _imagem(tmp_path / "grande.jpg", (4000, 2000))
    pequena = _imagem(tmp_path / "pequena.jpg", (1920, 1080))
    itens = [
        {"tipo": "imagem", "arquivo": grande},
        {"tipo": "imagem", "arquivo": pequena},
        {"tipo": "video", "arquivo": grande},            # videos nao entram
        {"tipo": "imagem", "arquivo": grande},            # repetida
        {"tipo": "imagem", "arquivo": str(tmp_path / "sumiu.jpg")},  # ilegivel
        {"arquivo": _imagem(tmp_path / "sem_tipo.png", (2200, 4000))},
    ]
    assert servico_imagens.imagens_grandes(itens) == [
        (grande, (4000, 2000)),
        (str(tmp_path / "sem_tipo.png"), (2200, 4000)),
    ]


def test_tamanho_imagem_ignora_limite_de_pixels_do_pillow(tmp_path, monkeypatch):
    caminho = _imagem(tmp_path / "a.png", (100, 100))
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 10)  # 10.000 px > 2 x 10
    assert motor_imagens.tamanho_imagem(caminho) == (100, 100)
    assert Image.MAX_IMAGE_PIXELS == 10  # limite restaurado


# --- reducao ----------------------------------------------------------------

def test_reduzir_preserva_formato_exif_e_perfil_e_nao_altera_original(tmp_path):
    exif = Image.Exif()
    exif[0x010F] = "Camera de teste"  # Make
    origem = _imagem(tmp_path / "foto.jpg", (5538, 3812), exif=exif.tobytes(),
                     icc_profile=b"perfil-de-cor-falso", quality=90)
    bytes_originais = open(origem, "rb").read()

    reduzidas, progresso = {}, []
    servico_imagens.reduzir_imagens([origem], FULL_HD, progresso.append, reduzidas.__setitem__)

    nova = reduzidas[origem]
    assert nova == str(tmp_path / "foto (1569x1080).jpg")
    with Image.open(nova) as im:
        assert (im.format, im.size, im.mode) == ("JPEG", (1569, 1080), "RGB")
        assert im.getexif()[0x010F] == "Camera de teste"
        assert im.info["icc_profile"] == b"perfil-de-cor-falso"
    assert open(origem, "rb").read() == bytes_originais
    assert [(p.etapa, p.feitos, p.total) for p in progresso] == [(ETAPA_IMAGENS, 0, 1), (ETAPA_IMAGENS, 1, 1)]


@pytest.mark.parametrize("modo, salvar", [("RGBA", {}), ("LA", {}), ("P", {"transparency": 0})])
def test_reduzir_png_mantem_transparencia(tmp_path, modo, salvar):
    origem = _imagem(tmp_path / "t.png", (4000, 3000), modo, **salvar)
    reduzidas = {}
    servico_imagens.reduzir_imagens([origem], FULL_HD, ao_reduzir=reduzidas.__setitem__)
    with Image.open(reduzidas[origem]) as im:
        assert im.format == "PNG" and im.size == (1440, 1080)
        assert im.mode in ("RGBA", "LA")


def test_nao_sobrescreve_arquivo_existente(tmp_path):
    origem = _imagem(tmp_path / "foto.jpg", (4000, 2000))
    existente = tmp_path / "foto (1920x960).jpg"
    existente.write_bytes(b"arquivo da pessoa")
    reduzidas = {}
    servico_imagens.reduzir_imagens([origem], FULL_HD, ao_reduzir=reduzidas.__setitem__)
    assert reduzidas[origem] == str(tmp_path / "foto (1920x960) (2).jpg")
    assert existente.read_bytes() == b"arquivo da pessoa"


def test_pasta_sem_permissao_usa_pasta_do_usuario(tmp_path, monkeypatch):
    origem = _imagem(tmp_path / "foto.jpg", (4000, 2000))
    dados = tmp_path / "dados_usuario"
    monkeypatch.setattr(servico_imagens.caminhos, "pasta_dados_usuario", lambda: str(dados))
    reservar = servico_imagens._reservar_arquivo

    def reservar_sem_permissao_na_origem(pasta, nome, extensao):
        if pasta == str(tmp_path):
            raise PermissionError("somente leitura")
        return reservar(pasta, nome, extensao)

    monkeypatch.setattr(servico_imagens, "_reservar_arquivo", reservar_sem_permissao_na_origem)
    reduzidas = {}
    servico_imagens.reduzir_imagens([origem], FULL_HD, ao_reduzir=reduzidas.__setitem__)
    assert reduzidas[origem] == str(dados / "imagens_reduzidas" / "foto (1920x960).jpg")
    assert os.path.exists(reduzidas[origem])


def test_falha_no_meio_mantem_as_ja_reduzidas_e_nao_deixa_arquivo_vazio(tmp_path):
    boa = _imagem(tmp_path / "boa.jpg", (4000, 2000))
    ruim = tmp_path / "ruim.jpg"
    ruim.write_bytes(open(boa, "rb").read()[:2000])  # jpeg truncado
    reduzidas = {}
    with pytest.raises(Exception):
        servico_imagens.reduzir_imagens([boa, str(ruim)], FULL_HD, ao_reduzir=reduzidas.__setitem__)
    assert list(reduzidas) == [boa]
    assert sorted(os.listdir(tmp_path)) == ["boa (1920x960).jpg", "boa.jpg", "ruim.jpg"]
