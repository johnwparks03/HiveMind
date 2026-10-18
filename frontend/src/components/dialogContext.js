import { createContext, useContext } from "react";

export const DialogContext = createContext(null);

// HiveMind's own replacement for window.confirm and window.alert. Both return a promise:
//   const ok = await confirm({ title, message, confirmLabel, danger });  // true or false
//   await alert({ title, message });
export function useDialog() {
  const value = useContext(DialogContext);
  if (!value) throw new Error("useDialog must be used inside <DialogProvider>");
  return value;
}
