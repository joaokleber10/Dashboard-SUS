# Tarefas de melhorias do frontend

Marque `[x]` quando uma tarefa estiver concluída. A lista é um planejamento: nenhuma mudança de código é feita apenas por marcar uma tarefa.

## Identidade visual de Patos

- [ ] **Aplicar as cores oficiais da Prefeitura de Patos** ao tema do dashboard. Consultar a [página oficial de Identidade Visual](https://patos.pb.gov.br/governo_e_municipio/identidade) e usar os arquivos oficiais da marca disponibilizados nela para confirmar a paleta e os valores de cor. A Prefeitura informa que as cores do logotipo seguem as cores da bandeira do município. Não inventar códigos HEX nem alterar a marca oficial. Depois, definir tokens de cor consistentes e conferir contraste e acessibilidade.

## Prioridade alta — clareza do painel

- [ ] **Organizar o cabeçalho** para destacar o título, o escopo do painel e as informações de fonte, período e atualização da base.
- [ ] **Agrupar e simplificar os filtros** de período, UF, município, sexo, faixa etária e CID-10; deixar visível como limpar a seleção.
- [ ] **Exibir um resumo dos filtros ativos** para que o recorte analisado fique claro.
- [ ] **Refinar os cartões de indicadores (KPIs)**: explicitar o que cada valor mede e sua unidade; só incluir comparações quando forem metodologicamente válidas.
- [ ] **Melhorar a ordem de leitura**: indicadores, evolução temporal, perfil etário, causas CID-10 e municípios.

## Prioridade média — uso e leitura

- [ ] **Aprimorar títulos, legendas e unidades dos gráficos** para facilitar a interpretação sem depender apenas das cores.
- [ ] **Melhorar a tabela de municípios**, incluindo uma leitura fácil dos filtros e das medidas exibidas.
- [ ] **Revisar mensagens de carregamento, erro e ausência de dados**, para explicar claramente o que aconteceu e o que o usuário pode fazer.
- [ ] **Verificar acessibilidade**: contraste, navegação por teclado, foco visível e alternativas textuais para informações transmitidas pelos gráficos.

## Dados e manutenção

- [ ] **Esclarecer a origem e o processo de atualização dos dados** no painel, distinguindo dados carregados pelo ETL de uma eventual integração direta com API.
- [ ] **Planejar a incorporação futura da base de Patos**, identificando a fonte e a cobertura antes de compará-la com SIH/SUS.
- [ ] **Investigar a redução do bundle do frontend**, avaliando divisão de código e carregamento sob demanda dos gráficos.
- [ ] **Atualizar o README** para refletir a estrutura atual do projeto e os comandos corretos de execução e testes.

## Referência oficial

- [Identidade Visual — Prefeitura Municipal de Patos](https://patos.pb.gov.br/governo_e_municipio/identidade)
