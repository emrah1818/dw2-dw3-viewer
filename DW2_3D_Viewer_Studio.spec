# -*- mode: python ; coding: utf-8 -*-
"""Windows PyInstaller spec. Build on Windows with EXE_ERSTELLEN.bat."""
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

root = Path(SPECPATH)
extra_data = [
    (str(root / 'assets'), 'assets'),
    (str(root / 'www'), 'www'),
    (str(root / 'licenses'), 'licenses'),
    (str(root / 'tools'), 'tools'),
    (str(root / 'data'), 'data'),
]
extra_bins = []
hidden = ['android_api', 'android_edit', 'studio'] + collect_submodules('dw2studio')
for module in ('vtkmodules', 'trimesh', 'pyqtgraph'):
    d, b, h = collect_all(module)
    extra_data.extend(d)
    extra_bins.extend(b)
    hidden.extend(h)
# vtkmodules uses dynamic imports for rendering and native OpenGL modules.
hidden += collect_submodules('vtkmodules')

analysis = Analysis(
    [str(root / 'main.py')],
    pathex=[str(root)],
    binaries=extra_bins,
    datas=extra_data,
    hiddenimports=sorted(set(hidden)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide2', 'PySide6', 'PyQt5', 'tkinter'],
    noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name='DW2_3D_Viewer_Studio',
    console=False,
    icon=str(root / 'assets' / 'DW2_3D_Viewer.ico'),
    version=str(root / 'windows_version_info.txt'),
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe, analysis.binaries, analysis.datas,
    strip=False, upx=False,
    name='DW2_3D_Viewer_Studio',
)
