import { test } from "node:test";
import assert from "node:assert/strict";
import { bulkEligible, bulkResultText, removeConfirmText, selectedInView, toggleSelected } from "./selection.js";

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

test("bulkEligible picks what each action can act on", () => {
  const files = [
    { file_id: "a", index_state: "indexed", public_state: "private" },
    { file_id: "b", index_state: "indexed", public_state: "public" },
    { file_id: "c", index_state: "pending", public_state: "private" },
    { file_id: "d", index_state: "indexed", public_state: "private", publish_state: "failed" },
  ];
  assert.deepEqual(bulkEligible(files, "share").map((f) => f.file_id), ["a"]);
  assert.deepEqual(bulkEligible(files, "unshare").map((f) => f.file_id), ["b"]);
});

test("bulkResultText reports partial failure", () => {
  assert.equal(bulkResultText("share", 3, 2), "3 of 5 made public; 2 failed. Try those again.");
});
