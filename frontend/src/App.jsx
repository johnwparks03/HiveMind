import { useEffect, useRef, useState } from "react";
import { api } from "./api/client";
import ChatInput from "./components/ChatInput";
import ChatMessage from "./components/ChatMessage";
import FolderBar from "./components/FolderBar";
import StatusDot from "./components/StatusDot";
import "./App.css";

export default function App() {
  const [online, setOnline] = useState(null);
  const [folders, setFolders] = useState([]);
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [showFolders, setShowFolders] = useState(true);
  const scrollRef = useRef(null);

  useEffect(() => {
    api.ping().then(setOnline);
    refreshFolders();
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function refreshFolders() {
    try {
      const data = await api.listFolders();
      setFolders(data.folders);
      setOnline(true);
    } catch {
      setOnline(false);
    }
  }

  async function handleAddFolder(path) {
    setBusy(true);
    try {
      await api.addFolder(path);
      await refreshFolders();
    } catch (err) {
      pushSystemError(`Couldn't add that folder: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleRescan(folderId) {
    setBusy(true);
    try {
      await api.rescanFolder(folderId);
    } catch (err) {
      pushSystemError(`Rescan failed: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleRemoveFolder(folderId) {
    setBusy(true);
    try {
      await api.removeFolder(folderId);
      await refreshFolders();
    } catch (err) {
      pushSystemError(`Couldn't remove that folder: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  function pushSystemError(text) {
    setMessages((prev) => [...prev, { role: "assistant", error: true, text }]);
  }

  async function handleSend(query) {
    setMessages((prev) => [...prev, { role: "user", text: query }]);
    setBusy(true);
    try {
      const result = await api.search(query);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", interpreted: result.interpreted, results: result.local_results },
      ]);
    } catch (err) {
      pushSystemError(
        err.message === "agent_unreachable"
          ? "Can't reach the local agent. Is it running on port 8420?"
          : `Search failed: ${err.message}`
      );
      setOnline(false);
    } finally {
      setBusy(false);
    }
  }

  async function handleOpenFile(fileId) {
    try {
      await api.openFile(fileId);
    } catch (err) {
      pushSystemError(`Couldn't open that file: ${err.message}`);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>HiveMind</h1>
        <div className="header-right">
          <StatusDot online={online} />
          <button className="link-button" onClick={() => setShowFolders((v) => !v)}>
            {showFolders ? "Hide folders" : "Folders"}
          </button>
        </div>
      </header>

      {showFolders && (
        <FolderBar
          folders={folders}
          onAdd={handleAddFolder}
          onRescan={handleRescan}
          onRemove={handleRemoveFolder}
          busy={busy}
        />
      )}

      <main className="chat-scroll" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="empty-state">
            <p>Add a folder above, then ask for something like:</p>
            <p className="example">"budget plan from last week"</p>
          </div>
        )}
        {messages.map((m, i) => (
          <ChatMessage key={i} message={m} onOpenFile={handleOpenFile} />
        ))}
      </main>

      <ChatInput onSend={handleSend} disabled={busy || online === false} />
    </div>
  );
}
