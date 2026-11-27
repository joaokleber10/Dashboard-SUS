# 📋 Guia de Exemplo: Adicionar uma Nova Tela

Este é um guia passo a passo de como adicionar uma nova tela ao Dashboard SUS, mantendo a estrutura organizada e reutilizando componentes existentes.

## 🎯 Cenário: Criar uma Tela de "Relatórios"

### Passo 1: Criar a Pasta da Página

```bash
mkdir -p frontend/src/pages/Relatorios
```

### Passo 2: Criar o Componente Principal

Arquivo: `frontend/src/pages/Relatorios/Relatorios.tsx`

```tsx
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { buscarMeta, buscarKpis } from "../../services/api";
import { filtrosPadrao } from "../../services/periodo";
import type { Filtros } from "../../types";
import { ErroBanner, KpiSkeleton } from "../../components/common";
import { FilterPanel, ActiveFiltersSummary } from "../../components/filters";
import { KpiCards } from "../../components/kpis";
import { TimeSeriesChart } from "../../components/charts";

export function Relatorios() {
  const [filtros, setFiltros] = useState<Filtros | null>(null);
  const [relatorioTipo, setRelatorioTipo] = useState<"resumo" | "detalhado">("resumo");

  const meta = useQuery({
    queryKey: ["meta"],
    queryFn: buscarMeta,
    staleTime: Infinity,
  });

  // Inicializar filtros ao carregar meta
  if (meta.data && filtros === null) {
    setFiltros(filtrosPadrao(meta.data));
  }

  const kpis = useQuery({
    queryKey: ["kpis", filtros],
    queryFn: () => buscarKpis(filtros as Filtros),
    enabled: filtros !== null,
  });

  if (meta.isError) return <ErroBanner erro={meta.error} />;
  if (meta.isPending || !meta.data) return <div className="skeleton alto" />;
  if (!filtros) return null;

  return (
    <div className="layout">
      {/* Painel de Filtros */}
      <FilterPanel meta={meta.data} filtros={filtros} onChange={setFiltros} />

      <main className="conteudo">
        {/* Resumo de Filtros */}
        <ActiveFiltersSummary
          meta={meta.data}
          filtros={filtros}
          onChange={setFiltros}
        />

        {/* Seletor de Tipo de Relatório */}
        <div className="painel">
          <div className="painel-topo">
            <h2>Tipo de Relatório</h2>
          </div>
          <div className="alternar">
            <button
              className={relatorioTipo === "resumo" ? "ativo" : ""}
              onClick={() => setRelatorioTipo("resumo")}
            >
              📊 Resumo
            </button>
            <button
              className={relatorioTipo === "detalhado" ? "ativo" : ""}
              onClick={() => setRelatorioTipo("detalhado")}
            >
              📋 Detalhado
            </button>
          </div>
        </div>

        {/* Conteúdo por Tipo */}
        {relatorioTipo === "resumo" ? (
          <>
            {kpis.isError && <ErroBanner erro={kpis.error} />}
            {kpis.isPending && <KpiSkeleton />}
            {kpis.data && <KpiCards dados={kpis.data} />}
          </>
        ) : (
          <>
            <div className="painel">
              <h3>Relatório Detalhado</h3>
              <p>Dados por período:</p>
              {kpis.isPending && <KpiSkeleton />}
              {kpis.data && <TimeSeriesChart filtros={filtros} />}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
```

### Passo 3: Criar o Index da Página

Arquivo: `frontend/src/pages/Relatorios/index.ts`

```ts
export { Relatorios } from "./Relatorios";
```

### Passo 4: Atualizar o App.tsx (Quando Implementar Router)

```tsx
import { useState } from "react";
import { Header } from "./components/layout/Header";
import { DataInfoBar } from "./components/layout/DataInfoBar";
import { Dashboard } from "./pages/Dashboard";
import { Relatorios } from "./pages/Relatorios";
import { useQuery } from "@tanstack/react-query";
import { buscarMeta } from "./services/api";
import type { Theme } from "./components/common/ThemeToggle";
import { temaInicial } from "./components/common/ThemeToggle";

type Pagina = "dashboard" | "relatorios";

function App() {
  const [theme, setTheme] = useState<Theme>(temaInicial);
  const [paginaAtual, setPaginaAtual] = useState<Pagina>("dashboard");

  const meta = useQuery({
    queryKey: ["meta"],
    queryFn: buscarMeta,
    staleTime: Infinity,
  });

  return (
    <div className="app">
      <Header theme={theme} onThemeChange={setTheme} />
      
      {meta.data && <DataInfoBar meta={meta.data} />}

      {/* Navegação entre páginas */}
      <nav style={{ marginBottom: "16px", display: "flex", gap: "8px" }}>
        <button
          onClick={() => setPaginaAtual("dashboard")}
          className={paginaAtual === "dashboard" ? "ativo" : ""}
        >
          Dashboard
        </button>
        <button
          onClick={() => setPaginaAtual("relatorios")}
          className={paginaAtual === "relatorios" ? "ativo" : ""}
        >
          Relatórios
        </button>
      </nav>

      {/* Renderizar página selecionada */}
      {paginaAtual === "dashboard" && <Dashboard />}
      {paginaAtual === "relatorios" && <Relatorios />}
    </div>
  );
}

export default App;
```

## 📝 Notas Importantes

### Estrutura de Pastas
- Cada tela tem sua própria pasta em `pages/`
- Componentes específicos da tela ficam na mesma pasta (opcional)
- Componentes reutilizáveis em `components/`

### Importações
```tsx
// ✓ Bom - Importar de serviços
import { buscarKpis } from "../../services/api";

// ✓ Bom - Importar de tipos
import type { Filtros } from "../../types";

// ✓ Bom - Importar de componentes comuns
import { ErroBanner } from "../../components/common";

// ✗ Evitar - Importar do arquivo raiz
// import { buscarKpis } from "../../api";
```

### Reutilização de Estado
Se a tela precisa dos mesmos filtros que o Dashboard, reutilize a lógica:

```tsx
import { filtrosPadrao } from "../../services/periodo";

// Na sua tela
if (meta.data && filtros === null) {
  setFiltros(filtrosPadrao(meta.data));
}
```

## 🎨 CSS Classes Disponíveis

A nova estrutura mantém todos os estilos globais em `styles/globals.css`. Use as classes predefinidas:

```css
.layout          /* Layout com filtros e conteúdo */
.painel          /* Painel com borda */
.painel-topo     /* Cabeçalho de painel */
.conteudo        /* Área de conteúdo principal */
.card            /* Card de informação */
.cards           /* Grid de cards */
.duas-colunas    /* Grid com duas colunas */
.alternar        /* Botões de alternância */
.chip            /* Chip/tag */
.ativo           /* Estado ativo */
.vazio           /* Mensagem de vazio */
.erro            /* Mensagem de erro */
.skeleton        /* Carregamento */
```

## 🚀 Próximos Passos

1. Implementar React Router para navegação
2. Adicionar testes unitários para a nova tela
3. Documentar no Storybook se necessário
4. Adicionar validações de entrada com Zod

