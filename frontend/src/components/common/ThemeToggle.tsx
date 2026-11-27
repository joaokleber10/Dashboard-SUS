export type Theme = "light" | "dark";

const THEME_KEY = "sus-theme";

export function temaInicial(): Theme {
  try {
    const salvo = localStorage.getItem(THEME_KEY);
    if (salvo === "light" || salvo === "dark") return salvo;
  } catch {
    /* armazenamento indisponível */
  }
  if (
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-color-scheme: dark)").matches
  ) {
    return "dark";
  }
  return "light";
}

export function salvarTema(tema: Theme): void {
  try {
    localStorage.setItem(THEME_KEY, tema);
  } catch {
    /* armazenamento indisponível */
  }
}

interface ThemeToggleProps {
  theme: Theme;
  onToggle: () => void;
}

export function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={onToggle}
      aria-label={
        theme === "dark" ? "Ativar tema claro" : "Ativar tema escuro"
      }
      title={
        theme === "dark"
          ? "Mudar para tema claro"
          : "Mudar para tema escuro"
      }
    >
      <span className="theme-toggle-indicator" aria-hidden="true" />
      {theme === "dark" ? "Tema claro" : "Tema escuro"}
    </button>
  );
}
