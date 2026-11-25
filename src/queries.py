"""SQL dos KPIs e gráficos. Valores sempre por parâmetro (?); colunas são fixas no código."""
from __future__ import annotations

import csv
import io
import unicodedata
from datetime import date, timedelta
from typing import TYPE_CHECKING, Optional

from src.dictionary import (
    BLOCO_POR_ID, CAPITULOS, FAIXAS_ETARIAS, cid_to_bloco, municipio6, municipio_nome,
)

if TYPE_CHECKING:
    from src.schemas import Filtros

TABELA = "internacoes"
_NOMES_CAPITULO = {c["id"]: c["nome"] for c in CAPITULOS}
_NOMES_CAPITULO["ND"] = "Sem CID válido"


# ------------------------------------------------------------------ WHERE
def build_where(f: "Filtros", incluir_cid: bool = True,
                periodo: Optional[tuple[date, date]] = None) -> tuple[str, list]:
    """Monta a cláusula WHERE parametrizada.

    incluir_cid=False ignora capítulo/grupo/CID (denominador do "total geral").
    periodo substitui data_inicio/data_fim (usado no período de comparação).
    """
    conds: list[str] = []
    params: list = []

    def add_in(coluna: str, valores: list[str]) -> None:
        if valores:
            conds.append(f"{coluna} IN ({','.join(['?'] * len(valores))})")
            params.extend(valores)

    if incluir_cid:
        add_in("capitulo_id", f.capitulo_ids)
        if f.grupo_ids:
            grupos_legado = [g for g in f.grupo_ids if g not in BLOCO_POR_ID]
            blocos = [BLOCO_POR_ID[g] for g in f.grupo_ids if g in BLOCO_POR_ID]
            partes: list[str] = []
            g_params: list = []
            if grupos_legado:
                partes.append(f"grupo_id IN ({','.join(['?'] * len(grupos_legado))})")
                g_params.extend(grupos_legado)
            for bloco in blocos:
                partes.append("(cid3 >= ? AND cid3 <= ?)")
                g_params.extend([bloco["inicio"], bloco["fim"]])
            if len(partes) == 1 and grupos_legado:
                conds.append(partes[0])
            elif partes:
                conds.append("(" + " OR ".join(partes) + ")")
            params.extend(g_params)
        add_in("cid3", f.cid_codigos)
    if f.uf:
        conds.append("uf = ?")
        params.append(f.uf)
    if f.municipio:
        conds.append("municipio_res = ?")
        params.append(f.municipio)
    inicio, fim = periodo if periodo is not None else (f.data_inicio, f.data_fim)
    if inicio:
        conds.append("data_internacao >= ?")
        params.append(inicio)
    if fim:
        conds.append("data_internacao < ?")  # fim inclusivo: dia seguinte, exclusivo
        params.append(fim + timedelta(days=1))
    add_in("faixa_etaria", f.faixas_etarias)
    add_in("sexo", f.sexos)
    add_in("carater", f.carater)
    add_in("complexidade", f.complexidade)
    return (" WHERE " + " AND ".join(conds)) if conds else "", params


# ----------------------------------------------------------------- helpers
def _menos_um_ano(d: date) -> date:
    try:
        return d.replace(year=d.year - 1)
    except ValueError:  # 29/02
        return d.replace(year=d.year - 1, day=28)


def _ultimo_dia_do_mes(d: date) -> date:
    primeiro_do_proximo = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return primeiro_do_proximo - timedelta(days=1)


def _meses_completos(inicio: date, fim: date) -> Optional[int]:
    """Nº de meses se [inicio, fim] cobre meses de calendário inteiros; senão None."""
    if inicio.day == 1 and fim == _ultimo_dia_do_mes(fim):
        return (fim.year - inicio.year) * 12 + fim.month - inicio.month + 1
    return None


