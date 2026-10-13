// Sign-in helpers: checks before we call the agent, and plain-language messages for its errors.
// Pure functions, so they can be tested with `node --test`.

const EMAIL_SHAPE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function isValidEmail(email) {
  return EMAIL_SHAPE.test(email.trim());
}

// Only checks what we can know locally. Password rules come from the sign-in service, and its
// message is shown as-is when a password is rejected.
export function validateCredentials({ email, password }) {
  if (!isValidEmail(email)) return "Enter a valid email address.";
  if (!password) return "Enter your password.";
  return null;
}

// Maps an agent error (code, message, details) to something a person can act on.
export function authErrorMessage(err) {
  if (!err) return null;
  switch (err.code) {
    case "invalid_credentials":
      return "That email or password isn't right.";
    case "user_exists":
      return "An account with that email already exists. Try signing in instead.";
    case "password_policy":
      return err.message || "That password doesn't meet the requirements.";
    case "too_many_attempts":
      return "Too many attempts. Wait a few minutes, then try again.";
    case "service_unavailable":
      return err.details?.missing?.length
        ? "Sign-in isn't set up on this computer yet."
        : "Can't reach the sign-in service. Check your connection and try again.";
    default:
      return "Something went wrong. Try again.";
  }
}
