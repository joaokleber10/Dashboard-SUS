import type { KeyboardEvent } from "react";

export interface ViewOption<T extends string> {
  id: T;
  nome: string;
}

interface Props<T extends string> {
  id: string;
  rotulo: string;
  opcoes: readonly ViewOption<T>[];
  valor: T;
  onChange: (valor: T) => void;
  compacta?: boolean;
  orientacao?: "horizontal" | "vertical";
}

/** As setas alternam e focam abas; Tab mantém a ordem dos controles da página. */
export default function ViewTabs<T extends string>({
  id,
  rotulo,
  opcoes,
  valor,
  onChange,
  compacta = false,
  orientacao = "horizontal",
}: Props<T>) {
  const navegar = (event: KeyboardEvent<HTMLButtonElement>, indice: number) => {
    let destino: number;
    switch (event.key) {
      case "ArrowRight":
        if (orientacao !== "horizontal") return;
        destino = (indice + 1) % opcoes.length;
        break;
      case "ArrowDown":
        if (orientacao !== "vertical") return;
        destino = (indice + 1) % opcoes.length;
        break;
      case "ArrowLeft":
        if (orientacao !== "horizontal") return;
        destino = (indice - 1 + opcoes.length) % opcoes.length;
        break;
      case "ArrowUp":
        if (orientacao !== "vertical") return;
        destino = (indice - 1 + opcoes.length) % opcoes.length;
        break;
      case "Home":
        destino = 0;
        break;
      case "End":
        destino = opcoes.length - 1;
        break;
      default:
        return;
    }
    event.preventDefault();
    onChange(opcoes[destino].id);
    const abas = event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>(
      '[role="tab"]',
    );
    abas?.[destino]?.focus();
  };

  return (
    <div
      role="tablist"
      aria-label={rotulo}
      aria-orientation={orientacao}
      className={`view-tabs${compacta ? " view-tabs--compacta" : ""}${orientacao === "vertical" ? " view-tabs--vertical" : ""}`}
    >
      {opcoes.map((opcao, indice) => (
        <button
          key={opcao.id}
          type="button"
          role="tab"
          id={`${id}-tab-${opcao.id}`}
          aria-controls={`${id}-panel-${opcao.id}`}
          aria-selected={valor === opcao.id}
          tabIndex={valor === opcao.id ? 0 : -1}
          className={valor === opcao.id ? "view-tab ativo" : "view-tab"}
          onClick={() => onChange(opcao.id)}
          onKeyDown={(event) => navegar(event, indice)}
        >
          {opcao.nome}
        </button>
      ))}
    </div>
  );
}
