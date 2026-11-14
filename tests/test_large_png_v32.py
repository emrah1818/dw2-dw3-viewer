"""Full-size project textures and explicit reduction to fixed native PS1 storage."""
from io import BytesIO
from pathlib import Path
import json
import pytest
from PIL import Image
from PyQt6.QtWidgets import QDialog,QFileDialog,QDialogButtonBox,QInputDialog
from dw2studio.core.texture_resolution import (read_png,native_scale,reduce_for_native,
    validate_preview_size,export_template)
from dw2studio.core.mini_assets import create_workcopy,replace_texture,export_texture
from dw2studio.core.model_export import export_model
from dw2studio.core import gltf_textures
from test_replacements_v2 import make_gltf


@pytest.mark.parametrize('factor',[1,2,3,4])
def test_integer_working_sizes_preserve_pixel_art_roundtrip(tmp_path,factor):
    base=Image.new('RGBA',(128,256),(20,90,180,255));base.paste((200,30,10,0),(64,128,128,256))
    path=tmp_path/'work.png';export_template(base,path,factor)
    source=read_png(path)
    assert source.size==(128*factor,256*factor) and native_scale(source.size)==factor
    for method in ('NEAREST','BOX'):
        reduced=reduce_for_native(source,method=method)
        assert reduced.size==base.size
        # Transparent RGB is undefined for averaging, visible pixels stay equal.
        assert reduced.getpixel((20,20))==base.getpixel((20,20)) and reduced.getpixel((100,200))[3]==0


@pytest.mark.parametrize('size',[(256,256),(512,512),(257,512),(640,1280),(8193,1)])
def test_invalid_native_ratio_scale_or_bounds_rejected(size):
    with pytest.raises(ValueError):native_scale(size)


def test_real_png_required_and_preview_ratio_protected(tmp_path):
    path=tmp_path/'fake.png';Image.new('RGB',(128,256)).save(path,'JPEG')
    with pytest.raises(ValueError,match='echte PNG'):read_png(path)
    validate_preview_size((512,1024),(128,256))
    validate_preview_size((256,512),(512,1024))  # returning from 4x to 2x works.
    with pytest.raises(ValueError,match='Seitenverhältnis'):validate_preview_size((512,512),(128,256))


@pytest.mark.parametrize('extension',['.gltf','.glb','.obj'])
def test_full_resolution_preview_and_export_keeps_hd_png(tmp_path,extension):
    if extension=='.obj':
        folder=tmp_path/'source';folder.mkdir();model=folder/'mesh.obj'
        model.write_text('mtllib mesh.mtl\nv 0 0 0\nv 1 0 0\nv 0 1 0\nvt 0 0\nvt 1 0\nvt 0 1\nusemtl skin\nf 1/1 2/2 3/3\n');(folder/'mesh.mtl').write_text('newmtl skin\nmap_Kd base.png\n');Image.new('RGBA',(128,256),(248,0,0,255)).save(folder/'base.png');animations=None
    else:
        model=make_gltf(tmp_path/'source');Image.new('RGBA',(128,256),(248,0,0,255)).save(model.parent/'base.png')
        animations=gltf_textures.document(model)['animations']
        if extension=='.glb':converted=tmp_path/'source.glb';export_model(model,converted);model=converted
    original=model.read_bytes();active=create_workcopy(model,tmp_path/'work')
    for factor in (2,3,4,2):
        png=tmp_path/'high.png';Image.new('RGBA',(128*factor,256*factor),(30,150,210,255)).save(png);replace_texture(active,0,png)
        output=tmp_path/'export.png';export_texture(active,0,output)
        with Image.open(output) as im:assert im.size==(128*factor,256*factor) and im.getpixel((0,0))==(30,150,210,255)
        if animations is not None:assert gltf_textures.document(active)['animations']==animations
    assert model.read_bytes()==original
    if extension!='.obj':
        exported=tmp_path/'final.glb';export_model(active,exported)
        with Image.open(BytesIO(gltf_textures.image_bytes(exported,0))) as im:assert im.size==(256,512)
        assert gltf_textures.document(exported)['animations']==animations


def test_large_native_dialog_requires_acceptance_and_discloses_resolution(qapp,tmp_path,monkeypatch):
    from dw2studio.gui.texture_size_dialog import NativeTextureSizeDialog,prepare_native_png
    path=tmp_path/'high.png';Image.new('RGBA',(512,1024),(0,120,240,255)).save(path)
    dialog=NativeTextureSizeDialog(read_png(path));assert dialog.factor==4
    assert dialog.normalized_image.size==(128,256)
    assert '128×256' in dialog.buttons.button(QDialogButtonBox.StandardButton.Ok).text()
    monkeypatch.setattr(NativeTextureSizeDialog,'exec',lambda d:QDialog.DialogCode.Rejected)
    assert prepare_native_png(path) is None
    monkeypatch.setattr(NativeTextureSizeDialog,'exec',lambda d:QDialog.DialogCode.Accepted)
    assert prepare_native_png(path).size==(128,256)
    dialog.reject()


