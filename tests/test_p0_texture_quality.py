"""P0 quality: the DW3 texture atlas keeps the pages' texels (charts, one common scale, exact HD)."""
import math
import numpy as np
from PIL import Image
from dw2studio.core.dw3_native import atlas, auto_hd_scale, charts, encode_model, layout, tile_uv
from dw2studio.core.native_model import NativeModel


def wide_source(tmp_path):
    """Two 256x256 pages with noise texels: page 0 used in a 249x80 band (wider than the 128-texel
    atlas), page 1 in two separate small islands. Like DW3 Greymon's pages."""
    rng = np.random.default_rng(7)
    for i in range(2):
        px = rng.integers(0, 256, (256, 256, 4), dtype=np.uint8)
        px[..., 3] = 255
        Image.fromarray(px, 'RGBA').save(tmp_path / f'tex{i}.png')
    verts = [[0, 0, 0], [100, 0, 0], [0, 100, 0], [100, 100, 0]]
    faces = [{'indices': [0, 1, 3, 2], 'uv': [[0, 0], [248, 0], [248, 79], [0, 79]], 'image': 0, 'abr': 0},
             {'indices': [0, 1, 2], 'uv': [[10, 10], [40, 10], [10, 40]], 'image': 1, 'abr': 0},
             {'indices': [1, 3, 2], 'uv': [[200, 200], [230, 200], [200, 230]], 'image': 1, 'abr': 0}]
    eye = np.eye(4).T.ravel().tolist()
    return {'format': 1, 'fps': 30, 'images': ['tex0.png', 'tex1.png'],
            'bones': [{'parent': -1, 'vertices': [], 'faces': []}, {'parent': 0, 'vertices': verts, 'faces': faces}],
            'motions': [{'id': 1, 'frames': [[eye, eye]]}]}


def test_charts_take_only_used_texels(tmp_path):
    s = wide_source(tmp_path)
    found, owner = charts(s, [(256, 256)] * 2)
    assert len(found) == 3                         # page 1's two islands stay apart
    assert sum(c['box'][2] * c['box'][3] for c in found) < 256 * 256 // 2
    assert all(id(f) in owner for f in s['bones'][1]['faces'])


def test_common_scale_keeps_aspect_and_fits(tmp_path):
    s = wide_source(tmp_path)
    found, _ = charts(s, [(256, 256)] * 2)
    scale, tiles, _ = layout(found)
    assert scale > 0.6                            # the old 2x2 grid: 64x112 tiles = 0.25 horizontally
    for x, y, w, h, cx, cy, cw, ch, rot in tiles:
        sw, sh = (h, w) if rot else (w, h)
        assert abs(sw / cw - scale) < 1.5 / cw + 1e-6 and abs(sh / ch - scale) < 1.5 / ch + 1e-6
        assert 0 <= x and x + w <= 128 and 0 <= y and y + h <= 224
    for i, a in enumerate(tiles):                 # no overlap
        for b in tiles[i + 1:]:
            assert a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0] or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1]


def test_hd_holds_every_polygon_texel_exactly(tmp_path):
    s = wide_source(tmp_path)
    k = auto_hd_scale(s, tmp_path)
    tim, hd, tiles, _, owner, scale = atlas(s, tmp_path, k)
    assert k * scale >= 2
    hda = np.asarray(hd)
    for f in s['bones'][1]['faces']:
        page = np.asarray(Image.open(tmp_path / s['images'][f['image']]).convert('RGBA'))
        x, y, tw, th, cx, cy, cw, ch, rot = t = tiles[owner[id(f)]]
        us, vs = [u for u, _ in f['uv']], [v for _, v in f['uv']]
        for v in range(min(vs), max(vs) + 1, 7):
            for u in range(min(us), max(us) + 1, 7):
                fu, fv = (u - cx + .5) / cw, (v - cy + .5) / ch
                if rot:
                    fu, fv = fv, fu
                assert tuple(hda[int((y + fv * th) * k), int((x + fu * tw) * k)]) == tuple(page[v, u])


def test_encoded_uvs_land_on_their_source_texels(tmp_path):
    s = wide_source(tmp_path)
    native, hd, rep = encode_model(s, tmp_path, hd_scale=0)
    assert rep['triangles'] == 4 and rep['charts'] == 3 and rep['texture_scale'] > 0.6
    _, _, tiles, _, owner, scale = atlas(s, tmp_path, rep['hd_scale'])
    for f in s['bones'][1]['faces']:
        t = tiles[owner[id(f)]]
        for u, v in f['uv']:
            ax, ay = tile_uv(t, u, v)
            x, y, tw, th, cx, cy, cw, ch, rot = t
            su = (ay - y + .5) * cw / th if rot else (ax - x + .5) * cw / tw
            sv = (ax - x + .5) * ch / tw if rot else (ay - y + .5) * ch / th
            assert math.hypot(su - .5 + cx - u, sv - .5 + cy - v) <= 0.5 / scale + 1e-6
    NativeModel(native)
