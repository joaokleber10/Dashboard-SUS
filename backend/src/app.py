"""API FastAPI do dashboard. Rodar: python -m uvicorn src.app:app --reload --port 8000"""
from __future__ import annotations

import os
from datetime import date, datetime, timezone
from typing import Annotated, Literal, Optional

import duckdb
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import ValidationError

try:  # .env local (no Docker as variáveis vêm do env_file)
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src import queries
from src.db import abrir_cursor, caminho_banco, get_db
from src.dictionary import meta_filtros, resolver_cid, uf_valida
from src.geo import ler_malha
from src.export import gerar_csv, limite_export, nome_arquivo
from src.schemas import Filtros

app = FastAPI(title="Dashboard Epidemiológico SUS", version="0.1.0")

_origens = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=_origens, allow_methods=["GET"], allow_headers=["*"])
app.add_middleware(GZipMiddleware, minimum_size=1000)


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
    fontes: Annotated[list[str], Query()] = [],
    municipio_ref: Literal["residencia", "atendimento"] = "residencia",
    comparacao: Literal["nenhuma", "periodo_anterior", "ano_anterior"] = "periodo_anterior",
) -> Filtros:
    try:
        return Filtros(capitulo_ids=capitulo_ids, grupo_ids=grupo_ids, cid_codigos=cid_codigos, uf=uf,
                       municipio=municipio, data_inicio=data_inicio, data_fim=data_fim,
                       faixas_etarias=faixas_etarias, sexos=sexos, carater=carater,
                       complexidade=complexidade, fontes=fontes, municipio_ref=municipio_ref,
                       comparacao=comparacao)
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
                        "competencia_min": cmin, "competencia_max": cmax,
                        "fonte": "SIH/SUS (RD — DATASUS)",
                        "ultima_atualizacao": datetime.fromtimestamp(caminho_banco().stat().st_mtime, tz=timezone.utc).isoformat()}
    dados["export_max_linhas"] = limite_export()
    dados["foco"] = queries.foco_local(db, os.getenv("FOCO_UF", ""), os.getenv("FOCO_MUNICIPIO", ""))
    tem_fonte = db.execute("SELECT count(*) FROM information_schema.columns WHERE table_name = 'internacoes' AND column_name = 'fonte'").fetchone()[0]
    dados["fontes_disponiveis"] = [
        {"id": r[0], "casos": int(r[1])}
        for r in db.execute("SELECT fonte, count(*) FROM internacoes GROUP BY 1 ORDER BY 2 DESC").fetchall()
    ] if tem_fonte else []
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
        sql, params = queries.consulta_export(f, limite, queries.colunas_tabela(cur))
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


@app.get("/municipios")
def get_municipios(
    ordenar_por: Literal["casos", "obitos", "taxa_mortalidade", "permanencia_media", "custo_total", "nome"] = "casos",
    ordem: Literal["asc", "desc"] = "desc",
    pagina: Annotated[int, Query(ge=1)] = 1,
    por_pagina: Annotated[int, Query(ge=1, le=200)] = 25,
    busca: Annotated[Optional[str], Query(max_length=60)] = None,
    f: Filtros = Depends(filtros_dep),
    db=Depends(get_db),
):
    """Tabela de municípios (ordenável, paginada). O filtro de município é ignorado de propósito."""
    return queries.municipios(db, f, ordenar_por, ordem, pagina, por_pagina, busca)


@app.get("/municipios/mapa")
def get_municipios_mapa(f: Filtros = Depends(filtros_dep), db=Depends(get_db)):
    """Todos os municípios do recorte (para o mapa coroplético e para a lista do painel)."""
    return queries.mapa_municipios(db, f)


@app.get("/geojson")
def get_geojson(uf: Optional[str] = None, db=Depends(get_db)):
    """Malha municipal da UF, servida do cache local (baixada do IBGE pelo ETL)."""
    sigla = (uf or "").strip().upper()
    if not sigla:
        ufs = [r[0] for r in db.execute("SELECT DISTINCT uf FROM internacoes ORDER BY 1").fetchall()]
        if len(ufs) != 1:
            raise HTTPException(status_code=422, detail="Informe a UF (?uf=PB).")
        sigla = ufs[0]
    if not uf_valida(sigla):
        raise HTTPException(status_code=422, detail=f"UF inexistente: {sigla!r}")
    conteudo = ler_malha(sigla)
    if conteudo is None:
        raise HTTPException(status_code=404, detail="Malha geográfica indisponível. Rode o ETL com acesso à internet: python -m src.etl")
    return Response(content=conteudo, media_type="application/geo+json", headers={"Cache-Control": "public, max-age=86400"})


@app.get("/cid/buscar")
def get_cid_buscar(
    q: Annotated[str, Query(max_length=40)] = "",
    limite: Annotated[int, Query(ge=1, le=50)] = 20,
    f: Filtros = Depends(filtros_dep),
    db=Depends(get_db),
):
    """Subcategorias CID-10 presentes nos dados que combinam com a busca (código ou nome)."""
    return queries.buscar_cid(db, f, q, limite)


@app.get("/cid/grupos")
def get_cid_grupos(f: Filtros = Depends(filtros_dep), db=Depends(get_db)):
    """Blocos oficiais da CID-10 presentes nos dados (com contagem), ignorando os filtros de grupo e CID."""
    return queries.grupos_dinamicos(db, f)


@app.get("/cid/resolver")
def get_cid_resolver(codigo: str = Query(..., min_length=1)):
    """Resolve um código CID-10 digitado para categoria, capítulo, bloco e grupo prioritário."""
    res = resolver_cid(codigo)
    if res is None:
        return {"valido": False, "cid3": None, "capitulo": None, "bloco": None, "grupo_prioritario": None}
    return {"valido": True, **res}
