// A password field with an eye toggle at the far right. The eye only appears once something is typed.
// The field is a text input masked with CSS rather than type="password", because browsers add their
// own reveal icon to password inputs, and that icon can't be styled or reliably hidden.
import { useState } from "react";

export default function PasswordInput({ id, value, onChange, autoComplete }) {
  // Each field keeps its own shown/hidden state, so its eye doesn't affect the other field.
  const [shown, setShown] = useState(false);

  return (
    <div className="password-field">
      <input
        id={id}
        type="text"
        className={shown ? "password-input" : "password-input is-masked"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        autoComplete={autoComplete}
        autoCapitalize="off"
        autoCorrect="off"
        spellCheck={false}
      />
      {value && (
        <button
          type="button"
          className="reveal-toggle"
          aria-pressed={shown}
          aria-label={shown ? "Hide password" : "Show password"}
          title={shown ? "Hide password" : "Show password"}
          onClick={() => setShown((s) => !s)}
        >
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">
            <path
              d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="2" />
            {shown && <path d="M3 3l18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />}
          </svg>
        </button>
      )}
    </div>
  );
}
