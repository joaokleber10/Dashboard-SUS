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
        dias_perm DOUBLE, val_tot DOUBLE)""")
    con.execute(f"INSERT INTO internacoes VALUES {LINHAS}")
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


def test_meta_fonte_e_kpis_municipios_atendidos(client):
    m = client.get("/meta/filtros").json()
    assert m["periodo"]["fonte"] == "SIH/SUS (RD — DATASUS)"
    assert m["periodo"]["ultima_atualizacao"]
    a = client.get("/kpis").json()["atual"]
    assert a["municipios_atendidos"] == 2
    # filtro por bloco CID-10 oficial
    blk = client.get("/kpis", params={"grupo_ids": ["I20-I25"]}).json()["atual"]
    assert blk["total"] == 1


def test_top_municipios_busca_e_favoritos(client):
    r = client.get("/top-municipios", params={"limite": 10}).json()
    assert r["total_municipios"] == 2
    codigos = [i["codigo"] for i in r["itens"]]
    assert set(codigos) == {"250750", "250910"}
    jp = next(i for i in r["itens"] if i["codigo"] == "250750")
    assert jp["nome"] == "João Pessoa - PB" and jp["casos"] == 3 and jp["obitos"] == 1

    # ignora filtro de municipio para manter a lista navegável
    r_mun = client.get("/top-municipios", params={"municipio": "250750"}).json()
    assert r_mun["total_municipios"] == 2

    # favoritos (incluindo um sem casos no recorte) aparecem no topo
    r_fav = client.get("/top-municipios", params={"favoritos": ["250400", "250910"]}).json()
    assert [i["codigo"] for i in r_fav["itens"][:2]] == ["250910", "250400"]
    assert r_fav["itens"][0]["favorito"] is True
    assert r_fav["itens"][1]["casos"] == 0 and r_fav["itens"][1]["nome"] == "Campina Grande - PB"

    # busca sem acento e por código
    r_busca = client.get("/top-municipios", params={"busca": "joao pessoa"}).json()
    assert len(r_busca["itens"]) == 1 and r_busca["itens"][0]["codigo"] == "250750"
    r_cod = client.get("/top-municipios", params={"busca": "250910"}).json()
    assert len(r_cod["itens"]) == 1 and r_cod["itens"][0]["codigo"] == "250910"


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


def test_export_csv(client):
    resp = client.get("/export/csv", params={"capitulo_ids": ["IX"]})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert 'filename="internacoes_sus.csv"' in resp.headers["content-disposition"]
    linhas = resp.text.strip().splitlines()
    assert linhas[0].startswith("n_aih,uf,ano_mes,data_internacao,data_saida,cid3")
    assert len(linhas) == 4  # cabeçalho + 3 linhas do capítulo IX
