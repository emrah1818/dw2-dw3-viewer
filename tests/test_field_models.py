"""Field/NPC models with A/D/E slots sharing a single physical file (no game data)."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import android_api as api
from dw2studio.core.disc import Entry
from dw2studio.core.fast_loading import ModelRequest, build_model, extract_request, ConversionQueue
from dw2studio.core.native_anim import parse_anim_file
from dw2studio.core.dw3_native import encode_model, encode_animation
from fixtures017 import make_pak
from test_015_native import source
from test_native_anim import modeldt


@pytest.fixture
def field_workspace(tmp_path, monkeypatch):
    ids = json.loads((Path(__file__).resolve().parents[1]/'data/native_file_ids_us.json').read_text())
    src = source(tmp_path)
    src['motions'][0].update(end='loop', loop_key=1)
    model, _, _ = encode_model(src, tmp_path)
    anim = encode_animation(src, {0: 0, 1: 0}, loops=[0, 1])
    fid = ids['E304QTNK.BIN']
    files = {ids['M304QTNK.BIN']: model, fid: anim,
             3258: modeldt([(304, 'Fieldmon', ids['M304QTNK.BIN'], [fid, 0, 0, fid, fid])])}
    image = make_pak(tmp_path/'game', files)
    monkeypatch.setattr(api, 'S', api.State())
    monkeypatch.setattr(api, 'UNDO', []); monkeypatch.setattr(api, 'REDO', [])
    monkeypatch.setattr(api, 'CACHE', tmp_path/'viewer')
    api.CACHE.mkdir()
    api.open_image(str(image))
    return image, src


def test_shared_slot_family_and_preview(field_workspace):
    files, aliases, meta = api._model_family(api._find(304))
    assert [Path(e.path).name for e in files] == ['M304QTNK.BIN', 'E304QTNK.BIN']
    assert list(aliases.values()) == [['A304QTNK.BIN', 'D304QTNK.BIN', 'E304QTNK.BIN']]
    result = api.prepare_model(304)
    assert result['animations'] == ['anim_A0','anim_A1','anim_D0','anim_D1','anim_E0','anim_E1']
    assert api.prepare_model(304)['url'] == result['url']  # cached reopen
    audit = api._audit_one(api._find(304))
    assert set(audit['anims']) == {'A', 'D', 'E'}
    assert api.size_info(304)['height'] > 0


def test_shared_slots_edited_texture_and_queued_path(field_workspace, tmp_path, monkeypatch):
    image, _ = field_workspace
    files, aliases, _ = api._model_family(api._find(304))
    data = api.S.session.current(files[1])
    request = ModelRequest('field', str(image), files + files[1:], tmp_path/'queued', api._find(304), '',
                           {'E304QTNK.BIN': data}, aliases)
    # Even repeated entries and edited bytes must materialize each destination once.
    folder = tmp_path/'extracted'; folder.mkdir()
    extract_request(request, folder)
    assert all((folder/f'{s}304QTNK.BIN').read_bytes() == data for s in 'ADE')
    from dw2studio.core import fast_loading as F
    monkeypatch.setattr(F, 'convert_models', lambda exe, src, out, **kw: api._convert(src, out))
    queue = ConversionQueue(); queue.active='field'; queue.priority='field'
    assert queue.convert(request).is_file()


def test_conflicting_destination_is_rejected(field_workspace, tmp_path):
    image, _ = field_workspace
    files, _, _ = api._model_family(api._find(304))
    aliases = {(e.path,e.lba): 'SAME.BIN' for e in files}
    request = ModelRequest('bad', str(image), files, tmp_path/'bad', api._find(304), '', {}, aliases)
    folder = tmp_path/'badfiles'; folder.mkdir()
    with pytest.raises(ValueError, match='Widersprüchliche'):
        extract_request(request, folder)


def test_domain_dw3_replacement_preserves_shared_table_and_height(field_workspace, tmp_path, monkeypatch):
    image, src = field_workspace
    # A genuinely different skeleton must replace both model and shared animation.
    from copy import deepcopy
    src = deepcopy(src)
    child = deepcopy(src['bones'][1]); child['parent'] = 1
    src['bones'].append(child)
    for frame in src['motions'][0]['frames']:
        frame.append([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1])
    folder = tmp_path/'dw3'; folder.mkdir()
    (folder/'native_source.json').write_text(json.dumps(src))
    # Reuse the synthetic source image from the fixture.
    (folder/'tex0.png').write_bytes((tmp_path/'tex0.png').read_bytes())
    fake = SimpleNamespace(path=tmp_path/'missing.iso', cache=tmp_path/'cache',
                           entries=[Entry('M000TEST.BIN',1,1,False)],
                           catalog=lambda: [{'id':0,'name':'M000TEST','digimon':'Testmon'}])
    monkeypatch.setattr(api, 'DW3', fake)
    monkeypatch.setattr(api, 'prepare_dw3', lambda ident: {'path':str(folder/'model.glb'), 'name':'M000TEST'})
    original_sha = hashlib.sha256(image.read_bytes()).hexdigest()
    plan = api.dw3_native_plan(0,304)
    assert [(a['slot'],a['clip']) for a in plan['assignments']] == [('E',0),('E',1)]
    assert 'Standby' in plan['assignments'][0]['role'] and 'Gehen' in plan['assignments'][1]['role']
    assert plan['assignments'][1]['action']['status'] == 'open'
    assert plan['scale'] == plan['slot_scale']
    result = api.dw3_native_apply(0,304,plan['assignments'])
    assert result['camera'] is None and result['files'] == 2
    assert {Path(e.path).name for e in api.S.session.edits.values()} <= {'M304QTNK.BIN','E304QTNK.BIN'}
    assert not api.S.battle_camera
    assert api.prepare_model(304)['animations'] == ['anim_A0','anim_A1','anim_D0','anim_D1','anim_E0','anim_E1']
    editor = api.anim_editor(304)
    assert editor['field'] and [p['role'] for p in editor['places']] == ['Domain / Feld: Standby','Domain / Feld: Gehen']
    api.anim_apply(304, editor['places'])
    # Project serialization, re-open, re-import and preview must retain the physical E file.
    saved = api.save_project('field.dw2mod')
    api.open_image(str(image)); api.load_project(saved['path'])
    assert len(api.prepare_model(304)['animations']) == 6
    port = tmp_path/'port'; port.mkdir()
    (port/'dw2_mod_api.json').write_text('{"mod_api":2}')
    assert api.export_port_mod(str(port))['count'] == 2
    assert hashlib.sha256(image.read_bytes()).hexdigest() == original_sha
