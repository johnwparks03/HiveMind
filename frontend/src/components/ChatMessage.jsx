import ResultCard from "./ResultCard";

function interpretedCaption(interpreted) {
  if (!interpreted) return null;
  const parts = [];
  if (interpreted.topic) parts.push(`topic "${interpreted.topic}"`);
  if (interpreted.date_from) {
    const from = new Date(interpreted.date_from).toLocaleDateString();
    const to = interpreted.date_to ? new Date(interpreted.date_to).toLocaleDateString() : from;
    parts.push(from === to ? `on ${from}` : `${from} – ${to}`);
  }
  if (parts.length === 0) return "Searched everything, most recent first";
  return `Searched for ${parts.join(", ")}`;
}

export default function ChatMessage({ message, onOpenFile }) {
  if (message.role === "user") {
    return (
      <div className="message message-user">
        <div className="bubble bubble-user">{message.text}</div>
      </div>
    );
  }

  if (message.error) {
    return (
      <div className="message message-assistant">
        <div className="bubble bubble-error">{message.text}</div>
      </div>
    );
  }

  return (
    <div className="message message-assistant">
      <div className="bubble bubble-assistant">
        <p className="interpreted-caption">{interpretedCaption(message.interpreted)}</p>
        {message.results.length === 0 ? (
          <p className="no-results">No local files matched.</p>
        ) : (
          <div className="result-list">
            {message.results.map((r) => (
              <ResultCard key={r.file_id} result={r} onOpen={onOpenFile} />
            ))}
          </div>
        )}
        <p className="teammate-note">Teammate search isn't built yet — this only looks at your own files.</p>
      </div>
    </div>
  );
}
