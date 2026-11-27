import type { Filtros, Meta } from "../../types";

export interface PriorityGroupsBarProps {
  meta: Meta;
  filtros: Filtros;
  onChange: (f: Filtros) => void;
}

function formatarIntervalo(inicio: string, fim: string): string {
  return inicio === fim ? inicio : `${inicio}–${fim}`;
}

export default function PriorityGroupsBar({
  meta,
  filtros,
  onChange,
}: PriorityGroupsBarProps) {
  const grupos = meta.grupos ?? [];
  if (grupos.length === 0) return null;

  const alternarGrupo = (id: string) => {
    const ativo = filtros.grupo_ids.includes(id);
    const proximo = ativo
      ? filtros.grupo_ids.filter((x) => x !== id)
      : [...filtros.grupo_ids, id];
    onChange({ ...filtros, grupo_ids: proximo });
  };

  return (
    <section
      className="bloco priority-groups-bar"
      aria-label="Grupos prioritários de doenças"
      style={{ padding: "12px 14px" }}
    >
      <div
        className="bloco-topo"
        style={{ marginBottom: 8, gap: 8, flexWrap: "wrap" }}
      >
        <h3 style={{ fontSize: "0.9rem" }}>Grupos prioritários (CID-10)</h3>
        {filtros.grupo_ids.length > 0 && (
          <button
            type="button"
            onClick={() => onChange({ ...filtros, grupo_ids: [] })}
            style={{ fontSize: "0.78rem", padding: "3px 8px" }}
          >
            Limpar grupos
          </button>
        )}
      </div>

      <div className="chips" style={{ gap: 8 }}>
        {grupos.map((g) => {
          const ativo = filtros.grupo_ids.includes(g.id);
          return (
            <button
              key={g.id}
              type="button"
              aria-pressed={ativo}
              className={ativo ? "chip ativo" : "chip"}
              onClick={() => alternarGrupo(g.id)}
              style={{
                background: ativo
                  ? "color-mix(in srgb, var(--azul) 14%, transparent)"
                  : "var(--superficie)",
                padding: "6px 12px",
                gap: 6,
              }}
            >
              <span style={{ fontWeight: ativo ? 600 : 500 }}>{g.nome}</span>
              <span
                style={{
                  fontSize: "0.75rem",
                  color: "var(--suave)",
                  fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                }}
              >
                {formatarIntervalo(g.inicio, g.fim)}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
