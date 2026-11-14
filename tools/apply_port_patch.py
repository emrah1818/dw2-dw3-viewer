"""Apply the API 2 patch only to its pinned, clean PC-port source checkout."""
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
repo=Path(sys.argv[1]).resolve()
expected=(root/'integration/pc_port_base.txt').read_text().strip()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
if head!=expected:raise SystemExit('PC-port commit differs from integration/pc_port_base.txt')
if subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True).strip():raise SystemExit('PC-port checkout must be clean')
subprocess.run(['git','apply','--check',str(root/'integration/pc_port_api2.patch')],cwd=repo,check=True)
subprocess.run(['git','apply',str(root/'integration/pc_port_api2.patch')],cwd=repo,check=True)
