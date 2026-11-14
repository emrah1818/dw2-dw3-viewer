"""0.17b: mod export with checks and conflicts, read back, compare. Self-made data only."""
import hashlib
import json
import pytest

from fixtures017 import open_session
from dw2studio.core.domains import DomainRepository
from dw2studio.core.techniques import TechniqueRepository
from dw2studio.core.battle_camera import CameraRepository
from dw2studio.core.evolution import EvolutionRepository, change_line
from dw2studio.core.digimon_names import NameRepository
from dw2studio.mod_io import check, export_checked, import_into, read_mod
from dw2studio.port_mod_manage import status


def edit_everything(session, entries):
    NameRepository(session, entries).rename(131, 'Foxmon')
    TechniqueRepository(session, entries).create(131, 4, 'Fox Fire', values={'mp': 9}, as_default=True, encounters=[(31, 0)])
    DomainRepository(session, entries).set_floor(0, 1, [0, 31, 32, 0, 0])
    DomainRepository(session, entries).set_group(32, {'boss': 1}, [None, {'level': 9}])
    CameraRepository(session, entries).set(131, 1500, 700)
    change_line(EvolutionRepository(session, entries), [{'id': 84, 'rows': [{'min_dp': 0, 'target': 131}]}])


def fingerprint(session):
    return sorted(hashlib.sha256(e.replacement).hexdigest() for e in session.edits.values())


@pytest.fixture
def port(tmp_path):
    folder = tmp_path / 'port'
    folder.mkdir()
    (folder / 'dw2.exe').write_bytes(b'placeholder')
    return folder


def test_roundtrip_export_and_read_back_is_identical(tmp_path, port):
    session, entries, pak = open_session(tmp_path)
    edit_everything(session, entries)
    report = check(session, session.pak, port)
    assert report['ok'] and not report['conflicts'] and len(report['files']) == 5
    expected = fingerprint(session)
    export_checked(session, session.pak, port)
    manifest = json.loads((port / 'Mods' / 'dw2studio_mod.json').read_text(encoding='utf-8'))
    assert {row['id'] for row in manifest['files']} == {603, 3180, 3183, 3257, 0xCE1}
    # Port format: Mods/files/<ID as 4 hex digits>.bin (host/pak.c load_mod_dir)
    assert sorted(p.name for p in (port / 'Mods' / 'files').iterdir()) == ['025B.bin', '0C6C.bin', '0C6F.bin', '0CB9.bin', '0CE1.bin']
    fresh, fresh_entries, _ = open_session(tmp_path / 'again')
    result = import_into(fresh, fresh_entries, port)
    assert result['files'] == 5 and fingerprint(fresh) == expected
    # read back through the editors
    assert NameRepository(fresh, fresh_entries).lookup(131)[1].record(131).text == 'Foxmon'
    assert CameraRepository(fresh, fresh_entries).values(131)['field_1E'] == 1500
    assert DomainRepository(fresh, fresh_entries).groups().group(32)['header']['boss'] == 1
    assert EvolutionRepository(fresh, fresh_entries).info(84)['rows'] == [{'min_dp': 0, 'target': 131}]
    assert 'Fox Fire' in [t['name'] for t in TechniqueRepository(fresh, fresh_entries).catalog()]


def test_second_export_is_a_conflict_until_replace(tmp_path, port):
    session, entries, _ = open_session(tmp_path)
    edit_everything(session, entries)
    export_checked(session, session.pak, port)
    report = check(session, session.pak, port)
    assert report['conflicts'] and report['ok']
    with pytest.raises(FileExistsError, match='Konflikt'):
        export_checked(session, session.pak, port)
    result = export_checked(session, session.pak, port, replace=True)
    assert result['replaced'] and len(status(port)['disabled']) == 1
    assert len(status(port)['active']['files']) == 6                        # five files + manifest


def test_check_reports_errors_in_plain_words(tmp_path, port):
    session, entries, _ = open_session(tmp_path)
    assert 'keine Änderungen' in ' '.join(check(session, session.pak, port)['errors'])
    assert 'nicht gefunden' in ' '.join(check(session, session.pak, tmp_path / 'missing')['errors'])
    other = tmp_path / 'other'; other.mkdir()
    TechniqueRepository(session, entries).create(131, 4, 'Fox Fire')
    assert any('dw2.exe' in w for w in check(session, session.pak, other)['warnings'])


@pytest.mark.parametrize('damage,match', [
    (lambda port: (port / 'Mods/files/7777.bin').write_bytes(b'x'), 'gibt es in dw2.pak nicht'),
    (lambda port: (port / 'Mods/files/025B.bin').write_bytes(b''), 'leer'),
    (lambda port: (port / 'Mods/files/025B.bin').write_bytes(bytes(2 * 1024 * 1024 + 1)), '2 MiB'),
])
def test_damaged_mod_files_are_refused(tmp_path, port, damage, match):
    session, entries, _ = open_session(tmp_path)
    edit_everything(session, entries)
    export_checked(session, session.pak, port)
    damage(port)
    fresh, fresh_entries, _ = open_session(tmp_path / 'again')
    with pytest.raises(ValueError, match=match):
        import_into(fresh, fresh_entries, port)
    assert not fresh.edits


def test_mod_for_another_pak_is_refused(tmp_path, port):
    from fixtures017 import wazadata, digimndt, enemyset, modeldt, domains_archive, dungeon
    session, entries, _ = open_session(tmp_path)
    edit_everything(session, entries)
    export_checked(session, session.pak, port)
    files = {603: wazadata(((1, 'Other', 1, 1), (4, 'Flame Ball', 6, 30))), 3180: digimndt(), 3183: enemyset(),
             3257: modeldt(), 0xE20: domains_archive(), 0xCE1: dungeon()}
    other, other_entries, _ = open_session(tmp_path / 'other', files)
    with pytest.raises(ValueError, match='andere dw2.pak'):
        import_into(other, other_entries, port)
    assert not other.edits


def test_shorter_and_longer_files_and_the_api2_check(tmp_path, port):
    session, entries, _ = open_session(tmp_path)
    TechniqueRepository(session, entries).create(131, 4, 'Fox Fire')
    edit = next(iter(session.edits.values()))
    assert len(edit.replacement) == len(edit.original)                      # padded back: no API 2 needed
    assert check(session, session.pak, port)['ok']
    entry = next(e for e in entries if e.path.endswith('ENEMYSET.BIN'))
    session.stage(entry, session.current(entry) + bytes(4096), 'größer')
    report = check(session, session.pak, port)
    assert not report['ok'] and 'Schnittstelle 2' in ' '.join(report['errors'])
    (port / 'dw2_mod_api.json').write_text('{"mod_api": 2}')
    assert check(session, session.pak, port)['ok']


def test_read_mod_without_files_folder(tmp_path, port):
    session, _, _ = open_session(tmp_path)
    with pytest.raises(ValueError, match='Mods'):
        read_mod(port, session.pak)
