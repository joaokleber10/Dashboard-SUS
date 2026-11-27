# 📁 Árvore Completa da Estrutura

```
frontend/src/
│
├─ 📄 App.tsx
│  └─ Componente raiz
│     ├─ Renderiza: Header
│     ├─ Renderiza: DataInfoBar  
│     └─ Renderiza: Dashboard
│
├─ 📄 main.tsx
│  └─ Ponto de entrada React
│
├─ 📄 vite-env.d.ts
│  └─ Tipos Vite
│
├─ 📁 pages/
│  │  Telas/Views da aplicação
│  │
│  └─ 📁 Dashboard/
│     ├─ Dashboard.tsx (componente da tela)
│     └─ index.ts (exportação)
│
├─ 📁 components/
│  │  Componentes reutilizáveis organizados por categoria
│  │
│  ├─ 📁 common/
│  │  │  Componentes básicos reutilizáveis
│  │  │
│  │  ├─ ErrorBanner.tsx
│  │  │  └─ Exibe mensagens de erro com ícone
│  │  │
│  │  ├─ Skeleton.tsx
│  │  │  └─ Componente de carregamento (KpiSkeleton)
│  │  │
│  │  ├─ ThemeToggle.tsx
│  │  │  ├─ Componente do alternador de tema
│  │  │  ├─ Lógica: temaInicial(), salvarTema()
│  │  │  └─ Type: Theme ("light" | "dark")
│  │  │
│  │  └─ index.ts
│  │     └─ export { ErroBanner, KpiSkeleton, ThemeToggle }
│  │
│  ├─ 📁 layout/
│  │  │  Componentes de layout principal
│  │  │
│  │  ├─ Header.tsx
│  │  │  ├─ Cabeçalho com título
│  │  │  └─ Contém: ThemeToggle
│  │  │
│  │  ├─ DataInfoBar.tsx
│  │  │  ├─ Barra de informações da base de dados
│  │  │  ├─ Mostra: fontes, competências, UFs, última atualização
│  │  │  └─ Props: { meta }
│  │  │
│  │  └─ index.ts
│  │     └─ export { Header, DataInfoBar }
│  │
│  ├─ 📁 filters/
│  │  │  Componentes de filtro de dados
│  │  │
│  │  ├─ FilterPanel.tsx
│  │  │  ├─ Painel principal com todos os filtros
│  │  │  ├─ Inclui: CheckGroup, BuscaCid, datas, etc
│  │  │  └─ Props: { meta, filtros, onChange }
│  │  │
│  │  ├─ ActiveFiltersSummary.tsx
│  │  │  ├─ Resumo de filtros ativos
│  │  │  ├─ Chips removíveis
│  │  │  └─ Botão de exportar CSV
│  │  │
│  │  ├─ PriorityGroupsBar.tsx
│  │  │  ├─ Barra com atalhos de grupos prioritários
│  │  │  ├─ Botões quick-filter
│  │  │  └─ Props: { meta, filtros, onChange }
│  │  │
│  │  ├─ GroupSelect.tsx
│  │  │  ├─ Selector dropdown de grupos dinâmicos
│  │  │  ├─ Busca funcional
│  │  │  └─ Props: { filtros, onChange }
│  │  │
│  │  └─ index.ts
│  │     └─ export { FilterPanel, ActiveFiltersSummary, ... }
│  │
│  ├─ 📁 charts/
│  │  │  Componentes de gráficos/visualizações
│  │  │
│  │  ├─ TimeSeriesChart.tsx
│  │  │  ├─ Gráfico de série temporal
│  │  │  ├─ Eixos: tempo (meses) vs casos/óbitos
│  │  │  └─ Props: { filtros }
│  │  │
│  │  ├─ AgePyramid.tsx
│  │  │  ├─ Pirâmide etária por sexo
│  │  │  ├─ Dados de demografia
│  │  │  └─ Props: { filtros }
│  │  │
│  │  ├─ TopCidChart.tsx
│  │  │  ├─ Gráfico horizontal top 10 CIDs
│  │  │  ├─ Dados por casos/óbitos
│  │  │  └─ Props: { filtros }
│  │  │
│  │  └─ index.ts
│  │     └─ export { TimeSeriesChart, AgePyramid, TopCidChart }
│  │
│  ├─ 📁 kpis/
│  │  │  Componentes de indicadores-chave
│  │  │
│  │  ├─ KpiCards.tsx
│  │  │  ├─ Grid de cartões com métricas
│  │  │  ├─ Mostra: total, óbitos, mortalidade, etc
│  │  │  ├─ Inclui: variação de período anterior
│  │  │  └─ Props: { dados: KpisResp }
│  │  │
│  │  └─ index.ts
│  │     └─ export { KpiCards }
│  │
│  └─ 📁 municipios/
│     │  Componentes de dados geográficos
│     │
│     ├─ MunicipiosMapa.tsx
│     │  ├─ Mapa geográfico interativo (SVG)
│     │  ├─ Cores por métrica (casos, óbitos, etc)
│     │  ├─ Filtro interativo
│     │  └─ Props: { meta, filtros, onChange }
│     │
│     ├─ MunicipiosTabela.tsx
│     │  ├─ Tabela com dados municipais
│     │  ├─ Paginação
│     │  ├─ Ordenação por coluna
│     │  └─ Props: { meta, filtros, onChange }
│     │
│     └─ index.ts
│        └─ export { MunicipiosMapa, MunicipiosTabela }
│
├─ 📁 services/
│  │  Lógica de negócio e integração com API
│  │
│  ├─ api.ts
│  │  ├─ Baseado em: import.meta.env.VITE_API_URL
│  │  ├─ Funções: (12 total)
│  │  │  ├─ buscarMeta()           → Meta com opções de filtro
│  │  │  ├─ buscarKpis(filtros)    → KPIs agregados
│  │  │  ├─ buscarSerie()          → Série temporal
│  │  │  ├─ buscarDemografia()     → Dados demográficos
│  │  │  ├─ buscarTopCid()         → Top 10 CIDs
│  │  │  ├─ buscarGruposDinamicos()→ Grupos por filtro
│  │  │  ├─ resolverCid()          → Validar/resolver CID
│  │  │  ├─ urlExportarCsv()       → URL de exportação
│  │  │  ├─ buscarMapa()           → Dados geográficos
│  │  │  ├─ buscarMunicipios()     → Tabela de municípios
│  │  │  ├─ buscarGeo()            → GeoJSON
│  │  │  └─ buscarCid()            → Busca CID
│  │  └─ Class: ApiError
│  │
│  ├─ periodo.ts
│  │  ├─ Funções: (5 total)
│  │  │  ├─ primeiroDia()      → "AAAA-MM-01"
│  │  │  ├─ ultimoDia()        → "AAAA-MM-31"
│  │  │  ├─ filtrosPadrao()    → Filtros iniciais
│  │  │  ├─ ultimoMes()        → Período do último mês
│  │  │  └─ periodoCompleto()  → Período total disponível
│  │  └─ Helpers para período/competência
│  │
│  └─ index.ts
│     └─ Centraliza exports de api.ts e periodo.ts
│
├─ 📁 types/
│  │  Tipos TypeScript compartilhados em toda app
│  │
│  └─ index.ts
│     ├─ Interfaces: (20+ tipos)
│     │  ├─ Opcao, Capitulo, GrupoPrioritario
│     │  ├─ Meta, Filtros, KpisResp
│     │  ├─ SerieResp, DemografiaResp
│     │  ├─ TopCidResp, MunicipiosResp
│     │  ├─ MapaResp, GeoJson
│     │  └─ ... (e mais)
│     └─ Types: OrdemMunicipios
│
└─ 📁 styles/
   │  Estilos globais
   │
   └─ globals.css
      ├─ Variáveis de tema (--bg, --texto, --azul, etc)
      ├─ Dark mode: :root[data-theme="dark"]
      ├─ CSS classes: .layout, .painel, .card, .chip
      ├─ Grid utilities: .duas-colunas, .cards
      ├─ State classes: .ativo, .vazio, .erro, .skeleton
      └─ Componentes: .municipios-table, .charts, etc

```

