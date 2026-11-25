import { memo, useEffect, useMemo, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { buscarGruposDinamicos, resolverCid } from "../api";
import { filtrosPadrao, periodoCompleto, ultimoMes } from "../periodo";
import type { Filtros, Meta, Opcao } from "../types";
import GroupSelect from "./GroupSelect";

interface CheckGroupProps {
  titulo: string;
  opcoes: Opcao[];
  valor: string[];
  onChange: (v: string[]) => void;
  vertical?: boolean;
}

function CheckGroup({
  titulo,
  opcoes,
  valor,
  onChange,
  vertical,
}: CheckGroupProps) {
  const alternar = (id: string) =>
    onChange(
      valor.includes(id) ? valor.filter((x) => x !== id) : [...valor, id],
    );
  return (
    <fieldset className="grupo">
      <legend>{titulo}</legend>
      <div className={vertical ? "lista" : "chips"}>
        {opcoes.map((o) => (
          <label
            key={o.id}
            className={valor.includes(o.id) ? "chip ativo" : "chip"}
          >
            <input
              type="checkbox"
              checked={valor.includes(o.id)}
              onChange={() => alternar(o.id)}
            />
            {o.nome}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

interface Props {
  meta: Meta;
  filtros: Filtros;
  onChange: (f: Filtros) => void;
}

const FilterPanel = memo(function FilterPanel({
  meta,
  filtros,
  onChange,
}: Props) {
  const set = <K extends keyof Filtros>(chave: K, valor: Filtros[K]) =>
    onChange({ ...filtros, [chave]: valor });
  const mes = ultimoMes(meta);

  // Exclui grupo_ids e cid_codigos para que selecionar um grupo nunca recarregue a lista do dropdown
  const filtrosParaGrupos = useMemo<Filtros>(
    () => ({
      ...filtros,
      grupo_ids: [],
      cid_codigos: [],
    }),
    [
      filtros.capitulo_ids,
      filtros.uf,
      filtros.municipio,
      filtros.data_inicio,
      filtros.data_fim,
      filtros.faixas_etarias,
      filtros.sexos,
      filtros.carater,
      filtros.complexidade,
      filtros.comparacao,
    ],
  );

  const gruposQuery = useQuery({
    queryKey: [
      "cid-grupos",
      filtros.capitulo_ids,
      filtros.uf,
      filtros.municipio,
      filtros.data_inicio,
      filtros.data_fim,
      filtros.faixas_etarias,
      filtros.sexos,
      filtros.carater,
      filtros.complexidade,
    ],
    queryFn: () => buscarGruposDinamicos(filtrosParaGrupos),
    placeholderData: keepPreviousData,
  });

  // Busca/resolução de código CID-10 com debounce
  const [cidInput, setCidInput] = useState("");
  const [cidDebounced, setCidDebounced] = useState("");

  useEffect(() => {
    const limpo = cidInput.trim().toUpperCase();
    const timer = window.setTimeout(() => setCidDebounced(limpo), 300);
    return () => window.clearTimeout(timer);
  }, [cidInput]);

  const cidQuery = useQuery({
    queryKey: ["cid-resolver", cidDebounced],
    queryFn: () => resolverCid(cidDebounced),
    enabled: cidDebounced.length >= 3,
    staleTime: 5 * 60 * 1000,
  });

  const adicionarCid = (codigo: string) => {
    const norm = codigo.trim().toUpperCase();
    if (!norm) return;
    if (!filtros.cid_codigos.includes(norm)) {
      set("cid_codigos", [...filtros.cid_codigos, norm]);
    }
    setCidInput("");
    setCidDebounced("");
  };

  const removerCid = (codigo: string) => {
    set(
      "cid_codigos",
      filtros.cid_codigos.filter((c) => c !== codigo),
    );
  };

  const filtrarPorBloco = (blocoId: string) => {
    if (!filtros.grupo_ids.includes(blocoId)) {
      set("grupo_ids", [...filtros.grupo_ids, blocoId]);
    }
    setCidInput("");
    setCidDebounced("");
  };

  return (
    <section className="painel painel-horizontal" aria-label="Filtros epidemiológicos">
      <div className="painel-topo">
        <h2>Filtros Epidemiológicos</h2>
        <button
          type="button"
          className="limpar-topo"
          onClick={() => onChange(filtrosPadrao(meta))}
        >
          Restaurar filtros padrão
        </button>
      </div>

      <div className="painel-grid-primario">
        <fieldset className="grupo grupo-periodo">
          <legend>Período (data de internação)</legend>
          <div className="datas">
            <input
              type="date"
              value={filtros.data_inicio}
              min={meta.periodo.data_min ?? undefined}
              max={filtros.data_fim || undefined}
              onChange={(e) => set("data_inicio", e.target.value)}
            />
            <span>até</span>
            <input
              type="date"
              value={filtros.data_fim}
              min={filtros.data_inicio || undefined}
              max={meta.periodo.data_max ?? undefined}
              onChange={(e) => set("data_fim", e.target.value)}
            />
          </div>
          <div className="atalhos">
            <button
              type="button"
              onClick={() => onChange({ ...filtros, ...periodoCompleto(meta) })}
            >
              Período completo
            </button>
            {mes && (
              <button
                type="button"
                onClick={() => onChange({ ...filtros, ...mes })}
              >
                Último mês
              </button>
            )}
          </div>
        </fieldset>

        <div className="grupo">
          <label className="campo">
            Comparar com
            <select
              value={filtros.comparacao}
              onChange={(e) =>
                set("comparacao", e.target.value as Filtros["comparacao"])
              }
            >
              <option value="nenhuma">Não comparar</option>
              <option value="periodo_anterior">Período anterior (MoM)</option>
              <option value="ano_anterior">
                Mesmo período do ano anterior (YoY)
              </option>
            </select>
          </label>
          {meta.ufs_disponiveis.length > 1 && (
            <label className="campo">
              UF
              <select
                value={filtros.uf}
                onChange={(e) => set("uf", e.target.value)}
              >
                <option value="">Todas</option>
                {meta.ufs
                  .filter((u) => meta.ufs_disponiveis.includes(u.sigla))
                  .map((u) => (
                    <option key={u.sigla} value={u.sigla}>
                      {u.nome}
                    </option>
                  ))}
              </select>
            </label>
          )}
        </div>

        <div className="grupo">
          <label className="campo" htmlFor="filter-capitulo">
            Capítulo CID-10
            <select
              id="filter-capitulo"
              value={filtros.capitulo_ids[0] ?? ""}
              onChange={(e) =>
                set("capitulo_ids", e.target.value ? [e.target.value] : [])
              }
            >
              <option value="">Todos os capítulos</option>
              {meta.capitulos.map((cap) => (
                <option key={cap.id} value={cap.id}>
                  {cap.destaque ? "★ " : ""}
                  {cap.id} — {cap.nome} ({cap.inicio}–{cap.fim})
                </option>
              ))}
            </select>
          </label>
        </div>

        <fieldset className="grupo">
          <legend>Grupo de doenças (dinâmico por CID-10)</legend>
          <GroupSelect
            grupos={gruposQuery.data ?? []}
            selecionados={filtros.grupo_ids}
            onChange={(ids) => set("grupo_ids", ids)}
            carregando={gruposQuery.isPending}
          />
        </fieldset>

        <fieldset className="grupo">
          <legend>Código CID-10</legend>
          <div style={{ display: "flex", gap: 6 }}>
            <input
              type="text"
              value={cidInput}
              onChange={(e) => setCidInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && cidQuery.data?.valido) {
                  e.preventDefault();
                  adicionarCid(cidQuery.data.cid3 ?? cidDebounced);
                }
              }}
              placeholder="Ex.: I21, J18, O80"
              aria-label="Código CID-10"
              className="cid-input"
            />
          </div>

          {cidDebounced.length >= 3 && cidQuery.isFetching && !cidQuery.data && (
            <p className="nota">Consultando CID-10…</p>
          )}

          {cidDebounced.length >= 3 && cidQuery.data && (
            <div className="cid-resolved-bar">
              {cidQuery.data.valido ? (
                <>
                  <div>
                    <strong>{cidQuery.data.cid3 ?? cidDebounced}</strong>
                    {cidQuery.data.bloco && (
                      <div>
                        Grupo: {cidQuery.data.bloco.nome} (
                        {cidQuery.data.bloco.inicio}–{cidQuery.data.bloco.fim})
                      </div>
                    )}
                    {cidQuery.data.grupo_prioritario && (
                      <div style={{ color: "var(--azul)" }}>
                        Prioritário: {cidQuery.data.grupo_prioritario.nome}
                      </div>
                    )}
                    {cidQuery.data.capitulo && (
                      <div style={{ color: "var(--suave)" }}>
                        Cap. {cidQuery.data.capitulo.id}:{" "}
                        {cidQuery.data.capitulo.nome}
                      </div>
                    )}
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    <button
                      type="button"
                      onClick={() =>
                        adicionarCid(cidQuery.data.cid3 ?? cidDebounced)
                      }
                      style={{ fontSize: "0.78rem", padding: "4px 8px" }}
                    >
                      + Filtrar CID {cidQuery.data.cid3 ?? cidDebounced}
                    </button>
                    {cidQuery.data.bloco && (
                      <button
                        type="button"
                        onClick={() => filtrarPorBloco(cidQuery.data.bloco!.id)}
                        style={{ fontSize: "0.78rem", padding: "4px 8px" }}
                      >
                        + Filtrar bloco ({cidQuery.data.bloco.inicio}–
                        {cidQuery.data.bloco.fim})
                      </button>
                    )}
                  </div>
                </>
              ) : (
                <span style={{ color: "var(--laranja)" }}>
                  Código CID-10 “{cidDebounced}” não reconhecido.
                </span>
              )}
            </div>
          )}

          {filtros.cid_codigos.length > 0 && (
            <div className="chips" style={{ marginTop: 8 }}>
              {filtros.cid_codigos.map((cod) => (
                <span key={cod} className="chip ativo">
                  {cod}
                  <button
                    type="button"
                    aria-label={`Remover CID ${cod}`}
                    onClick={() => removerCid(cod)}
                    style={{
                      border: 0,
                      background: "transparent",
                      padding: "0 2px",
                      lineHeight: 1,
                      fontWeight: 700,
                    }}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </fieldset>
      </div>

      <div className="painel-grid-chips">
        <CheckGroup
          titulo="Faixa etária"
          opcoes={meta.faixas_etarias.map((f) => ({
            id: f.id,
            nome: `${f.id} anos`,
          }))}
          valor={filtros.faixas_etarias}
          onChange={(v) => set("faixas_etarias", v)}
        />
        <CheckGroup
          titulo="Sexo"
          opcoes={meta.sexos}
          valor={filtros.sexos}
          onChange={(v) => set("sexos", v)}
        />
        <CheckGroup
          titulo="Caráter do atendimento"
          opcoes={meta.carater_atendimento}
          valor={filtros.carater}
          onChange={(v) => set("carater", v)}
        />
        <CheckGroup
          titulo="Complexidade"
          opcoes={meta.complexidades.filter((c) => c.id !== "nao_informada")}
          valor={filtros.complexidade}
          onChange={(v) => set("complexidade", v)}
        />
      </div>
    </section>
  );
});

export default FilterPanel;
