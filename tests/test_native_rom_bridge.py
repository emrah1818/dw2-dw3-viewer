"""Native PS1 TIM image tests: no generic OBJ/native model encoder is claimed."""
from pathlib import Path
import struct
from types import SimpleNamespace

import pytest
from PIL import Image

from dw2studio.assets.tim import TIM
from dw2studio.core.disc import Entry
from dw2studio.core.psx_patch import regenerate_form1, validate_form1_ecc
from dw2studio.core.psx_sector import SYNC, RAW_SIZE
from dw2studio.core.native_rom_bridge import (
    native_png, native_texture_info, native_model_entry, write_native_png_image_copy,
    write_cue_for_image, raw_image_path,
)


def native_model():
    palette = [0, 31, 992, 32767] + [0] * 12
    clut = struct.pack('<I4H', 44, 0, 0, 16, 1) + b''.join(struct.pack('<H', i) for i in palette)
    pixels = struct.pack('<I4H', 16, 0, 0, 1, 2) + bytes.fromhex('11 11 11 11')
    return b'MODEL-GEOMETRY' + struct.pack('<II',16,8) + clut + pixels + b'ANIMATION-DATA'


def sector(i, data=b''):
    raw = bytearray(RAW_SIZE)
    raw[:12] = SYNC
    raw[12:16] = bytes([0, i//75, i%75, 2])
    raw[16:20] = bytes([1,0,8,0])
    raw[20:24] = raw[16:20]
    raw[24:24+len(data)] = data
    return regenerate_form1(raw)


def image_fixture(tmp_path):
    payload = bytearray(2048)
    payload[0:6] = b'\x01CD001'
    root = bytearray(34)
    struct.pack_into('<I', root, 2, 19)
    struct.pack_into('<I', root, 10, 2048)
    payload[156:190] = root
    native = native_model()
    stream = [sector(i, native if i==3 else bytes(payload) if i==16 else b'') for i in range(24)]
    path = tmp_path/'original.bin'
    path.write_bytes(b''.join(stream))
    cue = tmp_path/'original.cue'
    cue.write_text('FILE "original.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')
    entry = Entry('RECOVERED/M003AGUM.BIN',3,len(native),False)
    digi = SimpleNamespace(id=3, code='AGUM', name='Agumon')
    return path, cue, entry, digi, native


def test_native_png_write_new_game_bin_and_cue(tmp_path):
    path, cue, entry, digi, original = image_fixture(tmp_path)
    assert raw_image_path(cue) == path.resolve()
    png, info = native_png(cue, [entry], digi, tmp_path/'original_native.png')
    assert info.region.width == 4 and info.region.height == 2
    with Image.open(png) as image:
        assert image.size == (4,2)
        Image.new('RGBA',image.size,(137,42,206,255)).save(tmp_path/'custom.png')
    dest = tmp_path/'changed.bin'
    result, data, count = write_native_png_image_copy(cue,[entry],digi,tmp_path/'custom.png',dest)
    assert result == dest and count == 1 and dest.stat().st_size == path.stat().st_size
    orig_bytes = path.read_bytes()
    patched = dest.read_bytes()
    assert orig_bytes != patched
    assert orig_bytes[:3*RAW_SIZE] == patched[:3*RAW_SIZE]
    assert orig_bytes[4*RAW_SIZE:] == patched[4*RAW_SIZE:]
    assert validate_form1_ecc(patched[3*RAW_SIZE:4*RAW_SIZE])
    new_file = patched[3*RAW_SIZE+24:3*RAW_SIZE+24+len(original)]
    start,end = info.region.offset,info.region.offset+info.region.length
    assert new_file[:start] == original[:start]
    assert new_file[end:] == original[end:]
    tim = TIM(new_file[start:])
    r,g,b,a = tim.to_image().getpixel((0,0))
    assert abs(r-137)<10 and abs(g-42)<10 and abs(b-206)<10 and a==255
    new_cue = write_cue_for_image(cue,dest)
    assert new_cue.is_file() and '"changed.bin"' in new_cue.read_text()
    assert raw_image_path(new_cue)==dest.resolve()
    assert path.read_bytes()==orig_bytes


def test_validation_before_writing(tmp_path):
    source,cue,entry,digi,_ = image_fixture(tmp_path)
    with pytest.raises(ValueError,match='muss 4 × 2'):
        Image.new('RGBA',(10,20)).save(tmp_path/'wrong.png')
        write_native_png_image_copy(source,[entry],digi,tmp_path/'wrong.png',tmp_path/'never.bin')
    assert not (tmp_path/'never.bin').exists()
    path,info=native_png(source,[entry],digi,tmp_path/'unchanged.png')
    with pytest.raises(ValueError,match='keine'):
        write_native_png_image_copy(source,[entry],digi,path,tmp_path/'no_change.bin')
    assert not (tmp_path/'no_change.bin').exists()
    assert not (tmp_path/'no_change.bin.tim-verification-partial').exists()
    with pytest.raises(ValueError,match='nicht vorhanden'):
        native_model_entry([entry],SimpleNamespace(id=100,code='????'))
    with pytest.raises(ValueError,match='mehrfach'):
        native_model_entry([entry,Entry(entry.path,4,entry.size,False)],digi)
    with pytest.raises(FileExistsError):
        native_png(source,[entry],digi,path)


def test_preserve_original_when_corrupted(tmp_path):
    image, _, entry,digi,_ = image_fixture(tmp_path)
    new=bytearray(image.read_bytes())
    new[3*RAW_SIZE+40]^=0xff
    image.write_bytes(new)
    with pytest.raises(ValueError):
        native_texture_info(image,[entry],digi)
    assert not list(tmp_path.glob('*.partial'))
