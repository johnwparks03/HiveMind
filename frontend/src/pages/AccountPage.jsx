import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, isAgentUnreachable } from "../api/client";
import { authErrorMessage, validateCredentials } from "../lib/auth";

const MODES = [
  { id: "login", label: "Sign in", submit: "Sign in", busy: "Signing in…" },
  { id: "signup", label: "Create account", submit: "Create account", busy: "Creating account…" },
];

export default function AccountPage() {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState(null);
  const [notice, setNotice] = useState(null);

  const session = useQuery({
    queryKey: ["session"],
    queryFn: api.getSession,
    refetchInterval: 15000,
  });

  function refreshSession() {
    queryClient.invalidateQueries({ queryKey: ["session"] });
  }

  const signIn = useMutation({
    mutationFn: ({ email, password }) => api.logIn(email, password),
    onSuccess: () => {
      setPassword("");
      setNotice(null);
      refreshSession();
    },
  });

  // Accounts are confirmed automatically by the sign-up trigger, so sign-in follows straight away.
  const signUp = useMutation({
    mutationFn: ({ email, password }) => api.signUp(email, password),
    onSuccess: (_data, { email, password }) => {
      setNotice("Account created. Signing you in…");
      signIn.mutate({ email, password });
    },
  });

  const logOut = useMutation({
    mutationFn: api.logOut,
    onSuccess: refreshSession,
  });

  function switchMode(next) {
    setMode(next);
    setFormError(null);
    setNotice(null);
    signIn.reset();
    signUp.reset();
  }

  function handleSubmit(e) {
    e.preventDefault();
    const creds = { email: email.trim(), password };
    const problem = validateCredentials(creds);
    setFormError(problem);
    if (problem) return;
    if (mode === "signup") signUp.mutate(creds);
    else signIn.mutate(creds);
  }

  const busy = signIn.isPending || signUp.isPending;
  const failure = signIn.error || signUp.error;
  const current = MODES.find((m) => m.id === mode);
  const signedIn = session.data?.signed_in;

  return (
    <section className="account-page" aria-labelledby="account-title">
      <h2 id="account-title" className="page-title">Your <span className="accent-word">account</span></h2>
      <p className="page-lede">Sign in to share with your team. Your files stay on this computer until you choose to share them.</p>

      {session.isPending && <p className="muted">Checking sign-in…</p>}

      {session.isError && (
        <div className="banner banner-error" role="alert">
          {isAgentUnreachable(session.error)
            ? "Can't reach the local agent. Start it on port 8420, then try again."
            : "Couldn't check your sign-in status. Try again in a moment."}
        </div>
      )}

      {signedIn && (
        <div className="account-card">
          <p className="account-status">
            <span className="dot dot-online" aria-hidden="true" /> Signed in as <strong>{session.data.email}</strong>
          </p>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => logOut.mutate()}
            disabled={logOut.isPending}
          >
            {logOut.isPending ? "Signing out…" : "Sign out"}
          </button>
          {logOut.isError && (
            <p className="inline-error" role="alert">Couldn't sign out. Try again.</p>
          )}
        </div>
      )}

      {session.data && !signedIn && (
        <div className="account-card">
          <div className="segmented" role="group" aria-label="Sign in or create an account">
            {MODES.map((m) => (
              <button
                key={m.id}
                type="button"
                className="segment"
                aria-pressed={mode === m.id}
                onClick={() => switchMode(m.id)}
              >
                {m.label}
              </button>
            ))}
          </div>

          <form className="account-form" onSubmit={handleSubmit} noValidate>
            <label htmlFor="account-email" className="field-label">Email</label>
            <input
              id="account-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              spellCheck={false}
            />

            <label htmlFor="account-password" className="field-label">Password</label>
            <input
              id="account-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === "signup" ? "new-password" : "current-password"}
            />

            {formError && <p className="inline-error" role="alert">{formError}</p>}
            {failure && !formError && (
              <p className="inline-error" role="alert">{authErrorMessage(failure)}</p>
            )}
            {notice && <p className="muted" role="status">{notice}</p>}

            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? current.busy : current.submit}
            </button>
          </form>
        </div>
      )}
    </section>
  );
}
