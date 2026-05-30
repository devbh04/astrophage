"use client";

import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  content: string;
}

/**
 * Markdown renderer for assistant messages.
 *
 * The agent is asked to reply in plain markdown (headings, bullets,
 * tables, bold/italic). This component themes the output to match the
 * Astrophage cream/parchment + solar-gold palette and keeps prose
 * readable in chat bubbles.
 */
const components: Components = {
  // Headings — keep them small inside chat bubbles, but visibly heavier.
  h1: ({ children }) => (
    <h1 className="font-headline-md text-lg text-primary mt-3 mb-2 first:mt-0">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="font-headline-md text-base text-primary mt-3 mb-1.5 first:mt-0">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="font-headline-md text-sm text-solar-gold uppercase tracking-wider mt-3 mb-1 first:mt-0">
      {children}
    </h3>
  ),
  h4: ({ children }) => (
    <h4 className="font-nav-label text-[11px] uppercase tracking-widest text-solar-gold mt-2 mb-1 first:mt-0">
      {children}
    </h4>
  ),

  p: ({ children }) => (
    <p className="font-body-md text-[14px] leading-relaxed text-on-surface my-2 first:mt-0 last:mb-0">
      {children}
    </p>
  ),

  strong: ({ children }) => (
    <strong className="font-headline-md text-primary">{children}</strong>
  ),
  em: ({ children }) => (
    <em className="italic text-on-surface-variant">{children}</em>
  ),

  ul: ({ children }) => (
    <ul className="list-disc pl-5 my-2 space-y-1 marker:text-solar-gold/70">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal pl-5 my-2 space-y-1 marker:text-solar-gold/70">
      {children}
    </ol>
  ),
  li: ({ children }) => (
    <li className="font-body-md text-[14px] leading-relaxed text-on-surface">
      {children}
    </li>
  ),

  // Blockquote — used for caveats / cosmic notes.
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-solar-gold/60 pl-3 my-2 italic text-on-surface-variant">
      {children}
    </blockquote>
  ),

  hr: () => (
    <hr className="my-3 border-0 border-t border-dashed border-outline/30" />
  ),

  // Tables — gfm.
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto wobbly-border-sm bg-surface-container-low/60">
      <table className="w-full text-[13px] font-body-md text-on-surface">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-surface-container/60 border-b border-outline/30">
      {children}
    </thead>
  ),
  tr: ({ children }) => (
    <tr className="border-b border-outline/20 last:border-b-0">{children}</tr>
  ),
  th: ({ children }) => (
    <th className="text-left px-3 py-2 font-nav-label text-[10px] uppercase tracking-widest text-solar-gold">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-3 py-2 align-top">{children}</td>
  ),

  // Inline code + code blocks.
  code: ({ inline, className, children, ...rest }: {
    inline?: boolean;
    className?: string;
    children?: React.ReactNode;
  } & React.HTMLAttributes<HTMLElement>) => {
    if (inline) {
      return (
        <code
          className="px-1.5 py-0.5 rounded bg-surface-container-low text-[12.5px] font-mono text-solar-gold"
          {...rest}
        >
          {children}
        </code>
      );
    }
    return (
      <pre className="my-2 p-3 wobbly-border-sm bg-surface-container-low/80 overflow-x-auto">
        <code
          className={`font-mono text-[12px] text-on-surface ${className || ""}`}
          {...rest}
        >
          {children}
        </code>
      </pre>
    );
  },

  // Links — open external in new tab.
  a: ({ href, children }) => (
    <a
      href={href}
      target={href?.startsWith("http") ? "_blank" : undefined}
      rel={href?.startsWith("http") ? "noopener noreferrer" : undefined}
      className="text-solar-gold underline decoration-solar-gold/50 hover:decoration-solar-gold"
    >
      {children}
    </a>
  ),
};

export default function MarkdownProse({ content }: Props) {
  return (
    <div className="font-body-md text-body-md text-on-surface">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
