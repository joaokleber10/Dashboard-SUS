import { memo, useEffect, useMemo, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { buscarCid, buscarGruposDinamicos, buscarMapa, resolverCid } from "../../services/api";
import { filtrosPadrao, periodoCompleto, ultimoMes } from "../../services/periodo";
import type { Filtros, Meta, Opcao } from "../../types";
import { ErroBanner } from "../common/ErrorBanner";
import PriorityGroupsBar from "./PriorityGroupsBar";
import GroupSelect from "./GroupSelect";

interface CheckGroupProps {
  titulo: string;
  opcoes: Opcao[];
  valor: string[];
  onChange: (v: string[]) => void;
  vertical?: boolean;
}

function CheckGroup({ titulo, opcoes, valor, onChange, vertical }: CheckGroupProps) {
  const alternar = (id: string) =>
    onChange(valor.includes(id) ? valor.filter((x) => x !== id) : [...valor, id]);
  return (
    <fieldset className="grupo">
      <legend>{titulo}</legend>
      <div className={vertical ? "lista" : "chips"}>
        {opcoes.map((opcao) => (
          <label key={opcao.id} className={valor.includes(opcao.id) ? "chip ativo" : "chip"}>
            <input type="checkbox" checked={valor.includes(opcao.id)} onChange={() => alternar(opcao.id)} />
            {opcao.nome}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

/** Uma única entrada mantém a busca por nome e a resolução de códigos/blocos. */
function BuscaCid({ filtros, onChange }: { filtros: Filtros; onChange: (f: Filtros) => void }) {
  const [texto, setTexto] = useState("");
  const [termo, setTermo] = useState("");
  useEffect(() => {
    const timer = window.setTimeout(() => setTermo(texto.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [texto]);

  const termoAtual = texto.trim() === termo;
  const codigo = termo.toUpperCase();
  const pareceCodigo = /^[A-Z]\d{2}(?:\.?\d)?$/.test(codigo);
  const busca = useQuery({
    queryKey: ["cid-busca", filtros, termo],
    queryFn: () => buscarCid(filtros, termo),
    enabled: termo.length >= 2,
    placeholderData: keepPreviousData,
  });
  const resolucao = useQuery({
    queryKey: ["cid-resolver", codigo],
    queryFn: () => resolverCid(codigo),
    enabled: pareceCodigo,
    staleTime: 5 * 60 * 1000,
  });

  const limparBusca = () => {
    setTexto("");
    setTermo("");
  };
  const adicionar = (cid: string) => {
    if (!filtros.cid_codigos.includes(cid)) {
      onChange({ ...filtros, cid_codigos: [...filtros.cid_codigos, cid] });
    }
    limparBusca();
  };

  return (
    <fieldset className="grupo busca-cid">
      <legend>Diagnóstico específico (CID-10)</legend>
      <input
        type="search"
        className="cid-input"
        aria-label="Buscar diagnóstico CID-10 por código ou nome"
        placeholder="Ex.: I21 ou infarto"
        value={texto}
        onChange={(event) => setTexto(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && termoAtual && pareceCodigo && resolucao.data?.valido) {
            event.preventDefault();
            adicionar(resolucao.data.cid3 ?? codigo);
          }
        }}
      />
      <small className="nota">Busque por código ou nome; selecione um resultado para filtrar.</small>
      {termoAtual && termo.length >= 2 && (
        <>
          {busca.isFetching && <p className="nota" role="status">Buscando diagnósticos…</p>}
          {busca.isError && <ErroBanner erro={busca.error} />}
          {pareceCodigo && resolucao.isError && <ErroBanner erro={resolucao.error} />}
          {pareceCodigo && resolucao.data && (
            resolucao.data.valido ? (
              <div className="cid-resolved-bar">
                <span>
                  <strong>{resolucao.data.cid3 ?? codigo}</strong>
                  {resolucao.data.bloco && ` · ${resolucao.data.bloco.nome}`}
                </span>
                <div className="atalhos">
                  <button type="button" onClick={() => adicionar(resolucao.data.cid3 ?? codigo)}>
                    Filtrar CID {resolucao.data.cid3 ?? codigo}
                  </button>
                  {resolucao.data.bloco && (
                    <button type="button" onClick={() => {
                      const id = resolucao.data.bloco!.id;
                      if (!filtros.grupo_ids.includes(id)) {
                        onChange({ ...filtros, grupo_ids: [...filtros.grupo_ids, id] });
                      }
                      limparBusca();
                    }}>
                      Filtrar bloco {resolucao.data.bloco.inicio}–{resolucao.data.bloco.fim}
                    </button>
                  )}
                </div>
              </div>
            ) : <p className="nota">Código “{codigo}” não reconhecido.</p>
          )}
          {!busca.isPlaceholderData && busca.data && (
            busca.data.itens.length === 0 ? (
              <small>Nenhum diagnóstico encontrado nos dados filtrados.</small>
            ) : (
              <ul aria-label="Diagnósticos encontrados">
                {busca.data.itens.map((item) => (
                  <li key={item.cid3}>
                    <button type="button" onClick={() => adicionar(item.cid3)}>
                      <strong>{item.cid3}</strong> {item.cid_nome ?? ""}{" "}
                      <small>({item.casos.toLocaleString("pt-BR")} internações)</small>
                    </button>
                  </li>
                ))}
              </ul>
            )
          )}
        </>
      )}
      {filtros.cid_codigos.length > 0 && (
        <div className="chips">
          {filtros.cid_codigos.map((cid) => (
            <button key={cid} type="button" className="chip ativo" aria-label={`Remover CID ${cid}`} onClick={() =>
              onChange({ ...filtros, cid_codigos: filtros.cid_codigos.filter((x) => x !== cid) })
            }>
              {cid} ×
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

const FilterPanel = memo(function FilterPanel({ meta, filtros, onChange }: Props) {
  const [avancadosAbertos, setAvancadosAbertos] = useState(false);
  const set = <K extends keyof Filtros>(chave: K, valor: Filtros[K]) =>
    onChange({ ...filtros, [chave]: valor });
  const mes = ultimoMes(meta);
  const foco = meta.foco;
  const munis = useQuery({
    queryKey: ["mapa", filtros],
    queryFn: () => buscarMapa(filtros),
    placeholderData: keepPreviousData,
  });
  const opcoesMunicipio = (munis.data?.itens ?? [])
    .filter((m) => m.codigo && m.identificado)
    .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));

  // Selecionar um grupo não deve restringir as opções do próprio seletor.
  const filtrosParaGrupos = useMemo<Filtros>(() => ({
    ...filtros, grupo_ids: [], cid_codigos: [],
  }), [filtros]);
  const grupos = useQuery({
    queryKey: ["cid-grupos", filtrosParaGrupos],
    queryFn: () => buscarGruposDinamicos(filtrosParaGrupos),
    enabled: avancadosAbertos,
    placeholderData: keepPreviousData,
  });
  const selecoesAvancadas = filtros.capitulo_ids.length + filtros.grupo_ids.length +
    filtros.cid_codigos.length + filtros.faixas_etarias.length + filtros.sexos.length +
    filtros.carater.length + filtros.complexidade.length + filtros.fontes.length +
    Number(filtros.comparacao !== "nenhuma") + Number(filtros.municipio_ref !== "residencia");

  return (
    <section className="painel painel-compacto" aria-label="Filtros compartilhados do painel">
      <div className="painel-topo">
        <div>
          <h2>Recorte dos dados</h2>
          <p className="painel-descricao">Os mesmos filtros valem para as três visões.</p>
        </div>
        <button type="button" className="limpar-topo" onClick={() => onChange(filtrosPadrao(meta))}>
          Restaurar padrão
        </button>
      </div>

      <div className="filtros-basicos">
        <fieldset className="grupo grupo-periodo">
          <legend>Período de internação</legend>
          <div className="datas">
            <input type="date" aria-label="Data inicial de internação" value={filtros.data_inicio}
              min={meta.periodo.data_min ?? undefined} max={filtros.data_fim || meta.periodo.data_max || undefined}
              onChange={(event) => {
                if (event.currentTarget.validity.valid) set("data_inicio", event.target.value);
              }} />
            <span>até</span>
            <input type="date" aria-label="Data final de internação" value={filtros.data_fim}
              min={filtros.data_inicio || meta.periodo.data_min || undefined} max={meta.periodo.data_max ?? undefined}
              onChange={(event) => {
                if (event.currentTarget.validity.valid) set("data_fim", event.target.value);
              }} />
          </div>
          <div className="atalhos">
            <button type="button" onClick={() => onChange({ ...filtros, ...periodoCompleto(meta) })}>Período completo</button>
            {mes && <button type="button" onClick={() => onChange({ ...filtros, ...mes })}>Último mês</button>}
          </div>
        </fieldset>

        <div className={meta.ufs_disponiveis.length > 1 ? "filtros-localidade filtros-localidade--com-uf" : "filtros-localidade"}>
          {meta.ufs_disponiveis.length > 1 && (
            <label className="campo">UF
              <select value={filtros.uf} onChange={(event) => onChange({ ...filtros, uf: event.target.value, municipio: "" })}>
                <option value="">Todas</option>
                {meta.ufs.filter((uf) => meta.ufs_disponiveis.includes(uf.sigla)).map((uf) => (
                  <option key={uf.sigla} value={uf.sigla}>{uf.nome}</option>
                ))}
              </select>
            </label>
          )}
          <label className="campo">Município
            <select value={filtros.municipio} onChange={(event) => set("municipio", event.target.value)}>
              <option value="">Todos os municípios</option>
              {filtros.municipio && !opcoesMunicipio.some((m) => m.codigo === filtros.municipio) && (
                <option value={filtros.municipio}>
                  {filtros.municipio === foco?.municipio_codigo ? foco.municipio_nome ?? filtros.municipio : filtros.municipio} (selecionado)
                </option>
              )}
              {foco && filtros.municipio !== foco.municipio_codigo && !opcoesMunicipio.some((m) => m.codigo === foco.municipio_codigo) && (
                <option value={foco.municipio_codigo}>{foco.municipio_nome ?? foco.municipio_codigo} (foco, sem casos no recorte)</option>
              )}
              {opcoesMunicipio.map((municipio) => (
                <option key={municipio.codigo} value={municipio.codigo!}>
                  {municipio.nome}{municipio.codigo === foco?.municipio_codigo ? " (foco)" : ""}
                </option>
              ))}
            </select>
          </label>
          <p className="nota filtros-referencia">
            Por {filtros.municipio_ref === "residencia" ? "residência do paciente" : "local do atendimento"}.
            {foco && filtros.municipio !== foco.municipio_codigo && (
              <> <button type="button" className="atalho-foco" onClick={() => set("municipio", foco.municipio_codigo)}>
                Ir para {foco.municipio_nome ?? "município em foco"}
              </button></>
            )}
          </p>
          {munis.isError && <p className="nota" role="status">Não foi possível carregar a lista de municípios.</p>}
        </div>
      </div>

      <details className="filtros-avancados" onToggle={(event) => setAvancadosAbertos(event.currentTarget.open)}>
        <summary>
          <span>Mais filtros</span>
          <span className="filtros-avancados-resumo">
            Diagnósticos, perfil e atendimento{selecoesAvancadas > 0 ? ` · ${selecoesAvancadas} seleções` : ""}
          </span>
        </summary>
        <div className="filtros-avancados-conteudo">
          <div className="filtros-secao">
            <h3>Diagnósticos</h3>
            <details className="filtro-capitulos">
              <summary>Capítulos CID-10 <span>{filtros.capitulo_ids.length ? filtros.capitulo_ids.join(", ") : "Todos"}</span></summary>
              <div className="filtro-capitulos-lista">
                <CheckGroup titulo="Selecionar capítulos" vertical
                  opcoes={meta.capitulos.map((cap) => ({ id: cap.id, nome: `${cap.id} — ${cap.nome} (${cap.inicio}–${cap.fim})` }))}
                  valor={filtros.capitulo_ids} onChange={(ids) => set("capitulo_ids", ids)} />
              </div>
              <button type="button" onClick={() => set("capitulo_ids", [])}>Todos os capítulos</button>
            </details>
            <fieldset className="grupo">
              <legend>Grupo de doenças</legend>
              <GroupSelect grupos={grupos.data ?? []} selecionados={filtros.grupo_ids}
                onChange={(ids) => set("grupo_ids", ids)} carregando={grupos.isFetching} />
              {grupos.isError && <ErroBanner erro={grupos.error} />}
            </fieldset>
            {avancadosAbertos && <BuscaCid filtros={filtros} onChange={onChange} />}
          </div>

          <div className="filtros-secao">
            <h3>Perfil das internações</h3>
            <CheckGroup titulo="Faixa etária" opcoes={meta.faixas_etarias.map((faixa) => ({ id: faixa.id, nome: `${faixa.id} anos` }))}
              valor={filtros.faixas_etarias} onChange={(ids) => set("faixas_etarias", ids)} />
            <CheckGroup titulo="Sexo" opcoes={meta.sexos} valor={filtros.sexos} onChange={(ids) => set("sexos", ids)} />
            <CheckGroup titulo="Caráter do atendimento" opcoes={meta.carater_atendimento} valor={filtros.carater} onChange={(ids) => set("carater", ids)} />
            <CheckGroup titulo="Complexidade" opcoes={meta.complexidades.filter((c) => c.id !== "nao_informada")}
              valor={filtros.complexidade} onChange={(ids) => set("complexidade", ids)} />
          </div>

          <div className="filtros-secao filtros-secao--contexto">
            <h3>Comparação e origem</h3>
            <div className="filtros-contexto-grid">
              <label className="campo">Comparar com
                <select value={filtros.comparacao} onChange={(event) => set("comparacao", event.target.value as Filtros["comparacao"])}>
                  <option value="nenhuma">Não comparar</option>
                  <option value="periodo_anterior">Período anterior (MoM)</option>
                  <option value="ano_anterior">Mesmo período do ano anterior (YoY)</option>
                </select>
              </label>
              <label className="campo">Município refere-se a
                <select value={filtros.municipio_ref} onChange={(event) => set("municipio_ref", event.target.value as Filtros["municipio_ref"])}>
                  <option value="residencia">Residência do paciente</option>
                  <option value="atendimento">Local do atendimento (hospital)</option>
                </select>
              </label>
              {meta.fontes_disponiveis.length > 1 && (
                <CheckGroup titulo="Fonte dos dados" opcoes={meta.fontes_disponiveis.map((fonte) => ({
                  id: fonte.id,
                  nome: `${fonte.id === "SIH" ? "SIH/SUS (oficial)" : fonte.id} · ${fonte.casos.toLocaleString("pt-BR")}`,
                }))} valor={filtros.fontes} onChange={(ids) => set("fontes", ids)} />
              )}
            </div>
          </div>
          <div className="filtros-prioritarios">
            <PriorityGroupsBar meta={meta} filtros={filtros} onChange={onChange} />
          </div>
        </div>
      </details>
    </section>
  );
});

export default FilterPanel;
