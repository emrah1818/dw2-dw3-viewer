"""Regression tests for the user-facing, byte-preserving PNG path."""
import json
import zipfile
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from PIL import Image, ImageCms, PngImagePlugin
from dw2studio.core import gltf_textures as gt
from dw2studio.core.mini_assets import replace_texture, export_texture, create_workcopy, texture_slots
from dw2studio.core.model_export import export_model
from dw2studio.core.model_replacements import active_replacement, publish_replacement
from dw2studio.core.rgb_project import save_rgb_project, load_rgb_project
from test_replacements_v2 import make_gltf
from test_rig_import_v8 import project


def colorful(path, variant=0):
    y,x=np.indices((131,73))
    pixels=np.stack(((x*3+variant)%256,y%256,(x+y)%256,np.full_like(x,255)),axis=-1).astype('uint8')
    pixels[0,0,3]=0
    info=PngImagePlugin.PngInfo();info.add_text('Author','Original edit')
    profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    Image.fromarray(pixels).save(path,pnginfo=info,icc_profile=profile)
    assert len(np.unique(pixels.reshape(-1,4),axis=0))>658
    return path.read_bytes()


@pytest.mark.parametrize('suffix',['.gltf','.glb'])
def test_many_colors_alpha_icc_and_png_bytes_survive_export(tmp_path,suffix):
    original=make_gltf(tmp_path/'source');model=original
    if suffix=='.glb':model=export_model(original,tmp_path/'model.glb')
    before=gt.document(model);source=tmp_path/'edited.png';payload=colorful(source)
    work=create_workcopy(model,tmp_path/'work');replace_texture(work,0,source)
    assert gt.image_bytes(work,0)==payload
    for key in ('animations','skins','nodes'):assert gt.document(work)[key]==before[key]
    source.write_bytes(b'changed after import')
    out=tmp_path/'result.png';export_texture(work,0,out);assert out.read_bytes()==payload
    glb=export_model(work,tmp_path/'export'/'result.glb')
    gltf=export_model(glb,tmp_path/'second'/'result.gltf')
    assert gt.image_bytes(glb,0)==gt.image_bytes(gltf,0)==payload
    assert gt.read_glb(glb)[1][:6]==b'ABCDEF'


def test_sixteen_bit_png_is_not_decoded_and_reencoded(tmp_path):
    model=make_gltf(tmp_path/'source');png=tmp_path/'16bit.png'
    Image.fromarray(np.arange(2048,dtype=np.uint16).reshape(32,64)).save(png)
    payload=png.read_bytes();assert payload[24]==16
    replace_texture(model,0,png)
    glb=export_model(model,tmp_path/'result.glb')
    assert gt.image_bytes(glb,0)==payload


def test_obj_jpeg_reference_becomes_exact_png(tmp_path):
    obj=tmp_path/'model.obj';obj.write_text('mtllib mesh.mtl\nv 0 0 0\nv 1 0 0\nv 0 1 0\nusemtl skin\nf 1 2 3\n')
    (tmp_path/'mesh.mtl').write_text('newmtl skin\nmap_Kd -clamp on old.jpg\n')
    jpg=tmp_path/'old.jpg';Image.new('RGB',(8,8),'red').save(jpg);old=jpg.read_bytes()
    png=tmp_path/'new.png';payload=colorful(png);replace_texture(obj,0,png)
    assert jpg.read_bytes()==old
    assert '-clamp on old_ersetzt.png' in (tmp_path/'mesh.mtl').read_text()
    assert texture_slots(obj)[0][1].read_bytes()==payload
    copied=export_model(obj,tmp_path/'out'/'export.obj')
    assert texture_slots(copied)[0][1].read_bytes()==payload


