#!/usr/bin/env node
/**
 * Manus MCP Server (stdio, zero dependências)
 * Expõe a API v2 do Manus (https://api.manus.ai) como ferramentas MCP.
 *
 * Requer: MANUS_API_KEY no ambiente (ou campo "apiKey" em ./manus.config.json).
 * Rodar:  node server.mjs
 */

import { createInterface } from 'node:readline';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SERVER_NAME = 'manus-mcp';
const SERVER_VERSION = '1.0.0';
const PROTOCOL_VERSION = '2025-06-18';
const BASE_URL = process.env.MANUS_API_BASE_URL || 'https://api.manus.ai';

function loadApiKey() {
  if (process.env.MANUS_API_KEY) return process.env.MANUS_API_KEY.trim();
  try {
    const here = dirname(fileURLToPath(import.meta.url));
    const cfg = JSON.parse(readFileSync(join(here, 'manus.config.json'), 'utf8'));
    if (cfg.apiKey) return String(cfg.apiKey).trim();
  } catch {
    /* sem arquivo de config */
  }
  return null;
}

async function api(path, { method = 'GET', query, body } = {}) {
  const apiKey = loadApiKey();
  if (!apiKey) {
    throw new Error(
      'MANUS_API_KEY não configurada. Gere uma chave em https://manus.im/app#settings/developers e coloque no campo de ambiente MANUS_API_KEY deste servidor MCP.'
    );
  }

  const url = new URL(BASE_URL + path);
  for (const [k, v] of Object.entries(query || {})) {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, String(v));
  }

  const res = await fetch(url, {
    method,
    headers: {
      'content-type': 'application/json',
      'x-manus-api-key': apiKey,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(`Resposta não-JSON (HTTP ${res.status}): ${text.slice(0, 500)}`);
  }

  if (!res.ok || data.ok === false) {
    const err = data.error || {};
    throw new Error(
      `Manus API ${res.status} ${err.code || ''}: ${err.message || text.slice(0, 500)}`
    );
  }
  return data;
}

const tools = [
  {
    name: 'manus_create_task',
    description:
      'Cria uma nova tarefa no Manus (agente autônomo) e retorna task_id e task_url. Use para delegar trabalho longo, pesquisas, automações de navegador ou geração de arquivos. A tarefa roda de forma assíncrona: acompanhe com manus_get_task / manus_get_task_messages.',
    inputSchema: {
      type: 'object',
      properties: {
        prompt: { type: 'string', description: 'Instrução completa para o agente Manus.' },
        agent_profile: {
          type: 'string',
          enum: ['lite', 'standard', 'max', 'max-medium', 'max-high', 'max-extra', 'max-ultra'],
          description: 'Perfil do agente (padrão: standard). max-ultra é o mais profundo e caro.',
        },
        project_id: { type: 'string', description: 'ID de projeto Manus (opcional) para aplicar instruções fixas.' },
        interactive_mode: {
          type: 'boolean',
          description: 'Se true, o agente pode pausar para perguntas. Padrão: false.',
        },
        hide_in_task_list: { type: 'boolean', description: 'Não listar a tarefa no app web. Padrão: false.' },
      },
      required: ['prompt'],
    },
  },
  {
    name: 'manus_list_tasks',
    description: 'Lista tarefas recentes do Manus com status, título, consumo de créditos e URL.',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'number', description: 'Quantidade (padrão 20).' },
        cursor: { type: 'string', description: 'Cursor de paginação.' },
        order: { type: 'string', enum: ['asc', 'desc'], description: 'Ordenação (padrão desc).' },
        scope: { type: 'string', description: 'Escopo opcional de filtro suportado pela API.' },
      },
    },
  },
  {
    name: 'manus_get_task',
    description:
      'Retorna detalhes de uma tarefa: status, agent_status, has_running_background_jobs e estado de espera. Use para saber se terminou antes de ler a conversa.',
    inputSchema: {
      type: 'object',
      properties: { task_id: { type: 'string', description: 'ID da tarefa.' } },
      required: ['task_id'],
    },
  },
  {
    name: 'manus_get_task_messages',
    description:
      'Lê a conversa/eventos de uma tarefa (resposta final, uso de ferramentas, pedidos de confirmação). Use verbose=true para ver parâmetros de ferramentas.',
    inputSchema: {
      type: 'object',
      properties: {
        task_id: { type: 'string', description: 'ID da tarefa.' },
        limit: { type: 'number', description: 'Quantidade de eventos (padrão 50).' },
        cursor: { type: 'string', description: 'Cursor de paginação.' },
        order: { type: 'string', enum: ['asc', 'desc'], description: 'Ordenação dos eventos.' },
        start_event_id: { type: 'string', description: 'Começar a partir deste event id.' },
        verbose: { type: 'boolean', description: 'Incluir detalhes de ferramentas.' },
      },
      required: ['task_id'],
    },
  },
  {
    name: 'manus_send_message',
    description: 'Envia uma nova mensagem (turno) para uma tarefa Manus existente, dando continuidade à conversa.',
    inputSchema: {
      type: 'object',
      properties: {
        task_id: { type: 'string', description: 'ID da tarefa.' },
        content: { type: 'string', description: 'Texto da mensagem.' },
        agent_profile: { type: 'string', description: 'Perfil opcional para este turno.' },
      },
      required: ['task_id', 'content'],
    },
  },
  {
    name: 'manus_stop_task',
    description: 'Para uma tarefa em execução.',
    inputSchema: {
      type: 'object',
      properties: { task_id: { type: 'string', description: 'ID da tarefa.' } },
      required: ['task_id'],
    },
  },
];

