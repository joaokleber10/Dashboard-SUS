"""SQL dos KPIs e gráficos. Valores sempre por parâmetro (?); colunas são fixas no código."""
from __future__ import annotations

import unicodedata
from datetime import date, timedelta
from typing import TYPE_CHECKING, Optional

from src.dictionary import BLOCO_POR_ID, CAPITULOS, FAIXAS_ETARIAS, cid_to_bloco, municipio6

if TYPE_CHECKING:
    from src.schemas import Filtros

TABELA = "internacoes"
_NOMES_CAPITULO = {c["id"]: c["nome"] for c in CAPITULOS}
_NOMES_CAPITULO["ND"] = "Sem CID válido"


def _coluna_municipio(f) -> str:
    """Município pela residência do paciente ou pelo hospital (atendimento). Lista fixa, nunca texto livre."""
    return "municipio_mov" if getattr(f, "municipio_ref", "residencia") == "atendimento" else "municipio_res"


# ------------------------------------------------------------------ WHERE
def build_where(f: "Filtros", incluir_cid: bool = True,
                periodo: Optional[tuple[date, date]] = None,
                incluir_municipio: bool = True,
                incluir_cid_codigos: bool = True) -> tuple[str, list]:
    """Monta a cláusula WHERE parametrizada.

    incluir_cid=False ignora capítulo/grupo/CID (denominador do "total geral").
    periodo substitui data_inicio/data_fim (usado no período de comparação).
    incluir_municipio=False ignora o filtro de município (mapa e tabela mostram todos os municípios).
    incluir_cid_codigos=False ignora só os códigos CID escolhidos (busca de subcategorias).
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
            legado = [g for g in f.grupo_ids if g not in BLOCO_POR_ID]
            blocos = [BLOCO_POR_ID[g] for g in f.grupo_ids if g in BLOCO_POR_ID]
            partes: list[str] = []
            g_params: list = []
            if legado:
                partes.append(f"grupo_id IN ({','.join(['?'] * len(legado))})")
                g_params.extend(legado)
            for bloco in blocos:
                partes.append("(cid3 >= ? AND cid3 <= ?)")
                g_params.extend([bloco["inicio"], bloco["fim"]])
            conds.append(partes[0] if len(partes) == 1 else "(" + " OR ".join(partes) + ")")
            params.extend(g_params)
        if incluir_cid_codigos:
            add_in("cid3", f.cid_codigos)
    if f.uf:
        conds.append("uf = ?")
        params.append(f.uf)
    if f.municipio and incluir_municipio:
        conds.append(f"{_coluna_municipio(f)} = ?")
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
    add_in("fonte", getattr(f, "fontes", []))
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


# ------------------------------------------------------ catálogos opcionais
_MUN_VAZIO = ("(SELECT CAST(NULL AS VARCHAR) AS codigo6, CAST(NULL AS VARCHAR) AS municipio_nome, "
              "CAST(NULL AS VARCHAR) AS municipio_uf WHERE false)")
_CID_VAZIO = "(SELECT CAST(NULL AS VARCHAR) AS cid3, CAST(NULL AS VARCHAR) AS cid_nome WHERE false)"


def _tabela_existe(db, nome: str) -> bool:
    return db.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = ?", [nome]).fetchone()[0] > 0


def _fonte_municipios(db) -> str:
    """Tabela de nomes, ou uma tabela vazia se o banco foi criado antes dela existir."""
    return "municipios" if _tabela_existe(db, "municipios") else _MUN_VAZIO


def _fonte_cid10(db) -> str:
    return "cid10" if _tabela_existe(db, "cid10") else _CID_VAZIO


def _sem_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).lower()


def _like_escape(texto: str) -> str:
    """Escapa %, _ e ! para uso com LIKE ... ESCAPE '!'."""
    return texto.replace("!", "!!").replace("%", "!%").replace("_", "!_")


# ------------------------------------------------------------- Top CID-10
def top_cid(db, f: "Filtros", limite: int = 10) -> dict:
    """Subcategorias (3 caracteres) mais frequentes no recorte filtrado (com nome, se houver catálogo)."""
    where, params = build_where(f)
    where += (" AND " if where else " WHERE ") + "cid3 IS NOT NULL"
    total = int(db.execute(f"SELECT count(*) FROM {TABELA}{where}", params).fetchone()[0])
    fonte = _fonte_cid10(db)
    linhas = db.execute(
        f"""WITH base AS (
              SELECT cid3, any_value(capitulo_id) AS capitulo_id, count(*) AS n,
                     count(*) FILTER (WHERE obito) AS obitos
              FROM {TABELA}{where} GROUP BY cid3 ORDER BY n DESC, cid3 LIMIT {int(limite)})
            SELECT b.cid3, b.capitulo_id, b.n, b.obitos, c.cid_nome
            FROM base b LEFT JOIN {fonte} AS c ON c.cid3 = b.cid3
            ORDER BY b.n DESC, b.cid3""", params).fetchall()
    itens = [{
        "cid3": cid3,
        "cid_nome": nome,
        "capitulo_id": cap,
        "capitulo_nome": _NOMES_CAPITULO.get(cap, "Sem capítulo"),
        "grupo_nome": bloco["nome"] if (bloco := cid_to_bloco(cid3)) else None,
        "casos": int(n),
        "obitos": int(obitos),
        "percentual": _pct(n, total),
    } for cid3, cap, n, obitos, nome in linhas]
    return {"total_com_cid": total, "itens": itens}


def buscar_cid(db, f: "Filtros", q: str = "", limite: int = 20) -> dict:
    """Subcategorias presentes nos dados (respeitando os demais filtros) que combinam com a busca.

    Busca por prefixo do código (I2, J18) e, se houver catálogo, por parte do nome (sem acento).
    Os códigos já escolhidos não restringem a busca.
    """
    where, params = build_where(f, incluir_cid_codigos=False)
    where += (" AND " if where else " WHERE ") + "cid3 IS NOT NULL"
    fonte = _fonte_cid10(db)
    filtro_sql, extra = "", []
    termo = (q or "").strip()
    if termo:
        codigo = _like_escape(termo.upper().replace(".", ""))
        nome = _like_escape(_sem_acentos(termo))
        filtro_sql = (" WHERE b.cid3 LIKE ? ESCAPE '!'"
                      " OR strip_accents(lower(coalesce(c.cid_nome, ''))) LIKE ? ESCAPE '!'")
        extra = [f"{codigo}%", f"%{nome}%"]
    linhas = db.execute(
        f"""WITH base AS (
              SELECT cid3, any_value(capitulo_id) AS capitulo_id, count(*) AS casos
              FROM {TABELA}{where} GROUP BY cid3)
            SELECT b.cid3, b.capitulo_id, b.casos, c.cid_nome
            FROM base b LEFT JOIN {fonte} AS c ON c.cid3 = b.cid3{filtro_sql}
            ORDER BY b.casos DESC, b.cid3 LIMIT {int(limite)}""", params + extra).fetchall()
    return {"itens": [{"cid3": cid3, "capitulo_id": cap, "casos": int(casos), "cid_nome": nome}
                      for cid3, cap, casos, nome in linhas]}


# ------------------------------------------------------- Grupos dinâmicos
def grupos_dinamicos(db, f: "Filtros") -> list[dict]:
    """Agrega internações por bloco oficial CID-10 ignorando filtros de grupo e CID."""
    f_base = f.model_copy(update={"grupo_ids": [], "cid_codigos": []})
    where, params = build_where(f_base)
    where += (" AND " if where else " WHERE ") + "cid3 IS NOT NULL"
    rows = db.execute(f"SELECT cid3, count(*) FROM {TABELA}{where} GROUP BY 1", params).fetchall()
    totais: dict[str, int] = {}
    for cid3, n in rows:
        bloco = cid_to_bloco(cid3)
        if bloco is None:
            continue
        totais[bloco["id"]] = totais.get(bloco["id"], 0) + int(n)
    itens = [{**BLOCO_POR_ID[bid], "internacoes": total} for bid, total in totais.items()]
    itens.sort(key=lambda x: (-x["internacoes"], x["id"]))
    return itens


# -------------------------------------------------------------- municípios
_ORDEM_MUNICIPIOS = {"casos": "casos", "obitos": "obitos", "taxa_mortalidade": "taxa_mortalidade",
                     "permanencia_media": "permanencia_media", "custo_total": "custo_total", "nome": "nome"}


def _rotulo_municipio(codigo: Optional[str], nome: Optional[str]) -> tuple[str, bool]:
    """(texto exibido, identificado?). Código sem nome ou ausente nunca quebra: ganha um rótulo claro."""
    if codigo is None:
        return "Município ignorado (sem código informado)", False
    if nome:
        return nome, True
    return f"Município não identificado (código {codigo})", False


def _cte_municipios(db, f: "Filtros") -> tuple[str, list]:
    """Agregado por município de residência (ignora o filtro de município) já com o nome do IBGE."""
    where, params = build_where(f, incluir_municipio=False)
    fonte = _fonte_municipios(db)
    col = _coluna_municipio(f)
    cte = f"""WITH agg AS (
          SELECT {col} AS codigo, count(*) AS casos, count(*) FILTER (WHERE obito) AS obitos,
                 avg(dias_perm) AS permanencia_media, sum(val_tot) AS custo_total
          FROM {TABELA}{where} GROUP BY {col}),
        nomeado AS (
          SELECT a.*, m.municipio_nome AS nome, 100.0 * a.obitos / nullif(a.casos, 0) AS taxa_mortalidade
          FROM agg a LEFT JOIN {fonte} AS m ON m.codigo6 = a.codigo)"""
    return cte, params


def _item_municipio(linha, total_casos: Optional[int] = None) -> dict:
    codigo, nome, casos, obitos, taxa, perm, custo = linha
    rotulo, identificado = _rotulo_municipio(codigo, nome)
    item = {"codigo": codigo, "nome": rotulo, "identificado": identificado, "casos": int(casos),
            "obitos": int(obitos), "taxa_mortalidade": _num(taxa), "permanencia_media": _num(perm),
            "custo_total": _num(custo)}
    if total_casos is not None:
        item["percentual"] = _pct(casos, total_casos)
    return item


def municipios(db, f: "Filtros", ordenar_por: str = "casos", ordem: str = "desc",
               pagina: int = 1, por_pagina: int = 25, busca: Optional[str] = None) -> dict:
    """Tabela de municípios: ordenável, paginada e com busca por nome (sem acento) ou código."""
    cte, params = _cte_municipios(db, f)
    coluna = _ORDEM_MUNICIPIOS.get(ordenar_por, "casos")       # lista fixa: nunca texto do usuário
    direcao = "ASC" if ordem == "asc" else "DESC"
    cond, extra = "", []
    termo = (busca or "").strip()
    if termo:
        cond = (" WHERE (strip_accents(lower(coalesce(nome, ''))) LIKE ? ESCAPE '!'"
                " OR coalesce(codigo, '') LIKE ? ESCAPE '!')")
        extra = [f"%{_like_escape(_sem_acentos(termo))}%", f"{_like_escape(termo)}%"]
    total_casos = int(db.execute(f"{cte} SELECT coalesce(sum(casos), 0) FROM nomeado", params).fetchone()[0])
    total_municipios = int(db.execute(f"{cte} SELECT count(*) FROM nomeado{cond}", params + extra).fetchone()[0])
    deslocamento = (max(int(pagina), 1) - 1) * int(por_pagina)
    linhas = db.execute(
        f"""{cte} SELECT codigo, nome, casos, obitos, taxa_mortalidade, permanencia_media, custo_total
            FROM nomeado{cond} ORDER BY {coluna} {direcao} NULLS LAST, codigo
            LIMIT {int(por_pagina)} OFFSET {int(deslocamento)}""", params + extra).fetchall()
    return {"total_municipios": total_municipios, "total_casos": total_casos, "pagina": int(pagina),
            "por_pagina": int(por_pagina), "itens": [_item_municipio(l, total_casos) for l in linhas]}


def mapa_municipios(db, f: "Filtros") -> dict:
    """Todos os municípios do recorte, sem paginação: alimenta o mapa e a lista de municípios do painel."""
    cte, params = _cte_municipios(db, f)
    linhas = db.execute(
        f"""{cte} SELECT codigo, nome, casos, obitos, taxa_mortalidade, permanencia_media, custo_total
            FROM nomeado ORDER BY casos DESC, codigo""", params).fetchall()
    return {"itens": [_item_municipio(l) for l in linhas]}


# ------------------------------------------------------------ exportação CSV
# (nome da coluna no CSV, expressão SQL). Sem n_aih: o arquivo não precisa identificar a AIH.
COLUNAS_EXPORT = [
    ("data_internacao", "CAST(data_internacao AS DATE)"),
    ("data_saida", "CAST(data_saida AS DATE)"),
    ("uf", "uf"),
    ("municipio_res", "municipio_res"),
    ("municipio_mov", "municipio_mov"),
    ("diag_princ", "diag_princ"),
    ("cid3", "cid3"),
    ("capitulo_id", "capitulo_id"),
    ("grupo_id", "grupo_id"),
    ("sexo", "sexo"),
    ("faixa_etaria", "faixa_etaria"),
    ("idade_anos", "round(idade_anos, 2)"),
    ("carater", "carater"),
    ("complexidade", "complexidade"),
    ("especialidade", "especialidade"),
    ("dias_perm", "dias_perm"),
    ("val_tot", "val_tot"),
    ("obito", "CAST(obito AS INTEGER)"),
    ("fonte", "fonte"),
]


def contar(db, f: "Filtros") -> int:
    where, params = build_where(f)
    return int(db.execute(f"SELECT count(*) FROM {TABELA}{where}", params).fetchone()[0])


def colunas_tabela(db) -> set[str]:
    """Colunas que a tabela internacoes realmente tem (bancos antigos podem não ter municipio_mov nem fonte)."""
    linhas = db.execute("SELECT column_name FROM information_schema.columns WHERE table_name = ?", [TABELA]).fetchall()
    return {r[0] for r in linhas}


def consulta_export(f: "Filtros", limite: int, existentes: Optional[set] = None) -> tuple[str, list]:
    """SQL do CSV. Com `existentes`, colunas que o banco não tem saem vazias (NULL) em vez de quebrar a exportação."""
    where, params = build_where(f)
    partes = []
    for nome, expr in COLUNAS_EXPORT:
        if existentes is not None and nome not in existentes:
            expr = "CAST(NULL AS VARCHAR)"
        partes.append(f"{expr} AS {nome}")
    sql = f"SELECT {', '.join(partes)} FROM {TABELA}{where} ORDER BY data_internacao, cid3 LIMIT {int(limite)}"
    return sql, params


# ------------------------------------------------------------- foco local
def foco_local(db, uf: str, municipio: str) -> Optional[dict]:
    """Resolve FOCO_MUNICIPIO (nome ou código IBGE) para o município em foco, ou None se não achar."""
    texto = (municipio or "").strip()
    if not texto:
        return None
    sigla = (uf or "").strip().upper() or None
    fonte = _fonte_municipios(db)
    if texto.replace(" ", "").isdigit():
        codigo = municipio6(texto.replace(" ", ""))
        if not codigo:
            return None
        linha = db.execute(f"SELECT municipio_nome, municipio_uf FROM {fonte} AS m WHERE codigo6 = ?", [codigo]).fetchone()
        return {"uf": linha[1] if linha else sigla, "municipio_codigo": codigo, "municipio_nome": linha[0] if linha else None}
    sql = f"SELECT codigo6, municipio_nome, municipio_uf FROM {fonte} AS m WHERE strip_accents(lower(municipio_nome)) = ?"
    params = [_sem_acentos(texto)]
    if sigla:
        sql += " AND municipio_uf = ?"
        params.append(sigla)
    linhas = db.execute(sql + " ORDER BY codigo6", params).fetchall()
    if len(linhas) != 1:        # nenhum, ou homônimos em várias UFs sem FOCO_UF para desempatar
        return None
    codigo, nome, uf_encontrada = linhas[0]
    return {"uf": uf_encontrada, "municipio_codigo": codigo, "municipio_nome": nome}