import { useMemo } from 'react';
import { renderMarkdown } from '../lib/markdown';

export function Markdown({ text, className = '' }) {
  const html = useMemo(() => renderMarkdown(text), [text]);
  if (!text) return null;
  return <div className={`md ${className}`} dangerouslySetInnerHTML={{ __html: html }} />;
}
