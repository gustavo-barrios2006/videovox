# -*- coding: utf-8 -*-
"""Midias pequenas geradas na hora para os testes dos servicos."""
import subprocess

import imageio_ffmpeg
import pytest
from PIL import Image

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def _ffmpeg(*args):
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", *args], check=True)


@pytest.fixture(scope="session")
def midias(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("midias")
    arquivos = {
        "foto": pasta / "foto.jpg",
        "transparente": pasta / "transparente_impar.png",
        "video": pasta / "video.mp4",
        "audio": pasta / "audio.wav",
    }
    Image.new("RGB", (400, 300), (30, 90, 160)).save(arquivos["foto"])
    Image.new("RGBA", (301, 201), (255, 0, 0, 128)).save(arquivos["transparente"])
    _ffmpeg("-f", "lavfi", "-i", "testsrc=size=320x240:rate=10",
            "-f", "lavfi", "-i", "sine=f=440:sample_rate=44100",
            "-t", "2", "-shortest", "-pix_fmt", "yuv420p", str(arquivos["video"]))
    _ffmpeg("-f", "lavfi", "-i", "sine=f=660:sample_rate=44100", "-t", "1.5", str(arquivos["audio"]))
    return {nome: str(caminho) for nome, caminho in arquivos.items()}
