import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, isAgentUnreachable } from "../api/client";
import FolderCard from "../components/FolderCard";
import FileRow from "../components/FileRow";
import { countsByFolder, countsFor, folderName, hasPendingWork, scopeFiles, totalsByState } from "../lib/files";

// Poll quickly while anything is indexing, slowly when idle (E2-S8 technical notes).
const FAST_POLL_MS = 2000;
const IDLE_POLL_MS = 15000;

const FILTERS = [
  { id: "all", label: "All" },
  { id: "indexed", label: "Indexed" },
  { id: "pending", label: "Indexing" },
  { id: "failed", label: "Failed" },
];

export default function FilesPage() {
  const queryClient = useQueryClient();
  const [newPath, setNewPath] = useState("");
  const [folderId, setFolderId] = useState(null); // null = all folders
  const [filter, setFilter] = useState("all");

  const folders = useQuery({
    queryKey: ["folders"],
    queryFn: api.listFolders,
    refetchInterval: IDLE_POLL_MS,
  });

  const files = useQuery({
    queryKey: ["files"],
    queryFn: api.listFiles,
    refetchInterval: (query) => (hasPendingWork(query.state.data ?? []) ? FAST_POLL_MS : IDLE_POLL_MS),
  });

  function refresh() {
    queryClient.invalidateQueries({ queryKey: ["folders"] });
    queryClient.invalidateQueries({ queryKey: ["files"] });
  }

  const addFolder = useMutation({
    mutationFn: (path) => api.addFolder(path),
    onSuccess: () => {
      setNewPath("");
      refresh();
    },
  });

  const rescan = useMutation({
    mutationFn: (id) => api.rescanFolder(id),
    onSuccess: refresh,
  });

  const removeFolder = useMutation({
    mutationFn: (id) => api.removeFolder(id),
    onSuccess: (_data, id) => {
      if (folderId === id) setFolderId(null);
      refresh();
    },
  });

  const folderList = folders.data ?? [];
  const fileList = files.data ?? [];
  const counts = countsByFolder(fileList);

  const inScope = scopeFiles(fileList, folderId);
  const visible = inScope.filter((f) => filter === "all" || f.index_state === filter);
  const scopeTotals = totalsByState(inScope);

  const selectedFolder = folderList.find((f) => f.folder_id === folderId);

  function handleAdd(e) {
    e.preventDefault();
    const path = newPath.trim();
    if (path) addFolder.mutate(path);
  }

  function handleRemove(folder) {
    const ok = window.confirm(`Stop watching ${folder.path}? Its index entries will be removed. Your files are not touched.`);
    if (ok) removeFolder.mutate(folder.folder_id);
  }

  const loadError = folders.isError || files.isError;

  return (
    <section className="files-page" aria-labelledby="files-title">
      <h2 id="files-title" className="page-title">Your folders</h2>
      <p className="page-lede">Add a folder to index its Word and PowerPoint files. Indexing runs in the background.</p>

      <form className="add-folder" onSubmit={handleAdd}>
        <label htmlFor="folder-path" className="field-label">Folder path</label>
        <div className="add-folder-row">
          <input
            id="folder-path"
            type="text"
            value={newPath}
            onChange={(e) => setNewPath(e.target.value)}
            placeholder="C:\Users\you\Documents\Notes"
            autoComplete="off"
            spellCheck={false}
          />
          <button type="submit" className="btn btn-primary" disabled={addFolder.isPending || !newPath.trim()}>
            {addFolder.isPending ? "Adding…" : "Add folder"}
          </button>
        </div>
        {addFolder.isError && (
          <p className="inline-error" role="alert">Couldn't add that folder: {addFolder.error.message}</p>
        )}
      </form>

      {loadError && (
        <div className="banner banner-error" role="alert">
          {isAgentUnreachable(folders.error ?? files.error)
            ? "Can't reach the local agent. Start it on port 8420, then refresh this page."
            : "Couldn't load your folders. Try again in a moment."}
        </div>
      )}

      {folderList.length === 0 && !loadError && (
        <div className="empty">
          <p>No folders yet.</p>
          <p className="muted">Add one above to start indexing.</p>
        </div>
      )}

      {folderList.length > 0 && (
        <ul className="folder-grid" aria-label="Watched folders">
          {folderList.map((folder) => (
            <li key={folder.folder_id}>
              <FolderCard
                folder={folder}
                counts={countsFor(counts, folder.folder_id)}
                selected={folderId === folder.folder_id}
                onSelect={() => setFolderId(folderId === folder.folder_id ? null : folder.folder_id)}
                onRescan={() => rescan.mutate(folder.folder_id)}
                onRemove={() => handleRemove(folder)}
                busy={rescan.isPending || removeFolder.isPending}
              />
            </li>
          ))}
        </ul>
      )}

      {folderList.length > 0 && (
        <div className="files-section">
          <div className="files-head">
            <h3 className="section-title">
              Files{selectedFolder ? ` in ${folderName(selectedFolder.path)}` : ""}
            </h3>
            {selectedFolder && (
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setFolderId(null)}>
                Show all folders
              </button>
            )}
          </div>

          <div className="filter-row" role="group" aria-label="Filter files by status">
            {FILTERS.map((f) => (
              <button
                key={f.id}
                type="button"
                className="filter-chip"
                aria-pressed={filter === f.id}
                onClick={() => setFilter(f.id)}
              >
                {f.label} <span className="chip-count">{scopeTotals[f.id]}</span>
              </button>
            ))}
          </div>

          {visible.length === 0 ? (
            <p className="empty muted">No files in this view.</p>
          ) : (
            <ul className="file-list">
              {visible.map((file) => (
                <FileRow key={file.file_id} file={file} />
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
