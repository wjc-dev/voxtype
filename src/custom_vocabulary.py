"""Shared user-managed hotwords for every cloud ASR engine."""

from __future__ import annotations

from pathlib import Path

from .runtime_paths import CUSTOM_VOCABULARY_FILE
from .utils.logger import logger


MAX_TERM_CHARACTERS = 64


def load_custom_vocabulary(
    path: Path | None = None,
    *,
    limit: int = 2_000,
) -> list[str]:
    """Load one hotword per line, preserving order and removing duplicates.

    The file intentionally stays plain text so it can be edited, backed up, or
    reviewed without a database. Invalid or excessively long entries are
    ignored instead of making the cloud ASR request fail.
    """

    vocabulary_path = path or CUSTOM_VOCABULARY_FILE
    try:
        lines = vocabulary_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return []

    terms: list[str] = []
    seen: set[str] = set()
    for raw_line in lines:
        term = raw_line.strip()
        if not term or term.startswith("#"):
            continue
        if len(term) > MAX_TERM_CHARACTERS or len(term.split()) > 7:
            logger.warning("忽略不符合热词长度要求的自定义词汇: %r", term)
            continue
        dedupe_key = term.casefold()
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        terms.append(term)
        if len(terms) >= max(0, limit):
            break
    return terms
