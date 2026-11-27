import { useEffect, useId, useMemo, useRef, useState } from "react";
import type { GrupoDinamico } from "../../types";

export interface GroupSelectProps {
  grupos: GrupoDinamico[];
  selecionados: string[];
  onChange: (ids: string[]) => void;
  carregando?: boolean;
  placeholder?: string;
}

function normalizar(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function formatarIntervalo(inicio: string, fim: string): string {
  return inicio === fim ? inicio : `${inicio}–${fim}`;
}

export default function GroupSelect({
  grupos,
  selecionados,
  onChange,
  carregando = false,
  placeholder = "Todos os grupos CID-10",
}: GroupSelectProps) {
  const [aberto, setAberto] = useState(false);
  const [busca, setBusca] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const buscaRef = useRef<HTMLInputElement>(null);
  const listboxId = useId();

  // Fecha APENAS com Escape ou clique/toque fora do componente (nunca em re-render ou layout shift)
  useEffect(() => {
    if (!aberto) return;

    const onPointerDown = (e: PointerEvent) => {
      const target = e.target;
      if (
        containerRef.current &&
        target instanceof Node &&
        !containerRef.current.contains(target)
      ) {
        setAberto(false);
      }
    };

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setAberto(false);
      }
    };

    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [aberto]);

  useEffect(() => {
    if (aberto) {
      buscaRef.current?.focus();
    }
  }, [aberto]);

  const filtrados = useMemo(() => {
    const termo = normalizar(busca.trim());
    if (!termo) return grupos;
    return grupos.filter((g) => {
      const alvo = normalizar(`${g.nome} ${g.inicio} ${g.fim} ${g.id}`);
      return alvo.includes(termo);
    });
  }, [grupos, busca]);

  const alternar = (id: string) => {
    if (selecionados.includes(id)) {
      onChange(selecionados.filter((x) => x !== id));
    } else {
      onChange([...selecionados, id]);
    }
  };

  const rotuloBotao = useMemo(() => {
    if (selecionados.length === 0) return placeholder;
    if (selecionados.length === 1) {
      const encontrado = grupos.find((g) => g.id === selecionados[0]);
      return encontrado ? encontrado.nome : selecionados[0];
    }
    return `${selecionados.length} grupos selecionados`;
  }, [selecionados, grupos, placeholder]);

  return (
    <div
      ref={containerRef}
      className="group-select"
      style={{ position: "relative" }}
    >
      <button
        type="button"
        className="group-select-trigger"
        aria-haspopup="listbox"
        aria-expanded={aberto}
        aria-controls={listboxId}
        onClick={() => setAberto((v) => !v)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
          textAlign: "left",
          fontSize: "0.85rem",
        }}
      >
        <span
          style={{
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {rotuloBotao}
        </span>
        <span aria-hidden="true" style={{ fontSize: "0.75rem", opacity: 0.7 }}>
          {aberto ? "▲" : "▼"}
        </span>
      </button>

      {aberto && (
        <div
          className="group-select-menu"
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: "calc(100% + 4px)",
            zIndex: 30,
            background: "var(--superficie)",
            border: "1px solid var(--borda)",
            borderRadius: 8,
            boxShadow: "0 8px 24px rgba(0, 0, 0, 0.14)",
            padding: 8,
          }}
        >
          <div style={{ display: "flex", gap: 6, marginBottom: 6 }}>
            <input
              ref={buscaRef}
              type="search"
              className="group-select-busca"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              placeholder="Buscar grupo ou CID..."
              aria-label="Buscar grupo de doenças CID-10"
              style={{
                flex: 1,
                minWidth: 0,
                padding: "6px 8px",
                fontSize: "0.82rem",
                border: "1px solid var(--borda)",
                borderRadius: 6,
                background: "var(--superficie)",
                color: "var(--texto)",
              }}
            />
            {selecionados.length > 0 && (
              <button
                type="button"
                onClick={() => onChange([])}
                title="Limpar seleção de grupos"
                style={{ fontSize: "0.75rem", padding: "4px 8px" }}
              >
                Limpar
              </button>
            )}
          </div>

          <div
            id={listboxId}
            role="listbox"
            aria-multiselectable="true"
            className="group-select-lista"
            style={{
              maxHeight: 240,
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: 2,
            }}
          >
            {carregando && grupos.length === 0 ? (
              <div
                style={{
                  padding: "10px 8px",
                  fontSize: "0.82rem",
                  color: "var(--suave)",
                }}
              >
                Carregando grupos…
              </div>
            ) : filtrados.length === 0 ? (
              <div
                style={{
                  padding: "10px 8px",
                  fontSize: "0.82rem",
                  color: "var(--suave)",
                }}
              >
                Nenhum grupo encontrado.
              </div>
            ) : (
              filtrados.map((g) => {
                const ativo = selecionados.includes(g.id);
                return (
                  <button
                    key={g.id}
                    type="button"
                    role="option"
                    aria-selected={ativo}
                    className={
                      ativo
                        ? "group-select-opcao ativo"
                        : "group-select-opcao"
                    }
                    onClick={() => alternar(g.id)}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      justifyContent: "space-between",
                      gap: 8,
                      width: "100%",
                      textAlign: "left",
                      padding: "6px 8px",
                      fontSize: "0.82rem",
                      border: ativo
                        ? "1px solid var(--azul)"
                        : "1px solid transparent",
                      background: ativo
                        ? "color-mix(in srgb, var(--azul) 12%, transparent)"
                        : "transparent",
                      borderRadius: 6,
                    }}
                  >
                    <span style={{ display: "flex", gap: 6, minWidth: 0 }}>
                      <input
                        type="checkbox"
                        checked={ativo}
                        readOnly
                        tabIndex={-1}
                        style={{
                          marginTop: 2,
                          accentColor: "var(--azul)",
                          pointerEvents: "none",
                        }}
                      />
                      <span>
                        <span style={{ fontWeight: ativo ? 600 : 400 }}>
                          {g.nome}
                        </span>{" "}
                        <span
                          style={{ color: "var(--suave)", fontSize: "0.78rem" }}
                        >
                          ({formatarIntervalo(g.inicio, g.fim)})
                        </span>
                      </span>
                    </span>
                    <span
                      style={{
                        color: "var(--suave)",
                        fontSize: "0.78rem",
                        whiteSpace: "nowrap",
                        fontVariantNumeric: "tabular-nums",
                      }}
                    >
                      {g.internacoes.toLocaleString("pt-BR")}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
