"""Regression: tiny blue/purple eye edits must not disappear in shared gray palettes."""
import struct
from pathlib import Path
import pytest
from PIL import Image
from PyQt6.QtWidgets import QFileDialog
from dw2studio.assets.tim import TIM
from dw2studio.core.dw2_native_atlas import decode_native_atlas,face_clut_map
from dw2studio.core.dw2_palette_recolor import (_raw_color,_decode,_palette_from_target,
    preview_native_texture,measure_native_quality)
from dw2studio.core.native_tim_patch import replace_tim
from test_dw2_native_atlas import model_fixture


def gray_model(colors=16):
    model=bytearray(model_fixture());tim=TIM(model[128:]);start=128+tim.pixel_offset
    palette=[_raw_color((i*16,)*3) for i in range(16)]
    struct.pack_into('<16H',model,128+tim.end-2048,*palette)
    for p in range(128*224):
        value=(p%128)//5%colors;offset=start+p//2
        model[offset]=(model[offset]&15)|(value<<4) if p&1 else (model[offset]&240)|value
    return bytes(model)


def target_eye(model):
    target=decode_native_atlas(model,128)
    # Only four tiny pixels, surrounded by thousands of gray metal pixels.
    edits={(20,20):(8,96,248,255),(21,20):(128,32,240,255),
           (20,21):(248,40,96,255),(21,21):(32,240,200,255)}
    for pos,color in edits.items():target.putpixel(pos,color)
    return target,edits


def test_tiny_color_edits_are_pinned_when_sharing_sixteen_grays():
    model=gray_model();target,edits=target_eye(model)
    tim,predicted,quality=preview_native_texture(model,128,target,palette_mode='protect')
    assert quality.edited_pixels_checked==4 and quality.edited_mean_rgb_error==0
    assert quality.edited_chroma_lost==0 and quality.edited_bad_pixel_fraction==0
    for pos,color in edits.items():assert predicted.getpixel(pos)==color
    assert tim[-2048:]!=model[-2048:] and len(tim)==16448
    assert model==gray_model()


