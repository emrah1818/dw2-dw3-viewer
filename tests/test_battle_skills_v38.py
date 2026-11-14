"""Real table layouts, byte-local writes, composition, RAW ECC and Qt actions."""
import csv
import struct
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QMessageBox
from PyQt6.QtTest import QTest
from dw2studio.core.battle_skills import (SkillTable, BaseTable, EnemyTable,
    AttackRepository, AttackPlan, FILE_INDEX, discover_tables)
from dw2studio.core.digimon_names import encode_name
from dw2studio.core.edit_session import EditSession
from dw2studio.core.disc import Entry
from dw2studio.core.catalog import DigimonCandidate
from dw2studio.core.psx_patch import validate_form1_ecc
from test_native_rom_bridge import sector


def tables_fixture():
    names = {1: 'Basic', 31: 'Pepper Breath', 36: 'Nova Blast', 48: 'Giga Blaster',
             88: 'Toy Flame', 90: 'Hail Storm', 96: 'SubZero Ice Punch',
             180: 'Hyper Flashing', 200: 'AntiDote', 220: 'Assist Test', 245: 'Counter Test'}
    pool = bytearray(b'\0'*4)
    pointers = {}
    for identifier, text in names.items():
        pointers[identifier] = len(pool)
        pool += encode_name(text) if len(text) <= 13 else bytes(encode_name(text[:13])+encode_name(text[13:]))
        pool += b'\xff'
    desc = len(pool)
    pool += encode_name('Battle skill')+b'\xfe\x41\xff'
    pool += bytes((-len(pool)) % 4)
    start = len(pool)
    waza = pool+bytearray(68*(len(names)+1))
    struct.pack_into('<I', waza, 0, start)
    for row, (identifier, text) in enumerate(names.items()):
        offset = start+68*row
        waza[offset:offset+68] = bytes([0xA5])*68  # opaque bytes must survive.
        struct.pack_into('<I', waza, offset, identifier | ((row % 4) << 18) | (6 << 20) | (2 << 24) | (3 << 28))
        waza[offset+4] = 12
        struct.pack_into('<h', waza, offset+8, 40)
        struct.pack_into('<II', waza, offset+0x24, pointers[identifier], desc)
    base = bytearray(18*5)
    for row, (identifier, skill) in enumerate([(3, 31), (5, 36), (12, 48), (23, 96)]):
        offset = row*18
        base[offset:offset+18] = bytes([0xAB])*18
        struct.pack_into('<hB', base, offset, identifier, skill)
    enemy = bytearray(100*4)
    for group, specs in enumerate([[(5, (36, 180, 0))], [(23, (96, 0, 0)), (3, (31, 0, 0))], [(23, (90, 1, 0))]], 1):
        offset = (group-1)*100
        enemy[offset] = group
        enemy[offset+1:offset+8] = bytes(range(1, 8))
        for slot, (identifier, skills) in enumerate(specs):
            row = offset+8+slot*30
            enemy[row:row+30] = bytes([0x31])*30
            struct.pack_into('<h', enemy, row, identifier)
            enemy[row+10] = 7+group
            enemy[row+15:row+18] = bytes(skills)
            rules = ((1, 2, 0), (0, 1, 7), (0, 4, 0), (0, 0, 0)) if skills[1] else ((0, 1, 7), (0, 4, 0), (0, 0, 0), (0, 0, 0))
            enemy[row+18:row+30] = bytes(v for rule in rules for v in rule)
    return {'WAZADATA.BIN': bytes(waza), 'DIGIMNDT.BIN': bytes(base), 'ENEMYSET.BIN': bytes(enemy)}


