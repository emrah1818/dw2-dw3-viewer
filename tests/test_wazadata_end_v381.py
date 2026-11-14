"""Regression: logical ISO EOF differs from the sector-padded native allocation.

DW2-TT documentation e6.PNG/e9.PNG: table 0x20AC, last row 0x6468,
68-byte stride, logical EOF 0x64AC, allocation 13*2048. Constructed payloads
with these boundaries contain no copyrighted native technique data.
"""
import struct
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog
from PyQt6.QtTest import QTest
from dw2studio.core.battle_skills import SkillTable, AttackRepository, AttackPlan
from dw2studio.core.disc import Entry
from dw2studio.core.edit_session import EditSession
from dw2studio.core.digimon_names import encode_name
from dw2studio.core.catalog import DigimonCandidate
from dw2studio.core.psx_patch import validate_form1_ecc
from test_battle_skills_v38 import tables_fixture, swap_plan
from test_native_rom_bridge import sector


def documented_layout():
    start = 0x20AC
    ids = list(range(1, 256))+[0x12D]
    data = bytearray(start+68*len(ids))
    struct.pack_into('<I', data, 0, start)
    pool = 4
    pointers = {}
    for name in ['Tech', 'Pepper Breath', 'Nova Blast', 'Giga Blaster', 'SubZero', 'Battle']:
        pointers[name] = pool
        raw = encode_name(name)+b'\xff'
        data[pool:pool+len(raw)] = raw
        pool += len(raw)
    labels = {31: 'Pepper Breath', 36: 'Nova Blast', 48: 'Giga Blaster', 96: 'SubZero'}
    for index, identifier in enumerate(ids):
        offset = start+index*68
        data[offset:offset+68] = b'\xA5'*68
        struct.pack_into('<I', data, offset, identifier | ((index % 4) << 18))
        data[offset+4] = 7
        struct.pack_into('<h', data, offset+8, 30)
        struct.pack_into('<II', data, offset+0x24, pointers[labels.get(identifier, 'Tech')], pointers['Battle'])
    assert len(data) == 0x64AC and start+68*255 == 0x6468
    return bytes(data)


@pytest.mark.parametrize('tail', [b'', b'\0\0', b'\0'*4, b'\0'*67, b'\0'*68, b'\0'*852])
def test_complete_logical_eof_and_short_stop_ids_are_supported(tail):
    original = documented_layout()+tail
    table = SkillTable(original)
    assert len(table.records) == 256
    assert table.records[0x12D].offset == 0x6468
    assert table.end_offset == 0x64AC
    assert table.end_kind == ('zero_id' if tail else 'file_end')
    assert table.records[31].name == 'Pepper Breath'
    changed = table.changed({36: {'mp': 19, 'power': 87}})
    assert len(changed) == len(original)
    assert changed[0x64AC:] == tail
    assert SkillTable(changed).records[36].mp == 19
    allowed = {table.records[36].offset+4, table.records[36].offset+8, table.records[36].offset+9}
    assert all(a == b or i in allowed for i, (a, b) in enumerate(zip(original, changed)))


@pytest.mark.parametrize('missing', [1, 2, 3, 12, 30, 66, 67])
def test_nonzero_incomplete_final_record_is_rejected(missing):
    with pytest.raises(ValueError, match='unvollständig|abgeschnitten'):
        SkillTable(documented_layout()[:-missing])


@pytest.mark.parametrize('tail', [b'\0', b'\x01', b'\x01\0', b'\xFF\x7F'+b'\0'*20])
def test_tail_is_never_silently_dropped_or_replaced_with_a_stop(tail):
    with pytest.raises(ValueError, match='unvollständig|abgeschnitten'):
        SkillTable(documented_layout()+tail)


def test_duplicate_ids_and_bad_text_pointers_still_fail_at_exact_eof():
    data = bytearray(documented_layout())
    struct.pack_into('<h', data, 0x6468, 36)
    with pytest.raises(ValueError, match='doppelte'):
        SkillTable(data)
    data = bytearray(documented_layout())
    struct.pack_into('<I', data, 0x6468+0x24, len(data)+4)
    with pytest.raises(ValueError, match='Textzeiger'):
        SkillTable(data)


