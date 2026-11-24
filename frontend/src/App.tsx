import { useEffect, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { buscarKpis, buscarMeta } from "./api";
import { filtrosPadrao } from "./periodo";
import type { Filtros } from "./types";
import FilterPanel from "./components/FilterPanel";
import KpiCards from "./components/KpiCards";
import TimeSeriesChart from "./components/TimeSeriesChart";
import AgePyramid from "./components/AgePyramid";
import TopCidChart from "./components/TopCidChart";
import { ErroBanner, KpiSkeleton } from "./components/Estados";

export default function App() {
  const meta = useQuery({
    queryKey: ["meta"],
    queryFn: buscarMeta,
    staleTime: Infinity,
  });
  const [filtros, setFiltros] = useState<Filtros | null>(null);

  useEffect(() => {
    if (meta.data && filtros === null) setFiltros(filtrosPadrao(meta.data));
  }, [meta.data, filtros]);

  const kpis = useQuery({
    queryKey: ["kpis", filtros],
    queryFn: () => buscarKpis(filtros as Filtros),
    enabled: filtros !== null,
    placeholderData: keepPreviousData,
  });

  return (
    <div className="app">
      <header className="topo">
        <h1>Monitoramento Epidemiológico — SUS</h1>
        <p>
          Internações hospitalares (SIH/SUS) · foco inicial: doenças
          cardiorrespiratórias
        </p>
      </header>

      {meta.isError && <ErroBanner erro={meta.error} />}
      {meta.isPending && <div className="skeleton alto" />}

      {meta.data && filtros && (
        <div className="layout">
          <FilterPanel
            meta={meta.data}
            filtros={filtros}
            onChange={setFiltros}
          />
          <main className="conteudo">
            {kpis.isError && <ErroBanner erro={kpis.error} />}
            {kpis.isPending && <KpiSkeleton />}
            {kpis.data &&
              (kpis.data.atual.total === 0 ? (
                <p className="vazio">
                  Nenhum dado para os filtros selecionados.
                </p>
              ) : (
                <KpiCards dados={kpis.data} />
              ))}
            <TimeSeriesChart filtros={filtros} />
            <div className="duas-colunas">
              <AgePyramid filtros={filtros} />
              <TopCidChart filtros={filtros} />
            </div>
          </main>
        </div>
      )}
    </div>
  );
}
