function formatDate(iso) {
  if (!iso) return null;
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function ResultCard({ result, onOpen }) {
  return (
    <div className="result-card">
      <div className="result-card-head">
        <span className="result-filename">{result.filename}</span>
        <button className="link-button" onClick={() => onOpen(result.file_id)}>
          Open
        </button>
      </div>
      {result.snippet && <p className="result-snippet">{result.snippet}</p>}
      <div className="result-meta">
        {result.file_modified_at && <span>Modified {formatDate(result.file_modified_at)}</span>}
        {result.score != null && <span>Match {(1 - result.score).toFixed(2)}</span>}
      </div>
    </div>
  );
}
