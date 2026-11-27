"""Testes de integração: cria um DuckDB pequeno e chama os endpoints de verdade."""
import duckdb
import pytest
from fastapi.testclient import TestClient

from src import db as dbmod
from src.app import app

LINHAS = """
 ('PB','2023-01-10','2023-01','2023-01','IX','iam','I21','65+','M','urgencia','media','250750',true ,5,1000),
 ('PB','2023-01-20','2023-01','2023-01','IX','hipertensao','I10','50-64','F','eletivo','media','250750',false,3,500),
 ('PB','2023-02-05','2023-02','2023-02','X','asma','J45','0-14','F','urgencia','alta','250910',false,2,300),
 ('PB','2023-02-15','2023-02','2023-02','X','pneumonia','J18','65+','M','urgencia','alta','250910',true ,10,2000),
 ('PB','2023-02-20','2023-02','2023-02','X','pneumonia','J18','65+','F','urgencia','media','250910',false,8,1500),
 ('PB','2023-03-01','2023-03','2023-03','IX','avc','I64','65+','F','urgencia','media','250750',false,4,700)
"""


@pytest.fixture()
def client(tmp_path, monkeypatch):
    caminho = tmp_path / "teste.duckdb"
    con = duckdb.connect(str(caminho))
    con.execute("""CREATE TABLE internacoes (uf VARCHAR, data_internacao TIMESTAMP, ano_mes VARCHAR,
        competencia VARCHAR, capitulo_id VARCHAR, grupo_id VARCHAR, cid3 VARCHAR, faixa_etaria VARCHAR,
        sexo VARCHAR, carater VARCHAR, complexidade VARCHAR, municipio_res VARCHAR, obito BOOLEAN,
        dias_perm DOUBLE, val_tot DOUBLE, n_aih VARCHAR, diag_princ VARCHAR, data_saida TIMESTAMP,
        idade_anos DOUBLE, especialidade VARCHAR)""")
    con.execute("""INSERT INTO internacoes (uf, data_internacao, ano_mes, competencia, capitulo_id, grupo_id, cid3,
        faixa_etaria, sexo, carater, complexidade, municipio_res, obito, dias_perm, val_tot)
        VALUES """ + LINHAS)
    con.close()
    monkeypatch.setenv("DUCKDB_PATH", str(caminho))
    dbmod.fechar()
    yield TestClient(app)
    dbmod.fechar()


def test_health_e_meta(client):
    assert client.get("/health").json() == {"status": "ok", "banco": True}
    m = client.get("/meta/filtros").json()
    assert any(c["id"] == "IX" for c in m["capitulos"])
    assert m["periodo"]["competencia_min"] == "2023-01" and m["ufs_disponiveis"] == ["PB"]


def test_kpis_sem_filtro(client):
    a = client.get("/kpis").json()["atual"]
    assert a["total"] == 6 and a["obitos"] == 2 and a["taxa_mortalidade"] == 33.33
    assert a["custo_total"] == 6000.0 and a["permanencia_media"] == pytest.approx(5.33)


def test_kpis_capitulo_e_proporcao(client):
    a = client.get("/kpis", params={"capitulo_ids": ["IX"]}).json()["atual"]
    assert a["total"] == 3 and a["total_geral"] == 6 and a["proporcao_total_geral"] == 50.0


def test_kpis_variacao_periodo_anterior_e_yoy(client):
    r = client.get("/kpis", params={"data_inicio": "2023-02-01", "data_fim": "2023-02-28"}).json()
    assert r["atual"]["total"] == 3 and r["anterior"]["total"] == 2
    assert r["variacao_pct"]["total"] == 50.0
    r = client.get("/kpis", params={"data_inicio": "2023-02-01", "data_fim": "2023-02-28",
                                    "comparacao": "ano_anterior"}).json()
    assert r["anterior"]["total"] == 0 and r["variacao_pct"]["total"] is None   # sem divisão por zero


def test_filtro_faixa_65_mais(client):
    assert client.get("/kpis", params={"faixas_etarias": ["65+"]}).json()["atual"]["total"] == 4


def test_resultado_vazio_nao_quebra(client):
    a = client.get("/kpis", params={"uf": "SP"}).json()["atual"]
    assert a["total"] == 0 and a["taxa_mortalidade"] is None and a["custo_medio"] is None
    assert client.get("/serie-temporal", params={"uf": "SP"}).json()["series"] == []


def test_validacao_422(client):
    for params in ({"data_inicio": "2023-03-01", "data_fim": "2023-01-01"}, {"capitulo_ids": ["ZZ"]},
                   {"uf": "XX"}, {"cid_codigos": ["lixo"]}, {"data_inicio": "nao-e-data"}):
        assert client.get("/kpis", params=params).status_code == 422


def test_serie_temporal_preenche_meses_zerados(client):
    r = client.get("/serie-temporal", params={"data_inicio": "2023-01-01", "data_fim": "2023-03-31"}).json()
    assert r["meses"] == ["2023-01", "2023-02", "2023-03"]
    por_id = {s["id"]: [p["casos"] for p in s["pontos"]] for s in r["series"]}
    assert por_id == {"IX": [2, 0, 1], "X": [0, 3, 0]}
    total = client.get("/serie-temporal", params={"agrupar_por": "total"}).json()["series"][0]
    assert total["id"] == "TOTAL" and [p["casos"] for p in total["pontos"]] == [2, 3, 1]


