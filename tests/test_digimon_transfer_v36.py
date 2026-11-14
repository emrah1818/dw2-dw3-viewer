"""Complete native family transfer, corruption checks and real UI export/import."""
import copy,json,struct
from pathlib import Path
from types import SimpleNamespace
import pytest
import numpy as np
from dw2studio.core import digimon_transfer as dt
from dw2studio.core import gltf_textures as gt
from dw2studio.core.model_export import export_model
from dw2studio.core.native_model import NativeModel
from dw2studio.core.rig_animation import NativeAnimation
from dw2studio.core.edit_session import EditSession
from dw2studio.core.disc import Entry
from dw2studio.core.catalog import DigimonCandidate
from test_rig_import_v8 import project,native_model,animation_bytes


def animation(bones,clips=2):
    # Independent valid target skeleton/clip layout, with room for donor data.
    table=4+bones*4;begin=table+(clips+1)*4
    streams=[bytes([0]*bones+[255,0,0]) for _ in range(clips)]
    matrix_start=(begin+sum(map(len,streams))+3)//4*4
    out=bytearray(matrix_start+bones*24);struct.pack_into('<I',out,0,0)
    for bone in range(bones):
        at=matrix_start+bone*24;struct.pack_into('<I',out,4+bone*4,at)
        struct.pack_into('<12h',out,at,4096,0,0,0,4096,0,0,0,4096,0,bone*20,0)
    pos=begin
    for i,data in enumerate(streams):struct.pack_into('<I',out,table+i*4,pos);out[pos:pos+len(data)]=data;pos+=len(data)
    return bytes(out)


def donor(tmp_path,suffix='.gltf'):
    folder=tmp_path/'donor';folder.mkdir();p=project(folder);p.assignment[:]=[0,1]
    scene=folder/'rig.gltf';p.export_gltf(scene)
    native,_=p.build_native();files={'M':native,'A':p.adjusted_animation_bytes()['A003TEST.BIN']}
    source=SimpleNamespace(id=3,code='AGUM',name='Agumon')
    payload=dt.make_payload(source,files)
    path=export_model(scene,tmp_path/('export'+suffix));dt.attach_payload(path,payload)
    return path,files,payload


