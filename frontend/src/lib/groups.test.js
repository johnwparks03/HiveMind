import { test } from "node:test";
import assert from "node:assert/strict";
import { groupErrorMessage, normaliseInviteCode } from "./groups.js";

test("normaliseInviteCode trims spaces and uppercases the code", () => {
  assert.equal(normaliseInviteCode("  k7q2-9xpd "), "K7Q2-9XPD");
});

test("known team error codes get plain-language messages", () => {
  assert.match(groupErrorMessage({ code: "already_in_team" }), /already on a team/);
  assert.match(groupErrorMessage({ code: "invalid_code" }), /isn't valid/);
  assert.match(groupErrorMessage({ code: "invite_expired" }), /expired/);
  assert.match(groupErrorMessage({ code: "no_team" }), /not on a team/);
});

test("service_unavailable says whether configuration or the network is the problem", () => {
  assert.match(
    groupErrorMessage({ code: "service_unavailable", details: { missing: ["HIVEMIND_CENTRAL_API_URL"] } }),
    /isn't set up/,
  );
  assert.match(groupErrorMessage({ code: "service_unavailable", details: {} }), /Can't reach the team service/);
});

test("unknown errors fall back to a generic message, and no error means no message", () => {
  assert.equal(groupErrorMessage({ code: "something_new" }), "Something went wrong. Try again.");
  assert.equal(groupErrorMessage(null), null);
});
