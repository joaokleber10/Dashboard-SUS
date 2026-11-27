"""Fontes de dados locais (CSV ou Excel) mapeadas para o esquema do dashboard.

Cada arquivo refs/fontes/<nome>.json descreve UMA fonte: onde está o arquivo, qual coluna dele corresponde a
cada campo do dashboard e como traduzir os valores. O adaptador monta um "SIH de mentirinha" (mesmas colunas e
códigos do RD) e reaproveita limpar_sih(): CID, datas, idade, sexo etc. passam pela mesma validação do SIH.

Privacidade: só as colunas mapeadas são lidas para o resultado; o restante do arquivo é descartado em memória.
Não mapeie identificadores pessoais (nome, CPF, CNS, endereço, telefone).
"""
from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from src import geo
from src.dictionary import municipio6, uf_valida
from src.etl import _gravar_parquet, limpar_sih

log = logging.getLogger("fontes")

CAMPOS = {"id", "data_internacao", "data_saida", "data_nascimento", "cid", "municipio_res", "municipio_mov",
          "sexo", "idade", "dias_perm", "valor", "obito", "carater", "complexidade", "especialidade"}
OBRIGATORIOS = ("data_internacao", "cid")
_SINAIS_DE_PII = ("cpf", "cns", "nome", "telefone", "celular", "endereco", "rg", "prontuario")

_SEXO = {"m": "M", "masculino": "M", "1": "M", "h": "M", "homem": "M",
         "f": "F", "feminino": "F", "2": "F", "3": "F", "mulher": "F"}
_CARATER = {"eletivo": "eletivo", "eletiva": "eletivo", "e": "eletivo", "1": "eletivo", "01": "eletivo",
            "urgencia": "urgencia", "urgente": "urgencia", "emergencia": "urgencia", "u": "urgencia",
            "2": "urgencia", "02": "urgencia"}
_COMPLEX = {"1": "atencao_basica", "01": "atencao_basica", "atencao basica": "atencao_basica",
            "basica": "atencao_basica", "2": "media", "02": "media", "media": "media",
            "media complexidade": "media", "3": "alta", "03": "alta", "alta": "alta",
            "alta complexidade": "alta"}
_OBITO_SIM = {"1", "s", "sim", "true", "verdadeiro", "y", "yes", "obito"}
_OBITO_NAO = {"0", "n", "nao", "false", "falso", "no", "alta", "cura", "melhorado"}
_UNIDADE_IDADE = {"anos": 4, "meses": 3, "dias": 2}


def _norm(valor) -> str:
    texto = unicodedata.normalize("NFKD", str(valor).strip().lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


# --------------------------------------------------------------- configuração
def carregar_config(caminho: Path) -> dict:
    """Lê e valida o JSON da fonte. O nome da fonte é o nome do arquivo (patos.json -> 'patos')."""
    try:
        cfg = json.loads(Path(caminho).read_text(encoding="utf-8-sig"))
    except ValueError as exc:
        raise ValueError(f"{Path(caminho).name}: JSON inválido ({exc})") from exc
    cfg = {k: v for k, v in cfg.items() if not k.startswith("_")}       # chaves "_ajuda" são comentários
    nome = Path(caminho).stem
    if not re.fullmatch(r"[a-z0-9_-]{1,40}", nome):
        raise ValueError(f"nome de fonte inválido {nome!r}: use letras minúsculas, números, _ ou -")
    if nome.lower() == "sih":
        raise ValueError("o nome 'sih' é reservado para a fonte oficial")
    for chave in ("arquivo", "uf", "colunas"):
        if chave not in cfg:
            raise ValueError(f"{Path(caminho).name}: falta a chave {chave!r}")
    if not uf_valida(cfg["uf"]):
        raise ValueError(f"{Path(caminho).name}: UF inválida {cfg['uf']!r}")
    colunas = cfg["colunas"]
    desconhecidos = sorted(set(colunas) - CAMPOS)
    if desconhecidos:
        raise ValueError(f"campos desconhecidos em 'colunas': {desconhecidos}. Válidos: {sorted(CAMPOS)}")
    faltando = [c for c in OBRIGATORIOS if c not in colunas]
    if faltando:
        raise ValueError(f"campos obrigatórios sem coluna: {faltando}")
    if "id" in colunas and any(s in _norm(colunas["id"]) for s in _SINAIS_DE_PII):
        raise ValueError(f"a coluna {colunas['id']!r} parece um identificador pessoal; não mapeie nome/CPF/CNS/endereço")
    unidade = cfg.get("unidade_idade", "anos")
    if unidade not in _UNIDADE_IDADE:
        raise ValueError(f"unidade_idade inválida {unidade!r}: use anos, meses ou dias")
    cfg.update({"nome": nome, "uf": cfg["uf"].upper(), "unidade_idade": unidade,
                "formato": str(cfg.get("formato", "csv")).lower(), "decimal": cfg.get("decimal", "."),
                "valores": cfg.get("valores", {})})
    if cfg["formato"] not in ("csv", "xlsx"):
        raise ValueError(f"formato inválido {cfg['formato']!r}: use csv ou xlsx")
    return cfg


def descobrir_configs(pasta: Path) -> list[Path]:
    """Todos os *.json da pasta, menos os modelos (*.exemplo.json)."""
    if not pasta.is_dir():
        return []
    return sorted(p for p in pasta.glob("*.json") if not p.name.endswith(".exemplo.json"))


def ler_origem(cfg: dict, arquivo: Path) -> pd.DataFrame:
    """Lê tudo como texto (dtype=str): a conversão de tipos é feita campo a campo, com tolerância."""
    if cfg["formato"] == "xlsx":
        return pd.read_excel(arquivo, sheet_name=cfg.get("aba", 0), dtype=str)
    opcoes = cfg.get("csv", {})
    separador = opcoes.get("separador")           # None: o pandas descobre sozinho
    for codificacao in ([opcoes["codificacao"]] if opcoes.get("codificacao") else ["utf-8-sig", "latin-1"]):
        try:
            return pd.read_csv(arquivo, sep=separador, engine="python", encoding=codificacao, dtype=str)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"não consegui decodificar {arquivo.name}; informe csv.codificacao no JSON")


