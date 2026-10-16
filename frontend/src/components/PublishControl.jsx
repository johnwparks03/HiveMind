import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import { Spinner } from "./Loading";

// Per-file publish toggle + tag editor (docs/stories BACKLOG.md E3-S9). Tags are
// editable whether or not the file is public — editing a public file's tags
// queues a re-sync (handled server-side), never extends its expiry.
export default function PublishControl({ file }) {
  const queryClient = useQueryClient();
  const [tagDraft, setTagDraft] = useState("");

  function refresh() {
    queryClient.invalidateQueries({ queryKey: ["files"] });
  }

  const publish = useMutation({ mutationFn: () => api.publishFile(file.file_id), onSuccess: refresh });
  const unpublish = useMutation({ mutationFn: () => api.unpublishFile(file.file_id), onSuccess: refresh });
  const retry = useMutation({ mutationFn: () => api.retryPublish(file.file_id), onSuccess: refresh });
  const setTags = useMutation({ mutationFn: (tags) => api.setTags(file.file_id, tags), onSuccess: refresh });

  const isPublic = file.public_state === "public";
  const failed = file.publish_state === "failed";
  const working = file.publish_state === "pending";
  const busy = publish.isPending || unpublish.isPending || retry.isPending || working;

  function addTag(e) {
    e.preventDefault();
    const tag = tagDraft.trim();
    if (!tag || file.tags.includes(tag)) return;
    setTags.mutate([...file.tags, tag]);
    setTagDraft("");
  }

  function removeTag(tag) {
    setTags.mutate(file.tags.filter((t) => t !== tag));
  }

  return (
    <div className="publish-control">
      <div className="publish-row">
        {failed ? (
          <>
            <span className="pill pill-failed">Publish failed</span>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => retry.mutate()} disabled={busy}>
              {retry.isPending ? <><Spinner />Retrying…</> : "Retry"}
            </button>
          </>
        ) : (
          <button
            type="button"
            className={`btn btn-sm ${isPublic ? "btn-outline" : "btn-primary"}`}
            onClick={() => (isPublic ? unpublish.mutate() : publish.mutate())}
            disabled={busy}
          >
            {unpublish.isPending || (working && isPublic) ? (
              <><Spinner />Unsharing…</>
            ) : publish.isPending || working ? (
              <><Spinner />Sharing…</>
            ) : isPublic ? "Unpublish" : "Share with team"}
          </button>
        )}
        {isPublic && file.tags.length === 0 && <span className="muted no-tags-flag">No tags</span>}
      </div>

      <div className="tag-list">
        {file.tags.map((tag) => (
          <span key={tag} className="tag-chip">
            {tag}
            <button type="button" aria-label={`Remove tag ${tag}`} onClick={() => removeTag(tag)}>
              ×
            </button>
          </span>
        ))}
        <form onSubmit={addTag} className="tag-add-form">
          <input
            type="text"
            value={tagDraft}
            onChange={(e) => setTagDraft(e.target.value)}
            placeholder="+ tag"
            className="tag-input"
          />
        </form>
      </div>

      {(() => {
        const error = publish.error ?? unpublish.error ?? retry.error ?? setTags.error;
        if (!error) return null;
        const message = error.code === "no_team"
          ? "Join a team first (see the Groups tab) before sharing."
          : "Something went wrong. Try again.";
        return <p className="inline-error" role="alert">{message}</p>;
      })()}
    </div>
  );
}
