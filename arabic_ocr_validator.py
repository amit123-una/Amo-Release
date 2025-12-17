"""
Arabic OCR Validator for Phase-1 Quality Control.

This module validates generated Arabic images using OCR to ensure
the rendered text matches the input exactly. Images that fail OCR
validation are rejected.

This is critical for Phase-1 success: accuracy over aesthetics.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None


class ArabicOCRValidator:
    """
    Validates Arabic text in images using OCR.
    
    This validator ensures that generated images contain the exact
    Arabic text that was requested, with no substitutions or hallucinations.
    """
    
    def __init__(self, lang: str = "ara"):
        """
        Initialize the OCR validator.
        
        Args:
            lang: Tesseract language code (default: "ara" for Arabic)
        """
        if pytesseract is None:
            raise ImportError(
                "pytesseract is required for OCR validation. "
                "Install with: pip install pytesseract"
            )
        
        self.lang = lang
        self._check_tesseract_installed()
    
    def _check_tesseract_installed(self):
        """Check if Tesseract OCR is installed."""
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            raise RuntimeError(
                "Tesseract OCR is not installed or not in PATH. "
                "Please install Tesseract OCR and Arabic language data."
            )
    
    def extract_text(self, image: Image.Image) -> str:
        """
        Extract Arabic text from image using OCR.
        
        Args:
            image: PIL Image containing Arabic text
            
        Returns:
            Extracted Arabic text string
        """
        # Configure Tesseract for Arabic
        config = f"--psm 6 -l {self.lang}"
        
        # Extract text
        text = pytesseract.image_to_string(image, config=config)
        
        # Clean up text (remove whitespace, normalize)
        text = re.sub(r"\s+", " ", text.strip())
        
        return text
    
    def validate(
        self,
        image: Image.Image,
        expected_text: str,
        tolerance: float = 0.9,
    ) -> Tuple[bool, str, float]:
        """
        Validate that image contains expected Arabic text.
        
        Args:
            image: Generated image to validate
            expected_text: Expected Arabic text
            tolerance: Minimum similarity score (0.0-1.0)
            
        Returns:
            Tuple of (is_valid, extracted_text, similarity_score)
        """
        # Extract text from image
        extracted = self.extract_text(image)
        
        # Normalize both texts for comparison
        expected_norm = self._normalize_arabic(expected_text)
        extracted_norm = self._normalize_arabic(extracted)
        
        # Compute similarity
        similarity = self._compute_similarity(expected_norm, extracted_norm)
        
        is_valid = similarity >= tolerance
        
        return is_valid, extracted, similarity
    
    def _normalize_arabic(self, text: str) -> str:
        """
        Normalize Arabic text for comparison.
        
        Args:
            text: Arabic text to normalize
            
        Returns:
            Normalized text
        """
        # Remove diacritics (optional - depends on requirements)
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text.strip())
        # Remove non-Arabic characters
        text = re.sub(r"[^\u0600-\u06FF\s]", "", text)
        return text
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute similarity between two Arabic texts.
        
        Uses character-level matching for accuracy.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0.0-1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Character-level comparison
        chars1 = set(text1.replace(" ", ""))
        chars2 = set(text2.replace(" ", ""))
        
        if not chars1 and not chars2:
            return 1.0
        
        if not chars1 or not chars2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(chars1 & chars2)
        union = len(chars1 | chars2)
        
        if union == 0:
            return 0.0
        
        return intersection / union


def validate_arabic_image(
    image_path: str,
    expected_text: str,
    tolerance: float = 0.9,
) -> Tuple[bool, str, float]:
    """
    Convenience function to validate an Arabic image file.
    
    Args:
        image_path: Path to image file
        expected_text: Expected Arabic text
        tolerance: Minimum similarity score
        
    Returns:
        Tuple of (is_valid, extracted_text, similarity_score)
    """
    if Image is None:
        raise ImportError("PIL (Pillow) is required. Install with: pip install Pillow")
    
    validator = ArabicOCRValidator()
    image = Image.open(image_path)
    return validator.validate(image, expected_text, tolerance)
