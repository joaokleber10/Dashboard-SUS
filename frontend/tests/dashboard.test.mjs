import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { test } from "node:test";
import { pathToFileURL } from "node:url";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const require = createRequire(import.meta.url);

// Usa somente dependências já instaladas; não modifica nem gera arquivos de produção.
async function carregarTs(caminho) {
  const fonte = await readFile(new URL(caminho, import.meta.url), "utf8");
  const resultado = ts.transpileModule(fonte, {
    compilerOptions: {
      module: ts.ModuleKind.ES2022,
      target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
    },
  });
  const codigo = resultado.outputText.replace(/from "(react\/jsx-runtime)"/g,
    (_, modulo) => `from ${JSON.stringify(pathToFileURL(require.resolve(modulo)).href)}`);
  return import(`data:text/javascript;base64,${Buffer.from(codigo).toString("base64")}`);
}

const periodo = await carregarTs("../src/services/periodo.ts");
const { default: ViewTabs } = await carregarTs("../src/components/common/ViewTabs.tsx");
const meta = {
  periodo: {
    data_min: "2023-12-15",
    data_max: "2024-03-12",
    competencia_min: "2024-01",
    competencia_max: "2024-04",
  },
  capitulos: [
    { id: "IX", padrao: true },
    { id: "X", padrao: true },
    { id: "XI", padrao: false },
  ],
  foco: { uf: "PB" },
  ufs_disponiveis: ["PB"],
};

test("Período completo usa internação, não competência", () => {
  assert.deepEqual(periodo.periodoCompleto(meta), {
    data_inicio: "2023-12-15", data_fim: "2024-03-12",
  });
});

test("Filtros padrão preservam os dois capítulos e todos os registros do período", () => {
  const filtros = periodo.filtrosPadrao(meta);
  assert.deepEqual(filtros.capitulo_ids, ["IX", "X"]);
  assert.equal(filtros.data_inicio, "2023-12-15");
  assert.equal(filtros.data_fim, "2024-03-12");
  assert.equal(filtros.uf, "PB");
  assert.equal(filtros.comparacao, "nenhuma");
});

test("Último mês respeita o último dia de internação carregado", () => {
  assert.deepEqual(periodo.ultimoMes(meta), {
    data_inicio: "2024-03-01", data_fim: "2024-03-12",
  });
});

test("Último mês não antecede a primeira internação de um recorte curto", () => {
  assert.deepEqual(periodo.ultimoMes({ ...meta, periodo: {
    ...meta.periodo, data_min: "2024-03-08",
  } }), { data_inicio: "2024-03-08", data_fim: "2024-03-12" });
});

test("Competência continua como fallback e respeita ano bissexto", () => {
  const semDatas = { ...meta, periodo: {
    data_min: null, data_max: null, competencia_min: "2024-02", competencia_max: "2024-02",
  } };
  assert.deepEqual(periodo.periodoCompleto(semDatas), {
    data_inicio: "2024-02-01", data_fim: "2024-02-29",
  });
});

test("Catálogo sem datas não inventa um período", () => {
  const vazio = { ...meta, periodo: {
    data_min: null, data_max: null, competencia_min: null, competencia_max: null,
  } };
  assert.deepEqual(periodo.periodoCompleto(vazio), { data_inicio: "", data_fim: "" });
  assert.equal(periodo.ultimoMes(vazio), null);
});

const opcoes = [
  { id: "geral", nome: "Visão geral" },
  { id: "perfil", nome: "Perfil e causas" },
  { id: "municipios", nome: "Municípios" },
];

function montarAbas(valor = "geral", orientacao = "horizontal") {
  let selecionado;
  let focado;
  let prevenido = false;
  const abasFoco = opcoes.map((_, indice) => ({ focus: () => { focado = indice; } }));
  const elemento = ViewTabs({ id: "teste", rotulo: "Visões", opcoes, valor,
    onChange: (id) => { selecionado = id; }, orientacao });
  return {
    elemento,
    tecla(indice, key) {
      elemento.props.children[indice].props.onKeyDown({ key,
        preventDefault: () => { prevenido = true; },
        currentTarget: { parentElement: { querySelectorAll: () => abasFoco } },
      });
      return { selecionado, focado, prevenido };
    },
  };
}

test("Abas anunciam seleção e apenas a ativa entra na ordem de Tab", () => {
  const { elemento } = montarAbas("perfil");
  const botoes = elemento.props.children;
  assert.deepEqual(botoes.map((botao) => botao.props["aria-selected"]), [false, true, false]);
  assert.deepEqual(botoes.map((botao) => botao.props.tabIndex), [-1, 0, -1]);
  assert.equal(botoes[1].props["aria-controls"], "teste-panel-perfil");
  const html = renderToStaticMarkup(elemento);
  assert.match(html, /role="tablist"/);
  assert.match(html, /id="teste-tab-perfil"/);
});

test("Seta direita avança, seleciona e foca a próxima aba", () => {
  assert.deepEqual(montarAbas().tecla(0, "ArrowRight"), {
    selecionado: "perfil", focado: 1, prevenido: true,
  });
});

test("Setas circulam entre a primeira e a última aba", () => {
  assert.equal(montarAbas().tecla(0, "ArrowLeft").selecionado, "municipios");
  assert.equal(montarAbas().tecla(2, "ArrowRight").selecionado, "geral");
});

test("Home e End focam as extremidades", () => {
  assert.equal(montarAbas().tecla(1, "Home").focado, 0);
  assert.equal(montarAbas().tecla(1, "End").focado, 2);
});

test("Tab não é interceptado pelo controle de abas", () => {
  assert.deepEqual(montarAbas().tecla(0, "Tab"), {
    selecionado: undefined, focado: undefined, prevenido: false,
  });
});

test("Menu lateral anuncia orientação vertical", () => {
  assert.equal(montarAbas("geral", "vertical").elemento.props["aria-orientation"], "vertical");
});

test("Seta para baixo avança e foca a próxima visão no menu lateral", () => {
  assert.deepEqual(montarAbas("geral", "vertical").tecla(0, "ArrowDown"), {
    selecionado: "perfil", focado: 1, prevenido: true,
  });
});

test("Setas verticais circulam nas extremidades", () => {
  assert.equal(montarAbas("geral", "vertical").tecla(0, "ArrowUp").selecionado, "municipios");
  assert.equal(montarAbas("geral", "vertical").tecla(2, "ArrowDown").selecionado, "geral");
});

test("Home e End continuam funcionando no menu lateral", () => {
  assert.equal(montarAbas("geral", "vertical").tecla(1, "Home").focado, 0);
  assert.equal(montarAbas("geral", "vertical").tecla(1, "End").focado, 2);
});

test("Abas não interceptam as setas fora do próprio eixo", () => {
  assert.equal(montarAbas("geral", "vertical").tecla(0, "ArrowRight").prevenido, false);
  assert.equal(montarAbas().tecla(0, "ArrowDown").prevenido, false);
});
