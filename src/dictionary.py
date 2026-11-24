"""Dicionários de domínio do dashboard epidemiológico (SIH/SUS).

Fonte única de verdade para capítulos CID-10, grupos de interesse, UFs,
faixas etárias e códigos categóricos do SIH. O ETL, a API e (via
/meta/filtros) o frontend dependem deste módulo.

ATENÇÃO: os códigos de SEXO, CAR_INT e COD_IDADE abaixo seguem o layout
usual do SIH/RD, mas devem ser conferidos no dicionário de dados da versão
dos arquivos baixados (o layout muda entre anos).
"""
from __future__ import annotations

import re
from typing import Optional

# ---------------------------------------------------------------- CID-10
_CID_RE = re.compile(r"^[A-Z]\d{2}$")


def _key(categoria: str) -> int:
    """Ordena categorias de 3 caracteres: 'A00' -> 0, 'B99' -> 199, 'D48' -> 348."""
    return (ord(categoria[0]) - 65) * 100 + int(categoria[1:3])


def normalizar_cid(codigo: object) -> Optional[str]:
    """Retorna a categoria de 3 caracteres (ex.: 'I21') ou None se inválido.

    Nunca levanta exceção: None, NaN, vazio, lixo e tipos estranhos viram None.
    """
    if not isinstance(codigo, str):
        return None
    cat = codigo.strip().upper().replace(".", "")[:3]
    return cat if _CID_RE.match(cat) else None


# destaque=True: os 6 capítulos exigidos no enunciado. Os demais existem para
# que o denominador "total geral" e a extensão para outras doenças funcionem.
CAPITULOS: list[dict] = [
    {"id": "I",     "nome": "Doenças Infecciosas e Parasitárias",                 "inicio": "A00", "fim": "B99", "destaque": True},
    {"id": "II",    "nome": "Neoplasias (Tumores)",                               "inicio": "C00", "fim": "D48", "destaque": True},
    {"id": "III",   "nome": "Doenças do Sangue e Órgãos Hematopoéticos",          "inicio": "D50", "fim": "D89", "destaque": False},
    {"id": "IV",    "nome": "Doenças Endócrinas, Nutricionais e Metabólicas",     "inicio": "E00", "fim": "E90", "destaque": True},
    {"id": "V",     "nome": "Transtornos Mentais e Comportamentais",              "inicio": "F00", "fim": "F99", "destaque": False},
    {"id": "VI",    "nome": "Doenças do Sistema Nervoso",                         "inicio": "G00", "fim": "G99", "destaque": False},
    {"id": "VII",   "nome": "Doenças do Olho e Anexos",                           "inicio": "H00", "fim": "H59", "destaque": False},
    {"id": "VIII",  "nome": "Doenças do Ouvido e da Apófise Mastóide",            "inicio": "H60", "fim": "H95", "destaque": False},
    {"id": "IX",    "nome": "Doenças do Aparelho Circulatório",                   "inicio": "I00", "fim": "I99", "destaque": True},
    {"id": "X",     "nome": "Doenças do Aparelho Respiratório",                   "inicio": "J00", "fim": "J99", "destaque": True},
    {"id": "XI",    "nome": "Doenças do Aparelho Digestivo",                      "inicio": "K00", "fim": "K93", "destaque": False},
    {"id": "XII",   "nome": "Doenças da Pele e do Tecido Subcutâneo",             "inicio": "L00", "fim": "L99", "destaque": False},
    {"id": "XIII",  "nome": "Doenças do Sistema Osteomuscular e Tecido Conjuntivo","inicio": "M00", "fim": "M99", "destaque": False},
    {"id": "XIV",   "nome": "Doenças do Aparelho Geniturinário",                  "inicio": "N00", "fim": "N99", "destaque": False},
    {"id": "XV",    "nome": "Gravidez, Parto e Puerpério",                        "inicio": "O00", "fim": "O99", "destaque": False},
    {"id": "XVI",   "nome": "Afecções Originadas no Período Perinatal",           "inicio": "P00", "fim": "P96", "destaque": False},
    {"id": "XVII",  "nome": "Malformações Congênitas e Anomalias Cromossômicas",  "inicio": "Q00", "fim": "Q99", "destaque": False},
    {"id": "XVIII", "nome": "Sintomas, Sinais e Achados Anormais",                "inicio": "R00", "fim": "R99", "destaque": False},
    {"id": "XIX",   "nome": "Lesões, Envenenamentos e Outras Causas Externas",    "inicio": "S00", "fim": "T98", "destaque": False},
    {"id": "XX",    "nome": "Causas Externas de Morbidade e Mortalidade",         "inicio": "V01", "fim": "Y98", "destaque": True},
    {"id": "XXI",   "nome": "Fatores que Influenciam o Estado de Saúde",          "inicio": "Z00", "fim": "Z99", "destaque": False},
    {"id": "XXII",  "nome": "Códigos para Propósitos Especiais",                  "inicio": "U00", "fim": "U99", "destaque": False},
]

