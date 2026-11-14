import json
import struct
from pathlib import Path
from PIL import Image
import pytest
from dw2studio.core import gltf_textures as gt
from dw2studio.core.model_export import export_model
from dw2studio.core.model_replacements import active_replacement,set_replacement,clear_replacement
from dw2studio.core.mini_assets import create_workcopy, replace_texture, export_texture, texture_slots


def make_gltf(folder):
    folder.mkdir(parents=True, exist_ok=True)
    data=b'ABCDEF'
    (folder/'mesh.bin').write_bytes(data)
    Image.new('RGBA',(4,4),(255,0,0,255)).save(folder/'base.png')
    doc={'asset':{'version':'2.0'},'buffers':[{'uri':'mesh.bin','byteLength':len(data)}],
         'bufferViews':[{'buffer':0,'byteOffset':1,'byteLength':3}],
         'images':[{'uri':'base.png'}],
         'textures':[{'source':0}],
         'animations':[{'name':'attack','samplers':[{'input':0,'output':0}], 'channels':[]}],
         'skins':[{'joints':[0]}], 'nodes':[{'name':'dummy'}]}
    model=folder/'test.gltf'
    model.write_text(json.dumps(doc),encoding='utf-8')
    return model


def test_animated_gltf_glb_gltf_roundtrip(tmp_path):
    model=make_gltf(tmp_path/'source')
    glb=tmp_path/'animated.glb'
    export_model(model,glb)
    doc,binary,_=gt.read_glb(glb)
    assert doc['animations'][0]['name']=='attack'
    assert doc['skins'][0]['joints']==[0]
    assert binary[:6]==b'ABCDEF'
    assert gt.image_bytes(glb,0)[:8]==b'\x89PNG\r\n\x1a\n'
    target=tmp_path/'out'/'animated.gltf'
    export_model(glb,target)
    text=json.loads(target.read_text())
    assert text['animations']==doc['animations']
    assert text['skins']==doc['skins']
    assert gt.image_bytes(target,0)==gt.image_bytes(glb,0)
    assert (target.parent/text['buffers'][0]['uri']).read_bytes()[:6]==b'ABCDEF'


def test_glb_texture_replace_keeps_binary_animation_and_source(tmp_path):
    src=make_gltf(tmp_path/'source')
    glb=tmp_path/'source.glb';export_model(src,glb)
    original=glb.read_bytes()
    active=create_workcopy(glb,tmp_path/'work')
    red_bytes=gt.image_bytes(active,0)
    with Image.open(tmp_path/'source'/'base.png') as im:
        old_size=im.size
    green=tmp_path/'green.png';Image.new('RGBA',old_size,(0,255,0,255)).save(green)
    replace_texture(active,0,green)
    doc,binary,_=gt.read_glb(active)
    assert doc['animations'][0]['name']=='attack'
    assert doc['skins'][0]['joints']==[0]
    assert binary[:6]==b'ABCDEF'
    exported=tmp_path/'texture.png';export_texture(active,0,exported)
    assert Image.open(exported).getpixel((0,0))==(0,255,0,255)
    assert glb.read_bytes()==original
    assert red_bytes!=gt.image_bytes(active,0)
    assert len(texture_slots(active))==1
    second=tmp_path/'blue.png';Image.new('RGBA',old_size,(0,0,255,255)).save(second)
    replace_texture(active,0,second)
    assert Image.open(tmp_path/'texture.png').getpixel((0,0))==(0,255,0,255)
    export_texture(active,0,exported)
    assert Image.open(exported).getpixel((0,0))==(0,0,255,255)


def test_gltf_replacement_keeps_animation_and_new_file(tmp_path):
    src=make_gltf(tmp_path/'source')
    original=src.read_bytes()
    model=create_workcopy(src,tmp_path/'work')
    blue=tmp_path/'blue.png';Image.new('RGBA',(4,4),(0,0,255,255)).save(blue)
    replace_texture(model,0,blue)
    doc=json.loads(model.read_text())
    assert doc['animations'][0]['name']=='attack'
    assert doc['images'][0]['uri']=='dw2_replacement_texture_1.png'
    assert (model.parent/doc['images'][0]['uri']).is_file()
    assert src.read_bytes()==original
    assert Image.open(tmp_path/'source'/'base.png').getpixel((0,0))==(255,0,0,255)
    new_glb=tmp_path/'edited.glb';export_model(model,new_glb)
    assert Image.open(__import__('io').BytesIO(gt.image_bytes(new_glb,0))).getpixel((0,0))==(0,0,255,255)
    assert gt.read_glb(new_glb)[0]['animations']==doc['animations']


