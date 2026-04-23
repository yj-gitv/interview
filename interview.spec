# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for 面试助手 (Interview Assistant).

Usage:  pyinstaller interview.spec
Output: dist/面试助手/面试助手.exe  (one-dir mode for faster startup)
"""

import os
import sys
import importlib

block_cipher = None

# Locate sherpa_onnx package to collect its native binaries
sherpa_binaries = []
try:
    import sherpa_onnx
    sherpa_pkg_dir = os.path.dirname(sherpa_onnx.__file__)
    for f in os.listdir(sherpa_pkg_dir):
        full = os.path.join(sherpa_pkg_dir, f)
        if os.path.isfile(full) and (f.endswith('.dll') or f.endswith('.pyd') or f.endswith('.so')):
            sherpa_binaries.append((full, 'sherpa_onnx'))
except ImportError:
    print("WARNING: sherpa_onnx not found, native binaries will be missing")

a = Analysis(
    ['launcher.py'],
    pathex=['backend'],
    binaries=sherpa_binaries,
    datas=[
        ('backend/app', 'app'),
    ],
    hiddenimports=[
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
        'fastapi',
        'starlette',
        'starlette.responses',
        'starlette.staticfiles',
        'pydantic',
        'pydantic_settings',
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'multipart',
        'httpx',
        'openai',
        'numpy',
        'sherpa_onnx',
        'sounddevice',
        'pymupdf',
        'docx',
        'fpdf',
        'fpdf.enums',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='面试助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='面试助手',
)
