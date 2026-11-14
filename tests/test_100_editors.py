"""1.0: technique parts and multi-assign, ID budget, evolution validation, mod import conflicts.
Self-made data only (fixtures017)."""
import struct
import pytest

from fixtures017 import open_session, digimndt
from dw2studio.core.battle_skills import SkillTable, BaseTable
from dw2studio.core.techniques import TechniqueRepository, copy_parts, assign, id_budget, PARTS
from dw2studio.core.evolution import EvolutionRepository, change_line, validate, _check
from dw2studio.mod_io import export_checked, import_into, ModConflict, import_conflicts


@pytest.fixture
def opened(tmp_path):
    return open_session(tmp_path)


def _rec(repo, t):
    skills = repo.tables()[0]
    off = skills.records[t].offset
    return skills.data[off:off + 68]


def test_copy_parts_takes_only_the_chosen_bytes(opened):
    session, entries, _ = opened
    repo = TechniqueRepository(session, entries)
    new = repo.create(131, 4, 'Fox Fire', as_default=True)['id']
    # give technique 2 a different sound, effect and status so the copy is visible
    skills = repo.tables()[0]
    data = bytearray(skills.data)
    off2 = skills.records[2].offset
    data[off2 + 5] = 3
    struct.pack_into('<h', data, off2 + 6, 1234)
    struct.pack_into('<6h', data, off2 + 0x2C, 70, 71, 72, 73, 74, 75)
    struct.pack_into('<I', data, off2 + 0x18, 0x40)
    struct.pack_into('<I', data, off2, (struct.unpack_from('<I', data, off2)[0] & ~(3 << 16)) | (2 << 16))
    session.stage(repo.files['WAZADATA.BIN'], bytes(data), 'Testvorbereitung')
    before = _rec(repo, new)
    assert copy_parts(repo, new, 2, ['sound'], digimon=131)
    after = _rec(repo, new)
    assert after[5] == 3 and struct.unpack_from('<h', after, 6)[0] == 1234
    assert after[:5] == before[:5] and after[8:] == before[8:]              # nothing else
    assert copy_parts(repo, new, 2, ['effect', 'status', 'animation'], digimon=131)
    after = _rec(repo, new)
    assert struct.unpack_from('<6h', after, 0x2C) == (70, 71, 72, 73, 74, 75)
    assert struct.unpack_from('<I', after, 0x18)[0] == 0x40
    assert (struct.unpack_from('<I', after, 0)[0] >> 16) & 3 == 2
    assert struct.unpack_from('<h', after, 0)[0] == new                     # id kept
    assert repo.tables()[0].records[new].name == 'Fox Fire'                 # name kept
    assert not copy_parts(repo, new, 2, ['sound'], digimon=131)             # already equal
    assert set(PARTS) == {'sound', 'effect', 'status', 'animation'}


def test_copy_parts_refuses_shared_and_bad_input(opened):
    session, entries, _ = opened
    repo = TechniqueRepository(session, entries)
    with pytest.raises(ValueError, match='mehrere'):
        copy_parts(repo, 1, 2, ['sound'], digimon=3)
    new = repo.create(131, 4, 'Fox Fire', as_default=True)['id']
    with pytest.raises(ValueError, match='Teile'):
        copy_parts(repo, new, 2, ['bogus'], digimon=131)
    with pytest.raises(ValueError, match='dieselbe'):
        copy_parts(repo, new, new, ['sound'], digimon=131)
    with pytest.raises(ValueError, match='fehlt'):
        copy_parts(repo, new, 99, ['sound'], digimon=131)


def test_assign_one_technique_to_several_digimon_in_one_step(opened):
    session, entries, _ = opened
    repo = TechniqueRepository(session, entries)
    assert assign(repo, 4, [3, 84, 3]) == [3, 84]
    base = repo.tables()[1]
    assert base.records[3][1] == 4 and base.records[84][1] == 4 and base.records[5][1] == 2
    assert len(session.edits) == 1
    assert repo.usage(4)['shared']
    with pytest.raises(ValueError, match='DIGIMNDT'):
        assign(repo, 4, [77])
    with pytest.raises(ValueError, match='vorhandene'):
        assign(repo, 99, [3])