def target_session(tmp_path,*,roles=('A',),model_size=None,animation_size=512,clips=2):
    data=native_model(bones=3,tim=1024)
    if model_size is not None:data=data[:model_size] if model_size<len(data) else data.ljust(model_size,b'\0')
    files={'M':data}|{r:animation(3,clips).ljust(animation_size,b'\0') for r in roles}
    contents=bytearray();entries=[]
    for r,data in files.items():
        entries.append(Entry(f'{r}012MTGR.BIN',len(contents)//2048,len(data),False))
        contents.extend(data.ljust(((len(data)+2047)//2048)*2048,b'\0'))
    contents.extend(b'unchanged sector'.ljust(2048,b'!'))
    path=tmp_path/'game.iso';path.write_bytes(contents)
    return EditSession(path,2048),entries,bytes(contents)


@pytest.mark.parametrize('suffix',['.gltf','.glb'])
def test_export_reimports_model_texture_skeleton_and_all_native_animations(tmp_path,suffix):
    path,files,payload=donor(tmp_path,suffix);transfer=dt.read_transfer(path)
    assert transfer.files==files and transfer.source['name']=='Agumon'
    assert len(gt.document(path)['animations'])==2
    session,entries,original=target_session(tmp_path)
    plan=dt.plan_transfer(transfer,entries,session)
    assert not plan.errors and plan.source_bones==2 and plan.target_bones==3
    assert dt.apply_plan(plan,session)==2
    m,a=(session.current(e) for e in entries)
    assert NativeModel(m).bone_count==2
    assert m[:len(files['M'])]==files['M'] or m[:NativeModel(files['M']).tim_end]==files['M'][:NativeModel(files['M']).tim_end]
    assert a[:len(files['A'])]==files['A']
    assert len(NativeAnimation(a,2).clips)==2
    out,_=session.save(tmp_path/'modified.iso');saved=EditSession(out,2048)
    assert [saved.current(e) for e in entries]==[m,a]
    assert out.stat().st_size==len(original) and session.source.read_bytes()==original
    assert out.read_bytes()[-2048:]==original[-2048:]


@pytest.mark.parametrize('change',['node','animation','image','buffer','native_blob'])
def test_edited_or_corrupt_files_do_not_silently_reimport_embedded_original(tmp_path,change):
    path,files,payload=donor(tmp_path);doc=gt.document(path)
    if change=='node':doc['nodes'][0]['translation']=[123,0,0]
    elif change=='animation':doc['animations'][0]['channels'][0]['target']['node']=1
    elif change=='image':doc['images'][0]['uri']=doc['images'][0]['uri'][:-8]+'AAAAAAAA'
    elif change=='buffer':
        uri=doc['buffers'][0]['uri'];doc['buffers'][0]['uri']=uri[:-8]+'AAAAAAAA'
    else:doc['extras'][dt.KEY]['files']['A']['sha256']='0'*64
    path.write_text(json.dumps(doc))
    with pytest.raises((ValueError,IndexError)):dt.read_transfer(path)


@pytest.mark.parametrize('problem',['model_too_big','animation_too_big','missing_role','extra_role','missing_clip'])
def test_incompatible_slots_leave_all_existing_edits_untouched(tmp_path,problem):
    path,files,payload=donor(tmp_path);transfer=dt.read_transfer(path)
    options={}
    if problem=='model_too_big':
        # Valid smaller native target; donor TIM offset makes the donor bigger.
        session,entries,original=target_session(tmp_path)
        small=native_model(bones=2,tim=256)
        original=small.ljust(18432,b'\0')+animation(2).ljust(2048,b'\0')
        session.source.write_bytes(original);session=EditSession(session.source,2048)
        entries=[Entry('M012MTGR.BIN',0,len(small),False),Entry('A012MTGR.BIN',9,512,False)]
    else:
        if problem=='animation_too_big':options['animation_size']=len(animation(3))
        if problem=='missing_role':options['roles']=('A','B')
        if problem=='extra_role':
            transfer=dt.Transfer(transfer.source,files|{'B':files['A']},payload)
        if problem=='missing_clip':options['clips']=3
        session,entries,original=target_session(tmp_path,**options)
    plan=dt.plan_transfer(transfer,entries,session)
    assert plan.errors
    before=session.edits.copy()
    with pytest.raises(ValueError):dt.apply_plan(plan,session)
    assert session.edits==before and session.source.read_bytes()==original


def test_failure_during_staging_rolls_back_whole_family(tmp_path,monkeypatch):
    path,files,payload=donor(tmp_path);session,entries,_=target_session(tmp_path)
    plan=dt.plan_transfer(dt.read_transfer(path),entries,session)
    before=session.edits.copy();stage=session.stage;count=0
    def fail(*a,**kw):
        nonlocal count
        count+=1
        if count==2:raise OSError('test disk error')
        return stage(*a,**kw)
    monkeypatch.setattr(session,'stage',fail)
    with pytest.raises(OSError):dt.apply_plan(plan,session)
    assert session.edits==before


def test_ordinary_old_export_explains_need_for_native_exchange_data(tmp_path):
    path,files,payload=donor(tmp_path);doc=gt.document(path);doc['extras'].pop(dt.KEY);path.write_text(json.dumps(doc))
    with pytest.raises(ValueError,match='erneut als GLTF/GLB exportieren'):dt.read_transfer(path)


def test_full_color_only_edit_removes_outdated_native_metadata(tmp_path):
    from PIL import Image
    from dw2studio.core.mini_assets import replace_texture
    path,files,payload=donor(tmp_path);png=tmp_path/'new.png';Image.new('RGBA',(128,256),'blue').save(png)
    replace_texture(path,0,png)
    assert dt.KEY not in gt.document(path)['extras']
    with pytest.raises(ValueError,match='keine nativen'):dt.read_transfer(path)


def test_real_gui_export_then_replace_and_discard_whole_family(window,tmp_path,monkeypatch):
    from PyQt6.QtWidgets import QFileDialog,QDialog
    from PyQt6.QtCore import Qt
    source,files,payload=donor(tmp_path)
    # Use an actual VTK scene with animated bones for the normal export path.
    window.load_model(source);window.active_native=True
    source_entries=[];contents=bytearray()
    for r,data in files.items():
        source_entries.append(Entry(f'{r}003AGUM.BIN',len(contents)//2048,len(data),False));contents.extend(data.ljust(((len(data)+2047)//2048)*2048,b'\0'))
    source_image=tmp_path/'source.iso';source_image.write_bytes(contents)
    digi=DigimonCandidate(3,'AGUM','Agumon',source_entries)
    window.image_path=source_image;window.session=EditSession(source_image,2048);window.entries=source_entries
    window.catalog=[digi];window.current=window.loaded_digimon=digi;window.active_digimon_key=window.key_for(digi)
    exported=tmp_path/'normal_export.glb'
    monkeypatch.setattr(QFileDialog,'getSaveFileName',lambda *a,**kw:(str(exported),'GLB (*.glb)'))
    window.export_model();assert not window.test_errors
    assert dt.read_transfer(exported).files==files
    assert len(gt.document(exported)['animations'])==2
    window.viewer.load(exported);window.viewer.timer.stop()
    window.viewer.importer.EnableAnimation(1);window.viewer.importer.UpdateAtTimeValue(0)
    before=[a.GetBounds() for a in window.viewer._model_actors]
    window.viewer.importer.UpdateAtTimeValue(1/30)
    assert [a.GetBounds() for a in window.viewer._model_actors]!=before
    session,entries,original=target_session(tmp_path)
    target=DigimonCandidate(12,'MTGR','MetalGreymon',entries)
    window.session=session;window.image_path=session.source;window.entries=entries;window.catalog=[target];window.current=target
    monkeypatch.setattr(window,'load_digimon',lambda:None)
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,**kw:(str(exported),''))
    monkeypatch.setattr(QDialog,'exec',lambda dialog:QDialog.DialogCode.Accepted)
    window.update_actions();window.replace_digimon_button.click()
    assert not window.test_errors and len(session.edits)==2
    assert NativeModel(session.current(entries[0])).bone_count==2
    assert NativeAnimation(session.current(entries[1]),2).clips
    assert session.source.read_bytes()==original
    window.pending.setCurrentRow(1);window.discard_selected()
    assert not session.edits and session.source.read_bytes()==original


@pytest.mark.parametrize('suffix',['.gltf','.glb'])
def test_exchange_is_one_portable_file_with_external_source_assets(tmp_path,suffix):
    import base64,shutil
    path,files,payload=donor(tmp_path)
    folder=tmp_path/'external';folder.mkdir();doc=gt.document(path);doc.pop('extras',None)
    for i,item in enumerate(doc['buffers']):
        data=base64.b64decode(item['uri'].split(',',1)[1]);name=f'buffer{i}.bin';(folder/name).write_bytes(data);item['uri']=name
    for i,item in enumerate(doc['images']):
        data=base64.b64decode(item['uri'].split(',',1)[1]);name=f'skin{i}.png';(folder/name).write_bytes(data);item['uri']=name
    external=folder/'model.gltf';external.write_text(json.dumps(doc))
    out=tmp_path/'single'/('transfer'+suffix);dt.export_exchange(external,out,payload)
    assert list(out.parent.iterdir())==[out]
    shutil.rmtree(folder);other=tmp_path/'moved';other.mkdir();moved=other/out.name;shutil.copy2(out,moved)
    assert dt.read_transfer(moved).files==files
    assert gt.image_bytes(moved,0)==gt.image_bytes(path,0)


def test_reexport_to_another_format_keeps_native_transfer(window,tmp_path,monkeypatch):
    from PyQt6.QtWidgets import QFileDialog
    path,files,payload=donor(tmp_path,'.glb')
    window.project_model=path;window.active_native=False;out=tmp_path/'reexport.gltf'
    monkeypatch.setattr(QFileDialog,'getSaveFileName',lambda *a,**kw:(str(out),'glTF (*.gltf)'))
    window.export_model()
    assert not window.test_errors and dt.read_transfer(out).files==files


def test_raw_image_and_portable_mod_project_keep_complete_native_family(tmp_path):
    from test_native_rom_bridge import sector
    path,files,payload=donor(tmp_path);iso,entries,original=target_session(tmp_path)
    raw=b''.join(sector(i,original[i*2048:(i+1)*2048]) for i in range(len(original)//2048))
    image=tmp_path/'game.bin';image.write_bytes(raw);session=EditSession(image,2352)
    dt.apply_plan(dt.plan_transfer(dt.read_transfer(path),entries,session),session)
    project=tmp_path/'transfer.dw2mod';session.export_project(project)
    restored=EditSession(image,2352);restored.import_project(project,entries)
    assert restored.edits==session.edits
    out,_=restored.save(tmp_path/'new.bin');saved=EditSession(out,2352)
    assert [saved.current(e) for e in entries]==[session.current(e) for e in entries]
    assert out.stat().st_size==len(raw) and image.read_bytes()==raw


@pytest.mark.parametrize('accepted',[False,True])
def test_gui_cancel_or_incompatible_plan_cannot_partially_replace(window,tmp_path,monkeypatch,accepted):
    from PyQt6.QtWidgets import QFileDialog,QDialog
    path,files,payload=donor(tmp_path)
    session,entries,original=target_session(tmp_path,roles=('A','B') if accepted else ('A',))
    target=DigimonCandidate(12,'MTGR','Target',entries)
    window.session=session;window.entries=entries;window.current=target;window.catalog=[target]
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,**k:(str(path),''))
    monkeypatch.setattr(QDialog,'exec',lambda dialog:QDialog.DialogCode.Accepted if accepted else QDialog.DialogCode.Rejected)
    window.replace_digimon()
    assert not session.edits and session.source.read_bytes()==original
    assert window.transfer_dialog.confirm.isEnabled()!=accepted


def test_transferred_files_are_readable_by_original_cpp_converter(tmp_path):
    import shutil,subprocess
    compiler=shutil.which('g++')
    if not compiler:pytest.skip('Optional upstream C++ verification requires g++.')
    path,files,payload=donor(tmp_path);session,entries,original=target_session(tmp_path)
    dt.apply_plan(dt.plan_transfer(dt.read_transfer(path),entries,session),session)
    m=tmp_path/'model.bin';a=tmp_path/'anim.bin';m.write_bytes(session.current(entries[0]));a.write_bytes(session.current(entries[1]))
    tests=Path(__file__).parent;upstream=tests.parent/'third_party/dw2_model_converter/src';exe=tmp_path/'check'
    subprocess.run([compiler,'-std=c++17','-O2','-I',str(upstream),str(tests/'upstream_rig_check.cpp'),str(upstream/'dw2_model.cpp'),str(upstream/'dw2_anim.cpp'),'-o',str(exe)],check=True,capture_output=True)
    result=subprocess.run([str(exe),str(m),str(a)],check=True,capture_output=True,text=True)
    assert result.stdout.splitlines()[:5]==['2 2','3 1 1','3 1 1','2 255 0','2 254 1']
