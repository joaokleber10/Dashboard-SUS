# Referência visual — Prefeitura de Patos / Dashboard-SUS

## Fontes

- Página oficial de identidade visual, consultada em 27/11/2026: https://patos.pb.gov.br/governo_e_municipio/identidade
- Site oficial: https://patos.pb.gov.br/
- A página oficial afirma que a identidade padroniza as cores do logotipo conforme a bandeira municipal e oferece os arquivos abaixo. Ela não informa HEX no texto consultado.
- Marca oficial / identidade em PDF, link oferecido na página: http://patos.pb.gov.br/admin/tinyfinder/assets/uploads/file/l1sq22bu.pdf
- Logo PNG transparente, ZIP oferecido na página: http://patos.pb.gov.br/admin/tinyfinder/assets/uploads/file/i623eg8p.zip
- Logo Corel Draw, ZIP oferecido na página: http://patos.pb.gov.br/admin/tinyfinder/assets/uploads/file/vg6m96pw.zip
- URL histórica do logo usado no site, ainda pendente de verificação nesta etapa: https://patos.pb.gov.br/skins/avancado/template/2024/assets/images/logo/logo-2025.png

## Referência do usuário

Imagem fornecida nesta conversa: 407ab522-ecba-467a-b225-de2a58f374b9.jpg (1366 × 1157). Caminho do anexo: C:\Users\PC\.manus-desktop\prod\uploads\d8Azhui0jBkOTGRV6wWdHA\kwGI2Nst5CC6z9DJl5F6A8\1-407ab522-ecba-467a-b225-de2a58f374b9.jpg.

Características observadas: sidebar azul-petróleo com navegação, fundo principal azul-escuro, superfícies de cartões em azul mais claro, bordas discretas, texto claro, destaque ciano, cabeçalho contextual, indicadores alinhados, filtros horizontais compactos e tabelas densas.

A imagem contém valores e datas demonstrativos. Não copiar os números, a atualização 10/02/2025, o período “últimos 12 meses”, um filtro de hospitais ou métricas adicionais sem suporte da API. Não recriar o quadrado PB como se fosse logotipo oficial.

## Paleta histórica recuperada

Referência anterior recuperada do trabalho de design de Meio Ambiente da Prefeitura de Patos: azul principal #014A7F; azul extraído do logo #1D94D1; ciano de apoio #0DCAF0; azul profundo #0B3850; fundo claro #F2F2F2; texto #333333; branco #FFFFFF.

Esses valores foram extraídos do CSS do site e de um PNG em trabalho anterior. Não foram todos certificados por um manual oficial. Tratar superfícies escuras e cores derivadas para contraste como escolhas do projeto, não especificações oficiais da prefeitura. Não importar automaticamente os verdes da temática ambiental.

## Escopo desta etapa

Adaptar a aparência à imagem, com marca real, navegação lateral e paleta de Patos, preservando as três visões e os filtros compartilhados já implementados. Mapa e tabela continuam alternáveis. Manter tema claro/escuro, dados reais e estado das consultas. Apenas frontend, mudanças locais, sem commit/push/publicação.

O bloqueio anterior do Vite em 127.0.0.1:5173 foi EACCES; a API local em localhost:8000 também não respondeu. Nenhuma tentativa de corrigir o ambiente foi feita nesta etapa.

## Asset local identificado

O usuário informou que a logo da cidade já está no código. Arquivo conferido: `src/Public/Icon/logo.png`, 221 × 208 px, PNG, 42.739 bytes. A imagem apresenta o brasão de Patos-PB. Usar diretamente por import do Vite, sem redesenhá-lo, recolori-lo ou alterar proporções. Não é necessário duplicar a imagem nem baixar outra marca. Não confundir `src/Public` com o diretório público padrão do Vite.

A origem imediata é o asset fornecido pelo usuário no repositório. A consulta ao HTML da página inicial foi encerrada porque deixou de ser necessária; não houve confirmação adicional da URL histórica `logo-2025.png` nem download da marca. A página de identidade foi lida com sucesso.

## Direção visual aprovada em 27/11/2026

