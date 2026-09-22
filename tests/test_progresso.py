# -*- coding: utf-8 -*-
"""Testes do progresso da geracao de video."""
import os

import pytest

from core.progresso import ETAPA_AUDIO, ETAPA_VIDEO, Progresso
from motor.progresso import RelatorDeProgresso, logger_para
from servicos.mixagem import gerar_video_final
from servicos.renderizacao import criar_video


# --- core -------------------------------------------------------------------

@pytest.mark.parametrize("feitos, total, esperado", [
    (0, 120, 0), (1, 120, 0), (59, 120, 49), (60, 120, 50),
    (119, 120, 99), (120, 120, 100), (130, 120, 100), (-1, 120, 0), (5, 0, 0),
])
def test_percentual_exato_arredondado_para_baixo(feitos, total, esperado):
    assert Progresso(ETAPA_VIDEO, 1, 1, feitos, total).percentual == esperado


# --- motor: traducao das barras do proglog -----------------------------------

def _simular(relator, barra, total):
    """Reproduz o que o proglog faz em iter_bar: total, cada indice e o fim."""
    for i in relator.iter_bar(**{barra: list(range(total))}):
        pass


def test_relator_com_audio_tem_duas_etapas_e_so_avisa_mudancas():
    eventos = []
    relator = RelatorDeProgresso(eventos.append, com_audio=True)
    _simular(relator, "chunk", 50)
    _simular(relator, "frame_index", 300)

    audio = [e for e in eventos if e.etapa == ETAPA_AUDIO]
    video = [e for e in eventos if e.etapa == ETAPA_VIDEO]
    assert eventos == audio + video
    assert {(e.numero_etapa, e.total_etapas) for e in audio} == {(1, 2)}
    assert {(e.numero_etapa, e.total_etapas) for e in video} == {(2, 2)}
    for etapa in (audio, video):
        percentuais = [e.percentual for e in etapa]
        assert percentuais[0] == 0 and percentuais[-1] == 100
        assert percentuais == sorted(set(percentuais))  # crescente, sem repetir
    # 300 quadros: um aviso por ponto percentual (0 a 100)
    assert len(video) == 101
    assert video[-1].feitos == video[-1].total == 300


def test_relator_sem_audio_tem_uma_etapa_e_ignora_outras_barras():
    eventos = []
    relator = RelatorDeProgresso(eventos.append, com_audio=False)
    _simular(relator, "chunk", 10)  # nao deveria acontecer, mas e ignorado
    _simular(relator, "t", 10)
    _simular(relator, "frame_index", 40)
    assert {(e.etapa, e.numero_etapa, e.total_etapas) for e in eventos} == {(ETAPA_VIDEO, 1, 1)}
    assert eventos[-1].percentual == 100


def test_relator_nao_guarda_log_por_quadro():
    relator = RelatorDeProgresso(lambda p: None, com_audio=False)
    _simular(relator, "frame_index", 1000)
    assert relator.logs == []


def test_logger_para():
    assert logger_para(None, com_audio=True) == "bar"
    assert isinstance(logger_para(print, com_audio=True), RelatorDeProgresso)


# --- servicos: progresso real de uma exportacao -------------------------------

def _etapas(eventos):
    return [(e.etapa, e.numero_etapa, e.total_etapas) for e in eventos]


def test_criar_video_reporta_quadros_exatos(midias, tmp_path):
    itens = [
        {"tipo": "imagem", "arquivo": midias["foto"], "duracao": 1.0, "inicio_destino": None},
        {"tipo": "video", "arquivo": midias["video"], "inicio": 0.0, "fim": 1.5, "inicio_destino": None},
    ]
    eventos = []
    criar_video(str(tmp_path / "a.mp4"), itens, 12, "maior_altura_largura", eventos.append)
    assert list(dict.fromkeys(_etapas(eventos))) == [(ETAPA_AUDIO, 1, 2), (ETAPA_VIDEO, 2, 2)]
    ultimo_video = [e for e in eventos if e.etapa == ETAPA_VIDEO][-1]
    assert ultimo_video.total == 30  # 2,5 s x 12 fps
    assert ultimo_video.feitos == 30 and ultimo_video.percentual == 100


def test_criar_video_sem_audio_tem_so_a_etapa_do_video(midias, tmp_path):
    itens = [{"tipo": "imagem", "arquivo": midias["foto"], "duracao": 2.0, "inicio_destino": None}]
    eventos = []
    criar_video(str(tmp_path / "b.mp4"), itens, 10, "maior_altura_largura", eventos.append)
    assert set(_etapas(eventos)) == {(ETAPA_VIDEO, 1, 1)}
    assert eventos[0].percentual == 0 and eventos[-1].percentual == 100
    assert eventos[-1].total == 20


def test_gerar_video_final_reporta_audio_e_video(midias, tmp_path):
    eventos = []
    audios = [{"arquivo": midias["audio"], "inicio": 0.0, "fim": None, "pos": None}]
    gerar_video_final(midias["video"], audios, str(tmp_path / "c.mp4"), eventos.append)
    assert list(dict.fromkeys(_etapas(eventos))) == [(ETAPA_AUDIO, 1, 2), (ETAPA_VIDEO, 2, 2)]
    assert eventos[-1].percentual == 100
    assert os.path.exists(tmp_path / "c.mp4")
