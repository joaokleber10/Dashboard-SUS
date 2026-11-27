# Estrutura de Pastas - Frontend SUS Dashboard

## 📁 Organização Atual

O frontend foi reorganizado em uma estrutura modular que facilita a adição de novas telas e componentes. Aqui está a hierarquia completa:

```
frontend/src/
├── pages/                      # Páginas/Telas da aplicação
│   ├── Dashboard/
│   │   ├── index.ts            # Export da tela
│   │   └── Dashboard.tsx        # Lógica e layout da tela
│   └── [OutrasTelas]/          # Adicione novas telas aqui
│
├── components/                 # Componentes reutilizáveis
│   ├── common/                 # Componentes básicos
│   │   ├── ErrorBanner.tsx      # Exibe mensagens de erro
│   │   ├── Skeleton.tsx         # Estados de carregamento (skeleton)
│   │   ├── ThemeToggle.tsx      # Alternador de tema
│   │   └── index.ts             # Export de componentes comuns
│   │
│   ├── layout/                 # Componentes de layout
│   │   ├── Header.tsx           # Cabeçalho com alternador de tema
│   │   ├── DataInfoBar.tsx      # Barra de informações da base de dados
│   │   └── index.ts
│   │
│   ├── filters/                # Componentes de filtros
│   │   ├── FilterPanel.tsx      # Painel principal de filtros
│   │   ├── ActiveFiltersSummary.tsx  # Resumo de filtros ativos
│   │   ├── PriorityGroupsBar.tsx    # Barra de grupos prioritários
│   │   ├── GroupSelect.tsx      # Seletor de grupos dinâmicos
│   │   └── index.ts
│   │
│   ├── charts/                 # Componentes de gráficos
│   │   ├── TimeSeriesChart.tsx  # Série temporal
│   │   ├── AgePyramid.tsx       # Pirâmide etária
│   │   ├── TopCidChart.tsx      # Top 10 CIDs
│   │   └── index.ts
│   │
│   ├── kpis/                   # Componentes de indicadores
│   │   ├── KpiCards.tsx         # Cartões de KPI
│   │   └── index.ts
│   │
│   └── municipios/             # Componentes de municípios
│       ├── MunicipiosMapa.tsx   # Mapa geográfico
│       ├── MunicipiosTabela.tsx # Tabela de municípios
│       └── index.ts
│
├── services/                   # Lógica de negócio e APIs
│   ├── api.ts                  # Chamadas da API
│   ├── periodo.ts              # Utilitários de período/competência
│   └── index.ts                # Export de serviços
│
├── types/                      # Tipos TypeScript compartilhados
│   └── index.ts                # Todos os tipos da aplicação
│
├── styles/                     # Estilos globais
│   └── globals.css             # CSS global
│
├── App.tsx                     # Componente raiz
├── main.tsx                    # Ponto de entrada
└── vite-env.d.ts               # Definições de tipos Vite
```

## 🚀 Como Adicionar uma Nova Tela

### Passo 1: Criar a Pasta da Página

```bash
mkdir -p frontend/src/pages/MinhaTelaNovaFeature
```

### Passo 2: Criar o Componente da Tela

Crie `frontend/src/pages/MinhaTelaNovaFeature/MinhaTelaNovaFeature.tsx`:

```tsx
import { useQuery } from "@tanstack/react-query";
import { buscarMeta } from "../../services/api";
import type { Filtros } from "../../types";
import { useState } from "react";

export function MinhaTelaNovaFeature() {
  const [filtros, setFiltros] = useState<Filtros | null>(null);
  
  const meta = useQuery({
    queryKey: ["meta"],
    queryFn: buscarMeta,
    staleTime: Infinity,
  });

  if (!meta.data) return <div>Carregando...</div>;

  return (
    <div className="layout">
      <h1>Minha Tela Nova</h1>
      {/* Seu conteúdo aqui */}
    </div>
  );
}
```

### Passo 3: Criar o Index da Página

Crie `frontend/src/pages/MinhaTelaNovaFeature/index.ts`:

```ts
export { MinhaTelaNovaFeature } from "./MinhaTelaNovaFeature";
```

### Passo 4: Atualizar o Roteamento (Quando Implementar Router)

No seu `App.tsx` ou arquivo de rotas, importe a nova página:

```tsx
import { Dashboard } from "./pages/Dashboard";
import { MinhaTelaNovaFeature } from "./pages/MinhaTelaNovaFeature";
```

## 📦 Importações Recomendadas

### Para APIs
```tsx
import { buscarMeta, buscarKpis, buscarSerie } from "../../services/api";
// ou
import { buscarMeta } from "../../services";
```

### Para Tipos
```tsx
import type { Filtros, Meta, KpisResp } from "../../types";
```

### Para Componentes Comuns
```tsx
import { ErroBanner, KpiSkeleton, ThemeToggle } from "../../components/common";
```

### Para Componentes de Categoria
```tsx
import { FilterPanel, ActiveFiltersSummary } from "../../components/filters";
import { TimeSeriesChart, AgePyramid } from "../../components/charts";
```

## 🎨 Estrutura de Componentes por Tipo

### Common (Reutilizáveis)
- **ErrorBanner**: Exibe erros
- **KpiSkeleton**: Carregamento de KPIs
- **ThemeToggle**: Botão alternador de tema

### Layout
- **Header**: Cabeçalho da aplicação
- **DataInfoBar**: Informações da base de dados

### Filters (Componentes de Filtro)
- **FilterPanel**: Painel completo de filtros
- **ActiveFiltersSummary**: Resumo dos filtros ativos
- **PriorityGroupsBar**: Atalhos para grupos prioritários
- **GroupSelect**: Selector de grupos dinâmicos

### Charts (Gráficos)
- **TimeSeriesChart**: Série temporal de casos
- **AgePyramid**: Distribuição por idade
- **TopCidChart**: Top 10 principais CIDs

### KPIs (Indicadores)
- **KpiCards**: Cartões com métricas principais

### Municipios (Dados Geográficos)
- **MunicipiosMapa**: Mapa interativo
- **MunicipiosTabela**: Tabela com dados municipais

## 💡 Boas Práticas

1. **Use index.ts para exports**: Facilita importações dentro do projeto
2. **Mantenha arquivos simples**: Um componente por arquivo quando possível
3. **Reutilize componentes**: Use componentes existentes ao criar novas telas
4. **Organize por feature**: Agrupe componentes relacionados na mesma pasta
5. **Tipagem**: Sempre use TypeScript para segurança de tipos

## 🔄 Próximas Melhorias

- [ ] Implementar React Router para navegação entre telas
- [ ] Adicionar testes unitários para componentes
- [ ] Criar sistema de temas mais robusto
- [ ] Implementar lazy loading de páginas
- [ ] Documentação de componentes com Storybook

