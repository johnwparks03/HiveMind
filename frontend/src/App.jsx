import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import logoUrl from "./assets/hivemind-logo.png";
import userIconUrl from "./assets/icons/user.svg";
import StatusIndicator from "./components/StatusIndicator";
import AccountPage from "./pages/AccountPage";
import AskPage from "./pages/AskPage";
import FilesPage from "./pages/FilesPage";
import SearchPage from "./pages/SearchPage";
import { api } from "./api/client";
import { tabFromHash } from "./lib/tabs";
import "./App.css";

const TABS = [
  { id: "search", label: "Search" },
  { id: "ask", label: "Ask" },
  { id: "files", label: "Files" },
  { id: "account", label: "Sign in" },
];

export default function App() {
  const [tab, setTab] = useState(() => tabFromHash(window.location.hash));
  // Bumped when the Search tab is clicked while already on Search, to clear it back to the entry page.
  const [searchKey, setSearchKey] = useState(0);

  // Same query key as the account page, so signing in or out updates the header straight away.
  const session = useQuery({
    queryKey: ["session"],
    queryFn: api.getSession,
    refetchInterval: 15000,
  });
  const signedIn = Boolean(session.data?.signed_in);

  useEffect(() => {
    const onHashChange = () => {
      const next = tabFromHash(window.location.hash);
      if (window.location.hash === "#/groups") window.history.replaceState(null, "", "#/account");
      setTab(next);
    };
    onHashChange();
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  function handleTabClick(id, e) {
    if (id !== tab) return;
    e.preventDefault();
    if (id === "search") setSearchKey((k) => k + 1);
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <img className="brand-logo" src={logoUrl} alt="" width="32" height="32" />
          <span>HiveMind</span>
        </div>
        <nav className="tabs" aria-label="Main">
          {TABS.map((t) => (
            <a
              key={t.id}
              href={`#/${t.id}`}
              className="tab"
              aria-current={tab === t.id ? "page" : undefined}
              onClick={(e) => handleTabClick(t.id, e)}
            >
              {t.id === "account" && signedIn ? "Sign out" : t.label}
            </a>
          ))}
        </nav>
        <div className="header-end">
          <StatusIndicator />
          <a className="account-btn" href="#/account" aria-label={signedIn ? "Account (signed in)" : "Account"}>
            <img src={userIconUrl} alt="" width="12" height="12" />
          </a>
        </div>
      </header>
      <div className="header-ribbon" aria-hidden="true" />

      <main className="page">
        {/* Search and Ask stay mounted so their query/answer survive a trip to another tab. */}
        <div hidden={tab !== "search"}>
          <SearchPage key={searchKey} />
        </div>
        <div hidden={tab !== "ask"}>
          <AskPage />
        </div>
        {tab === "files" && <FilesPage />}
        {tab === "account" && <AccountPage />}
      </main>
    </div>
  );
}
