import { useEffect, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { buscarKpis, buscarMeta } from "./api";
import { filtrosPadrao } from "./periodo";
import type { Filtros } from "./types";
import FilterPanel from "./components/FilterPanel";
import ActiveFiltersSummary from "./components/ActiveFiltersSummary";
import PriorityGroupsBar from "./components/PriorityGroupsBar";
import KpiCards from "./components/KpiCards";
import TimeSeriesChart from "./components/TimeSeriesChart";
import AgePyramid from "./components/AgePyramid";
import TopCidChart from "./components/TopCidChart";
import TopMunicipios from "./components/TopMunicipios";
import { ErroBanner, KpiSkeleton } from "./components/Estados";

type Theme = "light" | "dark";
const THEME_KEY = "sus-theme";

function temaInicial(): Theme {
  try {
    const salvo = localStorage.getItem(THEME_KEY);
    if (salvo === "light" || salvo === "dark") return salvo;
  } catch {
    /* armazenamento indisponível */
  }
  if (
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-color-scheme: dark)").matches
  ) {
    return "dark";
  }
  return "light";
}

function formatarCompetencia(comp: string | null | undefined): string {
  if (!comp) return "—";
  const limpo = comp.replace(/\D/g, "");
  if (limpo.length === 6) return `${limpo.slice(4, 6)}/${limpo.slice(0, 4)}`;
  if (/^\d{4}-\d{2}/.test(comp)) return `${comp.slice(5, 7)}/${comp.slice(0, 4)}`;
  return comp;
}

function formatarAtualizacao(valor: string | null | undefined): string | null {
  if (!valor) return null;
  const d = new Date(valor);
  if (!Number.isNaN(d.getTime())) {
    return new Intl.DateTimeFormat("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    }).format(d);
  }
  return valor;
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(temaInicial);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      /* armazenamento indisponível */
    }
  }, [theme]);

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

  const handleSelectMunicipio = (codigo: string) => {
    setFiltros((prev) =>
      prev
        ? { ...prev, municipio: prev.municipio === codigo ? "" : codigo }
        : prev,
    );
  };

  const ultimaAtualizacao = formatarAtualizacao(
    meta.data?.periodo.ultima_atualizacao,
  );

  return (
    <div className="app">
      <header className="topo">
        <div className="topo-row">
          <div>
            <h1>Monitoramento Epidemiológico — SUS</h1>
            <p>
              Internações hospitalares (SIH/SUS) · foco inicial: doenças
              cardiorrespiratórias
            </p>
          </div>
          <button
            type="button"
            className="theme-toggle"
            onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
            aria-label={
              theme === "dark" ? "Ativar tema claro" : "Ativar tema escuro"
            }
            title={
              theme === "dark"
                ? "Mudar para tema claro"
                : "Mudar para tema escuro"
            }
          >
            {theme === "dark" ? "☀️ Claro" : "🌙 Escuro"}
          </button>
        </div>
      </header>

      {meta.data && (
        <div className="data-info-bar" role="status">
          <span>
            <strong>Base de dados:</strong>{" "}
            {meta.data.periodo.fonte || "SIH/SUS (RD — DATASUS)"}
          </span>
          <span className="data-info-sep" aria-hidden="true">
            •
          </span>
          <span>
            <strong>Competências:</strong>{" "}
            {formatarCompetencia(meta.data.periodo.competencia_min)} a{" "}
            {formatarCompetencia(meta.data.periodo.competencia_max)}
          </span>
          <span className="data-info-sep" aria-hidden="true">
            •
          </span>
          <span>
            <strong>UFs:</strong>{" "}
            {meta.data.ufs_disponiveis.length > 0
              ? meta.data.ufs_disponiveis.join(", ")
              : "Todas"}
          </span>
          {ultimaAtualizacao && (
            <>
              <span className="data-info-sep" aria-hidden="true">
                •
              </span>
              <span>
                <strong>Última atualização:</strong> {ultimaAtualizacao}
              </span>
            </>
          )}
        </div>
      )}

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
            <ActiveFiltersSummary
              meta={meta.data}
              filtros={filtros}
              onChange={setFiltros}
            />
            <PriorityGroupsBar
              meta={meta.data}
              filtros={filtros}
              onChange={setFiltros}
            />

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

            <TopMunicipios
              filtros={filtros}
              onSelectMunicipio={handleSelectMunicipio}
            />
          </main>
        </div>
      )}
    </div>
  );
}