# ----------------------------------------------------------------- conversões
def _para_data(serie: pd.Series, formato: Optional[str]) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")
    txt = serie.astype("string").str.strip()
    if formato:
        return pd.to_datetime(txt, format=formato, errors="coerce")
    txt = txt.str.slice(0, 10)                     # ignora a hora (AAAA-MM-DD hh:mm:ss)
    return pd.to_datetime(txt, format="%Y-%m-%d", errors="coerce").fillna(
        pd.to_datetime(txt, format="%d/%m/%Y", errors="coerce"))


def _numero(serie: pd.Series, decimal: str = ".") -> pd.Series:
    s = serie.astype("string").str.strip()
    if decimal == ",":
        s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    else:
        s = s.str.replace(",", "", regex=False)
    return pd.to_numeric(s.str.replace(r"[^0-9.\-]", "", regex=True), errors="coerce")


def _mapear(serie: pd.Series, usuario: Optional[dict], padrao: dict) -> pd.Series:
    """Traduz valores: a tabela do usuário (no JSON) vale mais que a padrão. Sem correspondência: None."""
    do_usuario = {_norm(k): v for k, v in (usuario or {}).items()}
    mapa = {}
    for v in serie.dropna().unique():
        chave = _norm(v)
        mapa[v] = do_usuario.get(chave, padrao.get(chave))
    return serie.map(mapa)


def _mapear_obito(serie: pd.Series, usuario: Optional[dict]) -> tuple[pd.Series, int]:
    """-> (Series de '1'/'0'/None, quantidade de linhas com valor não reconhecido)."""
    do_usuario = {_norm(k): v for k, v in (usuario or {}).items()}
    mapa = {}
    for v in serie.dropna().unique():
        chave = _norm(v)
        if chave in do_usuario:
            mapa[v] = "1" if str(do_usuario[chave]).strip().lower() in ("1", "true") else "0"
        elif chave in _OBITO_SIM:
            mapa[v] = "1"
        elif chave in _OBITO_NAO:
            mapa[v] = "0"
        else:
            mapa[v] = None
    saida = serie.map(mapa)
    desconhecidos = int((serie.notna() & saida.isna()).sum())
    return saida, desconhecidos