def test_id_budget_counts_one_byte_ids(opened):
    session, entries, _ = opened
    repo = TechniqueRepository(session, entries)
    b = id_budget(repo)
    assert b['existing'] == 3 and b['free_count'] == 252 and b['max_id'] == 255
    assert b['unreferenced'] == []                                          # 1, 2, 4 all used
    repo.create(131, 4, 'Fox Fire', as_default=True)
    assert id_budget(repo)['free_count'] == 251


def test_evolution_validation_finds_cycles_missing_and_stage_problems(opened):
    session, entries, _ = opened
    repo = EvolutionRepository(session, entries)
    assert validate(repo)['ok']
    change_line(repo, [{'id': 5, 'rows': [{'min_dp': 0, 'target': 6}]}, {'id': 6, 'rows': [{'min_dp': 0, 'target': 5}]}])
    r = validate(repo)
    assert not r['ok'] and any(e['kind'] == 'cycle' for e in r['errors'])
    assert any(w['kind'] == 'stage' and w['id'] == 6 for w in r['warnings'])
    # a target without DIGIMNDT record, written as raw bytes (the editor refuses it)
    data = bytearray(session.current(repo.entry))
    off = BaseTable(bytes(data)).records[84][0]
    data[off + 13] = 200
    found = _check(bytes(data))
    assert any(e['kind'] == 'missing' and e['target'] == 200 for e in found['errors'])


def test_evolution_validation_reports_original_faults_as_warnings(tmp_path):
    rows = ((3, 1, 0, [(0, 5), (10, 6), (20, 84), (30, 131)]), (5, 2, 1, []), (6, 4, 2, []), (84, 1, 0, []), (131, 2, 0, []))
    data = bytearray(digimndt(rows))
    data[8 + 4] = 40                       # fifth DP bound set: DP 40+ has no target (no safe end)
    session, entries, _ = open_session(tmp_path, {3180: bytes(data)})
    r = validate(EvolutionRepository(session, entries))
    assert r['ok'] and any(w.get('original') for w in r['warnings'])


def test_import_conflict_names_double_technique_ids(tmp_path):
    port = tmp_path / 'port'
    port.mkdir()
    (port / 'dw2.exe').write_bytes(b'x')
    a, ea, _ = open_session(tmp_path / 'a')
    TechniqueRepository(a, ea).create(131, 4, 'Fox Fire', as_default=True)
    export_checked(a, a.pak, port)
    b, eb, _ = open_session(tmp_path / 'b')
    TechniqueRepository(b, eb).create(84, 2, 'Ice Shard', as_default=True)     # same free id, other bytes
    before = dict(b.edits)
    with pytest.raises(ModConflict) as err:
        import_into(b, eb, port)
    assert any(c.get('technique_ids') == [3] for c in err.value.conflicts)
    assert b.edits == before                                                 # nothing replaced
    r = import_into(b, eb, port, force=True)
    assert r['files'] == 2
    assert 'Fox Fire' in [t['name'] for t in TechniqueRepository(b, eb).catalog()]


def test_import_without_own_changes_has_no_conflict(tmp_path):
    port = tmp_path / 'port'
    port.mkdir()
    (port / 'dw2.exe').write_bytes(b'x')
    a, ea, _ = open_session(tmp_path / 'a')
    TechniqueRepository(a, ea).create(131, 4, 'Fox Fire', as_default=True)
    export_checked(a, a.pak, port)
    b, eb, _ = open_session(tmp_path / 'b')
    assert import_conflicts(b, eb, {603: a.current(next(e for e in ea if e.path.endswith('WAZADATA.BIN')))}) == []
    assert import_into(b, eb, port)['files'] == 2
