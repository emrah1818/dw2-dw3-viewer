import base64,json,struct
from pathlib import Path
import numpy as np
import pytest
from dw2studio.core.native_model import NativeModel
from dw2studio.core.rig_animation import NativeAnimation,BoneAdjustment,parents_from_depths,D,rotation_xyz
from dw2studio.core.rig_import import ObjMesh,RigProject
from dw2studio.core.gltf_document import read_document,pack_glb
from dw2studio.renderer.animation_data import read_gltf_animation_durations
from dw2studio.core.auto_models import model_animation_names


def native_model(bones=2,tim=512):
    begin=(12+16*bones+24+3)//4*4;data=bytearray(tim+0x4040+4);struct.pack_into('<III',data,0,tim,tim+0x4040,bones);cursor=begin;pointers=[[],[],[]]
    for bone in range(bones):
        pointers[0].append(cursor);struct.pack_into('<IH',data,cursor,4,0)
        for j,coords in enumerate(((0,0,0),(20,0,0),(0,-20,0),(20,-20,0))):struct.pack_into('<hhh',data,cursor+6+j*6,*coords)
        cursor=(cursor+30+3)//4*4;pointers[1].append(cursor);struct.pack_into('<IHhhh',data,cursor,1,0,0,0,4096);cursor+=12
        pointers[2].append(cursor);struct.pack_into('<II',data,cursor,0,1);p=cursor+8;data[p:p+8]=bytes([0,1,2,3,0,0,0,0]);data[p+8:p+16]=bytes([0,0,7,0,0,3,7,3]);struct.pack_into('<HHII',data,p+16,224*64,0,0,0);cursor+=36
    for i,table in enumerate(pointers):struct.pack_into(f'<{bones}I',data,12+i*bones*4,*table)
    struct.pack_into(f'<{bones}I',data,12+12*bones,*range(bones))
    pos=12+16*bones;data[pos:pos+20]=bytes([255,0,0,0,0,0,0,0,0,0])*2
    struct.pack_into('<III4H',data,tim,16,8,44,0,0,256,1);struct.pack_into('<I4H',data,tim+52,16396,0,0,32,256);data[tim+64:tim+0x3840]=b'\x11'*(0x3840-64);struct.pack_into('<1024H',data,tim+0x3840,*([0,31]+[0]*1022))
    return bytes(data)


def animation_bytes():
    out=bytearray(116);struct.pack_into('<7I',out,0,0,44,68,0,28,35,0);out[28:35]=bytes([0,0,0,1,255,0,0]);out[35:42]=bytes([0,1,0,0,254,1,0])
    def matrix(offset,rotation,translation):
        r=D@rotation@D;values=np.rint(np.r_[r.T.flatten()*4096,D@translation]).astype(int);struct.pack_into('<12h',out,offset,*values)
    matrix(44,np.eye(3),np.array([0,0,0]));matrix(68,np.eye(3),np.array([0,20,0]));matrix(92,rotation_xyz([0,0,90]),np.array([0,20,0]))
    return bytes(out)


def obj_file(tmp_path):
    path=tmp_path/'new.obj';path.write_text('''o body
v 0 0 0
v 10 0 0
v 0 10 0
v 0 20 0
v 10 20 0
v 0 30 0
vt 0 1
vt .05 1
vt 0 .98
f 1/1 2/2 3/3
g head
f 4/1 5/2 6/3
''');return path


def project(tmp_path):return RigProject(ObjMesh(obj_file(tmp_path)),native_model(),{'A003TEST.BIN':animation_bytes()})


def test_animation_layout_identity_roundtrip_and_pose():
    raw=animation_bytes();animation=NativeAnimation(raw,2)
    assert len(animation.clips)==2 and animation.clips[1].termination==254
    assert animation.adjusted([BoneAdjustment(),BoneAdjustment()])==raw
    world=animation.world_pose([0,1],0,1)
    assert np.allclose(world[1,:3,3],[0,20,0])
    assert np.allclose(world[1,:3,:3],rotation_xyz([0,0,90]),atol=1/4096)


def test_animation_correction_only_matrices_and_shared_timings():
    raw=animation_bytes();settings=[BoneAdjustment(),BoneAdjustment(label='Kopf',motion_scale=0,offset=[2,0,0])]
    changed=NativeAnimation(raw,2).adjusted(settings);after=NativeAnimation(changed,2)
    assert len(changed)==len(raw) and changed[:44]==raw[:44]
    assert np.allclose(after.local_pose(0,1)[1,:3,:3],np.eye(3))
    assert np.allclose(after.local_pose(0,1)[1,:3,3],[2,20,0])
    bad=bytearray(raw);struct.pack_into('<I',bad,4,10000)
    with pytest.raises(ValueError):NativeAnimation(bad,2)
    with pytest.raises(ValueError):parents_from_depths([0,2])


def test_new_geometry_roundtrip_fits_and_animates(tmp_path):
    p=project(tmp_path);p.assignment[:]=[0,1];native,report=p.build_native();m=NativeModel(native)
    assert len(native)==len(p.original) and report['geometry_used']<=report['geometry_budget']
    assert native[m.tim_start:]==p.original[m.tim_start:]
    triangles,world=p.preview('A003TEST.BIN',0,0)
    assert np.allclose(triangles,p.source_vertices()[p.mesh.face_indices])
    moved,world=p.preview('A003TEST.BIN',0,1)
    assert np.allclose(moved[0],triangles[0]) and not np.allclose(moved[1],triangles[1])
    # Decode actual new local bytes and animate those; source preview must agree.
    part=m.parts[1];vertices=np.array([struct.unpack_from('<hhh',native,part.vertices+6+i*6) for i in range(part.vertex_count)])@D
    decoded=(np.c_[vertices,np.ones(len(vertices))]@world[1].T)[:,:3]
    assert np.allclose(decoded,moved[1])


