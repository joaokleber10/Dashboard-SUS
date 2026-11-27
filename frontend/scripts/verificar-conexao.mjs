// Verificação manual somente leitura: não inicia serviços nem altera o ambiente.
// Executar na pasta frontend: node scripts/verificar-conexao.mjs
const endpoints = [
  ["Prévia", "http://127.0.0.1:5173/"],
  ["API", "http://localhost:8000/meta/filtros"],
];

for (const [nome, url] of endpoints) {
  try {
    const resposta = await fetch(url, { signal: AbortSignal.timeout(4000) });
    console.log(`${nome}: HTTP ${resposta.status} — ${url}`);
    console.log((await resposta.text()).slice(0, 120));
  } catch (erro) {
    console.log(`${nome}: ${erro.name} — ${erro.message} — ${url}`);
    if (erro.cause?.code) console.log(`Causa: ${erro.cause.code}`);
  }
}
