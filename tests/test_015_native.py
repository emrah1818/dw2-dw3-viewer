import hashlib
import json
import os
from pathlib import Path
import struct
from types import SimpleNamespace
import numpy as np
import pytest
from PIL import Image
from dw2studio.core.disc import Entry
from dw2studio.core.evolution import EvolutionRepository, target_for
from dw2studio.core.dw3_native import encode_model, encode_animation, hd_name
from dw2studio.core.native_anim import parse_anim_file, pose_matrix
from dw2studio.core.native_model import NativeModel


def source(tmp_path):
    Image.new('RGBA',(256,256),(255,0,128,255)).save(tmp_path/'tex0.png')
    def frame(x):
        m=np.eye(4);m[0,3]=x
        return [np.eye(4).T.ravel().tolist(),m.T.ravel().tolist()]
    return {'format':1,'fps':30,'bones':[{'parent':-1,'vertices':[],'faces':[]},
        {'parent':0,'vertices':[[0,0,0],[100,0,0],[0,100,0]],'faces':[{'indices':[0,1,2],'uv':[[0,0],[255,0],[0,255]],'image':0,'abr':0}]}],
        'images':['tex0.png'],'motions':[{'id':1,'frames':[frame(0),frame(20),frame(0)]}]}


def test_native_geometry_animation_coordinates_and_hd_id(tmp_path):
    s=source(tmp_path)
    native,hd,report=encode_model(s,tmp_path,scale=2)
    model=NativeModel(native)
    assert report['bones']==1 and report['triangles']==1 and hd.size==(512,1024)
    assert struct.unpack_from('<hhh',native,model.parts[0].vertices+12)==(200,0,0)
    anim=encode_animation(s,{0:0},scale=2,loops=[0])
    parsed=parse_anim_file(anim,1)
    assert parsed.clips[0].loop_row==0 and len(parsed.clips[0].rows)==3
    matrix,t=pose_matrix(anim,parsed.pose_offsets[0],parsed.clips[0].rows[1][0])
    assert matrix==[[4096,0,0],[0,4096,0],[0,0,4096]] and t==[40,0,0]
    # Independent FNV-1a reference for backend/texrep.c's upload identifier.
    data=struct.pack('<2i',32,256)+native[model.tim_start+20:model.tim_start+20+16384]
    h=14695981039346656037
    for b in data:h=((h^b)*1099511628211)%(1<<64)
    assert hd_name(native)==f'{h:016x}_32x256_m0.png'


def test_native_rejects_unrepresentable_coordinates_and_keys(tmp_path):
    s=source(tmp_path)
    with pytest.raises(ValueError,match='16-Bit'):encode_model(s,tmp_path,scale=1000)
    rows=[]
    for x in range(255):
        m=np.eye(4);m[0,3]=x
        rows.append([np.eye(4).T.ravel().tolist(),m.T.ravel().tolist()])
    s['motions'][0]['frames']=rows
    with pytest.raises(ValueError,match='254'):encode_animation(s,{0:0})


def test_evolution_boundaries_preserve_other_fields():
    data=bytearray(18*4)
    for i,identifier in enumerate([3,5,6]):
        o=18*i;struct.pack_into('<h',data,o,identifier);data[o+2]=7;data[o+4]=1;data[o+17]=0xA5
    entry=Entry('PAK/DIGIMNDT.BIN',123,len(data),False)
    class Session:
        def current(self,e):return bytes(data)
        def original(self,e):return bytes(data)
        def stage(self,e,replacement,label):data[:]=replacement
    repo=EvolutionRepository(Session(),[entry]);before=bytes(data)
    assert repo.change(3,[{'min_dp':0,'target':5},{'min_dp':7,'target':6}],rank=1)
    info=repo.info(3)
    assert [target_for(info['bounds'],info['targets'],dp) for dp in [0,6,7,255]]==[5,5,6,6]
    assert data[4]&15==1 and data[2]==7 and data[17]==0xA5 and data[18:]==before[18:]
    assert repo.change(3,[])
    assert target_for(repo.info(3)['bounds'],repo.info(3)['targets'],255)==0
    unchanged=bytes(data)
    with pytest.raises(ValueError):repo.change(3,[{'min_dp':1,'target':5}])
    with pytest.raises(ValueError):repo.change(3,[{'min_dp':0,'target':3}])
    assert bytes(data)==unchanged


