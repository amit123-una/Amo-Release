@echo off
REM ============================================================================
REM Quick Test Script for Arabic Phase-1 Setup
REM ============================================================================
REM This script runs quick validation tests without full setup
REM ============================================================================

setlocal enabledelayedexpansion

set TEST_LOG=arabic_test_log_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set TEST_LOG=!TEST_LOG: =0!
set PASSED=0
set FAILED=0

echo ============================================================================
echo Arabic Phase-1 Quick Test Suite
echo ============================================================================
echo Test log: %TEST_LOG%
echo.

echo Test log: %TEST_LOG% > "%TEST_LOG%"
echo Started: %date% %time% >> "%TEST_LOG%"
echo ============================================================================ >> "%TEST_LOG%"
echo.

REM Step 0: Activate Conda Environment
echo [STEP 0] Activating conda environment 'amo'...
echo [STEP 0] Activating conda environment 'amo'... >> "%TEST_LOG%"

REM Check if conda is available
where conda >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Conda not found in PATH, trying to initialize...
    echo [WARNING] Conda not found in PATH, trying to initialize... >> "%TEST_LOG%"
    
    REM Try common conda installation paths
    if exist "%USERPROFILE%\anaconda3\Scripts\conda.exe" (
        set "CONDA_BASE=%USERPROFILE%\anaconda3"
        call "%CONDA_BASE%\Scripts\activate.bat" %CONDA_BASE%
    ) else if exist "%LOCALAPPDATA%\anaconda3\Scripts\conda.exe" (
        set "CONDA_BASE=%LOCALAPPDATA%\anaconda3"
        call "%CONDA_BASE%\Scripts\activate.bat" %CONDA_BASE%
    ) else if exist "%USERPROFILE%\miniconda3\Scripts\conda.exe" (
        set "CONDA_BASE=%USERPROFILE%\miniconda3"
        call "%CONDA_BASE%\Scripts\activate.bat" %CONDA_BASE%
    ) else if exist "%LOCALAPPDATA%\miniconda3\Scripts\conda.exe" (
        set "CONDA_BASE=%LOCALAPPDATA%\miniconda3"
        call "%CONDA_BASE%\Scripts\activate.bat" %CONDA_BASE%
    ) else (
        echo [FAIL] Conda not found. Please ensure conda is installed and in PATH.
        echo [FAIL] Conda not found. Please ensure conda is installed and in PATH. >> "%TEST_LOG%"
        set /a FAILED+=1
        goto :test_summary
    )
)

REM Activate conda environment 'amo'
call conda activate amo >> "%TEST_LOG%" 2>&1
if errorlevel 1 (
    echo [FAIL] Failed to activate conda environment 'amo'!
    echo [FAIL] Failed to activate conda environment 'amo'! >> "%TEST_LOG%"
    set /a FAILED+=1
    goto :test_summary
) else (
    echo [PASS] Conda environment 'amo' activated
    echo [PASS] Conda environment 'amo' activated >> "%TEST_LOG%"
    set /a PASSED+=1
)
echo.

REM Test 1: Python Installation
echo [TEST 1] Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found
    echo [FAIL] Python not found >> "%TEST_LOG%"
    set /a FAILED+=1
) else (
    python --version
    echo [PASS] Python found
    echo [PASS] Python found >> "%TEST_LOG%"
    set /a PASSED+=1
)
echo.

REM Test 2: Required Modules
echo [TEST 2] Required Python modules...
python -c "import arabic_reshaper; import bidi; from PIL import Image; print('OK')" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Required modules missing (arabic_reshaper, python-bidi, Pillow)
    echo [FAIL] Required modules missing >> "%TEST_LOG%"
    set /a FAILED+=1
) else (
    echo [PASS] Required modules installed
    echo [PASS] Required modules installed >> "%TEST_LOG%"
    set /a PASSED+=1
)
echo.

