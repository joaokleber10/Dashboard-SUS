import { useMemo } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { buscarDemografia } from "../../services/api";
import type { Filtros } from "../../types";
import { ErroBanner } from "../common/ErrorBanner";

const nf = new Intl.NumberFormat("pt-BR");
const nf1 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });

export default function AgePyramid({ filtros, ativo = true }: { filtros: Filtros; ativo?: boolean }) {
  const q = useQuery({
    queryKey: ["demografia", filtros],
    queryFn: () => buscarDemografia(filtros),
    enabled: ativo,
    placeholderData: keepPreviousData,
  });

  const { dados, resumo, limite, vazio, ignorado } = useMemo(() => {
    const faixas = q.data?.faixas ?? [];
    const totalGeral = faixas.reduce((soma, f) => soma + f.total, 0);
    return {
      // Masculino negativo (esquerda) e feminino positivo (direita); faixa mais velha no topo.
      dados: [...faixas]
        .reverse()
        .map((f) => ({ faixa: f.faixa, Masculino: -f.M, Feminino: f.F })),
      resumo: faixas.map((f) => ({
        faixa: f.faixa,
        total: f.total,
        pct: totalGeral > 0 ? (f.total / totalGeral) * 100 : 0,
      })),
      limite: Math.max(1, ...faixas.flatMap((f) => [f.M, f.F])),
      vazio: faixas.every((f) => f.total === 0),
      ignorado: faixas.reduce((soma, f) => soma + f.I, 0),
    };
  }, [q.data]);

  return (
    <section className="bloco">
      <div className="bloco-topo">
        <h3>Pirâmide etária (faixa etária × sexo)</h3>
      </div>
      {q.isError && <ErroBanner erro={q.error} />}
      {q.isPending && <div className="skeleton alto" />}
      {q.data && vazio && (
        <p className="vazio">Nenhum dado para os filtros selecionados.</p>
      )}
      {ativo && q.data && !vazio && (
        <div className={q.isFetching ? "grafico atualizando" : "grafico"}>
          <ResponsiveContainer width="100%" height={340}>
            <BarChart
              data={dados}
              layout="vertical"
              stackOffset="sign"
              margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--borda)"
                horizontal={false}
              />
              <XAxis
                type="number"
                domain={[-limite, limite]}
                tickFormatter={(v: number) => nf.format(Math.abs(v))}
              />
              <YAxis type="category" dataKey="faixa" width={56} />
              <Tooltip
                formatter={(valor: number, nome: string) => [
                  nf.format(Math.abs(valor)),
                  nome,
                ]}
              />
              <Legend />
              <Bar dataKey="Masculino" stackId="piramide" fill="var(--chart-primary)" />
              <Bar dataKey="Feminino" stackId="piramide" fill="var(--chart-secondary)" />
            </BarChart>
          </ResponsiveContainer>

          <div className="age-summary">
            <span className="age-summary-titulo">
              Distribuição por faixa etária
            </span>
            <div className="age-summary-grid">
              {resumo.map((r) => (
                <div key={r.faixa} className="age-summary-item">
                  <span className="age-summary-faixa">{r.faixa}</span>
                  <strong className="age-summary-pct">
                    {nf1.format(r.pct)}%
                  </strong>
                  <small className="age-summary-total">
                    {nf.format(r.total)}
                  </small>
                </div>
              ))}
            </div>
          </div>

          {(ignorado > 0 || (q.data?.sem_faixa ?? 0) > 0) && (
            <p className="nota">
              Não exibidos: {nf.format(ignorado)} com sexo ignorado e{" "}
              {nf.format(q.data?.sem_faixa ?? 0)} sem idade válida.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
