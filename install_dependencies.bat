@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  LibreLinkUp Widget - Dependency Installer
::  Installs everything this app needs on a BARE Windows machine
::  (no Python, no pip, no nothing).
::  Requires: Python 3.8+ (installed below if missing)
::  Installs: pip, PySide6, requests
:: ============================================================

title LibreLinkUp Widget - Setup
echo.
echo  ============================================
echo   LibreLinkUp Widget - Dependency Installer
echo  ============================================
echo.

:: ------------------------------------------------------------
:: Step 1 - Python
:: ------------------------------------------------------------
echo  [1/4] Checking for Python...
python --version >nul 2>&1
if %errorlevel%==0 (
    echo        Python is already installed.
    goto :has_python
)

echo        Python NOT found. Installing Python 3.12...
echo        This downloads the official installer from python.org.

:: Bare Windows: use winget if available (fastest, uses Microsoft's package manager)
:: NOTE: The fallback label must be OUTSIDE an if/else block for cmd reliability.
winget --version >nul 2>&1
if %errorlevel%==0 (
    echo        Using winget to install Python...
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    if %errorlevel%==0 (
        echo        Python installed via winget.
        goto :has_python
    ) else (
        echo        [WARN] winget install failed, falling back to direct download...
    )
)
echo        Downloading Python directly (no winget or winget failed)...
set "PY_URL=https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe"
set "PY_FILE=%TEMP%\python-3.12.9-amd64.exe"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; ^
     Invoke-WebRequest -Uri '!PY_URL!' -OutFile '!PY_FILE!'"
if not exist "!PY_FILE!" (
    echo  [ERROR] Failed to download Python. Check your internet connection.
    pause
    exit /b 1
)
echo        Installing Python (silent, adds to PATH)...
"!PY_FILE!" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
echo        Python install finished.

:: Refresh PATH so 'python' is findable in this session
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"

:has_python
python --version

:: ------------------------------------------------------------
:: Step 2 - pip (bundled with most Python installs, but ensure)
:: ------------------------------------------------------------
echo.
echo  [2/4] Ensuring pip is available...
python -m pip --version >nul 2>&1
if %errorlevel%==0 (
    echo        pip is available.
) else (
    echo        pip missing - bootstrapping it...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%TEMP%\get-pip.py'"
    python "%TEMP%\get-pip.py"
)
python -m pip --version

:: ------------------------------------------------------------
:: Step 3 - Upgrade pip itself (recommended for fresh installs)
:: ------------------------------------------------------------
echo.
echo  [3/4] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo        pip upgraded.

:: ------------------------------------------------------------
:: Step 4 - Install app dependencies (PySide6 + requests)
:: ------------------------------------------------------------
echo.
echo  [4/4] Installing app dependencies (PySide6, requests)...
echo        This is the large Qt download (~150 MB) and may take a few minutes.
echo.
python -m pip install --upgrade PySide6 requests

if %errorlevel%==0 (
    echo.
    echo  ============================================
    echo   All dependencies installed successfully!
    echo  ============================================
    echo.
    echo   You can now run the app with:
    echo     python main.py
    echo.
) else (
    echo.
    echo  [ERROR] Something went wrong during dependency install.
    echo          Try running this script again, or install manually:
    echo          pip install PySide6 requests
)

echo.
pause