def test_sem_banco_responde_503(tmp_path, monkeypatch):
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "nao_existe.duckdb"))
    dbmod.fechar()
    c = TestClient(app)
    assert c.get("/health").json()["status"] == "sem_dados"
    assert c.get("/kpis").status_code == 503


def test_demografia_piramide(client):
    r = client.get("/demografia").json()
    por_faixa = {x["faixa"]: x for x in r["faixas"]}
    assert [x["faixa"] for x in r["faixas"]] == ["0-14", "15-29", "30-49", "50-64", "65+"]
    assert (por_faixa["65+"]["M"], por_faixa["65+"]["F"], por_faixa["65+"]["total"]) == (2, 2, 4)
    assert por_faixa["0-14"]["F"] == 1 and por_faixa["15-29"]["total"] == 0
    assert r["sem_faixa"] == 0
    filtrado = client.get("/demografia", params={"sexos": ["F"]}).json()
    assert sum(x["M"] for x in filtrado["faixas"]) == 0
    assert client.get("/demografia", params={"uf": "SP"}).json()["faixas"][0]["total"] == 0


def test_top_cid(client):
    r = client.get("/top-cid", params={"limite": 3}).json()
    assert r["total_com_cid"] == 6
    assert [i["cid3"] for i in r["itens"]] == ["J18", "I10", "I21"]      # empates por código
    j18 = r["itens"][0]
    assert (j18["casos"], j18["obitos"], j18["percentual"]) == (2, 1, 33.33)
    assert j18["capitulo_id"] == "X" and "Respiratório" in j18["capitulo_nome"]
    assert j18["grupo_nome"] is not None
    ix = client.get("/top-cid", params={"capitulo_ids": ["IX"]}).json()
    assert {i["cid3"] for i in ix["itens"]} == {"I21", "I10", "I64"}
    assert client.get("/top-cid", params={"limite": 0}).status_code == 422
    assert client.get("/top-cid", params={"uf": "SP"}).json()["itens"] == []


def test_export_csv(client):
    r = client.get("/export.csv")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert 'attachment; filename="internacoes.csv"' in r.headers["content-disposition"]
    assert r.headers["x-total-registros"] == "6" and r.headers["x-registros-exportados"] == "6"
    linhas = r.content.decode("utf-8-sig").strip().splitlines()
    assert linhas[0].startswith("data_internacao,data_saida,uf,municipio_res") and len(linhas) == 7
    assert "2023-01-10,,PB,250750" in linhas[1]                       # data sem hora, data_saida vazia


def test_export_csv_filtros_e_separador(client):
    r = client.get("/export.csv", params={"capitulo_ids": ["X"], "separador": ";", "uf": "PB"})
    linhas = r.content.decode("utf-8-sig").strip().splitlines()
    assert len(linhas) == 4 and linhas[0].split(";")[2] == "uf"
    assert 'filename="internacoes_PB.csv"' in r.headers["content-disposition"]
    vazio = client.get("/export.csv", params={"uf": "SP"})
    assert len(vazio.content.decode("utf-8-sig").strip().splitlines()) == 1     # só o cabeçalho


def test_export_csv_validacao_e_limite(client, monkeypatch):
    assert client.get("/export.csv", params={"uf": "XX"}).status_code == 422
    assert client.get("/export.csv", params={"separador": "|"}).status_code == 422
    monkeypatch.setenv("EXPORT_MAX_ROWS", "2")
    r = client.get("/export.csv")
    assert len(r.content.decode("utf-8-sig").strip().splitlines()) == 3
    assert r.headers["x-total-registros"] == "6" and r.headers["x-registros-exportados"] == "2"


def test_meta_informa_limite_e_capitulos_padrao(client, monkeypatch):
    monkeypatch.setenv("EXPORT_MAX_ROWS", "1234")
    m = client.get("/meta/filtros").json()
    assert m["export_max_linhas"] == 1234
    assert [c["id"] for c in m["capitulos"] if c["padrao"]] == ["IX", "X"]


def test_meta_fonte_e_kpis_municipios_atendidos(client):
    m = client.get("/meta/filtros").json()
    assert m["periodo"]["fonte"] == "SIH/SUS (RD — DATASUS)"
    assert m["periodo"]["ultima_atualizacao"]
    a = client.get("/kpis").json()["atual"]
    assert a["municipios_atendidos"] == 2
    # filtro por bloco CID-10 oficial
    blk = client.get("/kpis", params={"grupo_ids": ["I20-I25"]}).json()["atual"]
    assert blk["total"] == 1


def test_cid_grupos_e_resolver(client):
    grupos = client.get("/cid/grupos").json()
    assert len(grupos) >= 4
    assert grupos[0]["id"] == "J09-J18" and grupos[0]["internacoes"] == 2
    # ignora grupo_ids/cid_codigos mas respeita capitulo_ids
    grupos_ix = client.get("/cid/grupos", params={"capitulo_ids": ["IX"], "grupo_ids": ["iam"]}).json()
    assert all(g["capitulo"] == "IX" for g in grupos_ix) and len(grupos_ix) == 3

    res_ok = client.get("/cid/resolver", params={"codigo": "I21.9"}).json()
    assert res_ok["valido"] is True and res_ok["cid3"] == "I21"
    assert res_ok["bloco"]["id"] == "I20-I25" and res_ok["grupo_prioritario"]["id"] == "iam"

    res_bad = client.get("/cid/resolver", params={"codigo": "invalido"}).json()
    assert res_bad == {"valido": False, "cid3": None, "capitulo": None, "bloco": None, "grupo_prioritario": None}