def image_fixture(tmp_path, raw=False, private=False):
    tables = tables_fixture()
    count = 540 if private else 40
    payloads = [bytearray(2048) for _ in range(count)]
    entries = []
    for index, (name, data) in enumerate(tables.items()):
        lba = 500+index if private else 6+index
        payloads[lba][:len(data)] = data
        entries.append(Entry('AAA/4.AAA/DATAFILE/'+name, lba, len(data), False))
    if private:
        exe = bytearray(651264)
        exe[:8] = b'PS-X EXE'
        for entry in entries:
            index = FILE_INDEX[entry.path.split('/')[-1]]
            struct.pack_into('<I', exe, 0x33F94+index*4, entry.lba)
            struct.pack_into('<H', exe, 0x37900+index*2, 1)
        for index in range((len(exe)+2047)//2048):
            block = exe[index*2048:(index+1)*2048]
            payloads[24+index][:len(block)] = block
        entries = [Entry('SLUS_011.93', 24, len(exe), False)]
    image = tmp_path/('game.bin' if raw else 'game.iso')
    image.write_bytes(b''.join(sector(i, bytes(p)) for i, p in enumerate(payloads)) if raw else b''.join(payloads))
    return EditSession(image, 2352 if raw else 2048), entries


def swap_plan(repo, target=23):
    skills, base, enemies = repo.tables()
    donor = enemies.for_digimon(5)[0]
    changes = {r.key: (donor.skills, donor.rules) for r in enemies.for_digimon(target)}
    return AttackPlan(target, base.records[5][1], changes, {36: {'mp': 17, 'power': 87}})


def test_all_table_fields_and_opaque_bytes():
    tables = tables_fixture()
    skills = SkillTable(tables['WAZADATA.BIN'])
    assert skills.records[31].name == 'Pepper Breath'
    assert skills.records[48].name == 'Giga Blaster'
    assert {r.category for r in skills.records.values()} == {0, 1, 2, 3}
    r = skills.records[36]
    assert (r.mp, r.power, r.target, r.specialty, r.rank) == (12, 40, 6, 2, 3)
    changed = skills.changed({36: {'mp': 13, 'power': 84, 'category': 3, 'target': 9, 'specialty': 4, 'rank': 15, 'cast': 2}})
    new = SkillTable(changed).records[36]
    assert (new.mp, new.power, new.category, new.target, new.specialty, new.rank, new.cast) == (13, 84, 3, 9, 4, 15, 2)
    allowed = {r.offset+2, r.offset+3, r.offset+4, r.offset+8, r.offset+9}
    assert all(a == b or i in allowed for i, (a, b) in enumerate(zip(skills.data, changed)))
    assert changed[r.offset+5:r.offset+8] == b'\xa5'*3
    base = BaseTable(tables['DIGIMNDT.BIN'])
    changed = base.changed(23, 36)
    assert [i for i, (a, b) in enumerate(zip(base.data, changed)) if a != b] == [base.records[23][0]+2]


@pytest.mark.parametrize('raw', [False, True])
def test_swap_stage_two_species_project_export_reopen_and_raw_ecc(tmp_path, raw):
    session, entries = image_fixture(tmp_path, raw)
    original = session.source.read_bytes()
    repo = AttackRepository(session, entries)
    assert repo.apply(swap_plan(repo)) == 3
    repo.apply(AttackPlan(3, 88, {}, {31: {'mp': 8}}))
    assert session.source.read_bytes() == original
    assert repo.tables()[1].records[23][1] == 36
    assert repo.tables()[1].records[3][1] == 88
    project = tmp_path/'attacks.dw2mod'
    session.export_project(project)
    reopened = EditSession(session.source, session.sector_size)
    reopened.import_project(project, entries)
    output, backup = reopened.save(tmp_path/('new.bin' if raw else 'new.iso'))
    assert backup is None and output.stat().st_size == len(original)
    after = EditSession(output, session.sector_size)
    new_repo = AttackRepository(after, entries)
    skills, base, enemies = new_repo.tables()
    assert skills.records[36].power == 87 and skills.records[36].mp == 17
    assert skills.records[31].mp == 8
    assert base.records[23][1] == 36 and base.records[3][1] == 88
    before_enemies = EnemyTable(tables_fixture()['ENEMYSET.BIN'])
    donor = enemies.for_digimon(5)[0]
    for row in enemies.for_digimon(23):
        assert (row.skills, row.rules) == (donor.skills, donor.rules)
        old = before_enemies.records[row.key]
        assert enemies.data[row.offset:row.offset+15] == before_enemies.data[old.offset:old.offset+15]
    assert session.source.read_bytes() == original
    if raw:
        stream = output.read_bytes()
        assert all(validate_form1_ecc(stream[i:i+2352]) for i in range(0, len(stream), 2352))


def test_invalid_ai_empty_slots_and_foreign_rows_roll_back(tmp_path, monkeypatch):
    session, entries = image_fixture(tmp_path)
    repo = AttackRepository(session, entries)
    row = repo.tables()[2].for_digimon(23)[0]
    invalid = [AttackPlan(23, 256, {}, {}), AttackPlan(23, 36, {(2, 1): ((31, 0, 0), row.rules)}, {}),
               AttackPlan(23, 36, {row.key: ((36, 0, 0), ((0, 2, 7), (0, 0, 0), (0, 0, 0), (0, 0, 0)))}, {}),
               AttackPlan(23, 36, {}, {36: {'mp': 256}})]
    for plan in invalid:
        with pytest.raises(ValueError):
            repo.apply(plan)
        assert not session.edits
    stage = session.stage
    def failing_stage(entry, *args, **kwargs):
        if entry.path.endswith('WAZADATA.BIN'):
            raise ValueError('write failure')
        return stage(entry, *args, **kwargs)
    monkeypatch.setattr(session, 'stage', failing_stage)
    with pytest.raises(ValueError, match='write failure'):
        repo.apply(swap_plan(repo))
    assert not session.edits


def test_private_file_index_and_duplicate_allocation_checks(tmp_path):
    session, entries = image_fixture(tmp_path, private=True)
    repo = AttackRepository(session, entries)
    assert len(entries) == 4
    assert repo.tables()[0].records[36].name == 'Nova Blast'
    repo.apply(swap_plan(repo))
    assert all(len(e.original) == len(e.replacement) == 2048 for e in session.edits.values())
    bad = entries+[Entry('OTHER/WAZADATA.BIN', 510, 2048, False)]
    with pytest.raises(ValueError, match='mehrfach'):
        AttackRepository(session, bad)
    with pytest.raises(ValueError, match='fehlen'):
        discover_tables(session, [])


def test_corrupt_record_tables_and_csv_catalogue(tmp_path):
    tables = tables_fixture()
    bad = bytearray(tables['WAZADATA.BIN'])
    struct.pack_into('<I', bad, 0, len(bad)+4)
    with pytest.raises(ValueError):
        SkillTable(bad)
    bad = bytearray(tables['WAZADATA.BIN'])
    row = next(iter(SkillTable(bad).records.values()))
    struct.pack_into('<I', bad, row.offset+0x24, len(bad)+4)
    with pytest.raises(ValueError):
        SkillTable(bad)
    for filename, parser, stride in [('DIGIMNDT.BIN', BaseTable, 18), ('ENEMYSET.BIN', EnemyTable, 100)]:
        with pytest.raises(ValueError, match='Endeintrag'):
            parser(tables[filename][:-stride])
    session, entries = image_fixture(tmp_path)
    repo = AttackRepository(session, entries)
    path = tmp_path/'attacks.csv'
    repo.export_csv(path, {36: {'mp': 99}})
    with path.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f, delimiter=';'))
    assert len(rows) == len(SkillTable(tables['WAZADATA.BIN']).records)
    assert next(r for r in rows if r['Name'] == 'Nova Blast')['MP'] == '99'
    assert not session.edits


