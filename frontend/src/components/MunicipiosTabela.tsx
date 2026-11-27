import { useEffect, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { buscarMunicipios } from "../api";
import type { Filtros, Meta, OrdemMunicipios } from "../types";
import { ErroBanner } from "./Estados";

const nf = new Intl.NumberFormat("pt-BR");
const nf1 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });
const brl = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0,
});

const COLUNAS: { id: OrdemMunicipios; nome: string; num: boolean }[] = [
  { id: "nome", nome: "Município", num: false },
  { id: "casos", nome: "Internações", num: true },
  { id: "obitos", nome: "Óbitos", num: true },
  { id: "taxa_mortalidade", nome: "Letalidade", num: true },
  { id: "permanencia_media", nome: "Perm. média (dias)", num: true },
  { id: "custo_total", nome: "Custo total", num: true },
];

interface Props {
  meta: Meta;
  filtros: Filtros;
  onChange: (f: Filtros) => void;
}

export default function MunicipiosTabela({ meta, filtros, onChange }: Props) {
  const [ordem, setOrdem] = useState<OrdemMunicipios>("casos");
  const [dir, setDir] = useState<"asc" | "desc">("desc");
  const [pagina, setPagina] = useState(1);
  const [busca, setBusca] = useState("");
  const [buscaAtual, setBuscaAtual] = useState("");
  const focoCodigo = meta.foco?.municipio_codigo;

  useEffect(() => {
    const t = setTimeout(() => setBuscaAtual(busca), 300);
    return () => clearTimeout(t);
  }, [busca]);
  useEffect(() => setPagina(1), [filtros, ordem, dir, buscaAtual]);

  const q = useQuery({
    queryKey: ["municipios", filtros, ordem, dir, pagina, buscaAtual],
    queryFn: () => buscarMunicipios(filtros, ordem, dir, pagina, buscaAtual),
    placeholderData: keepPreviousData,
  });
  const paginas = q.data
    ? Math.max(1, Math.ceil(q.data.total_municipios / q.data.por_pagina))
    : 1;

  const ordenar = (id: OrdemMunicipios) => {
    if (id === ordem) setDir(dir === "desc" ? "asc" : "desc");
    else {
      setOrdem(id);
      setDir(id === "nome" ? "asc" : "desc");
    }
  };

  return (
    <section className="bloco">
      <div className="bloco-topo">
        <h3>Municípios</h3>
        <input
          type="search"
          placeholder="Buscar município ou código"
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
        />
      </div>
      {q.isError && <ErroBanner erro={q.error} />}
      {q.isPending && <div className="skeleton alto" />}
      {q.data && q.data.itens.length === 0 && (
        <p className="vazio">Nenhum município para os filtros selecionados.</p>
      )}
      {q.data && q.data.itens.length > 0 && (
        <div
          className={q.isFetching ? "tabela-wrap atualizando" : "tabela-wrap"}
        >
          <table className="tabela">
            <thead>
              <tr>
                {COLUNAS.map((c) => (
                  <th
                    key={c.id}
                    className={c.num ? "num" : ""}
                    aria-sort={
                      c.id === ordem
                        ? dir === "asc"
                          ? "ascending"
                          : "descending"
                        : "none"
                    }
                  >
                    <button type="button" onClick={() => ordenar(c.id)}>
                      {c.nome}
                      {c.id === ordem ? (dir === "asc" ? " ▲" : " ▼") : ""}
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {q.data.itens.map((m) => (
                <tr
                  key={m.codigo ?? "ign"}
                  className={`${m.codigo === focoCodigo ? "foco" : ""}${m.codigo && m.codigo === filtros.municipio ? " ativo" : ""}`}
                >
                  <td>
                    {m.codigo && m.identificado ? (
                      <button
                        type="button"
                        className="link"
                        onClick={() =>
                          onChange({
                            ...filtros,
                            municipio:
                              filtros.municipio === m.codigo ? "" : m.codigo!,
                          })
                        }
                      >
                        {m.nome}
                      </button>
                    ) : (
                      m.nome
                    )}
                    {m.codigo === focoCodigo && (
                      <span className="selo">foco</span>
                    )}
                  </td>
                  <td className="num">{nf.format(m.casos)}</td>
                  <td className="num">{nf.format(m.obitos)}</td>
                  <td className="num">
                    {m.taxa_mortalidade == null
                      ? "—"
                      : `${nf1.format(m.taxa_mortalidade)}%`}
                  </td>
                  <td className="num">
                    {m.permanencia_media == null
                      ? "—"
                      : nf1.format(m.permanencia_media)}
                  </td>
                  <td className="num">
                    {m.custo_total == null ? "—" : brl.format(m.custo_total)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="paginacao">
            <button
              type="button"
              disabled={pagina <= 1}
              onClick={() => setPagina(pagina - 1)}
            >
              Anterior
            </button>
            <span>
              Página {pagina} de {paginas} ·{" "}
              {nf.format(q.data.total_municipios)} municípios
            </span>
            <button
              type="button"
              disabled={pagina >= paginas}
              onClick={() => setPagina(pagina + 1)}
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
