import Loading, { Spinner } from "../components/Loading";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, isAgentUnreachable } from "../api/client";
import PasswordInput from "../components/PasswordInput";
import TeamPanel from "../components/TeamPanel";
import { authErrorMessage, validateCredentials } from "../lib/auth";

export default function AccountPage() {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState(null);

  const session = useQuery({
    queryKey: ["session"],
    queryFn: api.getSession,
    refetchInterval: 15000,
  });

  function refreshSession() {
    queryClient.invalidateQueries({ queryKey: ["session"] });
  }

  // Update the status straight from the response, so the page changes at once. The agent's
  // /session also looks up the team on central, which can be slow, so it refreshes in the background.
  const signIn = useMutation({
    mutationFn: ({ email, password }) => api.logIn(email, password),
    onSuccess: (data) => {
      setPassword("");
      queryClient.setQueryData(["session"], (old) => ({
        ...old,
        signed_in: true,
        email: data.email,
      }));
      refreshSession();
      queryClient.invalidateQueries({ queryKey: ["group"] });
      window.location.hash = "#/search";
    },
  });

  const logOut = useMutation({
    mutationFn: api.logOut,
    onSuccess: () => {
      setEmail("");
      queryClient.setQueryData(["session"], (old) => ({
        ...old,
        signed_in: false,
        email: null,
        team: null,
      }));
      refreshSession();
      queryClient.removeQueries({ queryKey: ["group"] });
    },
  });

  function handleSubmit(e) {
    e.preventDefault();
    const creds = { email: email.trim(), password };
    const problem = validateCredentials(creds);
    setFormError(problem);
    if (problem) return;
    signIn.mutate(creds);
  }

  const signedIn = session.data?.signed_in;
  const initial = (session.data?.email ?? "?").trim().charAt(0).toUpperCase();
  const signedOutLede = "Sign in to share with your team. Your files stay on this computer until you choose to share them, and teammates can read the files you make public, including through Ask.";
  const steps = [
    "Sign in with your email and password.",
    "Your files stay on this computer until you make them public; teammates can then read them.",
    "Sign out here anytime.",
  ];

  return (
    <section className="account-page" aria-label="Account">
      <header className="ac-intro">
        <h2 className="ac-title">Account</h2>
        {signedIn && <p className="ac-lede">Your profile, team and shared files.</p>}
        {session.data && !signedIn && <p className="ac-lede">{signedOutLede}</p>}
      </header>

      {session.isPending && <Loading label="Checking sign-in…" />}

      {session.isError && (
        <div className="banner banner-error" role="alert">
          {isAgentUnreachable(session.error)
            ? "HiveMind isn't running. Start it, then try again."
            : "Couldn't check your sign-in status. Try again in a moment."}
        </div>
      )}

      {signedIn && (
        <>
          <div className="ac-card ac-identity">
            <span className="ac-avatar" aria-hidden="true">{initial}</span>
            <p className="ac-identity-text">
              You are signed in as <strong>{session.data.email}</strong>
            </p>
            <button
              type="button"
              className="ac-btn ac-btn-danger"
              onClick={() => logOut.mutate()}
              disabled={logOut.isPending}
            >
              {logOut.isPending ? <><Spinner />Signing out…</> : "Sign out"}
            </button>
            {logOut.isError && (
              <p className="inline-error ac-identity-error" role="alert">Couldn't sign out. Try again.</p>
            )}
          </div>
          <TeamPanel signedIn />
        </>
      )}

      {session.data && !signedIn && (
        <>
          <div className="ac-card ac-howto">
            <p className="ac-eyebrow">How it works</p>
            <ol className="ac-steps" aria-label="How to use this page">
              {steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </div>

          <div className="ac-card ac-signin">
            <form className="ac-form" onSubmit={handleSubmit} noValidate>
              <div>
                <h3 className="ac-card-title">Sign in</h3>
                <p className="ac-muted">Your account connects you to your team.</p>
              </div>

              <div className="ac-field">
                <label htmlFor="account-email" className="ac-label">Email</label>
                <input
                  id="account-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  spellCheck={false}
                  placeholder="you@example.com"
                />
              </div>

              <div className="ac-field">
                <label htmlFor="account-password" className="ac-label">Password</label>
                <PasswordInput
                  id="account-password"
                  value={password}
                  onChange={setPassword}
                  autoComplete="current-password"
                />
              </div>

              {formError && <p className="inline-error" role="alert">{formError}</p>}
              {signIn.error && !formError && (
                <p className="inline-error" role="alert">{authErrorMessage(signIn.error)}</p>
              )}

              <button type="submit" className="ac-btn ac-btn-primary" disabled={signIn.isPending}>
                {signIn.isPending ? <><Spinner />Signing in…</> : "Sign in"}
              </button>
            </form>
          </div>
        </>
      )}
    </section>
  );
}
