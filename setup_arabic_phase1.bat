@echo off
REM ============================================================================
REM Phase-1 Arabic Text Rendering - Complete Setup Script
REM ============================================================================
REM This script automates all steps for Phase-1 Arabic text rendering:
REM 1. Dependency installation
REM 2. Dataset generation
REM 3. Validation
REM ============================================================================

setlocal enabledelayedexpansion

REM Configuration
set LOG_FILE=arabic_setup_log_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set LOG_FILE=!LOG_FILE: =0!
set VOCABULARY_FILE=arabic_vocabulary_sample.txt
set DATASET_DIR=arabic_dataset_phase1
set IMAGES_PER_WORD=10
set ERROR_COUNT=0

REM Create log file
echo ============================================================================ > "%LOG_FILE%"
echo Phase-1 Arabic Text Rendering Setup Log >> "%LOG_FILE%"
echo Started: %date% %time% >> "%LOG_FILE%"
echo ============================================================================ >> "%LOG_FILE%"
echo.

echo ============================================================================
echo Phase-1 Arabic Text Rendering - Setup Script
echo ============================================================================
echo Log file: %LOG_FILE%
echo.

REM ============================================================================
REM Step 0: Activate Conda Environment
REM ============================================================================
echo [STEP 0/6] Activating conda environment 'amo'...
echo [STEP 0/6] Activating conda environment 'amo'... >> "%LOG_FILE%"

REM Check if conda is available
where conda >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Conda not found in PATH, trying to initialize...
    echo [WARNING] Conda not found in PATH, trying to initialize... >> "%LOG_FILE%"
    
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
        echo [ERROR] Conda not found. Please ensure conda is installed and in PATH.
        echo [ERROR] Conda not found. Please ensure conda is installed and in PATH. >> "%LOG_FILE%"
        echo [ERROR] Or manually activate 'amo' environment before running this script.
        echo [ERROR] Or manually activate 'amo' environment before running this script. >> "%LOG_FILE%"
        set /a ERROR_COUNT+=1
        goto :error_exit
    )
)

REM Activate conda environment 'amo'
call conda activate amo >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to activate conda environment 'amo'!
    echo [ERROR] Failed to activate conda environment 'amo'! >> "%LOG_FILE%"
    echo [ERROR] Please ensure the 'amo' environment exists: conda env list
    echo [ERROR] Please ensure the 'amo' environment exists: conda env list >> "%LOG_FILE%"
    set /a ERROR_COUNT+=1
    goto :error_exit
) else (
    echo [SUCCESS] Conda environment 'amo' activated
    echo [SUCCESS] Conda environment 'amo' activated >> "%LOG_FILE%"
    REM Verify activation by checking Python path
    python -c "import sys; print('Python:', sys.executable)" >> "%LOG_FILE%" 2>&1
)
echo.

REM ============================================================================
REM Step 1: Check Python Installation
REM ============================================================================
echo [STEP 1/6] Checking Python installation...
echo [STEP 1/5] Checking Python installation... >> "%LOG_FILE%"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo [ERROR] Python is not installed or not in PATH! >> "%LOG_FILE%"
    set /a ERROR_COUNT+=1
    goto :error_exit
) else (
    python --version
    python --version >> "%LOG_FILE%"
    echo [SUCCESS] Python found
    echo [SUCCESS] Python found >> "%LOG_FILE%"
)
echo.

REM ============================================================================
REM Step 2: Install Dependencies
REM ============================================================================
echo [STEP 2/6] Installing Python dependencies...
echo [STEP 2/6] Installing Python dependencies... >> "%LOG_FILE%"

python -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip, continuing...
    echo [WARNING] Failed to upgrade pip, continuing... >> "%LOG_FILE%"
)

python -m pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies from requirements.txt!
    echo [ERROR] Failed to install dependencies from requirements.txt! >> "%LOG_FILE%"
    set /a ERROR_COUNT+=1
    goto :error_exit
) else (
    echo [SUCCESS] Dependencies installed
    echo [SUCCESS] Dependencies installed >> "%LOG_FILE%"
)
echo.

REM ============================================================================
REM Step 3: Validate Vocabulary File
REM ============================================================================
echo [STEP 3/6] Validating vocabulary file...
echo [STEP 3/6] Validating vocabulary file... >> "%LOG_FILE%"

if not exist "%VOCABULARY_FILE%" (
    echo [ERROR] Vocabulary file not found: %VOCABULARY_FILE%
    echo [ERROR] Vocabulary file not found: %VOCABULARY_FILE% >> "%LOG_FILE%"
    set /a ERROR_COUNT+=1
    goto :error_exit
)

REM Count words in vocabulary file
python -c "with open('%VOCABULARY_FILE%', 'r', encoding='utf-8') as f: words = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]; print(len(words))" > temp_word_count.txt 2>&1
set /p WORD_COUNT=<temp_word_count.txt
del temp_word_count.txt

if !WORD_COUNT! LSS 10 (
    echo [WARNING] Vocabulary file has only !WORD_COUNT! words (recommended: 100-500)
    echo [WARNING] Vocabulary file has only !WORD_COUNT! words (recommended: 100-500) >> "%LOG_FILE%"
) else (
    echo [SUCCESS] Vocabulary file validated: !WORD_COUNT! words found
    echo [SUCCESS] Vocabulary file validated: !WORD_COUNT! words found >> "%LOG_FILE%"
)
echo.

