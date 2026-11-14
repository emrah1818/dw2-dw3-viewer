"""Build the bundled headless MIT-licensed DW3 converter (MSVC or GCC)."""
from pathlib import Path
import os
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
source = root / 'third_party' / 'dw3_converter'
out = root / 'tools' / 'dw3_converter'
out.mkdir(parents=True, exist_ok=True)
sources = [str(source / (n + '.cpp')) for n in ('cli', 'model', 'game', 'dw2', 'gltf', 'stage_export')]
cxx = os.environ.get('CXX') or shutil.which('g++') or shutil.which('cl')
if not cxx:
    raise SystemExit('C++ compiler missing: install MSVC Build Tools or GCC.')
target = out / ('dw3_converter.exe' if os.name == 'nt' else 'dw3_converter')
if Path(cxx).name.lower() in ('cl', 'cl.exe'):
    cmd = [cxx, '/nologo', '/std:c++17', '/EHsc', '/O2', '/I' + str(source), *sources, '/Fe:' + str(target)]
else:
    cmd = [cxx, '-std=c++17', '-O2', '-I' + str(source), *sources, '-o', str(target)]
subprocess.run(cmd, cwd=out, check=True)
print(target)
