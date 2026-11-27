export function ErroBanner({ erro }: { erro: unknown }) {
  const msg = erro instanceof Error ? erro.message : "Erro inesperado.";
  return <div className="erro" role="alert">⚠ {msg}</div>;
}
