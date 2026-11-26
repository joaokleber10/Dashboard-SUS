"""Conexão DuckDB somente leitura para a API.

O DuckDB aceita um único processo escritor (o ETL). A API abre o arquivo com
read_only=True e entrega um cursor por requisição (seguro entre threads).
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Iterator, Optional

import duckdb
from fastapi import HTTPException

_lock = threading.Lock()
_con: Optional[duckdb.DuckDBPyConnection] = None
_con_path: Optional[str] = None


def caminho_banco() -> Path:
    return Path(os.getenv("DUCKDB_PATH", "./data/sus.duckdb"))


def fechar() -> None:
    """Fecha a conexão compartilhada (usado em testes e no shutdown)."""
    global _con, _con_path
    with _lock:
        if _con is not None:
            _con.close()
        _con, _con_path = None, None


def _conexao() -> duckdb.DuckDBPyConnection:
    global _con, _con_path
    caminho = str(caminho_banco())
    with _lock:
        if _con is not None and _con_path != caminho:
            _con.close()
            _con = None
        if _con is None:
            _con = duckdb.connect(caminho, read_only=True)
            _con_path = caminho
        return _con


def abrir_cursor() -> duckdb.DuckDBPyConnection:
    """Cursor novo (quem abre fecha). Levanta 503 se o banco não existe."""
    if not caminho_banco().exists():
        raise HTTPException(status_code=503, detail="Banco de dados não encontrado. Execute o ETL: python -m src.etl")
    try:
        return _conexao().cursor()
    except duckdb.Error as exc:
        raise HTTPException(status_code=503, detail=f"Não foi possível abrir o banco: {exc}")


def get_db() -> Iterator[duckdb.DuckDBPyConnection]:
    """Dependência do FastAPI: um cursor por requisição."""
    cur = abrir_cursor()
    try:
        yield cur
    finally:
        cur.close()
