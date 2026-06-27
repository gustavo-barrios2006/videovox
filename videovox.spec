# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata


a = Analysis(
    ['videovox.pyw'],
    pathex=[],
    binaries=[],
    datas=copy_metadata('imageio') + copy_metadata('imageio-ffmpeg'),
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch',
        'tensorflow',
        'torchvision',
        'transformers',
        'scipy',
        'pandas',
        'sklearn',
        'cv2',
        'matplotlib',
        'tkinter',
        'sqlite3',
        'h5py',
        'IPython',
        'jedi',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'notebook',
        'docutils',
        'llvmlite',
        'numba'
    ],
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
    name='videovox',
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
)