def _resolver_municipios(serie: pd.Series, nomes: list[dict], uf: str) -> tuple[pd.Series, list[str]]:
    """Código IBGE (6 ou 7 dígitos) ou nome do município -> código de 6 dígitos. -> (códigos, nomes não resolvidos)."""
    por_uf = {(m["municipio_uf"], _norm(m["municipio_nome"])): m["codigo6"] for m in nomes}
    por_nome: dict[str, set] = {}
    for m in nomes:
        por_nome.setdefault(_norm(m["municipio_nome"]), set()).add(m["codigo6"])
    mapa, nao_resolvidos = {}, []
    for v in serie.dropna().unique():
        s = str(v).strip()
        if s.replace(" ", "").isdigit() and len(s.replace(" ", "")) in (6, 7):
            mapa[v] = municipio6(s.replace(" ", ""))
            continue
        chave = _norm(re.sub(r"\s*[-/]\s*[A-Za-z]{2}$", "", s))       # "Patos - PB" -> "patos"
        codigo = por_uf.get((uf, chave))
        if codigo is None and len(por_nome.get(chave, ())) == 1:
            codigo = next(iter(por_nome[chave]))
        mapa[v] = codigo
        if codigo is None:
            nao_resolvidos.append(s)
    return serie.map(mapa), nao_resolvidos


# ---------------------------------------------------------------- construção
@dataclass
class RelatorioFonte:
    nome: str
    linhas_origem: int = 0
    linhas_validas: int = 0
    rejeitadas: int = 0
    cid_invalido: int = 0
    avisos: list[str] = field(default_factory=list)

    def resumo(self) -> str:
        texto = (f"fonte {self.nome}: origem={self.linhas_origem} validas={self.linhas_validas} "
                 f"rejeitadas={self.rejeitadas} cid_invalido={self.cid_invalido}")
        return texto + ("".join(f"\n   aviso: {a}" for a in self.avisos) if self.avisos else "")


def construir_externa(origem: pd.DataFrame, cfg: dict, nomes_municipios: list[dict]
                      ) -> tuple[pd.DataFrame, pd.DataFrame, RelatorioFonte]:
    """DataFrame da fonte local -> (limpo, rejeitados, relatório) no mesmo esquema do SIH."""
    rel = RelatorioFonte(cfg["nome"], linhas_origem=len(origem))
    mapeadas = cfg["colunas"]
    existentes = {str(c).strip().lower(): c for c in origem.columns}

    def col(campo: str) -> pd.Series:
        real = existentes.get(str(mapeadas[campo]).strip().lower())
        if real is None:
            raise ValueError(f"coluna {mapeadas[campo]!r} (campo {campo!r}) não existe no arquivo. "
                             f"Colunas disponíveis: {list(origem.columns)}")
        return origem[real]

    formato = cfg.get("formato_data")
    valores = cfg["valores"]
    raw = pd.DataFrame(index=origem.index)
    raw["DIAG_PRINC"] = col("cid").astype("string").str.strip()
    dt_inter = _para_data(col("data_internacao"), formato)
    raw["DT_INTER"] = dt_inter.dt.strftime("%Y%m%d")
    dt_saida = None
    if "data_saida" in mapeadas:
        dt_saida = _para_data(col("data_saida"), formato)
        raw["DT_SAIDA"] = dt_saida.dt.strftime("%Y%m%d")

    if "idade" in mapeadas:
        raw["IDADE"] = _numero(col("idade"))
        raw["COD_IDADE"] = _UNIDADE_IDADE[cfg["unidade_idade"]]
    elif "data_nascimento" in mapeadas:
        nasc = _para_data(col("data_nascimento"), formato)
        raw["IDADE"] = (dt_inter - nasc).dt.days.floordiv(365.25)
        raw["COD_IDADE"] = 4
    else:
        rel.avisos.append("sem idade nem data de nascimento: pirâmide etária e filtro de faixa etária ficam vazios")

    if "sexo" in mapeadas:
        sexo = _mapear(col("sexo"), valores.get("sexo"), _SEXO).fillna("I")
        raw["SEXO"] = sexo.map({"M": "1", "F": "3"}).fillna("0")
    if "carater" in mapeadas:
        carater = _mapear(col("carater"), valores.get("carater"), _CARATER).fillna("outros")
        raw["CAR_INT"] = carater.map({"eletivo": "01", "urgencia": "02"}).fillna("99")
    if "complexidade" in mapeadas:
        cx = _mapear(col("complexidade"), valores.get("complexidade"), _COMPLEX)
        raw["COMPLEX"] = cx.map({"atencao_basica": "01", "media": "02", "alta": "03"})
    if "especialidade" in mapeadas:
        raw["ESPEC"] = col("especialidade").astype("string").str.strip()
    if "id" in mapeadas:
        raw["N_AIH"] = col("id").astype("string").str.strip()

    if "obito" in mapeadas:
        morte, desconhecidos = _mapear_obito(col("obito"), valores.get("obito"))
        raw["MORTE"] = morte
        if desconhecidos:
            rel.avisos.append(f"{desconhecidos} linhas com valor de óbito não reconhecido (contadas como não óbito); "
                              f"traduza-os em valores.obito")
    else:
        rel.avisos.append("campo 'obito' não mapeado: a taxa de mortalidade aparecerá como 0%")

    if "dias_perm" in mapeadas:
        raw["DIAS_PERM"] = _numero(col("dias_perm"), cfg["decimal"])
    elif dt_saida is not None:
        dias = (dt_saida - dt_inter).dt.days
        raw["DIAS_PERM"] = dias.where(dias >= 0)
        rel.avisos.append("dias de permanência calculados como data de saída - data de internação")
    if "valor" in mapeadas:
        raw["VAL_TOT"] = _numero(col("valor"), cfg["decimal"])

    for campo, destino in (("municipio_res", "MUNIC_RES"), ("municipio_mov", "MUNIC_MOV")):
        if campo in mapeadas:
            raw[destino], nao = _resolver_municipios(col(campo), nomes_municipios, cfg["uf"])
            if nao:
                rel.avisos.append(f"{campo}: {len(set(nao))} municípios não reconhecidos "
                                  f"(ex.: {sorted(set(nao))[:5]}); ficarão sem município")
    if ("municipio_res" in mapeadas or "municipio_mov" in mapeadas) and not nomes_municipios:
        rel.avisos.append("tabela de municípios do IBGE ausente: nomes de municípios não puderam ser resolvidos")

    limpo, rejeitados, rel_sih = limpar_sih(raw, cfg["uf"], 2000, 1)      # ano/mês só preenchem colunas abaixo
    limpo["competencia"] = limpo["ano_mes"]          # em fonte local, competência = mês da internação
    limpo["ano"] = limpo["data_internacao"].dt.year.astype("int64")
    limpo["fonte"] = cfg["nome"]
    rel.linhas_validas = rel_sih.linhas_validas
    rel.rejeitadas = rel_sih.rejeitadas_data_invalida
    rel.cid_invalido = rel_sih.cid_invalido
    return limpo, rejeitados, rel


