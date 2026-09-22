# -*- coding: utf-8 -*-
"""Testes do registro de erros (erro.txt) e das pastas do app."""
import sys
import threading

import pytest

from infra import caminhos, log


@pytest.fixture
def pastas(tmp_path, monkeypatch):
    """Direciona as pastas candidatas do erro.txt para pastas de teste."""
    exe, dados, temp = tmp_path / "exe", tmp_path / "dados", tmp_path / "temp"
    exe.mkdir()
    monkeypatch.setattr(caminhos, "pasta_do_executavel", lambda: str(exe))
    monkeypatch.setattr(caminhos, "pasta_dados_usuario", lambda: str(dados))
    monkeypatch.setattr(log.tempfile, "gettempdir", lambda: str(temp))
    return exe, dados, temp


def _falhar(mensagem):
    try:
        raise ValueError(mensagem)
    except ValueError:
        return log.registrar_erro("Operação de teste")


def test_registra_ao_lado_do_executavel_e_acumula(pastas):
    exe, _, _ = pastas
    assert _falhar("primeiro") == str(exe / "erro.txt")
    assert _falhar("segundo") == str(exe / "erro.txt")
    texto = (exe / "erro.txt").read_text(encoding="utf-8")
    assert texto.count("- Operação de teste ====") == 2
    assert "ValueError: primeiro" in texto and "ValueError: segundo" in texto


def test_pasta_sem_permissao_cai_para_dados_do_usuario(pastas, monkeypatch):
    exe, dados, _ = pastas
    abrir_original = open

    def abrir(caminho, *args, **kwargs):
        if str(caminho).startswith(str(exe)):
            raise PermissionError("somente leitura")
        return abrir_original(caminho, *args, **kwargs)

    monkeypatch.setattr("builtins.open", abrir)
    assert _falhar("sem permissao") == str(dados / "erro.txt")
    assert "sem permissao" in (dados / "erro.txt").read_text(encoding="utf-8")


def test_nunca_lanca_excecao_mesmo_sem_nenhuma_pasta_gravavel(pastas, monkeypatch):
    def abrir(*args, **kwargs):
        raise PermissionError("nada gravavel")

    monkeypatch.setattr("builtins.open", abrir)
    assert _falhar("perdido") is None


def test_registra_exc_info_explicito(pastas):
    exe, _, _ = pastas
    try:
        raise KeyError("fora do except")
    except KeyError:
        info = sys.exc_info()
    assert log.registrar_erro("Explícito", info) == str(exe / "erro.txt")
    assert "KeyError: 'fora do except'" in (exe / "erro.txt").read_text(encoding="utf-8")


def test_mensagem_com_registro():
    assert log.mensagem_com_registro("Falhou.", None) == "Falhou."
    assert log.mensagem_com_registro("Falhou.", r"C:\app\erro.txt") == (
        "Falhou.\n\nOs detalhes do erro foram salvos em:\nC:\\app\\erro.txt"
    )


def test_erros_inesperados_sao_registrados(pastas, monkeypatch):
    exe, _, _ = pastas
    chamados = []
    monkeypatch.setattr(sys, "excepthook", lambda *a: chamados.append("sys"))
    monkeypatch.setattr(threading, "excepthook", lambda a: chamados.append("thread"))
    log.instalar_registro_de_erros_inesperados()

    try:
        raise RuntimeError("no evento")
    except RuntimeError:
        sys.excepthook(*sys.exc_info())

    def falha_na_thread():
        raise RuntimeError("na thread")

    t = threading.Thread(target=falha_na_thread)
    t.start()
    t.join()

    def sai_da_thread():
        raise SystemExit

    t = threading.Thread(target=sai_da_thread)
    t.start()
    t.join()

    texto = (exe / "erro.txt").read_text(encoding="utf-8")
    assert "RuntimeError: no evento" in texto and "RuntimeError: na thread" in texto
    assert "SystemExit" not in texto
    # os hooks anteriores continuam sendo chamados
    assert chamados == ["sys", "thread", "thread"]


def test_pasta_do_executavel(monkeypatch, tmp_path):
    caminhos.definir_pasta_programa(str(tmp_path / "fonte"))
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert caminhos.pasta_do_executavel() == str(tmp_path / "fonte")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "dist" / "videovox.exe"))
    assert caminhos.pasta_do_executavel() == str(tmp_path / "dist")
