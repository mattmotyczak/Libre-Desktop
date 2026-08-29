# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for LibreLinkUp Widget.
# Build:  pyinstaller --clean --noconfirm LibreLinkUpWidget.spec
#
# - onefile : bundles everything into a single .exe
# - console=False : no Python/console window at execution (tray widget)
# - upx=True : exe-level compression (requires UPX on PATH or --upx-dir)

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='LibreLinkUpWidget',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['vcruntime*.dll', 'msvcp*.dll'],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
