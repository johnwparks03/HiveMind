import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { api, isAgentUnreachable } from "./client.js";

// Each test swaps in a fake agent. The token endpoint always succeeds; `respond` decides the rest.
let calls;
let respond;
const realFetch = globalThis.fetch;

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

beforeEach(() => {
  calls = [];
  respond = () => jsonResponse(200, {});
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options });
    if (url.endsWith("/auth/token")) return jsonResponse(200, { token: "test-token" });
    return respond(url, options);
  };
});

afterEach(() => {
  globalThis.fetch = realFetch;
});

test("requests carry the startup token in X-HiveMind-Token", async () => {
  respond = () => jsonResponse(200, { folders: [] });
  await api.listFolders();
  const folderCall = calls.find((c) => c.url.endsWith("/folders"));
  assert.equal(folderCall.options.headers["X-HiveMind-Token"], "test-token");
});

test("an error envelope's message and code reach the caller", async () => {
  respond = () =>
    jsonResponse(400, { error: { code: "invalid_request", message: "not a directory", details: {} } });
  await assert.rejects(api.addFolder("C:\\nope"), (err) => {
    assert.equal(err.message, "not a directory");
    assert.equal(err.code, "invalid_request");
    assert.equal(err.status, 400);
    return true;
  });
});

test("a missing file on disk is distinguishable from other open failures", async () => {
  respond = () => jsonResponse(404, { error: { code: "file_missing", message: "file no longer on disk" } });
  await assert.rejects(api.openFile("abc"), (err) => err.code === "file_missing");
});

test("a non-JSON error body falls back to a generic message", async () => {
  respond = () => ({ ok: false, status: 500, json: async () => { throw new SyntaxError("bad json"); } });
  await assert.rejects(api.search("x"), (err) => err.message === "request_failed_500");
});

test("listFiles normalises agent column names to contract names", async () => {
  respond = () =>
    jsonResponse(200, {
      files: [
        { file_id: "1", index_status: "indexed", index_failure_reason: null },
        { file_id: "2", index_status: "failed", index_failure_reason: "no extractable text" },
      ],
    });
  const files = await api.listFiles();
  assert.deepEqual(files.map((f) => f.index_state), ["indexed", "failed"]);
  assert.equal(files[1].failure_reason, "no extractable text");
});

test("a refused connection is reported as the agent being unreachable", async () => {
  globalThis.fetch = async () => {
    throw new TypeError("fetch failed");
  };
  await assert.rejects(api.listFolders(), (err) => isAgentUnreachable(err));
});

test("an error response from the agent is not treated as unreachable", () => {
  assert.equal(isAgentUnreachable(Object.assign(new Error("not found"), { status: 404 })), false);
});
