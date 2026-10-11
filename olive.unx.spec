# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['olive.py'],
    pathex=['.'],
    binaries=[
        ('build/py', 'popeye'),
    ],
    datas=[
        ('conf', 'conf'),
        ('resources/fonts', 'resources/fonts'),
        ('yacpdb/indexer/indexer.md', 'yacpdb/indexer'),
        ('yacpdb/schemas', 'yacpdb/schemas'),
        ('yacpdb/resources', 'yacpdb/resources'),
    ],
    hiddenimports=[
        'base', 'yacpdb.board', 'chest', 'conf', 'fancy', 'gui', 'lang', 'model',
        'options', 'pbm', 'popeye', 'resources',
        'exporters', 'exporters.html', 'exporters.latex', 'exporters.pdf', 'exporters.xfen2img',
        'yacpdb.legacy', 'yacpdb.legacy.chess', 'yacpdb.legacy.popeye',
        'widgets', 'widgets.PlainTextEdit', 'widgets.ClickableLabel',
        'widgets.YesNoDialog', 'widgets.YesNoCancelDialog',
        'yacpdb', 'yacpdb.entry', 'yacpdb.storage',
        'yacpdb.indexer', 'yacpdb.indexer.cruncher', 'yacpdb.indexer.metadata',
        'yacpdb.p2w', 'yacpdb.p2w.parser', 'yacpdb.p2w.lexer', 'yacpdb.p2w.nodes',
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
    icon='resources/icons/olive.ico',
)
