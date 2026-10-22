// Hash routing for the main tabs. The Team tab was folded into Account, so old #/groups links land there.
export const TAB_IDS = ["search", "ask", "files", "account"];

const ALIASES = { groups: "account" };

export function tabFromHash(hash) {
  const id = hash.replace("#/", "");
  const resolved = ALIASES[id] ?? id;
  return TAB_IDS.includes(resolved) ? resolved : "search";
}
