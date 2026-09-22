# -*- coding: utf-8 -*-
"""Registro de erros no erro.txt, para diagnostico.

O arquivo fica ao lado do executavel (onde o usuario encontra facilmente).
Se essa pasta nao permitir escrita (ex.: Arquivos de Programas), vai para
%LOCALAPPDATA%\\VideoVox e, por ultimo, para a pasta temporaria do sistema.
Cada erro e acrescentado ao fim do arquivo, com data e operacao.
"""
import datetime
import os
import sys
import tempfile
import threading
import traceback

from infra import caminhos

NOME_ARQUIVO = "erro.txt"


def _pastas_candidatas():
    return [
        caminhos.pasta_do_executavel(),
        caminhos.pasta_dados_usuario(),
        tempfile.gettempdir(),
    ]


def registrar_erro(operacao, exc_info=None):
    """Grava o traceback no erro.txt e devolve o caminho do arquivo, ou None
    se nao foi possivel gravar em nenhuma pasta. Nunca lanca excecao: quem
    registra um erro nao pode falhar por causa do registro.

    Sem `exc_info`, usa a excecao em tratamento (chame de dentro do except).
    """
    try:
        if exc_info is None:
            detalhes = traceback.format_exc()
        else:
            detalhes = "".join(traceback.format_exception(*exc_info))
        agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        texto = f"==== {agora} - {operacao} ====\n{detalhes}\n"
    except Exception:
        return None

    for pasta in _pastas_candidatas():
        try:
            os.makedirs(pasta, exist_ok=True)
            caminho = os.path.join(pasta, NOME_ARQUIVO)
            with open(caminho, "a", encoding="utf-8") as f:
                f.write(texto)
            return caminho
        except Exception:
            continue
    return None


def mensagem_com_registro(mensagem, caminho_registro):
    """Acrescenta a mensagem de erro exibida ao usuario onde os detalhes foram
    gravados."""
    if not caminho_registro:
        return mensagem
    return f"{mensagem}\n\nOs detalhes do erro foram salvos em:\n{caminho_registro}"


def instalar_registro_de_erros_inesperados():
    """Registra no erro.txt excecoes nao tratadas: em eventos da interface
    (o wxPython as repassa ao sys.excepthook) e em threads."""
    excepthook_anterior = sys.excepthook
    threading_excepthook_anterior = threading.excepthook

    def excepthook(tipo, valor, tb):
        registrar_erro("Erro inesperado", (tipo, valor, tb))
        excepthook_anterior(tipo, valor, tb)

    def threading_excepthook(args):
        if not issubclass(args.exc_type, SystemExit):
            registrar_erro(
                "Erro inesperado em segundo plano",
                (args.exc_type, args.exc_value, args.exc_traceback),
            )
        threading_excepthook_anterior(args)

    sys.excepthook = excepthook
    threading.excepthook = threading_excepthook
