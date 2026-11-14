"""0.17b editors on self-made data: domains, enemy groups, individual techniques, camera, lines."""
import struct
import pytest

from fixtures017 import (open_session, wazadata, enemyset, dungeon, domains_archive, digimndt, modeldt,
                         WAZADATA, DIGIMNDT, ENEMYSET, MODELDT0, DOMAINS, DUNGEON)
from dw2studio.core.domains import DomainRepository, DomainTable, DungeonFile, EnemyGroups
from dw2studio.core.battle_skills import SkillTable, BaseTable
from dw2studio.core.techniques import TechniqueRepository
from dw2studio.core.battle_camera import CameraRepository, bucket, suggest, FIELD_MAX, measure
from dw2studio.core.evolution import EvolutionRepository, change_line


@pytest.fixture
def opened(tmp_path):
    return open_session(tmp_path)


# ---------------------------------------------------------------- Domains und Gegnergruppen
def test_domain_table_floors_and_groups_parse():
    assert DomainTable(domains_archive((0xCE1, 0xCE2))).rows == [0xCE1, 0xCE2]
    floors = DungeonFile(dungeon()).floors
    assert [f['name'] for f in floors] == ['Test Domain1F', 'Test Domain2F'] and floors[0]['sets'] == [0, 31, 31, 32, 0]
    g = EnemyGroups(enemyset()).group(32)
    assert g['header'] == {'map_digimon': 84, 'ai': 6, 'pace': 1, 'liked_gift': 3, 'dungeon_bgm': 1, 'boss': 0, 'points_per_level': 10}
    assert [m['digimon'] for m in g['members']] == [84, 131, 0] and g['members'][1]['skills'] == [1, 2, 0]


def test_every_group_writes_back_byte_identical():
    groups = EnemyGroups(enemyset())
    for sid in groups.groups:
        info = groups.group(sid)
        assert groups.changed(sid, info['header'], info['members']) == groups.data


def test_group_edit_changes_only_named_fields():
    groups = EnemyGroups(enemyset())
    out = EnemyGroups(groups.changed(32, {'boss': 1}, [None, {'level': 9, 'hp': 99}]))
    g = out.group(32)
    assert g['header']['boss'] == 1 and g['header']['ai'] == 6
    assert g['members'][1]['level'] == 9 and g['members'][1]['hp'] == 99 and g['members'][0]['level'] == 4
    row = out.groups[32] + 8 + 30
    assert out.data[row + 6:row + 10] == b'\x11\x22\x33\x44'          # unknown bytes kept
    changed = [i for i, (a, b) in enumerate(zip(groups.data, out.data)) if a != b]
    assert all(i in range(groups.groups[32], groups.groups[32] + 100) for i in changed)


@pytest.mark.parametrize('header,members,match', [
    ({'ai': 16}, None, '0–15'),
    ({'nope': 1}, None, 'Unbekanntes'),
    (None, [{'level': 100}], 'level'),
    (None, [{'skills': [0, 0, 0], 'rules': [[0, 1, 7], [0, 0, 0], [0, 0, 0], [0, 0, 0]]}], 'leeren Technikplatz'),
    (None, [{'hp': 0}], 'HP und Level'),
    (None, [{'skills': [9, 0, 0]}], 'unbekannte Technik'),
])
def test_group_edit_rejects_bad_values(header, members, match):
    with pytest.raises(ValueError, match=match):
        EnemyGroups(enemyset()).changed(32, header, members, skill_ids={1, 2, 4})


@pytest.mark.parametrize('data,match', [(b'', 'Endeintrag'), (enemyset()[:150], 'abgeschnitten'), (bytes(100), 'keine Gegnergruppen')])
def test_damaged_enemyset_is_refused(data, match):
    with pytest.raises(ValueError, match=match):
        EnemyGroups(data)


def test_damaged_dungeon_and_domain_table_are_refused():
    with pytest.raises(ValueError):
        DungeonFile(b'\x10\x00\x00\x00')                               # floor offset without terminator
    bad = bytearray(dungeon()); struct.pack_into('<I', bad, 0, len(bad) + 4)
    with pytest.raises(ValueError, match='außerhalb'):
        DungeonFile(bytes(bad))
    with pytest.raises(ValueError):
        DomainTable(b'\x00' * 8)


def test_clone_keeps_file_length_when_padding_allows():
    data = enemyset() + bytes(400)                     # like the disc: zero padding up to the sector end
    out = EnemyGroups(data).cloned(32, 40)
    assert len(out) == len(data) and EnemyGroups(out).group(40)['members'][0]['digimon'] == 84
    tight = enemyset()                                  # no room: the file grows by one group
    grown = EnemyGroups(tight).cloned(32, 40)
    assert len(grown) == len(tight) + 100 and 40 in EnemyGroups(grown).groups


def test_domain_repository_floor_clone_and_usage(opened):
    session, entries, _ = opened
    repo = DomainRepository(session, entries)
    new = repo.clone_group(32)
    assert new == 1 and repo.groups().group(new)['members'][0]['digimon'] == 84
    assert repo.set_floor(0, 1, [0, new, 32, 0, 0])
    assert repo.overview()[0]['floors'][1]['sets'] == [0, new, 32, 0, 0]
    assert repo.usage(new) == [{'domain': 0, 'name': 'Test Domain1F', 'floor': 1}]
    with pytest.raises(ValueError, match='gibt es nicht'):
        repo.set_floor(0, 0, [0, 77, 0, 0, 0])
    with pytest.raises(ValueError, match='Etage'):
        repo.set_floor(0, 5, [0, 0, 0, 0, 0])


