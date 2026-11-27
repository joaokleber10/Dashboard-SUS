"""Municípios e malha geográfica do IBGE: baixa uma vez (no ETL), guarda em DATA_DIR/geo e serve do cache.

A API nunca fala com o IBGE: /geojson e as consultas de município leem só arquivos e tabelas locais.
Falha de rede não derruba o ETL: o mapa fica indisponível e a tabela mostra o código no lugar do nome.
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
from pathlib import Path
from typing import Callable, Optional

from src.dictionary import UF_POR_SIGLA, UFS, municipio6

log = logging.getLogger("geo")

URL_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"
URL_MALHA = ("https://servicodados.ibge.gov.br/api/v3/malhas/estados/{codigo}"
             "?formato=application/vnd.geo+json&intrarregiao=municipio&qualidade=minima")
# Propriedades onde o IBGE costuma colocar o código do município na malha (testadas nesta ordem).
_CHAVES_CODIGO = ("codarea", "CD_MUN", "cd_mun", "codigo", "geocodigo", "id")


def pasta_geo() -> Path:
    return Path(os.getenv("DATA_DIR", "./data")) / "geo"


def baixar_json(url: str, tentativas: int = 3, timeout: int = 60):
    ultimo: Optional[Exception] = None
    for i in range(1, tentativas + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "sus-dashboard/0.1"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            ultimo = exc
            log.warning("Falha ao baixar %s (tentativa %d/%d): %s", url, i, tentativas, exc)
            time.sleep(2 * i)
    raise RuntimeError(f"Não foi possível baixar {url}") from ultimo


# ---------------------------------------------------------------- normalização
def normalizar_municipios(payload, sigla: str) -> list[dict]:
    """Resposta de /localidades/estados/{UF}/municipios -> [{codigo6, municipio_nome, municipio_uf}]."""
    saida = []
    for item in payload if isinstance(payload, list) else []:
        if not isinstance(item, dict):
            continue
        codigo, nome = municipio6(item.get("id")), item.get("nome")
        if codigo and nome:
            saida.append({"codigo6": codigo, "municipio_nome": str(nome).strip(), "municipio_uf": sigla})
    return saida


def extrair_codigo(props, codigo_uf: int) -> Optional[str]:
    """Acha, nas propriedades da feição, o código do município (6 dígitos, sem o verificador)."""
    if not isinstance(props, dict):
        return None
    prefixo = str(codigo_uf)
    ordem = [k for k in _CHAVES_CODIGO if k in props] + [k for k in props if k not in _CHAVES_CODIGO]
    for chave in ordem:
        valor = props[chave]
        if isinstance(valor, bool) or not isinstance(valor, (str, int)):
            continue
        s = str(valor).strip()
        if s.isdigit() and len(s) in (6, 7) and s.startswith(prefixo):
            return s[:6]
    return None


def normalizar_malha(geojson, codigo_uf: int) -> dict:
    """Mantém só polígonos com código reconhecido e reduz as propriedades a {"codigo": "250750"}."""
    feicoes = []
    brutas = geojson.get("features", []) if isinstance(geojson, dict) else []
    for ft in brutas:
        geom = ft.get("geometry") if isinstance(ft, dict) else None
        codigo = extrair_codigo(ft.get("properties") if isinstance(ft, dict) else None, codigo_uf)
        if codigo and isinstance(geom, dict) and geom.get("type") in ("Polygon", "MultiPolygon"):
            feicoes.append({"type": "Feature", "properties": {"codigo": codigo}, "geometry": geom})
    return {"type": "FeatureCollection", "features": feicoes}


# ------------------------------------------------------------------- arquivos
def _gravar_json(destino: Path, objeto) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(destino.suffix + ".tmp")
    tmp.write_text(json.dumps(objeto, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, destino)  # atômico


def garantir_municipios(pasta: Path, forcar: bool = False,
                        baixar: Callable = baixar_json) -> dict:
    """Nomes de TODOS os municípios (27 UFs): moradores de outras UFs também aparecem com nome."""
    destino = pasta / "municipios.json"
    if destino.exists() and not forcar:
        return {"ok": True, "cache": True, "total": len(carregar_municipios(pasta))}
    todos: list[dict] = []
    falhas: list[str] = []
    for uf in UFS:
        try:
            todos += normalizar_municipios(baixar(URL_MUNICIPIOS.format(uf=uf["sigla"])), uf["sigla"])
        except Exception as exc:
            falhas.append(uf["sigla"])
            log.warning("Municípios de %s não baixados: %s", uf["sigla"], exc)
    if not todos:
        return {"ok": False, "erro": "nenhum município baixado (sem internet?)", "falhas": falhas}
    _gravar_json(destino, todos)
    if falhas:
        log.warning("Municípios incompletos (faltam %s). Rode o ETL com --refresh-geo para completar.", falhas)
    return {"ok": True, "total": len(todos), "falhas": falhas}


def garantir_malha(pasta: Path, sigla: str, forcar: bool = False,
                   baixar: Callable = baixar_json) -> dict:
    destino = pasta / f"malha_{sigla}.geojson"
    if destino.exists() and not forcar:
        return {"ok": True, "cache": True}
    codigo = UF_POR_SIGLA[sigla]["codigo"]
    try:
        bruto = baixar(URL_MALHA.format(codigo=codigo))
        malha = normalizar_malha(bruto, codigo)
        if not malha["features"]:
            primeira = (bruto.get("features") or [{}])[0] if isinstance(bruto, dict) else {}
            props = list((primeira.get("properties") or {}).keys()) if isinstance(primeira, dict) else []
            raise ValueError(f"malha sem municípios reconhecidos (propriedades vistas: {props})")
    except Exception as exc:
        log.warning("Malha de %s indisponível: %s", sigla, exc)
        return {"ok": False, "erro": str(exc)}
    _gravar_json(destino, malha)
    return {"ok": True, "feicoes": len(malha["features"])}


def carregar_municipios(pasta: Optional[Path] = None) -> list[dict]:
    arquivo = (pasta or pasta_geo()) / "municipios.json"
    if not arquivo.is_file():
        return []
    try:
        return json.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        log.warning("municipios.json ilegível; ignorando")
        return []


def ler_malha(sigla: str, pasta: Optional[Path] = None) -> Optional[bytes]:
    arquivo = (pasta or pasta_geo()) / f"malha_{sigla}.geojson"
    return arquivo.read_bytes() if arquivo.is_file() else None