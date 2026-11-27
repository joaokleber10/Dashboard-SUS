export interface Opcao {
  id: string;
  nome: string;
}

export interface Capitulo extends Opcao {
  inicio: string;
  fim: string;
  destaque: boolean;
  padrao: boolean;
}

export interface GrupoPrioritario {
  id: string;
  nome: string;
  capitulo: string;
  inicio: string;
  fim: string;
}

export interface GrupoDinamico {
  id: string;
  nome: string;
  capitulo: string;
  inicio: string;
  fim: string;
  internacoes: number;
}

export interface BlocoCid {
  id: string;
  nome: string;
  capitulo: string;
  inicio: string;
  fim: string;
}

export interface CidResolvido {
  valido: boolean;
  cid3: string | null;
  capitulo: Capitulo | null;
  bloco: BlocoCid | null;
  grupo_prioritario: GrupoPrioritario | null;
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
  grupos: GrupoPrioritario[];
  faixas_etarias: FaixaEtaria[];
  sexos: Opcao[];
  carater_atendimento: Opcao[];
  complexidades: Opcao[];
  ufs: Uf[];
  ufs_disponiveis: string[];
  export_max_linhas: number;
  foco: {
    uf: string | null;
    municipio_codigo: string;
    municipio_nome: string | null;
  } | null;
  fontes_disponiveis: { id: string; casos: number }[];
  periodo: {
    data_min: string | null;
    data_max: string | null;
    competencia_min: string | null;
    competencia_max: string | null;
    fonte?: string;
    ultima_atualizacao?: string | null;
  };
}

export interface Filtros {
  capitulo_ids: string[];
  grupo_ids: string[];
  cid_codigos: string[];
  uf: string; // "" = todas
  municipio: string; // código IBGE de 6 dígitos, "" = todos
  municipio_ref: "residencia" | "atendimento";
  fontes: string[]; // [] = todas
  data_inicio: string; // AAAA-MM-DD ou ""
  data_fim: string;
  faixas_etarias: string[];
  sexos: string[];
  carater: string[];
  complexidade: string[];
  comparacao: "nenhuma" | "periodo_anterior" | "ano_anterior";
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
    municipios_atendidos?: number;
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
  cid_nome?: string | null;
  grupo_nome?: string | null;
  casos: number;
  obitos: number;
  percentual: number | null;
}

export interface TopCidResp {
  total_com_cid: number;
  itens: ItemCid[];
}

export interface ItemMunicipio {
  codigo: string | null;
  nome: string;
  identificado: boolean;
  casos: number;
  obitos: number;
  taxa_mortalidade: number | null;
  permanencia_media: number | null;
  custo_total: number | null;
  percentual?: number | null;
}
export interface MunicipiosResp {
  total_municipios: number;
  total_casos: number;
  pagina: number;
  por_pagina: number;
  itens: ItemMunicipio[];
}
export interface MapaResp {
  itens: ItemMunicipio[];
}
export interface BuscaCidResp {
  itens: {
    cid3: string;
    capitulo_id: string | null;
    casos: number;
    cid_nome: string | null;
  }[];
}
export interface GeoJson {
  type: "FeatureCollection";
  features: {
    type: "Feature";
    properties: { codigo: string };
    geometry: { type: string; coordinates: any };
  }[];
}
export type OrdemMunicipios =
  | "casos"
  | "obitos"
  | "taxa_mortalidade"
  | "permanencia_media"
  | "custo_total"
  | "nome";
