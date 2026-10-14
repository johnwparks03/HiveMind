// Loading state: a small spinning ring with a label. Use `Spinner` alone inside buttons.
export function Spinner() {
  return <span className="spinner" aria-hidden="true" />;
}

export default function Loading({ label }) {
  return (
    <p className="loading" role="status">
      <Spinner />
      <span>{label}</span>
    </p>
  );
}