def periodo_anterior(f: "Filtros") -> Optional[tuple[date, date]]:
    """Período de comparação; None se o usuário não informou as duas datas.

    - ano_anterior: mesmo recorte um ano antes (YoY).
    - periodo_anterior: se o recorte são meses de calendário inteiros, os mesmos
      meses imediatamente antes (julho -> junho inteiro); caso contrário, a mesma
      quantidade de dias imediatamente antes.
    """
    if f.comparacao == "nenhuma" or not (f.data_inicio and f.data_fim):
        return None
    if f.comparacao == "ano_anterior":
        return _menos_um_ano(f.data_inicio), _menos_um_ano(f.data_fim)
    n = _meses_completos(f.data_inicio, f.data_fim)
    if n is not None:
        y, m = divmod(f.data_inicio.year * 12 + f.data_inicio.month - 1 - n, 12)
        return date(y, m + 1, 1), f.data_inicio - timedelta(days=1)
    dias = (f.data_fim - f.data_inicio).days + 1
    return f.data_inicio - timedelta(days=dias), f.data_inicio - timedelta(days=1)


def _pct(parte, todo) -> Optional[float]:
    return round(100 * parte / todo, 2) if todo else None


def _num(x) -> Optional[float]:
    return None if x is None else round(float(x), 2)


def _var_pct(atual, anterior) -> Optional[float]:
    if atual is None or not anterior:
        return None
    return round((atual - anterior) / anterior * 100, 2)


def meses_entre(inicio: str, fim: str) -> list[str]:
    """['2023-01', ..., '2023-03'] a partir de 'AAAA-MM'."""
    y, m = map(int, inicio.split("-"))
    yf, mf = map(int, fim.split("-"))
    out = []
    while (y, m) <= (yf, mf):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


# -------------------------------------------------------------------- KPIs
def _agregados(db, where: str, params: list) -> dict:
    total, obitos, perm, custo_total, custo_medio, muns = db.execute(
        f"""SELECT count(*), count(*) FILTER (WHERE obito), avg(dias_perm), sum(val_tot), avg(val_tot),
                   count(DISTINCT municipio_res)
            FROM {TABELA}{where}""", params).fetchone()
    return {
        "total": int(total),
        "obitos": int(obitos),
        "taxa_mortalidade": _pct(obitos, total),
        "permanencia_media": _num(perm),
        "custo_total": _num(custo_total),
        "custo_medio": _num(custo_medio),
        "municipios_atendidos": int(muns or 0),
    }


def kpis(db, f: "Filtros") -> dict:
    where, params = build_where(f)
    atual = _agregados(db, where, params)

    w_geral, p_geral = build_where(f, incluir_cid=False)
    total_geral = int(db.execute(f"SELECT count(*) FROM {TABELA}{w_geral}", p_geral).fetchone()[0])
    atual["total_geral"] = total_geral
    atual["proporcao_total_geral"] = _pct(atual["total"], total_geral)

    anterior = variacao = periodo_ant = None
    per = periodo_anterior(f)
    if per:
        w2, p2 = build_where(f, periodo=per)
        anterior = _agregados(db, w2, p2)
        periodo_ant = {"inicio": per[0].isoformat(), "fim": per[1].isoformat()}
        variacao = {k: _var_pct(atual[k], anterior[k])
                    for k in ("total", "obitos", "permanencia_media", "custo_total", "custo_medio")}
        ta, tb = atual["taxa_mortalidade"], anterior["taxa_mortalidade"]
        variacao["taxa_mortalidade_pp"] = None if ta is None or tb is None else round(ta - tb, 2)
    return {"atual": atual, "anterior": anterior, "variacao_pct": variacao,
            "periodo_anterior": periodo_ant, "comparacao": f.comparacao}


