import { useEffect, useState } from "react";
import StatusIndicator from "./components/StatusIndicator";
import FilesPage from "./pages/FilesPage";
import SearchPage from "./pages/SearchPage";
import "./App.css";

const TABS = [
  { id: "search", label: "Search" },
  { id: "files", label: "Files" },
];

function tabFromHash() {
  const id = window.location.hash.replace("#/", "");
  return TABS.some((t) => t.id === id) ? id : "search";
}

export default function App() {
  const [tab, setTab] = useState(tabFromHash);
  // Bumped when the Search tab is clicked while already on Search, to clear it back to the entry page.
  const [searchKey, setSearchKey] = useState(0);

  useEffect(() => {
    const onHashChange = () => setTab(tabFromHash());
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
        <div className="brand">HiveMind</div>
        <nav className="tabs" aria-label="Main">
          {TABS.map((t) => (
            <a
              key={t.id}
              href={`#/${t.id}`}
              className="tab"
              aria-current={tab === t.id ? "page" : undefined}
              onClick={(e) => handleTabClick(t.id, e)}
            >
              {t.label}
            </a>
          ))}
        </nav>
        <StatusIndicator />
      </header>

      <main className="page">
        {/* Search stays mounted so its query and results survive a trip to Files. */}
        <div hidden={tab !== "search"}>
          <SearchPage key={searchKey} />
        </div>
        {tab === "files" && <FilesPage />}
      </main>
    </div>
  );
}
