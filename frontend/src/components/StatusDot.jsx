export default function StatusDot({ online }) {
  return (
    <span className="status-dot">
      <span className={`dot ${online ? "dot-online" : "dot-offline"}`} />
      {online ? "Agent connected" : "Agent unreachable"}
    </span>
  );
}
