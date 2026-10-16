import { allShared, folderName } from "../lib/files";
import { Spinner } from "./Loading";

export default function FolderCard({ folder, counts, selected, onSelect, onRescan, onRemove, onShare, onUnshare, busy, sharing, unsharing }) {
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

      {counts.public > 0 && (
        <p className="folder-progress folder-public-progress" aria-label={`${counts.public} of ${counts.total} files shared with your team`}>
          <strong>{counts.public}</strong> of {counts.total} public
        </p>
      )}

      {(counts.pending > 0 || counts.failed > 0) && (
        <p className="folder-stats">
          {counts.pending > 0 && <span className="stat stat-pending">{counts.pending} pending</span>}
          {counts.failed > 0 && <span className="stat stat-failed">{counts.failed} failed</span>}
        </p>
      )}

      <div className="folder-actions">
        <div className="folder-share-row">
          {(sharing || !allShared(counts)) && (
            <button type="button" className="btn btn-outline btn-sm" onClick={onShare} disabled={busy}>
              {sharing ? <><Spinner />Sharing…</> : "Share with team"}
            </button>
          )}
          {counts.public > 0 && (
            <button type="button" className="btn btn-outline btn-sm" onClick={onUnshare} disabled={busy}>
              {unsharing ? <><Spinner />Unsharing…</> : "Unshare"}
            </button>
          )}
        </div>
        <div className="folder-manage-row">
          <button type="button" className="btn btn-outline btn-sm" onClick={onRescan} disabled={busy}>
            Rescan
          </button>
          <button type="button" className="btn btn-danger-outline btn-sm" onClick={onRemove} disabled={busy}>
            Remove
          </button>
        </div>
      </div>
    </article>
  );
}
