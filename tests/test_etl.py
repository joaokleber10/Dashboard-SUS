import pandas as pd
import pytest
import os
import tempfile
from pathlib import Path
from src.etl import limpar_sih, extrair_caminhos


def _raw():
    return pd.DataFrame({
        "N_AIH":      ["1", "2", "3", "4", "5", "6"],
        "DIAG_PRINC": ["I219", "J45", "XXXX", None, "C80", "J18"],
        "DT_INTER":   ["20230105", "20230230", "20230110", "20230111", 20230115, "20230112"],
        "DT_SAIDA":   ["20230110", "20230301", "20230109", "20230115", "20230120", "20230118"],
        "SEXO":       [1, 3, "0", 1, 3, 3],
        "IDADE":      [65, 40, 30, 14, 40, 6],
        "COD_IDADE":  [4, 4, 4, 4, 4, 3],
        "MORTE":      [0, 0, 0, 1, 0, 1],
        "CAR_INT":    ["02", "01", "05", "02", "01", "02"],
        "MUNIC_RES":  ["250750", "250750", 2507507, None, "250750", "abc"],
        "DIAS_PERM":  [5, 1, 2, 4, 5, 6],
        "VAL_TOT":    [1000.5, 200, 300, 400, 500, 600],
    })


def test_rejeita_data_invalida_sem_quebrar():
    limpo, rej, rel = limpar_sih(_raw(), "PB", 2023, 1)
    assert len(limpo) == 5 and len(rej) == 1
    assert rel.rejeitadas_data_invalida == 1 and rel.linhas_lidas == 6
    assert rej.iloc[0]["motivo"] == "data_internacao_invalida"


def test_cid_capitulo_e_invalidos():
    limpo, _, rel = limpar_sih(_raw(), "PB", 2023, 1)
    por_aih = limpo.set_index("n_aih")
    assert por_aih.loc["1", "capitulo_id"] == "IX" and por_aih.loc["1", "grupo_id"] == "iam"
    assert por_aih.loc["5", "capitulo_id"] == "II"
    assert pd.isna(por_aih.loc["3", "capitulo_id"]) and pd.isna(por_aih.loc["4", "cid3"])
    assert rel.cid_invalido == 2 and rel.pct_cid_invalido == pytest.approx(40.0)


def test_idade_sexo_carater_municipio_obito():
    limpo, _, rel = limpar_sih(_raw(), "PB", 2023, 1)
    p = limpo.set_index("n_aih")
    assert p.loc["6", "faixa_etaria"] == "0-14"      # 6 meses não vira adulto
    assert p.loc["1", "faixa_etaria"] == "65+"
    assert p.loc["3", "sexo"] == "I" and p.loc["1", "sexo"] == "M"
    assert p.loc["3", "carater"] == "outros" and p.loc["1", "carater"] == "urgencia"
    assert p.loc["3", "municipio_res"] == "250750"   # 7 dígitos -> 6
    assert pd.isna(p.loc["6", "municipio_res"])
    assert bool(p.loc["4", "obito"]) and not bool(p.loc["1", "obito"])
    assert rel.saida_antes_internacao == 1            # AIH 3
    assert (p["ano_mes"] == "2023-01").all() and (p["competencia"] == "2023-01").all()


def test_colunas_opcionais_ausentes_nao_quebram():
    raw = _raw()[["DIAG_PRINC", "DT_INTER"]]
    limpo, _, rel = limpar_sih(raw, "PB", 2023, 1)
    assert len(limpo) == 5 and "SEXO" in rel.colunas_ausentes
    assert (limpo["sexo"] == "I").all()


def test_essenciais_ausentes_levantam_erro_claro():
    with pytest.raises(ValueError, match="essenciais"):
        limpar_sih(pd.DataFrame({"SEXO": [1]}), "PB", 2023, 1)


class _ItemFake:  # imita um item do FileBag sem atributo de caminho conhecido
    def __init__(self, nome): self.name = nome.replace(".parquet", "")
    def __str__(self): return self.name + ".parquet"


class _BagFake:
    def __init__(self, itens): self.files = tuple(itens)


def test_extrair_caminhos_acha_arquivo_no_cache_do_pysus():
    with tempfile.TemporaryDirectory() as d:
        alvo = Path(d) / "sih" / "RD" / "2023" / "01" / "PB" / "RDPB2301.parquet"
        alvo.parent.mkdir(parents=True)
        alvo.write_bytes(b"x")
        antigo = os.environ.get("PYSUS_CACHEPATH")
        os.environ["PYSUS_CACHEPATH"] = d
        try:
            assert extrair_caminhos(_BagFake([_ItemFake("RDPB2301.parquet")])) == [alvo]
        finally:
            if antigo is None:
                os.environ.pop("PYSUS_CACHEPATH", None)
            else:
                os.environ["PYSUS_CACHEPATH"] = antigo


def test_extrair_caminhos_usa_atributo_path_quando_existe():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "a.parquet"
        f.write_bytes(b"x")
        item = type("F", (), {"path": str(f)})()
        assert extrair_caminhos(_BagFake([item])) == [f]


def test_extrair_caminhos_erro_lista_atributos():
    with pytest.raises(FileNotFoundError, match="Atributos do objeto"):
        extrair_caminhos(_BagFake([_ItemFake("NAO_EXISTE_XYZ.parquet")]))


def test_formato_do_parquet_real_tudo_texto():
    """Imita o RD de PB 2023-01 observado: todas as colunas como string (dtype object)."""
    raw = pd.DataFrame({
        "N_AIH": ["1", "2", "3"], "DIAG_PRINC": ["N390", "E871", "I739"],
        "DT_INTER": ["20230112", "20221209", "20230105"], "DT_SAIDA": ["20230115", "20221215", "20230110"],
        "MUNIC_RES": ["250910", "250730", "251272"], "MUNIC_MOV": ["250910", "250730", "251272"],
        "SEXO": ["3", "1", "3"], "IDADE": ["45", "10", "70"], "COD_IDADE": ["4", "2", "4"],
        "DIAS_PERM": ["3", "6", "5"], "VAL_TOT": ["900.50", "1200.00", "700.00"],
        "MORTE": ["0", "1", "0"], "CAR_INT": ["02", "01", "02"], "COMPLEX": ["02", "03", "02"],
        "ESPEC": ["03", "01", "03"],
    })
    limpo, rej, rel = limpar_sih(raw, "PB", 2023, 1)
    p = limpo.set_index("n_aih")
    assert len(limpo) == 3 and len(rej) == 0 and rel.cid_invalido == 0
    assert p.loc["2", "ano_mes"] == "2022-12" and p.loc["2", "competencia"] == "2023-01"
    assert p.loc["2", "faixa_etaria"] == "0-14"       # 10 dias
    assert p.loc["3", "complexidade"] == "media" and p.loc["2", "complexidade"] == "alta"
    assert p.loc["1", "sexo"] == "F" and bool(p.loc["2", "obito"])
    assert p.loc["1", "val_tot"] == 900.5


def test_cod_idade_5_nao_gera_faixa_nula():
    raw = _raw().iloc[[0, 5]].copy()
    raw["IDADE"] = [2, 7]
    raw["COD_IDADE"] = [5, 5]
    limpo, _, rel = limpar_sih(raw, "PB", 2023, 1)
    assert rel.faixa_etaria_nula == 0 and (limpo["faixa_etaria"] == "65+").all()


def test_fonte_nao_suportada_falha_com_mensagem_clara():
    from src.etl import construir_config
    with pytest.raises(SystemExit):
        construir_config(["--uf", "PB", "--source", "SIM"])
