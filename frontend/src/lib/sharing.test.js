import { test } from "node:test";
import assert from "node:assert/strict";
import { SHARE_CONSENT_ONE, shareConfirmText, unshareConfirmText, unshareFolderConfirmText } from "./sharing.js";

test("making files public says teammates can read the contents, including through Ask", () => {
  assert.match(shareConfirmText(3), /^Make 3 files public\?/);
  assert.match(shareConfirmText(3), /read their contents, including when they use Ask/);
  assert.match(shareConfirmText(1), /^Make 1 file public\?/);
  assert.match(shareConfirmText(1), /read its contents/);
  assert.match(SHARE_CONSENT_ONE, /read this file's contents, including when they use Ask/);
});

test("making files private says teammates can no longer read them", () => {
  assert.match(unshareConfirmText(2), /^Make 2 public files private\? Teammates will no longer be able to read them\./);
  assert.match(unshareConfirmText(1), /^Make 1 public file private\?.*read it\./);
  assert.match(unshareFolderConfirmText("Notes"), /^Make all public files in Notes private\?.*no longer be able to read them/);
});
