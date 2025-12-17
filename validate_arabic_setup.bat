@echo off
REM ============================================================================
REM Validation Script for Arabic Phase-1 Setup
REM ============================================================================
REM This script validates that the setup completed successfully
REM ============================================================================

setlocal enabledelayedexpansion

set VALIDATION_LOG=arabic_validation_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set VALIDATION_LOG=!VALIDATION_LOG: =0!
set DATASET_DIR=arabic_dataset_phase1
set VALIDATION_PASSED=1

echo ============================================================================
echo Arabic Phase-1 Setup Validation
echo ============================================================================
echo Validation log: %VALIDATION_LOG%
echo.

echo Validation log: %VALIDATION_LOG% > "%VALIDATION_LOG%"
echo Started: %date% %time% >> "%VALIDATION_LOG%"
echo ============================================================================ >> "%VALIDATION_LOG%"
echo.

REM Step 0: Activate Conda Environment
echo [STEP 0] Activating conda environment 'amo'...
echo [STEP 0] Activating conda environment 'amo'... >> "%VALIDATION_LOG%"

REM Check if conda is available
where conda >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Conda not found in PATH, trying to initialize...
    echo [WARNING] Conda not found in PATH, trying to initialize... >> "%VALIDATION_LOG%"
    
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
        echo [WARN] Conda not found. Continuing without conda activation...
        echo [WARN] Conda not found. Continuing without conda activation... >> "%VALIDATION_LOG%"
    )
) else (
    REM Activate conda environment 'amo'
    call conda activate amo >> "%VALIDATION_LOG%" 2>&1
    if errorlevel 1 (
        echo [WARN] Failed to activate conda environment 'amo', continuing...
        echo [WARN] Failed to activate conda environment 'amo', continuing... >> "%VALIDATION_LOG%"
    ) else (
        echo [PASS] Conda environment 'amo' activated
        echo [PASS] Conda environment 'amo' activated >> "%VALIDATION_LOG%"
    )
)
echo.

REM Check 1: Dataset Directory
echo [CHECK 1] Dataset directory...
if exist "%DATASET_DIR%" (
    echo [PASS] Dataset directory exists
    echo [PASS] Dataset directory exists >> "%VALIDATION_LOG%"
) else (
    echo [FAIL] Dataset directory not found: %DATASET_DIR%
    echo [FAIL] Dataset directory not found: %DATASET_DIR% >> "%VALIDATION_LOG%"
    set VALIDATION_PASSED=0
)
echo.

REM Check 2: Images Directory
echo [CHECK 2] Images directory...
if exist "%DATASET_DIR%\images" (
    echo [PASS] Images directory exists
    echo [PASS] Images directory exists >> "%VALIDATION_LOG%"
) else (
    echo [FAIL] Images directory not found
    echo [FAIL] Images directory not found >> "%VALIDATION_LOG%"
    set VALIDATION_PASSED=0
)
echo.

REM Check 3: Labels File
echo [CHECK 3] Labels file...
if exist "%DATASET_DIR%\labels.txt" (
    echo [PASS] Labels file exists
    echo [PASS] Labels file exists >> "%VALIDATION_LOG%"
    
    REM Count lines in labels file
    for /f %%i in ('find /c /v "" ^< "%DATASET_DIR%\labels.txt"') do set LABEL_COUNT=%%i
    echo   Found !LABEL_COUNT! entries in labels file
    echo   Found !LABEL_COUNT! entries in labels file >> "%VALIDATION_LOG%"
) else (
    echo [FAIL] Labels file not found
    echo [FAIL] Labels file not found >> "%VALIDATION_LOG%"
    set VALIDATION_PASSED=0
)
echo.

