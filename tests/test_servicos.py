# -*- coding: utf-8 -*-
"""Testes dos casos de uso, com midias reais pequenas (sem wx)."""
import json
import os
import zipfile

import pytest
from moviepy import VideoFileClip

from servicos import midias as servico_midias
from servicos import projeto_io
from servicos.cortes import processar_cortes
from servicos.mixagem import gerar_video_final
from servicos.renderizacao import criar_video


def _info(caminho):
    with VideoFileClip(caminho) as clip:
        return clip.size, round(clip.duration, 1), clip.fps, clip.audio is not None


def _itens(midias):
    return [
        {"tipo": "imagem", "arquivo": midias["foto"], "duracao": 1.0,
         "inicio_destino": None, "ajuste_imagem": "preencher"},
        {"tipo": "imagem", "arquivo": midias["transparente"], "duracao": 0.5,
         "inicio_destino": 0.2, "ajuste_imagem": "sup_dir"},
        {"tipo": "video", "arquivo": midias["video"], "inicio": 0.5, "fim": 1.5,
         "inicio_destino": None, "ajuste_imagem": "preencher"},
    ]


# --- renderizacao -----------------------------------------------------------

@pytest.mark.parametrize("modo, tamanho", [
    ("maior_altura_largura", [400, 300]),
    ("maior_midia", [400, 300]),
    ("full_hd_vertical", [1080, 1920]),
])
def test_criar_video_tamanho_duracao_e_audio(midias, tmp_path, modo, tamanho):
    destino = str(tmp_path / "base.mp4")
    criar_video(destino, _itens(midias), 10, modo)
    # foto 0-1s, png 0.2-0.7s, video em sequencia 1-2s (com audio do video)
    assert _info(destino) == (tamanho, 2.0, 10, True)


def test_criar_video_silenciado_fica_sem_audio(midias, tmp_path):
    itens = _itens(midias)
    itens[2]["silenciado"] = True
    destino = str(tmp_path / "mudo.mp4")
    criar_video(destino, itens, 0, "maior_altura_largura")
    assert _info(destino) == ([400, 300], 2.0, 30, False)


def test_criar_video_arquivo_inexistente_propaga_erro(midias, tmp_path):
    itens = _itens(midias)
    itens[0]["arquivo"] = str(tmp_path / "sumiu.jpg")
    with pytest.raises(FileNotFoundError):
        criar_video(str(tmp_path / "x.mp4"), itens, 10, "maior_altura_largura")


# --- mixagem e cortes -------------------------------------------------------

def test_gerar_video_final_estende_ate_o_ultimo_audio(midias, tmp_path):
    destino = str(tmp_path / "final.mp4")
    audios = [
        {"arquivo": midias["audio"], "inicio": 0.0, "fim": None, "pos": None},
        {"arquivo": midias["audio"], "inicio": 0.5, "fim": 1.0, "pos": 2.5},
    ]
    gerar_video_final(midias["video"], audios, destino)
    size, duracao, _, tem_audio = _info(destino)
    assert size == [320, 240] and tem_audio
    assert duracao == 3.0


def test_processar_cortes(midias, tmp_path):
    destino = str(tmp_path / "cortado.mp4")
    assert processar_cortes(midias["video"], [(0.5, 1.0)], destino, "ultrafast") is True
    assert _info(destino)[1] == 1.5


def test_processar_cortes_tudo_cortado_nao_gera_arquivo(midias, tmp_path):
    destino = str(tmp_path / "vazio.mp4")
    assert processar_cortes(midias["video"], [(0.0, 99.0)], destino, "ultrafast") is False
    assert not os.path.exists(destino)


def test_duracao_recorte_audio_guarda_duracao_original(midias):
    item = {"arquivo": midias["audio"], "inicio": 0.5, "fim": None, "pos": None}
    assert servico_midias.obter_duracao_recorte_audio(item) == pytest.approx(1.0)
    assert item["duracao_original"] == pytest.approx(1.5)


def test_duracao_recorte_audio_arquivo_invalido_vale_zero(tmp_path):
    item = {"arquivo": str(tmp_path / "nao.mp3"), "inicio": 0.0, "fim": None, "pos": None}
    assert servico_midias.obter_duracao_recorte_audio(item) == 0.0
    assert "duracao_original" not in item


# --- projeto .wvp -----------------------------------------------------------

