import type { Filtros, Meta } from "../types";

const pad = (n: number) => String(n).padStart(2, "0");

export const primeiroDia = (competencia: string) => `${competencia}-01`;

export function ultimoDia(competencia: string): string {
  const [ano, mes] = competencia.split("-").map(Number);
  return `${competencia}-${pad(new Date(ano, mes, 0).getDate())}`; // dia 0 do mês seguinte
}

/** Filtros iniciais: capítulos padrão (cardiorrespiratórios), UF de foco, todo o período e sem comparação. */
export function filtrosPadrao(meta: Meta): Filtros {
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
    ...periodoCompleto(meta),
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
  const completo = periodoCompleto(meta);
  if (!completo.data_fim) return null;
  const inicioMes = primeiroDia(completo.data_fim.slice(0, 7));
  return {
    data_inicio: completo.data_inicio > inicioMes ? completo.data_inicio : inicioMes,
    data_fim: completo.data_fim,
  };
}

export function periodoCompleto(meta: Meta): {
  data_inicio: string;
  data_fim: string;
} {
  const { competencia_min: min, competencia_max: max } = meta.periodo;
  return {
    // Competência é somente fallback quando o catálogo não informa datas de internação.
    data_inicio: meta.periodo.data_min ?? (min ? primeiroDia(min) : ""),
    data_fim: meta.periodo.data_max ?? (max ? ultimoDia(max) : ""),
  };
}
