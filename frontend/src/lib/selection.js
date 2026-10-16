// Multi-select helpers for the Files list. Pure functions, so they can be tested with `node --test`.

export function toggleSelected(selected, id) {
  return selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id];
}

// Only the selected files that are currently showing count, so a filter change never removes hidden files.
export function selectedInView(selected, visibleIds) {
  const visible = new Set(visibleIds);
  return selected.filter((id) => visible.has(id));
}

// Which of the selected files a bulk share/unshare can act on. Only indexed files can be
// shared; a file whose last publish failed is left to its own Retry button.
export function bulkEligible(files, action) {
  return files.filter((f) =>
    action === "share"
      ? f.index_state === "indexed" && f.public_state !== "public" && f.publish_state !== "failed"
      : f.public_state === "public" && f.publish_state !== "failed",
  );
}

export function bulkResultText(action, ok, failed) {
  const verb = action === "share" ? "made public" : "made private";
  return `${ok} of ${ok + failed} ${verb}; ${failed} failed. Try those again.`;
}

export function removeConfirmText(count) {
  const noun = count === 1 ? "file" : "files";
  return `Remove ${count} ${noun} from HiveMind? They stay on your computer, and a rescan won't add them back.`;
}
