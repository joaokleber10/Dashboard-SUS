import type { Filtros, Meta } from "./types";

const pad = (n: number) => String(n).padStart(2, "0");

export const primeiroDia = (competencia: string) => `${competencia}-01`;

export function ultimoDia(competencia: string): string {
  const [ano, mes] = competencia.split("-").map(Number);
  return `${competencia}-${pad(new Date(ano, mes, 0).getDate())}`; // dia 0 do mês seguinte
}

/** Filtros iniciais: capítulos padrão (cardiorrespiratórios), UF de foco, todo o período e sem comparação. */
export function filtrosPadrao(meta: Meta): Filtros {
  const { competencia_min: min, competencia_max: max } = meta.periodo;
  return {
    capitulo_ids: meta.capitulos.filter((c) => c.padrao).map((c) => c.id),
    grupo_ids: [],
    cid_codigos: [],
    uf:
      meta.foco?.uf ??
      (meta.ufs_disponiveis.length === 1 ? meta.ufs_disponiveis[0] : ""),
    municipio: "",
    municipio_ref: "residencia",
    fontes: [],
    data_inicio: min ? primeiroDia(min) : "",
    data_fim: max ? ultimoDia(max) : "",
    faixas_etarias: [],
    sexos: [],
    carater: [],
    complexidade: [],
    comparacao: "nenhuma",
  };
}

export function ultimoMes(
  meta: Meta,
): { data_inicio: string; data_fim: string } | null {
  const max = meta.periodo.competencia_max;
  return max
    ? { data_inicio: primeiroDia(max), data_fim: ultimoDia(max) }
    : null;
}

export function periodoCompleto(meta: Meta): {
  data_inicio: string;
  data_fim: string;
} {
  const { competencia_min: min, competencia_max: max } = meta.periodo;
  return {
    data_inicio: min ? primeiroDia(min) : "",
    data_fim: max ? ultimoDia(max) : "",
  };
}
