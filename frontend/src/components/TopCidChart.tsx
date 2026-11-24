import { keepPreviousData, useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { buscarTopCid } from "../api";
import type { Filtros, ItemCid } from "../types";
import { ErroBanner } from "./Estados";

const nf = new Intl.NumberFormat("pt-BR");
const nf2 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });

function DicaCid({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: ItemCid }[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const i = payload[0].payload;
  return (
    <div className="dica">
      <strong>{i.cid3}</strong>
      {i.grupo_nome && <span className="dica-grupo">{i.grupo_nome}</span>}
      <span>{i.capitulo_nome}</span>
      <br />
      <span>
        {nf.format(i.casos)} internações ({nf2.format(i.percentual ?? 0)}% do
        recorte)
      </span>
      <br />
      <span>{nf.format(i.obitos)} óbitos</span>
    </div>
  );
}

export default function TopCidChart({ filtros }: { filtros: Filtros }) {
  const q = useQuery({
    queryKey: ["top-cid", filtros],
    queryFn: () => buscarTopCid(filtros, 10),
    placeholderData: keepPreviousData,
  });

  return (
    <section className="bloco">
      <div className="bloco-topo">
        <h3>Top 10 agravos (CID-10, 3 caracteres)</h3>
      </div>
      {q.isError && <ErroBanner erro={q.error} />}
      {q.isPending && <div className="skeleton alto" />}
      {q.data && q.data.itens.length === 0 && (
        <p className="vazio">Nenhum dado para os filtros selecionados.</p>
      )}
      {q.data && q.data.itens.length > 0 && (
        <div className={q.isFetching ? "grafico atualizando" : "grafico"}>
          <ResponsiveContainer width="100%" height={340}>
            <BarChart
              data={q.data.itens}
              layout="vertical"
              margin={{ top: 8, right: 24, left: 0, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--borda)"
                horizontal={false}
              />
              <XAxis
                type="number"
                tickFormatter={(v: number) => nf.format(v)}
              />
              <YAxis type="category" dataKey="cid3" width={48} />
              <Tooltip content={<DicaCid />} />
              <Bar
                dataKey="casos"
                name="Internações"
                fill="#0891b2"
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
          <p className="nota">
            Passe o mouse sobre a barra para ver o grupo, o capítulo, a
            participação e os óbitos.
          </p>
        </div>
      )}
    </section>
  );
}
