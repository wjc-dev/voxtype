"""Local, provider-independent cleanup for recognized text."""

from __future__ import annotations

import difflib
import os
import re


_CJK_AND_GENERAL_PUNCTUATION = (
    "，。！？；：、…—（）【】〔〕《》〈〉「」『』“”‘’·"
    ",.!?;:\"()[]{}<>~～"
)
_QUESTION_MARKS = "？?"
_TRANSLATE_TO_SPACE = str.maketrans(
    {
        character: " "
        for character in _CJK_AND_GENERAL_PUNCTUATION
        if character not in _QUESTION_MARKS
    }
)
_TRANSLATE_TO_EMPTY = str.maketrans(
    {character: "" for character in _CJK_AND_GENERAL_PUNCTUATION}
)
_PROTECTED_NUMERIC_SEPARATORS = {
    ".": "\ue000",
    ",": "\ue001",
    ":": "\ue002",
}

# Keep this intentionally narrow. Words such as “就是、然后、这个、那个” often
# carry real meaning and deleting them made the optional cleanup look like an
# ASR accuracy regression rather than a presentation preference.
_FILLER = r"(?:嗯+|呃+|额+|唔+|啊+|呐+)"
_BOUNDARY = r"[\s，。！？；：、,.!?;:]+"
_INLINE_BREAKS = re.compile(r"[\r\n\t\v\f\u2028\u2029]+")
_UNSAFE_CONTROLS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]+")


def sanitize_inline_text(text: str) -> str:
    """Make ASR output safe for single-line chat/editor insertion.

    Realtime ASR can occasionally return a line break. Some chat clients treat
    a synthetic newline as the Return key and immediately send the message.
    Voice input must never submit on the user's behalf, so every line/control
    separator is converted to an ordinary space before it reaches AX/CGEvent.
    """
    text = _INLINE_BREAKS.sub(" ", text or "")
    text = _UNSAFE_CONTROLS.sub("", text)
    return re.sub(r"[ \u00a0]+", " ", text).strip()


def _collapse_adjacent_repetitions(text: str) -> str:
    """Collapse obvious stutters while preserving normal repeated characters.

    We deliberately require a repeated unit of at least two characters.  This
    avoids damaging legitimate Chinese such as “人人”“常常”“看看”.
    """
    previous = None
    while text != previous:
        previous = text
        # Only collapse common function-word stutters. Broadly collapsing any
        # repeated character damages legitimate “哈哈哈、666” style content.
        text = re.sub(r"([我你他她它这那就是不有要会能想说的喂])\1{2,}", r"\1", text)
        # Whitespace/punctuation-separated repeated words or short clauses.
        text = re.sub(
            rf"(?<![A-Za-z0-9_])([^\s，。！？；：、,.!?;:]{{2,24}})"
            rf"(?:{_BOUNDARY}\1){{2,}}",
            r"\1",
            text,
        )
        # Immediate repetition, e.g. 你好你好你好. The lazy unit selects the
        # smallest meaningful repeated phrase (minimum length two).
        text = re.sub(r"(.{2,12}?)(?:\1){2,}", r"\1", text)
    return text


