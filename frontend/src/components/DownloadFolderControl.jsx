import { Spinner } from "./Loading";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

// Lets the user redirect teammate downloads away from the default (real Windows
// Downloads folder) to a folder of their choice - reuses the same native folder
// dialog as adding a folder to index (api.pickFolder), so there's no second
// picker implementation.
export default function DownloadFolderControl() {
  const queryClient = useQueryClient();
  const folder = useQuery({ queryKey: ["download-folder"], queryFn: api.getDownloadFolder });

  function refresh() {
    queryClient.invalidateQueries({ queryKey: ["download-folder"] });
  }

  const choose = useMutation({
    mutationFn: async () => {
      const path = await api.pickFolder();
      if (path) await api.setDownloadFolder(path);
    },
    onSuccess: refresh,
  });

  const reset = useMutation({ mutationFn: api.resetDownloadFolder, onSuccess: refresh });

  const busy = choose.isPending || reset.isPending;
  const error = choose.error ?? reset.error;

  return (
    <p className="download-folder-control muted">
      Teammate downloads save to <strong>{folder.isPending ? <Spinner /> : folder.data?.path ?? "…"}</strong>.
      <button type="button" className="btn btn-ghost btn-sm" onClick={() => choose.mutate()} disabled={busy}>
        Change
      </button>
      <button type="button" className="btn btn-ghost btn-sm" onClick={() => reset.mutate()} disabled={busy}>
        Use Downloads folder
      </button>
      {error && <span className="inline-error" role="alert">Couldn't update the download folder.</span>}
    </p>
  );
}
