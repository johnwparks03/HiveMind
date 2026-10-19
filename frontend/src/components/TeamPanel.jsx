import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import DownloadFolderControl from "./DownloadFolderControl";
import Loading, { Spinner } from "./Loading";
import { useDialog } from "./dialogContext";
import TeammateFileRow from "./TeammateFileRow";
import { api, isAgentUnreachable } from "../api/client";
import { formatDate } from "../lib/files";
import { groupErrorMessage, normaliseInviteCode } from "../lib/groups";

// One group per person for the MVP. Groups live on the central service, so everything here
// needs a sign-in; the Account page passes the session state and we say so instead of showing errors.
export default function TeamPanel({ signedIn }) {
  const queryClient = useQueryClient();

  const group = useQuery({
    queryKey: ["group"],
    queryFn: api.getGroup,
    enabled: signedIn,
  });

  function refreshGroup() {
    queryClient.invalidateQueries({ queryKey: ["group"] });
  }

  if (!signedIn) {
    return (
      <Shell lede="Sign in to create or join a team.">
        <div className="account-card">
          <p className="signed-in-text">Your team shows up here once you are signed in.</p>
        </div>
      </Shell>
    );
  }

  if (group.isPending) return <Shell><Loading label="Loading your team…" /></Shell>;

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
    <Shell lede="You're not on a team yet. Create one, or join with an invite code.">
      <div className="team-choices">
        <CreateGroup onCreated={refreshGroup} />
        <JoinGroup onJoined={refreshGroup} />
      </div>
    </Shell>
  );
}

function Shell({ lede, children }) {
  return (
    <section className="groups-page" aria-label="Team">
      <h2 className="page-title">Your <span className="accent-word">team</span></h2>
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
      <h3 className="section-title">Create a team</h3>
      <form className="account-form" onSubmit={handleSubmit}>
        <label htmlFor="group-name" className="field-label">Team name</label>
        <input id="group-name" type="text" value={name} onChange={(e) => setName(e.target.value)} />
        {create.isError && <p className="inline-error" role="alert">{groupErrorMessage(create.error)}</p>}
        <button type="submit" className="btn btn-primary" disabled={create.isPending || !name.trim()}>
          {create.isPending ? <><Spinner />Creating…</> : "Create team"}
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
          {join.isPending ? <><Spinner />Joining…</> : "Join team"}
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

  const { confirm } = useDialog();

  const leave = useMutation({
    mutationFn: api.leaveGroup,
    onSuccess: () => {
      setInvite(null);
      onChanged();
      queryClient.invalidateQueries({ queryKey: ["session"] });
    },
  });

  async function handleLeave() {
    const ok = await confirm({
      title: "Leave team?",
      message: `Leave ${group.name}? You will stop sharing files with this team.`,
      confirmLabel: "Leave",
      danger: true,
    });
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
    <div className="account-card group-card">
      <div className="team-header">
        <h3 className="section-title">{group.name}</h3>
      </div>

      <div className="team-columns">
        <section className="team-invite" aria-labelledby="invite-heading">
          <p className="field-label" id="invite-heading">Invite someone</p>
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
            {createInvite.isPending ? <><Spinner />Creating code…</> : invite ? "Create a new code" : "Create invite code"}
          </button>
        </section>
        <section className="team-members" aria-labelledby="members-heading">
          <p className="field-label" id="members-heading">Members ({members.length})</p>
          {members.length > 0 && (
            <ul className="member-list" aria-label="Team members">
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
          )}
        </section>
      </div>

      <TeamFiles />

      <div className="card-footer">
        {leave.isError && <p className="inline-error" role="alert">{groupErrorMessage(leave.error)}</p>}
        <button type="button" className="btn btn-danger-outline" onClick={handleLeave} disabled={leave.isPending}>
          {leave.isPending ? <><Spinner />Leaving…</> : "Leave team"}
        </button>
      </div>
    </div>
  );
}

// Everything the team has shared, newest first (reuses central's no-topic "list
// by recency" search mode — see agent/app/search/search_service.py:list_team_files).
function TeamFiles() {
  const files = useQuery({ queryKey: ["group-files"], queryFn: api.getGroupFiles });

  if (files.isPending) return <Loading label="Loading public files…" />;

  if (files.isError) {
    return (
      <div className="banner banner-error" role="alert">
        {isAgentUnreachable(files.error)
          ? "HiveMind isn't running. Start it, then try again."
          : groupErrorMessage(files.error)}
      </div>
    );
  }

  return (
    <div className="file-group team-files">
      <div className="file-group-head">
        <span className="file-group-name">Public files</span>
        <span className="muted file-group-count">
          {files.data.length} file{files.data.length === 1 ? "" : "s"}
        </span>
      </div>
      <DownloadFolderControl />
      {files.data.length === 0 ? (
        <p className="muted team-files-empty">No public files yet. Make one public from the Files page.</p>
      ) : (
        <ul className="file-list">
          {files.data.map((file) => (
            <TeammateFileRow key={file.file_id} file={file} />
          ))}
        </ul>
      )}
    </div>
  );
}
