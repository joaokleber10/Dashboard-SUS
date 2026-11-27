# Manus MCP Server

Servidor MCP local (stdio, zero dependências) que expõe a API v2 do Manus para qualquer agente compatível com MCP.

## Ferramentas expostas

| Ferramenta | O que faz |
| --- | --- |
| `manus_create_task` | Cria uma tarefa no Manus (prompt, perfil, projeto) e devolve `task_id` + `task_url` |
| `manus_list_tasks` | Lista tarefas recentes (status, título, créditos, URL) |
| `manus_get_task` | Detalhe/status de uma tarefa (inclui `has_running_background_jobs`) |
| `manus_get_task_messages` | Lê a conversa/eventos da tarefa (resposta final, uso de ferramentas) |
| `manus_send_message` | Manda um novo turno para uma tarefa existente |
| `manus_stop_task` | Para uma tarefa em execução |

## Requisito: chave de API

1. Abra <https://manus.im/app#settings/developers>
2. **Create API Key**, dê um nome (ex.: `mcp-local`) e copie a chave (ela só aparece uma vez).

A chave pode ser informada de duas formas:

- Variável de ambiente `MANUS_API_KEY` (recomendado — é o campo **Env** do painel);
- ou um arquivo `manus.config.json` nesta pasta: `{ "apiKey": "sua-chave" }`.

## Configuração no painel (Servidores MCP → +)

Comando: `node` — Argumento: caminho absoluto do `server.mjs`.

Formato VS Code / `mcp.json`:

```json
{
  "servers": {
    "manus": {
      "type": "stdio",
      "command": "node",
      "args": ["C:\\Users\\PC\\Documents\\GitHub\\Dashboard-SUS\\.manus\\manus-mcp\\server.mjs"],
      "env": { "MANUS_API_KEY": "sua-chave-aqui" }
    }
  }
}
```

Formato `mcpServers` (Cursor / Claude / maioria dos clientes):

```json
{
  "mcpServers": {
    "manus": {
      "command": "node",
      "args": ["C:\\Users\\PC\\Documents\\GitHub\\Dashboard-SUS\\.manus\\manus-mcp\\server.mjs"],
      "env": { "MANUS_API_KEY": "sua-chave-aqui" }
    }
  }
}
```

Se o painel tiver campos separados, preencha: **Nome** `manus`, **Command** `node`,
**Args** `C:\Users\PC\Documents\GitHub\Dashboard-SUS\.manus\manus-mcp\server.mjs`,
**Env** `MANUS_API_KEY=<chave>`.

## Teste manual

```powershell
$env:MANUS_API_KEY = "sua-chave"
'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}',
'{"jsonrpc":"2.0","id":2,"method":"tools/list"}',
'{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"manus_list_tasks","arguments":{"limit":3}}}' -join "`n" | node .manus\manus-mcp\server.mjs
```

## Observações

- Base URL alternativa: `MANUS_API_BASE_URL`.
- A API usa `x-manus-api-key`; não é preciso mais nada além do Node 18+ (aqui: Node 24).
