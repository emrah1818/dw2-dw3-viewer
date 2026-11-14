"""Synthetic native PS1 models only: no game copyrighted assets in tests."""
from __future__ import annotations
import struct
import pytest
from PIL import Image

from dw2studio.core.dw2_eyes import (eye_layout,eye_clut_map,eye_atlas,
                                     eye_animation_frames,blink_frame_at)
from dw2studio.core.dw2_palette_recolor import preview_native_texture
from dw2studio.core.dw2_native_atlas import decode_native_atlas


def synthetic_greymon_eye_layout():
    # Generate a tiny, fully artificial primitive table and a standard
    # 16448-byte DW2-shaped TIM with five differently colored eye tiles.
    tri = lambda a,b,c: (b'\0'*6 + bytes([*a,*b,*c]) + struct.pack('<HH',16000,0))
    primitive = (struct.pack('<I',0)*3 + struct.pack('<I',2) +
                 tri((40,48),(79,48),(40,95)) +
                 tri((79,48),(79,95),(40,95)))
    start=52+len(primitive)
    data=bytearray(start+16448)
    struct.pack_into('<III',data,0,start,start+16448,1)
    struct.pack_into('<I',data,20,52)  # primitive offset
    data[28:52]=(b'\x0a\x30\x0a\x30'+bytes(6)+bytes([255])*12+b'\0\0')[:24]
    data[52:start]=primitive
    t=start
    struct.pack_into('<III',data,t,16,8,44)
    struct.pack_into('<HHHH',data,t+12,0,0,256,1)
    struct.pack_into('<I',data,t+52,16396)
    struct.pack_into('<HHHH',data,t+56,0,0,32,256)
    bank=t+16448-2048+26*64
    # 16 colors, guaranteed opaque and distinct for each pose.
    for i in range(16):struct.pack_into('<H',data,bank+2*i,i*150+1)
    for f,(x,y,w,h) in enumerate(((0,0,40,48),(40,0,40,48),(80,0,40,48),
                                (0,48,40,48),(40,48,40,48))):
        for yy in range(y,y+h):
            for xx in range(x,x+w):
                p=yy*128+xx;at=t+64+p//2
                if p%2:data[at]=(data[at]&15)|((f+1)<<4)
                else:data[at]=(data[at]&240)|(f+1)
    return bytes(data)


def test_exposes_all_five_native_frames():
    model=synthetic_greymon_eye_layout()
    layout=eye_layout(model)
    assert layout is not None and len(layout.sources)==5
    full=eye_atlas(model)
    assert full.size==(128,256)
    assert full.getpixel((10,10))[3]>0
    assert full.getpixel((100,10))[3]>0
    plain=decode_native_atlas(model,struct.unpack_from('<I',model)[0])
    assert plain.getpixel((10,10))[3]==0  # why converter PNG hid eye frame
    frames=eye_animation_frames(model)
    assert len(frames)==5
    assert len({f.getpixel((45,55)) for f in frames})==5
    assert frames[4].getpixel((45,55))==plain.getpixel((45,55))


def test_native_eye_export_encodes_noop_byteidentically():
    model=synthetic_greymon_eye_layout()
    offset=struct.unpack_from('<I',model)[0]
    atlas=eye_atlas(model)
    tim,pred,quality=preview_native_texture(model,offset,atlas,eye_frames=True)
    assert tim==model[offset:offset+16448]
    assert pred.tobytes()==atlas.tobytes()
    assert quality.alpha_mismatch_fraction==0


def test_native_eye_recolor_keeps_geometry_and_frame_count():
    model=synthetic_greymon_eye_layout()
    offset=struct.unpack_from('<I',model)[0]
    image=eye_atlas(model)
    pix=image.load()
    for y in range(0,40):
        for x in range(80,120):
            if pix[x,y][3]>=64:pix[x,y]=(16,112,216,pix[x,y][3])
    tim,pred,quality=preview_native_texture(model,offset,image,eye_frames=True)
    modified=model[:offset]+tim+model[offset+16448:]
    assert modified[:offset]==model[:offset]
    assert eye_layout(modified) is not None
    assert pred.getpixel((90,10))[:3] != eye_atlas(model).getpixel((90,10))[:3]
    assert quality.palettes_rewritten>=1


def test_different_blink_layout_is_not_guessed():
    model=bytearray(synthetic_greymon_eye_layout())
    model[28]=14
    assert eye_layout(model) is None
    with pytest.raises(ValueError):eye_atlas(model)


def test_blink_timing_preview():
    assert blink_frame_at(0)==4
    assert blink_frame_at(3.56)==1
    assert blink_frame_at(3.65)==2
    assert blink_frame_at(3.8)==4
    with pytest.raises(ValueError):blink_frame_at(1,period=0)
