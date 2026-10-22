import assert from "node:assert/strict";
import test from "node:test";
import { tabFromHash } from "./tabs.js";

test("known tabs resolve to themselves", () => {
  assert.equal(tabFromHash("#/ask"), "ask");
  assert.equal(tabFromHash("#/files"), "files");
  assert.equal(tabFromHash("#/account"), "account");
});

test("the old Team route redirects to account", () => {
  assert.equal(tabFromHash("#/groups"), "account");
});

test("empty or unknown hashes fall back to search", () => {
  assert.equal(tabFromHash(""), "search");
  assert.equal(tabFromHash("#/nope"), "search");
});
