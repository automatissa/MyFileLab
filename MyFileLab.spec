# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('LICENSE', '.'),
        ('TERMS_OF_USE.md', '.'),
        ('icon_autopdf.ico', '.'),
    ],
    hiddenimports=[
        'certifi',
        'curl_cffi',
        'yt_dlp.compat._legacy',
        'features',
        'features.base_feature',
        'features.pdf_tools_feature',
        'features.pdf_export_feature',
        'features.image_tools_feature',
        'features.video_downloader_feature',
        'features.metadata_feature',
        'features.legal_feature',
        'features.utils',
    ],
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
    name='MyFileLab',
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
    icon=['icon_autopdf.ico'],
)
