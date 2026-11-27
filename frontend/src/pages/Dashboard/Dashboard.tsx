import { useEffect, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { buscarKpis, buscarMeta } from "../../services/api";
import { filtrosPadrao } from "../../services/periodo";
import type { Filtros } from "../../types";
import type { Theme } from "../../components/common/ThemeToggle";
import FilterPanel from "../../components/filters/FilterPanel";
import ActiveFiltersSummary from "../../components/filters/ActiveFiltersSummary";
import KpiCards from "../../components/kpis/KpiCards";
import TimeSeriesChart from "../../components/charts/TimeSeriesChart";
import AgePyramid from "../../components/charts/AgePyramid";
import TopCidChart from "../../components/charts/TopCidChart";
import MunicipiosMapa from "../../components/municipios/MunicipiosMapa";
import MunicipiosTabela from "../../components/municipios/MunicipiosTabela";
import ViewTabs from "../../components/common/ViewTabs";
import { ErroBanner, KpiSkeleton } from "../../components/common/Skeleton";
import { Header } from "../../components/layout/Header";
import { Sidebar } from "../../components/layout/Sidebar";

const VISOES = [
  { id: "geral", nome: "Visão geral" },
  { id: "perfil", nome: "Perfil e causas" },
  { id: "municipios", nome: "Municípios" },
] as const;
type Visao = (typeof VISOES)[number]["id"];

const TERRITORIO = [
  { id: "mapa", nome: "Mapa" },
  { id: "tabela", nome: "Tabela" },
] as const;
type VisaoTerritorio = (typeof TERRITORIO)[number]["id"];

const DESCRICOES: Record<Visao, string> = {
  geral: "Indicadores do recorte selecionado e evolução das internações no tempo.",
  perfil: "Distribuição por idade e sexo e diagnósticos mais frequentes no recorte.",
  municipios: "Explore os municípios no mapa ou compare os valores na tabela.",
};

interface Props {
  theme: Theme;
  onThemeChange: (theme: Theme) => void;
}

// Filtros e escolhas locais não são reiniciados ao trocar de visão.
export function Dashboard({ theme, onThemeChange }: Props) {
  const [filtros, setFiltros] = useState<Filtros | null>(null);
  const [visao, setVisao] = useState<Visao>("geral");
  const [territorio, setTerritorio] = useState<VisaoTerritorio>("mapa");
  const visaoAtual = VISOES.find((opcao) => opcao.id === visao) ?? VISOES[0];

  const meta = useQuery({
    queryKey: ["meta"],
    queryFn: buscarMeta,
    staleTime: Infinity,
  });

  useEffect(() => {
    if (meta.data && filtros === null) setFiltros(filtrosPadrao(meta.data));
  }, [meta.data, filtros]);

  const kpis = useQuery({
    queryKey: ["kpis", filtros],
    queryFn: () => buscarKpis(filtros as Filtros),
    enabled: filtros !== null && visao === "geral",
    placeholderData: keepPreviousData,
  });

  return (
    <div className="dashboard-shell">
      <a className="skip-link" href="#conteudo-principal">Ir para o conteúdo</a>
      <Sidebar opcoes={VISOES} valor={visao} onChange={setVisao} />

      <main id="conteudo-principal" tabIndex={-1} className="layout dashboard dashboard-main" aria-label="Painel de internações">
        <Header
          theme={theme}
          onThemeChange={onThemeChange}
          titulo={visaoAtual.nome}
          descricao={DESCRICOES[visao]}
          meta={meta.data}
        />

        {meta.data && filtros && (
          <div className="dashboard-filters">
            <FilterPanel meta={meta.data} filtros={filtros} onChange={setFiltros} />
            <ActiveFiltersSummary meta={meta.data} filtros={filtros} onChange={setFiltros} />
          </div>
        )}

        {VISOES.map((opcao) => (
          <section
            key={opcao.id}
            id={`dashboard-panel-${opcao.id}`}
            role="tabpanel"
            aria-labelledby={`dashboard-tab-${opcao.id}`}
            tabIndex={0}
            hidden={visao !== opcao.id}
            className="dashboard-view"
          >
            {meta.isError ? (
              <div className="dashboard-connection-state">
                <h2>Não foi possível carregar a base</h2>
                <p>Confira a conexão com a API. Nenhum indicador demonstrativo será exibido.</p>
                <ErroBanner erro={meta.error} />
                <button type="button" onClick={() => void meta.refetch()} disabled={meta.isFetching}>
                  {meta.isFetching ? "Tentando novamente…" : "Tentar novamente"}
                </button>
              </div>
            ) : !meta.data || !filtros ? (
              <div className="dashboard-loading" role="status" aria-label="Carregando opções do painel">
                <p>Carregando os metadados da base…</p>
                <div className="skeleton alto" aria-hidden="true" />
              </div>
            ) : (
              <>
                {/* Os controles permanecem montados; só a visão ativa consulta/renderiza gráficos. */}
                {opcao.id === "geral" && (
                  <>
                    <div className="dashboard-kpis" aria-busy={kpis.isFetching}>
                      {kpis.isFetching && !kpis.isPending && (
                        <p className="dashboard-update" role="status">
                          Atualizando indicadores. Os valores anteriores permanecem visíveis até a consulta terminar.
                        </p>
                      )}
                      {kpis.isError && <ErroBanner erro={kpis.error} />}
                      {kpis.isPending && <KpiSkeleton />}
                      {kpis.data && (
                        kpis.data.atual.total === 0 ? (
                          <p className="vazio">Nenhum dado para os filtros selecionados.</p>
                        ) : (
                          <div className={kpis.isFetching ? "dashboard-kpi-data atualizando" : "dashboard-kpi-data"}>
                            <KpiCards dados={kpis.data} />
                          </div>
                        )
                      )}
                    </div>
                    <TimeSeriesChart filtros={filtros} ativo={visao === "geral"} />
                  </>
                )}

                {opcao.id === "perfil" && (
                  <div className="duas-colunas">
                    <AgePyramid filtros={filtros} ativo={visao === "perfil"} />
                    <TopCidChart filtros={filtros} ativo={visao === "perfil"} />
                  </div>
                )}

                {opcao.id === "municipios" && (
                  <>
                    <header className="dashboard-view-heading territorio-heading">
                      <h2>Apresentação dos municípios</h2>
                      <ViewTabs
                        id="territorio"
                        rotulo="Apresentação dos municípios"
                        opcoes={TERRITORIO}
                        valor={territorio}
                        onChange={setTerritorio}
                        compacta
                      />
                    </header>
                    {TERRITORIO.map((modo) => (
                      <section
                        key={modo.id}
                        id={`territorio-panel-${modo.id}`}
                        role="tabpanel"
                        aria-labelledby={`territorio-tab-${modo.id}`}
                        tabIndex={0}
                        hidden={territorio !== modo.id}
                        className="territorio-view"
                      >
                        {modo.id === "mapa" ? (
                          <MunicipiosMapa meta={meta.data} filtros={filtros} onChange={setFiltros}
                            ativo={visao === "municipios" && territorio === "mapa"} />
                        ) : (
                          <MunicipiosTabela meta={meta.data} filtros={filtros} onChange={setFiltros}
                            ativo={visao === "municipios" && territorio === "tabela"} />
                        )}
                      </section>
                    ))}
                  </>
                )}
              </>
            )}
          </section>
        ))}

        <footer className="dashboard-footer">
          <p>Secretaria Municipal de Saúde · Patos-PB</p>
          <p>Internações (AIH), não pacientes únicos. Fonte: SIH/SUS — DATASUS.<br />
            Atualização conforme o processamento da base, não em tempo real.</p>
        </footer>
      </main>
    </div>
  );
}
