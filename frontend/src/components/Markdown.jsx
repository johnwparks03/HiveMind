import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// Renders model output as markdown. Raw HTML in the text is escaped, not rendered
// (react-markdown's default), which is what we want for LLM output.
const components = {
  a: ({ node: _node, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" />,
};

export default function Markdown({ children }) {
  return (
    <div className="markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {children}
      </ReactMarkdown>
    </div>
  );
}
