# -*- coding: utf-8 -*-
"""Regras de tempo das midias e audios: duracoes, sequencia no video destino
e os textos exibidos nas listas."""
import os


def duracao_midia(item):
    if item.get("tipo", "imagem") == "video":
        return item["fim"] - item["inicio"]

    return item["duracao"]


def duracao_recorte_audio(item, duracao_original):
    t_inicio = item["inicio"]
    t_fim = item["fim"] if item["fim"] is not None else duracao_original
    return max(0.0, min(t_fim, duracao_original) - t_inicio)


def descrever_midias(itens):
    """Textos da lista de midias. Itens sem inicio no destino entram em
    sequencia, logo apos o fim mais tardio das midias anteriores."""
    descricoes = []
    inicio_destino = 0

    for item in itens:
        duracao = duracao_midia(item)
        if item.get("inicio_destino") is not None:
            inicio_item_destino = item["inicio_destino"]
        else:
            inicio_item_destino = inicio_destino

        fim_destino = inicio_item_destino + duracao
        nome = os.path.basename(item["arquivo"])

        if item.get("tipo", "imagem") == "video":
            silenciado_str = " (Silenciado)" if item.get("silenciado") else ""
            descricao = (
                f"Vídeo: {nome}{silenciado_str} "
                f"original {item['inicio']}s-{item['fim']}s "
                f"-> final {inicio_item_destino}s-{fim_destino}s"
            )
        else:
            descricao = (
                f"Imagem: {nome} "
                f"duração {item['duracao']}s "
                f"-> final {inicio_item_destino}s-{fim_destino}s"
            )

        descricoes.append(descricao)
        inicio_destino = max(inicio_destino, fim_destino)

    return descricoes


def descrever_audios(audios, obter_duracao_recorte):
    """Textos da lista de audios. `obter_duracao_recorte(item)` devolve a
    duracao do recorte de cada audio; audios sem inicio no video entram em
    sequencia, logo apos o fim do audio anterior."""
    descricoes = []
    posicao_atual = 0
    for info in audios:
        nome = os.path.basename(info["arquivo"])
        fim_desc = f"{info['fim']}s" if info['fim'] is not None else "Fim"

        if info["pos"] is not None:
            pos_calculada = info["pos"]
        else:
            pos_calculada = posicao_atual

        duracao_recorte = obter_duracao_recorte(info)
        posicao_atual = pos_calculada + duracao_recorte

        if info["pos"] is not None:
            pos_desc = f"{pos_calculada}s"
        else:
            pos_desc = f"{pos_calculada}s (sequência)"

        descricoes.append(f"{nome} ({info['inicio']}s-{fim_desc}) em {pos_desc} no vídeo")

    return descricoes