# Subgrupos nomeados de interesse (não se sobrepõem).
GRUPOS: list[dict] = [
    {"id": "iam",         "nome": "Infarto Agudo do Miocárdio", "capitulo": "IX", "inicio": "I21", "fim": "I21"},
    {"id": "hipertensao", "nome": "Hipertensão",                "capitulo": "IX", "inicio": "I10", "fim": "I15"},
    {"id": "avc",         "nome": "AVC",                        "capitulo": "IX", "inicio": "I60", "fim": "I69"},
    {"id": "pneumonia",   "nome": "Pneumonia",                  "capitulo": "X",  "inicio": "J12", "fim": "J18"},
    {"id": "asma",        "nome": "Asma",                       "capitulo": "X",  "inicio": "J45", "fim": "J45"},
    {"id": "dpoc",        "nome": "DPOC",                       "capitulo": "X",  "inicio": "J44", "fim": "J44"},
    {"id": "diabetes",    "nome": "Diabetes Mellitus",          "capitulo": "IV", "inicio": "E10", "fim": "E14"},
]


def _em_faixa(cat: str, inicio: str, fim: str) -> bool:
    return _key(inicio) <= _key(cat) <= _key(fim)


def cid_to_chapter(codigo: object) -> Optional[str]:
    """Id do capítulo (ex.: 'IX') ou None se o CID for inválido/fora de qualquer capítulo."""
    cat = normalizar_cid(codigo)
    if cat is None:
        return None
    for cap in CAPITULOS:
        if _em_faixa(cat, cap["inicio"], cap["fim"]):
            return cap["id"]
    return None


def cid_to_grupo(codigo: object) -> Optional[str]:
    """Id do subgrupo de interesse (ex.: 'iam') ou None."""
    cat = normalizar_cid(codigo)
    if cat is None:
        return None
    for g in GRUPOS:
        if _em_faixa(cat, g["inicio"], g["fim"]):
            return g["id"]
    return None


# ------------------------------------------------------------------- UFs
UFS: list[dict] = [
    {"sigla": "RO", "codigo": 11, "nome": "Rondônia"},
    {"sigla": "AC", "codigo": 12, "nome": "Acre"},
    {"sigla": "AM", "codigo": 13, "nome": "Amazonas"},
    {"sigla": "RR", "codigo": 14, "nome": "Roraima"},
    {"sigla": "PA", "codigo": 15, "nome": "Pará"},
    {"sigla": "AP", "codigo": 16, "nome": "Amapá"},
    {"sigla": "TO", "codigo": 17, "nome": "Tocantins"},
    {"sigla": "MA", "codigo": 21, "nome": "Maranhão"},
    {"sigla": "PI", "codigo": 22, "nome": "Piauí"},
    {"sigla": "CE", "codigo": 23, "nome": "Ceará"},
    {"sigla": "RN", "codigo": 24, "nome": "Rio Grande do Norte"},
    {"sigla": "PB", "codigo": 25, "nome": "Paraíba"},
    {"sigla": "PE", "codigo": 26, "nome": "Pernambuco"},
    {"sigla": "AL", "codigo": 27, "nome": "Alagoas"},
    {"sigla": "SE", "codigo": 28, "nome": "Sergipe"},
    {"sigla": "BA", "codigo": 29, "nome": "Bahia"},
    {"sigla": "MG", "codigo": 31, "nome": "Minas Gerais"},
    {"sigla": "ES", "codigo": 32, "nome": "Espírito Santo"},
    {"sigla": "RJ", "codigo": 33, "nome": "Rio de Janeiro"},
    {"sigla": "SP", "codigo": 35, "nome": "São Paulo"},
    {"sigla": "PR", "codigo": 41, "nome": "Paraná"},
    {"sigla": "SC", "codigo": 42, "nome": "Santa Catarina"},
    {"sigla": "RS", "codigo": 43, "nome": "Rio Grande do Sul"},
    {"sigla": "MS", "codigo": 50, "nome": "Mato Grosso do Sul"},
    {"sigla": "MT", "codigo": 51, "nome": "Mato Grosso"},
    {"sigla": "GO", "codigo": 52, "nome": "Goiás"},
    {"sigla": "DF", "codigo": 53, "nome": "Distrito Federal"},
]
UF_POR_SIGLA = {u["sigla"]: u for u in UFS}


