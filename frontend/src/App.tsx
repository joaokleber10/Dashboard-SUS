import { useState } from "react";

// Componentes visuais usados por toda a pagina.
import { Dashboard } from "./pages/Dashboard";

// Tipo e valor inicial usados pelo tema claro/escuro.
import type { Theme } from "./components/common/ThemeToggle";
import { temaInicial } from "./components/common/ThemeToggle";

function App() {
  // O estado do tema pertence ao componente principal porque o tema aparece no
  // cabecalho e precisa continuar igual enquanto o usuario navega pela pagina.
  const [theme, setTheme] = useState<Theme>(temaInicial);

  return (
    <div className="app">
      {/* A página organiza menu, cabeçalho e dados sem duplicar a consulta de meta. */}
      <Dashboard theme={theme} onThemeChange={setTheme} />
    </div>
  );
}

export default App;
