# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for 面试助手 (Interview Assistant).

Build: pyinstaller interview.spec
Output: dist/interview-assistant/面试助手.exe
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all submodules for packages that use dynamic imports
hidden_imports = [
    *collect_submodules("uvicorn"),
    *collect_submodules("sqlalchemy"),
    *collect_submodules("pydantic"),
    *collect_submodules("pydantic_settings"),
    "app.main",
    "app.config",
    "app.database",
    "app.models",
    "app.models.interview",
    "app.models.candidate",
    "app.models.position",
    "app.models.transcript",
    "app.models.summary",
    "app.models.evaluation",
    "app.routers.candidates",
    "app.routers.comparison",
    "app.routers.interviews",
    "app.routers.matches",
    "app.routers.positions",
    "app.routers.summaries",
    "app.routers.settings_api",
    "app.services.interview_manager",
    "app.services.transcription",
    "app.services.audio_processing",
    "app.services.audio_capture",
    "app.services.realtime_analysis",
    "app.services.summary_gen",
    "app.services.question_gen",
    "app.services.matching",
    "app.services.pdf_export",
    "app.services.pii_masking",
    "app.services.llm_client",
    "app.services.webhook_push",
    "app.services.criteria_utils",
    "app.services.speaker_diarization",
    "multipart",
    "httptools",
    "websockets",
    "uvloop" if sys.platform != "win32" else "asyncio",
    "sherpa_onnx",
    "sounddevice",
    "numpy",
    "fpdf",
]

a = Analysis(
    ["launcher.py"],
    pathex=["backend"],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PIL", "scipy", "torch", "torchaudio"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="面试助手",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="interview-assistant",
)