def uf_valida(sigla: object) -> bool:
    return isinstance(sigla, str) and sigla.upper() in UF_POR_SIGLA


def municipio6(codigo: object) -> Optional[str]:
    """Padroniza código IBGE de município para 6 dígitos (sem dígito verificador)."""
    if codigo is None:
        return None
    s = re.sub(r"\D", "", str(codigo))
    if len(s) == 7:      # IBGE completo -> remove dígito verificador
        s = s[:6]
    return s if len(s) == 6 else None


# ------------------------------------------------------- Faixas etárias
FAIXAS_ETARIAS: list[dict] = [
    {"id": "0-14",  "min": 0,  "max": 14},
    {"id": "15-29", "min": 15, "max": 29},
    {"id": "30-49", "min": 30, "max": 49},
    {"id": "50-64", "min": 50, "max": 64},
    {"id": "65+",   "min": 65, "max": None},
]


def idade_para_anos(idade: object, cod_idade: object) -> Optional[float]:
    """Converte IDADE + COD_IDADE (SIH) para anos. None se inválido.

    COD_IDADE (SIH): 1=horas, 2=dias, 3=meses, 4=anos, 5=100 anos ou mais
    (IDADE guarda o excedente: 3 -> 103). O código 5 foi inferido dos dados reais
    (PB 2023-01: cod 4 vai até 99; cod 5 vai de 0 a 7).
    """
    try:
        valor = float(idade)  # type: ignore[arg-type]
        cod = int(float(cod_idade))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if valor != valor or valor < 0:  # NaN ou negativo
        return None
    if cod == 5:
        return 100.0 + valor
    fator = {1: 1 / 8760, 2: 1 / 365, 3: 1 / 12, 4: 1.0}.get(cod)
    return None if fator is None else valor * fator


def faixa_etaria(anos: Optional[float]) -> Optional[str]:
    if anos is None:
        return None
    for f in FAIXAS_ETARIAS:
        if anos >= f["min"] and (f["max"] is None or anos < f["max"] + 1):
            return f["id"]
    return None


# -------------------------------------------------- Sexo e caráter (SIH)
SEXOS: list[dict] = [
    {"id": "M", "nome": "Masculino"},
    {"id": "F", "nome": "Feminino"},
    {"id": "I", "nome": "Ignorado"},
]


def normalizar_sexo(valor: object) -> str:
    """SIH: 1=masculino, 3=feminino (2 em layouts antigos); resto -> ignorado."""
    s = str(valor).strip().lstrip("0") if valor is not None else ""
    return {"1": "M", "2": "F", "3": "F"}.get(s, "I")


CARATER_ATENDIMENTO: list[dict] = [
    {"id": "eletivo",  "nome": "Eletivo"},
    {"id": "urgencia", "nome": "Urgência"},
    {"id": "outros",   "nome": "Outros"},
]


def normalizar_carater(valor: object) -> str:
    """CAR_INT: 01=eletivo, 02=urgência; demais códigos (acidentes etc.) -> outros."""
    s = str(valor).strip().lstrip("0") if valor is not None else ""
    return {"1": "eletivo", "2": "urgencia"}.get(s, "outros")


COMPLEXIDADES: list[dict] = [
    {"id": "atencao_basica", "nome": "Atenção básica"},
    {"id": "media",          "nome": "Média complexidade"},
    {"id": "alta",           "nome": "Alta complexidade"},
    {"id": "nao_informada",  "nome": "Não informada"},
]


def normalizar_complexidade(valor: object) -> str:
    """COMPLEX (SIH): 01=atenção básica, 02=média, 03=alta; demais -> não informada.

    Observado no RD de PB 2023-01: só 02 e 03 aparecem.
    """
    s = str(valor).strip().lstrip("0") if valor is not None else ""
    return {"1": "atencao_basica", "2": "media", "3": "alta"}.get(s, "nao_informada")


def meta_filtros() -> dict:
    """Payload estático para GET /meta/filtros (a API acrescenta os períodos do banco)."""
    return {
        "capitulos": CAPITULOS,
        "grupos": GRUPOS,
        "ufs": UFS,
        "faixas_etarias": FAIXAS_ETARIAS,
        "sexos": SEXOS,
        "carater_atendimento": CARATER_ATENDIMENTO,
        "complexidades": COMPLEXIDADES,
    }
