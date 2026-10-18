// Talks only to the local agent (CLAUDE.md: "the frontend never calls the central
// service"). Interface A: header X-HiveMind-Token on every request except
// GET /auth/token, per API_Contract.md section 2.1 / Feature_List 1.11.

import { normaliseFile } from "../lib/files.js";

const AGENT_BASE = "http://127.0.0.1:8420";

let tokenPromise = null;

async function getToken() {
  if (!tokenPromise) {
    tokenPromise = fetch(`${AGENT_BASE}/auth/token`)
      .then((res) => {
        if (!res.ok) throw new Error("agent_unreachable");
        return res.json();
      })
      .then((data) => data.token)
      .catch((err) => {
        tokenPromise = null; // allow retry on next call
        throw err;
      });
  }
  return tokenPromise;
}

async function request(path, options = {}) {
  const token = await getToken();
  const res = await fetch(`${AGENT_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-HiveMind-Token": token,
      ...options.headers,
    },
  });

  if (res.status === 401) tokenPromise = null; // agent restarted; fetch a fresh token next time

  if (!res.ok) {
    let detail;
    try {
      detail = await res.json();
    } catch {
      detail = null;
    }
    const error = new Error(detail?.error?.message || `request_failed_${res.status}`);
    error.code = detail?.error?.code;
    error.details = detail?.error?.details ?? {};
    error.status = res.status;
    throw error;
  }
  if (res.status === 204) return null;
  return res.json();
}

// True when the agent process itself can't be reached (not when it returned an error).
export function isAgentUnreachable(err) {
  return err.message === "agent_unreachable" || err instanceof TypeError;
}

export const api = {
  search: (query, includeTeammates) =>
    request("/search", { method: "POST", body: JSON.stringify({ query, include_teammates: Boolean(includeTeammates) }) }),
  // Online-only (local Bedrock call, decided 2026-10-15, demo/MVP) — unlike search,
  // there's no offline fallback for synthesizing an answer across files.
  // fileIds optionally scopes which files to consider; omitted/empty searches everything.
  // includeTeammates also uses teammates' public files; the answer then carries teammate_skipped_reason.
  ask: (question, fileIds, includeTeammates) =>
    request("/ask", {
      method: "POST",
      body: JSON.stringify({ question, file_ids: fileIds ?? [], include_teammates: Boolean(includeTeammates) }),
    }),
  // Saved Ask chats (agent-local). A chat is created on first question if the user hasn't started one.
  listChats: () => request("/chats").then((data) => data.chats),
  createChat: () => request("/chats", { method: "POST" }),
  getChat: (chatId) => request(`/chats/${chatId}`),
  deleteChat: (chatId) => request(`/chats/${chatId}`, { method: "DELETE" }),
  // Resolves to { messages, teammateSkippedReason }. The reason (why teammates' files were left out, or
  // null) is only on the live answer; it is not saved with the chat, so the caller has to keep it.
  askInChat: (chatId, question, fileIds, includeTeammates) =>
    request(`/chats/${chatId}/messages`, {
      method: "POST",
      body: JSON.stringify({ question, file_ids: fileIds ?? [], include_teammates: Boolean(includeTeammates) }),
    }).then((data) => ({
      messages: data.messages,
      teammateSkippedReason: data.messages?.[data.messages.length - 1]?.teammate_skipped_reason ?? null,
    })),
  listFolders: () => request("/folders").then((data) => data.folders),
  listFiles: () => request("/files").then((data) => data.files.map(normaliseFile)),
  addFolder: (path) => request("/folders", { method: "POST", body: JSON.stringify({ path }) }),
  // Opens the Windows folder dialog on the laptop. Resolves to the chosen path, or null on cancel.
  pickFolder: () => request("/folders/pick", { method: "POST" }).then((data) => data.path),
  rescanFolder: (folderId) => request(`/folders/${folderId}/rescan`, { method: "POST" }),
  removeFolder: (folderId) => request(`/folders/${folderId}`, { method: "DELETE" }),
  openFile: (fileId) => request(`/files/${fileId}/open`, { method: "POST" }),
  // Removes files from HiveMind only. They stay on disk, and rescans won't add them back.
  removeFiles: (fileIds) =>
    request("/files/remove", { method: "POST", body: JSON.stringify({ file_ids: fileIds }) }),
  ping: () => request("/folders").then(() => true).catch(() => false),
  // Publish/share a file or folder with the team (docs/stories BACKLOG.md E3-S4/S5/S6).
  setTags: (fileId, tags) =>
    request(`/files/${fileId}/tags`, { method: "PUT", body: JSON.stringify({ tags }) }).then(normaliseFile),
  publishFile: (fileId) => request(`/files/${fileId}/publish`, { method: "POST" }).then(normaliseFile),
  unpublishFile: (fileId) => request(`/files/${fileId}/unpublish`, { method: "POST" }).then(normaliseFile),
  retryPublish: (fileId) => request(`/files/${fileId}/retry`, { method: "POST" }).then(normaliseFile),
  sharePreview: (folderId) => request(`/folders/${folderId}/share-preview`).then((data) => data.file_count),
  shareFolder: (folderId) => request(`/folders/${folderId}/share`, { method: "POST" }).then((data) => data.queued),
  unshareFolder: (folderId) => request(`/folders/${folderId}/unshare`, { method: "POST" }).then((data) => data.queued),
  // Teammate file download (docs/stories BACKLOG.md E4-S4/S5). The agent polls central
  // and streams to the real Windows Downloads folder; the frontend just polls the agent.
  requestTransfer: (fileId, filename) =>
    request("/transfers", { method: "POST", body: JSON.stringify({ file_id: fileId, filename }) }),
  getTransfer: (transferId) => request(`/transfers/${transferId}`),
  getDownloadFolder: () => request("/settings/download-folder"),
  setDownloadFolder: (path) =>
    request("/settings/download-folder", { method: "PUT", body: JSON.stringify({ path }) }),
  resetDownloadFolder: () => request("/settings/download-folder", { method: "DELETE" }),
  // Sign-in goes through the agent, which talks to Cognito. The frontend never sees Cognito tokens.
  logIn: (email, password) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logOut: () => request("/auth/logout", { method: "POST" }),
  getSession: () => request("/session"),
  // Groups: one team per person for the MVP (API_Contract section 3.1). The agent proxies these to central.
  getGroup: () => request("/team").then((data) => data.team),
  getGroupFiles: () => request("/team/files").then((data) => data.files),
  createGroup: (name) => request("/team", { method: "POST", body: JSON.stringify({ name }) }),
  createInvite: () => request("/team/invites", { method: "POST" }),
  joinGroup: (code) => request("/team/join", { method: "POST", body: JSON.stringify({ code }) }),
  leaveGroup: () => request("/team/leave", { method: "POST" }),
};
