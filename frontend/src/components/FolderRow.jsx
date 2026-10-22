import { useEffect, useRef } from "react";
import { allShared, folderName } from "../lib/files";
import { Spinner } from "./Loading";

// One folder: its name, status, and actions on a single header line, with its files underneath.
// Replaces the separate folder cards, so each folder appears once.
export default function FolderRow({
  folder,
  counts,
  open,
  onToggleOpen,
  shownCount,
  pickedCount,
  onToggleSelection,
  canShare,
  onRemove,
  onShare,
  onUnshare,
  sharing,
  unsharing,
  busy,
  children,
}) {
  const name = folderName(folder.path);
  const scanning = folder.scan_state === "scanning";
  // While the scan runs, progress is files finished out of files found; after that, files indexed out of files shown.
  const percent = scanning
    ? folder.scan_total ? Math.round((folder.scan_done / folder.scan_total) * 100) : 0
    : counts.total === 0 ? 0 : Math.round((counts.indexed / counts.total) * 100);
  const attention = [
    counts.pending > 0 && `${counts.pending} still reading`,
    counts.failed > 0 && `${counts.failed} couldn't be read`,
    folder.scan_state === "failed" && "Stopped before reading every file",
  ].filter(Boolean);

  const checkRef = useRef(null);
  useEffect(() => {
    if (checkRef.current) {
      checkRef.current.indeterminate = pickedCount > 0 && pickedCount < shownCount;
    }
  }, [pickedCount, shownCount]);

  return (
    <div className="file-group">
      <div className="file-group-head">
        <input
          ref={checkRef}
          type="checkbox"
          className="file-check"
          checked={shownCount > 0 && pickedCount === shownCount}
          disabled={shownCount === 0}
          onChange={onToggleSelection}
          aria-label={`Select all shown files in ${name}`}
        />
        <button type="button" className="file-group-toggle" aria-expanded={open} onClick={onToggleOpen}>
          <span className="file-group-chevron" aria-hidden="true">{open ? "▾" : "▸"}</span>
          <span className="file-group-name">{name}</span>
          <span className="muted file-group-count">
            {scanning ? `Reading ${folder.scan_done} of ${folder.scan_total ?? "?"} files…` : null}
            {scanning ? null : `${counts.total} file${counts.total === 1 ? "" : "s"}`}
            {!scanning && counts.public > 0 ? ` · ${counts.public} public` : ""}
            {attention.length > 0 ? ` · ${attention.join(" · ")}` : ""}
          </span>
        </button>

        <div className="folder-row-actions">
          {canShare && !allShared(counts) && (
            <button type="button" className="btn btn-outline btn-sm" onClick={onShare} disabled={busy}>
              {sharing ? <><Spinner />Making public…</> : "Make public"}
            </button>
          )}
          {canShare && counts.public > 0 && (
            <button type="button" className="btn btn-outline btn-sm" onClick={onUnshare} disabled={busy}>
              {unsharing ? <><Spinner />Making private…</> : "Make private"}
            </button>
          )}
          <button type="button" className="btn btn-danger-outline btn-sm" onClick={onRemove} disabled={busy}>
            Remove
          </button>
        </div>
      </div>

      <div
        className="progress folder-row-progress"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        aria-label={`${name} reading progress`}
      >
        <span className="progress-fill" style={{ width: `${percent}%` }} />
      </div>

      {open && children}
    </div>
  );
}
