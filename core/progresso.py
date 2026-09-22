# -*- coding: utf-8 -*-
"""Progresso de uma geracao de video, em etapas."""

ETAPA_AUDIO = "audio"
ETAPA_VIDEO = "video"


class Progresso:
    """Situacao de uma etapa da geracao: `feitos` de `total` unidades
    concluidas (blocos de audio ou quadros de video)."""

    def __init__(self, etapa, numero_etapa, total_etapas, feitos, total):
        self.etapa = etapa
        self.numero_etapa = numero_etapa
        self.total_etapas = total_etapas
        self.feitos = feitos
        self.total = total

    @property
    def percentual(self):
        """Percentual inteiro concluido da etapa, arredondado para baixo: so
        chega a 100 quando a ultima unidade termina."""
        if not self.total:
            return 0
        feitos = min(max(self.feitos, 0), self.total)
        return (100 * feitos) // self.total

    def __eq__(self, outro):
        return isinstance(outro, Progresso) and vars(self) == vars(outro)

    def __repr__(self):
        return (f"Progresso({self.etapa!r}, etapa {self.numero_etapa}/{self.total_etapas}, "
                f"{self.feitos}/{self.total} = {self.percentual}%)")
