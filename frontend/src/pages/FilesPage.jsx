import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import Loading, { Spinner } from "../components/Loading";
import { api, isAgentUnreachable } from "../api/client";
import FolderCard from "../components/FolderCard";
import FileRow from "../components/FileRow";
import { countsByFolder, countsFor, folderName, hasPendingWork, scopeFiles, totalsByState } from "../lib/files";
import { removeConfirmText, selectedInView, toggleSelected } from "../lib/selection";

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
  const [folderId, setFolderId] = useState(null); // null = all folders
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState([]); // file_ids ticked in the list

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
    onSuccess: refresh,
  });

  // The agent opens the Windows folder dialog. Cancelling gives null, and nothing happens.
  const pickFolder = useMutation({
    mutationFn: api.pickFolder,
    onSuccess: (path) => {
      if (path) addFolder.mutate(path);
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

  const removeFiles = useMutation({
    mutationFn: (ids) => api.removeFiles(ids),
    onSuccess: () => {
      setSelected([]);
      refresh();
    },
  });

  const sharePreview = useMutation({ mutationFn: (id) => api.sharePreview(id) });
  const shareFolder = useMutation({ mutationFn: (id) => api.shareFolder(id), onSuccess: refresh });
  const unshareFolder = useMutation({ mutationFn: (id) => api.unshareFolder(id), onSuccess: refresh });

  async function handleShare(folder) {
    let count;
    try {
      count = await sharePreview.mutateAsync(folder.folder_id);
    } catch {
      window.alert("Couldn't check what's eligible to share. Try again in a moment.");
      return;
    }
    if (count === 0) {
      window.alert("Nothing new to share — every indexed file here is already public.");
      return;
    }
    if (window.confirm(`Share ${count} file${count === 1 ? "" : "s"} with your team?`)) {
      shareFolder.mutate(folder.folder_id);
    }
  }

  function handleUnshare(folder) {
    if (window.confirm(`Make all shared files in ${folderName(folder.path)} private again?`)) {
      unshareFolder.mutate(folder.folder_id);
    }
  }

  const folderList = folders.data ?? [];
  const fileList = files.data ?? [];
  const counts = countsByFolder(fileList);

  const inScope = scopeFiles(fileList, folderId);
  const visible = inScope.filter((f) => filter === "all" || f.index_state === filter);
  const scopeTotals = totalsByState(inScope);

  const selectedFolder = folderList.find((f) => f.folder_id === folderId);

  // Only what's showing counts, so changing the filter never removes files you can't see.
  const selectedShown = selectedInView(selected, visible.map((f) => f.file_id));

  function handleRemove(folder) {
    const ok = window.confirm(`Stop watching ${folder.path}? Its index entries will be removed. Your files are not touched.`);
    if (ok) removeFolder.mutate(folder.folder_id);
  }

  function handleRemoveSelected() {
    if (selectedShown.length === 0) return;
    if (window.confirm(removeConfirmText(selectedShown.length))) removeFiles.mutate(selectedShown);
  }

  const loadError = folders.isError || files.isError;

  return (
    <section className="files-page" aria-labelledby="files-title">
      <h2 id="files-title" className="page-title">Your folders</h2>
      <p className="page-lede">Add a folder to index its Word and PowerPoint files. Indexing runs in the background.</p>

      <div className="add-folder">
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => pickFolder.mutate()}
          disabled={pickFolder.isPending || addFolder.isPending}
        >
          {pickFolder.isPending ? "Opening…" : addFolder.isPending ? "Adding…" : "Choose a folder"}
        </button>
        {(pickFolder.isError || addFolder.isError) && (
          <p className="inline-error" role="alert">
            Couldn't add that folder: {(pickFolder.error ?? addFolder.error).message}
          </p>
        )}
      </div>

      {loadError && (
        <div className="banner banner-error" role="alert">
          {isAgentUnreachable(folders.error ?? files.error)
            ? "Can't reach the local agent. Start it on port 8420, then refresh this page."
            : "Couldn't load your folders. Try again in a moment."}
        </div>
      )}

      {folders.isPending && <Loading label="Loading your folders…" />}

      {folderList.length === 0 && !loadError && !folders.isPending && (
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
                onShare={() => handleShare(folder)}
                onUnshare={() => handleUnshare(folder)}
                busy={rescan.isPending || removeFolder.isPending || sharePreview.isPending || shareFolder.isPending || unshareFolder.isPending}
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

          {selectedShown.length > 0 && (
            <div className="selection-bar" role="region" aria-label="Selected files">
              <span>{selectedShown.length} selected</span>
              <div className="selection-actions">
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => setSelected([])}>
                  Clear
                </button>
                <button
                  type="button"
                  className="btn btn-danger-ghost btn-sm"
                  onClick={handleRemoveSelected}
                  disabled={removeFiles.isPending}
                >
                  {removeFiles.isPending ? <><Spinner />Removing…</> : "Remove from HiveMind"}
                </button>
              </div>
              {removeFiles.isError && (
                <p className="inline-error" role="alert">Couldn't remove those files. Try again.</p>
              )}
            </div>
          )}

          {visible.length === 0 ? (
            <p className="empty muted">No files in this view.</p>
          ) : (
            <>
              {visible.length > 1 && selectedShown.length === 0 && (
                <div className="select-all">
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => setSelected(visible.map((f) => f.file_id))}
                  >
                    Select all shown
                  </button>
                </div>
              )}
              <ul className="file-list">
                {visible.map((file) => (
                  <FileRow
                    key={file.file_id}
                    file={file}
                    selected={selectedShown.includes(file.file_id)}
                    onToggle={(id) => setSelected(toggleSelected(selected, id))}
                  />
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </section>
  );
}
