// What users are told when they make files public. Publishing now uploads a file's text so teammates'
// searches and Ask can use it (E6), so every place that asks for the decision says so. Pure helpers,
// so the wording can be tested with `node --test`.

// For a button's tooltip, where a single file is meant.
export const SHARE_CONSENT_ONE = "Teammates will be able to read this file's contents, including when they use Ask.";

export function shareConfirmText(count) {
  const noun = count === 1 ? "file" : "files";
  const their = count === 1 ? "its" : "their";
  return `Make ${count} ${noun} public? Teammates will be able to read ${their} contents, including when they use Ask.`;
}

export function unshareConfirmText(count) {
  const noun = count === 1 ? "file" : "files";
  const them = count === 1 ? "it" : "them";
  return `Make ${count} public ${noun} private? Teammates will no longer be able to read ${them}.`;
}

export function unshareFolderConfirmText(folderName) {
  return `Make all public files in ${folderName} private? Teammates will no longer be able to read them.`;
}
