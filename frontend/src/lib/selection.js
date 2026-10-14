// Multi-select helpers for the Files list. Pure functions, so they can be tested with `node --test`.

export function toggleSelected(selected, id) {
  return selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id];
}

// Only the selected files that are currently showing count, so a filter change never removes hidden files.
export function selectedInView(selected, visibleIds) {
  const visible = new Set(visibleIds);
  return selected.filter((id) => visible.has(id));
}

export function removeConfirmText(count) {
  const noun = count === 1 ? "file" : "files";
  return `Remove ${count} ${noun} from HiveMind? They stay on your computer, and a rescan won't add them back.`;
}