# ----------------------------------------------------------- série temporal
def serie_temporal(db, f: "Filtros", agrupar_por: str = "capitulo") -> dict:
    where, params = build_where(f)
    if agrupar_por == "capitulo":
        serie_sql = "coalesce(capitulo_id, 'ND')"
    else:
        serie_sql = "'TOTAL'"
    linhas = db.execute(
        f"""SELECT ano_mes, {serie_sql} AS serie, count(*) AS casos, count(*) FILTER (WHERE obito) AS obitos
            FROM {TABELA}{where} GROUP BY 1, 2 ORDER BY 1, 2""", params).fetchall()
    if not linhas:
        return {"agrupar_por": agrupar_por, "meses": [], "series": []}

    dados = {(mes, serie): (int(casos), int(obitos)) for mes, serie, casos, obitos in linhas}
    ordem_meses = sorted({mes for mes, _ in dados})
    ini = f.data_inicio.strftime("%Y-%m") if f.data_inicio else ordem_meses[0]
    fim = f.data_fim.strftime("%Y-%m") if f.data_fim else ordem_meses[-1]
    meses = meses_entre(min(ini, ordem_meses[0]), max(fim, ordem_meses[-1]))
    series_ids = sorted({serie for _, serie in dados})
    series = [{
        "id": sid,
        "nome": "Total" if sid == "TOTAL" else _NOMES_CAPITULO.get(sid, sid),
        "pontos": [{"ano_mes": m, "casos": dados.get((m, sid), (0, 0))[0],
                    "obitos": dados.get((m, sid), (0, 0))[1]} for m in meses],
    } for sid in series_ids]
    return {"agrupar_por": agrupar_por, "meses": meses, "series": series}


# --------------------------------------------------------- pirâmide etária
def demografia(db, f: "Filtros") -> dict:
    """Contagem por faixa etária x sexo (M, F, I). Faixas sem casos vêm com zero."""
    where, params = build_where(f)
    linhas = db.execute(
        f"SELECT faixa_etaria, sexo, count(*) FROM {TABELA}{where} GROUP BY 1, 2", params).fetchall()
    tabela = {fx["id"]: {"M": 0, "F": 0, "I": 0} for fx in FAIXAS_ETARIAS}
    sem_faixa = 0
    for faixa, sexo, n in linhas:
        if faixa is None or faixa not in tabela:
            sem_faixa += int(n)
            continue
        tabela[faixa][sexo if sexo in ("M", "F") else "I"] += int(n)
    faixas = [{"faixa": fx, **v, "total": sum(v.values())} for fx, v in tabela.items()]
    return {"faixas": faixas, "sem_faixa": sem_faixa}


# ------------------------------------------------------------- Top CID-10
def top_cid(db, f: "Filtros", limite: int = 10) -> dict:
    """Subcategorias (3 caracteres) mais frequentes no recorte filtrado."""
    where, params = build_where(f)
    where += (" AND " if where else " WHERE ") + "cid3 IS NOT NULL"
    total = int(db.execute(f"SELECT count(*) FROM {TABELA}{where}", params).fetchone()[0])
    linhas = db.execute(
        f"""SELECT cid3, any_value(capitulo_id), count(*) AS n, count(*) FILTER (WHERE obito)
            FROM {TABELA}{where} GROUP BY cid3 ORDER BY n DESC, cid3 LIMIT {int(limite)}""", params).fetchall()
    itens = [{
        "cid3": cid3,
        "capitulo_id": cap,
        "capitulo_nome": _NOMES_CAPITULO.get(cap, "Sem capítulo"),
        "grupo_nome": bloco["nome"] if (bloco := cid_to_bloco(cid3)) else None,
        "casos": int(n),
        "obitos": int(obitos),
        "percentual": _pct(n, total),
    } for cid3, cap, n, obitos in linhas]
    return {"total_com_cid": total, "itens": itens}