## 📊 Totalizações

### Arquivos por Tipo
- **Componentes TSX**: 11
- **Serviços TS**: 2
- **Tipos TS**: 1
- **Estilos CSS**: 1
- **Índices TS**: 8
- **Total**: 23 arquivos

### Componentes por Categoria
- **common**: 3 componentes
- **layout**: 2 componentes
- **filters**: 4 componentes
- **charts**: 3 componentes
- **kpis**: 1 componente
- **municipios**: 2 componentes
- **pages**: 1 componente

### Funções de API
- 12 funções de requisição HTTP

### Tipos Definidos
- 20+ interfaces/types

## 🎯 Dependências de Componentes

```
App
├─ Header (uses ThemeToggle)
├─ DataInfoBar (uses Meta)
└─ Dashboard
   ├─ FilterPanel (uses Meta, GroupSelect)
   ├─ ActiveFiltersSummary (uses Meta, urlExportarCsv)
   ├─ PriorityGroupsBar (uses Meta)
   ├─ KpiCards (uses KpisResp)
   ├─ TimeSeriesChart (uses buscarSerie)
   ├─ AgePyramid (uses buscarDemografia)
   ├─ TopCidChart (uses buscarTopCid)
   ├─ MunicipiosMapa (uses buscarGeo, buscarMapa)
   └─ MunicipiosTabela (uses buscarMunicipios)
```

---

**Gerado em**: 27 de Novembro de 2024
**Versão**: 1.0
