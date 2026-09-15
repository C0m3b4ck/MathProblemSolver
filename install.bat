@echo off
setlocal EnableDelayedExpansion

:: ═══════════════════════════════════════════════════════════════════════════
::  MathExerciseSolver — Windows Installer
::  Sets up everything: venv, Python packages, Tesseract, fonts, launcher
:: ═══════════════════════════════════════════════════════════════════════════

title MathExerciseSolver - Installer
color 0B

set "ROOT=%~dp0"
set "VENV=%ROOT%.venv"
set "FONTS=%ROOT%assets\fonts"
set "OUTPUT=%ROOT%output"
set "TESSERACT_URL=https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
set "TESSERACT_EXE=%TEMP%\tesseract-setup.exe"

echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║         MathExerciseSolver — Windows Installer           ║
echo  ║      Polish Grade 7-8 Math Solution Solver              ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

:: ── Step 0: Check Python ─────────────────────────────────────────────────
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python is not installed or not in PATH.
    echo  Download Python 3.10+ from: https://www.python.org/downloads/
    echo  IMPORTANT: Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
echo  Found Python %PYVER%

:: Verify Python is 3.10+
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>nul
if errorlevel 1 (
    echo.
    echo  WARNING: Python 3.10+ is recommended. Current: %PYVER%
    echo  Continue anyway? (Y/N)
    set /p "CONT=>"
    if /i not "!CONT!"=="Y" exit /b 1
)

:: ── Step 1: Create virtual environment ───────────────────────────────────
echo.
echo [2/6] Creating virtual environment...
if exist "%VENV%" (
    echo  Virtual environment already exists at .venv
    echo  Recreating...
    rmdir /s /q "%VENV%" 2>nul
)

python -m venv "%VENV%"
if errorlevel 1 (
    echo  ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)
echo  Created .venv

:: Activate venv
call "%VENV%\Scripts\activate.bat"

:: Upgrade pip
echo  Upgrading pip...
python -m pip install --upgrade pip --quiet 2>nul

:: ── Step 2: Install Python packages ──────────────────────────────────────
echo.
echo [3/6] Installing Python packages (this may take a few minutes)...
echo  Installing core packages...
pip install opencv-python Pillow sympy numpy reportlab pytesseract --quiet 2>nul
if errorlevel 1 (
    echo  ERROR: Failed to install core packages.
    pause
    exit /b 1
)
echo  Core packages installed.

echo  Installing pix2tex (math OCR model)...
pip install pix2tex --quiet 2>nul
if errorlevel 1 (
    echo  WARNING: pix2tex installation failed. Math OCR will use Tesseract only.
    echo  You can try installing manually later: pip install pix2tex
)
echo  pix2tex installed.

:: ── Step 3: Install Tesseract OCR ────────────────────────────────────────
echo.
echo [4/6] Installing Tesseract OCR...

:: Check if already installed
set "TESS_FOUND=0"
where tesseract >nul 2>&1 && set "TESS_FOUND=1"
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" set "TESS_FOUND=1"
if exist "%ProgramFiles%\Tesseract-OCR\tesseract.exe" set "TESS_FOUND=1"

if "!TESS_FOUND!"=="1" (
    echo  Tesseract is already installed.
    goto :tess_done
)

echo  Downloading Tesseract OCR installer (~45 MB)...
echo  Source: UB-Mannheim build (includes trained data for many languages)

:: Download with PowerShell
powershell -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
    "$ProgressPreference = 'SilentlyContinue'; " ^
    "Invoke-WebRequest -Uri '%TESSERACT_URL%' -OutFile '%TESSERACT_EXE%'" 2>nul

if not exist "%TESSERACT_EXE%" (
    echo.
    echo  WARNING: Could not download Tesseract automatically.
    echo  Manual download: https://github.com/UB-Mannheim/tesseract/wiki
    echo  Run the installer, then re-run this script.
    goto :tess_done
)

echo  Installing Tesseract (silent mode)...
"%TESSERACT_EXE%" /S /D="C:\Program Files\Tesseract-OCR"
if errorlevel 1 (
    echo.
    echo  WARNING: Tesseract installation may have failed.
    echo  If you see errors, try running this script as Administrator.
    echo  Or install manually: https://github.com/UB-Mannheim/tesseract/wiki
)

