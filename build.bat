@echo off
setlocal
title LibreLinkUp Widget - Build

echo ============================================
echo  LibreLinkUp Widget - PyInstaller Build
echo ============================================
echo.

:: Install build deps if not present
python -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

:: Add UPX to PATH if available (for exe compression)
set "UPX_DIR="
where upx >nul 2>&1
if %errorlevel%==0 (
    set "UPX_DIR=%PATH%"
) else (
    for /d %%d in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\UPX.UPX*") do (
        for /r "%%d" %%f in (upx.exe) do set "UPX_DIR=%%~dpf"
    )
    if defined UPX_DIR set "PATH=%UPX_DIR%;%PATH%"
)

echo Building one-file, no-console executable (this takes a few minutes)...
echo.

python -m PyInstaller --clean --noconfirm LibreLinkUpWidget.spec

if %errorlevel%==0 (
    echo.
    echo  ============================================
    echo   Build complete!
    echo   Output: dist\LibreLinkUpWidget.exe
    echo  ============================================
) else (
    echo.
    echo  [ERROR] Build failed. See messages above.
)

echo.
pause
