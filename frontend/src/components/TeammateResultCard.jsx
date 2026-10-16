import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import { formatDate } from "../lib/files";

const ERROR_MESSAGES = {
  owner_unresponsive: "The owner didn't respond in time.",
  file_unavailable: "This file is no longer available.",
  upload_failed: "The upload didn't finish in time.",
  download_failed: "The download failed.",
};

const STATUS_LABEL = {
  requested: "Requesting…",
  uploading: "Owner is sending the file…",
  ready: "Starting download…",
  downloading: "Downloading…",
};

const TERMINAL = new Set(["downloaded", "failed", "expired"]);

// A teammate's published file, with a download button (docs/stories BACKLOG.md
// E4-S4/S5). The agent handles the relay/S3 round-trip and polls central itself;
// this just polls the agent's own GET /transfers/{id} every 1.5s, per
// API_Contract.md section 2.6 ("the frontend polls this endpoint"). Owner
// identity is never returned by central, only whether they're currently online.
export default function TeammateResultCard({ result }) {
  const [transferId, setTransferId] = useState(null);

  const request = useMutation({
    mutationFn: () => api.requestTransfer(result.file_id, result.filename),
    onSuccess: (data) => setTransferId(data.transfer_id),
  });

  const transfer = useQuery({
    queryKey: ["transfer", transferId],
    queryFn: () => api.getTransfer(transferId),
    enabled: Boolean(transferId),
    refetchInterval: (query) => (TERMINAL.has(query.state.data?.status) ? false : 1500),
  });

  const status = transfer.data?.status;

  function retry() {
    setTransferId(null);
    request.mutate();
  }

  return (
    <article className="result-card teammate-result-card">
      <div className="result-head">
        <h3 className="result-name">{result.filename}</h3>
        <span className={`pill ${result.owner_online ? "pill-indexed" : "pill-pending"}`}>
          <span className="pill-dot" aria-hidden="true" />
          {result.owner_online ? "Owner online" : "Owner offline"}
        </span>
      </div>

      <dl className="meta">
        {result.file_created_at && (
          <div><dt>Created</dt><dd>{formatDate(result.file_created_at)}</dd></div>
        )}
        {result.file_modified_at && (
          <div><dt>Modified</dt><dd>{formatDate(result.file_modified_at)}</dd></div>
        )}
        {result.expires_at && (
          <div><dt>Expires</dt><dd>{formatDate(result.expires_at)}</dd></div>
        )}
      </dl>

      <div className="transfer-row">
        {!transferId && (
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => request.mutate()}
            disabled={request.isPending || !result.owner_online}
            title={result.owner_online ? undefined : "The owner needs to be online to send this file"}
          >
            Download
          </button>
        )}

        {status === "downloaded" && (
          <span className="pill pill-indexed">Saved to {transfer.data.saved_path}</span>
        )}

        {status === "failed" && (
          <>
            <span className="pill pill-failed">
              {ERROR_MESSAGES[transfer.data.error_code] || "Download failed."}
            </span>
            <button type="button" className="btn btn-outline btn-sm" onClick={retry}>
              Retry
            </button>
          </>
        )}

        {status && !TERMINAL.has(status) && (
          <span className="pill pill-pending">
            <span className="pill-dot" aria-hidden="true" />
            {STATUS_LABEL[status] || status}
          </span>
        )}

        {request.isError && (
          <p className="inline-error" role="alert">
            {request.error.code === "owner_offline"
              ? "The owner just went offline."
              : request.error.code === "not_found"
              ? "This file is no longer available."
              : "Couldn't start the download. Try again."}
          </p>
        )}
      </div>
    </article>
  );
}
