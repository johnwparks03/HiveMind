import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import { failureText, isTerminal, startErrorText, statusText } from "../lib/transfer";

// Download button and progress for one teammate file (docs/stories BACKLOG.md E4-S4/S5). The agent
// handles the relay/S3 round-trip and polls central itself; this polls the agent's own
// GET /transfers/{id} every 1.5s, per API_Contract.md section 2.6 ("the frontend polls this
// endpoint"). Used by the Search results and the Ask sources, which only know a file id and name.
// `disabled` (with `disabledTitle`) lets a caller that knows the owner is offline grey the button out.
export default function TransferControl({ fileId, filename, disabled = false, disabledTitle, className = "transfer-row" }) {
  const [transferId, setTransferId] = useState(null);

  const request = useMutation({
    mutationFn: () => api.requestTransfer(fileId, filename),
    onSuccess: (data) => setTransferId(data.transfer_id),
  });

  const transfer = useQuery({
    queryKey: ["transfer", transferId],
    queryFn: () => api.getTransfer(transferId),
    enabled: Boolean(transferId),
    refetchInterval: (query) => (isTerminal(query.state.data?.status) ? false : 1500),
  });

  const status = transfer.data?.status;

  function retry() {
    setTransferId(null);
    request.mutate();
  }

  return (
    <div className={className}>
      {!transferId && (
        <button
          type="button"
          className="btn btn-outline btn-sm"
          onClick={() => request.mutate()}
          disabled={request.isPending || disabled}
          title={disabled ? disabledTitle : undefined}
        >
          Download
        </button>
      )}

      {status === "downloaded" && (
        <span className="pill pill-indexed">Saved to {transfer.data.saved_path}</span>
      )}

      {status === "failed" && (
        <>
          <span className="pill pill-failed">{failureText(transfer.data.error_code)}</span>
          <button type="button" className="btn btn-outline btn-sm" onClick={retry}>
            Retry
          </button>
        </>
      )}

      {status && !isTerminal(status) && (
        <span className="pill pill-pending">
          <span className="pill-dot" aria-hidden="true" />
          {statusText(status)}
        </span>
      )}

      {request.isError && (
        <p className="inline-error" role="alert">{startErrorText(request.error.code)}</p>
      )}
    </div>
  );
}
