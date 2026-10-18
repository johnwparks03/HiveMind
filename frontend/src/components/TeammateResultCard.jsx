import { formatDate } from "../lib/files";
import TransferControl from "./TransferControl";

// A teammate's published file, with a download button (docs/stories BACKLOG.md E4-S4/S5). The
// download itself lives in TransferControl, shared with the Ask sources. Owner identity is never
// returned by central, only whether they're currently online.
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

      <dl className="meta">
        {result.file_created_at && (
          <div><dt>Created</dt><dd>{formatDate(result.file_created_at)}</dd></div>
        )}
        {result.file_modified_at && (
          <div><dt>Modified</dt><dd>{formatDate(result.file_modified_at)}</dd></div>
        )}
      </dl>

      <TransferControl
        fileId={result.file_id}
        filename={result.filename}
        disabled={!result.owner_online}
        disabledTitle="The owner needs to be online to send this file"
      />
    </article>
  );
}
