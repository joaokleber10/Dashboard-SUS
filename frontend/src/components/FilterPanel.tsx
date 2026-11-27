import { useEffect, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { buscarCid, buscarMapa } from "../api";
import type { Filtros, Meta, Opcao } from "../types";
import { filtrosPadrao, periodoCompleto, ultimoMes } from "../periodo";

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

/** Busca de subcategoria CID-10 por código ou nome; os escolhidos viram chips removíveis. */
function BuscaCid({
  filtros,
  onChange,
}: {
  filtros: Filtros;
  onChange: (f: Filtros) => void;
}) {
  const [texto, setTexto] = useState("");
  const [termo, setTermo] = useState("");
  useEffect(() => {
    const t = setTimeout(() => setTermo(texto.trim()), 250);
    return () => clearTimeout(t);
  }, [texto]);
  const q = useQuery({
    queryKey: ["cid-busca", filtros, termo],
    queryFn: () => buscarCid(filtros, termo),
    enabled: termo.length >= 2,
    placeholderData: keepPreviousData,
  });
  const add = (cid: string) => {
    if (!filtros.cid_codigos.includes(cid))
      onChange({ ...filtros, cid_codigos: [...filtros.cid_codigos, cid] });
    setTexto("");
  };
  return (
    <fieldset className="grupo busca-cid">
      <legend>Agravo específico (CID-10)</legend>
      <input
        type="search"
        placeholder="Ex.: I21 ou infarto"
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
      />
      {termo.length >= 2 &&
        q.data &&
        (q.data.itens.length === 0 ? (
          <small>Nada encontrado nos dados filtrados.</small>
        ) : (
          <ul>
            {q.data.itens.map((i) => (
              <li key={i.cid3}>
                <button type="button" onClick={() => add(i.cid3)}>
                  <strong>{i.cid3}</strong> {i.cid_nome ?? ""}{" "}
                  <small>({i.casos})</small>
                </button>
              </li>
            ))}
          </ul>
        ))}
      {filtros.cid_codigos.length > 0 && (
        <div className="chips">
          {filtros.cid_codigos.map((c) => (
            <button
              key={c}
              type="button"
              className="chip ativo"
              onClick={() =>
                onChange({
                  ...filtros,
                  cid_codigos: filtros.cid_codigos.filter((x) => x !== c),
                })
              }
            >
              {c} ✕
            </button>
          ))}
        </div>
      )}
    </fieldset>
  );
}

interface Props {
  meta: Meta;
  filtros: Filtros;
  onChange: (f: Filtros) => void;
}

export default function FilterPanel({ meta, filtros, onChange }: Props) {
  const set = <K extends keyof Filtros>(chave: K, valor: Filtros[K]) =>
    onChange({ ...filtros, [chave]: valor });
  const mes = ultimoMes(meta);
  const munis = useQuery({
    queryKey: ["mapa", filtros],
    queryFn: () => buscarMapa(filtros),
    placeholderData: keepPreviousData,
  });
  const opcoesMunicipio = (munis.data?.itens ?? [])
    .filter((m) => m.codigo && m.identificado)
    .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  const foco = meta.foco;

  return (
    <aside className="painel">
      <h2>Filtros</h2>

      <fieldset className="grupo">
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
        <label className="campo">
          Comparar com
          <select
            value={filtros.comparacao}
            onChange={(e) =>
              set("comparacao", e.target.value as Filtros["comparacao"])
            }
          >
            <option value="periodo_anterior">Período anterior (MoM)</option>
            <option value="ano_anterior">
              Mesmo período do ano anterior (YoY)
            </option>
          </select>
        </label>
      </fieldset>

      <CheckGroup
        titulo="Grupo de doenças (capítulo CID-10)"
        vertical
        opcoes={meta.capitulos.filter((c) => c.destaque)}
        valor={filtros.capitulo_ids}
        onChange={(v) => set("capitulo_ids", v)}
      />

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

      <label className="campo">
        Município
        <select
          value={filtros.municipio}
          onChange={(e) => set("municipio", e.target.value)}
        >
          <option value="">Todos</option>
          {foco &&
            !opcoesMunicipio.some(
              (m) => m.codigo === foco.municipio_codigo,
            ) && (
              <option value={foco.municipio_codigo}>
                {foco.municipio_nome ?? foco.municipio_codigo} (foco, sem casos
                no recorte)
              </option>
            )}
          {opcoesMunicipio.map((m) => (
            <option key={m.codigo} value={m.codigo!}>
              {m.nome}
              {m.codigo === foco?.municipio_codigo ? " ★" : ""}
            </option>
          ))}
        </select>
        {foco && filtros.municipio !== foco.municipio_codigo && (
          <button
            type="button"
            className="atalho-foco"
            onClick={() => set("municipio", foco.municipio_codigo)}
          >
            Ir para {foco.municipio_nome ?? "município em foco"}
          </button>
        )}
      </label>
      <label className="campo">
        Município refere-se a
        <select
          value={filtros.municipio_ref}
          onChange={(e) =>
            set("municipio_ref", e.target.value as Filtros["municipio_ref"])
          }
        >
          <option value="residencia">Residência do paciente</option>
          <option value="atendimento">Local do atendimento (hospital)</option>
        </select>
      </label>

      <BuscaCid filtros={filtros} onChange={onChange} />

      {meta.fontes_disponiveis.length > 1 && (
        <CheckGroup
          titulo="Fonte dos dados"
          vertical
          opcoes={meta.fontes_disponiveis.map((f) => ({
            id: f.id,
            nome: `${f.id === "SIH" ? "SIH/SUS (oficial)" : f.id} · ${f.casos.toLocaleString("pt-BR")}`,
          }))}
          valor={filtros.fontes}
          onChange={(v) => set("fontes", v)}
        />
      )}

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

      <button
        type="button"
        className="limpar"
        onClick={() => onChange(filtrosPadrao(meta))}
      >
        Restaurar filtros padrão
      </button>
    </aside>
  );
}
