import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { api, isAgentUnreachable } from "../api/client";
import HowTo from "../components/HowTo";
import Loading, { Spinner } from "../components/Loading";
import ResultCard from "../components/ResultCard";
import SearchIllustration from "../components/SearchIllustration";
import DownloadFolderControl from "../components/DownloadFolderControl";
import TeammateResultCard from "../components/TeammateResultCard";
import Switch from "../components/Switch";
import { interpretedCaption } from "../lib/files";
import { addRecent, loadRecent, removeRecent, saveRecent } from "../lib/recent";

const EXAMPLES = [
  "budget plan from last week",
  "meeting notes from 3 days ago",
  "roadmap deck from March",
];

export default function SearchPage() {
  const [text, setText] = useState("");
  const [recent, setRecent] = useState(loadRecent);
  const [recentOpen, setRecentOpen] = useState(false);
  const [includeTeammates, setIncludeTeammates] = useState(false);
  const search = useMutation({ mutationFn: ({ query, includeTeammates }) => api.search(query, includeTeammates) });

  function run(query) {
    const q = query.trim();
    if (!q) return;
    setText(q);
    setRecentOpen(false);
    const next = addRecent(recent, q);
    setRecent(next);
    saveRecent(next);
    search.mutate({ query: q, includeTeammates });
  }

  function clearRecent() {
    setRecent([]);
    saveRecent([]);
    setRecentOpen(false);
  }

  function forgetRecent(query) {
    const next = removeRecent(recent, query);
    setRecent(next);
    saveRecent(next);
  }

  function handleSubmit(e) {
    e.preventDefault();
    run(text);
  }

  const results = search.data;

  return (
    <section className="search-page" aria-labelledby="search-title">
      <h2 id="search-title" className="page-title">Find a <span className="accent-word">file</span></h2>
      <p className="page-lede">Describe what you need in plain words.</p>
      <HowTo steps={['Type a topic, or a time like "last week".', 'Press Enter to search.', 'Open the file you need.']} />

      <div className="search-box">
        <form className="search-form" role="search" onSubmit={handleSubmit}>
          <label htmlFor="search-input" className="sr-only">Search your files</label>
          <input
            id="search-input"
            type="search"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onFocus={() => setRecentOpen(true)}
            onClick={() => setRecentOpen(true)}
            onBlur={() => setRecentOpen(false)}
            onKeyDown={(e) => {
              if (e.key === "Escape") setRecentOpen(false);
            }}
            placeholder="e.g. budget plan from last week"
            autoComplete="off"
          />
          <button type="submit" className="btn btn-primary" disabled={search.isPending || !text.trim()}>
            {search.isPending ? <><Spinner />Searching…</> : "Search"}
          </button>
        </form>

        <div className="include-teammates">
          <Switch checked={includeTeammates} onChange={setIncludeTeammates}>
            Also search teammates' public files
          </Switch>
        </div>

        {recentOpen && recent.length > 0 && (
          <div className="recent" aria-label="Recent searches">
            <div className="recent-head">
              <span>Recent</span>
              {/* mousedown is prevented so the search box keeps focus and the click still lands. */}
              <button
                type="button"
                className="recent-clear"
                aria-label="Clear recent searches"
                title="Clear recent searches"
                onMouseDown={(e) => e.preventDefault()}
                onClick={clearRecent}
              >
                ×
              </button>
            </div>
            <ul>
              {recent.map((q) => (
                <li key={q} className="recent-row">
                  <button
                    type="button"
                    className="recent-item"
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => run(q)}
                  >
                    {q}
                  </button>
                  <button
                    type="button"
                    className="recent-remove"
                    aria-label={`Remove ${q} from recent searches`}
                    title="Remove"
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => forgetRecent(q)}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div aria-live="polite">
        {search.isError && (
          <div className="banner banner-error" role="alert">
            {isAgentUnreachable(search.error)
              ? "HiveMind isn't running. Start it, then try again."
              : `Search failed: ${search.error.message}`}
          </div>
        )}

        {search.isPending && <Loading label="Searching your files…" />}

        {!search.isPending && !results && !search.isError && (
          <div className="examples">
            <p className="examples-label">Try one of these</p>
            <div className="example-list">
              {EXAMPLES.map((example) => (
                <button key={example} type="button" className="example-chip" onClick={() => run(example)}>
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}

        {!search.isPending && !results && !search.isError && (
          <div className="search-hero">
            <SearchIllustration />
            <p className="hero-caption">Your notes and documents, found by what they're about.</p>
          </div>
        )}

        {results && (
          <>
            <p className="caption">{interpretedCaption(results.interpreted)}</p>
            <p className="result-count">
              {results.local_results.length} {results.local_results.length === 1 ? "result" : "results"} · your files only
            </p>
            {results.local_results.length === 0 ? (
              <div className="empty">
                <p>No files matched.</p>
                <p className="muted">Check that the folder has finished reading on the Files page, or try a broader topic.</p>
              </div>
            ) : (
              <div className="result-list">
                {results.local_results.map((r) => (
                  <ResultCard key={r.file_id} result={r} />
                ))}
              </div>
            )}
            {results.teammate.searched ? (
              <div className="teammate-section">
                {results.teammate.results.length > 0 && <DownloadFolderControl />}
                <p className="caption">
                  {results.teammate.results.length} teammate {results.teammate.results.length === 1 ? "result" : "results"}
                </p>
                {results.teammate.results.length > 0 ? (
                  <div className="result-list">
                    {results.teammate.results.map((r) => (
                      <TeammateResultCard key={r.file_id} result={r} />
                    ))}
                  </div>
                ) : (
                  <p className="muted">No teammate files matched.</p>
                )}
                <p className="footnote">The owner needs to be online for a download to start.</p>
              </div>
            ) : (
              <p className="footnote">
                {results.teammate.skipped_reason === "no_team"
                  ? "Join a team (see the Team tab) to search teammates' files."
                  : results.teammate.skipped_reason === "central_unavailable"
                  ? "Couldn't reach teammate search just now. Your own files are still shown above."
                  : "Only your own files are searched. Turn on \"Also search teammates' public files\" above to include public files."}
              </p>
            )}
          </>
        )}
      </div>
    </section>
  );
}
