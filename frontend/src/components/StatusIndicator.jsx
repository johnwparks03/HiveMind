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
  // Say what it means and what to do, in plain words.
  const label = {
    checking: "Connecting to HiveMind…",
    online: "HiveMind is ready",
    offline: "HiveMind isn't running. Start it, then refresh.",
  }[state];
  const hint = {
    checking: "Checking that HiveMind is running on this computer.",
    online: "HiveMind is running on this computer.",
    offline: "HiveMind isn't responding. Start it again, then refresh this page.",
  }[state];

  return (
    <div className="status" role="status" title={hint}>
      <span className={`dot dot-${state}`} aria-hidden="true" />
      <span className="status-label">{label}</span>
    </div>
  );
}