def test_attack_tables_compose_with_larger_native_model_and_animation_relocation(tmp_path):
    from test_native_relocation_v37 import image_fixture as model_image, transfer
    from dw2studio.core.digimon_transfer import plan_transfer, apply_plan
    from dw2studio.core.dw2_file_index import US
    from dw2studio.core.disc import Disc
    session, entries, targets, files, _ = model_image(tmp_path)
    data = bytearray(session.source.read_bytes())
    for index, (name, table) in enumerate(tables_fixture().items()):
        lba = 505+index
        data[lba*2048:lba*2048+len(table)] = table
        struct.pack_into('<I', data, 24*2048+US[1]+FILE_INDEX[name]*4, lba)
        struct.pack_into('<H', data, 24*2048+US[2]+FILE_INDEX[name]*2, 1)
        entries.append(Entry('AAA/'+name, lba, len(table), False))
    session.source.write_bytes(data)
    session = EditSession(session.source, 2048)
    apply_plan(plan_transfer(transfer(files), targets, session), session)
    repo = AttackRepository(session, entries)
    repo.apply(swap_plan(repo))
    assert len(session.edits) == 5
    output, _ = session.save(tmp_path/'all_edits.iso')
    after = EditSession(output, 2048)
    assert AttackRepository(after, entries).tables()[1].records[23][1] == 36
    disc = Disc(output)
    try:
        for old in targets:
            new = next(e for e in disc.entries if e.path == old.path)
            assert new.lba >= 520
            assert disc.read(new.lba, new.size) == session.current(old)
    finally:
        disc.close()
    assert session.source.read_bytes() == data


