import DOMPurify from 'dompurify';
import { marked } from 'marked';

marked.setOptions({
  gfm: true,
  breaks: true,
});

const stripHtmlTags = (value: string): string => {
  return value.replace(/<[^>]*>/g, '').trim();
};

const escapeHtmlAttribute = (value: string): string => {
  return value.replace(/"/g, '&quot;');
};

export const addChapterAnchors = (html: string): string => {
  return html.replace(/<h([23])([^>]*)>([\s\S]*?)<\/h\1>/gim, (_full, level: string, attrs: string, inner: string) => {
    const title = escapeHtmlAttribute(stripHtmlTags(inner));
    const normalizedAttrs = attrs && attrs.trim().length > 0 ? ` ${attrs.trim()}` : '';

    if (!title) {
      return `<h${level}${normalizedAttrs}>${inner}</h${level}>`;
    }

    return `<h${level}${normalizedAttrs} data-chapter="${title}">${inner}</h${level}>`;
  });
};

export interface RenderMarkdownOptions {
  includeChapterAnchors?: boolean;
}

export const renderMarkdownToHtml = (markdown: string, options: RenderMarkdownOptions = {}): string => {
  const { includeChapterAnchors = false } = options;

  const raw = marked.parse(markdown || '') as string;
  const withAnchors = includeChapterAnchors ? addChapterAnchors(raw) : raw;

  return DOMPurify.sanitize(withAnchors, {
    ADD_ATTR: ['target', 'data-chapter'],
  });
};
