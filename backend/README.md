# Dashboard SUS — Monitoramento Epidemiológico

<p align="center">
  <strong>Dashboard Interativo de Dados de Saúde Pública</strong><br>
  Análise, processamento e visualização de indicadores epidemiológicos a partir de dados públicos do SUS.
</p>

---

## Sobre o projeto

O **Dashboard SUS** é um projeto de análise e visualização de dados de saúde pública, desenvolvido com o objetivo de facilitar o monitoramento epidemiológico por meio de dados abertos oficiais do Sistema Único de Saúde (SUS).

A aplicação busca transformar dados públicos em informações acessíveis e relevantes, permitindo explorar a distribuição de doenças, acompanhar tendências temporais e analisar indicadores por diferentes recortes geográficos e demográficos.

O projeto possui como foco inicial as doenças dos aparelhos **circulatório e respiratório**, mantendo uma arquitetura extensível para incorporar outros grupos de doenças classificados pela CID-10.

## Objetivos

- Automatizar a extração e o processamento de dados epidemiológicos.
- Organizar e padronizar informações provenientes de fontes públicas.
- Disponibilizar indicadores de saúde por meio de visualizações interativas.
- Permitir análises temporais, geográficas e demográficas.
- Facilitar a exportação de dados para análises complementares.
- Desenvolver uma estrutura modular, reutilizável e escalável.

## Funcionalidades

### Monitoramento epidemiológico

O sistema contempla a análise de diferentes grupos de doenças:

| Grupo                                          | Classificação CID-10 |
| ---------------------------------------------- | -------------------- |
| Doenças do aparelho circulatório               | I00–I99              |
| Doenças do aparelho respiratório               | J00–J99              |
| Neoplasias e tumores                           | C00–D48              |
| Doenças endócrinas, nutricionais e metabólicas | E00–E90              |
| Doenças infecciosas e parasitárias             | A00–B99              |
| Causas externas de morbidade e mortalidade     | V01–Y98              |

### Filtros de análise

- Unidade Federativa (UF).
- Município, utilizando código IBGE.
- Período de referência.
- Grupo de doenças e subcategorias CID-10.
- Faixa etária.
- Sexo.
- Caráter de atendimento, quando disponível.

### Indicadores e visualizações

O dashboard foi especificado para disponibilizar:

- **Indicadores gerais:** total de registros, mortalidade, permanência hospitalar e variação percentual.
- **Série temporal:** evolução mensal dos registros.
- **Distribuição demográfica:** análise por faixa etária e sexo.
- **Ranking CID-10:** identificação dos agravos mais frequentes.
- **Distribuição geográfica:** comparação entre municípios.
- **Exportação:** download dos dados filtrados em CSV.

## Arquitetura do projeto

O projeto adota uma organização modular, buscando separar as responsabilidades de processamento, persistência, consultas e visualização.

```text
Dashboard-SUS/
│
├── data/
│   └── # Dados processados e arquivos auxiliares
│
├── frontend/
│   └── src/
│       ├── app.py
│       ├── database.py
│       ├── dictionary.py
│       ├── etl.py
│       ├── queries.py
│       ├── schemas.py
│       └── tests/
│
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile.backend
├── Dockerfile.frontend
└── README.md
```

_Observação: a estrutura acima representa a organização lógica dos principais componentes. Os nomes dos arquivos de teste e dos Dockerfiles devem refletir os nomes efetivamente utilizados no repositório._

### Responsabilidades dos módulos

| Módulo               | Responsabilidade                                                       |
| -------------------- | ---------------------------------------------------------------------- |
| `app.py`             | Inicialização e integração dos componentes da aplicação.               |
| `database.py`        | Gerenciamento da conexão e operações relacionadas ao banco de dados.   |
| `dictionary.py`      | Dicionários de classificação, códigos CID-10 e informações auxiliares. |
| `etl.py`             | Extração, transformação e carregamento dos dados epidemiológicos.      |
| `queries.py`         | Consultas e recuperação de informações para análise.                   |
| `schemas.py`         | Definição e validação das estruturas de dados.                         |
| `test_etl.py`        | Testes automatizados do pipeline ETL.                                  |
| `test_dictionary.py` | Testes das classificações e dicionários.                               |

## Tecnologias

