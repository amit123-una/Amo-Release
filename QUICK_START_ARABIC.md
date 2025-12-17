# Quick Start Guide - Phase-1 Arabic Text Rendering

## ✅ What's Already Done

1. **Sample vocabulary file created**: `arabic_vocabulary_sample.txt` (100 Arabic words)
2. **All modules created**: encoder, dataset generator, ControlNet, OCR validator
3. **Integration complete**: Phase-1 runs automatically after existing Arabic post-processing

## 🚀 What You Need to Do

### Step 1: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Tesseract OCR (required for validation)
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr tesseract-ocr-ara
# macOS: brew install tesseract tesseract-lang
```

### Step 2: Prepare Vocabulary (Optional - Sample Already Provided)

**Option A: Use the sample vocabulary (recommended for testing)**
```bash
# The file arabic_vocabulary_sample.txt already exists with 100 words
# Just use it directly!
```

**Option B: Create your own vocabulary**
```bash
# Create a text file with Arabic words (one per line)
# Example: my_vocabulary.txt
سفر
كتاب
مدرسة
# ... add 100-500 words
```

### Step 3: Generate Synthetic Dataset

```bash
python train_arabic_phase1.py \
    --vocabulary_file arabic_vocabulary_sample.txt \
    --dataset_dir arabic_dataset_phase1 \
    --images_per_word 10
```

This will:
- Generate 1000 images (100 words × 10 variations)
- Save them in `arabic_dataset_phase1/images/`
- Create `arabic_dataset_phase1/labels.txt`

**Time estimate**: 5-15 minutes depending on your system

### Step 4: Train ControlNet (⚠️ Requires Full Implementation)

**Current Status**: The training function is a placeholder. You need to integrate it with diffusers training utilities.

**Option A: Use existing diffusers training script** (Recommended)
```bash
# Navigate to diffusers examples
cd diffusers-amo/examples/controlnet

# Adapt train_controlnet.py to use your Arabic dataset
# You'll need to modify the dataset loading to use arabic_dataset_phase1/labels.txt
```

**Option B: Wait for full implementation**
- The `train_arabic_controlnet()` function in `arabic_controlnet.py` needs to be completed
- It should integrate with `diffusers-amo/examples/controlnet/train_controlnet.py`

### Step 5: Use Trained Model (After Training)

```bash
# Set environment variable to point to your trained ControlNet
export ARABIC_CONTROLNET_PATH=arabic_controlnet_checkpoint

# Run normal image generation
python run.py --prompt_file prompts.txt --model_type flux
```

If Arabic text is detected, Phase-1 will automatically run!

## 📋 Complete Workflow Example

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate dataset (uses sample vocabulary)
python train_arabic_phase1.py \
    --vocabulary_file arabic_vocabulary_sample.txt \
    --images_per_word 10 \
    --skip_dataset_generation false

# 3. Train ControlNet (requires full implementation)
# TODO: Complete train_arabic_controlnet() or use diffusers training script

# 4. Set model path and run
export ARABIC_CONTROLNET_PATH=arabic_controlnet_checkpoint
python run.py --prompt_file prompts.txt --model_type flux
```

## 🎯 What Works Right Now (Without Training)

Even without a trained ControlNet, you can:

1. **Test dataset generation**:
   ```bash
   python train_arabic_phase1.py --vocabulary_file arabic_vocabulary_sample.txt
   ```
   This will generate the synthetic dataset.

2. **Test Arabic detection**:
   ```python
   from arabic_text_utils import contains_arabic, extract_arabic_text
   print(contains_arabic("سفر"))  # True
   print(extract_arabic_text("Hello سفر world"))  # "سفر"
   ```

3. **Test existing Arabic post-processing** (already working):
   ```bash
   # Create prompts.txt with Arabic text
   echo "A beautiful landscape with the word سفر" > prompts.txt
   python run.py --prompt_file prompts.txt --model_type flux
   ```
   This will generate:
   - `sample_0000.png` - Original image
   - `sample_0000_arabic.png` - Arabic post-processing (existing feature)

## ⚠️ What's Missing

1. **Full ControlNet training implementation**
   - `train_arabic_controlnet()` in `arabic_controlnet.py` is a placeholder
   - Needs integration with diffusers training utilities
   - See `diffusers-amo/examples/controlnet/train_controlnet.py` for reference

2. **Trained ControlNet model**
   - You need to train the model first before Phase-1 rendering works
   - Without a trained model, Phase-1 will skip silently

## 🔍 Quick Test Commands

```bash
# Test vocabulary loading
python -c "from train_arabic_phase1 import load_vocabulary; print(len(load_vocabulary('arabic_vocabulary_sample.txt')))"

# Test dataset generation (single word)
python -c "from arabic_dataset import ArabicDatasetGenerator; gen = ArabicDatasetGenerator(); img = gen.generate_image('سفر'); img.save('test_arabic.png'); print('Saved test_arabic.png')"

# Test Arabic detection
python -c "from arabic_text_utils import contains_arabic; print('Contains Arabic:', contains_arabic('سفر'))"
```

## 📝 Summary

**What you can do NOW:**
- ✅ Use sample vocabulary (`arabic_vocabulary_sample.txt`)
- ✅ Generate synthetic dataset
- ✅ Test Arabic detection and extraction
- ✅ Use existing Arabic post-processing

**What needs to be done:**
- ⚠️ Complete ControlNet training implementation
- ⚠️ Train the ControlNet model
- ⚠️ Then Phase-1 rendering will work automatically

The foundation is ready - you just need to complete the training step!
