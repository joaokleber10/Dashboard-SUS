import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { test } from "node:test";
import { pathToFileURL } from "node:url";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const require = createRequire(import.meta.url);
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

const css = await readFile(new URL("../src/styles/brand.css", import.meta.url), "utf8");
const variaveis = (bloco) => Object.fromEntries(
  [...bloco.matchAll(/(--[a-z-]+):\s*(#[a-f0-9]{6})/gi)].map((m) => [m[1], m[2]]),
);
const blocoClaro = css.match(/:root\[data-theme="light"\]\s*\{([^}]+)/)?.[1];
const blocoEscuro = css.match(/:root\[data-theme="dark"\]\s*\{([^}]+)/)?.[1];
assert.ok(blocoClaro && blocoEscuro, "Tokens dos dois temas devem existir");
const claro = variaveis(blocoClaro);
const escuro = { ...claro, ...variaveis(blocoEscuro) };

function luminancia(hex) {
  assert.match(hex, /^#[\da-f]{6}$/i);
  const [r, g, b] = hex.slice(1).match(/../g).map((x) => parseInt(x, 16) / 255)
    .map((x) => x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4);
  return r * 0.2126 + g * 0.7152 + b * 0.0722;
}
function contraste(a, b) {
  const x = luminancia(a);
  const y = luminancia(b);
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}
function conferirPares(tokens, pares, minimo) {
  for (const [frente, fundo] of pares) {
    const valor = contraste(tokens[frente], tokens[fundo]);
    assert.ok(valor >= minimo, `${frente} em ${fundo}: ${valor.toFixed(2)}:1 < ${minimo}:1`);
  }
}

for (const [nome, tokens] of [["claro", claro], ["escuro", escuro]]) {
  test(`Tema ${nome}: pares principais de texto têm contraste AA`, () => {
    conferirPares(tokens, [
      ["--texto", "--bg"], ["--texto", "--superficie"],
      ["--suave", "--superficie"], ["--suave", "--superficie-alt"],
      ["--acao-texto", "--acao-bg"], ["--azul", "--superficie"],
    ], 4.5);
  });
  test(`Tema ${nome}: campos e gráficos têm contraste mínimo de 3:1`, () => {
    conferirPares(tokens, [
      ["--borda-forte", "--superficie"],
      ["--chart-primary", "--superficie"],
      ["--chart-secondary", "--superficie"],
      ["--chart-category", "--superficie"],
    ], 3);
  });
}

test("Sidebar mantém texto legível e seleção com borda de contraste", () => {
  conferirPares(claro, [
    ["--sidebar-texto", "--sidebar-bg"], ["--sidebar-suave", "--sidebar-bg"],
    ["--sidebar-ativo-texto", "--sidebar-ativo"],
  ], 4.5);
  conferirPares(claro, [["--sidebar-ativo-borda", "--sidebar-ativo"]], 3);
});

test("Legenda e extremos do mapa usam os mesmos tokens", () => {
  assert.match(css, /linear-gradient\(to right, var\(--chart-map-start\), var\(--chart-map-end\)\)/);
});

test("Brasão existente permanece disponível com suas proporções originais", async () => {
  const png = await readFile(new URL("../src/Public/Icon/logo.png", import.meta.url));
  assert.equal(png.subarray(0, 8).toString("hex"), "89504e470d0a1a0a");
  assert.equal(png.readUInt32BE(16), 221);
  assert.equal(png.readUInt32BE(20), 208);
});

const { default: KpiCards } = await carregarTs("../src/components/kpis/KpiCards.tsx");
// Fixtures identificadas: apenas testes, nunca resultados demonstrativos do aplicativo.
const dadosTeste = {
  atual: { total: 120, total_geral: 240, proporcao_total_geral: 50, obitos: 3,
    taxa_mortalidade: 2.5, permanencia_media: 4, custo_total: 1000,
    custo_medio: 1000 / 120, municipios_atendidos: 7 },
  anterior: null, variacao_pct: null, comparacao: "nenhuma", periodo_anterior: null,
};

test("Quatro cartões principais preservam os valores e municípios permanecem visíveis", () => {
  const html = renderToStaticMarkup(KpiCards({ dados: dadosTeste }));
  assert.equal((html.match(/class="card"/g) ?? []).length, 4);
  assert.match(html, /Internações/);
  assert.match(html, /Taxa de mortalidade hospitalar/);
  assert.match(html, /2,5%/);
  assert.match(html, /4 dias/);
  assert.match(html, /R\$\s*1\.000/);
  assert.match(html, /class="kpi-supplement"/);
  assert.match(html, /<strong>7<\/strong> municípios atendidos/);
});

test("Indicadores ausentes continuam como traço, não zero inventado", () => {
  const html = renderToStaticMarkup(KpiCards({ dados: {
    ...dadosTeste, atual: { ...dadosTeste.atual, taxa_mortalidade: null,
      permanencia_media: null, custo_total: null, custo_medio: null },
  } }));
  assert.equal((html.match(/class="card-valor">—<\/strong>/g) ?? []).length, 3);
});

const { DataInfoBar } = await carregarTs("../src/components/layout/DataInfoBar.tsx");
const metaTeste = {
  ufs_disponiveis: ["PB"],
  periodo: { competencia_min: "202401", competencia_max: "202403", fonte: "SIH/SUS (teste)",
    ultima_atualizacao: null },
};

test("Cabeçalho compacto preserva as competências reais e não inventa atualização", () => {
  const html = renderToStaticMarkup(DataInfoBar({ meta: metaTeste, compacta: true }));
  assert.match(html, /data-info-bar--compacta/);
  assert.match(html, /01\/2024 a 03\/2024/);
  assert.match(html, /PB/);
  assert.doesNotMatch(html, /Última atualização/);
});

const { temaInicial, salvarTema } = await carregarTs("../src/components/common/ThemeToggle.tsx");
function comArmazenamento(storage, fn) {
  const anterior = globalThis.localStorage;
  const janela = globalThis.window;
  try {
    globalThis.localStorage = storage;
    globalThis.window = { matchMedia: () => ({ matches: true }) };
    fn();
  } finally {
    if (anterior === undefined) delete globalThis.localStorage;
    else globalThis.localStorage = anterior;
    if (janela === undefined) delete globalThis.window;
    else globalThis.window = janela;
  }
}

test("Tema salvo tem prioridade sobre a preferência do sistema", () => {
  comArmazenamento({ getItem: (chave) => {
    assert.equal(chave, "sus-theme");
    return "light";
  } }, () => assert.equal(temaInicial(), "light"));
});

test("Controle de tema preserva a chave localStorage já usada pelo projeto", () => {
  const gravacoes = [];
  comArmazenamento({ setItem: (...args) => gravacoes.push(args) }, () => salvarTema("dark"));
  assert.deepEqual(gravacoes, [["sus-theme", "dark"]]);
});
