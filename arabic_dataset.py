"""
Synthetic Arabic Text Dataset Generator for Phase-1 Training.

This module generates a clean, noise-free dataset of Arabic text images
for training the ControlNet model. The dataset is fully controlled and
designed to teach the model correct Arabic glyph rendering.

Key features:
- Multiple fonts (system Arabic fonts)
- Multiple sizes
- High contrast
- Centered text
- Clean backgrounds
"""

from __future__ import annotations

import os
import random
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:
    arabic_reshaper = None
    get_display = None


class ArabicDatasetGenerator:
    """
    Generates synthetic Arabic text images for training.
    
    This generator creates clean, high-quality images with Arabic text
    rendered using various fonts and sizes. The goal is to provide
    a controlled dataset that teaches the model correct Arabic rendering.
    """
    
    def __init__(
        self,
        output_dir: str = "arabic_dataset",
        image_size: Tuple[int, int] = (512, 512),
        fonts: Optional[List[str]] = None,
        font_sizes: Optional[List[int]] = None,
    ):
        """
        Initialize the dataset generator.
        
        Args:
            output_dir: Directory to save generated images
            image_size: (width, height) of output images
            fonts: List of font paths or names (None = auto-detect)
            font_sizes: List of font sizes to use (None = default range)
        """
        if Image is None or ImageDraw is None or ImageFont is None:
            raise ImportError("PIL (Pillow) is required. Install with: pip install Pillow")
        
        if arabic_reshaper is None or get_display is None:
            raise ImportError(
                "arabic_reshaper and python-bidi are required. "
                "Install with: pip install arabic-reshaper python-bidi"
            )
        
        self.output_dir = Path(output_dir)
        self.image_size = image_size
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Auto-detect Arabic fonts if not provided
        if fonts is None:
            self.fonts = self._detect_arabic_fonts()
        else:
            self.fonts = fonts
        
        if font_sizes is None:
            # Default font sizes for 512x512 images
            self.font_sizes = [32, 40, 48, 56, 64, 72, 80]
        else:
            self.font_sizes = font_sizes
        
        if not self.fonts:
            raise RuntimeError(
                "No Arabic fonts found. Please install Arabic fonts on your system "
                "or provide font paths manually."
            )
    
    def _detect_arabic_fonts(self) -> List[str]:
        """
        Detect available Arabic fonts on the system.
        
        Returns:
            List of font paths or names
        """
        fonts = []
        
        # Common Arabic font names
        common_arabic_fonts = [
            "Arial",  # Windows/Linux
            "DejaVu Sans",  # Linux
            "Noto Sans Arabic",  # Linux
            "Tahoma",  # Windows
            "Times New Roman",  # Windows (supports Arabic)
            "Segoe UI",  # Windows
        ]
        
        for font_name in common_arabic_fonts:
            try:
                # Try to load the font
                font = ImageFont.truetype(font_name, 12)
                fonts.append(font_name)
            except (OSError, IOError):
                # Try alternative paths
                pass
        
        # Try system font directories
        system_font_dirs = []
        if os.name == "nt":  # Windows
            system_font_dirs = [
                os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts"),
            ]
        elif os.name == "posix":  # Linux/Mac
            system_font_dirs = [
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                os.path.expanduser("~/.fonts"),
            ]
        
        for font_dir in system_font_dirs:
            if os.path.exists(font_dir):
                for font_file in Path(font_dir).rglob("*.ttf"):
                    try:
                        font = ImageFont.truetype(str(font_file), 12)
                        fonts.append(str(font_file))
                        if len(fonts) >= 5:  # Limit to 5 fonts
                            break
                    except (OSError, IOError):
                        continue
        
        return fonts if fonts else ["arial.ttf"]  # Fallback
    
    def _prepare_arabic_text(self, text: str) -> str:
        """
        Prepare Arabic text for rendering (shaping + bidi).
        
        Args:
            text: Raw Arabic text
            
        Returns:
            Properly shaped and bidi-ordered text
        """
        reshaped = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped)
        return bidi_text
    
    def _render_text(
        self,
        text: str,
        font_path: str,
        font_size: int,
        text_color: Tuple[int, int, int] = (0, 0, 0),
        bg_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> Image.Image:
        """
        Render Arabic text onto an image.
        
        Args:
            text: Arabic text to render
            font_path: Path to font file or font name
            font_size: Font size in pixels
            text_color: RGB text color
            bg_color: RGB background color
            
        Returns:
            PIL Image with rendered text
        """
        # Prepare text
        prepared_text = self._prepare_arabic_text(text)
        
        # Create image
        img = Image.new("RGB", self.image_size, bg_color)
        draw = ImageDraw.Draw(img)
        
        # Load font
        try:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
            else:
                font = ImageFont.truetype(font_path, font_size)
        except (OSError, IOError):
            # Fallback to default font
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except (OSError, IOError):
                font = ImageFont.load_default()
        
        # Get text bounding box
        bbox = draw.textbbox((0, 0), prepared_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text
        x = (self.image_size[0] - text_width) // 2
        y = (self.image_size[1] - text_height) // 2
        
        # Draw text
        draw.text((x, y), prepared_text, fill=text_color, font=font)
        
        return img
    
    def generate_image(
        self,
        arabic_word: str,
        font_path: Optional[str] = None,
        font_size: Optional[int] = None,
        text_color: Optional[Tuple[int, int, int]] = None,
        bg_color: Optional[Tuple[int, int, int]] = None,
    ) -> Image.Image:
        """
        Generate a single Arabic text image.
        
        Args:
            arabic_word: Arabic word to render
            font_path: Font to use (None = random)
            font_size: Font size (None = random)
            text_color: Text color (None = black)
            bg_color: Background color (None = white)
            
        Returns:
            PIL Image with rendered Arabic text
        """
        if font_path is None:
            font_path = random.choice(self.fonts)
        if font_size is None:
            font_size = random.choice(self.font_sizes)
        if text_color is None:
            text_color = (0, 0, 0)  # Black
        if bg_color is None:
            bg_color = (255, 255, 255)  # White
        
        return self._render_text(arabic_word, font_path, font_size, text_color, bg_color)
    
    def generate_dataset(
        self,
        arabic_words: List[str],
        images_per_word: int = 10,
        progress_callback: Optional[callable] = None,
    ) -> List[Tuple[str, str]]:
        """
        Generate a complete dataset of Arabic text images.
        
        Args:
            arabic_words: List of Arabic words to render
            images_per_word: Number of variations per word
            progress_callback: Optional callback(progress, total) for progress updates
            
        Returns:
            List of (image_path, label) tuples
        """
        dataset = []
        total = len(arabic_words) * images_per_word
        current = 0
        
        # Create images directory
        images_dir = self.output_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Create labels file
        labels_file = self.output_dir / "labels.txt"
        
        for word_idx, word in enumerate(arabic_words):
            for variant in range(images_per_word):
                # Randomize font and size
                font = random.choice(self.fonts)
                size = random.choice(self.font_sizes)
                
                # Generate image
                img = self.generate_image(word, font_path=font, font_size=size)
                
                # Save image
                img_filename = f"word_{word_idx:04d}_var_{variant:03d}.png"
                img_path = images_dir / img_filename
                img.save(img_path)
                
                # Store metadata
                dataset.append((str(img_path), word))
                
                current += 1
                if progress_callback:
                    progress_callback(current, total)
        
        # Save labels file
        with open(labels_file, "w", encoding="utf-8") as f:
            for img_path, label in dataset:
                f.write(f"{img_path}\t{label}\n")
        
        print(f"Generated {len(dataset)} images in {self.output_dir}")
        print(f"Labels saved to {labels_file}")
        
        return dataset


def generate_phase1_dataset(
    vocabulary: List[str],
    output_dir: str = "arabic_dataset_phase1",
    images_per_word: int = 10,
) -> str:
    """
    Convenience function to generate Phase-1 Arabic dataset.
    
    Args:
        vocabulary: List of Arabic words (100-500 words for Phase-1)
        output_dir: Output directory
        images_per_word: Number of image variations per word
        
    Returns:
        Path to generated dataset directory
    """
    generator = ArabicDatasetGenerator(output_dir=output_dir)
    dataset = generator.generate_dataset(vocabulary, images_per_word=images_per_word)
    return str(generator.output_dir)