# ------------------------------------------------------------------------ E/S
def processar_fonte(caminho_config: Path, data_dir: Path) -> RelatorioFonte:
    cfg = carregar_config(caminho_config)
    arquivo = Path(cfg["arquivo"])
    if not arquivo.is_file():
        raise FileNotFoundError(f"arquivo da fonte {cfg['nome']!r} não encontrado: {arquivo}")
    origem = ler_origem(cfg, arquivo)
    limpo, rejeitados, rel = construir_externa(origem, cfg, geo.carregar_municipios(data_dir / "geo"))
    _gravar_parquet(limpo, data_dir / "processed" / "fontes" / f"{cfg['nome']}.parquet")
    arquivo_rej = data_dir / "processed" / "rejeitados" / f"fonte_{cfg['nome']}.parquet"
    if len(rejeitados):
        _gravar_parquet(rejeitados.astype("string"), arquivo_rej)
    elif arquivo_rej.exists():
        arquivo_rej.unlink()
    return rel


def inspecionar(caminho_config: Path, data_dir: Path) -> None:
    """Mostra o que há no arquivo da fonte e como o mapeamento o traduz (sem gravar nada)."""
    cfg = carregar_config(caminho_config)
    arquivo = Path(cfg["arquivo"])
    if not arquivo.is_file():
        raise FileNotFoundError(f"arquivo não encontrado: {arquivo}")
    origem = ler_origem(cfg, arquivo)
    print(f"\nArquivo: {arquivo} | linhas: {len(origem)} | colunas: {list(origem.columns)}")
    print("\nAmostra (5 linhas):\n", origem.head(5).to_string())
    existentes = {str(c).strip().lower(): c for c in origem.columns}
    for campo in ("sexo", "carater", "complexidade", "obito"):
        real = existentes.get(str(cfg["colunas"].get(campo, "")).strip().lower())
        if real is not None:
            print(f"\nValores de {real} (campo {campo}):\n", origem[real].value_counts(dropna=False).head(15).to_string())
    _, _, rel = construir_externa(origem, cfg, geo.carregar_municipios(data_dir / "geo"))
    print("\n--- Resultado do mapeamento ---\n" + rel.resumo())