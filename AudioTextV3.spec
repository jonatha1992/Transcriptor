# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\jgcorrea\\Desktop\\Repositorio\\Transcriptor\\Main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\jgcorrea\\Desktop\\Repositorio\\Transcriptor\\ffmpeg', 'ffmpeg/'), ('C:\\Users\\jgcorrea\\Desktop\\Repositorio\\Transcriptor\\Icons', 'Icons/')],
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
    name='AudioTextV3',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\jgcorrea\\Desktop\\Repositorio\\Transcriptor\\icono.ico'],
)
