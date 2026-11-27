import { useEffect, useState } from "react";
import ViewTabs, { type ViewOption } from "../common/ViewTabs";
import brasao from "../../Public/Icon/logo.png";

interface Props<T extends string> {
  opcoes: readonly ViewOption<T>[];
  valor: T;
  onChange: (valor: T) => void;
}

/** A mesma navegação vira uma faixa compacta no celular; o estado fica na página. */
export function Sidebar<T extends string>({ opcoes, valor, onChange }: Props<T>) {
  const [compacta, setCompacta] = useState(() =>
    typeof window !== "undefined" && window.matchMedia("(max-width: 900px)").matches,
  );

  useEffect(() => {
    const media = window.matchMedia("(max-width: 900px)");
    const atualizar = () => setCompacta(media.matches);
    atualizar();
    media.addEventListener("change", atualizar);
    return () => media.removeEventListener("change", atualizar);
  }, []);

  return (
    <aside className="sidebar" aria-label="Navegação do painel">
      <div className="sidebar-brand">
        <div className="sidebar-crest">
          <img src={brasao} alt="Brasão de Patos-PB" width={221} height={208} />
        </div>
        <div className="sidebar-brand-name">
          <span>Prefeitura Municipal</span>
          <strong>Patos<span className="sidebar-state"> · PB</span></strong>
          <small>Painel de saúde · SIH/SUS</small>
        </div>
      </div>

      <div className="sidebar-navigation">
        <span className="sidebar-section-label">Monitoramento</span>
        <ViewTabs
          id="dashboard"
          rotulo="Visões do painel"
          opcoes={opcoes}
          valor={valor}
          onChange={onChange}
          orientacao={compacta ? "horizontal" : "vertical"}
        />
      </div>

      <div className="sidebar-footer">
        <span>Secretaria Municipal de Saúde</span>
        <strong>Patos · Paraíba</strong>
        <small>Internações hospitalares</small>
      </div>
    </aside>
  );
}
