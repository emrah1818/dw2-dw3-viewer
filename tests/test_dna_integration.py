"""DNA authoring -> project -> installed mod lifecycle, using synthetic game tables."""
import json
import zipfile

import pytest
from fixtures017 import open_session
import android_api as api
from dw2studio.core.dna_overrides import DnaOverrides, FILENAME
from dw2studio.mod_io import check, export_checked
from dw2studio.port_mod_manage import disable, enable


def setup(tmp_path):
    session, entries, pak = open_session(tmp_path)
    api.configure(str(tmp_path / 'store'), '')
    api.open_image(str(pak))
    port = tmp_path / 'port'
    port.mkdir()
    (port / 'dw2_mod_api.json').write_text('{"mod_api":2,"dna_overrides":1}')
    return port


def call(method, *args):
    reply = json.loads(api.call(method, json.dumps(args)))
    assert reply['ok'], reply
    return reply.get('data')


def test_dna_only_project_undo_install_import_disable(tmp_path):
    port = setup(tmp_path)
    call('dna_set', 84, 131, 131, 3)
    assert api.S.dna_overrides == {(84, 131): (131, 3)}
    call('undo')
    assert not api.S.dna_overrides
    call('redo')
    saved = api.save_project('dna')
    with zipfile.ZipFile(saved['path']) as archive:
        assert DnaOverrides.from_json(archive.read(FILENAME)).resolve(131, 84) == (131, 3)
    api.S.dna_overrides = {}
    call('load_project', saved['path'])
    assert api.S.dna_overrides == {(84, 131): (131, 3)}
    assert api.mod_check(str(port))['ok']
    result = api.mod_export(str(port))
    assert result['dna_overrides'] == 1 and result['count'] == 0
    with pytest.raises(FileExistsError):
        api.mod_export(str(port))
    call('dna_remove', 84, 131)
    call('mod_import', str(port))
    assert api.S.dna_overrides == {(84, 131): (131, 3)}
    moved = disable(port)
    assert FILENAME in moved['moved']
    assert not (port / 'Mods' / FILENAME).exists()
    enable(port)
    assert DnaOverrides.from_json((port / 'Mods' / FILENAME).read_text()).resolve(84, 131) == (131, 3)
    # Replacing with a different rule backs up the original sidecar, without stale rules.
    call('dna_remove', 84, 131)
    call('dna_set', 84, 131, 84, 0)
    api.mod_export_replace(str(port))
    assert DnaOverrides.from_json((port / 'Mods' / FILENAME).read_text()).resolve(84, 131) == (84, 0)


def test_no_capability_refuses_export_before_any_write(tmp_path):
    port = setup(tmp_path)
    (port / 'dw2_mod_api.json').write_text('{"mod_api":2}')
    call('dna_set', 84, 131, 84, 3)
    assert not api.mod_check(str(port))['ok']
    with pytest.raises(ValueError, match='DNA'):
        api.mod_export(str(port))
    assert not (port / 'Mods').exists()


def test_invalid_species_and_rank_conflicts_leave_previous_rule(tmp_path):
    setup(tmp_path)
    call('dna_set', 84, 131, 84, 3)
    before = dict(api.S.dna_overrides)
    reply = json.loads(api.call('dna_set', '[84,131,255,3]'))
    assert not reply['ok'] and api.S.dna_overrides == before
    mod = DnaOverrides()
    mod.add(1, 2, 3, 3)
    with pytest.raises(ValueError, match='Stufe'):
        mod.add(1, 4, 3, 2)
    assert mod.resolve(1, 2) == (3, 3)


def test_malformed_import_is_atomic(tmp_path):
    port = setup(tmp_path)
    call('dna_set', 84, 131, 84, 3)
    api.mod_export(str(port))
    before = dict(api.S.dna_overrides)
    (port / 'Mods' / FILENAME).write_text('{"format":"dw2-dna-overrides","version":2,"rules":[]}')
    with pytest.raises(ValueError):
        api.mod_import(str(port))
    assert api.S.dna_overrides == before


def test_removing_last_rule_can_install_empty_override_file(tmp_path):
    port = setup(tmp_path)
    call('dna_set', 84, 131, 131, 3)
    api.mod_export(str(port))
    call('dna_remove', 84, 131)
    assert api.S.dna_modified and not api.S.dna_overrides
    result = api.mod_export_replace(str(port))
    assert result['dna_overrides'] == 0
    assert DnaOverrides.from_json((port / 'Mods' / FILENAME).read_text()).rules == {}
    project = api.save_project('empty-dna')
    call('discard', 'dna')
    assert not api.S.dna_modified
    call('load_project', project['path'])
    assert api.S.dna_modified and not api.S.dna_overrides


def test_import_dna_conflict_requires_force(tmp_path):
    port = setup(tmp_path)
    call('dna_set', 84, 131, 131, 3)
    api.mod_export(str(port))
    call('dna_set', 84, 131, 84, 0)
    from dw2studio.mod_io import ModConflict
    with pytest.raises(ModConflict):
        api.mod_import(str(port))
    assert api.S.dna_overrides == {(84, 131): (84, 0)}
    call('mod_import_force', str(port))
    assert api.S.dna_overrides == {(84, 131): (131, 3)}


def test_invalid_project_restores_existing_dna(tmp_path):
    setup(tmp_path)
    call('dna_set', 84, 131, 131, 3)
    saved = api.save_project('broken')
    # A different, structurally complete project with an invalid DNA version.
    target = tmp_path / 'invalid.dw2mod'
    with zipfile.ZipFile(saved['path']) as src, zipfile.ZipFile(target, 'w') as dst:
        for name in src.namelist():
            dst.writestr(name, src.read(name) if name != FILENAME else
                         '{"format":"dw2-dna-overrides","version":2,"rules":[]}')
    call('dna_set', 84, 131, 84, 0)
    before = dict(api.S.dna_overrides)
    with pytest.raises(ValueError):
        api.load_project(str(target))
    assert api.S.dna_overrides == before and api.S.dna_modified
