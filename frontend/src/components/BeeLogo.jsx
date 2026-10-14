// The HiveMind bee. Decorative: the wordmark next to it carries the name, so it's hidden from assistive tech.
// Colours come from the Deloitte palette: Deloitte Green body, charcoal stripes, blue wings.
export default function BeeLogo({ size = 28 }) {
  return (
    <svg
      className="bee-logo"
      viewBox="0 0 40 40"
      width={size}
      height={size}
      aria-hidden="true"
      focusable="false"
    >
      <ellipse cx="16" cy="11" rx="5.5" ry="7.5" transform="rotate(-18 16 11)" fill="#e5f5fc" stroke="#00a3e0" strokeWidth="1.5" />
      <ellipse cx="23" cy="10" rx="5.5" ry="7.5" transform="rotate(18 23 10)" fill="#e5f5fc" stroke="#00a3e0" strokeWidth="1.5" />
      <path d="M31 19 Q33 12 36 10" fill="none" stroke="#282728" strokeWidth="1.5" strokeLinecap="round" />
      <ellipse cx="20" cy="24" rx="11" ry="8" fill="#86bc25" stroke="#282728" strokeWidth="2" />
      <path d="M15 17 V31 M22 16 V32" stroke="#282728" strokeWidth="3" strokeLinecap="round" />
      <circle cx="31" cy="22" r="4" fill="#282728" />
      <circle cx="32.3" cy="21" r="1" fill="#ffffff" />
      <path d="M9 22 L4.5 24 L9 26 Z" fill="#282728" />
    </svg>
  );
}
