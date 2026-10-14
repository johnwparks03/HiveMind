import { test } from "node:test";
import assert from "node:assert/strict";
import { removeConfirmText, selectedInView, toggleSelected } from "./selection.js";

test("toggleSelected adds an id, then removes it when toggled again", () => {
  let selected = toggleSelected([], "a");
  assert.deepEqual(selected, ["a"]);
  selected = toggleSelected(selected, "b");
  assert.deepEqual(selected, ["a", "b"]);
  selected = toggleSelected(selected, "a");
  assert.deepEqual(selected, ["b"]);
});

test("selectedInView keeps only selections that are currently visible", () => {
  assert.deepEqual(selectedInView(["a", "b", "c"], ["b", "c", "d"]), ["b", "c"]);
  assert.deepEqual(selectedInView(["a"], []), []);
});

test("removeConfirmText says what happens and handles one or many", () => {
  assert.match(removeConfirmText(1), /Remove 1 file from HiveMind/);
  assert.match(removeConfirmText(3), /Remove 3 files from HiveMind/);
  assert.match(removeConfirmText(2), /stay on your computer/);
});
