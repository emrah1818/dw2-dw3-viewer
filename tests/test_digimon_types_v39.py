"""Native species-type nibble, composable shared-file edits and actual Qt button."""
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFileDialog
from dw2studio.core.battle_skills import AttackRepository, AttackPlan, BaseTable
from dw2studio.core.digimon_types import TypeRepository, TYPES, type_name
from dw2studio.core.edit_session import EditSession
from dw2studio.core.psx_patch import validate_form1_ecc
from dw2studio.core.catalog import DigimonCandidate
from test_battle_skills_v38 import image_fixture


def typed_image(tmp_path, raw=False, private=False):
    session, entries = image_fixture(tmp_path, raw, private)
    repo = TypeRepository(session, entries)
    data = repo.table().data
    for identifier, code in [(3, 1), (5, 1), (12, 1), (23, 0)]:
        data = BaseTable(data).with_type(identifier, code)
    session.stage(repo.entry, data)
    output, _ = session.save(tmp_path/('typed.bin' if raw else 'typed.iso'))
    return EditSession(output, session.sector_size), entries


@pytest.mark.parametrize('new_type', [0, 1, 2])
def test_only_low_type_nibble_changes_for_every_rank(new_type):
    from test_battle_skills_v38 import tables_fixture
    for rank in range(16):
        original = bytearray(tables_fixture()['DIGIMNDT.BIN'])
        offset = BaseTable(original).records[3][0]+4
        original[offset] = (rank << 4) | 1
        table = BaseTable(original)
        changed = table.with_type(3, new_type)
        assert changed[offset] == (rank << 4) | new_type
        assert BaseTable(changed).type_of(3) == new_type
        assert all(a == b or i == offset for i, (a, b) in enumerate(zip(original, changed)))
        assert len(changed) == len(original)


def test_invalid_codes_and_missing_records_do_not_stage(tmp_path):
    session, entries = typed_image(tmp_path)
    repo = TypeRepository(session, entries)
    for code in [-1, 3, 15, True, 'Virus', None]:
        with pytest.raises(ValueError):
            repo.change(3, code)
        assert not session.edits
    with pytest.raises(ValueError, match='keinen'):
        repo.change(999, 1)
    assert TYPES == {0: 'Data', 1: 'Vaccine', 2: 'Virus'}
    assert 'Unbekannter' in type_name(15)


def test_type_and_default_attack_updates_compose_and_restore_independently(tmp_path):
    session, entries = typed_image(tmp_path)
    types = TypeRepository(session, entries)
    attacks = AttackRepository(session, entries)
    original = types.table().data
    types.change(3, 2)
    attacks.apply(AttackPlan(3, 36, {}, {}))
    types.change(23, 1)
    attacks.apply(AttackPlan(3, 88, {}, {}))
    table = types.table()
    assert table.type_of(3) == 2 and table.records[3][1] == 88
    assert table.type_of(23) == 1 and len(session.edits) == 1
    types.change(3, types.original_type(3))
    assert types.table().records[3][1] == 88
    types.change(23, types.original_type(23))
    assert session.edits  # the independent attack change remains.
    attacks.apply(AttackPlan(3, 31, {}, {}))
    assert types.table().data == original and not session.edits


@pytest.mark.parametrize('raw', [False, True])
@pytest.mark.parametrize('private', [False, True])
def test_native_export_and_project_reopen_retain_types(tmp_path, raw, private):
    session, entries = typed_image(tmp_path, raw, private)
    source = session.source.read_bytes()
    repo = TypeRepository(session, entries)
    repo.change(3, 2)
    repo.change(23, 1)
    project = tmp_path/'types.dw2mod'
    session.export_project(project)
    reopened = EditSession(session.source, session.sector_size)
    reopened.import_project(project, entries)
    output, _ = reopened.save(tmp_path/('out.bin' if raw else 'out.iso'))
    after = EditSession(output, session.sector_size)
    table = TypeRepository(after, entries).table()
    assert table.type_of(3) == 2 and table.type_of(23) == 1
    assert table.records[3][1] == 31  # Pepper Breath was preserved.
    assert session.source.read_bytes() == source
    assert output.stat().st_size == len(source)
    if raw:
        data = output.read_bytes()
        assert all(validate_form1_ecc(data[i:i+2352]) for i in range(0, len(data), 2352))