# --------------------------------------------------------- Top Municípios
def _norm_texto(texto: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return sem_acento.lower().strip()


def top_municipios(
    db,
    f: "Filtros",
    limite: int = 10,
    busca: Optional[str] = None,
    favoritos: Optional[list[str]] = None,
) -> dict:
    """Ranking de municípios de residência (ignora filtro de município para manter lista navegável)."""
    f_base = f.model_copy(update={"municipio": None})
    where, params = build_where(f_base)
    where += (" AND " if where else " WHERE ") + "municipio_res IS NOT NULL"
    rows = db.execute(
        f"""SELECT municipio_res, count(*) AS casos, count(*) FILTER (WHERE obito) AS obitos,
                   coalesce(sum(val_tot), 0.0) AS custo_total
            FROM {TABELA}{where}
            GROUP BY 1""",
        params,
    ).fetchall()

    fav_codigos: list[str] = []
    for raw in favoritos or []:
        cod = municipio6(raw)
        if cod and cod not in fav_codigos:
            fav_codigos.append(cod)
    fav_set = set(fav_codigos)

    por_cod: dict[str, dict] = {}
    for cod_raw, casos, obitos, custo in rows:
        cod = str(cod_raw)
        casos_i = int(casos)
        obitos_i = int(obitos)
        por_cod[cod] = {
            "codigo": cod,
            "nome": municipio_nome(cod),
            "casos": casos_i,
            "obitos": obitos_i,
            "taxa_mortalidade": _pct(obitos_i, casos_i) or 0.0,
            "custo_total": _num(custo) or 0.0,
            "favorito": cod in fav_set,
        }

    for cod in fav_codigos:
        if cod not in por_cod:
            por_cod[cod] = {
                "codigo": cod,
                "nome": municipio_nome(cod),
                "casos": 0,
                "obitos": 0,
                "taxa_mortalidade": 0.0,
                "custo_total": 0.0,
                "favorito": True,
            }

    termo = _norm_texto(busca) if busca and busca.strip() else ""
    if termo:
        filtrados = [
            item for item in por_cod.values()
            if termo in _norm_texto(item["nome"]) or termo in item["codigo"]
        ]
        filtrados.sort(key=lambda x: (not x["favorito"], -x["casos"], x["nome"]))
        itens = filtrados[: int(limite)]
    else:
        fav_itens = sorted(
            (item for item in por_cod.values() if item["favorito"]),
            key=lambda x: (-x["casos"], x["nome"]),
        )
        outros = sorted(
            (item for item in por_cod.values() if not item["favorito"]),
            key=lambda x: (-x["casos"], x["nome"]),
        )
        restante = max(0, int(limite) - len(fav_itens))
        itens = fav_itens + outros[:restante]

    return {"total_municipios": len(rows), "itens": itens}


# ------------------------------------------------------- Grupos dinâmicos
def grupos_dinamicos(db, f: "Filtros") -> list[dict]:
    """Agrega internações por bloco oficial CID-10 ignorando filtros de grupo e CID."""
    f_base = f.model_copy(update={"grupo_ids": [], "cid_codigos": []})
    where, params = build_where(f_base)
    where += (" AND " if where else " WHERE ") + "cid3 IS NOT NULL"
    rows = db.execute(
        f"SELECT cid3, count(*) FROM {TABELA}{where} GROUP BY 1",
        params,
    ).fetchall()

    totais: dict[str, int] = {}
    for cid3, n in rows:
        bloco = cid_to_bloco(cid3)
        if bloco is None:
            continue
        bid = bloco["id"]
        totais[bid] = totais.get(bid, 0) + int(n)

    itens = [
        {**BLOCO_POR_ID[bid], "internacoes": total}
        for bid, total in totais.items()
    ]
    itens.sort(key=lambda x: (-x["internacoes"], x["id"]))
    return itens


# ----------------------------------------------------------- Exportar CSV
EXPORT_COLUMNS = (
    "n_aih", "uf", "ano_mes", "data_internacao", "data_saida",
    "cid3", "capitulo_id", "grupo_id", "faixa_etaria", "sexo",
    "carater", "complexidade", "municipio_res", "obito", "dias_perm", "val_tot",
)


def exportar_csv(db, f: "Filtros", limite: int = 50000) -> str:
    """Exporta linhas filtradas da tabela internacoes em formato CSV UTF-8."""
    where, params = build_where(f)
    existentes = {r[0] for r in db.execute(f"DESCRIBE {TABELA}").fetchall()}
    colunas_sql = ", ".join(c if c in existentes else f"NULL AS {c}" for c in EXPORT_COLUMNS)
    order_sql = "data_internacao DESC NULLS LAST" + (", n_aih ASC" if "n_aih" in existentes else "")
    rows = db.execute(
        f"SELECT {colunas_sql} FROM {TABELA}{where} ORDER BY {order_sql} LIMIT ?",
        [*params, int(limite)],
    ).fetchall()

    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(EXPORT_COLUMNS)
    writer.writerows(rows)
    return buf.getvalue()
