"""
Quick test script to verify Arabic text extraction is working correctly.
Run this to see what text is being extracted from your prompts.
"""

from arabic_text_utils import (
    contains_arabic,
    extract_arabic_text,
    prepare_arabic_for_rendering,
)

def test_extraction(text: str):
    """Test Arabic text extraction for a given input."""
    print(f"\n{'='*60}")
    print(f"Input text: {repr(text)}")
    print(f"Input text (display): {text}")
    
    has_arabic = contains_arabic(text)
    print(f"Contains Arabic: {has_arabic}")
    
    if has_arabic:
        extracted = extract_arabic_text(text)
        print(f"Extracted text: {repr(extracted)}")
        print(f"Extracted text (display): {extracted}")
        print(f"Extracted text (hex): {extracted.encode('utf-8').hex()}")
        
        prepared = prepare_arabic_for_rendering(extracted)
        print(f"Prepared text: {repr(prepared)}")
        print(f"Prepared text (display): {prepared}")
        
        # Show character-by-character breakdown
        print("\nCharacter breakdown:")
        for i, char in enumerate(extracted):
            print(f"  [{i}] {char} (U+{ord(char):04X})")
    else:
        print("No Arabic text detected!")

if __name__ == "__main__":
    # Test cases
    test_cases = [
        "سفر",  # Travel
        "Hello سفر world",  # Mixed
        "خَمْرَة",  # Wine (the word that keeps appearing)
        "سفر beautiful landscape",  # Arabic + English
    ]
    
    print("Arabic Text Extraction Test")
    print("="*60)
    
    for test_text in test_cases:
        test_extraction(test_text)
    
    print(f"\n{'='*60}")
    print("Test complete!")
    print("\nIf extraction is working correctly, you should see:")
    print("  - 'سفر' extracted correctly")
    print("  - 'خَمْرَة' extracted correctly")
    print("\nIf the model is generating 'wine' instead of 'travel',")
    print("this is because the diffusion model doesn't understand Arabic.")
    print("This is why Phase-1 ControlNet training is needed.")

