"""Regression: valid DW2 TIM blocks with a different second model-header word.

No assumption about that word's meaning is needed: the original C++ reader
ignores it. Test different values, preserve all source bytes, and exercise
normal UI export followed by native replacement instead of bypassing export.
"""
import copy,json,struct
from pathlib import Path
import pytest
from PyQt6.QtWidgets import QFileDialog,QDialog
from dw2studio.core import digimon_transfer as dt
from dw2studio.core import gltf_textures as gt
from dw2studio.core.catalog import DigimonCandidate
from dw2studio.core.disc import Entry
from dw2studio.core.edit_session import EditSession
from dw2studio.core.native_model import NativeModel
from dw2studio.core.rig_animation import NativeAnimation
from test_digimon_transfer_v36 import donor,target_session


@pytest.mark.parametrize('header_end',[0,64,16448,0xffffffff])
@pytest.mark.parametrize('suffix',['.gltf','.glb'])
def test_normal_ui_export_then_native_import_with_nonmatching_end_word(window,tmp_path,monkeypatch,header_end,suffix):
    path,files,payload=donor(tmp_path)
    model=bytearray(files['M']);struct.pack_into('<I',model,4,header_end);files['M']=bytes(model)
    contents=bytearray();source_entries=[]
    for r,data in files.items():
        source_entries.append(Entry(f'{r}003AGUM.BIN',len(contents)//2048,len(data),False))
        contents.extend(data.ljust(((len(data)+2047)//2048)*2048,b'\0'))
    image=tmp_path/'source.iso';image.write_bytes(contents)
    source=DigimonCandidate(3,'AGUM','Agumon',source_entries)
    window.session=EditSession(image,2048);window.image_path=image;window.entries=source_entries
    window.catalog=[source];window.current=window.loaded_digimon=source;window.active_native=True;window.active_digimon_key=window.key_for(source)
    window.project_model=path
    out=tmp_path/('normal_export'+suffix)
    monkeypatch.setattr(QFileDialog,'getSaveFileName',lambda *a,**k:(str(out),'glTF (*.gltf)' if suffix=='.gltf' else 'GLB (*.glb)'))
    window.update_actions();window.model_buttons[3].click()  # actual 3D-export button
    assert not window.test_errors and out.is_file()
    transfer=dt.read_transfer(out)
    assert transfer.files==files and struct.unpack_from('<I',transfer.files['M'],4)[0]==header_end
    assert len(gt.document(out)['animations'])==2
    window.viewer.load(out);window.viewer.timer.stop()
    assert window.viewer.animations.count()==2
    target,entries,original=target_session(tmp_path)
    candidate=DigimonCandidate(12,'MTGR','Target',entries)
    window.session=target;window.image_path=target.source;window.entries=entries;window.catalog=[candidate];window.current=candidate
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,**k:(str(out),''))
    monkeypatch.setattr(QDialog,'exec',lambda self:QDialog.DialogCode.Accepted)
    monkeypatch.setattr(window,'load_digimon',lambda:None)
    window.update_actions();window.replace_digimon_button.click()
    assert not window.test_errors and len(target.edits)==2
    used=dt._texture_end(NativeModel(files['M']))
    assert target.current(entries[0])[:used]==files['M'][:used]
    assert NativeAnimation(target.current(entries[1]),2).clips
    saved,_=target.save(tmp_path/'replaced.iso')
    restored=EditSession(saved,2048)
    assert restored.current(entries[0])==target.current(entries[0])
    assert restored.current(entries[1])==target.current(entries[1])
    assert saved.stat().st_size==len(original) and target.source.read_bytes()==original
    assert image.read_bytes()==bytes(contents)


def test_real_tim_end_is_used_for_trimming_not_a_short_header_value(tmp_path):
    path,files,payload=donor(tmp_path)
    data=bytearray(files['M']);struct.pack_into('<I',data,4,1)
    # Keep a known nonzero color in the actual final palette entry. A short
    # mistaken trim boundary must never cut it or any of the TIM zero bytes.
    actual_end=dt._texture_end(NativeModel(files['M']));data[actual_end-2:actual_end]=b'\x31\x12'
    files['M']=bytes(data)
    transfer=dt.Transfer({'name':'Source'},files,{})
    session,entries,_=target_session(tmp_path)
    plan=dt.plan_transfer(transfer,entries,session);assert not plan.errors
    dt.apply_plan(plan,session)
    result=session.current(entries[0])
    assert result[:actual_end]==files['M'][:actual_end] and result[actual_end-2:actual_end]==b'\x31\x12'


@pytest.mark.parametrize('corruption',['truncated','length','shape'])
def test_bad_tim_is_still_rejected_without_altering_source(corruption,tmp_path):
    path,files,payload=donor(tmp_path);data=bytearray(files['M']);start=NativeModel(data).tim_start
    if corruption=='truncated':data=data[:-100]
    elif corruption=='length':struct.pack_into('<I',data,start+52,0xffffffff)
    else:struct.pack_into('<H',data,start+60,16)  # invalid native width
    files['M']=bytes(data);before=bytes(data)
    with pytest.raises((ValueError,struct.error)):
        dt.make_payload(type('Source',(),{'id':3,'code':'AGUM','name':'Agumon'})(),files)
    assert files['M']==before


def test_original_cpp_reader_accepts_same_nonmatching_header(tmp_path):
    import shutil,subprocess
    compiler=shutil.which('g++')
    if not compiler:pytest.skip('Optional original-reader comparison needs g++.')
    path,files,payload=donor(tmp_path);model=bytearray(files['M']);struct.pack_into('<I',model,4,64)
    m=tmp_path/'model.bin';a=tmp_path/'anim.bin';m.write_bytes(model);a.write_bytes(files['A'])
    tests=Path(__file__).parent;up=tests.parent/'third_party/dw2_model_converter/src';exe=tmp_path/'check'
    subprocess.run([compiler,'-std=c++17','-O2','-I',str(up),str(tests/'upstream_rig_check.cpp'),str(up/'dw2_model.cpp'),str(up/'dw2_anim.cpp'),'-o',str(exe)],check=True,capture_output=True)
    rows=subprocess.run([str(exe),str(m),str(a)],check=True,capture_output=True,text=True).stdout.splitlines()
    assert rows[:5]==['2 2','3 1 1','3 1 1','2 255 0','2 254 1']
