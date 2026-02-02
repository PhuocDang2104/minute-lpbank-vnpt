"""
Markdown rendering helpers with basic sanitization.
"""
from typing import Optional, Set, Dict

import bleach
import markdown as md

_ALLOWED_TAGS: Set[str] = set(bleach.sanitizer.ALLOWED_TAGS).union(
    {
        "p",
        "pre",
        "code",
        "hr",
        "br",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "blockquote",
    }
)

_ALLOWED_ATTRIBUTES: Dict[str, Set[str]] = {
    **bleach.sanitizer.ALLOWED_ATTRIBUTES,
    "a": {"href", "title"},
    "td": {"colspan", "rowspan", "align"},
    "th": {"colspan", "rowspan", "align"},
}


def render_markdown_to_html(markdown_text: Optional[str]) -> str:
    """
    Render markdown text to sanitized HTML.

    Supports common extensions (tables, fenced code) and strips unsafe tags.
    """
    if not markdown_text:
        return ""

    html = md.markdown(
        markdown_text,
        extensions=["extra", "sane_lists", "tables", "fenced_code"],
    )
    return bleach.clean(html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRIBUTES, strip=True)
