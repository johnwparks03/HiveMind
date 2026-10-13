import { test } from "node:test";
import assert from "node:assert/strict";
import { RECENT_LIMIT, addRecent, loadRecent, removeRecent, saveRecent } from "./recent.js";

test("removeRecent drops only the named query, ignoring case", () => {
  assert.deepEqual(removeRecent(["budget", "Roadmap", "vendor"], "roadmap"), ["budget", "vendor"]);
  assert.deepEqual(removeRecent(["budget"], "missing"), ["budget"]);
});

function fakeStorage(initial = null, { throws = false } = {}) {
  const data = new Map();
  if (initial !== null) data.set("hivemind.recentSearches", initial);
  return {
    getItem: (key) => {
      if (throws) throw new Error("blocked");
      return data.has(key) ? data.get(key) : null;
    },
    setItem: (key, value) => {
      if (throws) throw new Error("blocked");
      data.set(key, value);
    },
    data,
  };
}

test("addRecent puts the newest query first", () => {
  assert.deepEqual(addRecent(["b"], "a"), ["a", "b"]);
});

test("addRecent keeps only the most recent three", () => {
  assert.equal(RECENT_LIMIT, 3);
  let list = [];
  for (const q of ["one", "two", "three", "four"]) list = addRecent(list, q);
  assert.deepEqual(list, ["four", "three", "two"]);
});

test("a repeated query moves to the front instead of appearing twice", () => {
  assert.deepEqual(addRecent(["budget", "roadmap", "vendor"], "Roadmap"), ["Roadmap", "budget", "vendor"]);
});

test("blank and whitespace-only queries are ignored, and queries are trimmed", () => {
  assert.deepEqual(addRecent(["a"], "   "), ["a"]);
  assert.deepEqual(addRecent([], "  budget plan  "), ["budget plan"]);
});

test("loadRecent returns [] for missing, invalid or non-list storage", () => {
  assert.deepEqual(loadRecent(fakeStorage()), []);
  assert.deepEqual(loadRecent(fakeStorage("not json")), []);
  assert.deepEqual(loadRecent(fakeStorage('{"a":1}')), []);
  assert.deepEqual(loadRecent(null), []);
});

test("loadRecent drops non-string entries and caps the list", () => {
  const stored = JSON.stringify(["a", 3, "b", "c", "d"]);
  assert.deepEqual(loadRecent(fakeStorage(stored)), ["a", "b", "c"]);
});

test("loadRecent and saveRecent round-trip", () => {
  const storage = fakeStorage();
  saveRecent(["budget plan", "meeting notes"], storage);
  assert.deepEqual(loadRecent(storage), ["budget plan", "meeting notes"]);
});

test("a blocked storage never throws", () => {
  const storage = fakeStorage(null, { throws: true });
  assert.doesNotThrow(() => saveRecent(["x"], storage));
  assert.deepEqual(loadRecent(storage), []);
});
