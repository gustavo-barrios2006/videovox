# -*- coding: utf-8 -*-
"""Testes das regras puras (sem wx e sem MoviePy)."""
import pytest

from core.cortes import intervalos_mantidos
from core.layout import calcular_quadro, normalizar_fps
from core.linha_do_tempo import (
    descrever_audios,
    descrever_midias,
    duracao_midia,
    duracao_recorte_audio,
)
from core.opcoes import (
    CHAVES_AJUSTE_IMAGEM,
    CHAVES_TAMANHO_QUADRO,
    POSICAO_AJUSTE_IMAGEM,
    indice_ajuste_imagem,
    indice_tamanho_quadro,
)
from core.validacao import validar_numero


# --- validacao --------------------------------------------------------------

@pytest.mark.parametrize("texto", ["0", "2", "10", "1.5", " 3.25 ", "007"])
def test_validar_numero_aceita(texto):
    assert validar_numero(texto)


@pytest.mark.parametrize("texto", ["", " ", "abc", "-1", "1.", ".5", "1,5", "1e3", "+2", "1.2.3"])
def test_validar_numero_rejeita(texto):
    assert not validar_numero(texto)


# --- opcoes -----------------------------------------------------------------

def test_indices_com_chave_desconhecida_voltam_ao_padrao():
    assert indice_ajuste_imagem("nao_existe") == 0
    assert indice_tamanho_quadro("nao_existe") == 0
    assert indice_ajuste_imagem("inf_dir") == CHAVES_AJUSTE_IMAGEM.index("inf_dir")
    assert indice_tamanho_quadro("full_hd_vertical") == CHAVES_TAMANHO_QUADRO.index("full_hd_vertical")


def test_preencher_nao_tem_posicao_fixa():
    assert POSICAO_AJUSTE_IMAGEM["preencher"] is None
    assert POSICAO_AJUSTE_IMAGEM["centralizar"] == "center"


# --- cortes -----------------------------------------------------------------

def test_intervalos_mantidos_ordena_e_mescla_sobrepostos():
    cortes = [(2.0, 2.5), (0.5, 1.0), (0.8, 1.2)]
    assert intervalos_mantidos(cortes, 3.0) == [(0, 0.5), (1.2, 2.0), (2.5, 3.0)]


def test_intervalos_mantidos_sem_cortes_mantem_tudo():
    assert intervalos_mantidos([], 5.0) == [(0, 5.0)]


def test_intervalos_mantidos_corte_ate_o_fim():
    assert intervalos_mantidos([(1.0, 99.0)], 3.0) == [(0, 1.0)]


def test_intervalos_mantidos_tudo_cortado():
    assert intervalos_mantidos([(0.0, 10.0)], 3.0) == []


# --- layout -----------------------------------------------------------------

def test_normalizar_fps():
    assert normalizar_fps(None) == 30
    assert normalizar_fps(0) == 30
    assert normalizar_fps(-5) == 30
    assert normalizar_fps(24) == 24


def test_quadro_maior_altura_e_largura_independentes():
    assert calcular_quadro([(400, 300), (300, 500)], "maior_altura_largura") == (400, 500)


def test_quadro_maior_midia_por_area_primeira_vence_empate():
    assert calcular_quadro([(400, 300), (300, 500)], "maior_midia") == (300, 500)
    assert calcular_quadro([(600, 100), (100, 600)], "maior_midia") == (600, 100)


@pytest.mark.parametrize("modo, esperado", [
    ("full_hd_horizontal", (1920, 1080)),
    ("full_hd_vertical", (1080, 1920)),
])
def test_quadro_resolucoes_padrao(modo, esperado):
    assert calcular_quadro([(401, 301)], modo) == esperado


def test_quadro_sempre_par_e_no_minimo_2():
    assert calcular_quadro([(401, 301)], "maior_altura_largura") == (400, 300)
    assert calcular_quadro([], "maior_altura_largura") == (2, 2)
    assert calcular_quadro([(1, 1)], "maior_midia") == (2, 2)


# --- linha do tempo ---------------------------------------------------------

def _imagem(arquivo, duracao, inicio_destino=None):
    return {"tipo": "imagem", "arquivo": arquivo, "duracao": duracao,
            "inicio_destino": inicio_destino, "ajuste_imagem": "preencher"}


def _video(arquivo, inicio, fim, inicio_destino=None, silenciado=False):
    item = {"tipo": "video", "arquivo": arquivo, "inicio": inicio, "fim": fim,
            "inicio_destino": inicio_destino, "ajuste_imagem": "preencher"}
    if silenciado:
        item["silenciado"] = True
    return item


def test_duracao_midia():
    assert duracao_midia(_imagem("a.jpg", 2.5)) == 2.5
    assert duracao_midia(_video("v.mp4", 1.0, 3.5)) == 2.5
    assert duracao_midia({"arquivo": "sem_tipo.jpg", "duracao": 4}) == 4


def test_descrever_midias_sequencia_e_posicao_fixa():
    itens = [
        _imagem(r"C:\m\foto.jpg", 2.0),
        _imagem("b.png", 1.5, inicio_destino=0.5),
        _video("v.mp4", 0.5, 3.0, silenciado=True),
        _video("w.mp4", 0.0, 1.5, inicio_destino=10.0),
        _imagem("c.jpg", 1.0),
    ]
    assert descrever_midias(itens) == [
        "Imagem: foto.jpg duração 2.0s -> final 0s-2.0s",
        # posicao fixa antes do fim anterior nao "volta" a sequencia
        "Imagem: b.png duração 1.5s -> final 0.5s-2.0s",
        "Vídeo: v.mp4 (Silenciado) original 0.5s-3.0s -> final 2.0s-4.5s",
        "Vídeo: w.mp4 original 0.0s-1.5s -> final 10.0s-11.5s",
        # depois de um item posicionado adiante, a sequencia continua dele
        "Imagem: c.jpg duração 1.0s -> final 11.5s-12.5s",
    ]


def test_duracao_recorte_audio():
    assert duracao_recorte_audio({"inicio": 0.5, "fim": None}, 3.0) == 2.5
    assert duracao_recorte_audio({"inicio": 0.5, "fim": 1.0}, 3.0) == 0.5
    assert duracao_recorte_audio({"inicio": 0.0, "fim": 9.0}, 3.0) == 3.0
    assert duracao_recorte_audio({"inicio": 2.0, "fim": 1.0}, 3.0) == 0.0


def test_descrever_audios_sequencia_e_posicao():
    audios = [
        {"arquivo": "a.mp3", "inicio": 0.0, "fim": None, "pos": None},
        {"arquivo": "b.wav", "inicio": 0.5, "fim": 1.0, "pos": 1.0},
        {"arquivo": "c.mp3", "inicio": 1.0, "fim": None, "pos": None},
    ]
    duracoes = {"a.mp3": 2.5, "b.wav": 0.5, "c.mp3": 1.5}
    assert descrever_audios(audios, lambda item: duracoes[item["arquivo"]]) == [
        "a.mp3 (0.0s-Fim) em 0s (sequência) no vídeo",
        "b.wav (0.5s-1.0s) em 1.0s no vídeo",
        "c.mp3 (1.0s-Fim) em 1.5s (sequência) no vídeo",
    ]
