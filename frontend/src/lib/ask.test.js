import { test } from "node:test";
import assert from "node:assert/strict";
import {
  INCLUDE_TEAMMATES_KEY,
  isTeammateSource,
  loadIncludeTeammates,
  saveIncludeTeammates,
  skippedReasonText,
} from "./ask.js";

test("only a source flagged teammate is a teammate source; older saved sources are local", () => {
  assert.equal(isTeammateSource({ file_id: "1", filename: "a.txt", source: "teammate" }), true);
  assert.equal(isTeammateSource({ file_id: "1", filename: "a.txt", source: "local" }), false);
  assert.equal(isTeammateSource({ file_id: "1", filename: "a.txt" }), false);
  assert.equal(isTeammateSource(undefined), false);
});

test("every skip reason the agent can send has its own plain wording", () => {
  const reasons = ["no_topic", "date_filter", "no_team", "central_unavailable"];
  const texts = reasons.map(skippedReasonText);
  assert.ok(texts.every((t) => typeof t === "string" && t.length > 20));
  assert.equal(new Set(texts).size, reasons.length);
  assert.match(skippedReasonText("no_topic"), /no topic/);
  assert.match(skippedReasonText("central_unavailable"), /your own files only/);
});

test("no reason means nothing to show, and an unknown reason still gets a sentence", () => {
  assert.equal(skippedReasonText(null), null);
  assert.equal(skippedReasonText(undefined), null);
  assert.match(skippedReasonText("something_new"), /weren't used/);
});

function fakeStorage(initial = {}) {
  const data = { ...initial };
  return { getItem: (k) => (k in data ? data[k] : null), setItem: (k, v) => { data[k] = v; }, data };
}

test("the switch is off by default and remembers its setting", () => {
  const storage = fakeStorage();
  assert.equal(loadIncludeTeammates(storage), false);
  saveIncludeTeammates(storage, true);
  assert.equal(storage.data[INCLUDE_TEAMMATES_KEY], "true");
  assert.equal(loadIncludeTeammates(storage), true);
  saveIncludeTeammates(storage, false);
  assert.equal(loadIncludeTeammates(storage), false);
});

test("a missing or throwing storage just means off", () => {
  assert.equal(loadIncludeTeammates(undefined), false);
  const broken = { getItem: () => { throw new Error("blocked"); }, setItem: () => { throw new Error("blocked"); } };
  assert.equal(loadIncludeTeammates(broken), false);
  assert.doesNotThrow(() => saveIncludeTeammates(broken, true));
});