REM Check 4: Image Count
echo [CHECK 4] Generated images...
if exist "%DATASET_DIR%\images" (
    for /f %%i in ('dir /b "%DATASET_DIR%\images\*.png" 2^>nul ^| find /c /v ""') do set IMAGE_COUNT=%%i
    
    if defined IMAGE_COUNT (
        if !IMAGE_COUNT! GEQ 100 (
            echo [PASS] Found !IMAGE_COUNT! images (excellent - 100+ images)
            echo [PASS] Found !IMAGE_COUNT! images (excellent - 100+ images) >> "%VALIDATION_LOG%"
        ) else if !IMAGE_COUNT! GEQ 10 (
            echo [PASS] Found !IMAGE_COUNT! images (minimum: 10)
            echo [PASS] Found !IMAGE_COUNT! images (minimum: 10) >> "%VALIDATION_LOG%"
        ) else (
            echo [WARN] Only !IMAGE_COUNT! images found (expected at least 10)
            echo [WARN] Only !IMAGE_COUNT! images found (expected at least 10) >> "%VALIDATION_LOG%"
        )
    ) else (
        echo [FAIL] No images found in dataset
        echo [FAIL] No images found in dataset >> "%VALIDATION_LOG%"
        set VALIDATION_PASSED=0
    )
) else (
    echo [FAIL] Images directory not found
    echo [FAIL] Images directory not found >> "%VALIDATION_LOG%"
    set VALIDATION_PASSED=0
)
echo.

REM Check 5: Sample Image Validation
echo [CHECK 5] Sample image validation...
if exist "%DATASET_DIR%\images" (
    set SAMPLE_IMAGE=
    for %%f in ("%DATASET_DIR%\images\*.png") do (
        set "SAMPLE_IMAGE=%%f"
        goto :found_sample
    )
    
    :found_sample
    if defined SAMPLE_IMAGE (
        python -c "from PIL import Image; img = Image.open(r'!SAMPLE_IMAGE!'); print('Size:', img.size, 'Mode:', img.mode)" >nul 2>&1
        if errorlevel 1 (
            echo [WARN] Could not validate sample image format
            echo [WARN] Could not validate sample image format >> "%VALIDATION_LOG%"
        ) else (
            echo [PASS] Sample image is valid
            echo [PASS] Sample image is valid >> "%VALIDATION_LOG%"
        )
    ) else (
        echo [FAIL] No sample images to validate
        echo [FAIL] No sample images to validate >> "%VALIDATION_LOG%"
        set VALIDATION_PASSED=0
    )
) else (
    echo [SKIP] Images directory not found, skipping validation
    echo [SKIP] Images directory not found, skipping validation >> "%VALIDATION_LOG%"
)
echo.

REM Check 6: Module Imports
echo [CHECK 6] Module imports...
python -c "from arabic_text_utils import contains_arabic; from arabic_dataset import ArabicDatasetGenerator; from arabic_encoder import ArabicGlyphEncoder; print('OK')" >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Module imports failed
    echo [FAIL] Module imports failed >> "%VALIDATION_LOG%"
    set VALIDATION_PASSED=0
) else (
    echo [PASS] All modules can be imported
    echo [PASS] All modules can be imported >> "%VALIDATION_LOG%"
)
echo.

REM Final Summary
echo ============================================================================
echo Validation Summary
echo ============================================================================
echo Validation Summary >> "%VALIDATION_LOG%"
echo.

if !VALIDATION_PASSED! EQU 1 (
    echo [SUCCESS] Setup validation PASSED
    echo [SUCCESS] Setup validation PASSED >> "%VALIDATION_LOG%"
    echo.
    echo Dataset is ready for training!
    echo Location: %DATASET_DIR%
    echo.
    echo Next steps:
    echo 1. Complete ControlNet training implementation
    echo 2. Train the model using the generated dataset
    echo 3. Set ARABIC_CONTROLNET_PATH environment variable
    echo.
) else (
    echo [FAILURE] Setup validation FAILED
    echo [FAILURE] Setup validation FAILED >> "%VALIDATION_LOG%"
    echo.
    echo Please run setup_arabic_phase1.bat to complete the setup
    echo.
)

echo Validation log: %VALIDATION_LOG%
echo Finished: %date% %time% >> "%VALIDATION_LOG%"
echo ============================================================================ >> "%VALIDATION_LOG%"

pause
exit /b !VALIDATION_PASSED!