def clean_spoken_disfluencies(
    text: str,
    enabled: bool | None = None,
    mode: str | None = None,
) -> str:
    """Remove common Mandarin fillers and clear, adjacent speech stutters.

    The function is deterministic and fast enough to run on every cumulative
    realtime preview.  This keeps the cursor output streaming; it does not wait
    for a second LLM request after the user releases the hotkey.
    """
    text = (text or "").strip()
    # Explicit arguments take precedence over environment variables.  This
    # matters because main.py loads the user's .env at import time, so simply
    # importing main in a test would otherwise pollute os.environ and make
    # `enabled=True` calls silently fail (the env var `DISFLUENCY_FILTER_MODE=off`
    # would override the caller's intent).
    if mode is None and enabled is None:
        mode = os.getenv("DISFLUENCY_FILTER_MODE", "").strip().lower()
    if not mode:
        if enabled is None:
            enabled = os.getenv("DISFLUENCY_FILTER_ENABLED", "false").lower() == "true"
        mode = "conservative" if enabled else "off"
    if mode not in {"off", "fillers", "conservative"}:
        mode = "off"
    if not text or mode == "off":
        return text

    # Remove fillers between a repeated word/phrase: 而且 嗯 而且 -> 而且.
    text = re.sub(
        rf"([^\s，。！？；：、,.!?;:]{{2,16}}){_BOUNDARY}"
        rf"{_FILLER}{_BOUNDARY}\1",
        r"\1",
        text,
    )
    # Filler tokens surrounded by ASR boundaries.
    text = re.sub(
        rf"(^|{_BOUNDARY}){_FILLER}(?=$|{_BOUNDARY})",
        lambda match: " " if match.start() else "",
        text,
    )
    # A filler at the beginning is also common without punctuation: 嗯我觉得…
    text = re.sub(rf"^{_FILLER}(?=[\u3400-\u9fffA-Za-z0-9])", "", text)
    if mode == "conservative":
        text = _collapse_adjacent_repetitions(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def normalize_for_comparison(text: str) -> str:
    """Normalize text for local safety checks without exposing its contents."""
    return re.sub(r"[^\w\u3400-\u9fff]+", "", (text or "").lower())


def is_context_echo(transcript: str, context: str) -> bool:
    """Detect a long ASR hallucination copied from recognition context.

    Short overlaps are intentionally ignored because users may genuinely speak
    a project name from their vocabulary.  This targets the dangerous failure
    mode where silence causes most of ``corpus.text`` to be returned verbatim.
    """
    candidate = normalize_for_comparison(transcript)
    source = normalize_for_comparison(context)
    if len(candidate) < 24 or len(source) < 24:
        return False
    if candidate in source and len(candidate) >= 32:
        return True
    if source in candidate and len(source) >= 32:
        return True
    if len(candidate) >= 48:
        return difflib.SequenceMatcher(
            a=candidate,
            b=source,
            autojunk=False,
        ).ratio() >= 0.78
    return False


def has_sufficient_speech(
    total_audio_ms: float,
    voiced_audio_ms: float,
    minimum_total_ms: float = 280.0,
    minimum_voiced_ms: float = 180.0,
) -> bool:
    """Return whether local audio evidence is sufficient to allow ASR output."""
    return (
        total_audio_ms >= minimum_total_ms
        and voiced_audio_ms >= minimum_voiced_ms
    )


def _protect_numeric_separators(text: str) -> str:
    for separator, placeholder in _PROTECTED_NUMERIC_SEPARATORS.items():
        text = re.sub(
            rf"(?<=\d){re.escape(separator)}(?=\d)",
            placeholder,
            text,
        )
    return text


def _restore_numeric_separators(text: str) -> str:
    for separator, placeholder in _PROTECTED_NUMERIC_SEPARATORS.items():
        text = text.replace(placeholder, separator)
    return text


def format_transcription_text(text: str, mode: str = "auto") -> str:
    """Format ASR text according to the configured punctuation mode.

    Modes:
      - auto: keep provider punctuation unchanged
      - spaces: replace punctuation with spaces, preserve question marks, and
        collapse repeated spaces
      - none: remove punctuation without adding spaces

    Numeric separators surrounded by digits are preserved, so values such as
    ``3.14``, ``1,000`` and ``10:30`` remain intact.
    """
    text = (text or "").strip()
    mode = (mode or "auto").strip().lower()

    if mode == "auto":
        return text
    if mode not in {"spaces", "none"}:
        raise ValueError(f"Unsupported punctuation mode: {mode}")

    text = _protect_numeric_separators(text)
    if mode == "spaces":
        text = text.translate(_TRANSLATE_TO_SPACE)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
    else:
        text = text.translate(_TRANSLATE_TO_EMPTY)

    return _restore_numeric_separators(text).strip()
