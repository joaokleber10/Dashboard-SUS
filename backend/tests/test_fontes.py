import json

import pandas as pd
import pytest

from src.fontes import carregar_config, construir_externa, descobrir_configs

MUNICIPIOS = [
    {"codigo6": "250750", "municipio_nome": "João Pessoa", "municipio_uf": "PB"},
    {"codigo6": "251000", "municipio_nome": "Cidade Teste", "municipio_uf": "PB"},
    {"codigo6": "260001", "municipio_nome": "Cidade Teste", "municipio_uf": "PE"},
]


def _cfg(tmp_path, **extra):
    cfg = {
        "arquivo": "x.csv", "uf": "PB", "formato_data": "%d/%m/%Y", "decimal": ",",
        "colunas": {"data_internacao": "DATA", "data_saida": "ALTA", "cid": "CID", "sexo": "SEXO",
                    "idade": "IDADE", "obito": "EVOLUCAO", "valor": "VALOR", "municipio_res": "MUN"},
        "valores": {"obito": {"ÓBITO": "1"}},
    }
    cfg.update(extra)
    caminho = tmp_path / "teste.json"
    caminho.write_text(json.dumps(cfg), encoding="utf-8")
    return carregar_config(caminho)


def _origem():
    return pd.DataFrame({
        "DATA": ["05/01/2023", "10/02/2023", "sem data", "15/03/2023"],
        "ALTA": ["10/01/2023", "09/02/2023", "01/01/2023", "20/03/2023"],
        "CID": ["I21.9", "J18", "I10", "J45"],
        "SEXO": ["Masculino", "F", "Feminino", "?"],
        "IDADE": ["70", "8", "40", "55"],
        "EVOLUCAO": ["ÓBITO", "Alta", "Alta", "Desconhecido"],
        "VALOR": ["1.234,50", "200,00", "", "300,00"],
        "MUN": ["João Pessoa", "250750", "Cidade Inexistente", "Cidade Teste"],
    })


def test_mapeamento_completo(tmp_path):
    limpo, rej, rel = construir_externa(_origem(), _cfg(tmp_path), MUNICIPIOS)
    assert len(limpo) == 3 and len(rej) == 1 and rel.rejeitadas == 1 and rel.linhas_origem == 4
    por_cid = limpo.set_index("cid3")
    assert por_cid.loc["I21", "capitulo_id"] == "IX" and por_cid.loc["I21", "faixa_etaria"] == "65+"
    assert por_cid.loc["I21", "sexo"] == "M" and bool(por_cid.loc["I21", "obito"])
    assert por_cid.loc["I21", "val_tot"] == pytest.approx(1234.5)           # vírgula decimal brasileira
    assert por_cid.loc["J18", "faixa_etaria"] == "0-14" and not bool(por_cid.loc["J18", "obito"])
    assert por_cid.loc["J18", "municipio_res"] == "250750"                  # código aceito direto
    assert por_cid.loc["I21", "municipio_res"] == "250750"                  # nome resolvido
    assert (limpo["fonte"] == "teste").all() and (limpo["uf"] == "PB").all()


def test_obito_desconhecido_gera_aviso_e_nao_quebra(tmp_path):
    _, _, rel = construir_externa(_origem(), _cfg(tmp_path), MUNICIPIOS)
    assert any("óbito não reconhecido" in a for a in rel.avisos)


def test_municipio_homonimo_usa_a_uf_da_fonte(tmp_path):
    limpo, _, _ = construir_externa(_origem().iloc[[3]], _cfg(tmp_path), MUNICIPIOS)
    assert limpo.iloc[0]["municipio_res"] == "251000"                       # PB, não PE


def test_municipio_nao_resolvido_vira_aviso(tmp_path):
    _, _, rel = construir_externa(_origem(), _cfg(tmp_path), MUNICIPIOS)
    assert any("não reconhecidos" in a for a in rel.avisos)


def test_idade_por_data_de_nascimento(tmp_path):
    cfg = _cfg(tmp_path)
    cfg["colunas"].pop("idade")
    cfg["colunas"]["data_nascimento"] = "NASC"
    origem = _origem().iloc[[0, 1]].assign(NASC=["05/01/1953", "10/02/2015"])
    limpo, _, _ = construir_externa(origem, cfg, MUNICIPIOS)
    por_cid = limpo.set_index("cid3")
    assert por_cid.loc["I21", "faixa_etaria"] == "65+" and por_cid.loc["J18", "faixa_etaria"] == "0-14"


def test_validacao_da_configuracao(tmp_path):
    def grava(nome, conteudo):
        p = tmp_path / nome
        p.write_text(json.dumps(conteudo), encoding="utf-8")
        return p
    base = {"arquivo": "x.csv", "uf": "PB", "colunas": {"data_internacao": "A", "cid": "B"}}
    carregar_config(grava("ok.json", base))
    for nome, ruim, trecho in [
        ("sih.json", base, "reservado"),
        ("a.json", {**base, "uf": "XX"}, "UF inválida"),
        ("b.json", {**base, "colunas": {"cid": "B"}}, "obrigatórios"),
        ("c.json", {**base, "colunas": {**base["colunas"], "foo": "Z"}}, "desconhecidos"),
        ("d.json", {**base, "colunas": {**base["colunas"], "id": "CPF_PACIENTE"}}, "identificador pessoal"),
        ("e.json", {k: v for k, v in base.items() if k != "arquivo"}, "falta a chave"),
        ("f.json", {**base, "unidade_idade": "séculos"}, "unidade_idade"),
    ]:
        with pytest.raises(ValueError, match=trecho):
            carregar_config(grava(nome, ruim))


def test_coluna_inexistente_lista_as_disponiveis(tmp_path):
    with pytest.raises(ValueError, match="Colunas disponíveis"):
        construir_externa(_origem().drop(columns=["CID"]), _cfg(tmp_path), MUNICIPIOS)


def test_descobrir_configs_ignora_modelos(tmp_path):
    for n in ("patos.json", "outra.json", "patos.exemplo.json", "leia.txt"):
        (tmp_path / n).write_text("{}", encoding="utf-8")
    assert [p.name for p in descobrir_configs(tmp_path)] == ["outra.json", "patos.json"]
    assert descobrir_configs(tmp_path / "nao_existe") == []