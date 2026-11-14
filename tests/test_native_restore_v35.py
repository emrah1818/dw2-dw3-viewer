"""Regression: primary PNG action must use v3.1 native palette writing again."""
import hashlib
import json
import struct
from pathlib import Path
import pytest
from PIL import Image
from PyQt6.QtWidgets import QFileDialog, QDialog, QLabel
from dw2studio.core.dw2_native_atlas import decode_native_atlas
from dw2studio.core.dw2_palette_recolor import preview_native_texture
from dw2studio.core.native_tim_patch import replace_tim, regions
from dw2studio.core.edit_session import EditSession
from dw2studio.core.disc import Entry
from dw2studio.core.catalog import DigimonCandidate
from dw2studio.core.native_rom_bridge import NativeTextureInfo
from test_color_protection_v33 import gray_model
from test_dw2_native_atlas import model_fixture
from test_eye_frames_v25 import synthetic_greymon_eye_layout


def palette_case(name):
    eyes=name=='five_eye_poses'
    model=synthetic_greymon_eye_layout() if eyes else gray_model() if name=='broad_recolor' else model_fixture()
    offset=struct.unpack_from('<I',model)[0]
    target=decode_native_atlas(model,offset,include_eye_frames=eyes)
    if name=='broad_recolor':
        pix=target.load()
        for y in range(81):
            for x in range(81):
                r,g,b,a=pix[x,y]
                if a:pix[x,y]=(r,min(255,g+100),max(0,b-40),a)
    elif name=='many_png_colors':
        for y in range(5,40):
            for x in range(5,40):target.putpixel((x,y),(x*3%256,y*4%256,(x+y)*3%256,255))
    elif name=='five_eye_poses':
        for x,y in ((10,10),(50,10),(90,10),(10,60),(50,60)):
            for dy in range(8):
                for dx in range(8):target.putpixel((x+dx,y+dy),(8,96,248,255))
    elif name=='new_flat_color':
        for y in range(10,40):
            for x in range(10,40):target.putpixel((x,y),(248,192,8,255))
    else:raise ValueError(name)
    return model,offset,target,eyes


@pytest.mark.parametrize('name',['new_flat_color','many_png_colors','broad_recolor','five_eye_poses'])
def test_restored_encoder_matches_actual_v31_golden_bytes(name):
    # Hashes generated with the untouched v3.1 implementation, not v3.5.
    golden=json.loads((Path(__file__).parent/'palette_v31_golden.json').read_text())[name]
    model,offset,target,eyes=palette_case(name)
    tim,predicted,quality=preview_native_texture(model,offset,target,eye_frames=eyes,palette_mode='v31')
    assert hashlib.sha256(tim).hexdigest()==golden['tim_sha256']
    assert hashlib.sha256(predicted.tobytes()).hexdigest()==golden['preview_sha256']
    assert quality.mean_rgb_error==golden['mean_rgb_error']
    assert quality.bad_pixel_fraction==golden['bad_pixel_fraction']
    assert quality.colors_rewritten==golden['colors_rewritten']
    assert quality.palettes_rewritten==golden['palettes_rewritten']
    assert tim[:64]==model[offset:offset+64] and len(tim)==16448


def test_many_colors_are_approximated_instead_of_triggering_exact_limit():
    model,offset,target,eyes=palette_case('many_png_colors')
    assert len(target.getcolors(32768))>658
    with pytest.raises(ValueError,match='maximal 16'):
        preview_native_texture(model,offset,target,palette_mode='exact')
    _,predicted,quality=preview_native_texture(model,offset,target,palette_mode='v31')
    assert quality.mean_rgb_error<5 and quality.alpha_mismatch_fraction==0
    assert max(predicted.getpixel((15,15))[:3])>0


@pytest.mark.parametrize('raw',[False,True])
def test_primary_import_previews_stages_and_saves_real_native_palette(window,tmp_path,monkeypatch,raw):
    from test_native_rom_bridge import sector
    model,offset,target,eyes=palette_case('many_png_colors');png=tmp_path/'edited.png';target.save(png)
    data=model.ljust(20480,b'\0');size=2352 if raw else 2048
    original=b''.join(sector(i,data[i*2048:(i+1)*2048]) for i in range(10)) if raw else data
    image=tmp_path/('game.bin' if raw else 'game.iso');image.write_bytes(original)
    entry=Entry('M003TEST.BIN',0,len(model),False);digi=DigimonCandidate(3,'TEST','Test',[entry])
    window.image_path=image;window.session=EditSession(image,size);window.entries=[entry]
    window.current=window.loaded_digimon=digi;window.active_digimon_key='003TEST';window.active_native=True
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,**k:(str(png),''))
    monkeypatch.setattr(window,'load_digimon',lambda:None)
    seen=[]
    def accept_preview(dialog):
        seen.append([label.text() for label in dialog.findChildren(QLabel)])
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(QDialog,'exec',accept_preview)
    assert window.palette_mode.currentData()=='v31'
    # Use the real main button, including its clicked signal routing.
    window.project_model=tmp_path/'display.gltf';window.update_actions()
    window.model_buttons[0].click()
    assert len(seen)==1 and any('wie v3.1' in text for text in seen[0])
    assert not window.test_errors and len(window.session.edits)==1
    assert image.read_bytes()==original
    expected,decoded,quality=preview_native_texture(model,offset,target,palette_mode='v31')
    changed=window.session.current(entry)
    assert changed[offset:offset+16448]==expected
    assert changed[:offset]==model[:offset] and changed[offset+16448:]==model[offset+16448:]
    output,_=window.session.save(tmp_path/('new.bin' if raw else 'new.iso'))
    saved=EditSession(output,size).current(entry)
    assert saved==changed and output.stat().st_size==image.stat().st_size
    assert decode_native_atlas(saved,offset).tobytes()==decoded.tobytes()
    assert quality.palettes_rewritten>0


