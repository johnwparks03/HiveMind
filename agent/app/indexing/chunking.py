"""Paragraph-aware chunking, falling back to fixed-size windows only for a
single paragraph too long to fit on its own. Feature_List 1.4.

Splitting purely by character count was pooling unrelated sections (different
PPTX slides, different topics in one meeting-notes doc) into a single chunk
whenever the whole document happened to be under CHUNK_SIZE_CHARS — which
diluted a strong, specific match down to a weak one on whole-chunk embedding
(measured: 0.72 similarity for a phrase alone vs. 0.16 once pooled with two
unrelated slides/topics in the same chunk). Keeping natural paragraph/slide
boundaries as the primary chunk unit fixes that directly.
"""
import re

from app.config import CHUNK_OVERLAP_CHARS, CHUNK_SIZE_CHARS

_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")


def _char_window_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    step = chunk_size - overlap
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += step
    return chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    text = text.strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in _PARAGRAPH_SPLIT.split(text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    # Deliberately NOT merging adjacent paragraphs back together, even when
    # several would fit under chunk_size combined — an earlier version of this
    # function did that, and a short multi-slide deck or multi-topic doc just
    # got pooled right back into one chunk, which is the exact dilution this
    # function exists to prevent. One paragraph (or slide) is one chunk; only
    # a single paragraph that's individually too long gets split further.
    chunks: list[str] = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            chunks.append(para)
        else:
            chunks.extend(_char_window_chunks(para, chunk_size, overlap))

    return chunks
