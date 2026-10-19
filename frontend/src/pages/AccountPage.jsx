import Loading, { Spinner } from "../components/Loading";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, isAgentUnreachable } from "../api/client";
import HowTo from "../components/HowTo";

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

  return (
    <section className="account-page" aria-label="Account">
      <div className="account-top">
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
              <h2 className="page-title">Your <span className="accent-word">account</span></h2>
              <div className="account-card signed-in-card">
                <p className="signed-in-text">
                  You are signed in as <strong>{session.data.email}</strong>
                </p>
                <button
                  type="button"
                  className="btn btn-danger"
                  onClick={() => logOut.mutate()}
                  disabled={logOut.isPending}
                >
                  {logOut.isPending ? <><Spinner />Signing out…</> : "Sign out"}
                </button>
                {logOut.isError && (
                  <p className="inline-error" role="alert">Couldn't sign out. Try again.</p>
                )}
              </div>
            </>
          )}

          {session.data && !signedIn && (
            <>
              <h2 className="page-title">Sign <span className="accent-word">in</span></h2>
              <p className="page-lede">Sign in to share with your team. Your files stay on this computer until you choose to share them, and teammates can read the files you make public, including through Ask.</p>
              <HowTo steps={['Sign in with your email and password.', 'Your files stay on this computer until you make them public. Teammates can then read them.', 'Sign out here anytime.']} />

              <div className="account-card">
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
                  <PasswordInput
                    id="account-password"
                    value={password}
                    onChange={setPassword}
                    autoComplete="current-password"
                  />

                  {formError && <p className="inline-error" role="alert">{formError}</p>}
                  {signIn.error && !formError && (
                    <p className="inline-error" role="alert">{authErrorMessage(signIn.error)}</p>
                  )}

                  <button type="submit" className="btn btn-primary" disabled={signIn.isPending}>
                    {signIn.isPending ? <><Spinner />Signing in…</> : "Sign in"}
                  </button>
                </form>
              </div>
            </>
          )}
      </div>

      {signedIn && <TeamPanel signedIn />}
    </section>
  );
}