def test_salvar_e_carregar_projeto_ida_e_volta(midias, tmp_path):
    imagens = _itens(midias)
    audios = [{"arquivo": midias["audio"], "inicio": 0.0, "fim": None, "pos": 1.0,
               "duracao_original": 1.5}]
    destino = str(tmp_path / "proj.wvp")
    projeto_io.salvar_projeto(destino, imagens, audios, "24", "full_hd_horizontal")

    with zipfile.ZipFile(destino) as z:
        dados = json.loads(z.read("project.json").decode("utf-8"))
        assert sorted(z.namelist()) == sorted(
            ["project.json", "media/foto.jpg", "media/transparente_impar.png",
             "media/video.mp4", "media/audio.wav"])
    assert dados["version"] == 1
    assert dados["fps"] == "24" and dados["tamanho_quadro"] == "full_hd_horizontal"

    projeto = projeto_io.carregar_projeto(destino, str(tmp_path / "temp_projects"))
    # arquivos originais existem: nada e extraido
    assert projeto.temp_dir is None
    assert projeto.imagens == imagens and projeto.audios == audios
    assert (projeto.fps, projeto.tamanho_quadro) == ("24", "full_hd_horizontal")


def test_nomes_repetidos_ganham_sufixo(midias, tmp_path):
    outra_pasta = tmp_path / "outra"
    outra_pasta.mkdir()
    copia = outra_pasta / "foto.jpg"
    copia.write_bytes(open(midias["foto"], "rb").read())
    imagens = [
        {"tipo": "imagem", "arquivo": midias["foto"], "duracao": 1.0},
        {"tipo": "imagem", "arquivo": str(copia), "duracao": 1.0},
        {"tipo": "imagem", "arquivo": midias["foto"], "duracao": 2.0},
    ]
    destino = str(tmp_path / "dup.wvp")
    projeto_io.salvar_projeto(destino, imagens, [], "30", "maior_altura_largura")
    with zipfile.ZipFile(destino) as z:
        salvos = json.loads(z.read("project.json").decode("utf-8"))["imagens"]
    assert [i["zip_path"] for i in salvos] == ["media/foto.jpg", "media/foto(1).jpg", "media/foto.jpg"]


def test_carregar_extrai_midias_quando_originais_sumiram(midias, tmp_path):
    destino = str(tmp_path / "proj.wvp")
    projeto_io.salvar_projeto(destino, _itens(midias), [], "30", "maior_altura_largura")

    # reescreve o project.json apontando para arquivos que nao existem mais
    movido = str(tmp_path / "movido.wvp")
    with zipfile.ZipFile(destino) as zin, zipfile.ZipFile(movido, "w") as zout:
        for info in zin.infolist():
            dados = zin.read(info.filename)
            if info.filename == "project.json":
                pj = json.loads(dados.decode("utf-8"))
                for it in pj["imagens"]:
                    it["arquivo"] = str(tmp_path / "sumiu" / os.path.basename(it["arquivo"]))
                del pj["tamanho_quadro"]
                dados = json.dumps(pj).encode("utf-8")
            zout.writestr(info, dados)

    temp = str(tmp_path / "temp_projects")
    projeto = projeto_io.carregar_projeto(movido, temp)
    assert projeto.temp_dir is not None and projeto.temp_dir.startswith(temp)
    assert projeto.tamanho_quadro == "maior_altura_largura"
    for item in projeto.imagens:
        assert item["arquivo"].startswith(projeto.temp_dir)
        assert os.path.exists(item["arquivo"])
        assert "zip_path" not in item


def test_salvar_projeto_com_arquivo_inexistente(tmp_path):
    imagens = [{"tipo": "imagem", "arquivo": str(tmp_path / "nao.jpg"), "duracao": 1.0}]
    with pytest.raises(FileNotFoundError, match="Arquivo não encontrado"):
        projeto_io.salvar_projeto(str(tmp_path / "p.wvp"), imagens, [], "30", "maior_altura_largura")
    assert not os.path.exists(tmp_path / "p.wvp")


def test_carregar_projeto_sem_arquivo_nem_zip_path(tmp_path):
    caminho = str(tmp_path / "quebrado.wvp")
    with zipfile.ZipFile(caminho, "w") as z:
        z.writestr("project.json", json.dumps({"imagens": [{"tipo": "imagem", "duracao": 1}]}))
    with pytest.raises(FileNotFoundError):
        projeto_io.carregar_projeto(caminho, str(tmp_path / "temp_projects"))
