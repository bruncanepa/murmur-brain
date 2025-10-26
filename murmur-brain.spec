# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Murmur Brain
Builds standalone executable with embedded Python backend and static frontend
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the project root directory
project_root = Path('.').absolute()
server_dir = project_root / 'server'
dist_dir = project_root / 'dist'

# Platform-specific settings
IS_MACOS = sys.platform == 'darwin'
IS_WINDOWS = sys.platform == 'win32'
IS_LINUX = sys.platform.startswith('linux')

# Application metadata
APP_NAME = 'Murmur-Brain'
VERSION = '2.0.0'
AUTHOR = 'Murmur Brain'
DESCRIPTION = 'Talk to Your Library with AI - No Internet, No Third Parties, Just You & Your Documents'

# Collect all Python dependencies
hiddenimports = [
    'fastapi',
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'pydantic',
    'pypdf',
    'python_multipart',
    'aiofiles',
    'sqlite3',
    'asyncio',
    'webview',
    'webview.window',
]

# Collect data files
datas = []

# Add the frontend dist folder
if dist_dir.exists():
    datas.append((str(dist_dir), 'dist'))

# Add the new modular backend structure
datas.append((str(server_dir / 'core'), 'core'))
datas.append((str(server_dir / 'modules'), 'modules'))

# Analysis - what to include
a = Analysis(
    [str(server_dir / 'desktop.py')],
    pathex=[str(project_root), str(server_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'numpy',
        'pandas',
        'tkinter',
        'PIL',
        'setuptools',
        'distutils'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ - Python archive
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Platform-specific executable configuration
if IS_MACOS:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,  # No console window
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,  # Set this for code signing
        entitlements_file=None,  # Set this for entitlements
        icon=None,  # TODO: Add icon
    )

    # macOS .app bundle
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )

    app = BUNDLE(
        coll,
        name=f'{APP_NAME}.app',
        icon=None,  # TODO: Add .icns icon
        bundle_identifier=f'com.murmurbrain.{APP_NAME.lower()}',
        version=VERSION,
        info_plist={
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': 'Murmur Brain',
            'CFBundleVersion': VERSION,
            'CFBundleShortVersionString': VERSION,
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '10.13.0',
            'NSHumanReadableCopyright': f'Copyright © 2024 {AUTHOR}',
        },
    )

elif IS_WINDOWS:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,  # No console window
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,  # Set this for code signing
        entitlements_file=None,
        icon=None,  # TODO: Add .ico icon
    )

else:  # Linux
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,  # TODO: Add .png icon
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )
