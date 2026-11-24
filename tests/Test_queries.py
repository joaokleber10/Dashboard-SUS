from datetime import date

from src.queries import build_where, meses_entre, periodo_anterior
from src.schemas import Filtros


def test_where_vazio():
    assert build_where(Filtros()) == ("", [])


def test_where_parametrizado_e_sem_cid():
    f = Filtros(capitulo_ids=["IX", "X"], cid_codigos=["i21.9"], uf="pb", sexos=["F"],
                data_inicio=date(2023, 1, 1), data_fim=date(2023, 1, 31))
    where, params = build_where(f)
    assert "capitulo_id IN (?,?)" in where and "cid3 IN (?)" in where and "uf = ?" in where
    assert params[:3] == ["IX", "X", "I21"] and "PB" in params and date(2023, 2, 1) in params
    assert "'" not in where and "IX" not in where          # valores nunca vão no SQL
    where2, params2 = build_where(f, incluir_cid=False)
    assert "capitulo_id" not in where2 and "cid3" not in where2 and "IX" not in params2


def test_periodo_anterior():
    # meses de calendário inteiros -> os mesmos meses imediatamente antes
    f = Filtros(data_inicio=date(2023, 7, 1), data_fim=date(2023, 7, 31))
    assert periodo_anterior(f) == (date(2023, 6, 1), date(2023, 6, 30))
    f = Filtros(data_inicio=date(2023, 2, 1), data_fim=date(2023, 2, 28))
    assert periodo_anterior(f) == (date(2023, 1, 1), date(2023, 1, 31))
    f = Filtros(data_inicio=date(2023, 1, 1), data_fim=date(2023, 1, 31))
    assert periodo_anterior(f) == (date(2022, 12, 1), date(2022, 12, 31))   # vira o ano
    f = Filtros(data_inicio=date(2023, 4, 1), data_fim=date(2023, 6, 30))
    assert periodo_anterior(f) == (date(2023, 1, 1), date(2023, 3, 31))     # trimestre
    # recorte livre -> mesma quantidade de dias antes
    f = Filtros(data_inicio=date(2023, 2, 10), data_fim=date(2023, 2, 19))
    assert periodo_anterior(f) == (date(2023, 1, 31), date(2023, 2, 9))
    f = Filtros(data_inicio=date(2024, 2, 29), data_fim=date(2024, 3, 31), comparacao="ano_anterior")
    assert periodo_anterior(f) == (date(2023, 2, 28), date(2023, 3, 31))
    assert periodo_anterior(Filtros(data_inicio=date(2023, 1, 1))) is None


def test_meses_entre():
    assert meses_entre("2022-11", "2023-02") == ["2022-11", "2022-12", "2023-01", "2023-02"]
    assert meses_entre("2023-03", "2023-03") == ["2023-03"]


def test_filtros_validacao():
    import pytest
    from pydantic import ValidationError
    for ruim in ({"capitulo_ids": ["ZZ"]}, {"uf": "XX"}, {"cid_codigos": ["lixo"]},
                 {"municipio": "abc"}, {"data_inicio": date(2023, 2, 1), "data_fim": date(2023, 1, 1)}):
        with pytest.raises(ValidationError):
            Filtros(**ruim)
    assert Filtros(faixas_etarias=["65"]).faixas_etarias == ["65+"]
    assert Filtros(municipio="2507507").municipio == "250750"
