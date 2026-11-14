"""Regression for the opaque-shadow-only game bug (overwritten embedded CLUT)."""
import struct
import pytest
from PIL import Image

from dw2studio.assets.tim import TIM, find_tim
from dw2studio.core.dw2_native_atlas import (
    decode_native_atlas, encode_native_atlas, face_clut_map,
)
from dw2studio.core.native_tim_patch import replace_tim


def model_fixture():
    # Same 128x256 4bpp layout as real MxxxYYYY.BIN. There is a face-selected
    # 1024-color palette in the last 2048 bytes of the TIM *pixel* region.
    texture_offset = 128
    header = bytearray(texture_offset)
    struct.pack_into('<III', header, 0, texture_offset, texture_offset+16448, 1)
    # offset arrays: vertex, normal, primitive, skeleton
    struct.pack_into('<IIII', header, 12, 80, 84, 52, 0)
    pos = 52
    struct.pack_into('<I', header, pos, 0);pos+=4   # semi-transparent quads
    struct.pack_into('<I', header, pos, 1);pos+=4   # opaque quad
    q = bytearray(20)
    for i, coord in enumerate(((0,0),(80,0),(0,80),(80,80))):
        q[8+i*2:10+i*2] = bytes(coord)
    struct.pack_into('<H', q, 16, 224 << 6)
    header[pos:pos+20] = q;pos+=20
    struct.pack_into('<II', header, pos, 0, 0)
    flags = struct.pack('<II', 0x10, 8)
    clut = struct.pack('<I4H', 44, 0, 480, 256, 1)
    clut += struct.pack('<16H', 0, *([32767] * 15))
    pixels = bytearray([0x11] * 16384)
    # Face palette bank 0: 0 invisible, 1 red, 2 green.
    struct.pack_into('<16H', pixels, 16384-2048, 0, 31, 992, *([32767]*13))
    img_block = struct.pack('<I4H', 16396, 0, 0, 32, 256)
    return bytes(header) + flags + clut + img_block + pixels


def test_realistic_native_tim_roundtrip_keeps_embedded_palette():
    model = model_fixture()
    image = decode_native_atlas(model, 128)
    assert image.getpixel((15,15))[0] > 230
    assert image.getpixel((15,15))[3] == 255
    result = encode_native_atlas(model, 128, image)
    assert result == model[128:128+16448]


def test_native_atlas_modified_colors_do_not_overwrite_real_clut(tmp_path):
    model = model_fixture()
    img = decode_native_atlas(model, 128)
    before = img.getpixel((15,15))
    assert before[0] > 230
    for y in range(10,40):
        for x in range(10,40):
            img.putpixel((x,y),(0,248,0,255))
    path = tmp_path/'edited.png';img.save(path)
    changed, region = replace_tim(model,path)
    assert region.offset == 128
    assert changed != model
    orig_tim = TIM(model[128:])
    new_tim = TIM(changed[128:])
    assert new_tim.data[-2048:new_tim.end] == orig_tim.data[-2048:orig_tim.end]
    assert new_tim.data[:new_tim.pixel_offset] == orig_tim.data[:orig_tim.pixel_offset]
    decoded = decode_native_atlas(changed,128)
    assert decoded.getpixel((15,15))[1] > 230
    assert decoded.getpixel((15,15))[3] == 255


def test_native_atlas_rejects_widespread_transparency():
    model = model_fixture()
    blank=Image.new('RGBA',(128,256),(0,0,0,0))
    with pytest.raises(ValueError,match='ausblenden'):
        encode_native_atlas(model,128,blank)


def test_native_atlas_rejects_old_dummy_palette_export():
    model = model_fixture()
    old=TIM(model[128:]).to_image()
    with pytest.raises(ValueError,match='v2.1/v2.2'):
        encode_native_atlas(model,128,old)
