@echo off
REM Build script for Local Brain on Windows
REM Builds the React frontend and packages everything into a single executable

echo ======================================
echo Local Brain - Build Script (Windows)
echo ======================================

REM Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Step 1: Build React frontend
echo.
echo Step 1: Building React frontend...
call npm run build

if not exist "dist\" (
    echo Error: dist folder not found after build
    exit /b 1
)

echo [32mReact frontend built successfully[0m

REM Step 2: Package with PyInstaller
echo.
echo Step 2: Packaging with PyInstaller...
pyinstaller local-brain.spec --clean --noconfirm

if %errorlevel% equ 0 (
    echo [32mBuild completed successfully![0m
    echo.
    echo Executable location:
    echo   -^> dist\LocalBrain.exe
    echo.
    echo To run:
    echo   dist\LocalBrain.exe
) else (
    echo [33mBuild failed. Check the output above for errors.[0m
    exit /b 1
)

echo.
echo ======================================
echo Build process complete!
echo ======================================

pause