def dialog_fixture(qapp, tmp_path):
    from dw2studio.gui.attack_dialog import AttackDialog
    session, entries = image_fixture(tmp_path)
    repo = AttackRepository(session, entries)
    catalog = [DigimonCandidate(3, 'AGUM', 'Agumon'), DigimonCandidate(5, 'GREY', 'Greymon'), DigimonCandidate(23, 'YUKI', 'Frigimon')]
    return AttackDialog(23, 'Frigimon', repo, catalog), session, entries


def test_qt_default_donor_all_encounters_and_global_edits_are_staged_only(qapp, tmp_path):
    dialog, session, entries = dialog_fixture(qapp, tmp_path)
    assert dialog.default_combo.currentData() == 96
    assert dialog.encounter_list.rowCount() == 2
    save = dialog.buttons.button(QDialogButtonBox.StandardButton.Save)
    assert not save.isEnabled()
    dialog.donor_combo.setCurrentIndex(dialog.donor_combo.findData(5))
    dialog.copy_donor()
    assert dialog.default_combo.currentData() == 36 and save.isEnabled()
    assert all(v[0] == (36, 180, 0) for v in dialog.drafts.values())
    row = next(i for i in range(dialog.catalogue.rowCount()) if dialog.catalogue.item(i, 0).data(Qt.ItemDataRole.UserRole) == 36)
    dialog.catalogue.selectRow(row)
    dialog.tech_fields['mp'].setValue(23)
    dialog.tech_fields['power'].setValue(90)
    assert not session.edits
    dialog.accept()
    assert dialog.result() == QDialog.DialogCode.Accepted
    dialog.repository.apply(dialog.plan())
    assert len(session.edits) == 3
    skills, base, enemies = dialog.repository.tables()
    assert skills.records[36].mp == 23 and skills.records[36].power == 90
    assert all(r.skills == (36, 180, 0) for r in enemies.for_digimon(23))
    dialog.close()


def test_qt_individual_encounter_extra_slot_ai_validation_and_cancel(qapp, tmp_path):
    dialog, session, _ = dialog_fixture(qapp, tmp_path)
    row = dialog.rows[0]
    dialog.slot_combos[1].setCurrentIndex(dialog.slot_combos[1].findData(200))
    assert dialog.drafts[row.key][0] == (96, 200, 0)
    assert '2' in dialog.ai_notice.text()
    # Change the first rule to a 50% use of slot2, keep the fallback attack1 rule.
    dialog.rule_controls[0][0].setValue(1)
    dialog.rule_controls[0][1].setCurrentIndex(2)
    dialog.rule_controls[1][1].setCurrentIndex(1)
    assert dialog.buttons.button(QDialogButtonBox.StandardButton.Save).isEnabled()
    assert len(dialog.plan().encounters) == 1
    dialog.slot_combos[1].setCurrentIndex(dialog.slot_combos[1].findData(0))
    assert not dialog.buttons.button(QDialogButtonBox.StandardButton.Save).isEnabled()
    assert 'leeren' in dialog.validation.text()
    dialog.slot_combos[1].setEditText('free form unknown')
    assert not dialog.buttons.button(QDialogButtonBox.StandardButton.Save).isEnabled()
    dialog.reject()
    assert not session.edits
    dialog.close()


def test_catalogue_search_moves_selection_and_never_edits_hidden_technique(qapp, tmp_path):
    dialog, session, _ = dialog_fixture(qapp, tmp_path)
    dialog.search.setText('nova')
    assert dialog.technique_id() == 36
    dialog.tech_fields['mp'].setValue(15)
    assert set(dialog.plan().techniques) == {36}
    dialog.search.setText('does not exist')
    assert dialog.technique_id() is None
    assert not dialog.tech_fields['mp'].isEnabled()
    dialog.search.clear()
    assert dialog.technique_id() == 1 and dialog.tech_fields['mp'].isEnabled()
    dialog.reject()
    assert not session.edits
    dialog.close()


