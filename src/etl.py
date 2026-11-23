"""ETL do SIH/SUS (arquivos RD) -> Parquet limpo -> tabela DuckDB.

Uso (a partir da raiz do projeto):
    python -m src.etl                       # usa o .env / variáveis de ambiente
    python -m src.etl --uf PB,PE --start 2023 --end 2024
    python -m src.etl --inspect             # baixa 1 mês e imprime colunas/valores
    python -m src.etl --force               # reprocessa mesmo que já exista

Fluxo por competência (UF, ano, mês):
    PySUS baixa/converte -> DuckDB lê o Parquet bruto -> pandas limpa ->
    grava data/processed/sih/uf=XX/ano=YYYY/sih_XX_YYYYMM.parquet
Ao final, recria a tabela `internacoes` no DuckDB a partir dos Parquets limpos.

O backend deve abrir o DuckDB com read_only=True (DuckDB aceita só 1 escritor).
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from src.dictionary import (
    cid_to_chapter, cid_to_grupo, faixa_etaria, idade_para_anos, municipio6,
    normalizar_carater, normalizar_cid, normalizar_complexidade, normalizar_sexo,
    uf_valida,
)

log = logging.getLogger("etl")

GRUPO_SIH = "RD"
ESSENCIAIS = ["DIAG_PRINC", "DT_INTER"]
COLUNAS_ORIGEM = [
    "N_AIH", "DIAG_PRINC", "DT_INTER", "DT_SAIDA", "MUNIC_RES", "MUNIC_MOV",
    "SEXO", "IDADE", "COD_IDADE", "DIAS_PERM", "VAL_TOT", "MORTE", "CAR_INT",
    "COMPLEX", "ESPEC",  # opcionais (filtros extras); ausentes não quebram o ETL
]


# ------------------------------------------------------------ configuração
@dataclass
class Config:
    ufs: list[str]
    ano_ini: int
    ano_fim: int
    data_dir: Path
    duckdb_path: Path
    force: bool = False

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed" / "sih"

    @property
    def rejected_dir(self) -> Path:
        return self.data_dir / "processed" / "rejeitados"


def construir_config(argv: Optional[list[str]] = None) -> tuple[Config, argparse.Namespace]:
    try:  # .env local (no Docker as variáveis já vêm do env_file)
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    p = argparse.ArgumentParser(description="ETL SIH/SUS (RD)")
    p.add_argument("--uf", default=os.getenv("ETL_UF", "PB"), help="UF ou lista separada por vírgula")
    p.add_argument("--start", type=int, default=int(os.getenv("ETL_YEAR_START", "2023")))
    p.add_argument("--end", type=int, default=int(os.getenv("ETL_YEAR_END", "2024")))
    p.add_argument("--force", action="store_true", help="reprocessa competências já existentes")
    p.add_argument("--inspect", action="store_true", help="baixa 1 mês e imprime colunas e valores")
    p.add_argument("--skip-load", action="store_true", help="não recria a tabela no DuckDB")
    args = p.parse_args(argv)

    ufs = [u.strip().upper() for u in args.uf.split(",") if u.strip()]
    invalidas = [u for u in ufs if not uf_valida(u)]
    if invalidas:
        p.error(f"UF(s) inválida(s): {invalidas}")
    if args.start > args.end:
        p.error("--start não pode ser maior que --end")

    data_dir = Path(os.getenv("DATA_DIR", "./data"))
    # Cache do PySUS dentro de data/ (precisa ser definido ANTES de importar o pysus).
    os.environ.setdefault("PYSUS_CACHEPATH", str(data_dir / "pysus_cache"))
    duck = Path(os.getenv("DUCKDB_PATH", str(data_dir / "sus.duckdb")))
    return Config(ufs, args.start, args.end, data_dir, duck, args.force), args


# ---------------------------------------------------------------- download
_ATRIBUTOS_CAMINHO = ("path", "local_path", "filepath", "file_path")


def _caminho_de(item) -> Optional[Path]:
    """Resolve o arquivo local de um item do FileBag (a API 2.x não documenta o atributo)."""
    if isinstance(item, (str, Path)):
        p = Path(item)
        if p.is_file():
            return p
    else:
        for attr in _ATRIBUTOS_CAMINHO:
            v = getattr(item, attr, None)
            if v is not None and Path(str(v)).is_file():
                return Path(str(v))
    # Fallback: procura pelo nome do arquivo dentro do cache do PySUS.
    cache = Path(os.environ.get("PYSUS_CACHEPATH", "./data/pysus_cache"))
    candidatos = []
    for bruto in (str(item), getattr(item, "basename", None), getattr(item, "name", None)):
        if bruto:
            nome = Path(str(bruto)).name
            candidatos.append(nome if Path(nome).suffix else nome + ".parquet")
    for nome in candidatos:
        achados = sorted(cache.rglob(nome))
        if achados:
            return achados[0]
    return None


def extrair_caminhos(resultado) -> list[Path]:
    """FileBag | lista | caminho -> lista de Path de arquivos locais existentes."""
    itens = getattr(resultado, "files", None)
    if itens is None:
        itens = [resultado] if isinstance(resultado, (str, Path)) else list(resultado)
    caminhos: list[Path] = []
    for it in itens:
        p = _caminho_de(it)
        if p is None:
            attrs = [a for a in dir(it) if not a.startswith("_")]
            raise FileNotFoundError(f"Arquivo local de {it!r} não encontrado. Atributos do objeto: {attrs}")
        caminhos.append(p)
    return caminhos


def baixar_competencia(uf: str, ano: int, mes: int, tentativas: int = 3):
    """Baixa o RD de (uf, ano, mês) via PySUS 2.x.

    Retorna lista de Path de .parquet locais (vazia = competência não publicada)
    ou um DataFrame, se a versão do PySUS devolver DataFrame.
    """
    import pysus  # import tardio: só o download precisa do pysus instalado

    ultimo_erro: Optional[Exception] = None
    for i in range(1, tentativas + 1):
        try:
            try:
                r = pysus.ftp.sih(state=uf, year=ano, month=mes, group=GRUPO_SIH,
                                  as_dataframe=False, show_progress=False)
            except TypeError:  # versão que não aceita esses kwargs
                r = pysus.ftp.sih(state=uf, year=ano, month=mes, group=GRUPO_SIH)
            if isinstance(r, pd.DataFrame):
                return r
            itens = getattr(r, "files", None)
            if itens is None:
                itens = [r] if isinstance(r, (str, Path)) else list(r or [])
            if len(itens) == 0:
                return []
            try:
                return extrair_caminhos(r)
            except FileNotFoundError:
                if hasattr(r, "download"):  # FileBag remoto: baixa e tenta de novo
                    return extrair_caminhos(r.download())
                raise
        except Exception as exc:  # FTP/rede do DATASUS é instável
            ultimo_erro = exc
            log.warning("Falha no download %s %d-%02d (tentativa %d/%d): %s",
                        uf, ano, mes, i, tentativas, exc)
            time.sleep(2 * i)
    raise RuntimeError(f"Download falhou para {uf} {ano}-{mes:02d}") from ultimo_erro


def _sql_lista(paths: list[str]) -> str:
    return "[" + ",".join("'" + str(p).replace("'", "''") + "'" for p in paths) + "]"


def ler_raw(resultado) -> pd.DataFrame:
    """Lê o Parquet bruto com DuckDB (só as colunas necessárias) ou aceita DataFrame."""
    if isinstance(resultado, pd.DataFrame):
        cols = [c for c in COLUNAS_ORIGEM if c in resultado.columns]
        return resultado[cols].copy()
    import duckdb
    paths = [Path(p).resolve().as_posix() for p in extrair_caminhos(resultado)]
    con = duckdb.connect()
    try:
        fonte = f"read_parquet({_sql_lista(paths)}, union_by_name=true)"
        disponiveis = [d[0] for d in con.execute(f"SELECT * FROM {fonte} LIMIT 0").description]
        cols = [c for c in COLUNAS_ORIGEM if c in disponiveis]
        if not cols:
            raise ValueError(f"Nenhuma coluna esperada encontrada. Colunas: {disponiveis[:20]}")
        sel = ", ".join(f'"{c}"' for c in cols)
        return con.execute(f"SELECT {sel} FROM {fonte}").df()
    finally:
        con.close()


# ---------------------------------------------------------------- limpeza
@dataclass
class RelatorioQualidade:
    uf: str
    ano: int
    mes: int
    linhas_lidas: int = 0
    rejeitadas_data_invalida: int = 0
    linhas_validas: int = 0
    cid_invalido: int = 0
    faixa_etaria_nula: int = 0
    saida_antes_internacao: int = 0
    municipio_nulo: int = 0
    colunas_ausentes: list[str] = field(default_factory=list)

    @property
    def pct_cid_invalido(self) -> float:
        return 100 * self.cid_invalido / self.linhas_validas if self.linhas_validas else 0.0

    def resumo(self) -> str:
        return (f"{self.uf} {self.ano}-{self.mes:02d}: lidas={self.linhas_lidas} "
                f"validas={self.linhas_validas} rejeitadas(data)={self.rejeitadas_data_invalida} "
                f"cid_invalido={self.cid_invalido} ({self.pct_cid_invalido:.2f}%) "
                f"faixa_nula={self.faixa_etaria_nula} saida<internacao={self.saida_antes_internacao} "
                f"municipio_nulo={self.municipio_nulo}"
                + (f" colunas_ausentes={self.colunas_ausentes}" if self.colunas_ausentes else ""))


def _map_unique(serie: pd.Series, func: Callable) -> pd.Series:
    """Aplica func só aos valores distintos (rápido) e devolve dtype string."""
    mapa = {v: func(v) for v in serie.dropna().unique()}
    return serie.map(mapa).astype("string")


def _para_data(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")
    txt = serie.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    return pd.to_datetime(txt, format="%Y%m%d", errors="coerce")


def limpar_sih(raw: pd.DataFrame, uf: str, ano: int, mes: int
               ) -> tuple[pd.DataFrame, pd.DataFrame, RelatorioQualidade]:
    """Função pura: DataFrame bruto -> (limpo, rejeitados, relatório). Não levanta por dado sujo."""
    faltando = [c for c in ESSENCIAIS if c not in raw.columns]
    if faltando:
        raise ValueError(f"Colunas essenciais ausentes no arquivo: {faltando}")

    rel = RelatorioQualidade(uf=uf, ano=ano, mes=mes, linhas_lidas=len(raw))
    rel.colunas_ausentes = [c for c in COLUNAS_ORIGEM if c not in raw.columns]

    def col(nome: str) -> pd.Series:
        return raw[nome] if nome in raw.columns else pd.Series(pd.NA, index=raw.index, dtype="object")

    data_inter = _para_data(col("DT_INTER"))
    invalida = data_inter.isna()
    rejeitados = raw.loc[invalida].copy()
    rejeitados["motivo"] = "data_internacao_invalida"
    rel.rejeitadas_data_invalida = int(invalida.sum())

    df = pd.DataFrame(index=raw.index)
    df["n_aih"] = col("N_AIH").astype("string")
    df["data_internacao"] = data_inter
    df["data_saida"] = _para_data(col("DT_SAIDA"))

    cid_raw = col("DIAG_PRINC").astype("string").str.strip()
    df["diag_princ"] = cid_raw
    df["cid3"] = _map_unique(cid_raw, normalizar_cid)
    df["capitulo_id"] = _map_unique(df["cid3"], cid_to_chapter)
    df["grupo_id"] = _map_unique(df["cid3"], cid_to_grupo)

    idade = pd.to_numeric(col("IDADE"), errors="coerce")
    cod = pd.to_numeric(col("COD_IDADE"), errors="coerce")
    par = pd.DataFrame({"i": idade, "c": cod})
    uniq = par.drop_duplicates().reset_index(drop=True)
    uniq["anos"] = [idade_para_anos(i, c) for i, c in zip(uniq["i"], uniq["c"])]
    df["idade_anos"] = par.merge(uniq, on=["i", "c"], how="left")["anos"].astype("float64").values
    df["faixa_etaria"] = _map_unique(df["idade_anos"], faixa_etaria)

    df["sexo"] = _map_unique(col("SEXO"), normalizar_sexo).fillna("I")
    df["carater"] = _map_unique(col("CAR_INT"), normalizar_carater).fillna("outros")
    df["complexidade"] = _map_unique(col("COMPLEX"), normalizar_complexidade).fillna("nao_informada")
    df["especialidade"] = col("ESPEC").astype("string")
    df["municipio_res"] = _map_unique(col("MUNIC_RES"), municipio6)
    df["municipio_mov"] = _map_unique(col("MUNIC_MOV"), municipio6)

    df["obito"] = pd.to_numeric(col("MORTE"), errors="coerce").fillna(0).astype(int).eq(1)
    df["dias_perm"] = pd.to_numeric(col("DIAS_PERM"), errors="coerce")
    df["val_tot"] = pd.to_numeric(col("VAL_TOT"), errors="coerce")

    df = df.loc[~invalida].copy()
    df["uf"] = uf
    df["ano"] = ano
    df["competencia"] = f"{ano}-{mes:02d}"
    df["ano_mes"] = df["data_internacao"].dt.strftime("%Y-%m")

    rel.linhas_validas = len(df)
    rel.cid_invalido = int(df["cid3"].isna().sum())
    rel.faixa_etaria_nula = int(df["faixa_etaria"].isna().sum())
    rel.saida_antes_internacao = int((df["data_saida"] < df["data_internacao"]).sum())
    rel.municipio_nulo = int(df["municipio_res"].isna().sum())
    return df.reset_index(drop=True), rejeitados.reset_index(drop=True), rel


# ------------------------------------------------------------ persistência
def _gravar_parquet(df: pd.DataFrame, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".tmp")
    df.to_parquet(tmp, index=False, compression="zstd")
    os.replace(tmp, destino)  # atômico: nunca deixa Parquet pela metade


def destino_processado(cfg: Config, uf: str, ano: int, mes: int) -> Path:
    return cfg.processed_dir / f"uf={uf}" / f"ano={ano}" / f"sih_{uf}_{ano}{mes:02d}.parquet"


def processar_competencia(cfg: Config, uf: str, ano: int, mes: int) -> Optional[RelatorioQualidade]:
    destino = destino_processado(cfg, uf, ano, mes)
    if destino.exists() and not cfg.force:
        log.info("%s %d-%02d já processado (cache) — pulando", uf, ano, mes)
        return None
    resultado = baixar_competencia(uf, ano, mes)
    vazio = (resultado is None or (isinstance(resultado, pd.DataFrame) and resultado.empty)
             or (isinstance(resultado, list) and not resultado))
    if vazio:
        log.warning("%s %d-%02d: sem arquivo publicado — pulando", uf, ano, mes)
        return None
    raw = ler_raw(resultado)
    limpo, rejeitados, rel = limpar_sih(raw, uf, ano, mes)
    log.info(rel.resumo())
    _gravar_parquet(limpo, destino)
    if len(rejeitados):
        rej = cfg.rejected_dir / f"uf={uf}" / f"rej_{uf}_{ano}{mes:02d}.parquet"
        _gravar_parquet(rejeitados.astype("string"), rej)
    return rel


def carregar_duckdb(cfg: Config) -> int:
    """Recria a tabela `internacoes` a partir dos Parquets limpos. Retorna nº de linhas."""
    import duckdb
    arquivos = list(cfg.processed_dir.glob("uf=*/ano=*/*.parquet"))
    if not arquivos:
        raise RuntimeError("Nenhum Parquet processado para carregar no DuckDB.")
    cfg.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    glob = str(cfg.processed_dir / "uf=*" / "ano=*" / "*.parquet").replace("'", "''")
    con = duckdb.connect(str(cfg.duckdb_path))
    try:
        con.execute(
            f"CREATE OR REPLACE TABLE internacoes AS "
            f"SELECT * FROM read_parquet('{glob}', union_by_name=true) "
            f"ORDER BY uf, data_internacao"
        )
        n = con.execute("SELECT count(*) FROM internacoes").fetchone()[0]
    finally:
        con.close()
    log.info("DuckDB %s: tabela internacoes com %d linhas", cfg.duckdb_path, n)
    return n


# ------------------------------------------------------------------ inspect
def inspecionar(cfg: Config) -> None:
    """Baixa 1 mês e imprime o que precisamos conferir contra o dictionary.py."""
    uf, ano = cfg.ufs[0], cfg.ano_ini
    log.info("Inspeção: baixando %s %d-01 ...", uf, ano)
    resultado = baixar_competencia(uf, ano, 1)
    print("\nRetorno normalizado:", type(resultado).__name__)
    if not isinstance(resultado, pd.DataFrame):
        print("Arquivos locais:", [str(p) for p in resultado])
    raw = ler_raw(resultado)
    print(f"\nLinhas: {len(raw)} | colunas lidas: {list(raw.columns)}")
    print("\nDtypes:\n", raw.dtypes.to_string())
    for c in ["SEXO", "COD_IDADE", "CAR_INT", "COMPLEX", "MORTE"]:
        if c in raw.columns:
            print(f"\nValores de {c}:\n", raw[c].value_counts(dropna=False).head(12).to_string())
    for c in ["DT_INTER", "DIAG_PRINC", "MUNIC_RES"]:
        if c in raw.columns:
            print(f"\nAmostra de {c}:", raw[c].head(5).tolist())
    if {"IDADE", "COD_IDADE"} <= set(raw.columns):
        print("\nIDADE por COD_IDADE (min / max / valores mais comuns):")
        idade_num = pd.to_numeric(raw["IDADE"], errors="coerce")
        for cod, grp in idade_num.groupby(raw["COD_IDADE"]):
            top = raw.loc[grp.index, "IDADE"].value_counts().head(8).to_dict()
            print(f"  COD_IDADE={cod}: n={len(grp)} min={grp.min()} max={grp.max()} top={top}")
    if "ESPEC" in raw.columns:
        print("\nValores de ESPEC:\n", raw["ESPEC"].value_counts(dropna=False).head(12).to_string())
    print("\n--- Relatório de qualidade sobre o mês real ---")
    _, _, rel = limpar_sih(raw, uf, ano, 1)
    print(rel.resumo())
    print("\nPYSUS_CACHEPATH =", os.environ.get("PYSUS_CACHEPATH"))


# --------------------------------------------------------------------- main
def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # silencia o ruído de HEAD/GET do PySUS
    cfg, args = construir_config(argv)
    if args.inspect:
        inspecionar(cfg)
        return 0

    hoje = date.today()
    ok = falhas = 0
    for uf in cfg.ufs:
        for ano in range(cfg.ano_ini, cfg.ano_fim + 1):
            for mes in range(1, 13):
                if (ano, mes) > (hoje.year, hoje.month):
                    continue
                try:
                    processar_competencia(cfg, uf, ano, mes)
                    ok += 1
                except Exception:
                    falhas += 1
                    log.exception("Competência %s %d-%02d falhou — seguindo para a próxima", uf, ano, mes)
    log.info("Competências ok/puladas=%d falhas=%d", ok, falhas)
    if ok == 0:
        return 1
    if not args.skip_load:
        carregar_duckdb(cfg)
    return 0 if falhas == 0 else 2


if __name__ == "__main__":
    sys.exit(main())