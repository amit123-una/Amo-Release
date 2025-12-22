"""
Prompt parsing utilities for deterministic text rendering.

Responsibilities:
- Extract quoted text segments from the prompt.
- Detect whether the extracted text is Arabic or English.
- Return a cleaned prompt (with quoted text removed) for diffusion.

The diffusion pipeline should use ONLY the cleaned prompt so that
the model focuses on scene / layout, while text is handled
deterministically by our own renderer.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional, Literal

# Simple Unicode-based Arabic detection.
_ARABIC_CHAR_PATTERN = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")

# Match text inside single or double quotes: "..." or '...'
_QUOTED_TEXT_PATTERN = re.compile(r"""(["'])(.+?)\1""", re.DOTALL)

Language = Literal["ar", "en"]


@dataclass
class ParsedPrompt:
    """Structured result of prompt parsing."""

    clean_prompt: str
    text: Optional[str]
    language: Optional[Language]


def _detect_language(text: str) -> Optional[Language]:
    """
    Very lightweight language detection:
    - If any Arabic codepoint is present -> "ar"
    - Else if text contains ASCII letters/digits -> "en"
    - Else -> None
    """
    if not text:
        return None

    if _ARABIC_CHAR_PATTERN.search(text):
        return "ar"

    # Basic heuristic for English / Latin text.
    if re.search(r"[A-Za-z0-9]", text):
        return "en"

    return None


def parse_prompt(prompt: str) -> ParsedPrompt:
    """
    Parse a full prompt and extract any quoted text.

    Example:
        "One billboard with 'سفر إلى المستقبل' at Safa Mall at night"

    Returns:
        ParsedPrompt(
            clean_prompt="One billboard with  at Safa Mall at night",
            text="سفر إلى المستقبل",
            language="ar",
        )

    Notes:
        - If multiple quoted segments exist, we currently take the FIRST
          as the text to render. This keeps behaviour simple and deterministic.
        - Quoted text is removed from the clean_prompt so the diffusion
          model is never asked to generate that text.
    """
    if not prompt:
        return ParsedPrompt(clean_prompt="", text=None, language=None)

    # Find all quoted segments.
    matches = list(_QUOTED_TEXT_PATTERN.finditer(prompt))
    if not matches:
        # No quoted text; return original prompt unchanged.
        return ParsedPrompt(clean_prompt=prompt, text=None, language=None)

    first = matches[0]
    extracted_text = first.group(2).strip()

    # Remove ALL quoted segments from the clean prompt so the model
    # never sees the literal text we want to render ourselves.
    clean_prompt = _QUOTED_TEXT_PATTERN.sub("", prompt).strip()

    # Normalise spaces after removal.
    clean_prompt = re.sub(r"\s{2,}", " ", clean_prompt)

    language = _detect_language(extracted_text)

    return ParsedPrompt(clean_prompt=clean_prompt, text=extracted_text or None, language=language)


__all__ = ["ParsedPrompt", "parse_prompt"]

