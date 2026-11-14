"""PS1-Image-Modus: kontrollierte Optimierung (Vertex-Clustering, Bildschritt) und CUE beim Export."""
from pathlib import Path
from types import SimpleNamespace

import pytest

import android_api as api
from dw2studio.core.dw3_native import encode_animation, encode_model, simplify_source, triangle_total
from dw2studio.core.native_gltf import NativeModel
from dw2studio.core.native_anim import parse_anim_file
from tests.test_100_format_limits import grid_bone, source


def test_simplify_reduces_triangles_and_keeps_input(tmp_path):
    strip = grid_bone(0, 40)
    strip['vertices'] = [[x, y * 3, z] for x, y, z in strip['vertices']]     # 10 × 30 Raster
    s = source(tmp_path, [{'parent': -1, 'vertices': [], 'faces': []}, strip])
    before = triangle_total(s)
    small = simplify_source(s, 15)
    assert triangle_total(small) < before
    assert triangle_total(s) == before                       # Eingabe unverändert
    assert all(len(f['uv']) == 3 for b in small['bones'] for f in b['faces'])
    native, _, rep = encode_model(small, tmp_path)
    assert rep['triangles'] == triangle_total(small)
    parse_anim_file(encode_animation(small, {0: 0}), len(NativeModel(native).parts))
    assert simplify_source(s, 0) is s
    tiny = simplify_source(s, 10000)                          # alles fiele weg: Teil bleibt erhalten
    assert triangle_total(tiny) == before


def test_frame_step_shrinks_animation(tmp_path):
    s = source(tmp_path, [{'parent': -1, 'vertices': [], 'faces': []}, grid_bone(0, 4)])
    import numpy as np
    def m(i, k):
        a = np.eye(4); a[0, 3] = 3 * k + i
        return a.T.ravel().tolist()
    s['motions'][0]['frames'] = [[m(i, k) for i in range(2)] for k in range(18)]   # 18 Bilder
    native, _, _ = encode_model(s, tmp_path)
    parts = len(NativeModel(native).parts)
    full, half = encode_animation(s, {0: 0}), encode_animation(s, {0: 0}, step=2)
    assert len(half) < len(full)
    parse_anim_file(half, parts)
    with pytest.raises(ValueError):
        encode_animation(s, {0: 0}, step=9)


def test_cue_text():
    tpl = 'FILE "Digimon World 2 (USA).bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n'
    assert api.cue_for('neu.bin', tpl) == tpl.replace('Digimon World 2 (USA).bin', 'neu.bin')
    assert 'MODE2/2352' in api.cue_for('x.bin') and '"x.bin"' in api.cue_for('x.bin')


def test_cue_written_next_to_exported_bin(tmp_path, monkeypatch):
    src = tmp_path / 'orig.bin'; src.write_bytes(b'\0' * 2352)
    (tmp_path / 'orig.cue').write_text('FILE "orig.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')
    out = tmp_path / 'out'; out.mkdir()
    exported = out / 'neu.bin'; exported.write_bytes(b'\0' * 2352)
    monkeypatch.setattr(api.S, 'session', SimpleNamespace(sector_size=2352), raising=False)
    monkeypatch.setattr(api.S, 'image_path', src, raising=False)
    monkeypatch.setattr(api.S, 'open_path', tmp_path / 'orig.cue', raising=False)
    cue = api._write_cue(exported)
    assert cue == out / 'neu.cue' and '"neu.bin"' in cue.read_text()
    assert api._write_cue(exported) is None                  # vorhandene CUE bleibt
    assert '"orig.bin"' in (tmp_path / 'orig.cue').read_text()


def test_iso_export_gets_no_cue(tmp_path, monkeypatch):
    iso = tmp_path / 'neu.iso'; iso.write_bytes(b'\0' * 2048)
    monkeypatch.setattr(api.S, 'session', SimpleNamespace(sector_size=2048), raising=False)
    assert api._write_cue(iso) is None