async function callTool(name, args = {}) {
  switch (name) {
    case 'manus_create_task': {
      const body = {
        message: { content: args.prompt },
        agent_profile: args.agent_profile || undefined,
        project_id: args.project_id || undefined,
        interactive_mode: args.interactive_mode ?? false,
        hide_in_task_list: args.hide_in_task_list ?? false,
      };
      const r = await api('/v2/task.create', { method: 'POST', body });
      const t = r.task || r;
      return {
        task_id: t.task_id || t.id,
        task_url: t.task_url,
        title: t.task_title || t.title,
        status: t.status,
      };
    }
    case 'manus_list_tasks':
      return await api('/v2/task.list', {
        query: { limit: args.limit ?? 20, cursor: args.cursor, order: args.order || 'desc', scope: args.scope },
      });
    case 'manus_get_task':
      return await api('/v2/task.detail', { query: { task_id: args.task_id } });
    case 'manus_get_task_messages':
      return await api('/v2/task.listMessages', {
        query: {
          task_id: args.task_id,
          limit: args.limit ?? 50,
          cursor: args.cursor,
          order: args.order,
          start_event_id: args.start_event_id,
          verbose: args.verbose,
        },
      });
    case 'manus_send_message': {
      const body = { task_id: args.task_id, message: { content: args.content } };
      if (args.agent_profile) body.agent_profile = args.agent_profile;
      return await api('/v2/task.sendMessage', { method: 'POST', body });
    }
    case 'manus_stop_task':
      return await api('/v2/task.stop', { method: 'POST', body: { task_id: args.task_id } });
    default:
      throw new Error(`Ferramenta desconhecida: ${name}`);
  }
}

function send(payload) {
  process.stdout.write(JSON.stringify(payload) + '\n');
}

function reply(id, result) {
  send({ jsonrpc: '2.0', id, result });
}

function replyError(id, code, message) {
  send({ jsonrpc: '2.0', id, error: { code, message } });
}

async function handle(msg) {
  const { id, method, params } = msg;

  if (method === 'initialize') {
    return reply(id, {
      protocolVersion: PROTOCOL_VERSION,
      capabilities: { tools: { listChanged: false } },
      serverInfo: { name: SERVER_NAME, version: SERVER_VERSION },
    });
  }

  if (method === 'notifications/initialized' || method === 'initialized') return; // notificação: sem resposta
  if (method === 'ping') return reply(id, {});
  if (method === 'tools/list') return reply(id, { tools });

  if (method === 'tools/call') {
    const name = params?.name;
    const args = params?.arguments || {};
    try {
      const result = await callTool(name, args);
      return reply(id, {
        content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
      });
    } catch (e) {
      return reply(id, {
        content: [{ type: 'text', text: `Erro: ${e.message}` }],
        isError: true,
      });
    }
  }

  if (id !== undefined) replyError(id, -32601, `Método não suportado: ${method}`);
}

const rl = createInterface({ input: process.stdin, terminal: false });
rl.on('line', (line) => {
  const trimmed = line.trim();
  if (!trimmed) return;
  let msg;
  try {
    msg = JSON.parse(trimmed);
  } catch {
    return;
  }
  Promise.resolve(handle(msg)).catch((e) => {
    if (msg?.id !== undefined) replyError(msg.id, -32603, String(e?.message || e));
  });
});
