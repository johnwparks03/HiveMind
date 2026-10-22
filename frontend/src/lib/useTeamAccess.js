import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

export const TEAM_REQUIRED_HINT = "Join a team to search their files";

// Whether the user is on a team, so teammate-search controls can be disabled otherwise.
// Shares the ["session"] and ["group"] queries with the Account page.
export function useHasTeam() {
  const session = useQuery({ queryKey: ["session"], queryFn: api.getSession, refetchInterval: 15000 });
  const signedIn = Boolean(session.data?.signed_in);
  const group = useQuery({ queryKey: ["group"], queryFn: api.getGroup, enabled: signedIn });
  return signedIn && Boolean(group.data);
}
