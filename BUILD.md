# Build Guide for Murmur Brain

This guide explains how to build Murmur Brain as standalone executables for macOS, Windows, and Linux.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Build Process](#build-process)
- [Platform-Specific Builds](#platform-specific-builds)
- [Code Signing](#code-signing)
- [Distribution](#distribution)
- [Troubleshooting](#troubleshooting)

---

## Overview

Murmur Brain uses a multi-stage build process:

1. **Frontend Build**: React app compiled with Vite → static files
2. **Backend Bundle**: Python FastAPI server packaged with PyInstaller
3. **Platform Packaging**: Creates platform-specific installers

### Architecture

```
┌─────────────────────────────────────────┐
│          Murmur Brain Executable        │
├─────────────────────────────────────────┤
│  Python Backend (PyInstaller)           │
│  ├─ FastAPI server                      │
│  ├─ Ollama integration                  │
│  ├─ SQLite database                     │
│  └─ Static files (React app)            │
└─────────────────────────────────────────┘
```

---

## Prerequisites

### Required Tools

#### All Platforms
- **Python 3.8+**: Backend runtime
- **Node.js 16+**: Frontend build
- **pnpm**: Package manager (`npm install -g pnpm`)
- **PyInstaller**: Python packager (`pip3 install pyinstaller`)

#### macOS
- **Xcode Command Line Tools**: `xcode-select --install`
- **create-dmg** (optional): `brew install create-dmg`

#### Windows
- **Windows SDK**: For code signing (optional)
- **NSIS** (optional): For installer creation

#### Linux
- **appimagetool** (optional): For AppImage creation
- **dpkg-deb** (optional): For .deb package creation

### Installing Prerequisites

**macOS:**
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python node
npm install -g pnpm
pip3 install pyinstaller

# Optional: for DMG creation
brew install create-dmg
```

**Windows (PowerShell as Administrator):**
```powershell
# Install Chocolatey (if not already installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install dependencies
choco install python nodejs
npm install -g pnpm
pip3 install pyinstaller

# Optional: for installer creation
choco install nsis
```

**Linux (Ubuntu/Debian):**
```bash
# Update package list
sudo apt update

# Install dependencies
sudo apt install -y python3 python3-pip nodejs npm
sudo npm install -g pnpm
pip3 install pyinstaller

# Optional: for AppImage
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
```

---

## Quick Start

### Option 1: Using npm/pnpm Scripts

```bash
# Build for current platform
pnpm build:exe

# Build for specific platform
pnpm build:macos    # macOS only
pnpm build:windows  # Windows only
pnpm build:linux    # Linux only

# Build for all platforms (limited by current OS)
pnpm build:all

# Clean build artifacts
pnpm build:clean
```

### Option 2: Using Python Script Directly

```bash
# Build for current platform
python3 build-all.py

# Build for specific platform
python3 build-all.py --macos
python3 build-all.py --windows
python3 build-all.py --linux

# Build for all platforms
python3 build-all.py --all

# Clean build artifacts
python3 build-all.py --clean

# Check dependencies only
python3 build-all.py --check
```

### Option 3: Using Platform-Specific Scripts

**macOS:**
```bash
./scripts/build-macos.sh
```

**Windows:**
```batch
scripts\build-windows.bat
```

**Linux:**
```bash
./scripts/build-linux.sh
```

---

## Build Process

### Detailed Build Steps

#### 1. Clean Previous Builds (Optional)

```bash
python3 build-all.py --clean
```

This removes:
- `build/` - Build output directory
- `dist_pyinstaller/` - PyInstaller temporary files
- `__pycache__/` - Python cache files
- `*.pyc` - Compiled Python files

#### 2. Check Dependencies

```bash
python3 build-all.py --check
```

Verifies:
- ✓ Node.js and pnpm installed
- ✓ Python 3 and pip3 installed
- ✓ PyInstaller available
- ✓ Platform-specific tools (optional)

#### 3. Build Frontend

```bash
pnpm install  # Install dependencies
pnpm build    # Build with Vite
```

Output: `dist/` folder with static files

#### 4. Build Backend

```bash
pip3 install -r server/requirements.txt  # Install Python deps
pyinstaller --clean -y murmur-brain.spec  # Build executable
```

Output: Platform-specific executable in `dist/`

#### 5. Package Application

Platform-specific packaging:
- **macOS**: `.app` bundle + `.dmg` installer
- **Windows**: `.exe` + installer (NSIS)
- **Linux**: AppImage + `.deb` package

---

## Platform-Specific Builds

### macOS Build

**Output Structure:**
```
build/macos/
├── Murmur-Brain.app          # Application bundle
└── Murmur-Brain.dmg          # Disk image installer (optional)
```

**Build Command:**
```bash
./scripts/build-macos.sh
```

**What it does:**
1. Builds frontend and backend
2. Creates `.app` bundle
3. Signs the app (if configured)
4. Creates `.dmg` installer (if create-dmg available)
5. Notarizes the app (if credentials configured)

**Running the app:**
```bash
open build/macos/Murmur-Brain.app
```

---

### Windows Build

**Output Structure:**
```
build/windows/
├── Murmur-Brain.exe          # Standalone executable
└── Murmur-Brain-Setup.exe    # Installer (optional)
```

**Build Command:**
```batch
scripts\build-windows.bat
```

**What it does:**
1. Builds frontend and backend
2. Creates standalone `.exe`
3. Signs the executable (if configured)
4. Creates installer with NSIS (if available)

**Running the app:**
```batch
build\windows\Murmur-Brain.exe
```

---

### Linux Build

**Output Structure:**
```
build/linux/
├── Murmur-Brain/                    # Application directory
├── Murmur-Brain-x86_64.AppImage     # Portable AppImage (optional)
└── Local-Brain_2.0.0_amd64.deb     # Debian package (optional)
```

**Build Command:**
```bash
./scripts/build-linux.sh
```

**What it does:**
1. Builds frontend and backend
2. Creates application directory
3. Creates AppImage (if appimagetool available)
4. Creates `.deb` package (if dpkg-deb available)

**Running the app:**
```bash
# From directory
./build/linux/Murmur-Brain/Murmur-Brain

# From AppImage
chmod +x build/linux/Murmur-Brain-x86_64.AppImage
./build/linux/Murmur-Brain-x86_64.AppImage

# From .deb
sudo dpkg -i build/linux/Local-Brain_2.0.0_amd64.deb
murmur-brain
```

---

## Code Signing

Code signing ensures users can trust your application. See [scripts/SIGNING_SETUP.md](scripts/SIGNING_SETUP.md) for detailed instructions.

### Quick Setup

**macOS:**
```bash
export CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
export APPLE_ID="your-apple-id@example.com"
export APPLE_ID_PASSWORD="xxxx-xxxx-xxxx-xxxx"
export TEAM_ID="YOUR_TEAM_ID"
```

**Windows:**
```batch
set CODESIGN_CERT=C:\path\to\certificate.pfx
set CODESIGN_PASSWORD=your_certificate_password
```

### Verify Signatures

**macOS:**
```bash
codesign --verify --verbose build/macos/Murmur-Brain.app
spctl -a -vv build/macos/Murmur-Brain.app
```

**Windows:**
```batch
signtool verify /pa build\windows\Murmur-Brain.exe
```

---

## Distribution

### File Sizes (Approximate)

| Platform | Size | Format |
|----------|------|--------|
| macOS .app | 80-120 MB | Application bundle |
| macOS .dmg | 70-100 MB | Compressed installer |
| Windows .exe | 60-90 MB | Standalone executable |
| Windows installer | 60-90 MB | NSIS installer |
| Linux AppImage | 70-100 MB | Portable executable |
| Linux .deb | 60-90 MB | Debian package |

### Upload Locations

1. **GitHub Releases**: Recommended for open-source distribution
   ```bash
   gh release create v2.0.0 \
     build/macos/Murmur-Brain.dmg \
     build/windows/Murmur-Brain-Setup.exe \
     build/linux/Murmur-Brain-x86_64.AppImage
   ```

2. **Direct Download**: Host on your own server
3. **Package Managers**: Submit to Homebrew (macOS), Chocolatey (Windows), etc.

### Distribution Checklist

- [ ] Build for all platforms
- [ ] Test executables on clean systems
- [ ] Sign all executables
- [ ] Create release notes
- [ ] Generate checksums (SHA256)
- [ ] Upload to distribution platform
- [ ] Update download links
- [ ] Announce release

---

## Ollama Dependency

Murmur Brain requires Ollama to be installed and running. The application will detect if Ollama is missing and guide users through installation.

### User Installation Guide

When users first run Murmur Brain without Ollama, they'll see:

**macOS:**
```bash
brew install ollama
ollama serve
```

**Windows:**
```powershell
winget install Ollama.Ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

---

## Troubleshooting

### Build Failures

**Error: "Module not found: PyInstaller"**
```bash
pip3 install pyinstaller
```

**Error: "node: command not found"**
```bash
# Install Node.js for your platform
# macOS: brew install node
# Windows: choco install nodejs
# Linux: sudo apt install nodejs npm
```

**Error: "pnpm: command not found"**
```bash
npm install -g pnpm
```

### PyInstaller Issues

**Error: "Cannot find module 'xyz'"**

Add to `murmur-brain.spec` hiddenimports:
```python
hiddenimports = [
    'fastapi',
    'uvicorn',
    'xyz',  # Add missing module
]
```

**Error: "Failed to execute script"**

Check logs in:
- macOS: Console.app
- Windows: Event Viewer
- Linux: Terminal output

### Platform-Specific Issues

**macOS: "App is damaged and can't be opened"**
```bash
# Remove quarantine attribute
xattr -cr build/macos/Murmur-Brain.app
```

**Windows: "Windows protected your PC"**
- This is expected for unsigned apps
- User can click "More info" → "Run anyway"
- Solution: Purchase code signing certificate

**Linux: "Permission denied"**
```bash
chmod +x build/linux/Murmur-Brain-x86_64.AppImage
```

### Build Size Issues

If executables are too large:

1. **Exclude unnecessary packages** in `murmur-brain.spec`:
   ```python
   excludes=[
       'matplotlib',
       'scipy',
       'numpy',
       'pandas',
   ]
   ```

2. **Use UPX compression** (already enabled in spec file)

3. **Remove debug symbols**:
   ```python
   strip=True  # in murmur-brain.spec
   ```

---

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/build.yml`:

```yaml
name: Build Executables

on:
  push:
    tags:
      - 'v*'

jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install -g pnpm
      - run: pip3 install pyinstaller
      - run: python3 build-all.py --macos
      - uses: actions/upload-artifact@v3
        with:
          name: macos-build
          path: build/macos/

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install -g pnpm
      - run: pip3 install pyinstaller
      - run: python build-all.py --windows
      - uses: actions/upload-artifact@v3
        with:
          name: windows-build
          path: build/windows/

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install -g pnpm
      - run: pip3 install pyinstaller
      - run: python3 build-all.py --linux
      - uses: actions/upload-artifact@v3
        with:
          name: linux-build
          path: build/linux/
```

---

## Support

For build issues:
1. Check this BUILD.md guide
2. Review [scripts/SIGNING_SETUP.md](scripts/SIGNING_SETUP.md) for signing issues
3. Open an issue on GitHub with:
   - Platform and version
   - Build command used
   - Full error output
   - Build environment details

---

## License

MIT License - See LICENSE file for details
