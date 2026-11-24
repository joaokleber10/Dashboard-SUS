"""SQL dos KPIs e gráficos. Valores sempre por parâmetro (?); colunas são fixas no código."""
from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING, Optional

from src.dictionary import CAPITULOS, FAIXAS_ETARIAS

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
        add_in("grupo_id", f.grupo_ids)
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
    if not (f.data_inicio and f.data_fim):
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
    total, obitos, perm, custo_total, custo_medio = db.execute(
        f"""SELECT count(*), count(*) FILTER (WHERE obito), avg(dias_perm), sum(val_tot), avg(val_tot)
            FROM {TABELA}{where}""", params).fetchone()
    return {
        "total": int(total),
        "obitos": int(obitos),
        "taxa_mortalidade": _pct(obitos, total),
        "permanencia_media": _num(perm),
        "custo_total": _num(custo_total),
        "custo_medio": _num(custo_medio),
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
        "casos": int(n),
        "obitos": int(obitos),
        "percentual": _pct(n, total),
    } for cid3, cap, n, obitos in linhas]
    return {"total_com_cid": total, "itens": itens}