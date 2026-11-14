"""Regression tests for the v2.8 import/export fixes."""
import json
from PIL import Image
import pytest

from dw2studio.core.mini_assets import create_workcopy, texture_slots, replace_texture, export_texture
from dw2studio.core.model_export import export_model
from dw2studio.core.native_rom_bridge import native_png
from dw2studio.renderer.blink_data import read_blinking_data
from tests.test_native_rom_bridge import image_fixture
from tests.test_replacements_v2 import make_gltf


def _obj_project(root):
    (root/'tex dir').mkdir(parents=True)
    Image.new('RGBA',(4,4),(255,0,0,255)).save(root/'tex dir'/'skin.png')
    Image.new('RGBA',(4,4),(0,255,0,255)).save(root/'eye.png')
    (root/'mat.mtl').write_text(
        'newmtl a\nmap_Kd -s 1 1 1 tex dir\\skin.png\n'      # Backslash, Leerzeichen, Option
        'newmtl b\nmap_Kd C:\\Users\\anderer-pc\\eye.png\n'   # absoluter Pfad eines anderen PCs
        'newmtl c\nmap_Kd fehlt.png\n')                       # fehlende Textur
    (root/'m.obj').write_text('mtllib mat.mtl\nv 0 0 0\nv 1 0 0\nv 0 1 0\nusemtl a\nf 1 2 3\n')
    return root/'m.obj'


def test_obj_import_survives_backslashes_absolute_and_missing_textures(tmp_path):
    work = create_workcopy(_obj_project(tmp_path/'src'), tmp_path/'work')
    names = sorted(n for n, _ in texture_slots(work))
    assert names == ['eye.png', 'skin.png']
    info = json.loads((work.parent/'model_import.json').read_text(encoding='utf-8'))
    assert info['skipped_references'] == ['fehlt.png']
    mtl = (work.parent/'mat.mtl').read_text()
    assert 'C:' not in mtl and '\\' not in mtl           # portable, relative Verweise
    new = tmp_path/'blue.png'
    Image.new('RGBA',(4,4),(0,0,255,255)).save(new)
    slot = [n for n, _ in texture_slots(work)].index('skin.png')
    replace_texture(work, slot, new)
    export_texture(work, slot, tmp_path/'out.png')
    assert Image.open(tmp_path/'out.png').getpixel((0,0)) == (0,0,255,255)


def test_obj_without_mtl_still_imports(tmp_path):
    src = tmp_path/'n.obj'
    src.write_text('mtllib gibtsnicht.mtl\nv 0 0 0\n')
    work = create_workcopy(src, tmp_path/'work')
    assert work.is_file() and texture_slots(work) == []


def test_gltf_export_twice_and_never_overwrites_foreign_files(tmp_path):
    src = make_gltf(tmp_path/'source')
    out = tmp_path/'out'
    out.mkdir()
    (out/'mesh.bin').write_bytes(b'FREMD')
    for _ in range(2):                                    # zweiter Export in dieselbe Datei
        export_model(src, out/'a.gltf')
    assert (out/'mesh.bin').read_bytes() == b'FREMD'
    doc = json.loads((out/'a.gltf').read_text())
    assert (out/doc['buffers'][0]['uri']).read_bytes()[:6] == b'ABCDEF'
    assert (out/doc['images'][0]['uri']).is_file()
    glb = tmp_path/'x.glb'
    export_model(src, glb)
    for _ in range(2):
        export_model(glb, out/'b.gltf')                   # früher: FileExistsError beim 2. Mal
    assert (out/'b_model.bin').is_file()


def test_invalid_blinking_data_never_blocks_loading(tmp_path):
    for extras in ({'blinking_data': [1, 2, 3]}, {'blinking_data': 'x'},
                   {'blinking_data': [300] * 24}, ['kaputt']):
        path = tmp_path/'m.gltf'
        path.write_text(json.dumps({'asset': {'version': '2.0'}, 'scene': 0, 'scenes': [{'extras': extras}]}))
        assert read_blinking_data(path) is None
    path.write_text(json.dumps({'asset': {'version': '2.0'}, 'scenes': [{'extras': {'blinking_data': list(range(24))}}]}))
    assert read_blinking_data(path) == bytes(range(24))
    path.write_text('{kein json')
    assert read_blinking_data(path) is None


def test_native_png_export_may_overwrite_when_confirmed(tmp_path):
    source, cue, entry, digi, _ = image_fixture(tmp_path)
    target = tmp_path/'tim.png'
    native_png(source, [entry], digi, target)
    with pytest.raises(FileExistsError):
        native_png(source, [entry], digi, target)         # ohne Bestätigung weiterhin geschützt
    native_png(source, [entry], digi, target, overwrite=True)
    with pytest.raises(ValueError):
        native_png(source, [entry], digi, tmp_path/'bad.bin', overwrite=True)
