# -*- coding: utf-8 -*-
"""Arquivo de projeto .wvp: um zip com o project.json e as midias usadas.

Formato (version 1):
    project.json  -> {"version", "fps", "tamanho_quadro", "imagens", "audios"}
    media/<nome>  -> copia de cada arquivo; cada item guarda o caminho em
                     "zip_path". Nomes repetidos ganham sufixo "(1)", "(2)"...
"""
import json
import os
import uuid
import zipfile

VERSAO_FORMATO = 1


def _verificar_arquivos_existem(imagens, audios):
    for item in imagens:
        if not os.path.exists(item["arquivo"]):
            raise FileNotFoundError(f"Arquivo não encontrado: {item['arquivo']}")
    for item in audios:
        if not os.path.exists(item["arquivo"]):
            raise FileNotFoundError(f"Arquivo não encontrado: {item['arquivo']}")


def _copiar_para_zip(zip_file, itens, path_to_zip_name, used_zip_names):
    """Grava no zip os arquivos ainda nao gravados e devolve copias dos itens
    com o "zip_path" de cada um."""
    itens_copy = []
    for item in itens:
        orig_path = item["arquivo"]
        if orig_path not in path_to_zip_name:
            base_name = os.path.basename(orig_path)
            name, ext = os.path.splitext(base_name)
            zip_name = f"media/{base_name}"
            counter = 1
            while zip_name in used_zip_names:
                zip_name = f"media/{name}({counter}){ext}"
                counter += 1
            used_zip_names.add(zip_name)
            path_to_zip_name[orig_path] = zip_name
            zip_file.write(orig_path, zip_name)

        item_data = item.copy()
        item_data["zip_path"] = path_to_zip_name[orig_path]
        itens_copy.append(item_data)
    return itens_copy


def salvar_projeto(destino, imagens, audios, fps_texto, tamanho_quadro):
    _verificar_arquivos_existem(imagens, audios)

    with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        path_to_zip_name = {}
        used_zip_names = set()

        imagens_copy = _copiar_para_zip(
            zip_file, imagens, path_to_zip_name, used_zip_names
        )
        audios_copy = _copiar_para_zip(
            zip_file, audios, path_to_zip_name, used_zip_names
        )

        project_data = {
            "version": VERSAO_FORMATO,
            "fps": fps_texto,
            "tamanho_quadro": tamanho_quadro,
            "imagens": imagens_copy,
            "audios": audios_copy
        }

        zip_file.writestr("project.json", json.dumps(project_data, indent=4, ensure_ascii=False))


class ProjetoCarregado:
    """Resultado de carregar_projeto. `temp_dir` e a pasta temporaria onde
    midias foram extraidas, ou None se nenhuma precisou ser extraida."""

    def __init__(self, fps, tamanho_quadro, imagens, audios, temp_dir):
        self.fps = fps
        self.tamanho_quadro = tamanho_quadro
        self.imagens = imagens
        self.audios = audios
        self.temp_dir = temp_dir


def _resolver_itens(zip_file, itens_raw, temp_dir, extraidos):
    """Aponta cada item para o arquivo original, se ainda existir, ou para a
    copia extraida do zip. `extraidos` e uma lista de um booleano, marcado
    quando algum arquivo precisa ser extraido."""
    novos = []
    for item in itens_raw:
        orig_file = item.get("arquivo")
        zip_path = item.get("zip_path")

        if orig_file and os.path.exists(orig_file):
            resolved_path = orig_file
        elif zip_path:
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)
            resolved_path = zip_file.extract(zip_path, temp_dir)
            extraidos[0] = True
        else:
            raise FileNotFoundError(f"Não foi possível encontrar o arquivo original ou zip_path.")

        item_copy = item.copy()
        item_copy["arquivo"] = resolved_path
        item_copy.pop("zip_path", None)
        novos.append(item_copy)
    return novos


def carregar_projeto(caminho_projeto, pasta_temp_projetos):
    session_id = uuid.uuid4().hex
    temp_dir = os.path.join(pasta_temp_projetos, session_id)

    with zipfile.ZipFile(caminho_projeto, 'r') as zip_file:
        project_json = zip_file.read("project.json").decode('utf-8')
        project_data = json.loads(project_json)

        fps_val = project_data.get("fps", "30")
        tamanho_quadro_val = project_data.get(
            "tamanho_quadro", "maior_altura_largura"
        )
        imagens_raw = project_data.get("imagens", [])
        audios_raw = project_data.get("audios", [])

        extraidos = [False]
        novas_imagens = _resolver_itens(zip_file, imagens_raw, temp_dir, extraidos)
        novos_audios = _resolver_itens(zip_file, audios_raw, temp_dir, extraidos)

    return ProjetoCarregado(
        fps_val,
        tamanho_quadro_val,
        novas_imagens,
        novos_audios,
        temp_dir if extraidos[0] else None
    )
