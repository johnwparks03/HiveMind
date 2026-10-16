import { formatDate, matchPercent } from "../lib/files";
import OpenButton from "./OpenButton";

export default function ResultCard({ result }) {
  const percent = matchPercent(result.score);

  return (
    <article className="result-card">
      <div className="result-head">
        <h3 className="result-name" title={result.path}>{result.filename}</h3>
        {percent != null && <span className="match">{percent}% match</span>}
      </div>

      <div className="result-foot">
        <dl className="meta">
          {result.file_created_at && (
            <div><dt>Created</dt><dd>{formatDate(result.file_created_at)}</dd></div>
          )}
          {result.file_modified_at && (
            <div><dt>Modified</dt><dd>{formatDate(result.file_modified_at)}</dd></div>
          )}
        </dl>
        <OpenButton fileId={result.file_id} filename={result.filename} />
      </div>
    </article>
  );
}
