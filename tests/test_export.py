from datetime import date
from types import SimpleNamespace

from src.export import gerar_csv, limite_export, nome_arquivo
from src.queries import COLUNAS_EXPORT, consulta_export
from src.schemas import Filtros


class CursorFalso:
    def __init__(self, linhas):
        self.linhas, self.fechado = list(linhas), False

    def fetchmany(self, n):
        lote, self.linhas = self.linhas[:n], self.linhas[n:]
        return lote

    def close(self):
        self.fechado = True


def test_gerar_csv_bom_cabecalho_lotes_e_fecha_cursor():
    cur = CursorFalso([("a", 1, None), ("b, c", 2.5, date(2023, 1, 2)), ("d", 3, "x")])
    partes = list(gerar_csv(cur, ["col1", "col2", "col3"], ",", lote=2))
    texto = "".join(partes)
    assert texto.startswith("\ufeffcol1,col2,col3\n") and len(partes) == 3      # cabeçalho + 2 lotes
    assert 'a,1,\n' in texto and '"b, c",2.5,2023-01-02' in texto                 # None vazio, vírgula entre aspas
    assert cur.fechado


def test_gerar_csv_fecha_cursor_se_o_cliente_cancelar():
    cur = CursorFalso([("a",), ("b",)])
    gerador = gerar_csv(cur, ["c"], ";", lote=1)
    next(gerador)
    gerador.close()                                                               # cliente desconectou
    assert cur.fechado


def test_nome_arquivo_e_limite(monkeypatch):
    assert nome_arquivo(SimpleNamespace(uf=None, data_inicio=None, data_fim=None)) == "internacoes.csv"
    f = SimpleNamespace(uf="PB", data_inicio=date(2023, 1, 1), data_fim=date(2023, 12, 31))
    assert nome_arquivo(f) == "internacoes_PB_2023-01-01_2023-12-31.csv"
    monkeypatch.setenv("EXPORT_MAX_ROWS", "abc")
    assert limite_export() == 500_000
    monkeypatch.setenv("EXPORT_MAX_ROWS", "-5")
    assert limite_export() == 500_000
    monkeypatch.setenv("EXPORT_MAX_ROWS", "10")
    assert limite_export() == 10


def test_consulta_export_parametrizada():
    sql, params = consulta_export(Filtros(capitulo_ids=["IX"], uf="PB"), 100)
    assert "WHERE capitulo_id IN (?) AND uf = ?" in sql and params == ["IX", "PB"]
    assert sql.endswith("LIMIT 100") and "n_aih" not in sql
    assert [c for c, _ in COLUNAS_EXPORT][:3] == ["data_internacao", "data_saida", "uf"]
