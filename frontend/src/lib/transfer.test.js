import { test } from "node:test";
import assert from "node:assert/strict";
import { failureText, isTerminal, startErrorText, statusText } from "./transfer.js";

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
