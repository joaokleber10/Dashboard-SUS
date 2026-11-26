import math
import pytest
from src.dictionary import (
    normalizar_cid, cid_to_chapter, cid_to_grupo, municipio6, idade_para_anos,
    faixa_etaria, normalizar_complexidade, normalizar_sexo, normalizar_carater, uf_valida, CAPITULOS,
)


@pytest.mark.parametrize("codigo,esperado", [
    ("I21", "IX"), ("I21.9", "IX"), ("i219", "IX"), (" J45 ", "X"),
    ("C80", "II"), ("D48", "II"),
    ("D50", "III"),            # fora de neoplasias
    ("A00", "I"), ("B99", "I"), ("V01", "XX"), ("Y98", "XX"), ("E14", "IV"),
    ("", None), (None, None), (float("nan"), None), ("XYZ", None), ("12", None), (123, None),
])
def test_cid_to_chapter(codigo, esperado):
    assert cid_to_chapter(codigo) == esperado


def test_capitulos_nao_se_sobrepoem():
    from src.dictionary import _key
    faixas = sorted((_key(c["inicio"]), _key(c["fim"])) for c in CAPITULOS)
    for (_, fim_a), (ini_b, _) in zip(faixas, faixas[1:]):
        assert fim_a < ini_b


def test_normalizar_cid():
    assert normalizar_cid("i21.0") == "I21"
    assert normalizar_cid("") is None


@pytest.mark.parametrize("codigo,esperado", [
    ("I21", "iam"), ("I10", "hipertensao"), ("I15", "hipertensao"), ("I64", "avc"),
    ("J13", "pneumonia"), ("J45", "asma"), ("J44", "dpoc"), ("E11", "diabetes"),
    ("I50", None), ("lixo", None),
])
def test_cid_to_grupo(codigo, esperado):
    assert cid_to_grupo(codigo) == esperado


def test_municipio6():
    assert municipio6("2507507") == "250750"
    assert municipio6(250750) == "250750"
    assert municipio6("abc") is None and municipio6(None) is None


def test_idade_e_faixa():
    assert idade_para_anos(6, 3) == pytest.approx(0.5)      # 6 meses
    assert faixa_etaria(idade_para_anos(6, 3)) == "0-14"    # bebê não vira adulto
    assert faixa_etaria(idade_para_anos(30, 4)) == "30-49"
    assert faixa_etaria(idade_para_anos(14, 4)) == "0-14"
    assert faixa_etaria(idade_para_anos(15, 4)) == "15-29"
    assert faixa_etaria(idade_para_anos(65, 4)) == "65+"
    assert faixa_etaria(idade_para_anos(100, 4)) == "65+"
    assert idade_para_anos(None, 4) is None
    assert idade_para_anos(10, 9) is None
    assert idade_para_anos(math.nan, 4) is None
    assert faixa_etaria(None) is None


def test_sexo_carater_uf():
    assert normalizar_sexo("1") == "M" and normalizar_sexo(3) == "F"
    assert normalizar_sexo("0") == "I" and normalizar_sexo(None) == "I"
    assert normalizar_carater("01") == "eletivo" and normalizar_carater("2") == "urgencia"
    assert normalizar_carater("05") == "outros"
    assert uf_valida("pb") and not uf_valida("XX")


def test_complexidade():
    assert normalizar_complexidade("02") == "media" and normalizar_complexidade("03") == "alta"
    assert normalizar_complexidade("01") == "atencao_basica"
    assert normalizar_complexidade(None) == "nao_informada" and normalizar_complexidade("00") == "nao_informada"


def test_idade_cod5_cem_anos_ou_mais():
    assert idade_para_anos(3, 5) == 103.0
    assert faixa_etaria(idade_para_anos(0, 5)) == "65+"
    assert idade_para_anos(10, 9) is None   # código desconhecido continua None


def test_capitulos_padrao_vem_do_dicionario():
    assert [c["id"] for c in CAPITULOS if c["padrao"]] == ["IX", "X"]
    assert all(c["destaque"] for c in CAPITULOS if c["padrao"])
