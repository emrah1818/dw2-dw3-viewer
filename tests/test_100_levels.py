"""1.0: digivolve level per Digimon, prepared format 1 (no effect with the current port)."""
import json
import pytest

from fixtures017 import open_session
from dw2studio.digivolve_levels import validate, dumps, loads, port_supports, FILENAME, FORMAT
from dw2studio.core.digimon_names import NameRepository
from dw2studio.mod_io import check, export_checked


def test_format_roundtrip_and_limits():
    text = dumps({131: 15, '84': 8})
    doc = json.loads(text)
    assert doc == {'format': 1, 'levels': {'84': 8, '131': 15}}
    assert loads(text) == {84: 8, 131: 15}
    assert loads('{"format": 1, "levels": {"5": 3}, "future_key": true}') == {5: 3}   # unknown keys ignored
    with pytest.raises(ValueError, match='Format 2'):
        loads('{"format": 2, "levels": {}}')
    for bad in ({0: 5}, {256: 5}, {5: 0}, {5: 100}, {5: '7'}, {'x': 5}):
        with pytest.raises(ValueError):
            validate(bad)
    with pytest.raises(ValueError, match='format'):
        loads('{"levels": {}}')


def test_port_capability_is_read_from_mod_api_file(tmp_path):
    assert not port_supports(tmp_path)
    (tmp_path / 'dw2_mod_api.json').write_text('{"mod_api": 2}')
    assert not port_supports(tmp_path)                       # the shipped port: not supported
    (tmp_path / 'dw2_mod_api.json').write_text('{"mod_api": 2, "digivolve_levels": 1}')
    assert port_supports(tmp_path)


def test_export_writes_file_with_warning_and_keeps_mod_files(tmp_path):
    port = tmp_path / 'port'
    port.mkdir()
    (port / 'dw2.exe').write_bytes(b'x')
    session, entries, _ = open_session(tmp_path)
    NameRepository(session, entries).rename(131, 'Foxmon')
    report = check(session, session.pak, port, {131: 15})
    assert report['ok'] and any('digivolve_levels.json' in w for w in report['warnings'])
    result = export_checked(session, session.pak, port, levels={131: 15})
    assert result['digivolve_levels'] == 1
    assert loads((port / 'Mods' / FILENAME).read_text(encoding='utf-8')) == {131: 15}
    assert sorted(p.name for p in (port / 'Mods' / 'files').iterdir())       # normal files still written
    report = check(session, session.pak, port)                                # no levels: no warning
    assert not any(FILENAME in w for w in report['warnings'])


def test_api_levels_undo_and_project(tmp_path):
    import android_api as api
    session, entries, pak = open_session(tmp_path)
    api.configure(str(tmp_path / 'store'), '')
    api.open_image(str(pak))
    r = api.call('digivolve_level_set', json.dumps([131, 15]))
    assert json.loads(r)['ok'] and api.S.digivolve_levels == {131: 15}
    assert 'Mega bleibt gesperrt' in api.digivolve_levels_info()['note']
    api.call('undo', '[]')
    assert api.S.digivolve_levels == {}
    api.call('redo', '[]')
    assert api.S.digivolve_levels == {131: 15}
    api.evolution_line([{'id': 84, 'rows': [{'min_dp': 0, 'target': 131}]}])
    saved = api.save_project('levels')
    api.open_image(str(pak))
    assert api.S.digivolve_levels == {}
    api.load_project(saved['path'])
    assert api.S.digivolve_levels == {131: 15}
    assert FORMAT == 1
