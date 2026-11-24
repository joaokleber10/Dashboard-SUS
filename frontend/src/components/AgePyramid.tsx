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
import { buscarDemografia } from "../api";
import type { Filtros } from "../types";
import { ErroBanner } from "./Estados";

const nf = new Intl.NumberFormat("pt-BR");

export default function AgePyramid({ filtros }: { filtros: Filtros }) {
  const q = useQuery({
    queryKey: ["demografia", filtros],
    queryFn: () => buscarDemografia(filtros),
    placeholderData: keepPreviousData,
  });

  const { dados, limite, vazio, ignorado } = useMemo(() => {
    const faixas = q.data?.faixas ?? [];
    return {
      // Masculino negativo (esquerda) e feminino positivo (direita); faixa mais velha no topo.
      dados: [...faixas]
        .reverse()
        .map((f) => ({ faixa: f.faixa, Masculino: -f.M, Feminino: f.F })),
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
      {q.data && !vazio && (
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
                stroke="#e5e7eb"
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
              <Bar dataKey="Masculino" stackId="piramide" fill="#2563eb" />
              <Bar dataKey="Feminino" stackId="piramide" fill="#db2777" />
            </BarChart>
          </ResponsiveContainer>
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
