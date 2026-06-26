"""Markdown chunking for rule-doc ingestion.

Splits a state rule doc into retrieval chunks at markdown headings, keeping each heading with
its body so a retrieved chunk reads as a self-contained, citable rule section.
"""

from __future__ import annotations

import re

_HEADING_RE = re.compile(r"^#{1,6}\s+.*$", re.MULTILINE)


def chunk_markdown(body_md: str) -> list[str]:
    """Return non-empty chunks, one per heading section (preamble before the first
    heading becomes its own chunk)."""
    text = body_md.strip()
    if not text:
        return []

    boundaries = [m.start() for m in _HEADING_RE.finditer(text)]
    if not boundaries:
        return [text]

    # Include any preamble before the first heading.
    cut_points = ([0] if boundaries[0] != 0 else []) + boundaries + [len(text)]
    chunks: list[str] = []
    for start, end in zip(cut_points, cut_points[1:], strict=False):
        section = text[start:end].strip()
        if section:
            chunks.append(section)
    return chunks
