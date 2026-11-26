"""Exportação CSV: nome do arquivo, limite de linhas e geração em streaming."""
from __future__ import annotations

import csv
import io
import os
from typing import Iterator, Sequence

LIMITE_PADRAO = 500_000


def limite_export() -> int:
    """Máximo de linhas por arquivo (EXPORT_MAX_ROWS no .env); valor inválido cai no padrão."""
    try:
        valor = int(os.getenv("EXPORT_MAX_ROWS", str(LIMITE_PADRAO)))
    except ValueError:
        return LIMITE_PADRAO
    return valor if valor > 0 else LIMITE_PADRAO


def nome_arquivo(f) -> str:
    partes = ["internacoes"]
    if f.uf:
        partes.append(f.uf)
    if f.data_inicio or f.data_fim:
        partes.append(f"{f.data_inicio or 'inicio'}_{f.data_fim or 'fim'}")
    return "_".join(partes) + ".csv"


def gerar_csv(cur, colunas: Sequence[str], separador: str = ",", lote: int = 5000) -> Iterator[str]:
    """Gera o CSV aos poucos (fetchmany) e SEMPRE fecha o cursor, mesmo se o cliente cancelar.

    Começa com BOM UTF-8 para o Excel reconhecer os acentos.
    """
    try:
        buf = io.StringIO()
        escritor = csv.writer(buf, delimiter=separador, lineterminator="\n")
        escritor.writerow(colunas)
        yield "\ufeff" + buf.getvalue()
        while True:
            linhas = cur.fetchmany(lote)
            if not linhas:
                break
            buf.seek(0)
            buf.truncate(0)
            escritor.writerows(linhas)
            yield buf.getvalue()
    finally:
        cur.close()