- Dashboard institucional para gestão da saúde, com leitura em notebook e adaptação ao celular. Linguagem de dados sóbria, seguindo a imagem do usuário.
- Redesign visual preservando arquitetura, dados e contratos de interação. Variância 3/10: grid e navegação previsíveis. Movimento 2/10: apenas feedback curto. Densidade 6/10: três visões e filtros progressivos. Dependência de assets 3/10: brasão real, sem imagens decorativas. Fidelidade à marca 9/10: brasão inalterado e azuis de Patos.
- Papel: leitura dos dados do recorte, não página de apresentação. Distância: notebook/desktop, com título contextual legível e números tabulares. Temperatura: institucional e calma. Capacidade: menu lateral de aproximadamente 220 px; gráficos de perfil e território não voltam à visão geral.
- Navegação lateral: Visão geral; Perfil e causas; Municípios. Em telas pequenas, navegação compacta, sem ocupar permanentemente 220 px.
- Principal #014A7F; azul de apoio #1D94D1; ciano #0DCAF0 para destaque no tema escuro; sidebar #0B3850. Fundo escuro derivado #0D1B2A e cartões #122C3E. Tema claro com #F2F2F2 e cartões brancos. Superfícies derivadas são decisões do dashboard, não HEX certificados do manual.
- Texto #0B3850 / secundário #536C7F sobre branco; texto #F2F7FA / secundário #B4CADA sobre cartões escuros. Branco em botões #014A7F. Não usar #1D94D1 como texto pequeno sobre branco: contraste de apenas 3,38:1.
- Tipografia existente preservada (system-ui / Segoe UI); sem instalar fontes ou bibliotecas. Título contextual maior, rótulos discretos, números com alinhamento tabular.
- Espaçamento em múltiplos de 8 px; bordas discretas; raio de 8–12 px; sem sombras fortes ou efeitos decorativos.
- Manter os indicadores originais, datas reais, preferência de tema salva, resumo e exportação dos filtros. Brasão sobre base clara quando necessário para manter legibilidade dos contornos pretos, sem mudar o arquivo.
- Maior risco: mover navegação e cabeçalho sem desmontar controles locais. Preservar filtros em uma fonte de estado, painéis montados e consultas desabilitadas nas visões ocultas.

### Contrastes calculados na preparação

| Primeiro plano | Fundo | Contraste |
|---|---|---|
| #FFFFFF | #014A7F | 9,18:1 |
| #0DCAF0 | #122C3E | 7,37:1 |
| #B4CADA | #122C3E | 8,52:1 |
| #F2F7FA | #122C3E | 13,37:1 |
| #536C7F | #FFFFFF | 5,50:1 |
| #0B3850 | #F2F2F2 | 11,06:1 |

Estes são os testes matemáticos da preparação, não uma auditoria WCAG completa. A validação dos tokens realmente implementados está em `tests/branding.test.mjs`.

## Primeira versão aplicada

- `src/components/layout/Sidebar.tsx`: brasão local, três visões, navegação vertical por teclado no desktop e horizontal em telas até 900 px.
- `src/components/layout/Header.tsx` e `DataInfoBar.tsx`: título por visão, tema e metadados reais. Nenhuma data demonstrativa ou botão Ajuda sem ação.
- `src/pages/Dashboard/Dashboard.tsx`: layout lateral; filtros em uma única fonte de estado; painéis permanentemente montados, com consultas e gráficos visuais ativos somente na visão selecionada. Mapa e tabela continuam exclusivos.
- `src/components/kpis/KpiCards.tsx`: quatro cartões principais alinhados. A contagem existente de municípios atendidos permanece como informação de apoio, sem quinta coluna ou métrica removida.
- `src/styles/brand.css`: tokens e regras da marca, temas claro/escuro, espaçamento, gráficos, campos, tabela, foco e movimento reduzido. Importado depois das folhas anteriores, sem migração de stack ou biblioteca nova.
- Gráficos usam tokens da paleta; séries temporais repetidas têm traçados diferentes para reduzir ambiguidade. O mapa mantém a transformação pela raiz e compartilha os mesmos extremos de cor com a legenda.
- Preferência `sus-theme` preservada. Exportar CSV mantém URL e comportamento; suas cores agora usam o par de ação adequado ao tema.
- Estados de carregamento e erro mantêm o menu e o cabeçalho visíveis; dados indisponíveis não são substituídos por números fictícios.

### Verificações executadas

Na pasta `frontend`:

```powershell
node node_modules/typescript/bin/tsc --noEmit
node --test tests/dashboard.test.mjs tests/branding.test.mjs
node node_modules/vite/bin/vite.js build
node scripts/verificar-conexao.mjs
```

TypeScript aprovado; 28 testes aprovados; build Vite 6.4.6 aprovado. O brasão foi resolvido no build (`dist/assets/logo-BPRu0Z8d.png`). Os testes cobrem períodos, handlers de teclado, renderização estática dos cartões/metadados, pares de contraste dos tokens, arquivo do brasão e persistência do tema. Não são testes de integração em navegador nem auditoria de acessibilidade completa.

Permanece o aviso de bundle JS maior que 500 kB, aproximadamente 640 kB antes de gzip. Não houve divisão de chunks ou otimização de performance nesta etapa.

### Prévia e conexão

A execução normal com permissão de rede voltou a falhar em `127.0.0.1:5173` com EACCES. A tentativa do mesmo comando com autorização de execução iniciou o serviço. Nenhuma configuração do Windows, política de execução ou código do backend foi alterado.

- Prévia local conferida com HTTP 200: http://127.0.0.1:5173/
- Metadados da API local conferidos com HTTP 200: http://localhost:8000/meta/filtros
- Comando da prévia: `node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort`

A navegação local do agente está desativada. Não houve inspeção visual em navegador, validação de screenshots ou teste de ponta a ponta de todos os endpoints. A prévia está disponível para o usuário conferir a primeira versão; esta etapa não afirma fidelidade pixel a pixel à imagem.

### Limite de entrega

Somente frontend, alterações locais, sem commit, staging, push ou publicação. A organização do Copilot e os arquivos anteriores foram preservados. Próximo passo: obter feedback da primeira versão antes de ampliar o refinamento visual.
