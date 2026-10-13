// Empty-state artwork for the Search page: two brains trading ideas across a shared document.
// Drawn as single outlines (no overlapping circles, per the Deloitte digital brand rules).
// Decorative only, so it's hidden from assistive tech; the text beside it carries the meaning.

const BRAIN =
  "M -56 8 C -62 -14 -46 -34 -26 -32 C -20 -50 6 -56 14 -40 C 26 -52 50 -40 46 -18 " +
  "C 64 -10 62 14 50 20 C 52 40 32 50 18 42 C 8 54 -18 52 -26 42 C -44 48 -62 34 -56 8 Z";

const FOLDS = [
  "M 4 -40 C -4 -24 6 -12 -2 4",
  "M -30 -6 C -22 -14 -14 -4 -20 6",
  "M 22 -10 C 30 -2 38 -8 36 4",
  "M 26 20 C 34 26 30 34 20 32",
];

function Brain({ transform }) {
  return (
    <g transform={transform}>
      <path d={BRAIN} fill="#eef6dc" stroke="#86bc25" strokeWidth="3" strokeLinejoin="round" />
      {FOLDS.map((d) => (
        <path key={d} d={d} fill="none" stroke="#86bc25" strokeWidth="2" strokeLinecap="round" />
      ))}
    </g>
  );
}

export default function SearchIllustration() {
  return (
    <svg
      className="search-illustration"
      viewBox="0 0 460 200"
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        {/* userSpaceOnUse keeps the head at 10 units; the default scales it with the 3px stroke. */}
        <marker id="hm-arrow" markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto" markerUnits="userSpaceOnUse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#00a3e0" />
        </marker>
      </defs>

      <Brain transform="translate(90 110)" />
      <Brain transform="translate(370 110) scale(-1 1)" />

      {/* Curved arrows: the top one points at the right brain, the bottom one back at the left. */}
      <path
        d="M 166 84 Q 230 28 294 84"
        fill="none"
        stroke="#00a3e0"
        strokeWidth="3"
        strokeLinecap="round"
        markerEnd="url(#hm-arrow)"
      />
      <path
        d="M 294 136 Q 230 192 166 136"
        fill="none"
        stroke="#00a3e0"
        strokeWidth="3"
        strokeLinecap="round"
        markerEnd="url(#hm-arrow)"
      />

      {/* The shared document in the middle. */}
      <g transform="translate(230 110)">
        <rect x="-22" y="-30" width="44" height="60" rx="4" fill="#ffffff" stroke="#282728" strokeWidth="2.5" />
        <path d="M 12 -30 L 22 -20 L 12 -20 Z" fill="#e6e6e6" stroke="#282728" strokeWidth="2" strokeLinejoin="round" />
        <path d="M -12 -12 H 12" stroke="#86bc25" strokeWidth="3" strokeLinecap="round" />
        <path d="M -12 0 H 12" stroke="#282728" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
        <path d="M -12 12 H 12" stroke="#282728" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
        <path d="M -12 22 H 4" stroke="#282728" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
      </g>
    </svg>
  );
}
