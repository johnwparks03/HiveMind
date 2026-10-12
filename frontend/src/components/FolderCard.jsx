import { folderName } from "../lib/files";

export default function FolderCard({ folder, counts, selected, onSelect, onRescan, onRemove, busy }) {
  const percent = counts.total === 0 ? 0 : Math.round((counts.indexed / counts.total) * 100);
  const name = folderName(folder.path);

  return (
    <article className={`folder-card${selected ? " is-selected" : ""}`}>
      <button
        type="button"
        className="folder-select"
        onClick={onSelect}
        aria-pressed={selected}
        title={folder.path}
      >
        <span className="folder-name">{name}</span>
        <span className="folder-path">{folder.path}</span>
      </button>

      <p className="folder-progress" aria-label={`${counts.indexed} of ${counts.total} files indexed`}>
        <strong>{counts.indexed}</strong> of {counts.total} indexed
      </p>
      <div
        className="progress"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        aria-label={`${name} indexing progress`}
      >
        <span className="progress-fill" style={{ width: `${percent}%` }} />
      </div>

      <div className="folder-foot">
        <span className="folder-stats">
          {counts.pending > 0 && <span className="stat stat-pending">{counts.pending} pending</span>}
          {counts.failed > 0 && <span className="stat stat-failed">{counts.failed} failed</span>}
        </span>
        <div className="folder-actions">
          <button type="button" className="btn btn-ghost btn-sm" onClick={onRescan} disabled={busy}>
            Rescan
          </button>
          <button type="button" className="btn btn-danger-ghost btn-sm" onClick={onRemove} disabled={busy}>
            Remove
          </button>
        </div>
      </div>
    </article>
  );
}
