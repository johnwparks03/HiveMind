import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, isAgentUnreachable } from "../api/client";
import Loading from "../components/Loading";
import Markdown from "../components/Markdown";
import OpenButton from "../components/OpenButton";
import ScopePicker from "../components/ScopePicker";

const EXAMPLES = [
  "what did we do the last two weeks",
  "give me a breakdown of this sprint",
  "what's the status of the budget plan",
];

// Chat-style Ask: saved conversations on the left, the thread in the middle, the question box below.
export default function AskPage() {
  const queryClient = useQueryClient();
  const [activeId, setActiveId] = useState(null); // null = a new, unsaved chat
  const [text, setText] = useState("");
  const [scopeFileIds, setScopeFileIds] = useState(() => new Set());
  const [pendingQuestion, setPendingQuestion] = useState(null);

  const chats = useQuery({ queryKey: ["chats"], queryFn: api.listChats });
  const chat = useQuery({
    queryKey: ["chat", activeId],
    queryFn: () => api.getChat(activeId),
    enabled: Boolean(activeId),
  });

  // Creates the chat on the first question, then asks inside it. The typed text is kept if this fails.
  const send = useMutation({
    mutationFn: async ({ chatId, question, fileIds }) => {
      const id = chatId ?? (await api.createChat()).chat_id;
      try {
        await api.askInChat(id, question, fileIds);
      } catch (err) {
        // A chat that was created just for this question shouldn't linger empty in the list.
        if (!chatId) await api.deleteChat(id).catch(() => {});
        throw err;
      }
      return id;
    },
    onSuccess: (id) => {
      setActiveId(id);
      setText("");
      setPendingQuestion(null);
      queryClient.invalidateQueries({ queryKey: ["chats"] });
      queryClient.invalidateQueries({ queryKey: ["chat", id] });
    },
    onError: () => setPendingQuestion(null),
  });

  const remove = useMutation({
    mutationFn: (chatId) => api.deleteChat(chatId),
    onSuccess: (_data, chatId) => {
      if (chatId === activeId) setActiveId(null);
      queryClient.removeQueries({ queryKey: ["chat", chatId] });
      queryClient.invalidateQueries({ queryKey: ["chats"] });
    },
  });

  function startNewChat() {
    setActiveId(null);
    setText("");
    send.reset();
  }

  function run(question) {
    const q = question.trim();
    if (!q || send.isPending) return;
    setPendingQuestion(q);
    send.mutate({ chatId: activeId, question: q, fileIds: Array.from(scopeFileIds) });
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
  const showExamples = !activeId && !pendingQuestion;

  return (
    <section className="ask-page" aria-labelledby="ask-title">
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
        <div className="ask-thread" aria-live="polite">
          {showExamples && (
            <div className="ask-empty">
              <h2 className="page-title">Ask about <span className="accent-word">your files</span></h2>
              <p className="page-lede">
                Ask across your files, like a summary of recent notes. This needs an internet connection,
                so there's no offline fallback.
              </p>
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
                {m.sources?.length > 0 && (
                  <ul className="ask-sources" aria-label="Based on these files">
                    {m.sources.map((s) => (
                      <li key={s.file_id} className="ask-source-row">
                        <span>{s.filename}</span>
                        <OpenButton fileId={s.file_id} filename={s.filename} />
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ),
          )}

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
                ? "Can't reach the local agent. Start it on port 8420, then try again."
                : send.error.code === "service_unavailable"
                  ? "Ask needs AWS credentials configured in agent/.env. See the agent README."
                  : `Ask failed: ${send.error.message}. Your question is still in the box.`}
            </div>
          )}
        </div>

        <div className="ask-composer">
          <ScopePicker selectedFileIds={scopeFileIds} onChange={setScopeFileIds} />
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
