import type { Meta } from "../../types";

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

interface DataInfoBarProps {
  meta: Meta;
  compacta?: boolean;
}

export function DataInfoBar({ meta, compacta = false }: DataInfoBarProps) {
  const ultimaAtualizacao = formatarAtualizacao(
    meta.periodo.ultima_atualizacao,
  );

  return (
    <div className={`data-info-bar${compacta ? " data-info-bar--compacta" : ""}`} role="status">
      <span>
        <strong>Base de dados:</strong>{" "}
        {meta.periodo.fonte || "SIH/SUS (RD — DATASUS)"}
      </span>
      <span className="data-info-sep" aria-hidden="true">
        •
      </span>
      <span>
        <strong>Competências:</strong>{" "}
        {formatarCompetencia(meta.periodo.competencia_min)} a{" "}
        {formatarCompetencia(meta.periodo.competencia_max)}
      </span>
      <span className="data-info-sep" aria-hidden="true">
        •
      </span>
      <span>
        <strong>UFs:</strong>{" "}
        {meta.ufs_disponiveis.length > 0
          ? meta.ufs_disponiveis.join(", ")
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
  );
}
// Barra com informacoes do periodo, fonte e quantidade de dados.
