import { useMemo, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { buscarGeo, buscarMapa } from "../api";
import type { Filtros, GeoJson, ItemMunicipio, Meta } from "../types";
import { ErroBanner } from "./Estados";

const nf = new Intl.NumberFormat("pt-BR");
const nf1 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });

type Metrica = "casos" | "obitos" | "taxa_mortalidade";
const METRICAS: { id: Metrica; nome: string }[] = [
  { id: "casos", nome: "Internações" },
  { id: "obitos", nome: "Óbitos" },
  { id: "taxa_mortalidade", nome: "Taxa de mortalidade (%)" },
];

/** Projeção equiretangular corrigida pela latitude média: suficiente para um estado. */
function montarCaminhos(geo: GeoJson) {
  let minX = Infinity,
    maxX = -Infinity,
    minY = Infinity,
    maxY = -Infinity;
  const percorrer = (c: any, fn: (x: number, y: number) => void) => {
    if (typeof c[0] === "number") fn(c[0], c[1]);
    else c.forEach((s: any) => percorrer(s, fn));
  };
  geo.features.forEach((f) =>
    percorrer(f.geometry.coordinates, (x, y) => {
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
    }),
  );
  const k = Math.cos((((minY + maxY) / 2) * Math.PI) / 180);
  const proj = (x: number, y: number): [number, number] => [
    (x - minX) * k,
    maxY - y,
  ];
  const anel = (pts: number[][]) =>
    pts
      .map(([x, y], i) => {
        const [px, py] = proj(x, y);
        return `${i ? "L" : "M"}${px.toFixed(3)} ${py.toFixed(3)}`;
      })
      .join("") + "Z";
  const caminhos = geo.features.map((f) => {
    const g = f.geometry;
    const poligonos = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
    return {
      codigo: f.properties.codigo,
      d: poligonos.map((p: number[][][]) => p.map(anel).join("")).join(""),
    };
  });
  return { caminhos, largura: (maxX - minX) * k, altura: maxY - minY };
}

function cor(valor: number | null | undefined, max: number): string {
  if (valor == null || valor <= 0 || max <= 0) return "var(--borda)";
  const t = Math.sqrt(Math.min(valor / max, 1)); // raiz: realça diferenças entre os pequenos
  return `hsl(205 80% ${92 - t * 62}%)`;
}

interface Props {
  meta: Meta;
  filtros: Filtros;
  onChange: (f: Filtros) => void;
}

export default function MunicipiosMapa({ meta, filtros, onChange }: Props) {
  const [metrica, setMetrica] = useState<Metrica>("casos");
  const [dica, setDica] = useState<ItemMunicipio | null>(null);
  const uf =
    filtros.uf ||
    (meta.ufs_disponiveis.length === 1 ? meta.ufs_disponiveis[0] : "");

  const geo = useQuery({
    queryKey: ["geo", uf],
    queryFn: () => buscarGeo(uf),
    enabled: !!uf,
    staleTime: Infinity,
    retry: false,
  });
  const dados = useQuery({
    queryKey: ["mapa", filtros],
    queryFn: () => buscarMapa(filtros),
    placeholderData: keepPreviousData,
  });

  const forma = useMemo(
    () => (geo.data ? montarCaminhos(geo.data) : null),
    [geo.data],
  );
  const porCodigo = useMemo(
    () => new Map((dados.data?.itens ?? []).map((i) => [i.codigo, i])),
    [dados.data],
  );
  const max = useMemo(
    () => Math.max(0, ...(dados.data?.itens ?? []).map((i) => i[metrica] ?? 0)),
    [dados.data, metrica],
  );
  const focoCodigo = meta.foco?.municipio_codigo;

  const selecionar = (codigo: string) =>
    onChange({
      ...filtros,
      municipio: filtros.municipio === codigo ? "" : codigo,
    });

  return (
    <section className="bloco">
      <div className="bloco-topo">
        <h3>Mapa por município{uf ? ` — ${uf}` : ""}</h3>
        <label className="campo inline">
          <select
            value={metrica}
            onChange={(e) => setMetrica(e.target.value as Metrica)}
          >
            {METRICAS.map((m) => (
              <option key={m.id} value={m.id}>
                {m.nome}
              </option>
            ))}
          </select>
        </label>
      </div>
      {!uf && (
        <p className="vazio">Escolha uma UF no filtro para ver o mapa.</p>
      )}
      {geo.isError && <ErroBanner erro={geo.error} />}
      {dados.isError && <ErroBanner erro={dados.error} />}
      {uf && (geo.isPending || dados.isPending) && (
        <div className="skeleton alto" />
      )}
      {forma && dados.data && (
        <div className={dados.isFetching ? "mapa atualizando" : "mapa"}>
          <svg
            viewBox={`0 0 ${forma.largura} ${forma.altura}`}
            role="img"
            aria-label={`Mapa de municípios de ${uf}`}
          >
            {forma.caminhos.map((c) => {
              const item = porCodigo.get(c.codigo);
              const ativo = filtros.municipio === c.codigo;
              const foco = focoCodigo === c.codigo;
              return (
                <path
                  key={c.codigo}
                  d={c.d}
                  fill={cor(item?.[metrica], max)}
                  className={`muni${ativo ? " ativo" : ""}${foco ? " foco" : ""}`}
                  onMouseEnter={() =>
                    setDica(
                      item ?? {
                        codigo: c.codigo,
                        nome: c.codigo,
                        identificado: false,
                        casos: 0,
                        obitos: 0,
                        taxa_mortalidade: null,
                        permanencia_media: null,
                        custo_total: null,
                      },
                    )
                  }
                  onMouseLeave={() => setDica(null)}
                  onClick={() => selecionar(c.codigo)}
                />
              );
            })}
          </svg>
          <div className="mapa-legenda">
            <span>0</span>
            <div className="degrade" />
            <span>
              {metrica === "taxa_mortalidade"
                ? `${nf1.format(max)}%`
                : nf.format(max)}
            </span>
          </div>
          <div className="mapa-dica" aria-live="polite">
            {dica ? (
              <>
                <strong>{dica.nome}</strong>
                {dica.codigo === focoCodigo && " (município em foco)"}
                <br />
                {nf.format(dica.casos)} internações · {nf.format(dica.obitos)}{" "}
                óbitos
                {dica.taxa_mortalidade != null &&
                  ` · ${nf1.format(dica.taxa_mortalidade)}% letalidade`}
              </>
            ) : (
              "Passe o mouse sobre um município; clique para filtrar o painel por ele."
            )}
          </div>
          <p className="nota">
            Municípios por{" "}
            {filtros.municipio_ref === "residencia"
              ? "residência do paciente"
              : "local de atendimento"}
            . Contorno grosso: município em foco
            {filtros.municipio ? "; contorno azul: município filtrado" : ""}.
            Cinza: sem casos no recorte.
          </p>
        </div>
      )}
    </section>
  );
}
