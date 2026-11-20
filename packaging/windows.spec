# Build from the pinned requirements-build.txt on Windows x64.
from pathlib import Path

root = Path(SPECPATH).parent
native = root / 'mc_finder' / '_native'
data = [(str(p), 'mc_finder/_native') for p in native.iterdir()
        if p.name == 'manifest.json' or 'license' in p.name.lower()]

a = Analysis(
    [str(root / 'scripts' / 'windows_entry.py')],
    pathex=[str(root)],
    binaries=[(str(native / 'finder.dll'), 'mc_finder/_native')],
    datas=data,
    hiddenimports=[],
    excludes=['tkinter', 'numpy', 'scipy', 'ziglang', 'PySide6.QtWebEngineCore',
              'PySide6.QtWebEngineWidgets', 'PySide6.QtQml', 'PySide6.QtQuick'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name='MinecraftStructureFinder', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False,
    version=str(root / 'packaging' / 'windows_version.txt'),
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False,
               name='MinecraftStructureFinder')
