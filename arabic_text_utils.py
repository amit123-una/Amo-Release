"""
Arabic text detection and preparation utilities for post-processing.

This module is intentionally small and self-contained so that:
- The core diffusion image generation logic remains unchanged.
- Arabic-related handling can be clearly audited and, if needed, disabled.

All functions here are pure helpers and do NOT call any diffusion APIs directly.
"""

from __future__ import annotations

import os
import re
from typing import Optional, Callable

try:
    import arabic_reshaper  # type: ignore
    from bidi.algorithm import get_display  # type: ignore
except Exception:
    # We deliberately avoid failing hard here so that non-Arabic prompts
    # keep working even if these optional dependencies are missing.
    arabic_reshaper = None  # type: ignore
    get_display = None  # type: ignore


# Precompiled regex for detecting Arabic script characters.
# Covers main Arabic blocks and presentation forms.
_ARABIC_CHAR_PATTERN = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
)


def contains_arabic(text: str) -> bool:
    """
    Return True if the given text contains any Arabic script character.

    Implementation uses Unicode ranges instead of heuristics to avoid
    false positives and to keep behaviour stable across environments.
    """
    if not text:
        return False
    return _ARABIC_CHAR_PATTERN.search(text) is not None


def extract_arabic_text(text: str) -> Optional[str]:
    """
    Extract the exact Arabic substrings from the original prompt.

    - Preserves characters exactly as they appear (no translation, no rewriting).
    - Concatenates multiple Arabic runs with a single space between them.
    - Non‑Arabic characters (Latin letters, quotes, etc.) are dropped from
      the extracted value by design, so the diffusion model is not asked to
      "guess" missing Arabic letters from English context.
    """
    if not text:
        return None

    # Walk through the string and collect contiguous Arabic runs.
    runs = []
    current = []

    for ch in text:
        if _ARABIC_CHAR_PATTERN.match(ch) or ch.isspace():
            # Keep spaces that appear inside Arabic segments to preserve
            # user-provided spacing between Arabic words.
            current.append(ch)
        else:
            if current:
                runs.append("".join(current).strip())
                current = []

    if current:
        runs.append("".join(current).strip())

    # Remove empty pieces and join with a single space.
    runs = [r for r in runs if r]
    if not runs:
        return None

    return " ".join(runs)


def prepare_arabic_for_rendering(text: str) -> str:
    """
    Prepare Arabic text for visual rendering.

    Uses:
    - arabic_reshaper: to shape characters into their correct contextual forms.
    - python-bidi: to enforce proper right-to-left display order.

    If the dependencies are missing, the function returns the original text
    so that the system degrades gracefully instead of failing.
    """
    if not text:
        return text

    # If optional dependencies are not available, fall back gracefully.
    if arabic_reshaper is None or get_display is None:
        print("Arabic rendering libs missing; using raw Arabic text.")
        return text

    try:
        reshaped = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped)
        return bidi_text
    except Exception as exc:
        # Any shaping failure should not break the main pipeline.
        print(f"Arabic text preparation failed, using raw text. Error: {exc}")
        return text


def build_arabic_output_path(original_path: str) -> str:
    """
    Given the original image path (e.g. sample_0003.png),
    return a sibling path for the Arabic-only image:

      sample_0003_arabic.png

    The directory structure is NOT changed.
    """
    directory, filename = os.path.split(original_path)
    name, ext = os.path.splitext(filename)
    arabic_name = f"{name}_arabic{ext or '.png'}"
    return os.path.join(directory, arabic_name)


def log(print_fn: Callable[[str], None], message: str) -> None:
    """
    Small helper to centralise Arabic-related logging with plain print().

    A thin wrapper is useful so that callers can later swap print()
    with another logger if needed without touching business logic.
    """
    try:
        print_fn(message)
    except Exception:
        # Never let logging break the main flow.
        pass