def setup_window(window, tmp_path, private=False):
    session, entries = typed_image(tmp_path, private=private)
    window.image = str(session.source)
    window.image_path = session.source
    window.index_key = 'types'
    window.session = session
    # Deliberately no WAZADATA/ENEMYSET entries: the type editor is independent.
    window.entries = [e for e in entries if e.path.endswith('DIGIMNDT.BIN') or e.path == 'SLUS_011.93']
    window.catalog = [DigimonCandidate(3, 'AGUM', 'Agumon'), DigimonCandidate(23, 'YUKI', 'Frigimon')]
    window.refresh_list()
    window.update_actions()
    return session


def test_button_current_type_change_and_original_restore_before_model_load(window, tmp_path, monkeypatch):
    from dw2studio.gui.type_dialog import TypeDialog
    session = setup_window(window, tmp_path)
    original = session.source.read_bytes()
    assert window.project_model is None and window.type_button.isEnabled()
    assert window.type_summary.text() == 'Typ: Vaccine'
    seen = []
    def exec_dialog(dialog):
        seen.append(dialog)
        assert dialog.current_type == 1
        dialog.type_combo.setCurrentIndex(dialog.type_combo.findData(2))
        dialog.accept()
        return dialog.result()
    monkeypatch.setattr(TypeDialog, 'exec', exec_dialog)
    monkeypatch.setattr(window, 'load_digimon', lambda: pytest.fail('Type editing must not reload geometry'))
    QTest.mouseClick(window.type_button, Qt.MouseButton.LeftButton)
    assert seen and not window.test_errors
    assert window.type_summary.text() == 'Typ: Virus'
    assert window.pending.count() == 1 and session.source.read_bytes() == original
    def restore(dialog):
        assert dialog.current_type == 2
        dialog.restore.click()
        dialog.accept()
        return dialog.result()
    monkeypatch.setattr(TypeDialog, 'exec', restore)
    QTest.mouseClick(window.type_button, Qt.MouseButton.LeftButton)
    assert window.type_summary.text() == 'Typ: Vaccine' and not session.edits


@pytest.mark.parametrize('private', [False, True])
def test_type_only_project_load_does_not_require_attack_tables(window, tmp_path, monkeypatch, private):
    session = setup_window(window, tmp_path, private)
    window.apply_digimon_type(3, 2)
    project = tmp_path/'type_only.dw2mod'
    session.export_project(project)
    window.session = EditSession(session.source, session.sector_size)
    if private:
        window.entries = [e for e in window.entries if e.path == 'SLUS_011.93']
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *a, **kw: (str(project), ''))
    monkeypatch.setattr(window, 'refresh_names', lambda: None)
    monkeypatch.setattr(window, 'load_digimon', lambda: None)
    window.load_project()
    assert not window.test_errors
    assert window.type_summary.text() == 'Typ: Virus'
    assert window.get_type_repository().table().type_of(3) == 2


def test_unknown_original_type_is_not_guessed_and_cancel_does_not_write(qapp, tmp_path):
    from dw2studio.gui.type_dialog import TypeDialog
    session, entries = image_fixture(tmp_path)
    repo = TypeRepository(session, entries)
    dialog = TypeDialog(3, 'Agumon', repo.table(), repo.original_type(3), repo.entry.path)
    assert dialog.current_type == 11  # opaque fixture byte 0xAB, never guessed.
    assert not dialog.buttons.button(QDialogButtonBox.StandardButton.Save).isEnabled()
    assert not dialog.restore.isEnabled()
    dialog.type_combo.setCurrentIndex(dialog.type_combo.findData(0))
    assert dialog.buttons.button(QDialogButtonBox.StandardButton.Save).isEnabled()
    dialog.reject()
    assert dialog.result() == QDialog.DialogCode.Rejected and not session.edits
    dialog.close()
