import { useState } from "react";

export default function FolderBar({ folders, onAdd, onRescan, busy }) {
  const [path, setPath] = useState("");

  function submit(e) {
    e.preventDefault();
    if (!path.trim()) return;
    onAdd(path.trim());
    setPath("");
  }

  return (
    <div className="folder-bar">
      <form onSubmit={submit} className="folder-form">
        <input
          type="text"
          placeholder="C:\Users\you\Documents\some-folder"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          disabled={busy}
        />
        <button type="submit" disabled={busy || !path.trim()}>
          Add folder
        </button>
      </form>
      {folders.length > 0 && (
        <ul className="folder-list">
          {folders.map((f) => (
            <li key={f.folder_id}>
              <span className="folder-path" title={f.path}>{f.path}</span>
              <button className="link-button" onClick={() => onRescan(f.folder_id)} disabled={busy}>
                Rescan
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
