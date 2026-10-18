// Wording and state for a teammate file download (API_Contract.md section 2.6). Shared by the
// Search results and the Ask sources, so both say the same thing. Pure, so `node --test` covers it.

// A transfer that ended as `failed` carries one of these error codes.
const FAILURE_TEXT = {
  owner_offline: "The owner went offline before sending the file.",
  owner_unresponsive: "The owner didn't respond in time.",
  upload_timeout: "The owner didn't finish sending the file in time.",
  file_unavailable: "This file is no longer available.",
  // Central uses this code both when the owner's computer reports a failed upload and when the owner
  // never finishes one, so the wording doesn't claim it was about time.
  upload_failed: "The file couldn't be sent from the owner's computer.",
  download_failed: "The download failed.",
};

const STATUS_TEXT = {
  requested: "Requesting…",
  uploading: "Owner is sending the file…",
  ready: "Starting download…",
  downloading: "Downloading…",
};

const TERMINAL = new Set(["downloaded", "failed", "expired"]);

export function isTerminal(status) {
  return TERMINAL.has(status);
}

// What the download control should show. "starting" is the moment between the click and central
// accepting the request, and "working" also covers the first poll, so there is never a blank gap
// between the button disappearing and a status appearing.
export function transferPhase({ requestPending, transferId, status }) {
  if (status === "downloaded") return "downloaded";
  if (status === "failed") return "failed";
  if (status === "expired") return "expired";
  if (requestPending) return "starting";
  if (transferId) return "working";
  return "idle";
}

export function failureText(code) {
  return FAILURE_TEXT[code] || "Download failed.";
}

export function statusText(status) {
  return STATUS_TEXT[status] || status;
}

// The request to start a download itself can be refused (POST /transfers).
export function startErrorText(code) {
  if (code === "owner_offline") return "The owner just went offline.";
  if (code === "not_found") return "This file is no longer available.";
  if (code === "own_file") return "This is your own file, so it's already on your computer.";
  return "Couldn't start the download. Try again.";
}
