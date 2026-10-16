import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import DownloadFolderControl from "../components/DownloadFolderControl";
import { Spinner } from "../components/Loading";
import TeammateResultCard from "../components/TeammateResultCard";
import { api, isAgentUnreachable } from "../api/client";
import { formatDate } from "../lib/files";
import { groupErrorMessage, normaliseInviteCode } from "../lib/groups";

// One group per person for the MVP. Groups live on the central service, so everything here
// needs a sign-in; without one we say so instead of showing errors.
export default function GroupsPage() {
  const queryClient = useQueryClient();
  const session = useQuery({ queryKey: ["session"], queryFn: api.getSession, refetchInterval: 15000 });
  const signedIn = Boolean(session.data?.signed_in);

  const group = useQuery({
    queryKey: ["group"],
    queryFn: api.getGroup,
    enabled: signedIn,
  });

  function refreshGroup() {
    queryClient.invalidateQueries({ queryKey: ["group"] });
  }

  if (session.isPending) return <Shell><p className="muted">Checking sign-in…</p></Shell>;

  if (session.isError) {
    return (
      <Shell>
        <div className="banner banner-error" role="alert">
          {isAgentUnreachable(session.error)
            ? "Can't reach the local agent. Start it on port 8420, then try again."
            : "Couldn't check your sign-in status. Try again in a moment."}
        </div>
      </Shell>
    );
  }

  if (!signedIn) {
    return (
      <Shell lede="Groups are shared with your team, so you need to sign in first.">
        <div className="account-card">
          <p className="signed-in-text">
            <a href="#/account">Go to Sign in</a>
          </p>
        </div>
      </Shell>
    );
  }

  if (group.isPending) return <Shell><p className="muted">Loading your group…</p></Shell>;

  if (group.isError) {
    return (
      <Shell>
        <div className="banner banner-error" role="alert">{groupErrorMessage(group.error)}</div>
      </Shell>
    );
  }

  if (group.data) {
    return (
      <Shell>
        <GroupDetail group={group.data} onChanged={refreshGroup} />
      </Shell>
    );
  }

  return (
    <Shell lede="You're not in a group yet. Create one, or join with an invite code.">
      <CreateGroup onCreated={refreshGroup} />
      <JoinGroup onJoined={refreshGroup} />
    </Shell>
  );
}

function Shell({ lede, children }) {
  return (
    <section className="groups-page" aria-label="Groups">
      <h2 className="page-title">Your <span className="accent-word">group</span></h2>
      {lede && <p className="page-lede">{lede}</p>}
      {children}
    </section>
  );
}

function CreateGroup({ onCreated }) {
  const [name, setName] = useState("");
  const create = useMutation({
    mutationFn: (groupName) => api.createGroup(groupName),
    onSuccess: () => {
      setName("");
      onCreated();
    },
  });

  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = name.trim();
    if (trimmed) create.mutate(trimmed);
  }

  return (
    <div className="account-card">
      <h3 className="section-title">Create a group</h3>
      <form className="account-form" onSubmit={handleSubmit}>
        <label htmlFor="group-name" className="field-label">Group name</label>
        <input id="group-name" type="text" value={name} onChange={(e) => setName(e.target.value)} />
        {create.isError && <p className="inline-error" role="alert">{groupErrorMessage(create.error)}</p>}
        <button type="submit" className="btn btn-primary" disabled={create.isPending || !name.trim()}>
          {create.isPending ? "Creating…" : "Create group"}
        </button>
      </form>
    </div>
  );
}

function JoinGroup({ onJoined }) {
  const [code, setCode] = useState("");
  const join = useMutation({
    mutationFn: (value) => api.joinGroup(value),
    onSuccess: () => {
      setCode("");
      onJoined();
    },
  });

  function handleSubmit(e) {
    e.preventDefault();
    const normalised = normaliseInviteCode(code);
    if (normalised) join.mutate(normalised);
  }

  return (
    <div className="account-card">
      <h3 className="section-title">Join with a code</h3>
      <form className="account-form" onSubmit={handleSubmit}>
        <label htmlFor="group-code" className="field-label">Invite code</label>
        <input
          id="group-code"
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          autoCapitalize="characters"
          spellCheck={false}
          placeholder="XXXX-XXXX"
        />
        {join.isError && <p className="inline-error" role="alert">{groupErrorMessage(join.error)}</p>}
        <button type="submit" className="btn btn-primary" disabled={join.isPending || !code.trim()}>
          {join.isPending ? "Joining…" : "Join group"}
        </button>
      </form>
    </div>
  );
}

