# Batch Files for Arabic Phase-1 Setup

This directory contains Windows batch files to automate the Phase-1 Arabic text rendering setup.

## 📋 Available Scripts

### 1. `setup_arabic_phase1.bat` - **Main Setup Script** ⭐
**Purpose**: Complete automated setup of Phase-1 Arabic text rendering

**What it does**:
- ✅ Checks Python installation
- ✅ Installs all dependencies from `requirements.txt`
- ✅ Validates vocabulary file
- ✅ Tests Arabic detection modules
- ✅ Generates synthetic dataset (1000+ images)
- ✅ Validates dataset generation
- ✅ Creates comprehensive log file

**Usage**:
```batch
setup_arabic_phase1.bat
```

**Output**:
- Creates `arabic_dataset_phase1/` directory with:
  - `images/` - Generated Arabic text images
  - `labels.txt` - Image-to-word mapping
- Creates log file: `arabic_setup_log_YYYYMMDD_HHMMSS.txt`

**Time**: 5-15 minutes depending on your system

---

### 2. `test_arabic_setup.bat` - **Quick Test Script**
**Purpose**: Test prerequisites and modules without full setup

**What it does**:
- ✅ Tests Python installation
- ✅ Tests required modules (arabic_reshaper, python-bidi, Pillow)
- ✅ Tests Arabic text utilities
- ✅ Tests vocabulary file
- ✅ Tests dataset generator
- ✅ Generates a single test image

**Usage**:
```batch
test_arabic_setup.bat
```

**Use this when**:
- You want to verify everything is ready before full setup
- You want to test after installing dependencies
- You want to troubleshoot issues

**Output**: Creates `arabic_test_log_YYYYMMDD_HHMMSS.txt`

---

### 3. `validate_arabic_setup.bat` - **Validation Script**
**Purpose**: Validate that setup completed successfully

**What it does**:
- ✅ Checks dataset directory exists
- ✅ Checks images directory exists
- ✅ Checks labels file exists
- ✅ Counts generated images
- ✅ Validates sample image format
- ✅ Tests module imports

**Usage**:
```batch
validate_arabic_setup.bat
```

**Use this when**:
- After running `setup_arabic_phase1.bat`
- To verify dataset is ready for training
- To check if setup needs to be re-run

**Output**: Creates `arabic_validation_YYYYMMDD_HHMMSS.txt`

---

## 🚀 Quick Start

### First Time Setup:
```batch
REM Step 1: Test prerequisites
test_arabic_setup.bat

REM Step 2: Run full setup
setup_arabic_phase1.bat

REM Step 3: Validate setup
validate_arabic_setup.bat
```

### After Setup:
```batch
REM Just validate
validate_arabic_setup.bat
```

---

## 📝 Log Files

All scripts create timestamped log files:
- `arabic_setup_log_YYYYMMDD_HHMMSS.txt` - Full setup log
- `arabic_test_log_YYYYMMDD_HHMMSS.txt` - Test results
- `arabic_validation_YYYYMMDD_HHMMSS.txt` - Validation results

Log files contain:
- All command output
- Success/failure status for each step
- Error messages (if any)
- Timestamps

---

## ⚠️ Troubleshooting

### Setup Fails at Dependency Installation
**Solution**:
```batch
REM Install dependencies manually first
pip install -r requirements.txt

REM Then run setup again
setup_arabic_phase1.bat
```

### Setup Fails at Dataset Generation
**Solution**:
1. Check log file for specific error
2. Verify vocabulary file exists: `arabic_vocabulary_sample.txt`
3. Test dataset generator manually:
   ```batch
   python -c "from arabic_dataset import ArabicDatasetGenerator; gen = ArabicDatasetGenerator(); img = gen.generate_image('سفر'); img.save('test.png')"
   ```

### Validation Fails
**Solution**:
1. Check if dataset directory exists
2. Run setup again: `setup_arabic_phase1.bat`
3. Check log files for details

---

## ✅ Success Indicators

### Setup Script Success:
- ✅ "All steps completed successfully!" message
- ✅ Dataset directory created with images
- ✅ Log file shows 0 errors

### Test Script Success:
- ✅ All tests show "[PASS]"
- ✅ 0 failed tests

### Validation Success:
- ✅ "Setup validation PASSED" message
- ✅ All checks show "[PASS]"

---

## 📊 Expected Results

After successful setup:
- **Dataset directory**: `arabic_dataset_phase1/`
- **Images**: 1000+ PNG files (100 words × 10 variations)
- **Labels file**: `arabic_dataset_phase1/labels.txt`
- **Log file**: Timestamped log with all details

---

## 🔄 Re-running Setup

If you need to regenerate the dataset:
```batch
REM Delete old dataset (optional)
rmdir /s /q arabic_dataset_phase1

REM Run setup again
setup_arabic_phase1.bat
```

---

## 📞 Next Steps After Setup

1. **Dataset is ready** in `arabic_dataset_phase1/`
2. **Complete ControlNet training** (see `QUICK_START_ARABIC.md`)
3. **Train the model** using the generated dataset
4. **Set environment variable**: `ARABIC_CONTROLNET_PATH=arabic_controlnet_checkpoint`
5. **Run image generation**: `python run.py --prompt_file prompts.txt`

---

## 💡 Tips

- **Run test script first** to catch issues early
- **Check log files** if something fails
- **Validation script** is quick - run it anytime to check status
- **All scripts pause** at the end so you can read the output

---

## 🐛 Common Issues

### "Python is not installed or not in PATH"
- Install Python from python.org
- Add Python to system PATH during installation

### "Required modules missing"
- Run: `pip install -r requirements.txt`
- Check internet connection

### "Vocabulary file not found"
- Ensure `arabic_vocabulary_sample.txt` exists in the same directory
- Or create your own vocabulary file

### "Dataset generation failed"
- Check if you have write permissions
- Ensure enough disk space (dataset is ~50-100 MB)
- Check log file for specific error

---

## 📚 Related Files

- `QUICK_START_ARABIC.md` - Complete setup guide
- `ARABIC_PHASE1_README.md` - Detailed documentation
- `arabic_vocabulary_sample.txt` - Sample vocabulary (100 words)
- `requirements.txt` - Python dependencies

