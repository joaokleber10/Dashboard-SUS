import { useEffect } from "react";
import { Theme, ThemeToggle, salvarTema } from "../common/ThemeToggle";
import type { Meta } from "../../types";
import { DataInfoBar } from "./DataInfoBar";

interface HeaderProps {
  theme: Theme;
  onThemeChange: (theme: Theme) => void;
  titulo?: string;
  descricao?: string;
  meta?: Meta;
}

export function Header({
  theme,
  onThemeChange,
  titulo = "Monitoramento Epidemiológico — SUS",
  descricao = "Internações hospitalares (SIH/SUS) · foco inicial: doenças cardiorrespiratórias",
  meta,
}: HeaderProps) {
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    salvarTema(theme);
  }, [theme]);

  const handleThemeToggle = () => {
    onThemeChange(theme === "dark" ? "light" : "dark");
  };

  return (
    <header className="topo">
      <div className="topo-row">
        <div className="topo-contexto">
          <span className="topo-eyebrow">Gestão pública · Saúde</span>
          <h1>{titulo}</h1>
          <p>{descricao}</p>
        </div>
        <div className="topo-ferramentas">
          {meta ? <DataInfoBar meta={meta} compacta /> : (
            <div className="topo-meta-pendente">
              <strong>SIH/SUS · DATASUS</strong>
              <span>Metadados da base ainda indisponíveis</span>
            </div>
          )}
          <ThemeToggle theme={theme} onToggle={handleThemeToggle} />
        </div>
      </div>
    </header>
  );
}
// Cabecalho principal e controle visual do tema claro/escuro.
