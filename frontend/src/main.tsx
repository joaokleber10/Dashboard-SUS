import React from "react";
import ReactDOM from "react-dom/client";

// React Query guarda respostas da API e evita requisicoes desnecessarias.
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import "./styles/globals.css";
import "./styles/dashboard.css";
import "./styles/brand.css";

// Configuracao compartilhada por todas as consultas do aplicativo.
const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 60_000, refetchOnWindowFocus: false, retry: 1 } },
});

// "root" vem do elemento com id=root no index.html.
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);
