import { urlExport } from "../api";
import type { Filtros } from "../types";

const nf = new Intl.NumberFormat("pt-BR");

interface Props { filtros: Filtros; total: number; limite: number }

export default function ExportButton({ filtros, total, limite }: Props) {
  const vazio = total === 0;
  return (
    <div className="barra-export">
      <a className={vazio ? "botao desativado" : "botao"} href={vazio ? undefined : urlExport(filtros)}
         download aria-disabled={vazio}>
        ⬇ Exportar CSV ({nf.format(Math.min(total, limite))} registros)
      </a>
      {total > limite && (
        <small className="nota">
          O recorte tem {nf.format(total)} registros; o arquivo traz só os primeiros {nf.format(limite)}.
          Refine os filtros para exportar o restante.
        </small>
      )}
    </div>
  );
}
