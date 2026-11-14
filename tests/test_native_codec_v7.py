import struct
from pathlib import Path
import pytest
from PIL import Image
from dw2studio.core.native_model import NativeModel
from dw2studio.core.native_texture import NativeTexture


def native_fixture():
    # Layout-matching synthetic one-bone model. No original game assets.
    v,n,p,t=64,96,112,160
    data=bytearray(t+0x4040+4)
    struct.pack_into('<III',data,0,t,t+0x4040,1)
    struct.pack_into('<4I',data,12,v,n,p,0)
    data[28:38]=bytes([0,0,2,4,2,0,4,0,6,0])
    data[38:48]=bytes([255,0,0,0,0,0,0,0,0,0])
    struct.pack_into('<IH',data,v,4,0)
    for i,coords in enumerate(((0,0,0),(7,0,0),(0,3,0),(7,3,0))):struct.pack_into('<hhh',data,v+6+i*6,*coords)
    struct.pack_into('<IHhhh',data,n,1,0,0,0,4096)
    struct.pack_into('<II',data,p,0,1)
    q=p+8;data[q:q+8]=bytes([0,1,2,3,0,0,0,0]);data[q+8:q+16]=bytes([0,0,7,0,0,3,7,3]);struct.pack_into('<HH',data,q+16,224*64,0)
    struct.pack_into('<II',data,q+20,0,0)
    struct.pack_into('<III4H',data,t,16,8,44,0,0,256,1)
    struct.pack_into('<I4H',data,t+52,16396,0,0,32,256)
    data[t+64:t+0x3840]=b'\x11'*(0x3840-64)
    struct.pack_into('<1024H',data,t+0x3840,*([0,31]+[0]*1022))
    return bytes(data)


def test_native_obj_roundtrip_and_shape_only_changes(tmp_path):
    data=native_fixture();m=NativeModel(data);obj=tmp_path/'form.obj';m.export_obj(obj)
    assert m.import_obj(obj)==data
    obj.write_text(obj.read_text().replace('v 7 0 0','v 9 0 0'))
    changed=m.import_obj(obj)
    assert changed!=data and len(changed)==len(data)
    assert changed[160:]==data[160:]
    assert struct.unpack_from('<hhh',changed,76)==(9,0,0)
    obj.write_text(obj.read_text().replace('f 1//1','f 3//1'))
    with pytest.raises(ValueError,match='Topologie'):m.import_obj(obj)


def test_native_atlas_roundtrip_new_colors_and_eyes(tmp_path):
    data=native_fixture();tex=NativeTexture(data);png=tmp_path/'skin.png';tex.to_image().save(png)
    assert tex.replace(png)==data
    assert tex.model.eyes()[0].width==8
    image=tex.to_image()
    for i in tex._eye_positions():image.putpixel((i%128,i//128),(0,248,0,255))
    image.save(png);changed=tex.replace(png,eyes_only=True)
    assert changed!=data and len(changed)==len(data)
    assert changed[:160]==data[:160]
    again=NativeTexture(changed).to_image()
    for i in tex._eye_positions():assert again.getpixel((i%128,i//128))==(0,248,0,255)
    # Other body pixels in the atlas are ignored by eyes-only import.
    image.putpixel((100,100),(248,0,248,255));image.save(png)
    assert tex.replace(png,eyes_only=True)==changed
    with pytest.raises(ValueError,match='CLUT'):tex.replace(png)


def test_bad_png_layout_reserved_rows_and_too_many_colors(tmp_path):
    data=native_fixture();tex=NativeTexture(data);png=tmp_path/'skin.png'
    Image.new('RGBA',(16,16)).save(png)
    with pytest.raises(ValueError,match='128×256'):tex.replace(png)
    image=tex.to_image();image.putpixel((0,255),(255,0,0,255));image.save(png)
    with pytest.raises(ValueError,match='reserviert'):tex.replace(png)
    image=tex.to_image()
    for i,index in enumerate(sorted(tex._eye_positions())[:17]):image.putpixel((index%128,index//128),((i%8)*32,(i//8)*32,128,255))
    image.save(png)
    with pytest.raises(ValueError,match='Maximal 16'):tex.replace(png)


def test_malformed_native_model_rejected():
    data=bytearray(native_fixture());struct.pack_into('<I',data,12,0)
    with pytest.raises(ValueError,match='Geometrie'):NativeModel(data)
    with pytest.raises(ValueError):NativeModel(b'not a model')


def test_native_replacement_preserves_animation_bone_interface():
    from dw2studio.core.native_model import validate_replacement
    data=native_fixture();changed=bytearray(data);struct.pack_into('<I',changed,24,2)
    with pytest.raises(ValueError,match='Hierarchie'):validate_replacement(data,changed)
    assert validate_replacement(data,data)==data