REM Test 3: Arabic Text Utils
echo [TEST 3] Arabic text utilities...
python -c "from arabic_text_utils import contains_arabic, extract_arabic_text; assert contains_arabic('سفر') == True; assert extract_arabic_text('Hello سفر world') == 'سفر'; print('OK')" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Arabic text utilities test failed
    echo [FAIL] Arabic text utilities test failed >> "%TEST_LOG%"
    set /a FAILED+=1
) else (
    echo [PASS] Arabic text utilities working
    echo [PASS] Arabic text utilities working >> "%TEST_LOG%"
    set /a PASSED+=1
)
echo.

REM Test 4: Vocabulary File
echo [TEST 4] Vocabulary file...
if exist "arabic_vocabulary_sample.txt" (
    python -c "with open('arabic_vocabulary_sample.txt', 'r', encoding='utf-8') as f: words = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]; print(len(words))" > temp_count.txt 2>&1
    set /p COUNT=<temp_count.txt
    del temp_count.txt
    if !COUNT! GEQ 10 (
        echo [PASS] Vocabulary file found with !COUNT! words
        echo [PASS] Vocabulary file found with !COUNT! words >> "%TEST_LOG%"
        set /a PASSED+=1
    ) else (
        echo [FAIL] Vocabulary file has too few words: !COUNT!
        echo [FAIL] Vocabulary file has too few words: !COUNT! >> "%TEST_LOG%"
        set /a FAILED+=1
    )
) else (
    echo [FAIL] Vocabulary file not found
    echo [FAIL] Vocabulary file not found >> "%TEST_LOG%"
    set /a FAILED+=1
)
echo.

REM Test 5: Dataset Generator
echo [TEST 5] Dataset generator module...
python -c "from arabic_dataset import ArabicDatasetGenerator; gen = ArabicDatasetGenerator(); print('OK')" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Dataset generator module test failed
    echo [FAIL] Dataset generator module test failed >> "%TEST_LOG%"
    set /a FAILED+=1
) else (
    echo [PASS] Dataset generator module working
    echo [PASS] Dataset generator module working >> "%TEST_LOG%"
    set /a PASSED+=1
)
echo.

REM Test 6: Generate Single Test Image
echo [TEST 6] Generate test image...
python -c "from arabic_dataset import ArabicDatasetGenerator; gen = ArabicDatasetGenerator(); img = gen.generate_image('سفر'); img.save('test_output.png'); print('OK')" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Test image generation failed
    echo [FAIL] Test image generation failed >> "%TEST_LOG%"
    set /a FAILED+=1
) else (
    if exist "test_output.png" (
        echo [PASS] Test image generated successfully
        echo [PASS] Test image generated successfully >> "%TEST_LOG%"
        del test_output.png
        set /a PASSED+=1
    ) else (
        echo [FAIL] Test image file not created
        echo [FAIL] Test image file not created >> "%TEST_LOG%"
        set /a FAILED+=1
    )
)
echo.

REM Test 7: ControlNet Module (if available)
echo [TEST 7] ControlNet module...
python -c "from arabic_controlnet import ArabicControlNetRenderer; print('OK')" >nul 2>&1
if errorlevel 1 (
    echo [WARN] ControlNet module test failed (expected if dependencies missing)
    echo [WARN] ControlNet module test failed >> "%TEST_LOG%"
) else (
    echo [PASS] ControlNet module available
    echo [PASS] ControlNet module available >> "%TEST_LOG%"
    set /a PASSED+=1
)
echo.

REM Summary
echo ============================================================================
echo Test Summary
echo ============================================================================
echo Tests passed: !PASSED!
echo Tests failed: !FAILED!
echo.
echo Test Summary >> "%TEST_LOG%"
echo Tests passed: !PASSED! >> "%TEST_LOG%"
echo Tests failed: !FAILED! >> "%TEST_LOG%"
echo Finished: %date% %time% >> "%TEST_LOG%"
echo ============================================================================ >> "%TEST_LOG%"

:test_summary
if !FAILED! EQU 0 (
    echo [SUCCESS] All tests passed!
    echo.
    echo You can now run setup_arabic_phase1.bat for full setup
) else (
    echo [WARNING] Some tests failed. Please check the log: %TEST_LOG%
    echo.
    echo Install missing dependencies:
    echo   pip install -r requirements.txt
)

echo.
echo Test log saved to: %TEST_LOG%
pause
