"""Offline lexical query expansion (WordNet). Adds a few synonyms of the topic's
own words before embedding, to close the gap between a short query and a document's
actual wording — entirely local, no network call at query time, no Bedrock.
"""
import re

import nltk

from app.config import (
    QUERY_EXPANSION_MAX_SYNONYMS_PER_WORD,
    QUERY_EXPANSION_MAX_TOTAL_WORDS,
)

_WORD_RE = re.compile(r"[a-zA-Z]+")
# Short/common words add noise, not signal, once expanded (e.g. "for" has no useful
# synonyms worth searching on).
_MIN_WORD_LENGTH = 4
_STOPWORDS = {
    "from", "with", "about", "regarding", "this", "that", "these", "those",
    "have", "will", "shall", "into", "onto", "over", "under",
}

_wordnet_ready = False


def _ensure_wordnet_data() -> None:
    """Download WordNet once (cached under ~/nltk_data after that); skip the
    network check entirely once it's already there, same reasoning as the
    HF_HUB_OFFLINE fix in embeddings.py — don't retry a network call on every
    single agent startup for data that's already local.
    """
    global _wordnet_ready
    if _wordnet_ready:
        return
    try:
        nltk.data.find("corpora/wordnet")
    except LookupError:
        nltk.download("wordnet", quiet=True)
    try:
        nltk.data.find("corpora/omw-1.4")
    except LookupError:
        nltk.download("omw-1.4", quiet=True)
    _wordnet_ready = True


def expand_topic(topic: str) -> str:
    """Returns `topic` with a handful of WordNet synonyms appended, for use as the
    embedding input. The original `topic` is left untouched by the caller for
    display and for filename-boost matching — only the text handed to the
    embedding model is expanded.
    """
    if not topic:
        return topic

    _ensure_wordnet_data()
    from nltk.corpus import wordnet as wn

    words = _WORD_RE.findall(topic.lower())
    original = set(words)
    extra: list[str] = []

    for word in words:
        if len(extra) >= QUERY_EXPANSION_MAX_TOTAL_WORDS:
            break
        if len(word) < _MIN_WORD_LENGTH or word in _STOPWORDS:
            continue

        synsets = wn.synsets(word)
        if not synsets:
            continue

        # Only the most common sense (WordNet orders synsets roughly by frequency) —
        # pulling from every sense of an ambiguous word ("pitch" as in baseball, tar,
        # musical pitch, a sales pitch) adds noise, not signal.
        found = 0
        for lemma in synsets[0].lemmas():
            name = lemma.name().replace("_", " ").lower()
            if name == word or name in original or name in extra:
                continue
            extra.append(name)
            found += 1
            if found >= QUERY_EXPANSION_MAX_SYNONYMS_PER_WORD:
                break

    if not extra:
        return topic
    return topic + " " + " ".join(extra[:QUERY_EXPANSION_MAX_TOTAL_WORDS])
