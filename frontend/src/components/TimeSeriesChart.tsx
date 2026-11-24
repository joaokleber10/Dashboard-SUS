import { useMemo, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { buscarSerie } from "../api";
import type { Filtros } from "../types";
import { ErroBanner } from "./Estados";

const CORES = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2"];
const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
const rotuloMes = (m: string) => `${MESES[Number(m.slice(5, 7)) - 1]}/${m.slice(2, 4)}`;
const nf = new Intl.NumberFormat("pt-BR");

export default function TimeSeriesChart({ filtros }: { filtros: Filtros }) {
  const [agrupar, setAgrupar] = useState<"capitulo" | "total">("capitulo");
  // Sem capítulo selecionado seriam ~20 linhas ilegíveis: mostra só o total.
  const efetivo = filtros.capitulo_ids.length === 0 ? "total" : agrupar;

  const q = useQuery({
    queryKey: ["serie", filtros, efetivo],
    queryFn: () => buscarSerie(filtros, efetivo),
    placeholderData: keepPreviousData,
  });

  const dados = useMemo(() => {
    if (!q.data) return [];
    return q.data.meses.map((m) => {
      const linha: Record<string, string | number> = { ano_mes: m };
      q.data!.series.forEach((s) => {
        linha[s.id] = s.pontos.find((p) => p.ano_mes === m)?.casos ?? 0;
      });
      return linha;
    });
  }, [q.data]);

  return (
    <section className="bloco">
      <div className="bloco-topo">
        <h3>Evolução mensal de internações</h3>
        <div className="alternar">
          <button type="button" className={efetivo === "capitulo" ? "ativo" : ""}
                  disabled={filtros.capitulo_ids.length === 0} onClick={() => setAgrupar("capitulo")}>Por grupo</button>
          <button type="button" className={efetivo === "total" ? "ativo" : ""}
                  onClick={() => setAgrupar("total")}>Total</button>
        </div>
      </div>

      {q.isError && <ErroBanner erro={q.error} />}
      {q.isPending && <div className="skeleton alto" />}
      {q.data && q.data.series.length === 0 && <p className="vazio">Nenhum dado para os filtros selecionados.</p>}
      {q.data && q.data.series.length > 0 && (
        <div className={q.isFetching ? "grafico atualizando" : "grafico"}>
          <ResponsiveContainer width="100%" height={340}>
            <LineChart data={dados} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="ano_mes" tickFormatter={rotuloMes} />
              <YAxis tickFormatter={(v: number) => nf.format(v)} width={64} />
              <Tooltip labelFormatter={(m: string) => rotuloMes(m)}
                       formatter={(valor: number, nome: string) => [`${nf.format(valor)} internações`, nome]} />
              <Legend />
              {q.data.series.map((s, i) => (
                <Line key={s.id} type="monotone" dataKey={s.id} name={s.nome}
                      stroke={CORES[i % CORES.length]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
