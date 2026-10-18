// Pure helpers for the Ask page, so they can be tested with `node --test`.

// A source from an Ask answer. Sources saved before teammates existed have no `source`: they are local.
export function isTeammateSource(source) {
  return source?.source === "teammate";
}

// Why teammates' files were left out of an answer (the agent's `teammate_skipped_reason`).
const SKIPPED_TEXT = {
  no_topic: "Teammates' files weren't used because the question has no topic to match. Try naming what you're looking for.",
  date_filter: "Teammates' files weren't used because the question has a date range, which can't be applied to their files.",
  no_team: "Join a team (see the Team tab) to include teammates' files.",
  central_unavailable: "Couldn't reach teammates' files just now. This answer uses your own files only.",
};

// null/undefined means teammates were searched (or weren't asked for): nothing to say.
export function skippedReasonText(reason) {
  if (!reason) return null;
  return SKIPPED_TEXT[reason] ?? "Teammates' files weren't used for this answer.";
}

// The switch is off by default and remembered for the browser session only. Storage is passed in
// (sessionStorage in the app) and may be missing or throw in a private window: then it is just off.
export const INCLUDE_TEAMMATES_KEY = "ask.includeTeammates";

export function loadIncludeTeammates(storage) {
  try {
    return storage?.getItem(INCLUDE_TEAMMATES_KEY) === "true";
  } catch {
    return false;
  }
}

export function saveIncludeTeammates(storage, value) {
  try {
    storage?.setItem(INCLUDE_TEAMMATES_KEY, String(Boolean(value)));
  } catch {
    // Not remembered; the switch still works for this page.
  }
}
