"""Compatibility regressions for PAK overlays and the DW3 converter boundary."""
import hashlib
import json
import os
from pathlib import Path
import struct
from types import SimpleNamespace
import pytest
from dw2studio.pak import PakFile, MAGIC
from dw2studio.port_mod import export, plan


def make_pak(path, payload, identifier=42, fmt=0):
    h = bytearray(80)
    struct.pack_into('<8s6I', h, 0, MAGIC, 1, 80, 1, 80, 64, 0)
    record = struct.pack('<4I2Q', identifier, 123, 1, fmt, 144, len(payload)) + hashlib.sha256(payload).digest()
    path.write_bytes(h + record + payload)
    return PakFile(path)


def session(payload):
    edit = SimpleNamespace(path='TEST.BIN', lba=123, original=payload, replacement=payload.upper(), relocate=False, label='test')
    return SimpleNamespace(edits={('TEST.BIN', 123): edit}, _check_source=lambda: None)


def test_port_parses_export_as_hex_and_detects_case_alias(tmp_path):
    pak = make_pak(tmp_path / 'test.pak', b'hello')
    files = tmp_path / 'port/Mods/files'
    files.mkdir(parents=True)
    (files / '2a.BIN').write_bytes(b'existing user mod')
    with pytest.raises(FileExistsError):
        export(session(b'hello'), pak, tmp_path / 'port')
    assert (files / '2a.BIN').read_bytes() == b'existing user mod'
    (files / '2a.BIN').unlink()
    result = export(session(b'hello'), pak, tmp_path / 'port')
    target = Path(result['files'][0])
    assert int(target.stem, 16) == 42  # host/pak.c uses strtol(..., 16)
    assert target.name == '002A.bin'


def test_export_rejects_damaged_payload_and_audio(tmp_path):
    pak = make_pak(tmp_path / 'damaged.pak', b'hello')
    with pak.path.open('r+b') as f:
        f.seek(144); f.write(b'xxxxx')
    with pytest.raises(ValueError, match='SHA-256'):
        plan(session(b'hello'), pak)
    audio = make_pak(tmp_path / 'audio.pak', b'hello', fmt=1)
    with pytest.raises(ValueError, match='audio/movie'):
        plan(session(b'hello'), audio)


@pytest.mark.skipif(not os.environ.get('DW2_TEST_PAK'), reason='Private DW2 PAK not provided')
def test_real_pak_edit_preview_mod_and_project_roundtrip(tmp_path, monkeypatch):
    import android_api as api
    from dw2studio.pak_workspace import open_workspace
    session_, entries, catalog, key = open_workspace(os.environ['DW2_TEST_PAK'])
    original_hash = hashlib.sha256(session_.source.read_bytes()).hexdigest()
    monkeypatch.setattr(api, 'S', api.State())
    api.configure(tmp_path, '')
    info = api.open_image(str(session_.source))
    assert info['source_kind'] == 'pak' and info['count'] > 200
    assert api.name_info(3)['current'] == 'Agumon'
    model = api.prepare_model(3)
    assert (api.CACHE / model['url']).is_file()
    api.rename(3, 'TestAgumon')
    api.set_type(3, 2)
    project = api.save_project('test.dw2mod')
    result = api.export_port_mod(str(tmp_path / 'port'))
    manifest = json.loads(Path(result['manifest']).read_text())
    for row in manifest['files']:
        assert row['replacement_sha256'] == hashlib.sha256((tmp_path / 'port/Mods/files' / f"{row['id']:04X}.bin").read_bytes()).hexdigest()
    api.open_image(str(session_.source))
    api.load_project(project['path'])
    assert api.name_info(3)['current'] == 'TestAgumon'
    assert api.type_info(3)['code'] == 2
    assert hashlib.sha256(session_.source.read_bytes()).hexdigest() == original_hash
    with pytest.raises(ValueError, match='PAK'):
        api.S.session.save(tmp_path / 'not-an-image.iso')


@pytest.mark.skipif(not os.environ.get('DW3_TEST_DISC'), reason='Private DW3 disc not provided')
def test_real_dw3_animation_and_textures(tmp_path):
    from dw2studio.dw3 import Dw3Disc
    from dw2studio.core.gltf_mesh import GltfMesh
    from dw2studio.core.gltf_textures import read_glb
    from PIL import Image
    disc = Dw3Disc(os.environ['DW3_TEST_DISC'], tmp_path)
    assert len(disc.catalog()) > 200
    result = disc.prepare(0)
    doc, _, _ = read_glb(result['path'])
    assert len(doc['animations']) > 10 and len(doc['skins'][0]['joints']) > 5
    mesh = GltfMesh(result['path'])
    assert len(mesh.groups) > 5  # rigid skin groups survive material batching
    for image in Path(result['path']).parent.glob('*.png'):
        with Image.open(image) as im:
            im.verify()
