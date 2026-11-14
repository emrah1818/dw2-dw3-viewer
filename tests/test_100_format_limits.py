"""1.0 / Abschnitt 15: DW2 format limits are met by conversion, not by refusing the model.

- more than 256 vertices in one bone -> sibling parts, each with <= 256 vertices
- more than eight hierarchy levels -> deep bones hang on level 7 with the product of the skipped
  local matrices, so every pose stays exact
- protective checks (254 poses, 64 parts, 16-bit) stay in place
"""
import numpy as np
import pytest
from PIL import Image

from dw2studio.core.dw3_native import (encode_model, encode_animation, plan, bone_chunks, limits_report,
                                      MAX_PART, MAX_DEPTH)
from dw2studio.core.native_gltf import NativeModel
from dw2studio.core.native_anim import parse_anim_file


def grid_bone(parent, n):
    """A flat strip with N quads: 2N+2 vertices, 2N triangles."""
    verts = [[x * 10, y * 10, 0] for x in range(n + 1) for y in (0, 1)]
    faces = [{'indices': [2 * x, 2 * x + 2, 2 * x + 1], 'uv': [[0, 0], [1, 0], [0, 1]], 'image': 0, 'abr': 0} for x in range(n)]
    faces += [{'indices': [2 * x + 1, 2 * x + 2, 2 * x + 3], 'uv': [[0, 0], [1, 0], [0, 1]], 'image': 0, 'abr': 0} for x in range(n)]
    return {'parent': parent, 'vertices': verts, 'faces': faces}


def tri_bone(parent):
    return {'parent': parent, 'vertices': [[0, 0, 0], [50, 0, 0], [0, 50, 0]],
            'faces': [{'indices': [0, 1, 2], 'uv': [[0, 0], [1, 0], [0, 1]], 'image': 0, 'abr': 0}]}


def source(tmp_path, bones, frames=None):
    Image.new('RGBA', (64, 64), (200, 100, 50, 255)).save(tmp_path / 'tex0.png')
    n = len(bones)
    if frames is None:
        def m(i, k):
            a = np.eye(4)
            a[0, 3] = 5 + i + k
            if i % 2:
                c, s_ = np.cos(0.1 * k), np.sin(0.1 * k)
                a[:3, :3] = [[c, -s_, 0], [s_, c, 0], [0, 0, 1]]
            return a.T.ravel().tolist()
        frames = [[m(i, k) for i in range(n)] for k in range(3)]
    return {'format': 1, 'fps': 30, 'bones': bones, 'images': ['tex0.png'],
            'motions': [{'id': 1, 'frames': frames}]}


def world(frames, chain_of, b):
    out = np.eye(4)
    for c in chain_of(b):
        out = out @ np.asarray(frames[c]).reshape(4, 4).T
    return out


def test_bone_with_600_vertices_is_split_into_parts(tmp_path):
    big = grid_bone(0, 299)                                  # 600 vertices, 598 triangles
    s = source(tmp_path, [{'parent': -1, 'vertices': [], 'faces': []}, big])
    chunks = bone_chunks(big)
    assert len(chunks) >= 3
    for c in chunks:
        assert len(c) <= MAX_PART and len({f['indices'][k] for f, cs in c for k in cs}) <= MAX_PART
    assert sum(len(c) for c in chunks) == 598
    native, _, rep = encode_model(s, tmp_path)
    model = NativeModel(native)
    assert len(model.parts) == len(chunks) and rep['triangles'] == 598
    assert limits_report(s)['split_bones'] == [1]
    parse_anim_file(encode_animation(s, {0: 0}), len(model.parts))


def test_twelve_levels_are_flattened_with_exact_poses(tmp_path):
    bones = [{'parent': -1, 'vertices': [], 'faces': []}] + [tri_bone(i) for i in range(12)]   # chain depth 12
    s = source(tmp_path, bones)
    nodes = plan(s)
    assert max(n['depth'] for n in nodes) == MAX_DEPTH and len(nodes) == 12
    assert [n['src'] for n in nodes if len(n['chain']) > 1] == [9, 10, 11, 12]
    # every native part's world matrix (DW2 depth stack: parent = last part one level up)
    frames = s['motions'][0]['frames'][1]
    stack, native_world = {}, {}
    for n in nodes:
        local = np.eye(4)
        for c in n['chain']:
            local = local @ np.asarray(frames[c]).reshape(4, 4).T
        parent = stack.get(n['depth'] - 1, np.eye(4))
        native_world[n['src']] = parent @ local
        stack[n['depth']] = native_world[n['src']]
    for b in range(1, 13):                                    # source world = product down the real chain
        chain = []
        x = b
        while x > 0:
            chain.insert(0, x)
            x = bones[x]['parent']
        assert np.allclose(native_world[b], world(frames, lambda _: chain, b))
    native, _, _ = encode_model(s, tmp_path)
    anim = encode_animation(s, {0: 0})
    assert len(parse_anim_file(anim, len(NativeModel(native).parts)).clips[0].rows) == 3
    assert limits_report(s)['flattened_bones'] == [9, 10, 11, 12]


def test_protective_limits_stay(tmp_path):
    bones = [{'parent': -1, 'vertices': [], 'faces': []}] + [tri_bone(0) for _ in range(65)]
    with pytest.raises(ValueError):
        plan(source(tmp_path, bones[:66]))                    # 65 body bones: refused
    many = [{'parent': -1, 'vertices': [], 'faces': []}] + [grid_bone(0, 299) for _ in range(30)]
    with pytest.raises(ValueError, match='DW2-Teile'):
        plan(source(tmp_path, many))                          # 90+ parts after splitting: refused


def test_final_model_check_before_export(tmp_path):
    import struct
    from dw2studio.core.format_limits import model_problems
    bones = [{'parent': -1, 'vertices': [], 'faces': []}, tri_bone(0), tri_bone(1)]
    native, _, _ = encode_model(source(tmp_path, bones), tmp_path)
    assert model_problems(native) == []
    n = NativeModel(native).bone_count
    bad = bytearray(native)
    struct.pack_into('<I', bad, 12 + 12 * n + 4, 8)              # part 1 on level 9
    assert any('Hierarchieebene 9' in p for p in model_problems(bytes(bad)))
    struct.pack_into('<I', bad, 12 + 12 * n + 4, 3)              # jumps from level 1 to 4
    assert any('springt' in p for p in model_problems(bytes(bad)))
    assert model_problems(b'nonsense' * 10)[0].startswith('Modell nicht lesbar')
