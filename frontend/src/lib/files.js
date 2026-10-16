// Pure helpers shared by the Search and Files pages. Kept free of React and fetch so
// they can be tested with `node --test`.

// The agent's SQLite column is `index_status` and `index_failure_reason`; API_Contract.md
// calls them `index_state` and `failure_reason`. Normalise to the contract names here.
// `tags` is stored as a JSON string column too, but the contract says it's an array.
export function normaliseFile(raw) {
  let tags = raw.tags;
  if (typeof tags === "string") {
    try {
      tags = JSON.parse(tags);
    } catch {
      tags = [];
    }
  }
  return {
    ...raw,
    index_state: raw.index_state ?? raw.index_status ?? "pending",
    failure_reason: raw.failure_reason ?? raw.index_failure_reason ?? null,
    tags: Array.isArray(tags) ? tags : [],
  };
}

const EMPTY_COUNTS = { total: 0, indexed: 0, pending: 0, failed: 0, public: 0 };

// The agent's folder object has no counts yet, so derive them from the file list.
// `public` is orthogonal to the indexed/pending/failed index-state bucket — a file
// is counted in exactly one of those three, and separately counted as public or not.
export function countsByFolder(files) {
  const counts = {};
  for (const file of files) {
    const c = (counts[file.folder_id] ??= { ...EMPTY_COUNTS });
    c.total += 1;
    if (file.index_state === "indexed") c.indexed += 1;
    else if (file.index_state === "failed") c.failed += 1;
    else c.pending += 1;
    if (file.public_state === "public") c.public += 1;
  }
  return counts;
}

export function countsFor(counts, folderId) {
  return counts[folderId] ?? EMPTY_COUNTS;
}

export function hasPendingWork(files) {
  return files.some((file) => file.index_state === "pending");
}

// Files inside the selected folder, or every folder when none is selected (folderId == null).
export function scopeFiles(files, folderId) {
  return files.filter((file) => folderId == null || file.folder_id === folderId);
}

export function totalsByState(files) {
  const totals = { all: files.length, indexed: 0, pending: 0, failed: 0 };
  for (const file of files) {
    if (file.index_state === "indexed") totals.indexed += 1;
    else if (file.index_state === "failed") totals.failed += 1;
    else if (file.index_state === "pending") totals.pending += 1;
  }
  return totals;
}

const isShared = (file) => file.public_state === "public";

export function totalsByShare(files) {
  const shared = files.filter(isShared).length;
  return { all: files.length, shared, unshared: files.length - shared };
}

// `active` is the set of share filters switched on ("shared", "unshared"). Neither on, or
// both on, means no filtering.
export function matchesShareFilter(file, active) {
  const shared = active.includes("shared");
  const unshared = active.includes("unshared");
  if (shared === unshared) return true;
  return shared ? isShared(file) : !isShared(file);
}

// True when every indexed file in the folder is already public, so there is nothing left to
// share. Pending and failed files can't be shared, so they don't count.
export function allShared(counts) {
  return counts.indexed > 0 && counts.public >= counts.indexed;
}

// Groups files under their folder, in folder order. Folders with no files are skipped,
// so a filter that empties a folder hides its header too.
export function groupByFolder(files, folders) {
  const byFolder = new Map();
  for (const file of files) {
    if (!byFolder.has(file.folder_id)) byFolder.set(file.folder_id, []);
    byFolder.get(file.folder_id).push(file);
  }
  return folders
    .filter((folder) => byFolder.has(folder.folder_id))
    .map((folder) => ({ folder, files: byFolder.get(folder.folder_id) }));
}

export function folderName(path) {
  return path.split(/[\\/]/).filter(Boolean).pop() ?? path;
}

export function formatDate(iso) {
  if (!iso) return null;
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

// The agent returns a distance-style `score`; the UI shows similarity as a percentage.
export function matchPercent(score) {
  if (score == null) return null;
  return Math.round(Math.min(1, Math.max(0, 1 - score)) * 100);
}

export function interpretedCaption(interpreted) {
  if (!interpreted) return null;
  const parts = [];
  if (interpreted.topic) parts.push(`topic "${interpreted.topic}"`);
  if (interpreted.date_from) {
    const from = new Date(interpreted.date_from).toLocaleDateString();
    const to = interpreted.date_to ? new Date(interpreted.date_to).toLocaleDateString() : from;
    parts.push(from === to ? `on ${from}` : `${from} – ${to}`);
  }
  if (parts.length === 0) return "Searched everything, most recent first";
  return `Searched for ${parts.join(", ")}`;
}
