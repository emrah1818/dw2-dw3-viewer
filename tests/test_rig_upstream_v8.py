"""Cross-check the native writer with the unchanged bundled jype C++ reader."""
from pathlib import Path
import shutil,struct,subprocess
import pytest
from test_rig_import_v8 import project


def test_new_native_files_parse_in_upstream_cpp(tmp_path):
    compiler=shutil.which('g++')
    if not compiler:pytest.skip('Optional upstream comparison requires g++.')
    root=Path(__file__).resolve().parents[1];upstream=root/'third_party'/'dw2_model_converter'/'src';exe=tmp_path/'read_upstream'
    subprocess.run([compiler,'-std=c++17','-O2','-I',str(upstream),str(Path(__file__).with_name('upstream_rig_check.cpp')),str(upstream/'dw2_model.cpp'),str(upstream/'dw2_anim.cpp'),'-o',str(exe)],check=True,capture_output=True)
    p=project(tmp_path);p.assignment[:]=[0,1];p.settings[1].motion_scale=.5;p.settings[1].offset=[2,0,0]
    model,_=p.build_native();animation=p.adjusted_animation_bytes()['A003TEST.BIN'];(tmp_path/'model.bin').write_bytes(model);(tmp_path/'anim.bin').write_bytes(animation)
    result=subprocess.run([str(exe),str(tmp_path/'model.bin'),str(tmp_path/'anim.bin')],capture_output=True,text=True,check=True)
    rows=result.stdout.splitlines();assert rows[:5]==['2 2','3 1 1','3 1 1','2 255 0','2 254 1']
    assert [list(map(int,line.split())) for line in rows[5:]]==[list(struct.unpack_from('<12h',animation,offset)) for offset in (44,68,92)]
