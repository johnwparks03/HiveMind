// Recent searches: the last few queries, newest first, kept in this browser only.
// Pure helpers plus a thin storage wrapper, so the logic is testable with `node --test`.

export const RECENT_LIMIT = 3;
const STORAGE_KEY = "hivemind.recentSearches";

// Newest first. A repeat moves to the front instead of appearing twice (case-insensitive).
export function addRecent(list, query) {
  const q = query.trim();
  if (!q) return list;
  const rest = list.filter((item) => item.toLowerCase() !== q.toLowerCase());
  return [q, ...rest].slice(0, RECENT_LIMIT);
}

export function removeRecent(list, query) {
  return list.filter((item) => item.toLowerCase() !== query.toLowerCase());
}

// Storage can be missing, blocked, or hold junk; any of those means "no recent searches".
export function loadRecent(storage = globalThis.localStorage) {
  try {
    const parsed = JSON.parse(storage?.getItem(STORAGE_KEY) ?? "[]");
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item) => typeof item === "string").slice(0, RECENT_LIMIT);
  } catch {
    return [];
  }
}

export function saveRecent(list, storage = globalThis.localStorage) {
  try {
    storage?.setItem(STORAGE_KEY, JSON.stringify(list));
  } catch {
    // Not saving is acceptable; the list simply won't survive a reload.
  }
}
