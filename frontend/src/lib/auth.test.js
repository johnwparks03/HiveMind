import { test } from "node:test";
import assert from "node:assert/strict";
import { authErrorMessage, isValidEmail, validateCredentials } from "./auth.js";

test("isValidEmail accepts ordinary addresses and trims spaces", () => {
  assert.equal(isValidEmail("rowan@example.com"), true);
  assert.equal(isValidEmail("  rowan@example.com  "), true);
});

test("isValidEmail rejects missing parts and spaces", () => {
  assert.equal(isValidEmail(""), false);
  assert.equal(isValidEmail("rowan"), false);
  assert.equal(isValidEmail("rowan@"), false);
  assert.equal(isValidEmail("rowan@example"), false);
  assert.equal(isValidEmail("ro wan@example.com"), false);
});

test("validateCredentials asks for a valid email first, then a password", () => {
  assert.equal(validateCredentials({ email: "nope", password: "" }), "Enter a valid email address.");
  assert.equal(validateCredentials({ email: "a@b.co", password: "" }), "Enter your password.");
  assert.equal(validateCredentials({ email: "a@b.co", password: "x" }), null);
});

test("known agent error codes get plain-language messages", () => {
  assert.equal(authErrorMessage({ code: "invalid_credentials" }), "That email or password isn't right.");
  assert.match(authErrorMessage({ code: "user_exists" }), /already exists/);
  assert.match(authErrorMessage({ code: "too_many_attempts" }), /Too many attempts/);
});

test("password_policy shows the sign-in service's own message", () => {
  const err = { code: "password_policy", message: "Password must include a number" };
  assert.equal(authErrorMessage(err), "Password must include a number");
});

test("service_unavailable says whether configuration is missing or the network is down", () => {
  assert.match(
    authErrorMessage({ code: "service_unavailable", details: { missing: ["HIVEMIND_COGNITO_CLIENT_ID"] } }),
    /isn't set up/,
  );
  assert.match(
    authErrorMessage({ code: "service_unavailable", details: {} }),
    /Can't reach the sign-in service/,
  );
});

test("unknown errors fall back to a generic message, and no error means no message", () => {
  assert.equal(authErrorMessage({ code: "something_new" }), "Something went wrong. Try again.");
  assert.equal(authErrorMessage(null), null);
});
