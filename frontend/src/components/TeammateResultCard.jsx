import { formatDate } from "../lib/files";

// A teammate's published file. No download button yet — the relay/download piece
// (docs/stories BACKLOG.md E4) hasn't been built, so showing one here would be a
// button that doesn't work. Owner identity is never returned by central, only
// whether they're currently online (relevant once download exists, since a
// transfer needs the owner's agent reachable).
export default function TeammateResultCard({ result }) {
  return (
    <article className="result-card teammate-result-card">
      <div className="result-head">
        <h3 className="result-name">{result.filename}</h3>
        <span className={`pill ${result.owner_online ? "pill-indexed" : "pill-pending"}`}>
          <span className="pill-dot" aria-hidden="true" />
          {result.owner_online ? "Owner online" : "Owner offline"}
        </span>
      </div>

      {result.tags?.length > 0 && (
        <ul className="tag-list" aria-label="Tags">
          {result.tags.map((tag) => (
            <li key={tag} className="tag">{tag}</li>
          ))}
        </ul>
      )}

      <dl className="meta">
        {result.file_created_at && (
          <div><dt>Created</dt><dd>{formatDate(result.file_created_at)}</dd></div>
        )}
        {result.file_modified_at && (
          <div><dt>Modified</dt><dd>{formatDate(result.file_modified_at)}</dd></div>
        )}
        {result.expires_at && (
          <div><dt>Expires</dt><dd>{formatDate(result.expires_at)}</dd></div>
        )}
      </dl>
    </article>
  );
}
