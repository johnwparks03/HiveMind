import { formatDate } from "../lib/files";
import OpenButton from "./OpenButton";
import PublishControl from "./PublishControl";

const STATE_LABEL = {
  indexed: "Indexed",
  pending: "Indexing",
  failed: "Failed",
};

export default function FileRow({ file, selected, onToggle, canShare }) {
  return (
    <li className={`file-row${selected ? " is-selected" : ""}`}>
      <input
        type="checkbox"
        className="file-check"
        checked={selected}
        onChange={() => onToggle(file.file_id)}
        aria-label={`Select ${file.filename}`}
      />
      <div className="file-main">
        <div className="file-line">
          <span className="file-name" title={file.path}>{file.filename}</span>
          <span className={`pill pill-${file.index_state}`}>
            <span className="pill-dot" aria-hidden="true" />
            {STATE_LABEL[file.index_state] ?? file.index_state}
          </span>
        </div>
        <div className="file-meta">
          {file.file_modified_at && <span>Modified {formatDate(file.file_modified_at)}</span>}
          {file.index_state === "failed" && file.failure_reason && (
            <span className="failure-reason">{file.failure_reason}</span>
          )}
        </div>
        {file.index_state === "indexed" && <PublishControl file={file} canShare={canShare} />}
      </div>
      <OpenButton fileId={file.file_id} filename={file.filename} />
    </li>
  );
}
