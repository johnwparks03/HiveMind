import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { api, isAgentUnreachable } from "../api/client";
import Loading from "../components/Loading";
import OpenButton from "../components/OpenButton";
import ScopePicker from "../components/ScopePicker";

const EXAMPLES = [
  "what did we do the last two weeks",
  "give me a breakdown of this sprint",
  "what's the status of the budget plan",
];

export default function AskPage() {
  const [text, setText] = useState("");
  const [scopeFileIds, setScopeFileIds] = useState(() => new Set());
  const ask = useMutation({ mutationFn: ({ question, fileIds }) => api.ask(question, fileIds) });

  function run(question) {
    const q = question.trim();
    if (!q) return;
    setText(q);
    ask.mutate({ question: q, fileIds: Array.from(scopeFileIds) });
  }

  function handleSubmit(e) {
    e.preventDefault();
    run(text);
  }

  const result = ask.data;

  return (
    <section className="search-page" aria-labelledby="ask-title">
      <h2 id="ask-title" className="page-title">Ask about <span className="accent-word">your files</span></h2>
      <p className="page-lede">
        Ask a question across multiple files, like a summary of recent notes. This needs an
        internet connection — unlike Search, there's no offline fallback.
      </p>

      <ScopePicker selectedFileIds={scopeFileIds} onChange={setScopeFileIds} />

      <div className="search-box">
        <form className="search-form" onSubmit={handleSubmit}>
          <label htmlFor="ask-input" className="sr-only">Ask a question about your files</label>
          <input
            id="ask-input"
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="e.g. give me a breakdown of what we did the last two weeks"
            autoComplete="off"
          />
          <button type="submit" className="btn btn-primary" disabled={ask.isPending || !text.trim()}>
            {ask.isPending ? "Thinking…" : "Ask"}
          </button>
        </form>
      </div>

      <div aria-live="polite">
        {ask.isError && (
          <div className="banner banner-error" role="alert">
            {isAgentUnreachable(ask.error)
              ? "Can't reach the local agent. Start it on port 8420, then try again."
              : ask.error.code === "service_unavailable"
              ? "Ask needs AWS credentials configured in agent/.env — see the agent README."
              : `Ask failed: ${ask.error.message}`}
          </div>
        )}

        {ask.isPending && <Loading label="Reading your files and thinking…" />}

        {!ask.isPending && !result && !ask.isError && (
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

        {result && (
          <>
            <div className="ask-answer">{result.answer}</div>
            {result.sources.length > 0 && (
              <>
                <p className="caption">Based on these files</p>
                <ul className="ask-sources">
                  {result.sources.map((s) => (
                    <li key={s.file_id} className="ask-source-row">
                      <span>{s.filename}</span>
                      <OpenButton fileId={s.file_id} filename={s.filename} />
                    </li>
                  ))}
                </ul>
              </>
            )}
            <p className="footnote">Only your own local files are used. Teammate content isn't included yet.</p>
          </>
        )}
      </div>
    </section>
  );
}