def test_per_digimon_mapping_is_isolated_and_restorable(tmp_path):
    model=make_gltf(tmp_path/'source')
    agum=tmp_path/'replacements'/'003AGUM'
    meta=tmp_path/'replacements'/'029MGRE'
    active=set_replacement(model,agum)
    assert active_replacement(agum)==active
    assert active_replacement(meta) is None
    replaced=set_replacement(model,meta)
    assert active_replacement(meta)==replaced
    clear_replacement(meta)
    assert active_replacement(meta) is None
    assert active_replacement(agum)==active


def test_glb_corrupt_header_does_not_modify_file(tmp_path):
    model=tmp_path/'bad.glb';model.write_bytes(b'glTF'+b'corrupt')
    with pytest.raises(ValueError):gt.read_glb(model)
    assert model.read_bytes()==b'glTF'+b'corrupt'


def test_invalid_png_rejected_without_glb_corruption(tmp_path):
    model=make_gltf(tmp_path/'source')
    glb=tmp_path/'image.glb';export_model(model,glb)
    before=glb.read_bytes()
    png=tmp_path/'incorrect.png';Image.new('RGB',(8,4)).save(png,format='JPEG')
    with pytest.raises(ValueError,match='PNG'):
        replace_texture(glb,0,png)
    assert glb.read_bytes()==before


def test_static_obj_export_preserves_mtl_texture(tmp_path):
    source=tmp_path/'import';source.mkdir()
    (source/'model.obj').write_text('mtllib mesh.mtl\nv 0 0 0\nv 1 0 0\nv 0 1 0\nusemtl skin\nf 1 2 3\n')
    (source/'mesh.mtl').write_text('newmtl skin\nmap_Kd tex.png\n')
    Image.new('RGB',(4,4),(33,44,55)).save(source/'tex.png')
    target=tmp_path/'output'/'copy.obj'
    export_model(source/'model.obj',target)
    assert target.is_file()
    assert (target.parent/'mesh.mtl').is_file()
    assert Image.open(target.parent/'tex.png').getpixel((0,0))==(33,44,55)


def test_real_mesh_gltf_glb_roundtrip(tmp_path):
    import trimesh
    src=tmp_path/'model';src.mkdir()
    scene=trimesh.Scene()
    scene.add_geometry(trimesh.creation.box(extents=(1,2,3)))
    for name,data in scene.export(file_type='gltf').items():
        (src/name).write_bytes(data)
    glb=tmp_path/'output.glb'
    export_model(src/'model.gltf',glb)
    assert len(trimesh.load(str(glb),force='scene').geometry)>0
    gltf=tmp_path/'output.gltf'
    export_model(glb,gltf)
    assert len(trimesh.load(str(gltf),force='scene').geometry)>0


def test_glb_invalid_textures_and_animation_frames(tmp_path):
    model=make_gltf(tmp_path/'source')
    glb=tmp_path/'model.glb';export_model(model,glb)
    before=glb.read_bytes()
    with pytest.raises(IndexError):gt.image_bytes(glb,999)
    with pytest.raises(IndexError):gt.replace_png(glb,999,tmp_path/'source'/'base.png')
    assert glb.read_bytes()==before


def test_glb_animation_durations_preserved(tmp_path):
    from dw2studio.renderer.animation_data import read_gltf_animation_durations
    src=make_gltf(tmp_path/'source')
    doc=json.loads(src.read_text())
    doc['accessors']=[{'componentType':5126,'count':2,'type':'SCALAR','min':[0],'max':[2.5]}]
    src.write_text(json.dumps(doc))
    glb=tmp_path/'timed.glb';export_model(src,glb)
    assert read_gltf_animation_durations(src)==[2.5]
    assert read_gltf_animation_durations(glb)==[2.5]
