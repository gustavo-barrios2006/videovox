# -*- coding: utf-8 -*-
"""Traducao do progresso reportado pelo MoviePy (via proglog) para Progresso.

Ao exportar, o MoviePy grava primeiro o audio, em blocos (barra "chunk"), e
depois os quadros do video (barra "frame_index"). Cada barra informa o total
antes de comecar e o indice a cada item: o percentual e exato, sem estimativa
de tempo.
"""
import proglog

from core.progresso import ETAPA_AUDIO, ETAPA_VIDEO, Progresso

_ETAPA_DA_BARRA = {"chunk": ETAPA_AUDIO, "frame_index": ETAPA_VIDEO}


class RelatorDeProgresso(proglog.ProgressBarLogger):
    """Logger do MoviePy que chama `ao_progredir(Progresso)` quando a etapa ou
    o percentual inteiro mudam. Com audio, sao duas etapas (audio e depois
    video); sem audio, so a do video."""

    def __init__(self, ao_progredir, com_audio):
        super().__init__(logged_bars=None)
        self.ao_progredir = ao_progredir
        self.etapas = [ETAPA_AUDIO, ETAPA_VIDEO] if com_audio else [ETAPA_VIDEO]
        self._ultimo = None

    def bars_callback(self, bar, attr, value, old_value=None):
        etapa = _ETAPA_DA_BARRA.get(bar)
        if etapa not in self.etapas or attr not in ("index", "total"):
            return
        dados = self.bars[bar]
        if not dados.get("total"):
            return
        progresso = Progresso(
            etapa,
            self.etapas.index(etapa) + 1,
            len(self.etapas),
            max(dados["index"], 0),
            dados["total"],
        )
        chave = (progresso.etapa, progresso.percentual)
        if chave != self._ultimo:
            self._ultimo = chave
            self.ao_progredir(progresso)


def logger_para(ao_progredir, com_audio):
    """Logger a passar ao write_videofile: o padrao do MoviePy (barra no
    console) quando ninguem acompanha o progresso."""
    if ao_progredir is None:
        return "bar"
    return RelatorDeProgresso(ao_progredir, com_audio)