# ---------------------------------------------------------------- Individuelle Techniken
def test_clone_keeps_every_original_byte_and_copies_the_record():
    table = SkillTable(wazadata())
    out = SkillTable(table.cloned(4, 9, 'Fox Fire', 'Blue flames.', {'mp': 9, 'power': 55}))
    for i, rec in table.records.items():
        assert out.data[rec.offset:rec.offset + 68] == table.data[rec.offset:rec.offset + 68]
    new = out.records[9]
    assert (new.name, new.description, new.mp, new.power, new.cast, new.specialty) == ('Fox Fire', 'Blue flames.', 9, 55, 1, 2)
    src = table.records[4]
    assert out.data[new.offset + 0x2C:new.offset + 0x44] == table.data[src.offset + 0x2C:src.offset + 0x44]   # effects
    second = SkillTable(out.cloned(1, 10, 'Ice Pick'))
    assert second.records[9].name == 'Fox Fire' and second.records[10].name == 'Ice Pick'
    assert second.records[10].description == table.records[1].description           # shares the source text


@pytest.mark.parametrize('new_id,name,match', [(4, 'X', 'frei'), (256, 'X', '1–255'), (9, 'Ünicode', 'Zeichensatz'),
                                               (9, 'A' * 18, '17'), (9, ' X', 'Leerzeichen')])
def test_clone_rejects_bad_ids_and_names(new_id, name, match):
    with pytest.raises(ValueError, match=match):
        SkillTable(wazadata()).cloned(1, new_id, name)


def test_individual_technique_changes_only_its_digimon(opened):
    session, entries, _ = opened
    repo = TechniqueRepository(session, entries)
    before = {c['id']: c for c in repo.catalog()}
    r = repo.create(131, 4, 'Fox Fire', values={'mp': 9}, as_default=True, encounters=[(31, 0)])
    skills, base, enemies = repo.tables()
    assert base.records[131][1] == r['id'] and base.records[3][1] == 1             # other Digimon unchanged
    assert r['id'] in enemies.records[(31, 0)].skills and enemies.records[(32, 1)].skills == (1, 2, 0)
    after = {c['id']: c for c in repo.catalog() if c['id'] != r['id']}
    assert after == before                                                 # every existing technique unchanged
    assert repo.usage(r['id'])['digimon'] == [131]
    assert repo.edit(r['id'], {'power': 77}, 'Fox Blaze', digimon=131)
    assert repo.tables()[0].records[r['id']].name == 'Fox Blaze'
    with pytest.raises(ValueError, match='mehrere'):
        repo.edit(1, {'power': 1}, digimon=3)                              # shared by several Digimon
    with pytest.raises(ValueError):
        repo.edit(r['id'], {'power': 1}, digimon=5)                        # not this Digimon's


# ---------------------------------------------------------------- Kamera
def test_camera_bucket_and_limits():
    assert bucket(0x2FF) == 0 and bucket(0x300) == 0 and bucket(0x3FF) == 0 and bucket(0x400) == 1
    assert bucket(FIELD_MAX) == 8 and FIELD_MAX < 0x300 + 9 * 256          # table has nine entries
    assert suggest(1190, 601, (1800, 2500), (1800, 2500)) == (1190, 601)
    high = suggest(1190, 601, (1800, 2500), (9000, 20000))
    assert high[0] == FIELD_MAX
    low = suggest(1190, 601, (1800, 2500), (100, 100))
    assert low[0] >= 0x100 and low[1] >= 0


def test_camera_repository_writes_only_two_fields(opened):
    session, entries, _ = opened
    repo = CameraRepository(session, entries)
    entry = next(e for e in entries if e.path.endswith('MODELDT0.BIN'))
    before = session.current(entry)
    assert repo.set(131, 1920, 900)
    after = session.current(entry)
    assert repo.values(131) == {'field_1E': 1920, 'hit_fx_y': 900, 'bucket': 4}
    assert sum(a != b for a, b in zip(before, after)) <= 4
    with pytest.raises(ValueError, match='9 Stufen'):
        repo.set(131, 0xC00, 900)


def test_camera_measure_on_a_synthetic_model(tmp_path):
    from test_015_native import source
    from dw2studio.core.dw3_native import encode_model, encode_animation
    s = source(tmp_path)
    native, _, _ = encode_model(s, tmp_path)
    anim = encode_animation(s, {0: 0})
    stand, reach = measure(native, anim, [anim])
    assert stand > 0 and reach >= stand


# ---------------------------------------------------------------- Digitationslinien
def test_line_changes_several_species_in_one_edit(opened):
    session, entries, _ = opened
    repo = EvolutionRepository(session, entries)
    assert change_line(repo, [{'id': 84, 'rows': [{'min_dp': 0, 'target': 131}], 'rank': 0},
                              {'id': 131, 'rows': [{'min_dp': 0, 'target': 5}, {'min_dp': 20, 'target': 6}], 'rank': 1}]) == [84, 131]
    assert repo.info(84)['rows'] == [{'min_dp': 0, 'target': 131}] and repo.info(131)['rank'] == 1
    assert len(session.edits) == 1 and 'Digitationslinie' in next(iter(session.edits.values())).label
    data = session.current(repo.entry)
    assert data[BaseTable(data).records[3][0] + 17] == 0xA5                   # unknown byte kept


def test_line_with_one_bad_row_changes_nothing(opened):
    session, entries, _ = opened
    repo = EvolutionRepository(session, entries)
    with pytest.raises(ValueError):
        change_line(repo, [{'id': 84, 'rows': [{'min_dp': 0, 'target': 131}]}, {'id': 131, 'rows': [{'min_dp': 5, 'target': 5}]}])
    assert not session.edits
    with pytest.raises(ValueError, match='einmal'):
        change_line(repo, [{'id': 84, 'rows': []}, {'id': 84, 'rows': []}])
