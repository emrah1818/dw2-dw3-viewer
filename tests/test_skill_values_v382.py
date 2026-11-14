"""MP/AP shown at selection time, derived from bytes and current dialog edits."""
import csv
from PyQt6.QtCore import Qt
from dw2studio.core.battle_skills import AttackPlan, power_label, skill_label
from test_battle_skills_v38 import dialog_fixture, setup_window


def select_technique(dialog, identifier):
    row = next(i for i in range(dialog.catalogue.rowCount())
               if dialog.catalogue.item(i, 0).data(Qt.ItemDataRole.UserRole) == identifier)
    dialog.catalogue.selectRow(row)
    return row


def test_reference_values_and_zero_healing_values_are_unambiguous(qapp, tmp_path):
    dialog, session, _ = dialog_fixture(qapp, tmp_path)
    table = dialog.skills
    # MetalKid skill list: Pepper Breath 8 MP / 17.5 AP; Nova Blast 12 / 27.5.
    assert skill_label(table.records[31], {'mp': 8, 'power': 35}) == '1F · Pepper Breath · 8 MP · 17,5 AP'
    assert skill_label(table.records[36], {'mp': 12, 'power': 55}) == '24 · Nova Blast · 12 MP · 27,5 AP'
    assert power_label(1) == '0,5 AP'
    assert power_label(35, decimal_comma=False) == '17.5 AP'
    assert power_label(0) == '— AP'
    assert power_label(-40) == 'Heilwert -40 (nativ)'
    assert not session.edits
    dialog.close()


def test_native_values_are_shown_in_default_slot_table_and_donor_choices(qapp, tmp_path):
    dialog, session, _ = dialog_fixture(qapp, tmp_path)
    assert '12 MP · 20 AP' in dialog.default_combo.currentText()
    assert '12 MP · 20 AP' in dialog.slot_combos[0].currentText()
    assert '12 MP · 20 AP' in dialog.encounter_list.item(0, 3).text()
    dialog.donor_combo.setCurrentIndex(dialog.donor_combo.findData(5))
    assert 'Nova Blast · 12 MP · 20 AP' in dialog.donor_variant.currentText()
    assert not session.edits and not dialog.plan().encounters
    dialog.close()


def test_local_value_edits_refresh_labels_preserve_donor_variant_and_all_assignments(qapp, tmp_path):
    dialog, session, _ = dialog_fixture(qapp, tmp_path)
    dialog.donor_combo.setCurrentIndex(dialog.donor_combo.findData(5))
    dialog.donor_variant.setCurrentIndex(0)  # preserve deliberate default-only choice.
    donor_key = dialog.donor_variant.currentData()
    ids = [c.currentData() for c in dialog.skill_combos]
    row = select_technique(dialog, 96)
    dialog.tech_fields['mp'].setValue(25)
    dialog.tech_fields['power'].setValue(55)
    assert '25 MP · 27,5 AP' in dialog.default_combo.currentText()
    assert '25 MP · 27,5 AP' in dialog.slot_combos[0].currentText()
    assert '25 MP · 27,5 AP' in dialog.encounter_list.item(0, 3).text()
    assert dialog.catalogue.item(row, 4).text() == '27,5 AP'
    assert '25 MP · 27,5 AP' in dialog.value_preview.text()
    assert [c.currentData() for c in dialog.skill_combos] == ids
    assert dialog.donor_variant.currentData() == donor_key
    plan = dialog.plan()
    assert plan.default is None and not plan.encounters
    assert plan.techniques == {96: {'mp': 25, 'power': 55}}
    assert not session.edits
    dialog.repository.apply(plan)
    assert dialog.repository.tables()[0].records[96].power == 55
    assert len(session.edits) == 1
    dialog.close()


def test_refresh_preserves_invalid_search_text_and_restore_updates_values(qapp, tmp_path):
    dialog, session, _ = dialog_fixture(qapp, tmp_path)
    dialog.slot_combos[1].setEditText('incomplete search')
    select_technique(dialog, 96)
    dialog.tech_fields['power'].setValue(35)
    assert dialog.slot_combos[1].currentText() == 'incomplete search'
    assert 'vollständigen' in dialog.validation.text()
    dialog.slot_combos[1].setCurrentIndex(dialog.slot_combos[1].findData(0))
    dialog.restore_technique()
    assert '12 MP · 20 AP' in dialog.default_combo.currentText()
    assert not dialog.plan().techniques and not session.edits
    dialog.close()


def test_csv_exports_separate_native_and_display_values(qapp, tmp_path):
    dialog, session, _ = dialog_fixture(qapp, tmp_path)
    path = tmp_path/'values.csv'
    dialog.repository.export_csv(path, {31: {'mp': 8, 'power': 35}})
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream, delimiter=';'))
    r = next(r for r in rows if r['Name'] == 'Pepper Breath')
    assert r['MP'] == '8' and r['AP'] == '17,5' and r['Power (nativ)'] == '35'
    assert not session.edits
    dialog.close()


def test_sidebar_updates_from_image_edits_with_mp_and_ap(window, tmp_path):
    setup_window(window, tmp_path)
    assert '12 MP · 20 AP' in window.attack_summary.text()
    window.apply_attack_plan(AttackPlan(23, None, {}, {96: {'mp': 21, 'power': 55}}))
    assert '21 MP · 27,5 AP' in window.attack_summary.text()
