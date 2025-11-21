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
        ('p2w/parser.out', 'p2w'),
    ],
    hiddenimports=[
        'base', 'board', 'chest', 'conf', 'fancy', 'gui', 'lang', 'model', 
        'options', 'pbm', 'popeye', 'resources',
        'exporters', 'exporters.html', 'exporters.latex', 'exporters.pdf', 'exporters.xfen2img',
        'legacy', 'legacy.chess', 'legacy.popeye',
        'widgets', 'widgets.PlainTextEdit', 'widgets.ClickableLabel', 
        'widgets.YesNoDialog', 'widgets.YesNoCancelDialog',
        'yacpdb', 'yacpdb.entry', 'yacpdb.storage',
        'yacpdb.indexer', 'yacpdb.indexer.cruncher', 'yacpdb.indexer.metadata',
        'p2w', 'p2w.parser', 'p2w.lexer', 'p2w.nodes', 'p2w.parsetab',
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
