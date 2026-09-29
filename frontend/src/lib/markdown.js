import { marked } from 'marked';
import DOMPurify from 'dompurify';

marked.setOptions({
  breaks: true, // Convert \n to <br>
  gfm: true, // GitHub Flavored Markdown
});

// Links in answers point at PartSelect / YouTube: open them in a new tab.
DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A') {
    node.setAttribute('target', '_blank');
    node.setAttribute('rel', 'noopener noreferrer');
  }
});

// The assistant's text is model output, so it is sanitised before it is
// injected as HTML.
export function renderMarkdown(text = '') {
  return DOMPurify.sanitize(marked.parse(text));
}
