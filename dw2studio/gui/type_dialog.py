"""Edit the selected species' native Data/Vaccine/Virus type."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox,
                            QPushButton, QDialogButtonBox)
from ..core.digimon_types import TYPES, type_name


class TypeDialog(QDialog):
    def __init__(self, identifier, name, table, original_type, filename, parent=None):
        super().__init__(parent)
        self.identifier = identifier
        self.table = table
        self.current_type = table.type_of(identifier)
        self.setWindowTitle(f'Typ ändern · #{identifier:03} {name}')
        self.resize(580, 350)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f'#{identifier:03} · {name}'))
        layout.addWidget(QLabel(f'Aktueller Typ: {type_name(self.current_type)}'))
        note = QLabel('Ändert den Typ dieser Digimon-Art im Spiel. Der Typ wird unter anderem für Kampf-Typvorteile, Typ-Anzeigen und typabhängige DNA-Regeln abgefragt.')
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addWidget(QLabel('Neuer Typ'))
        self.type_combo = QComboBox()
        self.type_combo.setObjectName('digimonType')
        for code in (1, 2, 0):
            self.type_combo.addItem(TYPES[code], code)
        if self.current_type not in TYPES:
            self.type_combo.addItem(type_name(self.current_type), self.current_type)
        self.type_combo.setCurrentIndex(self.type_combo.findData(self.current_type))
        layout.addWidget(self.type_combo)
        self.restore = QPushButton('Originaltyp aus geöffnetem Quell-Image einsetzen')
        self.restore.setEnabled(original_type in TYPES)
        self.restore.clicked.connect(lambda: self.type_combo.setCurrentIndex(self.type_combo.findData(original_type)))
        layout.addWidget(self.restore)
        self.validation = QLabel()
        self.validation.setWordWrap(True)
        layout.addWidget(self.validation)
        note = QLabel(f'Ziel: {filename}\nZunächst vormerken. Erst „Neues Image exportieren“ oder bestätigtes „Image überschreiben“ schreibt die Spieldatei.')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText('Typ vormerken')
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Abbrechen')
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.type_combo.currentIndexChanged.connect(self.validate)
        self.validate()

    @property
    def new_type(self):
        return self.type_combo.currentData()

    def validate(self):
        try:
            changed = self.table.with_type(self.identifier, self.new_type)
            active = changed != self.table.data
            self.validation.setText(f'{type_name(self.current_type)} → {type_name(self.new_type)} · '+('Zum Vormerken bereit.' if active else 'Typ unverändert.'))
        except ValueError as exc:
            active = False
            self.validation.setText(str(exc))
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setEnabled(active)

    def accept(self):
        self.validate()
        if self.buttons.button(QDialogButtonBox.StandardButton.Save).isEnabled():
            super().accept()