@pytest.mark.skipif(not(os.environ.get('DW2_TEST_PAK') and os.environ.get('DW3_TEST_DISC')),reason='Private game data not provided')
def test_real_native_import_history_project_and_export(tmp_path,monkeypatch):
    import android_api as api
    monkeypatch.setattr(api,'S',api.State())
    monkeypatch.setattr(api,'UNDO',[]);monkeypatch.setattr(api,'REDO',[])
    api.configure(tmp_path,'')
    api.open_image(os.environ['DW2_TEST_PAK']);api.open_dw3(os.environ['DW3_TEST_DISC'])
    sha=hashlib.sha256(api.S.image_path.read_bytes()).hexdigest()
    plan=api.dw3_native_plan(0,3)
    # Select actual source motions; no semantic attack names are inferred.
    for i,row in enumerate(plan['assignments']):row['motion']=plan['motions'][i%5]['id']
    reply=json.loads(api.call('dw3_native_apply',json.dumps([0,3,plan['assignments'],1.,4])))
    assert reply['ok'],reply
    assert reply['data']['bones']==18
    assert len(api.S.session.edits)==11 and api.S.session.active_hd_files()
    model_entry=next(e for e in api.S.entries if Path(e.path).name=='M003AGUM.BIN')
    assert NativeModel(api.S.session.current(model_entry)).bone_count==18
    api.undo();assert not api.S.session.edits and not api.S.session.active_hd_files()
    api.redo();assert len(api.S.session.edits)==11 and api.S.session.active_hd_files()
    project=api.save_project('015.dw2mod')
    expected={k:hashlib.sha256(v.replacement).hexdigest() for k,v in api.S.session.edits.items()}
    api.open_image(os.environ['DW2_TEST_PAK']);api.load_project(project['path'])
    assert {k:hashlib.sha256(v.replacement).hexdigest() for k,v in api.S.session.edits.items()}==expected
    assert api.S.session.active_hd_files()
    port=tmp_path/'port';port.mkdir()
    with pytest.raises(ValueError,match='Overlay-API 2'):api.export_port_mod(port)
    (port/'dw2_mod_api.json').write_text('{"mod_api":2}')
    result=api.export_port_mod(port)
    assert result['count']==11 and len(list((port/'Mods/Textures').rglob('*.png')))==1
    assert hashlib.sha256(api.S.image_path.read_bytes()).hexdigest()==sha


def test_split_rigid_mesh_keeps_parent_and_motion(tmp_path):
    from copy import deepcopy
    from dw2studio.core.rig_animation import parents_from_depths
    s=source(tmp_path)
    s['bones'][1]['faces']*=257
    child=deepcopy(s['bones'][1]);child['parent']=1;child['faces']=child['faces'][:1]
    s['bones'].append(child)
    for frame in s['motions'][0]['frames']:frame.append(frame[1][:])
    native,_,report=encode_model(s,tmp_path)
    model=NativeModel(native)
    assert report['bones']==3 and report['triangles']==258
    assert [len(p.primitives) for p in model.parts]==[256,1,1]
    depths=struct.unpack_from('<3I',native,12+12*3)
    assert depths==(0,0,1) and parents_from_depths(list(depths))==[-1,-1,1]
    anim=encode_animation(s,{0:0})
    parsed=parse_anim_file(anim,3)
    for row in parsed.clips[0].rows:
        assert pose_matrix(anim,parsed.pose_offsets[0],row[0])==pose_matrix(anim,parsed.pose_offsets[1],row[1])
