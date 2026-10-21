# HiveMind frontend design guide

Visual reference for the React frontend. Source design: Figma file `qOYniV5zEoiPUQ2keXRvYj` ("HiveMind"). Frames: Ask `1:599`, Files `1:796`, Search `1:1139`, logo `1:597`. Implemented 2026-10-18 on branch `feature/figma-redesign`.

The redesign is visual only. `src/api/`, `src/lib/`, queries, handlers and hash routing are unchanged. The source of truth for values is `src/index.css` (tokens) and `src/App.css` (components); this file explains how to use them.

## Tokens (`src/index.css`)
Use the semantic aliases in components. Never hardcode a colour.

| Token | Value | Use |
|---|---|---|
| `--bg` | `#f8f9ff` | page background |
| `--surface` | `#ffffff` | cards, inputs |
| `--surface-tint` | `#eff4ff` | panels (Ask sidebar, composer), step cards, chips |
| `--surface-ribbon` | `#e5eeff` | header ribbon, tab track, quiet buttons |
| `--pill-bg` | `#dce9ff` | status pill, filter chips, selection bar |
| `--accent` / `--accent-hover` | `#8d4b00` / `#825100` | primary buttons, focus, accent text |
| `--accent-tile` | `#ffdcc3` | icon tile, user chat bubble |
| `--on-accent` | `#ffffff` | text on amber |
| `--ink` / `--ink-soft` / `--ink-muted` | `#0b1c30` / `#554336` / `#887364` | text, secondary text, hints |
| `--placeholder` | `#dbc2b0` | placeholder text |
| `--line` | `#dce3f2` | borders and dividers |
| `--ok` `--ok-soft` | `#0f8a5f` / `#e2f5ec` | ready / match |
| `--pending-soft` | `#fff3d4` | reading / owner offline |
| `--error` `--error-soft` | `#ba1a1a` / `#ffe9e6` | errors, failed, destructive |
| `--r-sm/md/lg/xl` | 4 / 8 / 12 / 16px | radii (`--radius` = md) |
| `--shadow-1`, `--shadow-up`, `--shadow-inset` | | card, composer, field shadows |
| `--font-sans`, `--font-mono` | Inter, system mono | text; step numbers, invite code |

Light theme only (`color-scheme: light`); there is no dark mode.

## Typography
Inter 400/500/600/700 (Google Fonts link in `index.html`). Sizes in use: 11px caps labels (600, 0.05em tracking), 12px controls and meta, 13px body/buttons, 14px base, 15px lede, 17px brand and card titles, 28px page H2 (700, -0.025em).

## Components (class names are read by logic; keep them)
- **Header**: `.app-header` (56px, blurred white), `.brand` + `.brand-logo`, `.tabs`/`.tab` (`aria-current="page"` is the white segment), `.header-end` with `.status` (pill; `.dot-online|offline|checking`) and `.account-btn`; `.header-ribbon` is the 8px strip below.
- **Buttons**: `.btn` + `.btn-primary | .btn-outline | .btn-ghost | .btn-danger | .btn-danger-outline | .btn-danger-ghost`, `.btn-sm`. Outline buttons inside `.result-card`, `.file-row`, `.file-group-head`, `.selection-bar` render in the light tint.
- **Pills**: `.pill` + `.pill-indexed | .pill-pending | .pill-failed` (the file `index_state` produces `pill-${state}`; every state needs a style), `.pill-wrap` for long text, `.match` for the match percentage.
- **Switch** (`Switch.jsx`): `.switch`, `.switch-track`, `.switch-thumb`; 32x16 amber when on.
- **Step cards** (`HowTo.jsx`): `.how-to li` with a numbered amber badge from a CSS counter.
- **Cards**: `.result-card` (amber left border on the first local result, none on `.teammate-result-card`), `.file-group` (folder card), `.account-card`, `.add-folder`, `.filter-block`.
- **Dialog**: `.dialog-backdrop`, `.dialog` (amber top border).
- **Inputs**: text/search/email/password share one style; the search box draws its magnifier with a CSS background image.

## Page layouts
- **Search** (`.search-page`): centred column, max 1120px. Search box, teammates switch (`.include-teammates`), "Try" chips (shown before the first search), results, teammate section with the download-folder strip.
- **Ask** (`.ask-page`): grid of a 288px sidebar and the chat card. The page height is `100vh - 112px`; the chat list and `.ask-thread` scroll on their own. `.ask-thread.is-empty` centres the hero (icon tile, H2, step cards, starter chips). The composer (`.ask-composer`) holds `.ask-controls` (scope picker + teammates switch) and `.ask-form` with the Send button inside the field. `is-chatting` and `is-active` are still set by `AskPage.jsx`. Below 720px it stacks and the page scrolls.
- **Files** (`.files-page`): keeps the pre-Figma layout, not the Figma Files frame. A 1200px column with a bordered add-folder card, plain filter chips (dark pill when a status chip is pressed), an optional bordered `.selection-bar`, then one bordered folder bar per `.file-group` with the progress bar beneath it and a bordered `.file-list`. These rules live in the "Files page: previous layout" block in `App.css` and are scoped under `.files-page`, because the Account Team panel shares `.file-group`, `.file-list` and `.file-row` and keeps the card look. Colours still come from the tokens.
- **Account** (`#/account`, `#/groups` redirects here): sign-in or signed-in card on top, then the full-width team section (`TeamPanel`, shown when signed in; invite and members in `.team-columns`, then the public files as a `.file-group` of `TeammateFileRow` rows). Token-only restyle (no Figma frames): `.account-card`, `.team-choices`, `.invite-code`.
- Breakpoints: 720px (Ask stacks, team choices stack) and 640px (header wraps, forms stack).
- Search and Ask stay mounted and are toggled with `hidden` in `App.jsx`; keep that so their state survives tab changes.

## Conventions for new UI
- Reuse tokens and existing classes; add a class rather than renaming one logic depends on (`is-chatting`, `is-empty`, `is-active`, `is-selected`, `pill-*`, `dot-*`, `password-input`/`is-masked`).
- Keep `:focus-visible` outlines, `aria-*` attributes, `role="status"`/`alert`, and reduced-motion support.
- Do not change the dev port (5173 is in the agent's CORS allowlist).

## Assets
Logo: `src/assets/hivemind-logo.png` (64px, shown at 32px). Icons: `src/assets/icons/*.svg` (plus, trash, chat, user, send, scope-folder, chevron-down). To refresh from Figma, call `get_design_context` for the frame and download with `curl -L --ssl-no-revoke` (plain `curl` fails on this machine). Figma asset URLs expire after 7 days.

## In the Figma design but deliberately not built
These have no feature behind them; do not fake them (the Files layout itself was also reverted to the previous one, see Page layouts):
- Files: file table column headers and Modified column, "Local Engine" / "POSIX Local" tags, "Retry OCR", per-folder "Indexed 95%" label (the progress bar is built).
- Search: "Semantic match" strip and "Found N results (x local, y teammates)" line.
- Ask: multiline textarea ("Shift+Enter for newline"); the composer stays a single-line input.
- Starter chips use the existing example queries, not the Figma sample text.