def test_cancel_native_preview_never_stages_or_changes_source(window,tmp_path,monkeypatch):
    model,offset,target,eyes=palette_case('new_flat_color');png=tmp_path/'edited.png';target.save(png)
    image=tmp_path/'game.iso';image.write_bytes(model.ljust(20480,b'\0'));before=image.read_bytes()
    entry=Entry('M003TEST.BIN',0,len(model),False);digi=DigimonCandidate(3,'TEST','Test',[entry])
    window.image_path=image;window.session=EditSession(image,2048);window.entries=[entry]
    window.current=window.loaded_digimon=digi;window.active_digimon_key='003TEST';window.active_native=True
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,**k:(str(png),''))
    monkeypatch.setattr(QDialog,'exec',lambda self:QDialog.DialogCode.Rejected)
    window.replace_png()
    assert not window.session.edits and image.read_bytes()==before and not window.test_errors


def test_v31_preview_reports_local_loss_without_new_v33_rejection(window,tmp_path,monkeypatch):
    from test_color_protection_v33 import target_eye
    model=gray_model();target,edits=target_eye(model)
    # A small global tint changes real native bytes while the four vivid
    # pixels still lose saturation with v3.1's whole-bank optimization.
    for y in range(81):
        for x in range(81):
            if (x,y) not in edits:
                r,g,b,a=target.getpixel((x,y));target.putpixel((x,y),(r,g,min(248,b+8),a))
    png=tmp_path/'eye.png';target.save(png)
    _,_,quality=preview_native_texture(model,128,target,palette_mode='v31')
    assert quality.edited_chroma_lost>0
    info=NativeTextureInfo(Entry('M003TEST.BIN',0,len(model),False),regions(model)[0],0,tmp_path/'game.iso',model)
    texts=[]
    def inspect(dialog):
        texts.extend(label.text() for label in dialog.findChildren(QLabel))
        return QDialog.DialogCode.Rejected
    monkeypatch.setattr(QDialog,'exec',inspect)
    assert not window._confirm_native_colors(info,png,palette_mode='v31')
    assert any('Einzelne bearbeitete Bereiche' in text for text in texts)
    assert any('Entfärbte bearbeitete Pixel' in text for text in texts)


def test_converter_cache_follows_palette_bytes_even_when_revision_restarts(window,tmp_path):
    model,offset,target,eyes=palette_case('new_flat_color');png=tmp_path/'new.png';target.save(png)
    first,_=replace_tim(model,png,recolor=True,palette_mode='v31')
    target.paste((8,96,248,255),(10,10,40,40));target.save(png)
    second,_=replace_tim(model,png,recolor=True,palette_mode='v31')
    image=tmp_path/'image.iso';image.write_bytes(model.ljust(20480,b'\0'))
    entry=Entry('M003TEST.BIN',0,len(model),False);digi=DigimonCandidate(3,'TEST','Test',[entry])
    window.image_path=image;window.index_key='same-source';window.entries=[entry];window.session=EditSession(image,2048)
    original_folder=window.request_for(digi).folder
    window.revisions['003TEST']=1;window.session.stage(entry,first);a=window.request_for(digi)
    window.session=EditSession(image,2048);window.session.stage(entry,second);b=window.request_for(digi)
    assert a.key==b.key and a.folder!=b.folder
    window.revisions['003TEST']=7
    assert window.request_for(digi).folder==b.folder
    window.session.remove((entry.path,entry.lba))
    assert window.request_for(digi).folder==original_folder


def test_two_digimon_imports_are_collected_then_exported_together(window,tmp_path,monkeypatch):
    model,offset,target,eyes=palette_case('new_flat_color')
    image=tmp_path/'game.iso';image.write_bytes(model.ljust(20480,b'\0')*2);original=image.read_bytes()
    entries=[Entry('M003TEST.BIN',0,len(model),False),Entry('M004BETA.BIN',10,len(model),False)]
    digis=[DigimonCandidate(3,'TEST','First',[entries[0]]),DigimonCandidate(4,'BETA','Second',[entries[1]])]
    window.image_path=image;window.session=EditSession(image,2048);window.entries=entries;window.catalog=digis
    monkeypatch.setattr(window,'load_digimon',lambda:None)
    monkeypatch.setattr(QDialog,'exec',lambda dialog:QDialog.DialogCode.Accepted)
    expected=[]
    for i,digi in enumerate(digis):
        window.current=window.loaded_digimon=digi;window.active_digimon_key=window.key_for(digi);window.active_native=True
        target.paste(((248,192,8,255),(8,96,248,255))[i],(10,10,40,40))
        png=tmp_path/f'edit{i}.png';target.save(png)
        expected.append(replace_tim(model,png,recolor=True,palette_mode='v31')[0])
        monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,_p=png,**k:(str(_p),''))
        window.replace_png()
    assert len(window.session.edits)==2 and not window.test_errors
    assert window.pending.count()==2 and image.read_bytes()==original
    out,_=window.session.save(tmp_path/'both.iso');session=EditSession(out,2048)
    assert [session.current(e) for e in entries]==expected
    assert out.stat().st_size==len(original)
