import { test } from "node:test";
import assert from "node:assert/strict";
import {
  countsByFolder,
  allShared,
  countsFor,
  groupByFolder,
  matchesShareFilter,
  totalsByShare,
  folderName,
  hasPendingWork,
  interpretedCaption,
  matchPercent,
  normaliseFile,
  scopeFiles,
  totalsByState,
} from "./files.js";

test("normaliseFile maps agent column names to contract names", () => {
  const file = normaliseFile({
    file_id: "a",
    index_status: "failed",
    index_failure_reason: "no extractable text",
  });
  assert.equal(file.index_state, "failed");
  assert.equal(file.failure_reason, "no extractable text");
});

test("normaliseFile keeps contract names when they are already present", () => {
  const file = normaliseFile({ file_id: "a", index_state: "indexed", failure_reason: null });
  assert.equal(file.index_state, "indexed");
  assert.equal(file.failure_reason, null);
});

test("normaliseFile parses the tags JSON string column into a real array", () => {
  assert.deepEqual(normaliseFile({ tags: '["budget", "q4"]' }).tags, ["budget", "q4"]);
  assert.deepEqual(normaliseFile({ tags: null }).tags, []);
  assert.deepEqual(normaliseFile({ tags: "not json" }).tags, []);
  assert.deepEqual(normaliseFile({ tags: ["already", "an", "array"] }).tags, ["already", "an", "array"]);
});

test("countsByFolder groups files by folder and buckets them by state", () => {
  const files = [
    { folder_id: "f1", index_state: "indexed", public_state: "public" },
    { folder_id: "f1", index_state: "indexed" },
    { folder_id: "f1", index_state: "pending" },
    { folder_id: "f1", index_state: "failed" },
    { folder_id: "f2", index_state: "pending" },
  ];
  const counts = countsByFolder(files);
  assert.deepEqual(countsFor(counts, "f1"), { total: 4, indexed: 2, pending: 1, failed: 1, public: 1 });
  assert.deepEqual(countsFor(counts, "f2"), { total: 1, indexed: 0, pending: 1, failed: 0, public: 0 });
});

test("countsFor returns zeros for a folder with no files yet", () => {
  assert.deepEqual(countsFor({}, "missing"), { total: 0, indexed: 0, pending: 0, failed: 0, public: 0 });
});

test("hasPendingWork is true only while a file is still pending", () => {
  assert.equal(hasPendingWork([{ index_state: "indexed" }, { index_state: "failed" }]), false);
  assert.equal(hasPendingWork([{ index_state: "indexed" }, { index_state: "pending" }]), true);
  assert.equal(hasPendingWork([]), false);
});

test("matchPercent converts the agent's distance score to a clamped percentage", () => {
  assert.equal(matchPercent(0.29), 71);
  assert.equal(matchPercent(-0.5), 100);
  assert.equal(matchPercent(2), 0);
  assert.equal(matchPercent(null), null);
});

test("interpretedCaption describes what the query was understood to mean", () => {
  assert.equal(interpretedCaption(null), null);
  assert.equal(
    interpretedCaption({ topic: null, date_from: null, date_to: null }),
    "Searched everything, most recent first",
  );
  assert.equal(interpretedCaption({ topic: "budget plan", date_from: null }), 'Searched for topic "budget plan"');

  const day = new Date(2026, 9, 11).toISOString();
  const sameDay = interpretedCaption({ topic: null, date_from: day, date_to: day });
  assert.match(sameDay, /^Searched for on /);

  const range = interpretedCaption({
    topic: "budget plan",
    date_from: new Date(2026, 9, 5).toISOString(),
    date_to: new Date(2026, 9, 11).toISOString(),
  });
  assert.match(range, /^Searched for topic "budget plan", .+ – .+$/);
});

test("folderName takes the last segment of Windows and POSIX paths", () => {
  assert.equal(folderName("C:\\Users\\rhagey\\Documents\\Notes"), "Notes");
  assert.equal(folderName("/home/rhagey/Notes/"), "Notes");
  assert.equal(folderName("Notes"), "Notes");
});

// Scale: the Files page filters and counts whatever the agent returns. These mirror the
// 83-file test corpus (60 docx, 20 pptx, 3 edge cases) plus a second folder, so a bug that
// only shows up past a handful of files gets caught here.
function syntheticFiles() {
  const states = ["indexed", "pending", "failed"];
  const files = [];
  for (let i = 0; i < 83; i += 1) {
    files.push({ file_id: `a${i}`, folder_id: "f1", index_state: states[i % 3] });
  }
  for (let i = 0; i < 40; i += 1) {
    files.push({ file_id: `b${i}`, folder_id: "f2", index_state: i < 30 ? "indexed" : "failed" });
  }
  return files;
}

test("counts and totals stay consistent across a corpus-sized file list", () => {
  const files = syntheticFiles();
  const counts = countsByFolder(files);

  assert.equal(countsFor(counts, "f1").total, 83);
  assert.equal(countsFor(counts, "f2").total, 40);
  for (const folderId of ["f1", "f2"]) {
    const c = countsFor(counts, folderId);
    assert.equal(c.indexed + c.pending + c.failed, c.total, `buckets must add up for ${folderId}`);
  }

  const totals = totalsByState(files);
  assert.equal(totals.all, 123);
  assert.equal(totals.indexed + totals.pending + totals.failed, totals.all);
});

test("scopeFiles narrows to one folder, or keeps everything when no folder is selected", () => {
  const files = syntheticFiles();
  assert.equal(scopeFiles(files, null).length, 123);
  assert.equal(scopeFiles(files, "f2").length, 40);
  assert.equal(scopeFiles(files, "missing").length, 0);
});

test("totalsByState reports the scope the status chips show", () => {
  const scoped = scopeFiles(syntheticFiles(), "f2");
  assert.deepEqual(totalsByState(scoped), { all: 40, indexed: 30, pending: 0, failed: 10 });
});

test("totalsByShare and matchesShareFilter split files by public_state", () => {
  const files = [{ public_state: "public" }, { public_state: "private" }, { public_state: null }];
  assert.deepEqual(totalsByShare(files), { all: 3, shared: 1, unshared: 2 });
  assert.equal(files.filter((f) => matchesShareFilter(f, ["shared"])).length, 1);
  assert.equal(files.filter((f) => matchesShareFilter(f, ["unshared"])).length, 2);
  // Neither or both switched on means no filtering.
  assert.equal(files.filter((f) => matchesShareFilter(f, [])).length, 3);
  assert.equal(files.filter((f) => matchesShareFilter(f, ["shared", "unshared"])).length, 3);
});

test("allShared is true only when every indexed file is public", () => {
  assert.equal(allShared({ indexed: 3, public: 3 }), true);
  assert.equal(allShared({ indexed: 3, public: 2 }), false);
  assert.equal(allShared({ indexed: 0, public: 0 }), false);
  // A failed file in the folder doesn't stop it counting as fully shared.
  assert.equal(allShared({ total: 4, indexed: 3, failed: 1, public: 3 }), true);
});

test("groupByFolder keeps folder order and skips empty folders", () => {
  const folders = [{ folder_id: "a" }, { folder_id: "b" }, { folder_id: "c" }];
  const files = [
    { file_id: 1, folder_id: "c" },
    { file_id: 2, folder_id: "a" },
    { file_id: 3, folder_id: "c" },
  ];
  const groups = groupByFolder(files, folders);
  assert.deepEqual(groups.map((g) => g.folder.folder_id), ["a", "c"]);
  assert.deepEqual(groups[1].files.map((f) => f.file_id), [1, 3]);
});
