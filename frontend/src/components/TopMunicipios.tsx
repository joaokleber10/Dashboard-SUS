import { useEffect, useMemo, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { buscarTopMunicipios } from "../api";
import type { Filtros } from "../types";
import { ErroBanner } from "./Estados";

const FAV_KEY = "sus-municipios-favoritos";

const nf = new Intl.NumberFormat("pt-BR");
const nf2 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });
const brl = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0,
});

function lerFavoritos(): string[] {
  try {
    const raw = localStorage.getItem(FAV_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed)
      ? parsed.filter((x): x is string => typeof x === "string")
      : [];
  } catch {
    return [];
  }
}

interface Props {
  filtros: Filtros;
  onSelectMunicipio: (codigo: string) => void;
}

export default function TopMunicipios({ filtros, onSelectMunicipio }: Props) {
  const [favoritos, setFavoritos] = useState<string[]>(lerFavoritos);
  const [busca, setBusca] = useState("");
  const [buscaDebounced, setBuscaDebounced] = useState("");

  useEffect(() => {
    try {
      localStorage.setItem(FAV_KEY, JSON.stringify(favoritos));
    } catch {
      /* armazenamento indisponível */
    }
  }, [favoritos]);

  useEffect(() => {
    const id = window.setTimeout(() => setBuscaDebounced(busca.trim()), 250);
    return () => window.clearTimeout(id);
  }, [busca]);

  const toggleFavorito = (codigo: string) => {
    setFavoritos((prev) =>
      prev.includes(codigo)
        ? prev.filter((c) => c !== codigo)
        : [...prev, codigo],
    );
  };

  const q = useQuery({
    queryKey: ["top-municipios", filtros, buscaDebounced, favoritos],
    queryFn: () =>
      buscarTopMunicipios(filtros, {
        limite: 10,
        busca: buscaDebounced || undefined,
        favoritos: favoritos.length > 0 ? favoritos : undefined,
      }),
    placeholderData: keepPreviousData,
  });

  const favSet = useMemo(() => new Set(favoritos), [favoritos]);

  const itens = useMemo(() => {
    const lista = q.data?.itens ?? [];
    return [...lista].sort((a, b) => {
      const fa = favSet.has(a.codigo) || Boolean(a.favorito) ? 1 : 0;
      const fb = favSet.has(b.codigo) || Boolean(b.favorito) ? 1 : 0;
      return fb - fa;
    });
  }, [q.data, favSet]);

  return (
    <section className="bloco">
      <div className="bloco-topo municipios-topo">
        <div>
          <h3>Top 10 municípios (código IBGE e nome)</h3>
          {q.data && (
            <p className="bloco-subtitulo">
              {nf.format(q.data.total_municipios)} município
              {q.data.total_municipios === 1 ? "" : "s"} no recorte
              {favoritos.length > 0 &&
                ` · ${favoritos.length} favorito${favoritos.length === 1 ? "" : "s"} fixado${favoritos.length === 1 ? "" : "s"}`}
            </p>
          )}
        </div>

        <div className="municipios-busca">
          <input
            type="search"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Pesquisar município por nome ou código IBGE..."
            aria-label="Pesquisar município por nome ou código IBGE"
          />
          {busca && (
            <button
              type="button"
              className="municipios-busca-limpar"
              onClick={() => setBusca("")}
              title="Limpar busca"
              aria-label="Limpar busca"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {q.isError && <ErroBanner erro={q.error} />}
      {q.isPending && <div className="skeleton alto" />}

      {q.data && itens.length === 0 && (
        <p className="vazio">
          {buscaDebounced
            ? `Nenhum município encontrado para "${buscaDebounced}".`
            : "Nenhum dado para os filtros selecionados."}
        </p>
      )}

      {q.data && itens.length > 0 && (
        <div className={q.isFetching ? "grafico atualizando" : "grafico"}>
          <div className="municipios-tabela-wrap">
            <table className="municipios-table">
              <thead>
                <tr>
                  <th className="col-fav" aria-label="Favorito">
                    ★
                  </th>
                  <th>Código IBGE</th>
                  <th>Município</th>
                  <th className="col-num">Internações</th>
                  <th className="col-num">Óbitos</th>
                  <th className="col-num">Mortalidade</th>
                  <th className="col-num">Custo SUS</th>
                  <th className="col-acao">Filtro</th>
                </tr>
              </thead>
              <tbody>
                {itens.map((item) => {
                  const ehFav =
                    favSet.has(item.codigo) || Boolean(item.favorito);
                  const ehAtivo = filtros.municipio === item.codigo;
                  const rowClasses = [
                    "municipio-row",
                    ehFav ? "municipio-row--fav" : "",
                    ehAtivo ? "municipio-row--ativo" : "",
                  ]
                    .filter(Boolean)
                    .join(" ");

                  return (
                    <tr
                      key={item.codigo}
                      className={rowClasses}
                      onClick={() => onSelectMunicipio(item.codigo)}
                    >
                      <td className="col-fav">
                        <button
                          type="button"
                          className={ehFav ? "fav-btn ativo" : "fav-btn"}
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleFavorito(item.codigo);
                          }}
                          title={
                            ehFav
                              ? "Remover dos favoritos"
                              : "Fixar município no topo"
                          }
                          aria-label={
                            ehFav
                              ? `Remover ${item.nome} dos favoritos`
                              : `Favoritar ${item.nome}`
                          }
                          aria-pressed={ehFav}
                        >
                          {ehFav ? "★" : "☆"}
                        </button>
                      </td>
                      <td className="col-ibge">
                        <code>{item.codigo}</code>
                      </td>
                      <td className="col-nome">
                        <span>{item.nome}</span>
                      </td>
                      <td className="col-num">{nf.format(item.casos)}</td>
                      <td className="col-num">{nf.format(item.obitos)}</td>
                      <td className="col-num">
                        {item.taxa_mortalidade === null ||
                        item.taxa_mortalidade === undefined
                          ? "—"
                          : `${nf2.format(item.taxa_mortalidade)}%`}
                      </td>
                      <td className="col-num">
                        {item.custo_total === null ||
                        item.custo_total === undefined
                          ? "—"
                          : brl.format(item.custo_total)}
                      </td>
                      <td className="col-acao">
                        <button
                          type="button"
                          className={
                            ehAtivo
                              ? "municipio-filtro-btn ativo"
                              : "municipio-filtro-btn"
                          }
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectMunicipio(item.codigo);
                          }}
                        >
                          {ehAtivo ? "Ativo" : "Filtrar"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="nota">
            Clique em um município para filtrar o painel por município de
            residência (clique novamente para remover). Use ★ para fixar
            municípios no topo.
          </p>
        </div>
      )}
    </section>
  );
}
