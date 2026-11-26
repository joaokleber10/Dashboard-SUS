"""API FastAPI do dashboard. Rodar: python -m uvicorn src.app:app --reload --port 8000"""
from __future__ import annotations

import os
from datetime import date
from typing import Annotated, Literal, Optional

import duckdb
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError

try:  # .env local (no Docker as variáveis vêm do env_file)
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src import queries
from src.db import abrir_cursor, caminho_banco, get_db
from src.dictionary import meta_filtros
from src.export import gerar_csv, limite_export, nome_arquivo
from src.schemas import Filtros

app = FastAPI(title="Dashboard Epidemiológico SUS", version="0.1.0")

_origens = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_origens, allow_methods=["GET"], allow_headers=["*"])


@app.exception_handler(duckdb.CatalogException)
async def _tabela_ausente(_request, _exc):
    return JSONResponse(status_code=503, content={"detail": "Tabela 'internacoes' não encontrada. Execute o ETL: python -m src.etl"})


def filtros_dep(
    capitulo_ids: Annotated[list[str], Query()] = [],
    grupo_ids: Annotated[list[str], Query()] = [],
    cid_codigos: Annotated[list[str], Query()] = [],
    uf: Optional[str] = None,
    municipio: Optional[str] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    faixas_etarias: Annotated[list[str], Query()] = [],
    sexos: Annotated[list[str], Query()] = [],
    carater: Annotated[list[str], Query()] = [],
    complexidade: Annotated[list[str], Query()] = [],
    comparacao: Literal["periodo_anterior", "ano_anterior"] = "periodo_anterior",
) -> Filtros:
    try:
        return Filtros(capitulo_ids=capitulo_ids, grupo_ids=grupo_ids, cid_codigos=cid_codigos, uf=uf,
                       municipio=municipio, data_inicio=data_inicio, data_fim=data_fim,
                       faixas_etarias=faixas_etarias, sexos=sexos, carater=carater,
                       complexidade=complexidade, comparacao=comparacao)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=[
            {"campo": ".".join(str(p) for p in e["loc"]) or "filtros",
             "mensagem": str(e["msg"]).removeprefix("Value error, ")}
            for e in exc.errors()])


def _iso(d) -> Optional[str]:
    return None if d is None else d.isoformat()[:10]


@app.get("/health")
def health():
    existe = caminho_banco().exists()
    return {"status": "ok" if existe else "sem_dados", "banco": existe}


@app.get("/meta/filtros")
def meta(db=Depends(get_db)):
    """Opções dos seletores (dicionário) + o que existe de fato no banco."""
    dados = meta_filtros()
    dmin, dmax, cmin, cmax = db.execute(
        "SELECT min(data_internacao), max(data_internacao), min(competencia), max(competencia) FROM internacoes"
    ).fetchone()
    dados["periodo"] = {"data_min": _iso(dmin), "data_max": _iso(dmax),
                        "competencia_min": cmin, "competencia_max": cmax}
    dados["export_max_linhas"] = limite_export()
    dados["ufs_disponiveis"] = [r[0] for r in db.execute("SELECT DISTINCT uf FROM internacoes ORDER BY 1").fetchall()]
    return dados


@app.get("/kpis")
def get_kpis(f: Filtros = Depends(filtros_dep), db=Depends(get_db)):
    return queries.kpis(db, f)


@app.get("/serie-temporal")
def get_serie_temporal(
    agrupar_por: Literal["capitulo", "total"] = "capitulo",
    f: Filtros = Depends(filtros_dep),
    db=Depends(get_db),
):
    return queries.serie_temporal(db, f, agrupar_por)


@app.get("/demografia")
def get_demografia(f: Filtros = Depends(filtros_dep), db=Depends(get_db)):
    return queries.demografia(db, f)


@app.get("/top-cid")
def get_top_cid(
    limite: Annotated[int, Query(ge=1, le=50)] = 10,
    f: Filtros = Depends(filtros_dep),
    db=Depends(get_db),
):
    return queries.top_cid(db, f, limite)


@app.get("/export.csv")
def exportar_csv(separador: Literal[",", ";"] = ",", f: Filtros = Depends(filtros_dep)):
    """Dados filtrados em CSV (streaming). Limite de linhas: EXPORT_MAX_ROWS."""
    limite = limite_export()
    cur = abrir_cursor()
    try:
        total = queries.contar(cur, f)
        sql, params = queries.consulta_export(f, limite)
        cur.execute(sql, params)
        colunas = [c[0] for c in cur.description]
    except Exception:
        cur.close()
        raise
    cabecalhos = {
        "Content-Disposition": f'attachment; filename="{nome_arquivo(f)}"',
        "X-Total-Registros": str(total),
        "X-Registros-Exportados": str(min(total, limite)),
        "Access-Control-Expose-Headers": "Content-Disposition, X-Total-Registros, X-Registros-Exportados",
    }
    return StreamingResponse(gerar_csv(cur, colunas, separador), media_type="text/csv; charset=utf-8",
                             headers=cabecalhos)
