"""Catálogo opcional de nomes de CID-10 (categorias de 3 caracteres).

Ordem de preferência para o nome mostrado ao lado de cada código:
  1. refs/cid10.csv (opcional): nome exato da categoria (colunas CAT e DESCRICAO, como no DATASUS).
  2. src/cid10_blocos.py: nome do BLOCO que contém o código, ex.: I21 -> "Doenças isquêmicas do coração (bloco I20-I25)".
  3. Nada: a tela mostra só o código.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.dictionary import normalizar_cid

log = logging.getLogger("catalogos")
_COLUNAS_CODIGO = ("cat", "cid3", "categoria", "codigo", "cod", "cid", "subcat")
_COLUNAS_NOME = ("descricao", "descrabrev", "nome", "descricao_cid")


def _vazio() -> pd.DataFrame:
    return pd.DataFrame({"cid3": pd.Series(dtype="string"), "cid_nome": pd.Series(dtype="string")})


def catalogo_por_blocos(blocos=None) -> pd.DataFrame:
    """Expande os blocos da CID-10 (inicio..fim) em todas as categorias de 3 caracteres que eles cobrem."""
    if blocos is None:
        try:
            from src.cid10_blocos import BLOCOS_CID10 as blocos
        except ImportError:
            return _vazio()
    linhas = []
    for b in blocos:
        ini, fim = normalizar_cid(b.get("inicio")), normalizar_cid(b.get("fim"))
        chave = lambda c: (ord(c[0]) - 65) * 100 + int(c[1:])       # permite blocos que cruzam letras (X85-Y09)
        if not ini or not fim or chave(ini) > chave(fim):
            log.warning("CID-10: bloco inválido ignorado: %s", b.get("id"))
            continue
        for k in range(chave(ini), chave(fim) + 1):
            linhas.append((f"{chr(65 + k // 100)}{k % 100:02d}", f"{b['nome']} (bloco {b['id']})"))
    if not linhas:
        return _vazio()
    return pd.DataFrame(linhas, columns=["cid3", "cid_nome"]).drop_duplicates(subset="cid3").reset_index(drop=True)


def carregar_catalogo(caminho: Path, blocos=None) -> pd.DataFrame:
    """Catálogo final: o CSV (nome exato) tem prioridade; os blocos preenchem as categorias que ele não tem."""
    exato = carregar_cid10(caminho)
    por_bloco = catalogo_por_blocos(blocos)
    if len(exato) == 0:
        return por_bloco
    faltantes = por_bloco[~por_bloco["cid3"].isin(exato["cid3"])]
    return pd.concat([exato, faltantes], ignore_index=True)


def carregar_cid10(caminho: Path) -> pd.DataFrame:
    """Devolve DataFrame(cid3, cid_nome). Nunca levanta exceção: problema vira aviso e catálogo vazio."""
    if not caminho.is_file():
        return _vazio()
    df = None
    for codificacao in ("utf-8-sig", "latin-1"):
        try:
            df = pd.read_csv(caminho, sep=None, engine="python", encoding=codificacao, dtype=str)
            break
        except UnicodeDecodeError:
            continue
        except Exception as exc:
            log.warning("CID-10: não consegui ler %s (%s)", caminho, exc)
            return _vazio()
    if df is None:
        return _vazio()
    colunas = {str(c).strip().lower(): c for c in df.columns}
    col_codigo = next((colunas[k] for k in _COLUNAS_CODIGO if k in colunas), None)
    col_nome = next((colunas[k] for k in _COLUNAS_NOME if k in colunas), None)
    if col_codigo is None or col_nome is None:
        log.warning("CID-10: colunas de código/descrição não encontradas em %s (vistas: %s)", caminho, list(df.columns))
        return _vazio()
    codigos = df[col_codigo].astype("string").str.strip().str.upper().str.replace(".", "", regex=False)
    # Só categorias de 3 caracteres: nome de subcategoria (4 caracteres) não descreve a categoria.
    valido = codigos.map(lambda c: isinstance(c, str) and len(c) == 3 and normalizar_cid(c) == c)
    saida = pd.DataFrame({"cid3": codigos[valido], "cid_nome": df.loc[valido, col_nome].astype("string").str.strip()})
    saida = saida.dropna().drop_duplicates(subset="cid3").reset_index(drop=True)
    if saida.empty:
        log.warning("CID-10: %s não tem categorias de 3 caracteres (use CID-10-CATEGORIAS.CSV)", caminho)
    else:
        log.info("CID-10: %d categorias carregadas de %s", len(saida), caminho)
    return saida