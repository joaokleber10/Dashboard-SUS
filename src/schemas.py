"""Modelo único de filtros, reaproveitado por todos os endpoints."""
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from src.dictionary import (
    BLOCOS_CID10, CAPITULOS, CARATER_ATENDIMENTO, COMPLEXIDADES, FAIXAS_ETARIAS, GRUPOS, SEXOS,
    municipio6, normalizar_cid, uf_valida,
)

_VALIDOS = {
    "capitulo_ids": {c["id"] for c in CAPITULOS},
    "grupo_ids": {g["id"] for g in GRUPOS} | {b["id"] for b in BLOCOS_CID10},
    "faixas_etarias": {f["id"] for f in FAIXAS_ETARIAS},
    "sexos": {s["id"] for s in SEXOS},
    "carater": {c["id"] for c in CARATER_ATENDIMENTO},
    "complexidade": {c["id"] for c in COMPLEXIDADES},
}


class Filtros(BaseModel):
    capitulo_ids: list[str] = Field(default_factory=list)
    grupo_ids: list[str] = Field(default_factory=list)
    cid_codigos: list[str] = Field(default_factory=list)
    uf: Optional[str] = None
    municipio: Optional[str] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    faixas_etarias: list[str] = Field(default_factory=list)
    sexos: list[str] = Field(default_factory=list)
    carater: list[str] = Field(default_factory=list)
    complexidade: list[str] = Field(default_factory=list)
    comparacao: Literal["nenhuma", "periodo_anterior", "ano_anterior"] = "periodo_anterior"

    @field_validator("capitulo_ids", "grupo_ids", "faixas_etarias", "sexos", "carater", "complexidade")
    @classmethod
    def _ids_validos(cls, valores: list[str], info):
        limpos = [v.strip() for v in valores if v and v.strip()]
        if info.field_name == "faixas_etarias":
            # '65+' chega como '65 ' se o '+' não for codificado como %2B na URL
            limpos = ["65+" if v == "65" else v for v in limpos]
        invalidos = [v for v in limpos if v not in _VALIDOS[info.field_name]]
        if invalidos:
            raise ValueError(f"valores inválidos {invalidos}; aceitos: {sorted(_VALIDOS[info.field_name])}")
        return list(dict.fromkeys(limpos))

    @field_validator("cid_codigos")
    @classmethod
    def _cids_validos(cls, valores: list[str]):
        normalizados, invalidos = [], []
        for v in valores:
            n = normalizar_cid(v)
            (normalizados if n else invalidos).append(n or v)
        if invalidos:
            raise ValueError(f"códigos CID-10 inválidos: {invalidos} (use o formato I21 ou I21.9)")
        return sorted(set(normalizados))

    @field_validator("uf")
    @classmethod
    def _uf(cls, v: Optional[str]):
        if v is None or v == "":
            return None
        if not uf_valida(v):
            raise ValueError(f"UF inexistente: {v!r}")
        return v.upper()

    @field_validator("municipio")
    @classmethod
    def _municipio(cls, v: Optional[str]):
        if v is None or v == "":
            return None
        m = municipio6(v)
        if m is None:
            raise ValueError(f"código de município inválido: {v!r} (use o código IBGE de 6 ou 7 dígitos)")
        return m

    @model_validator(mode="after")
    def _periodo_coerente(self):
        if self.data_inicio and self.data_fim and self.data_inicio > self.data_fim:
            raise ValueError("data_inicio não pode ser maior que data_fim")
        return self
