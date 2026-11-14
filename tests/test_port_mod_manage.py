"""Installierte PC-Port-Mods ansehen, deaktivieren, aktivieren. Nur synthetische Dateien."""
import json
import pytest
from dw2studio.port_mod_manage import MANIFEST, status, disable, enable


def install(port, *, textures=True):
    files = port / 'Mods' / 'files'
    files.mkdir(parents=True)
    (files / '0C6C.bin').write_bytes(b'typ')
    (files / '0cb9.BIN').write_bytes(b'name')
    (files / 'notiz.txt').write_text('bleibt liegen')
    doc = {'name': 'Test', 'mod_api': 1, 'textures': [], 'files': [
        {'id': 0xC6C, 'path': 'PAK/DIGIMNDT.BIN', 'label': 'Typ'}, {'id': 0xCB9, 'path': 'PAK/MODELDT0.BIN', 'label': 'Name'}]}
    if textures:
        pack = port / 'Mods' / 'Textures' / 'pack'
        pack.mkdir(parents=True)
        (pack / 'a.png').write_bytes(b'png')
        (pack / 'fremd.png').write_bytes(b'nicht vom Manifest genannt')
        doc['textures'] = ['Textures/pack/a.png']
    (port / 'Mods' / MANIFEST).write_text(json.dumps(doc), encoding='utf-8')


def snapshot(port):
    return {p.relative_to(port).as_posix(): p.read_bytes() for p in port.rglob('*') if p.is_file()}


def test_disable_then_enable_restores_every_byte(tmp_path):
    install(tmp_path)
    before = snapshot(tmp_path)
    active = status(tmp_path)['active']
    assert [r['file'] for r in active['files']] == ['files/0C6C.bin', 'files/0cb9.BIN', 'Textures/pack/a.png', MANIFEST]
    assert active['files'][0]['name'] == 'DIGIMNDT.BIN' and active['files'][1]['label'] == 'Name'
    result = disable(tmp_path)
    assert len(result['moved']) == 4
    mods = tmp_path / 'Mods'
    assert not list((mods / 'files').glob('*.bin')) and not list((mods / 'files').glob('*.BIN')) and not (mods / MANIFEST).exists()
    assert (mods / 'files' / 'notiz.txt').exists() and (mods / 'Textures' / 'pack' / 'fremd.png').exists()
    state = status(tmp_path)
    assert not state['active']['files'] and [s['set'] for s in state['disabled']] == [result['set']]
    assert sorted(snapshot(tmp_path).values()) == sorted(before.values())      # nichts gelöscht, nur verschoben
    assert enable(tmp_path)['set'] == result['set']
    assert snapshot(tmp_path) == before and not (mods / 'disabled' / result['set']).exists()


def test_refuses_instead_of_overwriting(tmp_path):
    install(tmp_path, textures=False)
    first = disable(tmp_path)['set']
    with pytest.raises(ValueError, match='keine PC-Port-Mods aktiv'):
        disable(tmp_path)
    install_again = tmp_path / 'Mods' / 'files' / '0C6C.bin'
    install_again.write_bytes(b'neuer Mod')
    before = snapshot(tmp_path)
    with pytest.raises(FileExistsError):
        enable(tmp_path)
    assert snapshot(tmp_path) == before
    second = disable(tmp_path)['set']
    assert second != first and len(status(tmp_path)['disabled']) == 2
    assert enable(tmp_path, first)['set'] == first
    with pytest.raises(ValueError, match='existiert nicht'):
        enable(tmp_path, 'gibt_es_nicht')


def test_manifest_cannot_point_outside_mods(tmp_path):
    install(tmp_path, textures=False)
    (tmp_path / 'dw2.pak').write_bytes(b'original')
    manifest = tmp_path / 'Mods' / MANIFEST
    doc = json.loads(manifest.read_text(encoding='utf-8')); doc['textures'] = ['../dw2.pak']
    manifest.write_text(json.dumps(doc), encoding='utf-8')
    with pytest.raises(ValueError, match='außerhalb'):
        disable(tmp_path)
    assert (tmp_path / 'dw2.pak').read_bytes() == b'original'


def test_missing_port_folder(tmp_path):
    with pytest.raises(ValueError, match='nicht gefunden'):
        status(tmp_path / 'fehlt')
