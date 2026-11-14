import json
from pathlib import Path
from PIL import Image
from dw2studio.core.mini_assets import create_workcopy,texture_slots,replace_texture,export_texture

def test_animated_gltf_texture_workcopy(tmp_path):
    src=tmp_path/'source';src.mkdir()
    (src/'model.gltf').write_text(json.dumps({'asset':{'version':'2.0'},'images':[{'uri':'skin.png'}], 'animations':[{'name':'attack'}]}))
    Image.new('RGBA',(16,16),(255,0,0,255)).save(src/'skin.png')
    (tmp_path/'replacement.png').write_bytes(b'')
    Image.new('RGB',(16,16),(0,255,0)).save(tmp_path/'replacement.png')
    model=create_workcopy(src/'model.gltf',tmp_path/'projects')
    assert texture_slots(model)[0][1].exists()
    replace_texture(model,0,tmp_path/'replacement.png')
    assert Image.open(texture_slots(model)[0][1]).getpixel((0,0))==(0,255,0)
    assert Image.open(src/'skin.png').getpixel((0,0))==(255,0,0,255)
    assert json.loads(model.read_text())['animations'][0]['name']=='attack'
    export_texture(model,0,tmp_path/'result.png')
    assert Image.open(tmp_path/'result.png').size==(16,16)

def test_full_color_accepts_other_aspect_ratio_without_resizing(tmp_path):
    src=tmp_path/'model.gltf';src.write_text(json.dumps({'images':[{'uri':'skin.png'}]}))
    Image.new('RGBA',(16,16)).save(tmp_path/'skin.png')
    source=tmp_path/'small.png';Image.new('RGB',(8,4)).save(source)
    replace_texture(src,0,source)
    result=tmp_path/'out.png';export_texture(src,0,result)
    assert result.read_bytes()==source.read_bytes()
    assert Image.open(tmp_path/'skin.png').size==(16,16)


def test_obj_dependencies(tmp_path):
    src=tmp_path/'a.obj';src.write_text('mtllib a.mtl\nv 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n')
    (tmp_path/'a.mtl').write_text('newmtl m\nmap_Kd a.png\n')
    Image.new('RGBA',(4,4)).save(tmp_path/'a.png')
    model=create_workcopy(src,tmp_path/'work')
    assert texture_slots(model)[0][1].name=='a.png'
