import type {
  BuscaCidResp,
  DemografiaResp,
  Filtros,
  GeoJson,
  KpisResp,
  MapaResp,
  Meta,
  MunicipiosResp,
  OrdemMunicipios,
  SerieResp,
  TopCidResp,
} from "./types";

const BASE: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function formatarDetalhe(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) =>
        d && typeof d === "object" && "mensagem" in d
          ? `${(d as any).campo}: ${(d as any).mensagem}`
          : JSON.stringify(d),
      )
      .join("; ");
  }
  return "erro desconhecido";
}

/** Converte os filtros em query string; URLSearchParams já codifica '+' como %2B ('65+'). */
export function paraQuery(
  f: Filtros,
  extra: Record<string, string> = {},
): string {
  const p = new URLSearchParams();
  for (const [chave, valor] of Object.entries(f)) {
    if (Array.isArray(valor)) valor.forEach((v) => p.append(chave, v));
    else if (valor) p.set(chave, valor);
  }
  for (const [k, v] of Object.entries(extra)) p.set(k, v);
  return p.toString();
}

async function get<T>(caminho: string, query = ""): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(`${BASE}${caminho}${query ? `?${query}` : ""}`);
  } catch {
    throw new ApiError(
      0,
      `Não foi possível falar com a API em ${BASE}. O backend está rodando?`,
    );
  }
  if (!resp.ok) {
    let detalhe: unknown;
    try {
      detalhe = (await resp.json()).detail;
    } catch {
      /* corpo não é JSON */
    }
    throw new ApiError(
      resp.status,
      formatarDetalhe(detalhe) || `HTTP ${resp.status}`,
    );
  }
  return resp.json() as Promise<T>;
}

export const buscarMeta = () => get<Meta>("/meta/filtros");
export const buscarKpis = (f: Filtros) => get<KpisResp>("/kpis", paraQuery(f));
export const buscarSerie = (f: Filtros, agrupar: "capitulo" | "total") =>
  get<SerieResp>("/serie-temporal", paraQuery(f, { agrupar_por: agrupar }));
export const buscarDemografia = (f: Filtros) =>
  get<DemografiaResp>("/demografia", paraQuery(f));
export const buscarTopCid = (f: Filtros, limite = 10) =>
  get<TopCidResp>("/top-cid", paraQuery(f, { limite: String(limite) }));

export const buscarMapa = (f: Filtros) =>
  get<MapaResp>("/municipios/mapa", paraQuery(f));
export const buscarMunicipios = (
  f: Filtros,
  ordenar: OrdemMunicipios,
  ordem: "asc" | "desc",
  pagina: number,
  busca: string,
  porPagina = 15,
) =>
  get<MunicipiosResp>(
    "/municipios",
    paraQuery(f, {
      ordenar_por: ordenar,
      ordem,
      pagina: String(pagina),
      por_pagina: String(porPagina),
      ...(busca ? { busca } : {}),
    }),
  );
export const buscarGeo = (uf: string) =>
  get<GeoJson>("/geojson", new URLSearchParams({ uf }).toString());
export const buscarCid = (f: Filtros, q: string) =>
  get<BuscaCidResp>("/cid/buscar", paraQuery(f, { q, limite: "15" }));

/** URL de download do CSV com os filtros atuais (o navegador baixa direto, sem passar pela memória do JS). */
export const urlExport = (f: Filtros) => `${BASE}/export.csv?${paraQuery(f)}`;
