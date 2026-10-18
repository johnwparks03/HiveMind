import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import { failureText, isTerminal, startErrorText, statusText, transferPhase } from "../lib/transfer";
import { Spinner } from "./Loading";

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
  const phase = transferPhase({ requestPending: request.isPending, transferId, status });

  function retry() {
    setTransferId(null);
    request.mutate();
  }

  return (
    <div className={className}>
      {phase === "idle" && (
        <button
          type="button"
          className="btn btn-outline btn-sm"
          onClick={() => request.mutate()}
          disabled={disabled}
          title={disabled ? disabledTitle : undefined}
        >
          Download
        </button>
      )}

      {/* One pill from the click until the file is saved, so there is no white button flashing to blue.
          "Requesting..." is also what central reports for a request it has just accepted. */}
      {(phase === "starting" || phase === "working") && (
        <span className="pill pill-pending" role="status">
          <Spinner />
          {phase === "starting" ? statusText("requested") : statusText(status ?? "requested")}
        </span>
      )}

      {phase === "downloaded" && (
        <span className="pill pill-indexed pill-wrap" title={transfer.data.saved_path}>
          Saved to {transfer.data.saved_path}
        </span>
      )}

      {(phase === "failed" || phase === "expired") && (
        <>
          <span className="pill pill-failed pill-wrap">
            {phase === "expired" ? "This download expired before it finished." : failureText(transfer.data.error_code)}
          </span>
          <button type="button" className="btn btn-outline btn-sm" onClick={retry}>
            Retry
          </button>
        </>
      )}

      {request.isError && (
        <p className="inline-error" role="alert">{startErrorText(request.error.code)}</p>
      )}
    </div>
  );
}
