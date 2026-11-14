"""1.0: DW3 FaceRects become DW2 eye / face records (Gfx_AnimateModelTex). Self-made data."""
import struct
import numpy as np
from PIL import Image

from dw2studio.core.dw3_native import face_plan, atlas, face_records, encode_model, encode_animation
from dw2studio.core.native_model import NativeModel
from dw2studio.dw3_fighters import _face


def source(tmp_path):
    img = Image.new('RGBA', (256, 256), (40, 40, 40, 255))
    px = img.load()
    for y in range(64, 80):                     # eye area: white
        for x in range(32, 64):
            px[x, y] = (255, 255, 255, 255)
    for y in range(200, 216):                   # frames: open (white), half (grey), closed (black)
        for x in range(0, 32):
            px[x, y] = (255, 255, 255, 255)
        for x in range(32, 64):
            px[x, y] = (128, 128, 128, 255)
        for x in range(64, 96):
            px[x, y] = (0, 0, 0, 255)
    img.save(tmp_path / 'tex0.png')
    face = {'indices': [0, 1, 2], 'uv': [[32, 64], [63, 64], [32, 79]], 'image': 0, 'abr': 0}
    return {'format': 1, 'fps': 30, 'images': ['tex0.png'], 'pages': [[8, 0]], 'tex_origin': [512, 0],
            'bones': [{'parent': -1, 'vertices': [], 'faces': []},
                      {'parent': 0, 'vertices': [[0, 0, 0], [100, 0, 0], [0, 100, 0]], 'faces': [face]}],
            'motions': [{'id': 1, 'frames': [[np.eye(4).ravel().tolist()] * 2] * 2}]}


# tpage 8: x = 8*64 = 512 = TEX_X; the eye at texel 32,64 = halfword 8 relative to the origin
FACE = [{'x': 8, 'y': 64, 'w': 8, 'h': 16, 'frames': [(0, 200), (8, 200), (16, 200)]},
        {'x': 0, 'y': 0, 'w': 0, 'h': 0, 'frames': [(0, 0)] * 3}]


def test_face_table_parser_stops_at_ff():
    raw = bytes([8, 64, 8, 16, 0, 200, 8, 200, 16, 200]) + bytes([0xFF]) + bytes(20)
    rects = _face(raw, 0)
    assert rects == [{'x': 8, 'y': 64, 'w': 8, 'h': 16, 'frames': [(0, 200), (8, 200), (16, 200)]}]


def test_plan_maps_rect_to_page_pixels(tmp_path):
    parts, notes = face_plan(source(tmp_path), FACE)
    assert notes == [] and parts == [{'slot': 0, 'image': 0, 'dst': (32, 64), 'size': (32, 16),
                                      'frames': [(0, 200), (32, 200), (64, 200)]}]
    s = source(tmp_path)
    del s['pages']
    assert face_plan(s, FACE)[1]                 # old conversion: reason, no guess


def test_atlas_holds_three_aligned_frames_and_record(tmp_path):
    s = source(tmp_path)
    parts, _ = face_plan(s, FACE)
    tim, hd, tiles, records = atlas(s, tmp_path, 1, parts)
    assert len(records) == 1
    r = records[0]
    assert r['dst'][0] % 4 == 0 and r['size'][0] % 4 == 0 and all(f[0] % 4 == 0 for f in r['frames'])
    pix = np.frombuffer(tim[20:20 + 256 * 64], dtype=np.uint8).reshape(256, 64)
    idx = np.zeros((256, 128), np.uint8)
    idx[:, 0::2], idx[:, 1::2] = pix & 15, pix >> 4
    w, h = r['size']
    crops = [idx[y:y + h, x:x + w] for x, y in r['frames']]
    assert not np.array_equal(crops[0], crops[2])                          # open differs from closed
    x, y = r['dst']
    assert np.array_equal(idx[y:y + h, x:x + w], crops[0])                  # the page shows the open frame
    rec = face_records(records)
    assert rec[0] == x // 4 and rec[1] == y and rec[2] == w // 4 and rec[3] == h
    assert rec[10] == 255 and rec[20] == 255 and len(rec) % 4 == 0          # no second eye, end


def test_model_carries_eyes_and_stays_valid(tmp_path):
    s = source(tmp_path)
    native, _, rep = encode_model(s, tmp_path, face=FACE)
    m = NativeModel(native)
    assert rep['eyes'] == 1 and len(m.eyes()) == 1
    plain, _, rep2 = encode_model(s, tmp_path)
    assert rep2['eyes'] == 0 and native[NativeModel(plain).blink_offset] != 255
    assert plain[NativeModel(plain).blink_offset] == 255
    encode_animation(s, {0: 0})