O projeto utiliza Python como base para processamento e organização dos dados.

| Tecnologia   | Aplicação                                              |
| ------------ | ------------------------------------------------------ |
| Python       | Desenvolvimento da aplicação e processamento de dados. |
| Docker       | Containerização e padronização do ambiente.            |
| SQL          | Persistência e consulta de informações.                |
| Pytest       | Testes automatizados.                                  |
| Git / GitHub | Versionamento e gerenciamento do código.               |

_As bibliotecas específicas de banco de dados, visualização e processamento devem ser atualizadas conforme as dependências efetivamente utilizadas no projeto._

## Fontes de dados

O projeto tem como referência os dados abertos oficiais disponibilizados pelo Ministério da Saúde.

Entre as fontes consideradas na especificação estão:

- **DATASUS — SIH/SUS:** Sistema de Informações Hospitalares.
- **DATASUS — SIM:** Sistema de Informações sobre Mortalidade.
- **DEMAS:** API de Dados Abertos do Ministério da Saúde.
- **OpenDataSUS:** Portal de dados abertos da saúde.

Documentação e acesso:

- [DATASUS](https://datasus.saude.gov.br/)
- [OpenDataSUS](https://opendatasus.saude.gov.br/)
- [API de Dados Abertos do Ministério da Saúde](https://apidadosabertos.saude.gov.br/v1/)

**Fonte efetivamente utilizada:** preencher após confirmar qual conjunto de dados ou API alimenta a implementação atual.

## Configuração e execução

### Pré-requisitos

- Python 3.10 ou superior.
- Docker e Docker Compose, caso utilizados para execução containerizada.
- Git.

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DO_REPOSITORIO>
```

### 2. Configurar as variáveis de ambiente

Crie seu arquivo `.env` a partir do modelo disponibilizado:

```bash
cp .env.example .env
```

Configure os parâmetros necessários conforme o ambiente de execução.

**Importante:** não compartilhe o arquivo `.env` nem credenciais de acesso no repositório.

### 3. Instalar as dependências

```bash
python -m venv .venv
```

Ative o ambiente virtual:

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

### Execução com Docker

O projeto contempla configurações de containerização para os componentes de backend e frontend.

Os comandos definitivos de build e inicialização devem acompanhar os nomes dos Dockerfiles e os respectivos contextos de construção presentes no repositório.

## Testes

O projeto utiliza Pytest para execução dos testes automatizados.

Para executar a suíte de testes:

```bash
pytest
```

Para executar um módulo específico:

```bash
pytest frontend/src/test_etl.py
```

Os testes têm como finalidade verificar o comportamento dos componentes, a consistência das transformações e o tratamento de situações inesperadas.

## Tratamento e qualidade dos dados

O processamento dos dados deve considerar situações como:

- Códigos CID-10 inválidos ou não identificados.
- Municípios sem correspondência.
- Datas ausentes ou inválidas.
- Campos demográficos incompletos.
- Duplicidades e inconsistências nos registros.
- Diferenças de estrutura entre fontes de dados.

A utilização de mecanismos de armazenamento intermediário e cache também busca evitar a necessidade de realizar novas extrações de dados brutos a cada interação do usuário.

## Versionamento

O projeto utiliza Git para controle de versão, adotando o padrão **Conventional Commits** para organização do histórico de desenvolvimento.

Exemplos:

```text
feat: implement ETL pipeline
fix: handle invalid epidemiological records
test: add automated ETL tests
refactor: improve database operations
docs: update project documentation
build: configure Docker environment
```

## Considerações sobre os dados

Os dados disponibilizados pelo SUS estão sujeitos a limitações relacionadas à atualização das bases, preenchimento dos registros, disponibilidade de informações e critérios de classificação.

Portanto, os indicadores apresentados devem ser interpretados considerando as características e limitações da fonte utilizada.

Os resultados representam informações provenientes das bases públicas consultadas e não substituem análises epidemiológicas oficiais.

## Status do projeto

**Em desenvolvimento.**

O projeto está sendo desenvolvido de forma modular, com foco na construção de um pipeline de dados confiável e em uma interface de monitoramento epidemiológico interativa.

---

<p align="center">
  Desenvolvido como projeto de estudo e aplicação de engenharia de dados, processamento de informações e visualização de dados em saúde pública.
</p>
