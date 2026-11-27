import { useId, useState } from "react";
import { urlExportarCsv } from "../../services/api";
import { periodoCompleto } from "../../services/periodo";
import type { Filtros, Meta } from "../../types";

export interface ActiveFiltersSummaryProps {
  meta: Meta;
  filtros: Filtros;
  onChange: (f: Filtros) => void;
}

interface Pill {
  chave: string;
  rotulo: string;
  aoRemover: () => void;
}

export default function ActiveFiltersSummary({
  meta,
  filtros,
  onChange,
}: ActiveFiltersSummaryProps) {
  const [mostrarTodos, setMostrarTodos] = useState(false);
  const listaId = useId();
  const completo = periodoCompleto(meta);
  const pills: Pill[] = [];

  const periodoAlterado =
    (filtros.data_inicio && filtros.data_inicio !== completo.data_inicio) ||
    (filtros.data_fim && filtros.data_fim !== completo.data_fim);

  if (periodoAlterado) {
    pills.push({
      chave: "periodo",
      rotulo: `Período: ${filtros.data_inicio || "…"} a ${filtros.data_fim || "…"}`,
      aoRemover: () => onChange({ ...filtros, ...completo }),
    });
  }

  if (filtros.uf) {
    const ufObj = meta.ufs.find((u) => u.sigla === filtros.uf);
    pills.push({
      chave: `uf:${filtros.uf}`,
      rotulo: `UF: ${ufObj ? `${ufObj.nome} (${ufObj.sigla})` : filtros.uf}`,
      aoRemover: () => onChange({ ...filtros, uf: "" }),
    });
  }

  if (filtros.municipio) {
    pills.push({
      chave: `mun:${filtros.municipio}`,
      rotulo: `Município: ${filtros.municipio === meta.foco?.municipio_codigo && meta.foco.municipio_nome ? meta.foco.municipio_nome : filtros.municipio}`,
      aoRemover: () => onChange({ ...filtros, municipio: "" }),
    });
  }

  if (filtros.municipio_ref === "atendimento") {
    pills.push({
      chave: "municipio-ref",
      rotulo: "Municípios por local do atendimento",
      aoRemover: () => onChange({ ...filtros, municipio_ref: "residencia" }),
    });
  }

  if (filtros.comparacao !== "nenhuma") {
    pills.push({
      chave: "comparacao",
      rotulo: filtros.comparacao === "periodo_anterior"
        ? "Comparação: período anterior"
        : "Comparação: ano anterior",
      aoRemover: () => onChange({ ...filtros, comparacao: "nenhuma" }),
    });
  }

  for (const capId of filtros.capitulo_ids) {
    const cap = meta.capitulos.find((c) => c.id === capId);
    pills.push({
      chave: `cap:${capId}`,
      rotulo: cap ? `Cap. ${cap.id}: ${cap.nome}` : `Cap. ${capId}`,
      aoRemover: () =>
        onChange({
          ...filtros,
          capitulo_ids: filtros.capitulo_ids.filter((x) => x !== capId),
        }),
    });
  }

  for (const grupoId of filtros.grupo_ids) {
    const grupo = meta.grupos?.find((g) => g.id === grupoId);
    pills.push({
      chave: `grp:${grupoId}`,
      rotulo: grupo ? `Grupo: ${grupo.nome}` : `Grupo: ${grupoId}`,
      aoRemover: () =>
        onChange({
          ...filtros,
          grupo_ids: filtros.grupo_ids.filter((x) => x !== grupoId),
        }),
    });
  }

  for (const cid of filtros.cid_codigos) {
    pills.push({
      chave: `cid:${cid}`,
      rotulo: `CID: ${cid}`,
      aoRemover: () =>
        onChange({
          ...filtros,
          cid_codigos: filtros.cid_codigos.filter((x) => x !== cid),
        }),
    });
  }

  for (const fonte of filtros.fontes) {
    pills.push({
      chave: `fonte:${fonte}`,
      rotulo: `Fonte: ${fonte}`,
      aoRemover: () =>
        onChange({ ...filtros, fontes: filtros.fontes.filter((x) => x !== fonte) }),
    });
  }

  for (const faixa of filtros.faixas_etarias) {
    pills.push({
      chave: `faixa:${faixa}`,
      rotulo: `Idade: ${faixa} anos`,
      aoRemover: () =>
        onChange({
          ...filtros,
          faixas_etarias: filtros.faixas_etarias.filter((x) => x !== faixa),
        }),
    });
  }

  for (const sexoId of filtros.sexos) {
    const sexo = meta.sexos.find((s) => s.id === sexoId);
    pills.push({
      chave: `sexo:${sexoId}`,
      rotulo: `Sexo: ${sexo ? sexo.nome : sexoId}`,
      aoRemover: () =>
        onChange({
          ...filtros,
          sexos: filtros.sexos.filter((x) => x !== sexoId),
        }),
    });
  }

  for (const caraterId of filtros.carater) {
    const car = meta.carater_atendimento.find((c) => c.id === caraterId);
    pills.push({
      chave: `carater:${caraterId}`,
      rotulo: `Caráter: ${car ? car.nome : caraterId}`,
      aoRemover: () =>
        onChange({
          ...filtros,
          carater: filtros.carater.filter((x) => x !== caraterId),
        }),
    });
  }

  for (const compId of filtros.complexidade) {
    const comp = meta.complexidades.find((c) => c.id === compId);
    pills.push({
      chave: `comp:${compId}`,
      rotulo: `Complexidade: ${comp ? comp.nome : compId}`,
      aoRemover: () =>
        onChange({
          ...filtros,
          complexidade: filtros.complexidade.filter((x) => x !== compId),
        }),
    });
  }

  const limparTodos = () => {
    onChange({
      ...filtros,
      ...completo,
      capitulo_ids: [],
      grupo_ids: [],
      cid_codigos: [],
      uf: "",
      municipio: "",
      municipio_ref: "residencia",
      comparacao: "nenhuma",
      fontes: [],
      faixas_etarias: [],
      sexos: [],
      carater: [],
      complexidade: [],
    });
  };

  const pillsVisiveis = mostrarTodos ? pills : pills.slice(0, 3);

  return (
    <section
      className="bloco active-filters-bar"
      aria-label="Filtros ativos"
      style={{
        padding: "10px 14px",
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 10,
      }}
    >
      <div
        className="chips"
        id={listaId}
        style={{ alignItems: "center", flex: "1 1 auto", minWidth: 0 }}
      >
        <span
          style={{
            fontSize: "0.8rem",
            fontWeight: 600,
            color: "var(--suave)",
            marginRight: 2,
          }}
        >
          Filtros ativos{pills.length > 0 ? ` (${pills.length})` : ""}:
        </span>
        {pills.length === 0 ? (
          <span style={{ fontSize: "0.82rem", color: "var(--suave)" }}>
            Nenhum filtro restritivo (todos os registros)
          </span>
        ) : (
          pillsVisiveis.map((pill) => (
            <span
              key={pill.chave}
              className="chip ativo"
              style={{ fontSize: "0.8rem", padding: "3px 8px" }}
            >
              <span>{pill.rotulo}</span>
              <button
                type="button"
                aria-label={`Remover filtro ${pill.rotulo}`}
                onClick={pill.aoRemover}
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
          ))
        )}
        {pills.length > 3 && (
          <button
            type="button"
            aria-expanded={mostrarTodos}
            aria-controls={listaId}
            onClick={() => setMostrarTodos(!mostrarTodos)}
          >
            {mostrarTodos ? "Recolher resumo" : `Ver mais ${pills.length - 3}`}
          </button>
        )}
      </div>

      <div
        className="active-filters-actions"
        style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}
      >
        {pills.length > 0 && (
          <button
            type="button"
            onClick={limparTodos}
            style={{ fontSize: "0.82rem", padding: "5px 10px" }}
          >
            Limpar
          </button>
        )}
        <a
          href={urlExportarCsv(filtros)}
          download
          className="btn-exportar-csv"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontSize: "0.82rem",
            fontWeight: 600,
            padding: "5px 12px",
            borderRadius: 6,
            border: "1px solid var(--acao-bg)",
            background: "var(--acao-bg)",
            color: "var(--acao-texto)",
            textDecoration: "none",
          }}
        >
          Exportar CSV
        </a>
      </div>
    </section>
  );
}