function GroupDetail({ group, onChanged }) {
  const queryClient = useQueryClient();
  const [invite, setInvite] = useState(null);
  const [copied, setCopied] = useState(false);
  const members = group.members ?? [];

  const createInvite = useMutation({
    mutationFn: api.createInvite,
    onSuccess: (data) => {
      setInvite(data);
      setCopied(false);
    },
  });

  const leave = useMutation({
    mutationFn: api.leaveGroup,
    onSuccess: () => {
      setInvite(null);
      onChanged();
      queryClient.invalidateQueries({ queryKey: ["session"] });
    },
  });

  function handleLeave() {
    const ok = window.confirm(`Leave ${group.name}? You will stop sharing files with this group.`);
    if (ok) leave.mutate();
  }

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(invite.code);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <>
      <div className="account-card group-card">
        <h3 className="section-title">{group.name}</h3>
        {members.length > 0 && (
          <>
            <p className="field-label members-label">Members ({members.length})</p>
            <ul className="member-list" aria-label="Group members">
              {members.map((m, i) => (
                <li key={m.email ?? i} className="member-row">
                  {m.email ? (
                    <span className="member-email">{m.email}</span>
                  ) : (
                    <span className="member-email muted">Email not available yet</span>
                  )}
                  {m.is_you && <span className="member-you">You</span>}
                </li>
              ))}
            </ul>
          </>
        )}
        <TeamFiles />
        <div className="card-footer">
          {leave.isError && <p className="inline-error" role="alert">{groupErrorMessage(leave.error)}</p>}
          <button type="button" className="btn btn-danger-outline" onClick={handleLeave} disabled={leave.isPending}>
            {leave.isPending ? <><Spinner />Leaving…</> : "Leave group"}
          </button>
        </div>
      </div>

      <div className="account-card">
        <h3 className="section-title">Invite someone</h3>
        {invite ? (
          <>
            <p className="invite-code" aria-label={`Invite code ${invite.code}`}>{invite.code}</p>
            <p className="muted">Valid until {formatDate(invite.expires_at)}. Anyone with this code can join.</p>
            <button type="button" className="btn btn-outline" onClick={copyCode}>
              {copied ? "Copied" : "Copy code"}
            </button>
          </>
        ) : (
          <p className="muted">Create a code and share it. It works for 7 days.</p>
        )}
        {createInvite.isError && (
          <p className="inline-error" role="alert">{groupErrorMessage(createInvite.error)}</p>
        )}
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => createInvite.mutate()}
          disabled={createInvite.isPending}
        >
          {createInvite.isPending ? "Creating code…" : invite ? "Create a new code" : "Create invite code"}
        </button>
      </div>
    </>
  );
}

// Everything the team has shared, newest first (reuses central's no-topic "list
// by recency" search mode — see agent/app/search/search_service.py:list_team_files).
function TeamFiles() {
  const files = useQuery({ queryKey: ["group-files"], queryFn: api.getGroupFiles });

  if (files.isPending) return <p className="muted">Loading shared files…</p>;

  if (files.isError) {
    return (
      <div className="banner banner-error" role="alert">
        {isAgentUnreachable(files.error)
          ? "Can't reach the local agent. Start it on port 8420, then try again."
          : groupErrorMessage(files.error)}
      </div>
    );
  }

  if (files.data.length === 0) {
    return <p className="muted">No files shared yet. Publish one from the Files page.</p>;
  }

  return (
    <>
      <DownloadFolderControl />
      <div className="result-list group-files">
        {files.data.map((file) => (
          <TeammateResultCard key={file.file_id} result={file} />
        ))}
      </div>
    </>
  );
}
