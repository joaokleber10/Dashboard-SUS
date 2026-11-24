export function ErroBanner({ erro }: { erro: unknown }) {
  const msg = erro instanceof Error ? erro.message : "Erro inesperado.";
  return <div className="erro" role="alert">⚠ {msg}</div>;
}

export function KpiSkeleton() {
  return (
    <section className="cards">
      {[0, 1, 2, 3].map((i) => <div key={i} className="card skeleton" style={{ height: 112 }} />)}
    </section>
  );
}
