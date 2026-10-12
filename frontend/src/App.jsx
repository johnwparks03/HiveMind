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

  useEffect(() => {
    const onHashChange = () => setTab(tabFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

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
            >
              {t.label}
            </a>
          ))}
        </nav>
        <StatusIndicator />
      </header>

      <main className="page">{tab === "search" ? <SearchPage /> : <FilesPage />}</main>
    </div>
  );
}
