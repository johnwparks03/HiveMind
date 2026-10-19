import { formatDate } from "../lib/files";
import TransferControl from "./TransferControl";

// A teammate's public file as a row in the team's file list, laid out like FileRow on the Files page.
// The download lives in TransferControl; central returns only whether the owner is online, never who they are.
export default function TeammateFileRow({ file }) {
  return (
    <li className="file-row">
      <div className="file-main">
        <div className="file-line">
          <span className="file-name">{file.filename}</span>
          <span className={`pill ${file.owner_online ? "pill-indexed" : "pill-pending"}`}>
            <span className="pill-dot" aria-hidden="true" />
            {file.owner_online ? "Owner online" : "Owner offline"}
          </span>
        </div>
        <div className="file-meta">
          {file.file_created_at && <span>Created {formatDate(file.file_created_at)}</span>}
          {file.file_modified_at && <span>Modified {formatDate(file.file_modified_at)}</span>}
        </div>
      </div>
      <TransferControl
        fileId={file.file_id}
        filename={file.filename}
        disabled={!file.owner_online}
        disabledTitle="The owner needs to be online to send this file"
      />
    </li>
  );
}
