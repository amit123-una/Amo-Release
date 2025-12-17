"""
Arabic Glyph Encoder for Phase-1 Arabic Text Rendering.

This module implements a lightweight encoder that converts Arabic strings
into sequences of glyph tokens (initial/medial/final/isolated forms).

The encoder uses arabic_reshaper and python-bidi to ensure correct
Arabic character shaping before diffusion conditioning.

This is a visual generation problem, not semantic - we encode glyphs,
not meanings.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:
    arabic_reshaper = None
    get_display = None


class ArabicGlyphEncoder:
    """
    Encodes Arabic text into glyph sequences for visual rendering.
    
    This encoder:
    - Shapes Arabic characters into correct contextual forms
    - Enforces proper RTL display order
    - Outputs glyph tokens that can be used for conditioning
    """
    
    def __init__(self):
        """Initialize the Arabic glyph encoder."""
        if arabic_reshaper is None or get_display is None:
            raise ImportError(
                "arabic_reshaper and python-bidi are required for Arabic encoding. "
                "Install with: pip install arabic-reshaper python-bidi"
            )
    
    def encode(self, text: str) -> Tuple[str, List[str]]:
        """
        Encode Arabic text into shaped glyph sequence.
        
        Args:
            text: Input Arabic text string
            
        Returns:
            Tuple of (shaped_text, glyph_tokens)
            - shaped_text: Properly shaped and bidi-ordered text
            - glyph_tokens: List of individual glyph characters
        """
        if not text:
            return "", []
        
        # Step 1: Reshape Arabic characters into contextual forms
        reshaped = arabic_reshaper.reshape(text)
        
        # Step 2: Apply bidirectional algorithm for RTL display
        bidi_text = get_display(reshaped)
        
        # Step 3: Extract individual glyph tokens
        # Each character in the shaped text is a glyph token
        glyph_tokens = list(bidi_text)
        
        return bidi_text, glyph_tokens
    
    def get_glyph_sequence_length(self, text: str) -> int:
        """
        Get the number of glyph tokens for a given Arabic text.
        
        Args:
            text: Input Arabic text
            
        Returns:
            Number of glyph tokens after shaping
        """
        _, tokens = self.encode(text)
        return len(tokens)
    
    def validate_arabic_text(self, text: str) -> bool:
        """
        Validate that text contains Arabic characters.
        
        Args:
            text: Input text to validate
            
        Returns:
            True if text contains Arabic characters
        """
        # Arabic Unicode ranges
        arabic_pattern = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
        return bool(arabic_pattern.search(text))


def create_encoder() -> Optional[ArabicGlyphEncoder]:
    """
    Factory function to create an Arabic glyph encoder.
    
    Returns:
        ArabicGlyphEncoder instance, or None if dependencies are missing
    """
    try:
        return ArabicGlyphEncoder()
    except ImportError:
        return None