REM ============================================================================
REM Step 4: Test Arabic Detection Module
REM ============================================================================
echo [STEP 4/6] Testing Arabic detection module...
echo [STEP 4/6] Testing Arabic detection module... >> "%LOG_FILE%"

python -c "from arabic_text_utils import contains_arabic, extract_arabic_text; print('Test 1:', contains_arabic('سفر')); print('Test 2:', extract_arabic_text('Hello سفر world'))" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Arabic detection module test failed!
    echo [ERROR] Arabic detection module test failed! >> "%LOG_FILE%"
    set /a ERROR_COUNT+=1
    goto :error_exit
) else (
    echo [SUCCESS] Arabic detection module working
    echo [SUCCESS] Arabic detection module working >> "%LOG_FILE%"
)
echo.

REM ============================================================================
REM Step 5: Generate Synthetic Dataset
REM ============================================================================
echo [STEP 5/6] Generating synthetic dataset...
echo [STEP 5/6] Generating synthetic dataset... >> "%LOG_FILE%"
echo This may take 5-15 minutes depending on your system...
echo.

python train_arabic_phase1.py --vocabulary_file "%VOCABULARY_FILE%" --dataset_dir "%DATASET_DIR%" --images_per_word %IMAGES_PER_WORD% --skip_dataset_generation false >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Dataset generation failed!
    echo [ERROR] Dataset generation failed! >> "%LOG_FILE%"
    set /a ERROR_COUNT+=1
    goto :error_exit
)

REM Validate dataset was created
if not exist "%DATASET_DIR%\images" (
    echo [ERROR] Dataset images directory not found!
    echo [ERROR] Dataset images directory not found! >> "%LOG_FILE%"
    set /a ERROR_COUNT+=1
    goto :error_exit
)

if not exist "%DATASET_DIR%\labels.txt" (
    echo [ERROR] Dataset labels file not found!
    echo [ERROR] Dataset labels file not found! >> "%LOG_FILE%"
    set /a ERROR_COUNT+=1
    goto :error_exit
)

REM Count generated images
for /f %%i in ('dir /b "%DATASET_DIR%\images\*.png" 2^>nul ^| find /c /v ""') do set IMAGE_COUNT=%%i

if !IMAGE_COUNT! LSS 10 (
    echo [WARNING] Only !IMAGE_COUNT! images generated (expected more)
    echo [WARNING] Only !IMAGE_COUNT! images generated (expected more) >> "%LOG_FILE%"
) else (
    echo [SUCCESS] Dataset generated: !IMAGE_COUNT! images
    echo [SUCCESS] Dataset generated: !IMAGE_COUNT! images >> "%LOG_FILE%"
)
echo.

REM ============================================================================
REM Validation Summary
REM ============================================================================
echo ============================================================================
echo Validation Summary
echo ============================================================================
echo Validation Summary >> "%LOG_FILE%"
echo.

REM Test dataset generator
echo [VALIDATION] Testing dataset generator...
echo [VALIDATION] Testing dataset generator... >> "%LOG_FILE%"
python -c "from arabic_dataset import ArabicDatasetGenerator; gen = ArabicDatasetGenerator(); img = gen.generate_image('سفر'); img.save('test_arabic_output.png'); print('Test image saved')" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [WARNING] Dataset generator test failed
    echo [WARNING] Dataset generator test failed >> "%LOG_FILE%"
    set /a ERROR_COUNT+=1
) else (
    if exist "test_arabic_output.png" (
        echo [SUCCESS] Dataset generator test passed
        echo [SUCCESS] Dataset generator test passed >> "%LOG_FILE%"
        del test_arabic_output.png
    ) else (
        echo [WARNING] Test image not created
        echo [WARNING] Test image not created >> "%LOG_FILE%"
    )
)
echo.

REM ============================================================================
REM Final Summary
REM ============================================================================
echo ============================================================================
echo Setup Complete!
echo ============================================================================
echo Setup Complete! >> "%LOG_FILE%"
echo.

if !ERROR_COUNT! EQU 0 (
    echo [SUCCESS] All steps completed successfully!
    echo [SUCCESS] All steps completed successfully! >> "%LOG_FILE%"
    echo.
    echo Next steps:
    echo 1. Dataset is ready in: %DATASET_DIR%
    echo 2. To train ControlNet, you need to complete the training implementation
    echo 3. See QUICK_START_ARABIC.md for details
    echo.
    echo Next steps: >> "%LOG_FILE%"
    echo 1. Dataset is ready in: %DATASET_DIR% >> "%LOG_FILE%"
    echo 2. To train ControlNet, you need to complete the training implementation >> "%LOG_FILE%"
    echo 3. See QUICK_START_ARABIC.md for details >> "%LOG_FILE%"
) else (
    echo [WARNING] Setup completed with !ERROR_COUNT! error(s)
    echo [WARNING] Setup completed with !ERROR_COUNT! error(s) >> "%LOG_FILE%"
    echo Please check the log file for details: %LOG_FILE%
)

echo.
echo Log file: %LOG_FILE%
echo ============================================================================
echo Log file: %LOG_FILE% >> "%LOG_FILE%"
echo Finished: %date% %time% >> "%LOG_FILE%"
echo ============================================================================ >> "%LOG_FILE%"

pause
exit /b !ERROR_COUNT!

:error_exit
echo.
echo [ERROR] Setup failed at step with error count: !ERROR_COUNT!
echo [ERROR] Setup failed at step with error count: !ERROR_COUNT! >> "%LOG_FILE%"
echo Please check the log file for details: %LOG_FILE%
echo.
pause
exit /b !ERROR_COUNT!
