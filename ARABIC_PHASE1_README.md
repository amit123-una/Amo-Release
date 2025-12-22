# Phase-1 Arabic Text Rendering

This document describes the Phase-1 Arabic text rendering capability added to amo-release.

## Overview

Phase-1 adds a **trained ControlNet model** that renders Arabic text accurately, character-by-character, without hallucination or substitution. This runs **after** the existing Arabic post-processing, so your existing functionality is never affected.

## Architecture

### 1. Arabic Glyph Encoder (`arabic_encoder.py`)
- Encodes Arabic text into glyph sequences (initial/medial/final/isolated)
- Uses `arabic_reshaper` and `python-bidi` for correct shaping
- Treats Arabic rendering as a **visual generation problem**, not semantic

### 2. Synthetic Dataset Generator (`arabic_dataset.py`)
- Generates clean, noise-free training data
- Renders Arabic words using multiple fonts and sizes
- High contrast, centered text, clean backgrounds
- Fully controlled dataset for teaching the model

### 3. ControlNet Renderer (`arabic_controlnet.py`)
- Trained ControlNet model for Arabic text rendering
- Uses Arabic text images as conditioning input
- Generates images with correct Arabic glyphs

### 4. OCR Validator (`arabic_ocr_validator.py`)
- Validates generated images using OCR
- Ensures output matches input exactly
- Rejects samples that fail validation

## Integration

Phase-1 rendering is **automatically triggered** when:
1. Arabic text is detected in the prompt
2. Existing Arabic post-processing completes
3. A trained ControlNet model is available (set `ARABIC_CONTROLNET_PATH` environment variable)

The integration in `run.py` ensures:
- ✅ Existing image generation logic is **unchanged**
- ✅ Phase-1 runs **after** existing Arabic post-processing
- ✅ Failures in Phase-1 **never break** the main pipeline
- ✅ Non-Arabic prompts work exactly as before

## Usage

### Step 1: Prepare Vocabulary

Create a text file with Arabic words (100-500 words for Phase-1):

```bash
# arabic_vocabulary.txt
سفر
كتاب
مدرسة
...
```

### Step 2: Generate Synthetic Dataset

```bash
python -c "from arabic_dataset import generate_phase1_dataset; \
           vocabulary = open('arabic_vocabulary.txt', 'r', encoding='utf-8').read().strip().split('\n'); \
           generate_phase1_dataset(vocabulary, 'arabic_dataset_phase1', images_per_word=10)"
```

Or use the training script:

```bash
python train_arabic_phase1.py --vocabulary_file arabic_vocabulary.txt --images_per_word 10
```

### Step 3: Train ControlNet

```bash
python train_arabic_phase1.py \
    --vocabulary_file arabic_vocabulary.txt \
    --dataset_dir arabic_dataset_phase1 \
    --output_dir arabic_controlnet_checkpoint \
    --num_epochs 10 \
    --batch_size 4 \
    --learning_rate 1e-5
```

**Note:** The full training implementation requires integration with diffusers training utilities. See `diffusers-amo/examples/controlnet/train_controlnet.py` for reference.

### Step 4: Use Trained Model

Set the environment variable to point to your trained ControlNet:

```bash
export ARABIC_CONTROLNET_PATH=arabic_controlnet_checkpoint
```

Then run your normal image generation:

```bash
python run.py --prompt_file prompts.txt --model_type flux
```

If Arabic text is detected, Phase-1 rendering will automatically run after the existing Arabic post-processing.

## Output Files

When Phase-1 is active, you'll get:

1. `sample_0003.png` - Original image (unchanged)
2. `sample_0003_arabic.png` - Existing Arabic post-processing (unchanged)
3. `sample_0003_phase1_arabic.png` - **NEW** Phase-1 ControlNet rendering (validated with OCR)

If OCR validation fails, the image is saved as `sample_0003_phase1_arabic_rejected.png` for debugging.

## Success Criteria (Phase-1)

✅ **Input word = سفر**  
✅ **Output image shows exactly سفر**  
✅ **No extra letters**  
✅ **No substitutions**  
✅ **No hallucination**  
✅ **OCR validation passes (similarity ≥ 0.9)**

**Accuracy is more important than aesthetics for Phase-1.**

## Dependencies

Install additional dependencies:

```bash
pip install -r requirements.txt
```

New dependencies:
- `Pillow>=10.0.0` - For synthetic dataset generation
- `pytesseract>=0.3.10` - For OCR validation (requires Tesseract OCR installed separately)

### Installing Tesseract OCR

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Install Arabic language data during installation

**Linux:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-ara
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

## Phase-1 Scope

**In Scope:**
- ✅ 100-500 Arabic words
- ✅ 512×512 resolution
- ✅ Centered text rendering
- ✅ Character-by-character accuracy
- ✅ OCR validation

**Out of Scope (for now):**
- ❌ Full sentence layout
- ❌ Calligraphy styles
- ❌ Mixed Arabic + English
- ❌ Large-scale training

## Troubleshooting

### Phase-1 not running?

1. Check if Arabic text is detected:
   ```python
   from arabic_text_utils import contains_arabic
   print(contains_arabic("سفر"))  # Should be True
   ```

2. Check if ControlNet path is set:
   ```bash
   echo $ARABIC_CONTROLNET_PATH
   ```

3. Check if ControlNet model exists:
   ```bash
   ls -la arabic_controlnet_checkpoint/
   ```

### OCR validation failing?

1. Ensure Tesseract OCR is installed with Arabic language data
2. Check OCR extraction:
   ```python
   from arabic_ocr_validator import ArabicOCRValidator
   validator = ArabicOCRValidator()
   text = validator.extract_text(image)
   print(text)
   ```

3. Adjust tolerance in `run.py` if needed (default: 0.9)

## Next Steps

After Phase-1 proves feasibility:
- Expand vocabulary (500 → 1000+ words)
- Add more font variations
- Improve OCR validation
- Scale to higher resolutions
- Add sentence layout support

