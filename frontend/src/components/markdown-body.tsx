'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Props = {
  children: string;
  className?: string;
};

export function MarkdownBody({ children, className }: Props) {
  return (
    <div className={className}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}
