export interface Opcao {
  id: string;
  nome: string;
}
export interface Capitulo extends Opcao {
  inicio: string;
  fim: string;
  destaque: boolean;
}
export interface FaixaEtaria {
  id: string;
  min: number;
  max: number | null;
}
export interface Uf {
  sigla: string;
  codigo: number;
  nome: string;
}

export interface Meta {
  capitulos: Capitulo[];
  faixas_etarias: FaixaEtaria[];
  sexos: Opcao[];
  carater_atendimento: Opcao[];
  complexidades: Opcao[];
  ufs: Uf[];
  ufs_disponiveis: string[];
  periodo: {
    data_min: string | null;
    data_max: string | null;
    competencia_min: string | null;
    competencia_max: string | null;
  };
}

export interface Filtros {
  capitulo_ids: string[];
  uf: string; // "" = todas
  data_inicio: string; // AAAA-MM-DD ou ""
  data_fim: string;
  faixas_etarias: string[];
  sexos: string[];
  carater: string[];
  complexidade: string[];
  comparacao: "periodo_anterior" | "ano_anterior";
}

export interface Agregados {
  total: number;
  obitos: number;
  taxa_mortalidade: number | null;
  permanencia_media: number | null;
  custo_total: number | null;
  custo_medio: number | null;
}

export interface KpisResp {
  atual: Agregados & {
    total_geral: number;
    proporcao_total_geral: number | null;
  };
  anterior: Agregados | null;
  variacao_pct: Record<string, number | null> | null;
  periodo_anterior: { inicio: string; fim: string } | null;
  comparacao: string;
}

export interface Ponto {
  ano_mes: string;
  casos: number;
  obitos: number;
}
export interface SerieItem {
  id: string;
  nome: string;
  pontos: Ponto[];
}
export interface SerieResp {
  agrupar_por: string;
  meses: string[];
  series: SerieItem[];
}

export interface FaixaDemografia {
  faixa: string;
  M: number;
  F: number;
  I: number;
  total: number;
}
export interface DemografiaResp {
  faixas: FaixaDemografia[];
  sem_faixa: number;
}

export interface ItemCid {
  cid3: string;
  capitulo_id: string | null;
  capitulo_nome: string;
  casos: number;
  obitos: number;
  percentual: number | null;
}
export interface TopCidResp {
  total_com_cid: number;
  itens: ItemCid[];
}
