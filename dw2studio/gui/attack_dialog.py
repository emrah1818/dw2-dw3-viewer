"""Species defaults, encounter loadouts / AI and the image's complete catalogue."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QWidget, QFormLayout, QComboBox, QSpinBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QLineEdit, QGroupBox,
    QDialogButtonBox, QFileDialog, QMessageBox, QCheckBox, QScrollArea, QCompleter)
from ..core.battle_skills import (AttackPlan, CATEGORIES, SkillTable, BaseTable,
                                EnemyTable, skill_label, power_label)


class AttackDialog(QDialog):
    def __init__(self, identifier, name, repository, catalog, parent=None):
        super().__init__(parent)
        self.identifier = identifier
        self.repository = repository
        self.skills, self.base, self.enemies = repository.tables()
        self.original_skills = SkillTable(repository.session.original(repository.entries['WAZADATA.BIN']))
        self.original_base = BaseTable(repository.session.original(repository.entries['DIGIMNDT.BIN']))
        self.original_enemies = EnemyTable(repository.session.original(repository.entries['ENEMYSET.BIN']))
        self.rows = self.enemies.for_digimon(identifier)
        self.drafts = {r.key: (r.skills, r.rules) for r in self.rows}
        self.techniques = {}
        self.skill_combos = []
        self._loading = True
        self.setWindowTitle(f'Attacken bearbeiten · #{identifier:03} {name}')
        self.resize(1050, 820)
        layout = QVBoxLayout(self)
        heading = QLabel(f'#{identifier:03} · {name} · Attacken im Spiel-Image')
        heading.setStyleSheet('font-size:17px;font-weight:600')
        layout.addWidget(heading)
        note = QLabel('Standardtechnik und Gegner-Attacken werden getrennt gespeichert. Änderungen werden zunächst vorgemerkt und erst mit „Neues Image exportieren“ oder „Image überschreiben“ ins Spiel geschrieben.')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)
        self.build_species(catalog)
        self.build_catalogue()
        self.validation = QLabel()
        self.validation.setWordWrap(True)
        layout.addWidget(self.validation)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText('Attacken vormerken')
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Abbrechen')
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self._loading = False
        if self.rows:
            self.encounter_list.selectRow(0)
            self.load_encounter()
        if self.catalogue.rowCount():
            self.catalogue.selectRow(0)
            self.load_technique()
        self.validate()

    def skill_label(self, identifier):
        if not identifier:
            return '— leer —'
        r = self.skills.records.get(identifier)
        return skill_label(r, self.techniques.get(identifier)) if r else f'{identifier:02X} · unbekannte Technik-ID · MP/AP unbekannt'

    def skill_combo(self, current=0, empty=True):
        combo = QComboBox()
        if empty:
            combo.addItem('— leer —', 0)
        for identifier in sorted(self.skills.records):
            if 1 <= identifier <= 255:
                combo.addItem(self.skill_label(identifier), identifier)
        if combo.findData(current) < 0:
            combo.addItem(self.skill_label(current), current)
        combo.setCurrentIndex(combo.findData(current))
        self.searchable(combo)
        self.skill_combos.append(combo)
        for index in range(combo.count()):
            combo.setItemData(index, combo.itemText(index), Qt.ItemDataRole.ToolTipRole)
        return combo

    def refresh_skill_labels(self, identifier):
        """Refresh one technique without emitting slot changes or losing IDs/search text."""
        was_loading = self._loading
        self._loading = True
        try:
            for combo in self.skill_combos:
                index = combo.findData(identifier)
                if index < 0:
                    continue
                current = combo.currentIndex()
                text = combo.currentText()
                canonical = current >= 0 and text == combo.itemText(current)
                blocked = combo.blockSignals(True)
                try:
                    label = self.skill_label(identifier)
                    combo.setItemText(index, label)
                    combo.setItemData(index, label, Qt.ItemDataRole.ToolTipRole)
                    combo.setEditText(combo.itemText(current) if canonical else text)
                finally:
                    combo.blockSignals(blocked)
            for row in range(len(self.rows)):
                self.render_encounter(row)
            key = self.donor_variant.currentData()
            self.load_donor()
            index = self.donor_variant.findData(key)
            if index >= 0:
                self.donor_variant.setCurrentIndex(index)
        finally:
            self._loading = was_loading

    @staticmethod
    def searchable(combo):
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        combo.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        combo.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        combo.setMaxVisibleItems(15)

    @staticmethod
    def chosen(combo):
        # Editable search text must resolve to an actual item, never a stale index.
        index = combo.findText(combo.currentText(), Qt.MatchFlag.MatchExactly)
        if index < 0:
            raise ValueError('Bitte einen vollständigen Eintrag aus der Attackenliste auswählen.')
        return combo.itemData(index)

    def build_species(self, catalog):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        self.tabs.addTab(scroll, 'Digimon · Zuordnung & Gegner')
        layout = QVBoxLayout(page)
        self.default_combo = self.skill_combo(self.base.records.get(self.identifier, (0, 0))[1], empty=False)
        self.default_combo.setObjectName('defaultSkill')
        self.default_combo.setEnabled(self.identifier in self.base.records)
        form = QFormLayout()
        form.addRow('Standard / erlernbare Technik', self.default_combo)
        layout.addLayout(form)
        self.default_combo.currentTextChanged.connect(self.validate)
        note = QLabel('DIGIMNDT: eine Standardtechnik pro Art. Bereits im Spielstand gespeicherte Digimon behalten ihre erlernten Attacken. Die zwölf Lernplätze befinden sich im Spielstand; ENEMYSET initialisiert Wildgegner mit drei Techniken.')
        note.setWordWrap(True)
        layout.addWidget(note)
        if self.identifier not in self.base.records:
            layout.addWidget(QLabel('Für dieses Digimon ist kein Standardtechnik-Datensatz vorhanden.'))
        donor = QGroupBox('Attacken eines anderen Digimon übernehmen')
        dv = QVBoxLayout(donor)
        line = QHBoxLayout()
        self.donor_combo = QComboBox()
        for c in sorted(catalog, key=lambda c: c.id):
            if c.id in self.base.records or self.enemies.for_digimon(c.id):
                self.donor_combo.addItem(f'#{c.id:03} · {c.name} ({c.code})', c.id)
        self.searchable(self.donor_combo)
        line.addWidget(self.donor_combo, 1)
        self.donor_variant = QComboBox()
        line.addWidget(self.donor_variant, 1)
        dv.addLayout(line)
        self.donor_all = QCheckBox('Auf alle Begegnungen dieses Ziel-Digimon anwenden')
        self.donor_all.setChecked(True)
        dv.addWidget(self.donor_all)
        self.copy_button = QPushButton('Standardtechnik + gewählte Gegner-Attacken / KI übernehmen')
        self.copy_button.clicked.connect(self.copy_donor)
        dv.addWidget(self.copy_button)
        layout.addWidget(donor)
        self.donor_combo.currentTextChanged.connect(self.load_donor)
        self.load_donor()
        layout.addWidget(QLabel('Gegnerbegegnungen dieses Digimon · jede Zeile ist getrennt bearbeitbar'))
        self.encounter_list = QTableWidget(len(self.rows), 6)
        self.encounter_list.setObjectName('enemySkills')
        self.encounter_list.setHorizontalHeaderLabels(['Gruppe', 'Platz', 'Level', 'Slot 1', 'Slot 2', 'Slot 3'])
        self.encounter_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.encounter_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.encounter_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.encounter_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.encounter_list.horizontalHeader().setStretchLastSection(True)
        self.encounter_list.setMinimumHeight(130)
        for index in range(len(self.rows)):
            self.render_encounter(index)
        self.encounter_list.itemSelectionChanged.connect(self.load_encounter)
        layout.addWidget(self.encounter_list)
        self.encounter_editor = QGroupBox('Attacken der gewählten Begegnung')
        ev = QVBoxLayout(self.encounter_editor)
        slots = QFormLayout()
        self.slot_combos = []
        for index in range(3):
            combo = self.skill_combo()
            combo.setObjectName(f'enemySkill{index+1}')
            combo.currentTextChanged.connect(self.edit_encounter)
            slots.addRow(f'Slot {index+1}', combo)
            self.slot_combos.append(combo)
        ev.addLayout(slots)
        ai = QGroupBox('Gegner-KI · vier Regeln in Auswertungsreihenfolge')
        av = QVBoxLayout(ai)
        help_text = QLabel('Aktive Regeln müssen auf belegte Slots zeigen. 0 beendet die Regelliste, 4 bedeutet Abwehr. Bedingungen und Zielcodes bleiben erhalten; zum gezielten Einsatz neuer Slots die passende Regel auswählen. Bedingung 0 gilt immer und übergeht spätere Regeln.')
        help_text.setWordWrap(True)
        av.addWidget(help_text)
        self.rule_controls = []
        for index in range(4):
            line = QHBoxLayout()
            line.addWidget(QLabel(f'{index+1}. Bedingung'))
            condition = QSpinBox()
            condition.setRange(0, 255)
            condition.setToolTip('0: immer · 1: 50 % · 2: 25 % · 3: 12,5 %. Weitere Codes aus dem Spiel beibehalten oder von einer passenden Begegnung übernehmen.')
            line.addWidget(condition)
            action = QComboBox()
            for value, label in enumerate(['0 · Ende', '1 · Attacken-Slot 1', '2 · Attacken-Slot 2', '3 · Attacken-Slot 3', '4 · Abwehr']):
                action.addItem(label, value)
            line.addWidget(action, 1)
            line.addWidget(QLabel('Zielcode'))
            target = QSpinBox()
            target.setRange(0, 255)
            target.setToolTip('Aus Sicht eines Wildgegners: 0 Technikvorgabe / selbst · 1 zufälliger Verbündeter · 5 Verbündeter mit wenigsten HP · 6 besiegter Verbündeter · 7 zufälliges Spieler-Digimon · 8 Spieler-Digimon mit wenigsten HP.')
            line.addWidget(target)
            condition.valueChanged.connect(self.edit_encounter)
            action.currentIndexChanged.connect(self.edit_encounter)
            target.valueChanged.connect(self.edit_encounter)
            av.addLayout(line)
            self.rule_controls.append((condition, action, target))
        ev.addWidget(ai)
        self.ai_notice = QLabel()
        self.ai_notice.setWordWrap(True)
        ev.addWidget(self.ai_notice)
        replicate = QPushButton('Diese drei Slots und KI-Regeln auf alle Begegnungen dieses Digimon kopieren')
        replicate.clicked.connect(self.replicate_encounter)
        ev.addWidget(replicate)
        layout.addWidget(self.encounter_editor)
        self.encounter_editor.setEnabled(bool(self.rows))
        if not self.rows:
            layout.addWidget(QLabel('Keine ENEMYSET-Begegnung für dieses Digimon vorhanden.'))
        restore = QPushButton('Standardtechnik und alle Begegnungen dieses Digimon aus Quell-Image wiederherstellen')
        restore.clicked.connect(self.restore_species)
        layout.addWidget(restore)
        layout.addStretch()

    def render_encounter(self, index):
        row = self.rows[index]
        values = [str(row.set_id), str(row.slot+1), str(row.level)]
        values += [self.skill_label(i) for i in self.drafts[row.key][0]]
        for col, text in enumerate(values):
            item = QTableWidgetItem(text)
            item.setToolTip(text)
            self.encounter_list.setItem(index, col, item)

    def load_encounter(self):
        index = self.encounter_list.currentRow()
        if self._loading or index < 0:
            return
        self._loading = True
        skills, rules = self.drafts[self.rows[index].key]
        for combo, skill in zip(self.slot_combos, skills):
            if combo.findData(skill) < 0:
                combo.addItem(self.skill_label(skill), skill)
            combo.setCurrentIndex(combo.findData(skill))
        for controls, rule in zip(self.rule_controls, rules):
            condition, action, target = controls
            condition.setValue(rule[0])
            if action.findData(rule[1]) < 0:
                action.addItem(f'{rule[1]} · unbekannter Code (beibehalten)', rule[1])
            action.setCurrentIndex(action.findData(rule[1]))
            target.setValue(rule[2])
        self._loading = False
        self.validate()

    def edit_encounter(self):
        if self._loading:
            return
        index = self.encounter_list.currentRow()
        if index < 0:
            return
        try:
            skills = tuple(self.chosen(c) for c in self.slot_combos)
        except ValueError:
            self.validate()
            return
        rules = tuple((c.value(), a.currentData(), t.value()) for c, a, t in self.rule_controls)
        self.drafts[self.rows[index].key] = (skills, rules)
        self._loading = True
        self.render_encounter(index)
        self._loading = False
        self.validate()

    def replicate_encounter(self):
        index = self.encounter_list.currentRow()
        if index < 0:
            return
        draft = self.drafts[self.rows[index].key]
        self._loading = True
        for i, row in enumerate(self.rows):
            self.drafts[row.key] = draft
            self.render_encounter(i)
        self._loading = False
        self.load_encounter()

    def load_donor(self):
        self.donor_variant.clear()
        try:
            identifier = self.chosen(self.donor_combo)
        except ValueError:
            self.copy_button.setEnabled(False)
            return
        self.donor_variant.addItem('Nur Standardtechnik übernehmen', None)
        for row in self.enemies.for_digimon(identifier):
            self.donor_variant.addItem(f'Gruppe {row.set_id} / Platz {row.slot+1} / Lv {row.level}: '+
                ', '.join(self.skill_label(i) for i in row.skills if i), row.key)
        if self.donor_variant.count() > 1:
            self.donor_variant.setCurrentIndex(1)
        for index in range(self.donor_variant.count()):
            self.donor_variant.setItemData(index, self.donor_variant.itemText(index), Qt.ItemDataRole.ToolTipRole)
        self.copy_button.setEnabled(True)

    def copy_donor(self):
        identifier = self.chosen(self.donor_combo)
        if identifier in self.base.records and self.default_combo.isEnabled():
            value = self.base.records[identifier][1]
            self.default_combo.setCurrentIndex(self.default_combo.findData(value))
        key = self.donor_variant.currentData()
        if key is not None:
            donor = self.enemies.records[key]
            targets = range(len(self.rows)) if self.donor_all.isChecked() else [self.encounter_list.currentRow()]
            self._loading = True
            for index in targets:
                if index >= 0:
                    self.drafts[self.rows[index].key] = (donor.skills, donor.rules)
                    self.render_encounter(index)
            self._loading = False
            self.load_encounter()
        self.validate()

    def restore_species(self):
        self._loading = True
        if self.identifier in self.original_base.records:
            value = self.original_base.records[self.identifier][1]
            self.default_combo.setCurrentIndex(self.default_combo.findData(value))
        for index, row in enumerate(self.rows):
            original = self.original_enemies.records[row.key]
            self.drafts[row.key] = (original.skills, original.rules)
            self.render_encounter(index)
        self._loading = False
        self.load_encounter()
        self.validate()

    def build_catalogue(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.tabs.addTab(page, f'Alle Techniken ({len(self.skills.records)}) · globale Werte')
        notice = QLabel('MP = Verbrauch pro Einsatz. AP = normale Angriffsstärke (nativer power-Wert ÷ 2), kein garantierter Endschaden. Nullwerte erscheinen als — AP; negative Rohwerte gehören zur Heillogik. Änderungen hier gelten für ALLE Digimon mit dieser Technik. Beschreibung und Effektdateien werden dadurch nicht umgeschrieben.')
        notice.setWordWrap(True)
        layout.addWidget(notice)
        line = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText('Technikname oder Hex-ID suchen …')
        self.search.textChanged.connect(self.filter_catalogue)
        line.addWidget(self.search, 1)
        export = QPushButton('Gesamte Liste als CSV exportieren')
        export.clicked.connect(self.export_csv)
        line.addWidget(export)
        layout.addLayout(line)
        self.catalogue = QTableWidget(len(self.skills.records), 5)
        self.catalogue.setObjectName('allBattleSkills')
        self.catalogue.setHorizontalHeaderLabels(['Hex-ID', 'Technik', 'Art', 'MP-Kosten', 'Stärke (AP)'])
        self.catalogue.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.catalogue.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.catalogue.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.catalogue.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for row, r in enumerate(self.skills.records.values()):
            values = [f'{r.identifier:02X}', r.name, CATEGORIES[r.category], str(r.mp), power_label(r.power)]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, r.identifier)
                self.catalogue.setItem(row, col, item)
        self.catalogue.itemSelectionChanged.connect(self.load_technique)
        layout.addWidget(self.catalogue, 1)
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setMaximumHeight(95)
        layout.addWidget(self.description)
        form = QFormLayout()
        self.tech_fields = {}
        for field, label, lower, upper in [('mp', 'MP-Kosten', 0, 255), ('power', 'Nativer power-Wert (2 × AP)', -32768, 32767)]:
            spin = QSpinBox()
            spin.setRange(lower, upper)
            spin.valueChanged.connect(self.edit_technique)
            self.tech_fields[field] = spin
            form.addRow(label, spin)
        self.value_preview = QLabel()
        self.value_preview.setWordWrap(True)
        form.addRow('Anzeige in der Attackenauswahl', self.value_preview)
        combo = QComboBox()
        combo.addItems(list(CATEGORIES))
        combo.currentIndexChanged.connect(self.edit_technique)
        self.tech_fields['category'] = combo
        form.addRow('Technikart', combo)
        layout.addLayout(form)
        advanced = QGroupBox('Weitere native Technikwerte · Codes unverändert lassen, wenn unbekannt')
        adv = QFormLayout(advanced)
        for field, label, upper in [('cast', 'Startanimation (0–3)', 3), ('target', 'Zieltyp-Code (0–15)', 15),
                                   ('specialty', 'Element-Code (0–15)', 15), ('rank', 'Rang-Code (0–15)', 15)]:
            spin = QSpinBox()
            spin.setRange(0, upper)
            spin.valueChanged.connect(self.edit_technique)
            self.tech_fields[field] = spin
            adv.addRow(label, spin)
        layout.addWidget(advanced)
        restore = QPushButton('Gewählte globale Technik aus Quell-Image wiederherstellen')
        restore.clicked.connect(self.restore_technique)
        layout.addWidget(restore)

    def technique_id(self):
        row = self.catalogue.currentRow()
        return self.catalogue.item(row, 0).data(Qt.ItemDataRole.UserRole) if row >= 0 else None

    def load_technique(self):
        if self._loading:
            return
        identifier = self.technique_id()
        if identifier is None:
            return
        record = self.skills.records[identifier]
        changes = self.techniques.get(identifier, {})
        self._loading = True
        for field, control in self.tech_fields.items():
            value = changes.get(field, getattr(record, field))
            control.setCurrentIndex(value) if isinstance(control, QComboBox) else control.setValue(value)
        self._loading = False
        self.description.setText(f'{record.name}: {record.description}')
        self.value_preview.setText(self.skill_label(identifier))

    def edit_technique(self):
        if self._loading:
            return
        identifier = self.technique_id()
        if identifier is None:
            return
        record = self.skills.records[identifier]
        values = {field: control.currentIndex() if isinstance(control, QComboBox) else control.value()
                  for field, control in self.tech_fields.items()}
        changes = {k: v for k, v in values.items() if v != getattr(record, k)}
        if changes:
            self.techniques[identifier] = changes
        else:
            self.techniques.pop(identifier, None)
        row = self.catalogue.currentRow()
        for col, text in [(2, CATEGORIES[values['category']]), (3, str(values['mp'])), (4, power_label(values['power']))]:
            self.catalogue.item(row, col).setText(text)
        self.refresh_skill_labels(identifier)
        self.value_preview.setText(self.skill_label(identifier))
        self.validate()

    def restore_technique(self):
        identifier = self.technique_id()
        if identifier is None or identifier not in self.original_skills.records:
            return
        original, current = self.original_skills.records[identifier], self.skills.records[identifier]
        self.techniques[identifier] = {field: getattr(original, field) for field in self.tech_fields
                                      if getattr(original, field) != getattr(current, field)}
        self.load_technique()
        self.edit_technique()

    def filter_catalogue(self, text):
        text = text.casefold().strip()
        visible = []
        for row in range(self.catalogue.rowCount()):
            match = text in ' '.join(self.catalogue.item(row, col).text() for col in range(3)).casefold()
            self.catalogue.setRowHidden(row, not match)
            if match:
                visible.append(row)
        current = self.catalogue.currentRow()
        if current not in visible:
            if visible:
                self.catalogue.selectRow(visible[0])
            else:
                self.catalogue.clearSelection()
                self.catalogue.setCurrentCell(-1, -1)
                self.description.setText('Keine Technik gefunden.')
        for control in self.tech_fields.values():
            control.setEnabled(bool(visible))

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Alle Techniken exportieren', 'DW2_Attacken.csv', 'CSV (*.csv)')
        if path:
            try:
                self.repository.export_csv(path, self.techniques)
            except Exception as exc:
                QMessageBox.warning(self, 'Technikliste konnte nicht exportiert werden', str(exc))

    def plan(self):
        default = self.chosen(self.default_combo) if self.default_combo.isEnabled() else None
        if self.identifier in self.base.records and default == self.base.records[self.identifier][1]:
            default = None
        changes = {row.key: self.drafts[row.key] for row in self.rows
                   if self.drafts[row.key] != (row.skills, row.rules)}
        return AttackPlan(self.identifier, default, changes, dict(self.techniques))

    def validate(self):
        if self._loading or not hasattr(self, 'buttons'):
            return
        try:
            # Reject incomplete editable-combo text even before it enters drafts.
            if self.rows:
                for combo in self.slot_combos:
                    self.chosen(combo)
            plan = self.plan()
            files = self.repository.preview(plan)
            text = f'{len(plan.encounters)} Gegnerbegegnung(en) · {len(plan.techniques)} globale Technikänderung(en) · {len(files)} native Datei(en). '
            text += 'Bereit zum Vormerken.' if files else 'Keine neuen Änderungen.'
            self.validation.setText(text)
            self.validation.setStyleSheet('color:#91d9ac')
            active = bool(files)
        except (ValueError, OSError) as exc:
            active = False
            self.validation.setText(str(exc))
            self.validation.setStyleSheet('color:#f3ba81')
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setEnabled(active)
        index = self.encounter_list.currentRow()
        if index >= 0:
            skills, rules = self.drafts[self.rows[index].key]
            used = set()
            for _, action, _ in rules:
                if action == 0:
                    break
                used.add(action)
            unused = [str(i+1) for i, skill in enumerate(skills) if skill and i+1 not in used]
            self.ai_notice.setText('Belegte Slots ohne aktive KI-Regel: '+', '.join(unused)+'. Regeln bei Bedarf anpassen.' if unused else 'Alle belegten Slots sind in der aktiven KI-Regelliste referenziert. Bedingungen bestimmen ihren Einsatz.')

    def accept(self):
        self.validate()
        if self.buttons.button(QDialogButtonBox.StandardButton.Save).isEnabled():
            super().accept()
