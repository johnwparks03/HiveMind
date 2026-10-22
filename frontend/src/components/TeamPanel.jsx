import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import DownloadFolderControl from "./DownloadFolderControl";
import Loading, { Spinner } from "./Loading";
import { useDialog } from "./dialogContext";
import TeammateFileRow from "./TeammateFileRow";
import { api, isAgentUnreachable } from "../api/client";
import { formatDate } from "../lib/files";
import copyIconUrl from "../assets/icons/copy.svg";
import keyIconUrl from "../assets/icons/key-round.svg";
import usersIconUrl from "../assets/icons/users-round.svg";
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
      <Shell>
        <p className="ac-muted">Your team shows up here once you are signed in.</p>
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

  if (group.data) return <GroupDetail group={group.data} onChanged={refreshGroup} />;

  return (
    <Shell>
      <div className="ac-team-intro">
        <h3 className="ac-card-title ac-card-title-lg">Your team starts here</h3>
        <p className="ac-muted ac-muted-lg">Create a team or join one with an invite code. You can belong to only one team.</p>
      </div>
      <div className="ac-choices">
        <CreateGroup onCreated={refreshGroup} />
        <JoinGroup onJoined={refreshGroup} />
      </div>
    </Shell>
  );
}

function Shell({ children }) {
  return (
    <section className="ac-card ac-team" aria-label="Team">
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
    <form className="ac-choice" onSubmit={handleSubmit}>
      <span className="ac-icon-tile ac-icon-tile-sm" aria-hidden="true"><img src={usersIconUrl} alt="" width="20" height="20" /></span>
      <div>
        <h3 className="ac-card-title">Create a team</h3>
        <p className="ac-muted">Start a shared space for your team.</p>
      </div>
      <div className="ac-field">
        <label htmlFor="group-name" className="ac-label">Team name</label>
        <input id="group-name" type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Enter a team name" />
      </div>
      {create.isError && <p className="inline-error" role="alert">{groupErrorMessage(create.error)}</p>}
      <button type="submit" className="ac-btn ac-btn-primary" disabled={create.isPending || !name.trim()}>
        {create.isPending ? <><Spinner />Creating…</> : "Create team"}
      </button>
    </form>
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
    <form className="ac-choice" onSubmit={handleSubmit}>
      <span className="ac-icon-tile ac-icon-tile-sm" aria-hidden="true"><img src={keyIconUrl} alt="" width="20" height="20" /></span>
      <div>
        <h3 className="ac-card-title">Join with a code</h3>
        <p className="ac-muted">Use a code from someone on your team.</p>
      </div>
      <div className="ac-field">
        <label htmlFor="group-code" className="ac-label">Invite code</label>
        <input
          id="group-code"
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          autoCapitalize="characters"
          spellCheck={false}
          placeholder="Enter an invite code"
        />
      </div>
      {join.isError && <p className="inline-error" role="alert">{groupErrorMessage(join.error)}</p>}
      <button type="submit" className="ac-btn ac-btn-primary" disabled={join.isPending || !code.trim()}>
        {join.isPending ? <><Spinner />Joining…</> : "Join team"}
      </button>
    </form>
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
    <>
      <section className="ac-card ac-team" aria-label="Team">
        <div className="ac-team-heading">
          <span className="ac-icon-tile" aria-hidden="true"><img src={usersIconUrl} alt="" width="20" height="20" /></span>
          <div>
            <p className="ac-eyebrow ac-eyebrow-muted">Your team</p>
            <h3 className="ac-team-name">{group.name}</h3>
          </div>
          <div className="ac-leave">
            {leave.isError && <p className="inline-error" role="alert">{groupErrorMessage(leave.error)}</p>}
            <button type="button" className="ac-btn ac-btn-danger-outline" onClick={handleLeave} disabled={leave.isPending}>
              {leave.isPending ? <><Spinner />Leaving…</> : "Leave team"}
            </button>
          </div>
        </div>

        <div className="ac-columns">
          <div className="ac-side">
          <section className="ac-invite" aria-labelledby="invite-heading">
            <div>
              <h4 className="ac-card-title" id="invite-heading">Invite someone</h4>
              <p className="ac-muted">Invite codes last 7 days.</p>
            </div>
            {invite && (
              <div className="ac-code">
                <p className="ac-code-value" aria-label={`Invite code ${invite.code}`}>{invite.code}</p>
                <p>Valid until {formatDate(invite.expires_at)}. Anyone with this code can join.</p>
              </div>
            )}
            {createInvite.isError && (
              <p className="inline-error" role="alert">{groupErrorMessage(createInvite.error)}</p>
            )}
            <div className="ac-actions">
              {invite && (
                <button type="button" className="ac-btn" onClick={copyCode}>
                  <img src={copyIconUrl} alt="" width="16" height="16" />
                  {copied ? "Copied" : "Copy code"}
                </button>
              )}
              <button
                type="button"
                className={invite ? "ac-btn" : "ac-btn ac-btn-primary"}
                onClick={() => createInvite.mutate()}
                disabled={createInvite.isPending}
              >
                {createInvite.isPending ? <><Spinner />Creating code…</> : invite ? "Create a new code" : "Create invite code"}
              </button>
            </div>
          </section>

          <section className="ac-members" aria-labelledby="members-heading">
            <div className="ac-heading-row">
              <h4 className="ac-card-title" id="members-heading">Members</h4>
              <span className="ac-muted">{members.length}</span>
            </div>
            {members.length > 0 && (
              <ul className="ac-member-list" aria-label="Team members">
                {members.map((m, i) => (
                  <li key={m.email ?? i} className="ac-member">
                    <span className={m.email ? "ac-member-avatar" : "ac-member-avatar is-empty"} aria-hidden="true">
                      {m.email ? m.email.charAt(0).toUpperCase() : "–"}
                    </span>
                    <span className={m.email ? "ac-member-email" : "ac-member-email ac-muted"}>
                      {m.email ?? "Email not available yet"}
                    </span>
                    {m.is_you && <span className="ac-you">You</span>}
                  </li>
                ))}
              </ul>
            )}
          </section>
          </div>

          <TeamFiles />
        </div>
      </section>
    </>
  );
}

// Everything the team has shared, newest first (reuses central's no-topic "list
// by recency" search mode — see agent/app/search/search_service.py:list_team_files).
function TeamFiles() {
  const files = useQuery({ queryKey: ["group-files"], queryFn: api.getGroupFiles });

  if (files.isPending) return <section className="ac-files"><Loading label="Loading public files…" /></section>;

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
    <section className="ac-files" aria-label="Public files">
      <div className="ac-heading-row">
        <h3 className="ac-card-title ac-card-title-lg">Public files</h3>
        <span className="ac-muted">
          {files.data.length} file{files.data.length === 1 ? "" : "s"}
        </span>
      </div>
      <DownloadFolderControl />
      {files.data.length === 0 ? (
        <p className="ac-muted">No public files yet. Make one public from the Files page.</p>
      ) : (
        <ul className="ac-file-list">
          {files.data.map((file) => (
            <TeammateFileRow key={file.file_id} file={file} />
          ))}
        </ul>
      )}
    </section>
  );
}
