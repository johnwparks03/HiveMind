// An on/off toggle. A real button with role="switch", so Space/Enter work and screen readers announce the state.
export default function Switch({ checked, onChange, children }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      className="switch"
      onClick={() => onChange(!checked)}
    >
      <span className="switch-track" aria-hidden="true">
        <span className="switch-thumb" />
      </span>
      <span className="switch-label">{children}</span>
    </button>
  );
}
