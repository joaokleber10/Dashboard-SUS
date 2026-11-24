import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// envDir ".." faz o Vite ler o .env da raiz do projeto (só variáveis VITE_* chegam ao navegador).
export default defineConfig({
  plugins: [react()],
  envDir: "..",
  server: { port: 5173 },
});
