// Three plain numbered steps shown under a page's intro, so a first-time user knows what to do.
export default function HowTo({ steps }) {
  return (
    <ol className="how-to" aria-label="How to use this page">
      {steps.map((step) => (
        <li key={step}>{step}</li>
      ))}
    </ol>
  );
}