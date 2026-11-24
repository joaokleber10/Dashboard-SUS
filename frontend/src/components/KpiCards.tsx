import type { KpisResp } from "../types";

const nf = new Intl.NumberFormat("pt-BR");
const nf1 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });
const nf2 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });
const brl = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0,
});

function Variacao({
  valor,
  unidade,
}: {
  valor: number | null | undefined;
  unidade: "%" | "p.p.";
}) {
  if (valor === null || valor === undefined) {
    return (
      <span
        className="variacao neutra"
        title="Sem dados no período de comparação"
      >
        —
      </span>
    );
  }
  // Convenção: alta de volume/mortalidade/permanência/custo = pressão no sistema (laranja); queda = verde.
  const classe = valor === 0 ? "neutra" : valor > 0 ? "alta" : "queda";
  const seta = valor === 0 ? "•" : valor > 0 ? "▲" : "▼";
  return (
    <span className={`variacao ${classe}`}>
      {seta} {nf2.format(Math.abs(valor))} {unidade}
    </span>
  );
}

interface CardProps {
  titulo: string;
  valor: string;
  extra?: string;
  variacao?: React.ReactNode;
  title?: string;
}

function Card({ titulo, valor, extra, variacao, title }: CardProps) {
  return (
    <div className="card" title={title}>
      <span className="card-titulo">{titulo}</span>
      <strong className="card-valor">{valor}</strong>
      <div className="card-rodape">
        {variacao}
        {extra && <small>{extra}</small>}
      </div>
    </div>
  );
}

export default function KpiCards({ dados }: { dados: KpisResp }) {
  const a = dados.atual;
  const v = dados.variacao_pct;
  const rotuloComp =
    dados.comparacao === "ano_anterior"
      ? "vs. ano anterior"
      : "vs. período anterior";

  return (
    <section className="cards">
      <Card
        titulo="Internações"
        valor={nf.format(a.total)}
        extra={`${nf2.format(a.proporcao_total_geral ?? 0)}% do total · ${rotuloComp}`}
        variacao={<Variacao valor={v?.total} unidade="%" />}
      />
      <Card
        titulo="Taxa de mortalidade hospitalar"
        valor={
          a.taxa_mortalidade === null
            ? "—"
            : `${nf2.format(a.taxa_mortalidade)}%`
        }
        extra={`${nf.format(a.obitos)} óbitos · ${rotuloComp}`}
        variacao={<Variacao valor={v?.taxa_mortalidade_pp} unidade="p.p." />}
      />
      <Card
        titulo="Permanência média"
        valor={
          a.permanencia_media === null
            ? "—"
            : `${nf1.format(a.permanencia_media)} dias`
        }
        extra={rotuloComp}
        variacao={<Variacao valor={v?.permanencia_media} unidade="%" />}
      />
      <Card
        titulo="Custo total (SUS)"
        valor={a.custo_total === null ? "—" : brl.format(a.custo_total)}
        extra={
          a.custo_medio === null
            ? rotuloComp
            : `Custo médio por internação (AIH): ${brl.format(a.custo_medio)} · ${rotuloComp}`
        }
        variacao={<Variacao valor={v?.custo_total} unidade="%" />}
        title="Valor total aprovado das AIHs no SIH/SUS (campo VAL_TOT — soma dos serviços hospitalares, profissionais e complementares)."
      />
      {a.municipios_atendidos !== undefined && (
        <Card
          titulo="Municípios atendidos"
          valor={nf.format(a.municipios_atendidos)}
          extra="Municípios de residência no recorte"
        />
      )}
    </section>
  );
}
