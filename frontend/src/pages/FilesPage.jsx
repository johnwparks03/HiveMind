import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import HowTo from "../components/HowTo";
import Loading, { Spinner } from "../components/Loading";
import { api, isAgentUnreachable } from "../api/client";
import FolderRow from "../components/FolderRow";
import FileRow from "../components/FileRow";
import {
  countsByFolder,
  countsFor,
  folderName,
  hasPendingWork,
  matchesShareFilter,
  totalsByShare,
  totalsByState,
} from "../lib/files";
import { bulkEligible, bulkResultText, removeConfirmText, selectedInView, toggleSelected } from "../lib/selection";
import { shareConfirmText, unshareConfirmText, unshareFolderConfirmText } from "../lib/sharing";

// Poll quickly while anything is indexing, slowly when idle (E2-S8 technical notes).
const FAST_POLL_MS = 2000;
const IDLE_POLL_MS = 15000;

const FILTERS = [
  { id: "all", label: "All" },
  { id: "indexed", label: "Ready" },
  { id: "pending", label: "Reading" },
  { id: "failed", label: "Couldn't read" },
];

const SHARE_FILTERS = [
  { id: "shared", label: "Public" },
  { id: "unshared", label: "Private" },
];

// A folder with more files than this starts collapsed in the all-folders view.
const AUTO_COLLAPSE_OVER = 10;

