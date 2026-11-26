# Dashboard Interativo de Monitoramento Epidemiológico (SUS)

## 1. Visão Geral do Projeto
O objetivo dessa tarefa é desenvolver um **Dashboard Interativo de Dados de Saúde Pública** utilizando dados abertos oficiais do **SUS (DATASUS / Ministério da Saúde)**.

Inicialmente motivado pelo monitoramento de **doenças cardiorrespiratórias**, o sistema deve ser arquitetado de forma **dinâmica e extensível**, permitindo que o usuário final selecione e filtre diferentes grupos de agravos (capítulos da CID-10), recortes geográficos, períodos e perfis demográficos.

Crie todo o projeto em um container Docker, definindo todas as variaveis ambientes em um arquivo .env

---

## 2. Fontes de Dados Recomendadas
Você tem liberdade para escolher uma (ou combinar mais de uma) das abordagens abaixo para ingestão dos dados:

1. **Microdados do DATASUS via biblioteca (`PySUS` em Python ou `microdatasus` em R):**
   * **SIH/SUS (Sistema de Informações Hospitalares — `RD`):** Internações hospitalares, custos, dias de permanência e diagnóstico principal (`DIAG_PRINC`).
   * **SIM (Sistema de Informações sobre Mortalidade — `DO`):** Óbitos declarados e causa básica (`CAUSABAS`).
2. **API REST de Dados Abertos da DEMAS (`https://apidadosabertos.saude.gov.br/v1/`):**
   * Endpoints de procedimentos hospitalares (`/assistencia-a-saude/sih-procedimentos-hospitalares`) e capacidade instalada/leitos (`/assistencia-a-saude/cnes-leitos`).
3. **Conjuntos de Dados Abertos (OpenDataSUS / CKAN):**
   * Arquivos CSV/Parquet consolidados do Portal de Dados Abertos do Ministério da Saúde.

> Para não sobrecarregar o ambiente local durante o teste, você pode restringir a extração inicial a **1 Estado (UF)** e uma janela de **12 a 24 meses**, desde que o código permita alterar esses parâmetros facilmente.

---

## 3. Requisitos Funcionais (Filtros e Seleções)

O dashboard deve conter uma barra ou painel de controles com os seguintes filtros combináveis:

### 3.1. Seletor de Grupo de Doenças (Capítulos CID-10)
O usuário deve poder alternar entre múltiplos grupos de doenças (com foco especial nos dois primeiros, mas permitindo comparar com os demais):
* **Doenças do Aparelho Circulatório (CID-10: `I00–I99`)** — *Ex.: Infarto Agudo do Miocárdio (`I21`), Hipertensão (`I10–I15`), AVC (`I60–I69`).*
* **Doenças do Aparelho Respiratório (CID-10: `J00–J99`)** — *Ex.: Pneumonia (`J12–J18`), Asma (`J45`), DPOC (`J44`).*
* **Neoplasias / Tumores (CID-10: `C00–D48`).**
* **Doenças Endócrinas, Nutricionais e Metabólicas (CID-10: `E00–E90`)** — *Ex.: Diabetes Mellitus (`E10–E14`).*
* **Doenças Infecciosas e Parasitárias (CID-10: `A00–B99`).**
* **Causas Externas de Morbidade e Mortalidade (CID-10: `V01–Y98`).**
* **Filtro fino opcional (Subcategoria CID-10):** Busca ou seleção de códigos específicos dentro do capítulo selecionado.

### 3.2. Filtros Geográficos e Temporais
* **Unidade Federativa (UF)** e **Município** (código IBGE).
* **Período:** Seleção de intervalo de datas (Mês/Ano de competência ou data de internação/óbito).

### 3.3. Filtros Demográficos e Assistenciais
* **Faixa Etária** (ex.: `0-14`, `15-29`, `30-49`, `50-64`, `65+` anos).
* **Sexo** (`Masculino`, `Feminino`, `Ignorado`).
* **Caráter de Atendimento / Complexidade** (quando aplicável ao SIH: Eletivo vs. Urgência).
* **Outros que possam ser úteis** A vontade para adicionar filtros diversos, pensando ainda, em expandir o dashboard para outros tipos de doenças.

---

## 4. Indicadores (KPIs) e Visualizações Obrigatórias

O painel deve atualizar dinamicamente os seguintes componentes conforme os filtros aplicados:

1. **Cards de Resumo (KPIs de Topo):**
   * Total de registros no período (Internações e/ou Óbitos).
   * Taxa de mortalidade hospitalar ou proporção em relação ao total geral.
   * Tempo médio de permanência hospitalar (dias) e/ou Custo médio/total (se utilizado SIH).
   * Variação percentual em relação ao período anterior (MoM ou YoY).
2. **Série Temporal (Gráfico de Linha/Área):**
   * Evolução mensal dos casos por grupo de doença selecionado (permitindo identificar sazonalidade, comum em doenças cardiorrespiratórias no inverno).
3. **Distribuição Demográfica (Gráfico de Barras / Pirâmide Etária):**
   * Comparativo por faixa etária e sexo.
4. **Ranking de Agravos Específicos (Top 10 CID-10):**
   * Gráfico de barras horizontais mostrando as 10 subcategorias CID-10 mais frequentes dentro do grupo filtrado.
5. **Visão Geográfica ou Tabular por Município:**
   * Mapa coroplético ou tabela interativa ordenável com os municípios de maior incidência/volume.
6. **Exportação de Dados:**
   * Botão para baixar os dados filtrados na tela em formato `.csv`.

---

## 5. Requisitos Técnicos e Arquitetura

* **Stack Sugerida:**
  * Web Fullstack:* Backend em `FastAPI` + Frontend em `React`/`Next.js`.
* **Separação de Responsabilidades:**
  * Separe claramente a camada de **extração/tratamento de dados (`etl/` ou `data_pipeline.py`)** da camada de **visualização (`app.py` / `dashboard/`)**.
* **Cache e Performance:**
  * O dashboard **não deve** baixar arquivos brutos do DATASUS a cada clique de filtro do usuário. Utilize cache local (`.parquet`, `DuckDB`, `SQLite` ou `@st.cache_data`).
* **Tratamento de Erros e Dados Ausentes:**
  * Códigos CID inválidos, municípios sem correspondência ou datas nulas devem ser tratados sem quebrar a aplicação.

---

## 6. Entregáveis 

Entregue um repositório Git (ou arquivo compactado estruturado) contendo:

```text
├── README.md               # Instruções de instalação, execução e decisões técnicas
├── requirements.txt        # (ou pyproject.toml) Dependências com versões
├── src/
│   ├── etl.py              # Script/módulo de coleta e limpeza dos dados do SUS
│   ├── dictionary.py       # Mapeamento de capítulos CID-10, UFs e faixas etárias
│   └── app.py              # Aplicação do Dashboard interativo
└── data/                   # (Opcional/Ignorado se grande) Amostra processada em Parquet/CSV
```

### Documentação no `README.md`:
* Como rodar o pipeline de dados e como iniciar o dashboard em menos de 3 comandos.
* Qual fonte do SUS foi utilizada (SIH, SIM, API DEMAS) e quais limitações você encontrou nos dados brutos.
