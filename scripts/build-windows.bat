@echo off
REM Windows-specific build and packaging script
REM Creates .exe and installer with NSIS

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set BUILD_DIR=%PROJECT_ROOT%\build\windows
set APP_NAME=Murmur-Brain

echo ==================================================
echo Windows Build and Packaging Script
echo ==================================================

cd /d "%PROJECT_ROOT%"

REM Step 1: Run main build
echo.
echo [*] Running main build process...
python build-all.py --windows

if errorlevel 1 (
    echo [X] Build failed
    exit /b 1
)

REM Step 2: Code signing (if configured)
echo.
echo [*] Checking for code signing...

if defined CODESIGN_CERT (
    echo [*] Code signing with certificate: %CODESIGN_CERT%

    set EXE_PATH=%BUILD_DIR%\%APP_NAME%.exe

    REM Sign the executable
    signtool sign /f "%CODESIGN_CERT%" /p "%CODESIGN_PASSWORD%" ^
        /t http://timestamp.digicert.com ^
        /fd SHA256 ^
        "!EXE_PATH!"

    REM Verify signature
    signtool verify /pa "!EXE_PATH!"

    echo [+] Code signing completed
) else (
    echo [!] CODESIGN_CERT not set, skipping code signing
    echo     To enable signing, set: CODESIGN_CERT=path\to\certificate.pfx
    echo     And: CODESIGN_PASSWORD=your_password
)

REM Step 3: Create installer with NSIS (if available)
echo.
echo [*] Creating installer...

where makensis >nul 2>nul
if %errorlevel% equ 0 (
    set NSI_SCRIPT=%SCRIPT_DIR%\installer.nsi

    if exist "!NSI_SCRIPT!" (
        makensis "!NSI_SCRIPT!"
        echo [+] Installer created
    ) else (
        echo [!] NSIS script not found: !NSI_SCRIPT!
        echo     Create installer.nsi for custom installer
    )
) else (
    echo [!] NSIS not found. Install from: https://nsis.sourceforge.io/
    echo     Skipping installer creation
)

REM Summary
echo.
echo ==================================================
echo Build Complete!
echo ==================================================
echo Output location: %BUILD_DIR%
echo.
dir /b "%BUILD_DIR%"
echo.

endlocal
