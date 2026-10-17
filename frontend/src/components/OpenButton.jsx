import { useMutation } from "@tanstack/react-query";
import { api } from "../api/client";

// Opens the file in its Windows default app via the agent. Shows the error inline, next to the button.
export default function OpenButton({ fileId, filename }) {
  const open = useMutation({ mutationFn: () => api.openFile(fileId) });

  return (
    <div className="open-wrap">
      <button
        type="button"
        className="btn btn-outline btn-sm"
        onClick={() => open.mutate()}
        disabled={open.isPending}
        aria-label={`Open ${filename}`}
      >
        {open.isPending ? "Opening…" : "Open"}
      </button>
      {open.isError && (
        <span className="inline-error" role="alert">
          {open.error.code === "file_missing" ? "This file has been moved or deleted." : "Couldn't open that file"}
        </span>
      )}
    </div>
  );
}
