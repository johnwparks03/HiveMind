import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

// Local-only for now: agent reachability. Signed-in and relay state arrive with the central service (Feature_List 2.4).
export default function StatusIndicator() {
  const { data: online, isPending } = useQuery({
    queryKey: ["agent-status"],
    queryFn: api.ping,
    refetchInterval: 15000,
  });

  const state = isPending ? "checking" : online ? "online" : "offline";
  const label = { checking: "Checking agent", online: "Agent connected", offline: "Agent offline" }[state];

  return (
    <div className="status" role="status">
      <span className={`dot dot-${state}`} aria-hidden="true" />
      {label}
    </div>
  );
}
