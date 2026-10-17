import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, isAgentUnreachable } from "../api/client";
import HowTo from "../components/HowTo";
import Loading from "../components/Loading";
import Markdown from "../components/Markdown";
import OpenButton from "../components/OpenButton";
import ScopePicker from "../components/ScopePicker";
import Switch from "../components/Switch";
import TransferControl from "../components/TransferControl";
import {
  isTeammateSource,
  loadIncludeTeammates,
  saveIncludeTeammates,
  skippedReasonText,
  teammateScopeHint,
} from "../lib/ask";

const EXAMPLES = [
  "what did we do the last two weeks",
  "give me a breakdown of this sprint",
  "what's the status of the budget plan",
];

// sessionStorage can be blocked (private windows, embedded views): then the switch just isn't remembered.
function sessionStore() {
  try {
    return window.sessionStorage;
  } catch {
    return undefined;
  }
}

// The files an answer was based on, collapsed by default so long answers stay readable. A teammate's
// file isn't on this computer, so it offers a download (through the owner's laptop) instead of Open.
// Sources saved before teammates existed have no `source` and count as local.
function Sources({ sources }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="ask-sources-block">
      <button type="button" className="ask-sources-toggle" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        <span className="file-group-chevron" aria-hidden="true">{open ? "▾" : "▸"}</span>
        <span className="file-group-name">Sources used</span>
        <span className="muted file-group-count">{sources.length} file{sources.length === 1 ? "" : "s"}</span>
      </button>
      {open && (
        <ul className="ask-sources" aria-label="Based on these files">
          {sources.map((s) => (
            <li key={s.file_id} className="ask-source-row">
              <span>
                {s.filename}
                {isTeammateSource(s) && <span className="source-badge">Teammate</span>}
              </span>
              {isTeammateSource(s) ? (
                <TransferControl fileId={s.file_id} filename={s.filename} className="ask-transfer" />
              ) : (
                <OpenButton fileId={s.file_id} filename={s.filename} />
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// Chat-style Ask: saved conversations on the left, the thread in the middle, the question box below.
export default function AskPage() {
  const queryClient = useQueryClient();
  const [activeId, setActiveId] = useState(null); // null = a new, unsaved chat
  const [text, setText] = useState("");
  const [scopeFileIds, setScopeFileIds] = useState(() => new Set());
  const [pendingQuestion, setPendingQuestion] = useState(null);
  // Off by default; remembered for this browser session only.
  const [includeTeammates, setIncludeTeammates] = useState(() => loadIncludeTeammates(sessionStore()));
  // Why teammates' files were left out of the latest answer. It comes only with the live answer (it is
  // not saved with the chat), so it is kept here until the next question or another chat is opened.
  const [skippedReason, setSkippedReason] = useState(null);

  const chats = useQuery({ queryKey: ["chats"], queryFn: api.listChats });
  const chat = useQuery({
    queryKey: ["chat", activeId],
    queryFn: () => api.getChat(activeId),
    enabled: Boolean(activeId),
  });

  // Creates the chat on the first question, then asks inside it. The typed text is kept if this fails.
  const send = useMutation({
    mutationFn: async ({ chatId, question, fileIds, includeTeammates: withTeammates }) => {
      const id = chatId ?? (await api.createChat()).chat_id;
      try {
        const { teammateSkippedReason } = await api.askInChat(id, question, fileIds, withTeammates);
        return { id, teammateSkippedReason };
      } catch (err) {
        // A chat that was created just for this question shouldn't linger empty in the list.
        if (!chatId) await api.deleteChat(id).catch(() => {});
        throw err;
      }
    },
    onSuccess: ({ id, teammateSkippedReason }) => {
      setActiveId(id);
      setSkippedReason(teammateSkippedReason);
      setText("");
      setPendingQuestion(null);
      queryClient.invalidateQueries({ queryKey: ["chats"] });
      queryClient.invalidateQueries({ queryKey: ["chat", id] });
    },
    onError: () => {
      setPendingQuestion(null);
      setSkippedReason(null);
    },
  });

  const remove = useMutation({
    mutationFn: (chatId) => api.deleteChat(chatId),
    onSuccess: (_data, chatId) => {
      if (chatId === activeId) {
        setActiveId(null);
        setSkippedReason(null);
      }
      queryClient.removeQueries({ queryKey: ["chat", chatId] });
      queryClient.invalidateQueries({ queryKey: ["chats"] });
    },
  });

  function startNewChat() {
    setActiveId(null);
    setText("");
    setSkippedReason(null);
    send.reset();
  }

  function changeIncludeTeammates(value) {
    setIncludeTeammates(value);
    saveIncludeTeammates(sessionStore(), value);
  }

  function run(question) {
    const q = question.trim();
    if (!q || send.isPending) return;
    setPendingQuestion(q);
    setSkippedReason(null);
    send.mutate({ chatId: activeId, question: q, fileIds: Array.from(scopeFileIds), includeTeammates });
  }

  function handleSubmit(e) {
    e.preventDefault();
    run(text);
  }

  function handleDelete(chatId, title) {
    if (window.confirm(`Delete "${title || "this chat"}"? Its saved messages will be removed.`)) {
      remove.mutate(chatId);
    }
  }

  const messages = activeId ? chat.data?.messages ?? [] : [];
  const skippedText = activeId ? skippedReasonText(skippedReason) : null;
  const scopeHint = teammateScopeHint(includeTeammates, scopeFileIds.size);
  const showExamples = !activeId && !pendingQuestion;

  return (
    <section className={`ask-page${showExamples ? "" : " is-chatting"}`} aria-labelledby="ask-title">
      <aside className="ask-sidebar" aria-label="Saved chats">
        <button type="button" className="btn btn-primary ask-new" onClick={startNewChat}>
          New chat
        </button>

        {chats.isPending && <p className="muted ask-side-note">Loading chats…</p>}
        {chats.data?.length === 0 && <p className="muted ask-side-note">Your chats will show here.</p>}

        <ul className="ask-chat-list">
          {(chats.data ?? []).map((c) => (
            <li key={c.chat_id} className={`ask-chat-item${c.chat_id === activeId ? " is-active" : ""}`}>
              <button
                type="button"
                className="ask-chat-open"
                aria-current={c.chat_id === activeId ? "true" : undefined}
                onClick={() => {
                  setActiveId(c.chat_id);
                  setSkippedReason(null);
                  send.reset();
                }}
              >
                {c.title || "New chat"}
              </button>
              <button
                type="button"
                className="ask-chat-delete"
                aria-label={`Delete ${c.title || "chat"}`}
                title="Delete chat"
                onClick={() => handleDelete(c.chat_id, c.title)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <div className="ask-main">
        <div className={`ask-thread${showExamples ? " is-empty" : ""}`} aria-live="polite">
          {showExamples && (
            <div className="ask-empty">
              <h2 className="page-title">Ask about <span className="accent-word">your files</span></h2>
              <p className="page-lede">
                Ask across your files, like a summary of recent notes. Turn on teammates' files to include what your team has made public.
              </p>
              <HowTo steps={['Pick the files to use (optional).', 'Ask a question in plain words.', 'Read the answer, then open or download its sources.']} />
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
            </div>
          )}

          {activeId && chat.isPending && <Loading label="Opening chat…" />}

          {messages.map((m) =>
            m.role === "user" ? (
              <div key={m.message_id} className="ask-msg ask-msg-user">
                <div className="ask-bubble">{m.content}</div>
              </div>
            ) : (
              <div key={m.message_id} className="ask-msg ask-msg-assistant">
                <div className="ask-bubble ask-answer"><Markdown>{m.content}</Markdown></div>
                {m.sources?.length > 0 && <Sources sources={m.sources} />}
              </div>
            ),
          )}

          {skippedText && !pendingQuestion && <p className="footnote ask-footnote">{skippedText}</p>}

          {pendingQuestion && (
            <>
              <div className="ask-msg ask-msg-user">
                <div className="ask-bubble">{pendingQuestion}</div>
              </div>
              <Loading label="Reading your files and thinking…" />
            </>
          )}

          {send.isError && (
            <div className="banner banner-error" role="alert">
              {isAgentUnreachable(send.error)
                ? "HiveMind isn't running. Start it, then try again."
                : send.error.code === "service_unavailable"
                  ? "Ask isn't set up on this computer yet. Ask whoever set up HiveMind for help."
                  : `Ask failed: ${send.error.message}. Your question is still in the box.`}
            </div>
          )}
        </div>

        <div className="ask-composer">
          <ScopePicker selectedFileIds={scopeFileIds} onChange={setScopeFileIds} />
          <div className="include-teammates ask-teammates">
            <Switch checked={includeTeammates} onChange={changeIncludeTeammates}>
              Also use teammates' public files
            </Switch>
            {scopeHint && <p className="footnote ask-footnote">{scopeHint}</p>}
          </div>
          <form className="ask-form" onSubmit={handleSubmit}>
            <label htmlFor="ask-input" className="sr-only">Ask a question about your files</label>
            <input
              id="ask-input"
              type="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Ask about your files"
              autoComplete="off"
            />
            <button type="submit" className="btn btn-primary" disabled={send.isPending || !text.trim()}>
              {send.isPending ? "Thinking…" : "Send"}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