def test_portable_project_keeps_two_distinct_models_and_original_bytes(tmp_path):
    models={};expected={}
    for i,key in enumerate(('003AGUM','029MGRE')):
        model=make_gltf(tmp_path/key);png=tmp_path/(key+'.png');expected[key]=colorful(png,i*47)
        replace_texture(model,0,png);models[key]=model
    archive=save_rgb_project(tmp_path/'models.dw2rgb',models)
    root=tmp_path/'restored';loaded=load_rgb_project(archive,root,set(models))
    assert set(loaded)==set(models)
    for key in models:
        assert active_replacement(root/key)==loaded[key]
        assert gt.image_bytes(loaded[key],0)==expected[key]
    assert expected['003AGUM']!=expected['029MGRE']


@pytest.mark.parametrize('malicious',['../escape.txt','unknown_id'])
def test_invalid_project_leaves_existing_mapping_unchanged(tmp_path,malicious):
    root=tmp_path/'registry';model=create_workcopy(make_gltf(tmp_path/'source'),root/'003AGUM');publish_replacement(model,root/'003AGUM')
    manifest=root/'003AGUM'/'replacement.json';before=manifest.read_bytes()
    archive=tmp_path/'bad.dw2rgb'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr('viewer.json',json.dumps({'format':'DW2 Full Color Viewer 1','models':{'999XXXX':'999XXXX/model.gltf'}}))
        if malicious!='unknown_id':z.writestr(malicious,'bad')
    with pytest.raises(ValueError):load_rgb_project(archive,root,{'003AGUM'})
    assert manifest.read_bytes()==before
    assert not (tmp_path/'escape.txt').exists()


def test_explicit_fullcolor_action_bypasses_native_codec_and_survives_navigation(window,tmp_path,monkeypatch):
    import studio as main
    from dw2studio.core.edit_session import EditSession
    from PyQt6.QtWidgets import QFileDialog
    # A real animated skinned model exercises VTK, rather than a UI-only stub.
    models=[]
    for i in range(2):
        folder=tmp_path/f'rig{i}';folder.mkdir();p=project(folder);p.assignment[:]=[0,1]
        path=folder/'rig.gltf';p.export_gltf(path);models.append(path)
    image=tmp_path/'disc.iso';image.write_bytes(bytes(2048*16));before=image.read_bytes()
    window.image=str(image);window.image_path=image;window.index_key='test';window.rgb_namespace='test';window.session=EditSession(image,2048)
    window.catalog=[SimpleNamespace(id=3,code='AGUM',name='Agumon'),SimpleNamespace(id=29,code='MGRE',name='MetalGreymon')]
    window.entries=[];window.refresh_list();window.model_paths=dict(zip(('003AGUM','029MGRE'),models))
    monkeypatch.setattr(window,'start_eyes',lambda:None)
    def forbidden(*args,**kwargs):pytest.fail('Full-color action entered native PS1 encoding')
    monkeypatch.setattr(window,'import_native_png',forbidden);monkeypatch.setattr(window,'_confirm_native_colors',forbidden)
    window.load_digimon();png=tmp_path/'edit.png';payload=colorful(png)
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,**k:(str(png),'PNG'))
    window.replace_preview_png()
    replacement=window.project_model
    assert replacement!=models[0] and not window.active_native
    assert gt.image_bytes(replacement,0)==payload
    from vtkmodules.util.numpy_support import vtk_to_numpy
    actual=[]
    for actor in window.viewer._model_actors:
        texture=actor.GetProperty().GetTexture('albedoTex') or actor.GetTexture()
        if texture:
            texture.Update();im=texture.GetInput()
            actual.append(vtk_to_numpy(im.GetPointData().GetScalars()).reshape((131,73,4)))
    expected=np.array(Image.open(png))
    assert actual and all(np.array_equal(a,expected) or np.array_equal(a,expected[::-1]) for a in actual)
    assert not window.session.edits and image.read_bytes()==before
    window.digimon.setCurrentRow(1);window.load_digimon();assert window.project_model==models[1]
    window.digimon.setCurrentRow(0);window.load_digimon();assert window.project_model==replacement
    # A late native converter result must not undo the new full-color texture.
    window.model_ready('test/003AGUM/0',str(models[0]),.01)
    assert window.project_model==replacement and not window.active_native
    assert not window.test_errors
