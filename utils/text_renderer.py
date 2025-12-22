"""
Deterministic text rendering utilities.

This module renders Arabic and English text into transparent PNGs
using Pillow. It is deliberately simple and configurable, and it
does NOT call any diffusion models.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple, Literal

from PIL import Image, ImageDraw, ImageFont

try:
    import arabic_reshaper  # type: ignore
    from bidi.algorithm import get_display  # type: ignore
except Exception:  # pragma: no cover - optional deps
    arabic_reshaper = None  # type: ignore
    get_display = None  # type: ignore

Language = Literal["ar", "en"]


@dataclass
class TextRenderConfig:
    """Configuration for deterministic text rendering."""

    font_path: Optional[str] = None
    font_size: int = 64
    color: Tuple[int, int, int, int] = (0, 0, 0, 255)  # RGBA
    padding: int = 16
    max_width: Optional[int] = None  # If set, text is constrained to this width


def _load_font(config: TextRenderConfig) -> ImageFont.FreeTypeFont:
    """Load a font with graceful fallbacks."""
    candidates = []
    if config.font_path:
        candidates.append(config.font_path)

    # Reasonable defaults for Windows / general systems.
    candidates.extend(
        [
            "arial.ttf",
            "arialuni.ttf",
            "Tahoma.ttf",
        ]
    )

    last_error: Optional[Exception] = None
    for path in candidates:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, config.font_size)
            # If not a full path, Pillow will search system font dirs.
            return ImageFont.truetype(path, config.font_size)
        except Exception as exc:  # pragma: no cover - environment dependent
            last_error = exc
            continue

    # Final fallback to default font.
    try:
        return ImageFont.load_default()
    except Exception as exc:  # pragma: no cover - extremely unlikely
        raise RuntimeError(f"Unable to load any font; last error: {last_error or exc}") from exc


def _prepare_arabic(text: str) -> str:
    """Apply shaping + bidi to Arabic text, if libraries are available."""
    if not text:
        return text

    if arabic_reshaper is None or get_display is None:
        # Degrade gracefully; caller can still render base text.
        print("[WARN] arabic_reshaper or python-bidi missing; rendering raw Arabic text.")
        return text

    try:
        reshaped = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped)
        return bidi_text
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[WARN] Arabic text preparation failed, using raw text. Error: {exc}")
        return text


def render_text_to_image(
    text: str,
    language: Language,
    config: Optional[TextRenderConfig] = None,
) -> Image.Image:
    """
    Render the given text into a transparent RGBA image.

    For Arabic, applies shaping and right-to-left ordering.
    For English, renders the text as-is (left-to-right).
    """
    if not text:
        raise ValueError("Text to render must be non-empty.")

    cfg = config or TextRenderConfig()
    font = _load_font(cfg)

    if language == "ar":
        prepared_text = _prepare_arabic(text)
    else:
        prepared_text = text

    # Measure text size.
    dummy_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    dummy_draw = ImageDraw.Draw(dummy_img)
    bbox = dummy_draw.textbbox((0, 0), prepared_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    width = text_width + 2 * cfg.padding
    height = text_height + 2 * cfg.padding

    # Respect a maximum width if provided by scaling font down once.
    if cfg.max_width is not None and width > cfg.max_width:
        scale = cfg.max_width / float(width)
        new_font_size = max(10, int(cfg.font_size * scale))
        font = _load_font(TextRenderConfig(font_path=cfg.font_path, font_size=new_font_size))
        bbox = dummy_draw.textbbox((0, 0), prepared_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        width = text_width + 2 * cfg.padding
        height = text_height + 2 * cfg.padding

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    x = cfg.padding
    y = cfg.padding
    draw.text((x, y), prepared_text, font=font, fill=cfg.color)

    return img


__all__ = ["TextRenderConfig", "render_text_to_image"]

