"""Check the PC-port checkout used for the companion build.

Since 0.16b the overlay API 2 changes live in emrah1818/dw2-pc-port itself (branch
development/dw3-mod-studio, doc/MOD_API2.md); the build only verifies the pinned commit.
"""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[1]
repo = Path(sys.argv[1]).resolve()
expected = (root / 'integration/pc_port_base.txt').read_text().strip()
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
if head != expected:
    raise SystemExit('PC-port commit differs from integration/pc_port_base.txt')
if subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo, text=True).strip():
    raise SystemExit('PC-port checkout must be clean')
if not (repo / 'doc/MOD_API2.md').is_file():
    raise SystemExit('PC-port checkout has no overlay API 2 (doc/MOD_API2.md missing)')
print('PC-port', head, 'with overlay API 2')
