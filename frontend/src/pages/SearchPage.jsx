import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { api, isAgentUnreachable } from "../api/client";
import ResultCard from "../components/ResultCard";
import { interpretedCaption } from "../lib/files";

const EXAMPLES = [
  "budget plan from last week",
  "meeting notes from 3 days ago",
  "roadmap deck from March",
];

export default function SearchPage() {
  const [text, setText] = useState("");
  const search = useMutation({ mutationFn: api.search });

  function run(query) {
    const q = query.trim();
    if (!q) return;
    setText(q);
    search.mutate(q);
  }

  function handleSubmit(e) {
    e.preventDefault();
    run(text);
  }

  const results = search.data;

  return (
    <section className="search-page" aria-labelledby="search-title">
      <h2 id="search-title" className="page-title">Find a file</h2>
      <p className="page-lede">Describe what you need in plain words. Dates like "last week" work.</p>

      <form className="search-form" role="search" onSubmit={handleSubmit}>
        <label htmlFor="search-input" className="sr-only">Search your files</label>
        <input
          id="search-input"
          type="search"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="e.g. budget plan from last week"
          autoComplete="off"
        />
        <button type="submit" className="btn btn-primary" disabled={search.isPending || !text.trim()}>
          {search.isPending ? "Searching…" : "Search"}
        </button>
      </form>

      <div aria-live="polite">
        {search.isError && (
          <div className="banner banner-error" role="alert">
            {isAgentUnreachable(search.error)
              ? "Can't reach the local agent. Start it on port 8420, then try again."
              : `Search failed: ${search.error.message}`}
          </div>
        )}

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

        {results && (
          <>
            <p className="caption">{interpretedCaption(results.interpreted)}</p>
            <p className="result-count">
              {results.local_results.length} {results.local_results.length === 1 ? "result" : "results"} · your files only
            </p>
            {results.local_results.length === 0 ? (
              <div className="empty">
                <p>No files matched.</p>
                <p className="muted">Check that the folder has finished indexing on the Files page, or try a broader topic.</p>
              </div>
            ) : (
              <div className="result-list">
                {results.local_results.map((r) => (
                  <ResultCard key={r.file_id} result={r} />
                ))}
              </div>
            )}
            <p className="footnote">Teammate search isn't available yet. Only your own files are searched.</p>
          </>
        )}
      </div>
    </section>
  );
}
