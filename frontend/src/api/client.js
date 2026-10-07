// Talks only to the local agent (CLAUDE.md: "the frontend never calls the central
// service"). Interface A: header X-HiveMind-Token on every request except
// GET /auth/token, per API_Contract.md section 2.1 / Feature_List 1.11.

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

  if (!res.ok) {
    let detail;
    try {
      detail = await res.json();
    } catch {
      detail = null;
    }
    const error = new Error(detail?.error?.message || `request_failed_${res.status}`);
    error.code = detail?.error?.code;
    error.status = res.status;
    throw error;
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  search: (query) => request("/search", { method: "POST", body: JSON.stringify({ query }) }),
  listFolders: () => request("/folders"),
  addFolder: (path) => request("/folders", { method: "POST", body: JSON.stringify({ path }) }),
  rescanFolder: (folderId) => request(`/folders/${folderId}/rescan`, { method: "POST" }),
  removeFolder: (folderId) => request(`/folders/${folderId}`, { method: "DELETE" }),
  openFile: (fileId) => request(`/files/${fileId}/open`, { method: "POST" }),
  ping: () => getToken().then(() => true).catch(() => false),
};
