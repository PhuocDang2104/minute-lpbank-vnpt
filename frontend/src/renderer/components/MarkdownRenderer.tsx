import { useMemo } from 'react';
import { renderMarkdownToHtml } from '../lib/markdown';

interface MarkdownRendererProps {
  content: string;
  className?: string;
  includeChapterAnchors?: boolean;
}

export const MarkdownRenderer = ({ content, className, includeChapterAnchors = false }: MarkdownRendererProps) => {
  const html = useMemo(() => {
    return renderMarkdownToHtml(content, { includeChapterAnchors });
  }, [content, includeChapterAnchors]);

  return <div className={className} dangerouslySetInnerHTML={{ __html: html }} />;
};