def image_fixture(tmp_path, raw=False, private=False):
    tables = tables_fixture()
    tables['WAZADATA.BIN'] = documented_layout()
    total = 540 if private else 60
    payloads = [bytearray(2048) for _ in range(total)]
    entries = []
    for name, lba in [('WAZADATA.BIN', 500 if private else 6),
                      ('DIGIMNDT.BIN', 520 if private else 30),
                      ('ENEMYSET.BIN', 521 if private else 31)]:
        data = tables[name]
        for i in range((len(data)+2047)//2048):
            chunk = data[i*2048:(i+1)*2048]
            payloads[lba+i][:len(chunk)] = chunk
        entries.append(Entry('AAA/4.AAA/DATAFILE/'+name, lba, len(data), False))
    if private:
        from dw2studio.core.battle_skills import FILE_INDEX
        from dw2studio.core.dw2_file_index import US
        exe = bytearray(651264)
        exe[:8] = b'PS-X EXE'
        for entry in entries:
            index = FILE_INDEX[entry.path.split('/')[-1]]
            struct.pack_into('<I', exe, US[1]+index*4, entry.lba)
            struct.pack_into('<H', exe, US[2]+index*2, (entry.size+2047)//2048)
        for i in range((len(exe)+2047)//2048):
            chunk = exe[i*2048:(i+1)*2048]
            payloads[24+i][:len(chunk)] = chunk
        entries = [Entry('SLUS_011.93', 24, len(exe), False)]
    path = tmp_path/('game.bin' if raw else 'game.iso')
    path.write_bytes(b''.join(sector(i, bytes(p)) for i, p in enumerate(payloads)) if raw else b''.join(payloads))
    return EditSession(path, 2352 if raw else 2048), entries


@pytest.mark.parametrize('raw', [False, True])
@pytest.mark.parametrize('private', [False, True])
def test_documented_size_direct_and_private_tables_edit_project_export_and_reopen(tmp_path, raw, private):
    session, entries = image_fixture(tmp_path, raw, private)
    original = session.source.read_bytes()
    repo = AttackRepository(session, entries)
    table = repo.tables()[0]
    assert len(table.records) == 256
    assert table.end_kind == ('zero_id' if private else 'file_end')
    repo.apply(swap_plan(repo))
    project = tmp_path/'hotfix.dw2mod'
    session.export_project(project)
    reopened = EditSession(session.source, session.sector_size)
    reopened.import_project(project, entries)
    output, _ = reopened.save(tmp_path/('out.bin' if raw else 'out.iso'))
    after = EditSession(output, session.sector_size)
    skills, base, enemies = AttackRepository(after, entries).tables()
    assert skills.records[36].mp == 17 and skills.records[36].power == 87
    assert base.records[23][1] == 36
    assert all(r.skills[:2] == (36, 180) for r in enemies.for_digimon(23))
    assert output.stat().st_size == len(original) and session.source.read_bytes() == original
    if raw:
        data = output.read_bytes()
        assert all(validate_form1_ecc(data[i:i+2352]) for i in range(0, len(data), 2352))


def test_attack_button_opens_complete_catalogue_for_logical_eof(window, tmp_path, monkeypatch):
    from dw2studio.gui.attack_dialog import AttackDialog
    session, entries = image_fixture(tmp_path)
    window.image = str(session.source)
    window.image_path = session.source
    window.index_key = 'waza_eof'
    window.session = session
    window.entries = entries
    window.catalog = [DigimonCandidate(3, 'AGUM', 'Agumon'), DigimonCandidate(5, 'GREY', 'Greymon')]
    window.refresh_list()
    window.update_actions()
    assert window.current.id == 3 and 'Pepper Breath' in window.attack_summary.text()
    seen = []
    def edit(dialog):
        seen.append(dialog)
        assert dialog.catalogue.rowCount() == 256
        assert dialog.default_combo.currentData() == 31
        dialog.default_combo.setCurrentIndex(dialog.default_combo.findData(36))
        dialog.accept()
        return dialog.result()
    monkeypatch.setattr(AttackDialog, 'exec', edit)
    QTest.mouseClick(window.attack_button, Qt.MouseButton.LeftButton)
    assert seen and not window.test_errors
    assert window.get_attack_repository().tables()[1].records[3][1] == 36
    assert 'Nova Blast' in window.attack_summary.text()
