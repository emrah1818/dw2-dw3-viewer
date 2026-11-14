"""Launch the frozen desktop and require WebGL plus the Python bridge."""
from pathlib import Path
import json
import os
import subprocess
import sys

exe = Path(sys.argv[1]).resolve()
report = Path('windows-smoke.json').resolve()
env = dict(os.environ)
env['QTWEBENGINE_CHROMIUM_FLAGS'] = '--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader'
proc = subprocess.run([str(exe), '--smoke-test', '--smoke-report=' + str(report)], env=env, timeout=60)
if proc.returncode != 0 or not report.is_file() or not json.loads(report.read_text())['ok']:
    raise SystemExit('Frozen desktop smoke test failed')
print(report.read_text())
