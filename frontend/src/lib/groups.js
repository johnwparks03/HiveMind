// Group helpers: invite-code cleanup and plain-language messages for team errors.
// Pure functions, so they can be tested with `node --test`.

// The server trims and uppercases codes too; doing it here means what the user sees matches what is sent.
export function normaliseInviteCode(code) {
  return code.trim().toUpperCase();
}

// Maps an agent error code (API_Contract section 3.1) to something a person can act on.
export function groupErrorMessage(err) {
  if (!err) return null;
  switch (err.code) {
    case "already_in_team":
      return "You're already on a team. Leave it before creating or joining another.";
    case "invalid_code":
      return "That invite code isn't valid. Check it and try again.";
    case "invite_expired":
      return "That invite has expired. Ask for a new code.";
    case "no_team":
      return "You're not on a team yet.";
    case "service_unavailable":
      return err.details?.missing?.length
        ? "Sign-in isn't set up on this computer yet."
        : "Can't reach the team service. Check your connection and try again.";
    default:
      return "Something went wrong. Try again.";
  }
}
