import type { Filtros, Meta, Opcao } from "../types";
import { filtrosPadrao, periodoCompleto, ultimoMes } from "../periodo";

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
        {opcoes.map((o) => (
          <label key={o.id} className={valor.includes(o.id) ? "chip ativo" : "chip"}>
            <input type="checkbox" checked={valor.includes(o.id)} onChange={() => alternar(o.id)} />
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

export default function FilterPanel({ meta, filtros, onChange }: Props) {
  const set = <K extends keyof Filtros>(chave: K, valor: Filtros[K]) => onChange({ ...filtros, [chave]: valor });
  const mes = ultimoMes(meta);

  return (
    <aside className="painel">
      <h2>Filtros</h2>

      <fieldset className="grupo">
        <legend>Período (data de internação)</legend>
        <div className="datas">
          <input type="date" value={filtros.data_inicio} min={meta.periodo.data_min ?? undefined}
                 max={filtros.data_fim || undefined} onChange={(e) => set("data_inicio", e.target.value)} />
          <span>até</span>
          <input type="date" value={filtros.data_fim} min={filtros.data_inicio || undefined}
                 max={meta.periodo.data_max ?? undefined} onChange={(e) => set("data_fim", e.target.value)} />
        </div>
        <div className="atalhos">
          <button type="button" onClick={() => onChange({ ...filtros, ...periodoCompleto(meta) })}>Período completo</button>
          {mes && <button type="button" onClick={() => onChange({ ...filtros, ...mes })}>Último mês</button>}
        </div>
        <label className="campo">
          Comparar com
          <select value={filtros.comparacao}
                  onChange={(e) => set("comparacao", e.target.value as Filtros["comparacao"])}>
            <option value="periodo_anterior">Período anterior (MoM)</option>
            <option value="ano_anterior">Mesmo período do ano anterior (YoY)</option>
          </select>
        </label>
      </fieldset>

      <CheckGroup titulo="Grupo de doenças (capítulo CID-10)" vertical
                  opcoes={meta.capitulos.filter((c) => c.destaque)}
                  valor={filtros.capitulo_ids} onChange={(v) => set("capitulo_ids", v)} />

      {meta.ufs_disponiveis.length > 1 && (
        <label className="campo">
          UF
          <select value={filtros.uf} onChange={(e) => set("uf", e.target.value)}>
            <option value="">Todas</option>
            {meta.ufs.filter((u) => meta.ufs_disponiveis.includes(u.sigla)).map((u) => (
              <option key={u.sigla} value={u.sigla}>{u.nome}</option>
            ))}
          </select>
        </label>
      )}

      <CheckGroup titulo="Faixa etária"
                  opcoes={meta.faixas_etarias.map((f) => ({ id: f.id, nome: `${f.id} anos` }))}
                  valor={filtros.faixas_etarias} onChange={(v) => set("faixas_etarias", v)} />
      <CheckGroup titulo="Sexo" opcoes={meta.sexos}
                  valor={filtros.sexos} onChange={(v) => set("sexos", v)} />
      <CheckGroup titulo="Caráter do atendimento" opcoes={meta.carater_atendimento}
                  valor={filtros.carater} onChange={(v) => set("carater", v)} />
      <CheckGroup titulo="Complexidade" opcoes={meta.complexidades.filter((c) => c.id !== "nao_informada")}
                  valor={filtros.complexidade} onChange={(v) => set("complexidade", v)} />

      <button type="button" className="limpar" onClick={() => onChange(filtrosPadrao(meta))}>
        Restaurar filtros padrão
      </button>
    </aside>
  );
}