def test_qt_restore_one_species_preserves_other_species_and_global_technique(qapp, tmp_path):
    dialog, session, entries = dialog_fixture(qapp, tmp_path)
    repo = dialog.repository
    repo.apply(swap_plan(repo))
    repo.apply(AttackPlan(3, 88, {}, {31: {'mp': 99}}))
    dialog.close()
    from dw2studio.gui.attack_dialog import AttackDialog
    dialog = AttackDialog(23, 'Frigimon', repo, [])
    dialog.restore_species()
    repo.apply(dialog.plan())
    skills, base, enemies = repo.tables()
    assert base.records[23][1] == 96 and base.records[3][1] == 88
    assert enemies.data == tables_fixture()['ENEMYSET.BIN']
    assert skills.records[31].mp == 99
    assert (repo.entries['ENEMYSET.BIN'].path, repo.entries['ENEMYSET.BIN'].lba) not in session.edits
    row = next(i for i in range(dialog.catalogue.rowCount()) if dialog.catalogue.item(i, 0).data(Qt.ItemDataRole.UserRole) == 36)
    dialog.catalogue.selectRow(row)
    dialog.restore_technique()
    repo.apply(dialog.plan())
    assert repo.tables()[0].records[36].mp == 12 and repo.tables()[0].records[31].mp == 99
    dialog.close()


def setup_window(window, tmp_path, private=False):
    session, entries = image_fixture(tmp_path, private=private)
    window.image = str(session.source)
    window.image_path = session.source
    window.index_key = 'attacks'
    window.session = session
    window.entries = entries
    window.catalog = [DigimonCandidate(5, 'GREY', 'Greymon'), DigimonCandidate(23, 'YUKI', 'Frigimon')]
    window.refresh_list()
    window.digimon.setCurrentRow(1)
    window.update_actions()
    return session, entries


@pytest.mark.parametrize('private', [False, True])
def test_main_button_before_model_load_and_project_reload(window, qapp, tmp_path, monkeypatch, private):
    from dw2studio.gui.attack_dialog import AttackDialog
    session, entries = setup_window(window, tmp_path, private)
    assert window.project_model is None and window.attack_button.isEnabled()
    assert 'SubZero Ice Punch' in window.attack_summary.text()
    seen = []
    def exec_dialog(dialog):
        seen.append(dialog)
        dialog.donor_combo.setCurrentIndex(dialog.donor_combo.findData(5))
        dialog.copy_donor()
        dialog.accept()
        return dialog.result()
    monkeypatch.setattr(AttackDialog, 'exec', exec_dialog)
    monkeypatch.setattr(window, 'load_digimon', lambda: pytest.fail('Attack edits should not load geometry'))
    QTest.mouseClick(window.attack_button, Qt.MouseButton.LeftButton)
    assert seen and not window.test_errors and len(session.edits) == 2
    assert 'Nova Blast' in window.attack_summary.text()
    assert window.pending.count() == 2
    project = tmp_path/'attacks.dw2mod'
    session.export_project(project)
    window.session = EditSession(session.source, session.sector_size)
    if private:
        window.entries = [e for e in window.entries if e.path == 'SLUS_011.93']
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *a, **k: (str(project), ''))
    monkeypatch.setattr(window, 'refresh_names', lambda: None)
    monkeypatch.setattr(window, 'load_digimon', lambda: None)
    window.load_project()
    assert not window.test_errors and window.get_attack_repository().tables()[1].records[23][1] == 36
    window.pending.setCurrentRow(0)
    monkeypatch.setattr(window, 'ask', lambda *a: QMessageBox.StandardButton.No)
    window.discard_selected()
    assert len(window.session.edits) == 2
    monkeypatch.setattr(window, 'ask', lambda *a: QMessageBox.StandardButton.Yes)
    window.discard_selected()
    assert len(window.session.edits) == 1


def test_main_selection_summary_is_cached_and_empty_search_clears_it(window, tmp_path, monkeypatch):
    setup_window(window, tmp_path)
    repo = window.get_attack_repository()
    monkeypatch.setattr(repo, 'tables', lambda: pytest.fail('Arrow navigation must reuse attack-name cache'))
    window.digimon.setCurrentRow(0)
    assert 'Nova Blast' in window.attack_summary.text()
    window.digimon.setCurrentRow(1)
    assert 'SubZero Ice Punch' in window.attack_summary.text()
    window.search.setText('missing species')
    assert not window.attack_button.isEnabled() and 'wählen' in window.attack_summary.text()
