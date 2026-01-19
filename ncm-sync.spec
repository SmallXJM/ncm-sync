# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import sys
import os

block_cipher = None

# 1. Collect all NCM submodules dynamically to ensure correct import resolution
hiddenimports = (
    collect_submodules("ncm.client.apis")
    + collect_submodules("ncm.server.routers")
    + collect_submodules("ncm.server.websockets")
)

# 2. Add required third-party hidden imports
hiddenimports += [
    "uvicorn",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
]

# 3. Define data files (resources)
datas = [
    ("web/dist", "web/dist"),  # Frontend static files
]

# 4. Analysis
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "PyQt5",
        "PySide6",
        "IPython",
        "pytest",
        "unittest",
        "pdb",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 5. EXE (Single Executable)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ncm-sync',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False if you want a windowed app without console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None, # Add icon if available, e.g., 'resources/icon.ico'
)
