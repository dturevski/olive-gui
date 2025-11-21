# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['olive.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('resources/fonts/*.ttf', 'resources/fonts'),
        ('resources/fonts/gc2.gif', 'resources/fonts'),
        ('resources/fonts/roboto/*.ttf', 'resources/fonts/roboto'),
        ('conf/*.yaml', 'conf'),
        ('conf/*.txt', 'conf'),
        ('conf/dist/*.yaml', 'conf/dist'),
        ('build/py', 'popeye'),
        ('yacpdb/indexer/indexer.md', 'yacpdb/indexer'),
        ('yacpdb/schemas/*', 'yacpdb/schemas'),
        ('p2w/parser.out', 'p2w'),
    ],
    hiddenimports=['base', 'gui', 'resources', 'model', 'board', 'popeye', 'chest', 'conf', 'lang', 'options', 'pbm', 'fancy', 'validate'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='olive',
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

app = BUNDLE(
    exe,
    name='olive.app',
    icon='resources/icons/olive.ico',
    bundle_identifier=None,
)
