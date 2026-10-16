import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

// Per-file publish toggle (docs/stories BACKLOG.md E3-S9). Tags still exist on
// the file record and are used by central search, but aren't shown/edited here
// (2026-10-16: too cluttered) — they're generated automatically on publish.
export default function PublishControl({ file }) {
  const queryClient = useQueryClient();

  function refresh() {
    queryClient.invalidateQueries({ queryKey: ["files"] });
  }

  const publish = useMutation({ mutationFn: () => api.publishFile(file.file_id), onSuccess: refresh });
  const unpublish = useMutation({ mutationFn: () => api.unpublishFile(file.file_id), onSuccess: refresh });
  const retry = useMutation({ mutationFn: () => api.retryPublish(file.file_id), onSuccess: refresh });

  const isPublic = file.public_state === "public";
  const failed = file.publish_state === "failed";
  const working = file.publish_state === "pending";
  const busy = publish.isPending || unpublish.isPending || retry.isPending || working;

  return (
    <div className="publish-control">
      <div className="publish-row">
        {failed ? (
          <>
            <span className="pill pill-failed">Publish failed</span>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => retry.mutate()} disabled={busy}>
              Retry
            </button>
          </>
        ) : (
          <button
            type="button"
            className={`btn btn-sm ${isPublic ? "btn-outline" : "btn-primary"}`}
            onClick={() => (isPublic ? unpublish.mutate() : publish.mutate())}
            disabled={busy}
          >
            {working ? "Working…" : isPublic ? "Unpublish" : "Share with team"}
          </button>
        )}
      </div>

      {(() => {
        const error = publish.error ?? unpublish.error ?? retry.error;
        if (!error) return null;
        const message = error.code === "no_team"
          ? "Join a team first (see the Groups tab) before sharing."
          : "Something went wrong. Try again.";
        return <p className="inline-error" role="alert">{message}</p>;
      })()}
    </div>
  );
}
