import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DialogContext } from "./dialogContext";

// Renders one HiveMind-styled dialog at a time. Escape or a click on the backdrop cancels a confirm
// (resolves false) and closes an alert.
export default function DialogProvider({ children }) {
  const [dialog, setDialog] = useState(null); // { kind, title, message, confirmLabel, danger, resolve }
  const confirmRef = useRef(null);

  const open = useCallback(
    (kind, options) =>
      new Promise((resolve) => {
        setDialog({ kind, ...options, resolve });
      }),
    [],
  );

  const api = useMemo(
    () => ({
      confirm: (options) => open("confirm", options),
      alert: (options) => open("alert", options),
    }),
    [open],
  );

  const close = useCallback(
    (result) => {
      dialog?.resolve(result);
      setDialog(null);
    },
    [dialog],
  );

  useEffect(() => {
    if (!dialog) return undefined;
    const previous = document.activeElement;
    confirmRef.current?.focus();
    function onKey(e) {
      if (e.key === "Escape") close(false);
    }
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      if (previous instanceof HTMLElement) previous.focus();
    };
  }, [dialog, close]);

  return (
    <DialogContext.Provider value={api}>
      {children}
      {dialog && (
        <div className="dialog-backdrop" onMouseDown={(e) => e.target === e.currentTarget && close(false)}>
          <div
            className="dialog"
            role={dialog.kind === "confirm" ? "alertdialog" : "dialog"}
            aria-modal="true"
            aria-labelledby="dialog-title"
            aria-describedby="dialog-message"
          >
            <h2 id="dialog-title" className="dialog-title">
              {dialog.title ?? (dialog.kind === "confirm" ? "Are you sure?" : "HiveMind")}
            </h2>
            <p id="dialog-message" className="dialog-message">{dialog.message}</p>
            <div className="dialog-actions">
              {dialog.kind === "confirm" && (
                <button type="button" className="btn btn-outline" onClick={() => close(false)}>
                  {dialog.cancelLabel ?? "Cancel"}
                </button>
              )}
              <button
                type="button"
                ref={confirmRef}
                className={`btn ${dialog.danger ? "btn-danger" : "btn-primary"}`}
                onClick={() => close(true)}
              >
                {dialog.confirmLabel ?? (dialog.kind === "confirm" ? "Confirm" : "OK")}
              </button>
            </div>
          </div>
        </div>
      )}
    </DialogContext.Provider>
  );
}