:: Add to PATH for current session
set "PATH=C:\Program Files\Tesseract-OCR;%PATH%"

:: Clean up installer
del "%TESSERACT_EXE%" 2>nul

:tess_done
:: ── Step 4: Install Polish language data for Tesseract ───────────────────
echo.
echo [5/6] Downloading Polish language data for Tesseract...

set "TESS_DATA=C:\Program Files\Tesseract-OCR\tessdata"
if exist "%TESS_DATA%\pol.traineddata" (
    echo  Polish language data already present.
    goto :lang_done
)

if not exist "%TESS_DATA%" (
    echo  WARNING: Tesseract tessdata directory not found.
    echo  Skipping Polish language download.
    goto :lang_done
)

echo  Downloading pol.traineddata...
powershell -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
    "$ProgressPreference = 'SilentlyContinue'; " ^
    "Invoke-WebRequest -Uri 'https://github.com/tesseract-ocr/tessdata/raw/main/pol.traineddata' " ^
    "-OutFile '%TESS_DATA%\pol.traineddata'" 2>nul

if exist "%TESS_DATA%\pol.traineddata" (
    echo  Polish language data downloaded.
) else (
    echo  WARNING: Could not download Polish language data.
    echo  You can download manually from: https://github.com/tesseract-ocr/tessdata
)

:lang_done
:: ── Step 5: Download handwriting font ────────────────────────────────────
echo.
echo [6/6] Downloading handwriting font...

if not exist "%FONTS%" mkdir "%FONTS%"

if exist "%FONTS%\Caveat-Regular.ttf" (
    echo  Handwriting font already present.
    goto :font_done
)

echo  Downloading Caveat font from Google Fonts...
powershell -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
    "$ProgressPreference = 'SilentlyContinue'; " ^
    "$url = 'https://fonts.google.com/download?family=Caveat'; " ^
    "$zip = '%TEMP%\caveat-font.zip'; " ^
    "Invoke-WebRequest -Uri $url -OutFile $zip; " ^
    "Expand-Archive -Path $zip -DestinationPath '%TEMP%\caveat-font' -Force; " ^
    "Get-ChildItem -Path '%TEMP%\caveat-font' -Recurse -Filter '*.ttf' | " ^
    "ForEach-Object { Copy-Item $_.FullName '%FONTS%' -Force }"

if exist "%FONTS%\Caveat-Regular.ttf" (
    echo  Caveat font downloaded to assets\fonts\
) else (
    echo  WARNING: Could not download font automatically.
    echo  The app will fall back to system fonts.
    echo  You can download Caveat manually from: https://fonts.google.com/specimen/Caveat
)

:font_done
:: ── Create launcher ──────────────────────────────────────────────────────
echo.
echo Creating launcher scripts...

(
    echo @echo off
    echo title MathExerciseSolver
    echo cd /d "%%~dp0"
    echo call .venv\Scripts\activate.bat
    echo python main.py --gui
    echo if errorlevel 1 pause
) > "%ROOT%MathExerciseSolver.bat"

(
    echo @echo off
    echo title MathExerciseSolver - CLI
    echo cd /d "%%~dp0"
    echo call .venv\Scripts\activate.bat
    echo echo.
    echo echo Drag and drop an image onto this file, or run:
    echo echo   python main.py path\to\image.png
    echo echo.
    echo set /p "IMG=Image path: "
    echo python main.py %%IMG%% --pdf
    echo echo.
    echo pause
) > "%ROOT%MathExerciseSolver-CLI.bat"

echo  Created MathExerciseSolver.bat (GUI launcher)
echo  Created MathExerciseSolver-CLI.bat (CLI launcher)

:: ── Create output directory ──────────────────────────────────────────────
if not exist "%OUTPUT%" mkdir "%OUTPUT%"

:: ── Done ─────────────────────────────────────────────────────────────────
echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║                   INSTALLATION COMPLETE                  ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.
echo  To launch the app, double-click:
echo    MathExerciseSolver.bat      (GUI mode)
echo    MathExerciseSolver-CLI.bat  (CLI mode)
echo.
echo  Or from command line:
echo    .venv\Scripts\activate
echo    python main.py --gui
echo    python main.py image.png --pdf
echo.
echo  Run 'python main.py --status' to verify all dependencies.
echo.
pause
