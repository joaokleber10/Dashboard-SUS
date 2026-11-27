import pandas as pd

from src.catalogos import carregar_catalogo, catalogo_por_blocos

BLOCOS = [
    {"id": "I20-I25", "nome": "Doenças isquêmicas do coração", "capitulo": "IX", "inicio": "I20", "fim": "I25"},
    {"id": "J12-J18", "nome": "Pneumonia", "capitulo": "X", "inicio": "J12", "fim": "J18"},
    {"id": "X85-Y09", "nome": "Agressões", "capitulo": "XX", "inicio": "X85", "fim": "Y09"},
    {"id": "X99-X01", "nome": "Bloco invertido", "capitulo": "XX", "inicio": "X99", "fim": "X01"},
]


def test_blocos_expandem_para_categorias():
    df = catalogo_por_blocos(BLOCOS).set_index("cid3")["cid_nome"]
    assert df["I21"] == "Doenças isquêmicas do coração (bloco I20-I25)"
    assert df["J18"].startswith("Pneumonia") and "I26" not in df.index and "X50" not in df.index
    assert df["Y05"].startswith("Agressões") and df["X99"].startswith("Agressões")
    assert len(df) == 6 + 7 + 25                         # bloco inválido ignorado, sem exceção


def test_csv_tem_prioridade_e_blocos_completam(tmp_path):
    csv = tmp_path / "cid10.csv"
    csv.write_text("CAT;DESCRICAO\nI21;Infarto agudo do miocárdio\n", encoding="utf-8")
    df = carregar_catalogo(csv, BLOCOS).set_index("cid3")["cid_nome"]
    assert df["I21"] == "Infarto agudo do miocárdio"           # nome exato vence
    assert df["I20"].endswith("(bloco I20-I25)")              # o resto vem do bloco
    assert df.index.is_unique


def test_sem_csv_usa_so_blocos_e_sem_nada_fica_vazio(tmp_path):
    assert len(carregar_catalogo(tmp_path / "nao_existe.csv", BLOCOS)) == 38
    assert len(carregar_catalogo(tmp_path / "nao_existe.csv", [])) == 0
    assert isinstance(carregar_catalogo(tmp_path / "x.csv", []), pd.DataFrame)