def test_missing_assignments_budget_and_missing_uv_rejected(tmp_path):
    p=project(tmp_path)
    with pytest.raises(ValueError,match='zugeordnet'):p.build_native()
    p.assignment[:]=[0,1];p.model.tim_start=90
    with pytest.raises((ValueError,struct.error)):p.build_native()
    path=tmp_path/'no_uv.obj';path.write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n')
    p=RigProject(ObjMesh(path),native_model(),{'A.BIN':animation_bytes()});p.assignment[:]=0
    with pytest.raises(ValueError,match='ohne UV'):p.build_native()


def test_blink_records_native_units_and_preserved_terminator(tmp_path):
    p=project(tmp_path);p.assignment[:]=[0,1]
    record={'enabled':True,'x':0,'y':0,'w':8,'h':4,'open_x':8,'open_y':0,'half_x':16,'half_y':0,'closed_x':24,'closed_y':0}
    p.blink_records=[record,dict(record,enabled=False)];new,_=p.build_native();eyes=NativeModel(new).eyes()
    assert eyes[0].width==8 and eyes[0].frames==((8,0),(16,0),(24,0))
    pos=p.model.blink_offset;assert new[pos+20:pos+24]==p.original[pos+20:pos+24]
    p.blink_records[0]['w']=7
    with pytest.raises(ValueError,match='4 teilbar'):p.build_native()


def test_rig_mapping_strict_identity_and_export_animations(tmp_path):
    p=project(tmp_path);p.assignment[:]=[0,1];p.settings[1].label='Kopf';p.settings[1].motion_scale=.5
    mapping=tmp_path/'rig.dw2rig';p.save(mapping);loaded=project(tmp_path);loaded.load(mapping)
    assert loaded.assignment.tolist()==[0,1] and loaded.settings[1].label=='Kopf'
    gltf=tmp_path/'rig.gltf';p.export_gltf(gltf);doc=read_document(gltf)
    assert len(doc['animations'])==2 and doc['nodes'][1]['name']=='Kopf'
    assert doc['nodes'][0]['children'][0]==1
    glb=tmp_path/'rig.glb';pack_glb(gltf,glb);packed=read_document(glb)
    assert len(packed['animations'])==2 and 'uri' not in packed['buffers'][0]
    assert len(model_animation_names(glb))==2 and read_gltf_animation_durations(glb)==pytest.approx([1/30,1/30])
    changed=json.loads(mapping.read_text());changed['obj_sha256']='bad';mapping.write_text(json.dumps(changed))
    with pytest.raises(ValueError,match='passt nicht'):p.load(mapping)


def test_obj_negative_indices_groups_and_bad_topology(tmp_path):
    path=tmp_path/'mesh.obj';path.write_text('v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\ng left arm\nf -4 -3 -2 -1\n')
    mesh=ObjMesh(path);assert len(mesh.faces)==2 and mesh.groups==['left arm']
    path.write_text('v nan 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n')
    with pytest.raises(ValueError,match='endliche'):ObjMesh(path)


def test_actual_target_budget_and_vertex_limit(tmp_path):
    path=obj_file(tmp_path);text=path.read_text();text+='\ng too_many\n'+'f 1/1 2/2 3/3\n'*20;path.write_text(text)
    with pytest.raises(ValueError,match='Zielplatz zu groß'):RigProject(ObjMesh(path),native_model(tim=240),{'A.BIN':animation_bytes()})
    obj=tmp_path/'vertices.obj';lines=['vt 0 1','vt .1 1','vt 0 .9']
    for i in range(86):
        lines += [f'v {i*3} 0 0',f'v {i*3+1} 0 0',f'v {i*3} 1 0']
        k=i*3+1;lines.append(f'f {k}/1 {k+1}/2 {k+2}/3')
    obj.write_text('\n'.join(lines));p=RigProject(ObjMesh(obj),native_model(tim=8192),{'A.BIN':animation_bytes()});p.assignment[:]=0
    with pytest.raises(ValueError,match='256 Vertices'):p.build_native()


def test_invalid_mapping_load_is_atomic(tmp_path):
    p=project(tmp_path);p.assignment[:]=[0,1];file=tmp_path/'p.dw2rig';p.save(file);doc=json.loads(file.read_text());doc['assignment']=[1,0];doc['blink_records']=[{'enabled':True}];file.write_text(json.dumps(doc))
    with pytest.raises((ValueError,KeyError)):p.load(file)
    assert p.assignment.tolist()==[0,1]


def test_glb_export_api_preserves_clips(tmp_path):
    from dw2studio.core.model_export import export_model
    p=project(tmp_path);p.assignment[:]=[0,1];gltf=tmp_path/'source.gltf';p.export_gltf(gltf)
    target=tmp_path/'export.glb';export_model(gltf,target)
    assert len(read_document(target)['animations'])==2


def test_subpixel_geometry_is_rejected_before_becoming_invisible(tmp_path):
    p=project(tmp_path);p.assignment[:]=[0,1];p.scale=.001
    with pytest.raises(ValueError,match='Koordinatenraster'):p.build_native()
