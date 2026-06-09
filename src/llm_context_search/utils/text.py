from __future__ import annotations

import re


def tokenize(text: str) -> list[str]:
    """Simple tokenizer supporting ASCII and Polish characters."""
    return re.findall(r"[\wąćęłńóśźż]+", text.lower())


def contains_any(text: str, terms: set[str]) -> bool:
    if not text or not terms:
        return False
    text_tokens = set(tokenize(text))
    return bool(text_tokens & terms)
