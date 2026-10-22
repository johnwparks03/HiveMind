import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { folderName, hasPendingWork, hasScanningFolders } from "../lib/files";
import { Spinner } from "./Loading";

// While a folder is being read or a file is still pending, the list refreshes this often.
const SCAN_POLL_MS = 2000;

// Folder checkboxes expand to individual file checkboxes. There's no separate
// "folder selected" state — a folder's checkbox is checked/indeterminate/unchecked
// based on how many of its files are in `selectedFileIds`, and toggling it
// selects or clears all of that folder's files at once. Empty selection means
// "search everything," same as the backend's default.
export default function ScopePicker({ selectedFileIds, onChange }) {
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState(() => new Set());

  const queryClient = useQueryClient();
  const folders = useQuery({
    queryKey: ["folders"],
    queryFn: api.listFolders,
    refetchInterval: (query) => (hasScanningFolders(query.state.data ?? []) ? SCAN_POLL_MS : false),
  });
  const files = useQuery({
    queryKey: ["files"],
    queryFn: api.listFiles,
    refetchInterval: (query) =>
      hasPendingWork(query.state.data ?? []) || hasScanningFolders(folders.data ?? []) ? SCAN_POLL_MS : false,
  });

  // The last poll can land just before the final file is written, so refresh the files once when a scan ends.
  const scanning = hasScanningFolders(folders.data ?? []);
  useEffect(() => {
    if (!scanning) queryClient.invalidateQueries({ queryKey: ["files"] });
  }, [scanning, queryClient]);

  if (!folders.data || !files.data || folders.data.length === 0) return null;

  const filesByFolder = {};
  for (const file of files.data) {
    (filesByFolder[file.folder_id] ??= []).push(file);
  }

  function toggleExpanded(folderId) {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(folderId) ? next.delete(folderId) : next.add(folderId);
      return next;
    });
  }

  function toggleFile(fileId) {
    const next = new Set(selectedFileIds);
    next.has(fileId) ? next.delete(fileId) : next.add(fileId);
    onChange(next);
  }

  function toggleFolder(folderId, folderFiles) {
    const ids = folderFiles.map((f) => f.file_id);
    const allSelected = ids.every((id) => selectedFileIds.has(id));
    const next = new Set(selectedFileIds);
    ids.forEach((id) => (allSelected ? next.delete(id) : next.add(id)));
    onChange(next);
  }

  const scopedCount = selectedFileIds.size;

  return (
    <div className="scope-picker">
      <button type="button" className="scope-toggle" onClick={() => setOpen((v) => !v)}>
        {scopedCount === 0 ? "Using all your files" : `Using ${scopedCount} selected file${scopedCount === 1 ? "" : "s"}`}
        <span aria-hidden="true">{open ? " ▲" : " ▼"}</span>
      </button>

      {open && (
        <div className="scope-panel">
          {scopedCount > 0 && (
            <button type="button" className="btn btn-outline btn-sm scope-clear" onClick={() => onChange(new Set())}>
              Clear selection — search everything
            </button>
          )}
          <ul className="scope-folder-list">
            {folders.data.map((folder) => {
              const folderFiles = filesByFolder[folder.folder_id] ?? [];
              const ids = folderFiles.map((f) => f.file_id);
              const selectedInFolder = ids.filter((id) => selectedFileIds.has(id)).length;
              const isExpanded = expanded.has(folder.folder_id);
              return (
                <li key={folder.folder_id} className="scope-folder-row">
                  <div className="scope-folder-head">
                    <input
                      type="checkbox"
                      className="file-check"
                      checked={ids.length > 0 && selectedInFolder === ids.length}
                      ref={(el) => {
                        if (el) el.indeterminate = selectedInFolder > 0 && selectedInFolder < ids.length;
                      }}
                      onChange={() => toggleFolder(folder.folder_id, folderFiles)}
                      aria-label={`Select all files in ${folderName(folder.path)}`}
                    />
                    <button
                      type="button"
                      className="scope-folder-name"
                      onClick={() => toggleExpanded(folder.folder_id)}
                    >
                      {folderName(folder.path)} ({ids.length})
                      {folder.scan_state === "scanning" && <Spinner />}
                      <span aria-hidden="true">{isExpanded ? " ▲" : " ▼"}</span>
                    </button>
                  </div>
                  {isExpanded && (
                    <ul className="scope-file-list">
                      {folderFiles.map((file) => (
                        <li key={file.file_id} className="scope-file-row">
                          <label>
                            <input
                              type="checkbox"
                              className="file-check"
                              checked={selectedFileIds.has(file.file_id)}
                              onChange={() => toggleFile(file.file_id)}
                            />
                            {file.filename}
                          </label>
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