def test_exact_mode_preserves_all_colors_if_they_fit():
    model=gray_model(15);target=decode_native_atlas(model,128);target.putpixel((20,20),(8,96,248,255))
    tim,predicted,quality=preview_native_texture(model,128,target,palette_mode='exact')
    cmap=face_clut_map(model)
    assert all(predicted.getpixel((p%128,p//128))==target.getpixel((p%128,p//128)) for p,c in enumerate(cmap[:128*224]) if c!=-1)
    assert quality.mean_rgb_error==0 and quality.edited_mean_rgb_error==0
    assert tim[:64]==model[128:192]


def test_exact_mode_rejects_extra_colors_instead_of_grayscaling(tmp_path):
    model=gray_model();target,edits=target_eye(model);path=tmp_path/'eye.png';target.save(path)
    for operation in (lambda:preview_native_texture(model,128,target,palette_mode='exact'),
                      lambda:replace_tim(model,path,recolor=True,palette_mode='exact')):
        with pytest.raises(ValueError,match='Teilpalette 0.*maximal 16'):operation()
    assert model==gray_model()


def test_quality_guard_detects_local_color_loss_despite_near_zero_global_error(monkeypatch):
    import dw2studio.core.dw2_native_atlas as atlas
    model=gray_model();target,edits=target_eye(model)
    quality=measure_native_quality(model,128,target,original_model=model)
    assert quality.mean_rgb_error<1 and quality.bad_pixel_fraction<.01
    assert quality.edited_chroma_lost==4 and quality.edited_mean_rgb_error>18
    # Mimic the broken encoder: it keeps old grayscale data and looks globally fine.
    monkeypatch.setattr(atlas,'encode_native_atlas',lambda *args,**kwargs:model[128:128+16448])
    with pytest.raises(ValueError,match='bearbeiteten Farben'):preview_native_texture(model,128,target)


def test_rgb555_rounding_is_hardware_precision_not_a_gray_palette():
    model=gray_model(15);target=decode_native_atlas(model,128);target.putpixel((20,20),(3,97,255,255))
    _,predicted,quality=preview_native_texture(model,128,target,palette_mode='exact')
    assert predicted.getpixel((20,20))==_decode(_raw_color((3,97,255)),False)
    assert predicted.getpixel((20,20))[2]==248 and quality.edited_max_rgb_error<=7


def test_visibility_and_stp_classes_survive_custom_palette():
    original=[0,_raw_color((64,64,64)),_raw_color((32,32,32),semi=True)]+[0]*13
    samples=[(0,0,(0,0,0,0),True,(0,0,0,0)),
             (1,1,(8,96,248,255),True,_decode(original[1],True)),
             (2,2,(128,32,240,127),True,_decode(original[2],True))]
    palette,indexes=_palette_from_target(samples,original,palette_mode='exact')
    assert [_decode(palette[i],s[3])[3] for s,i in zip(samples,indexes)]==[0,255,127]
    assert _decode(palette[indexes[1]],True)[:3]==(8,96,248)


def test_over_budget_many_new_colors_cannot_report_success_if_they_lose_hue():
    model=gray_model();target=decode_native_atlas(model,128)
    for y in range(10,40):
        for x in range(10,40):target.putpixel((x,y),(8+(x%8)*8,32+(y%8)*8,248,255))
    _,predicted,quality=preview_native_texture(model,128,target,palette_mode='protect')
    assert quality.edited_chroma_lost==0 and quality.edited_mean_rgb_error<18
    assert predicted.getpixel((20,20))[2]>180


@pytest.mark.parametrize('raw',[False,True])
def test_saved_image_contains_the_same_new_palette_as_the_preview(tmp_path,raw):
    from dw2studio.core.disc import Entry
    from dw2studio.core.edit_session import EditSession
    model=gray_model(15);target=decode_native_atlas(model,128);target.putpixel((20,20),(8,96,248,255))
    png=tmp_path/'blue.png';target.save(png);expected,_,_=preview_native_texture(model,128,target,palette_mode='exact')
    changed,_=replace_tim(model,png,recolor=True,palette_mode='exact');image=tmp_path/('original.bin' if raw else 'original.iso');payload=model.ljust(20480,b'\0')
    from test_native_rom_bridge import sector
    original=b''.join(sector(i,payload[i*2048:(i+1)*2048]) for i in range(10)) if raw else payload
    image.write_bytes(original);size=2352 if raw else 2048
    entry=Entry('M003TEST.BIN',0,len(model),False);session=EditSession(image,size);session.stage(entry,changed)
    output,_=session.save(tmp_path/('changed.bin' if raw else 'changed.iso'));saved=EditSession(output,size).current(entry)
    assert saved[128:128+16448]==expected and len(saved)==len(model)
    assert image.read_bytes()==original and output.stat().st_size==len(original)
    assert decode_native_atlas(saved,128).getpixel((20,20))==(8,96,248,255)


def test_gui_selected_exact_mode_passes_to_preview_and_encoder(window,tmp_path,monkeypatch):
    from dw2studio.core.disc import Entry
    from dw2studio.core.catalog import DigimonCandidate
    from dw2studio.core.edit_session import EditSession
    model=gray_model(15);target=decode_native_atlas(model,128);target.putpixel((20,20),(8,96,248,255));png=tmp_path/'blue.png';target.save(png)
    image=tmp_path/'game.iso';image.write_bytes(model.ljust(20480,b'\0'));entry=Entry('M003TEST.BIN',0,len(model),False)
    digi=DigimonCandidate(3,'TEST','Test',[entry]);window.image_path=image;window.session=EditSession(image,2048);window.entries=[entry];window.current=window.loaded_digimon=digi;window.active_digimon_key='003TEST'
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *a,**k:(str(png),''));monkeypatch.setattr(window,'load_digimon',lambda:None)
    seen=[]
    def confirm(*args,**kwargs):seen.append(kwargs['palette_mode']);return True
    monkeypatch.setattr(window,'_confirm_native_colors',confirm)
    window.palette_mode.setCurrentIndex(window.palette_mode.findData('exact'));window.import_native_png()
    assert seen==['exact'] and not window.test_errors
    assert decode_native_atlas(window.session.current(entry),128).getpixel((20,20))==(8,96,248,255)