export default function FilesPage() {
  const queryClient = useQueryClient();

  const [filter, setFilter] = useState("all");
  const [shareFilters, setShareFilters] = useState([]); // "shared" / "unshared"; none or both = show all
  const [selected, setSelected] = useState([]); // file_ids ticked in the list
  const [openOverrides, setOpenOverrides] = useState(() => new Map()); // folder_id -> open, once the user toggles it

  // Sharing only makes sense in a group, so without one every share control is hidden.
  const session = useQuery({ queryKey: ["session"], queryFn: api.getSession, refetchInterval: IDLE_POLL_MS });
  const inGroup = Boolean(session.data?.team);

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

  // No bulk endpoint on the agent, so this fans out to the per-file ones. One failure
  // doesn't stop the rest; the result says how many went through.
  const bulkShare = useMutation({
    mutationFn: async ({ action, files }) => {
      const call = action === "share" ? api.publishFile : api.unpublishFile;
      const results = await Promise.allSettled(files.map((f) => call(f.file_id)));
      const failed = results.filter((r) => r.status === "rejected");
      return {
        action,
        ok: results.length - failed.length,
        failed: failed.length,
        noTeam: failed.some((r) => r.reason?.code === "no_team"),
      };
    },
    onSuccess: (result) => {
      refresh();
      if (result.failed === 0) setSelected([]);
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
      window.alert("Nothing new to make public. Every readable file here is already public.");
      return;
    }
    if (window.confirm(shareConfirmText(count))) {
      shareFolder.mutate(folder.folder_id);
    }
  }

  function handleUnshare(folder) {
    if (window.confirm(unshareFolderConfirmText(folderName(folder.path)))) {
      unshareFolder.mutate(folder.folder_id);
    }
  }

  const folderList = folders.data ?? [];
  const fileList = files.data ?? [];
  const counts = countsByFolder(fileList);

  const inScope = fileList;
  const visible = inScope.filter(
    (f) => (filter === "all" || f.index_state === filter) && matchesShareFilter(f, inGroup ? shareFilters : []),
  );
  const scopeTotals = totalsByState(inScope);
  const shareTotals = totalsByShare(inScope);



  // Only what's showing counts, so changing the filter never removes files you can't see.
  const selectedShown = selectedInView(selected, visible.map((f) => f.file_id));

  function handleRemove(folder) {
    const ok = window.confirm(`Remove ${folderName(folder.path)} from HiveMind? Its files stay on your computer.`);
    if (ok) removeFolder.mutate(folder.folder_id);
  }

  const selectedFiles = visible.filter((f) => selectedShown.includes(f.file_id));
  const shareable = bulkEligible(selectedFiles, "share");
  const unshareable = bulkEligible(selectedFiles, "unshare");

  function handleBulkShare(action) {
    const files = action === "share" ? shareable : unshareable;
    const n = files.length;
    const text = action === "share" ? shareConfirmText(n) : unshareConfirmText(n);
    if (window.confirm(text)) bulkShare.mutate({ action, files });
  }

  // Grouped by folder only in the all-folders view; one folder is already a single list.
  // Every folder appears once, with its files under it. Empty folders still show, so they can be rescanned or removed.
  const groups = folderList.map((folder) => ({ folder, files: visible.filter((f) => f.folder_id === folder.folder_id) }));
  const isOpen = (id, count) => (openOverrides.has(id) ? openOverrides.get(id) : count <= AUTO_COLLAPSE_OVER);

  function toggleGroup(id, count) {
    setOpenOverrides((prev) => new Map(prev).set(id, !isOpen(id, count)));
  }

  function setAllGroups(open) {
    setOpenOverrides(new Map((groups ?? []).map((g) => [g.folder.folder_id, open])));
  }

  function toggleGroupSelection(groupFiles) {
    const ids = groupFiles.map((f) => f.file_id);
    const allSelected = ids.every((id) => selectedShown.includes(id));
    setSelected(allSelected ? selected.filter((id) => !ids.includes(id)) : [...new Set([...selected, ...ids])]);
  }

  function renderRows(list) {
    return (
      <ul className="file-list">
        {list.map((file) => (
          <FileRow
            key={file.file_id}
            file={file}
            canShare={inGroup}
            selected={selectedShown.includes(file.file_id)}
            onToggle={(id) => setSelected(toggleSelected(selected, id))}
          />
        ))}
      </ul>
    );
  }

  function handleRemoveSelected() {
    if (selectedShown.length === 0) return;
    if (window.confirm(removeConfirmText(selectedShown.length))) removeFiles.mutate(selectedShown);
  }

  const loadError = folders.isError || files.isError;

  return (
    <section className="files-page" aria-labelledby="files-title">
      <h2 id="files-title" className="page-title">Your folders</h2>
      <p className="page-lede">Add a folder of files to your HiveMind agent so you can search them and make them public to your team. Teammates can read the contents of public files, including when they use Ask.</p>
      <HowTo steps={['Choose a folder to add it.', 'Wait while HiveMind reads your files.', 'Make files public to share them. Teammates can then read them.']} />

      <div className="add-folder">
        <div className="add-folder-row">
          <div className="add-folder-text">
            <strong>Add a folder</strong>
            <span className="muted">PDF, Word, PowerPoint and text files inside it get read so you can search them.</span>
          </div>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => pickFolder.mutate()}
            disabled={pickFolder.isPending || addFolder.isPending}
          >
            {pickFolder.isPending ? "Opening…" : addFolder.isPending ? "Adding…" : "Upload a folder"}
          </button>
        </div>
        {(pickFolder.isError || addFolder.isError) && (
          <p className="inline-error" role="alert">
            Couldn't add that folder: {(pickFolder.error ?? addFolder.error).message}
          </p>
        )}
      </div>

      {loadError && (
        <div className="banner banner-error" role="alert">
          {isAgentUnreachable(folders.error ?? files.error)
            ? "HiveMind isn't running. Start it, then refresh this page."
            : "Couldn't load your folders. Try again in a moment."}
        </div>
      )}

      {folders.isPending && <Loading label="Loading your folders…" />}

      {folderList.length === 0 && !loadError && !folders.isPending && (
        <div className="empty">
          <p>No folders yet.</p>
          <p className="muted">Add one above to get started.</p>
        </div>
      )}

      {folderList.length > 0 && (
        <div className="files-section">
          <div className="files-head">
            <h3 className="section-title">Your folders and files</h3>
          </div>

          <div className="filter-block">
          <div className="filter-row" role="group" aria-label="Filter files by status and visibility">
            <span className="filter-label">Status</span>
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
            {inGroup && SHARE_FILTERS.map((f) => (
              <button
                key={f.id}
                type="button"
                className="filter-chip filter-chip-share"
                aria-pressed={shareFilters.includes(f.id)}
                onClick={() =>
                  setShareFilters((prev) => (prev.includes(f.id) ? prev.filter((x) => x !== f.id) : [...prev, f.id]))
                }
              >
                {f.label} <span className="chip-count">{shareTotals[f.id]}</span>
              </button>
            ))}
          </div>
          </div>

          {selectedShown.length > 0 && (
            <div className="selection-bar" role="region" aria-label="Selected files">
              <span>{selectedShown.length} selected</span>
              <div className="selection-actions">
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => setSelected([])}>
                  Clear
                </button>
                {inGroup && (<>
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  onClick={() => handleBulkShare("share")}
                  disabled={shareable.length === 0 || bulkShare.isPending}
                >
                  {bulkShare.isPending && bulkShare.variables?.action === "share"
                    ? <><Spinner />Making public…</>
                    : `Make public (${shareable.length})`}
                </button>
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  onClick={() => handleBulkShare("unshare")}
                  disabled={unshareable.length === 0 || bulkShare.isPending}
                >
                  {bulkShare.isPending && bulkShare.variables?.action === "unshare"
                    ? <><Spinner />Making private…</>
                    : `Make private (${unshareable.length})`}
                </button>
                </>)}
                <button
                  type="button"
                  className="btn btn-danger-ghost btn-sm"
                  onClick={handleRemoveSelected}
                  disabled={removeFiles.isPending}
                >
                  {removeFiles.isPending ? <><Spinner />Removing…</> : "Remove from HiveMind"}
                </button>
              </div>
              {bulkShare.isSuccess && bulkShare.data.failed > 0 && (
                <p className="inline-error" role="alert">
                  {bulkShare.data.noTeam
                    ? "Join a team first (see the Team tab) before making files public."
                    : bulkResultText(bulkShare.data.action, bulkShare.data.ok, bulkShare.data.failed)}
                </p>
              )}
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
              {groups.length > 1 && (
                <div className="group-controls">
                  <button type="button" className="btn btn-outline" onClick={() => setAllGroups(true)}>
                    Expand all
                  </button>
                  <button type="button" className="btn btn-outline" onClick={() => setAllGroups(false)}>
                    Collapse all
                  </button>
                </div>
              )}
              {groups.map(({ folder, files: groupFiles }) => {
                const id = folder.folder_id;
                const open = isOpen(id, groupFiles.length);
                const ids = groupFiles.map((f) => f.file_id);
                const pickedCount = ids.filter((x) => selectedShown.includes(x)).length;
                return (
                  <FolderRow
                    key={id}
                    folder={folder}
                    counts={countsFor(counts, id)}
                    open={open}
                    onToggleOpen={() => toggleGroup(id, groupFiles.length)}
                    shownCount={ids.length}
                    pickedCount={pickedCount}
                    onToggleSelection={() => toggleGroupSelection(groupFiles)}
                    canShare={inGroup}
                    onRescan={() => rescan.mutate(id)}
                    onRemove={() => handleRemove(folder)}
                    onShare={() => handleShare(folder)}
                    onUnshare={() => handleUnshare(folder)}
                    sharing={sharePreview.isPending || shareFolder.isPending}
                    unsharing={unshareFolder.isPending}
                    busy={rescan.isPending || removeFolder.isPending || sharePreview.isPending || shareFolder.isPending || unshareFolder.isPending}
                  >
                    {renderRows(groupFiles)}
                  </FolderRow>
                );
              })}
            </>
          )}
        </div>
      )}
    </section>
  );
}