@pytest.mark.parametrize('factor',[2,3,4])
@pytest.mark.parametrize('eyes_only',[False,True])
def test_large_png_native_buttons_encode_same_size_and_do_not_write_image(window,tmp_path,monkeypatch,factor,eyes_only):
    from test_eye_variants_v26 import synthetic_agumon_style
    from dw2studio.core.edit_session import EditSession
    from dw2studio.core.disc import Entry
    from dw2studio.core.catalog import DigimonCandidate
    from dw2studio.core.dw2_eyes import eye_layout
    from dw2studio.gui.texture_size_dialog import NativeTextureSizeDialog
    model=synthetic_agumon_style();image=tmp_path/'game.iso';original=model.ljust(20480,b'\0');image.write_bytes(original)
    entry=Entry('M003TEST.BIN',0,len(model),False);digi=DigimonCandidate(3,'TEST','Test',[entry])
    window.image=str(image);window.image_path=image;window.entries=[entry];window.current=window.loaded_digimon=digi;window.active_digimon_key='003TEST';window.session=EditSession(image,2048)
    source=window.native_image(window._native_selection(),True);layout=eye_layout(model)
    for x,y,w,h in layout.sources+(layout.target,):source.paste((0,248,0,255),(x,y,x+w,y+h))
    source=source.resize((128*factor,256*factor),Image.Resampling.NEAREST);path=tmp_path/'high.png';source.save(path)
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,**k:(str(path),''))
    monkeypatch.setattr(NativeTextureSizeDialog,'exec',lambda d:QDialog.DialogCode.Accepted)
    verified=[]
    def confirm(info,png,**kwargs):
        with Image.open(png) as im:verified.append(im.size)
        return True
    monkeypatch.setattr(window,'_confirm_native_colors',confirm);monkeypatch.setattr(window,'load_digimon',lambda:None)
    window.import_native_png(eyes_only)
    assert not window.test_errors and verified==[(128,256)] and image.read_bytes()==original
    assert len(window.session.edits)==1 and len(window.session.current(entry))==len(model)
    decoded=window.native_image(window._native_selection(),True);x,y,w,h=layout.target
    assert decoded.getpixel((x+w//2,y+h//2))==(0,248,0,255)
    output,_=window.session.save(tmp_path/'edited.iso');reopened=EditSession(output,2048)
    assert reopened.current(entry)==window.session.current(entry) and output.stat().st_size==len(original)


def test_cancelled_large_native_import_stages_nothing(window,tmp_path,monkeypatch):
    from test_eye_variants_v26 import synthetic_agumon_style
    from dw2studio.core.edit_session import EditSession
    from dw2studio.core.disc import Entry
    from dw2studio.core.catalog import DigimonCandidate
    from dw2studio.gui.texture_size_dialog import NativeTextureSizeDialog
    model=synthetic_agumon_style();image=tmp_path/'cancel.iso';image.write_bytes(model.ljust(20480,b'\0'))
    entry=Entry('M003TEST.BIN',0,len(model),False);digi=DigimonCandidate(3,'TEST','Test',[entry]);window.session=EditSession(image,2048);window.image_path=image;window.entries=[entry];window.loaded_digimon=digi
    png=tmp_path/'large.png';Image.new('RGBA',(512,1024)).save(png)
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,**k:(str(png),''));monkeypatch.setattr(NativeTextureSizeDialog,'exec',lambda d:QDialog.DialogCode.Rejected)
    monkeypatch.setattr(window,'_confirm_native_colors',lambda *a,**k:pytest.fail('Cancelled import must not reach color encoding'))
    window.import_native_png();assert not window.session.edits and not window.test_errors


def test_rig_texture_picker_accepts_large_template_then_uses_native_size(qapp,tmp_path,monkeypatch):
    from test_rig_import_v8 import project
    from dw2studio.gui.rig_dialog import RigImportDialog
    from dw2studio.gui.texture_size_dialog import NativeTextureSizeDialog
    from dw2studio.core.native_texture import NativeTexture
    p=project(tmp_path);image=NativeTexture(p.original).to_image();png=tmp_path/'rig_hd.png';export_template(image,png,4)
    dialog=RigImportDialog(p,tmp_path/'rig_cache')
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,**k:(str(png),''));monkeypatch.setattr(NativeTextureSizeDialog,'exec',lambda d:QDialog.DialogCode.Accepted)
    dialog.load_texture();assert dialog.project.texture_png
    with Image.open(dialog.project.texture_png) as im:assert im.size==(128,256)
    with Image.open(png) as im:assert im.size==(512,1024)
    dialog.reject()


def test_real_vtk_receives_full_hd_texture_and_keeps_animations(window,tmp_path):
    from test_rig_import_v8 import project
    from dw2studio.renderer.eye_vtk import _texture_for_actor
    p=project(tmp_path);p.assignment[:]=[0,1];path=tmp_path/'rig.gltf';p.export_gltf(path)
    png=tmp_path/'hd.png';Image.new('RGBA',(512,1024),(40,120,200,255)).save(png);replace_texture(path,0,png)
    window.viewer.load(path);window.viewer.timer.stop()
    textures=[_texture_for_actor(a) for a in window.viewer._model_actors]
    assert any(t and t.GetInput().GetDimensions()[:2]==(512,1024) for t in textures)
    assert window.viewer.importer.GetNumberOfAnimations()==2
