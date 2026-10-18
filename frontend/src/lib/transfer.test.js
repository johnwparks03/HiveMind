import { test } from "node:test";
import assert from "node:assert/strict";
import { failureText, isTerminal, startErrorText, statusText, transferPhase } from "./transfer.js";

test("every error code a failed transfer can carry has wording, including the ones that used to fall through", () => {
  for (const code of ["owner_offline", "owner_unresponsive", "upload_timeout", "file_unavailable", "upload_failed", "download_failed"]) {
    assert.notEqual(failureText(code), "Download failed.", code);
  }
  assert.equal(failureText("something_else"), "Download failed.");
  assert.equal(failureText(undefined), "Download failed.");
});

test("a download that cannot start gives a specific reason when central says why", () => {
  assert.match(startErrorText("owner_offline"), /went offline/);
  assert.match(startErrorText("not_found"), /no longer available/);
  assert.match(startErrorText("own_file"), /your own file/);
  assert.match(startErrorText("unknown"), /Couldn't start the download/);
});

test("downloaded, failed and expired are final; everything else keeps polling", () => {
  assert.ok(["downloaded", "failed", "expired"].every(isTerminal));
  assert.ok(["requested", "uploading", "ready", "downloading", undefined].every((s) => !isTerminal(s)));
});

test("in-progress statuses read as plain sentences and unknown ones show as they are", () => {
  assert.equal(statusText("uploading"), "Owner is sending the file…");
  assert.equal(statusText("weird"), "weird");
});

test("the owner failing to send the file is not described as running out of time", () => {
  assert.doesNotMatch(failureText("upload_failed"), /in time/);
  assert.match(failureText("upload_failed"), /owner's computer/);
});

test("the download control is never blank between the click and the first status", () => {
  assert.equal(transferPhase({ requestPending: false, transferId: null, status: undefined }), "idle");
  assert.equal(transferPhase({ requestPending: true, transferId: null, status: undefined }), "starting");
  // Central accepted the request but the first poll has not come back yet.
  assert.equal(transferPhase({ requestPending: false, transferId: "t1", status: undefined }), "working");
  for (const status of ["requested", "uploading", "ready", "downloading"]) {
    assert.equal(transferPhase({ requestPending: false, transferId: "t1", status }), "working", status);
  }
});

test("a finished download shows its outcome, including one that expired", () => {
  assert.equal(transferPhase({ requestPending: false, transferId: "t1", status: "downloaded" }), "downloaded");
  assert.equal(transferPhase({ requestPending: false, transferId: "t1", status: "failed" }), "failed");
  assert.equal(transferPhase({ requestPending: false, transferId: "t1", status: "expired" }), "expired");
});

test("after a retry starts, the old failure gives way to the new request", () => {
  assert.equal(transferPhase({ requestPending: true, transferId: null, status: undefined }), "starting");
});
