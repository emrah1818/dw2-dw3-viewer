"""Edit a native species name, with validation against the actual name pool."""
from PyQt6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,
                            QPushButton,QDialogButtonBox)
from ..core.digimon_names import MAX_NAME_LENGTH


class RenameDialog(QDialog):
    def __init__(self,identifier,table,filename,original_name,parent=None):
        super().__init__(parent);self.identifier=identifier;self.table=table
        current=table.record(identifier).text
        self.setWindowTitle('Namen ändern · Digimon im Spiel');self.resize(600,410)
        layout=QVBoxLayout(self)
        heading=QLabel(f'#{identifier:03} · Aktueller Spielname: {current or "(leer)"}')
        heading.setWordWrap(True);layout.addWidget(heading)
        description=QLabel('Ändert den Standardnamen dieser Digimon-Art in der nativen Spieldatei. Neue Gegner und Anzeigen, die diesen Standardnamen verwenden, übernehmen ihn. Bereits gespeicherte Spitznamen und eigenständige Dialogtexte werden dadurch nicht geändert.')
        description.setWordWrap(True);layout.addWidget(description)
        layout.addWidget(QLabel('Neuer Name'))
        self.name_edit=QLineEdit(current);self.name_edit.setObjectName('digimonName');self.name_edit.setMaxLength(MAX_NAME_LENGTH);layout.addWidget(self.name_edit)
        hint=QLabel('1–13 Zeichen. A–Z, a–z, 0–9, Leerzeichen und & ? ! / - , . \' : +. Der vorhandene Namensspeicher muss ausreichen. Umlaute und andere nicht unterstützte Zeichen werden abgewiesen.');hint.setWordWrap(True);layout.addWidget(hint)
        self.validation=QLabel();self.validation.setWordWrap(True);layout.addWidget(self.validation)
        note=QLabel(f'Ziel: {filename}\nDie Änderung wird vorgemerkt. Erst der Image-Export oder bestätigtes Überschreiben schreibt die Spieldatei.');note.setWordWrap(True);layout.addWidget(note)
        if original_name:
            restore=QPushButton('Namen aus geöffnetem Quell-Image einsetzen');restore.clicked.connect(lambda:self.name_edit.setText(original_name));layout.addWidget(restore)
        self.buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText('Namen vormerken')
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Abbrechen')
        self.buttons.accepted.connect(self.accept);self.buttons.rejected.connect(self.reject);layout.addWidget(self.buttons)
        self.name_edit.textChanged.connect(self.validate);self.validate();self.name_edit.selectAll();self.name_edit.setFocus()

    @property
    def new_name(self):return self.name_edit.text()

    def validate(self):
        try:
            changed=self.table.renamed(self.identifier,self.new_name)
            active=changed!=self.table.data
            self.validation.setText(f'{len(self.new_name)} / {MAX_NAME_LENGTH} Zeichen · '+('Nativ geprüft; Dateigröße bleibt gleich.' if active else 'Name unverändert.'))
            self.validation.setStyleSheet('color:#91d9ac')
        except ValueError as exc:
            active=False;self.validation.setText(str(exc));self.validation.setStyleSheet('color:#f3ba81')
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setEnabled(active)

    def accept(self):
        self.validate()
        if self.buttons.button(QDialogButtonBox.StandardButton.Save).isEnabled():super().accept()
