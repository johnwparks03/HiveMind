import docxIconUrl from "../assets/icons/file-docx.svg";
import pdfIconUrl from "../assets/icons/file-pdf.svg";
import pptxIconUrl from "../assets/icons/file-pptx.svg";
import textIconUrl from "../assets/icons/file-text.svg";
import { fileTypeOf } from "../lib/files";
import TransferControl from "./TransferControl";

const ICONS = { pdf: pdfIconUrl, docx: docxIconUrl, pptx: pptxIconUrl, txt: textIconUrl, other: textIconUrl };

// A teammate's public file as a row in the team's file list, laid out like FileRow on the Files page.
// The download lives in TransferControl; central returns only whether the owner is online, never who they are.
export default function TeammateFileRow({ file }) {
  const type = fileTypeOf(file.filename);
  return (
    <li className="ac-file">
      <span className={`ac-file-icon is-${type}`} aria-hidden="true"><img src={ICONS[type]} alt="" width="19" height="19" /></span>
      <div className="ac-file-main">
        <div className="ac-file-line">
          <span className="ac-file-name">{file.filename}</span>
          <span className={`pill ${file.owner_online ? "pill-indexed" : "pill-failed"}`}>
            <span className="pill-dot" aria-hidden="true" />
            {file.owner_online ? "Owner online" : "Owner offline"}
          </span>
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
