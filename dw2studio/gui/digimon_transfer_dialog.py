"""Review a complete native model/animation replacement before staging it."""
from PyQt6.QtWidgets import (QDialog,QVBoxLayout,QLabel,QTableWidget,QTableWidgetItem,
                            QDialogButtonBox,QHeaderView,QAbstractItemView)


class DigimonTransferDialog(QDialog):
    def __init__(self,plan,target,parent=None):
        super().__init__(parent);self.plan=plan
        self.setWindowTitle('Digimon ersetzen · Modell, Texturen und Animationen');self.resize(740,560)
        layout=QVBoxLayout(self);source=plan.transfer.source
        heading=QLabel(f'Quelle: #{source["id"]:03d} {source["name"]} ({source["code"]})\nZiel: #{target.id:03d} {target.name} ({target.code})')
        heading.setWordWrap(True);layout.addWidget(heading)
        note=QLabel(f'Das Modell einschließlich Texturen und Skelett sowie alle A–K-Animationsdateien werden gemeinsam ersetzt. Knochen: Quelle {plan.source_bones}, Ziel bisher {plan.target_bones}. Der Zielname bleibt erhalten.')
        note.setWordWrap(True);layout.addWidget(note)
        table=QTableWidget(len(plan.rows),4);self.table=table
        table.setHorizontalHeaderLabels(['Datei','Quelle · Bytes','Bisher · Bytes','Prüfung'])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch)
        for row,values in enumerate(plan.rows):
            for col,value in enumerate(values):table.setItem(row,col,QTableWidgetItem(str(value)))
        layout.addWidget(table,1)
        status=QLabel('\n'.join(plan.errors) if plan.errors else f'Geprüft. {len(plan.relocated)} Datei(en) erhalten einen neuen Datenbereich. Die Änderungen werden gesammelt; erst Image speichern schreibt Daten und aktualisierte Verweise.')
        status.setWordWrap(True);status.setStyleSheet('color: #f3c875;' if plan.errors else 'color: #89dcb5;');layout.addWidget(status)
        foot=QLabel('Größere Ersatzdateien werden verlagert; das Image kann wachsen. Quelle und andere Digimon bleiben unabhängig. Das Spiel verwendet weiterhin die Animationsplätze des Ziel-Digimon. Ein praktischer Test im Spiel ist anschließend erforderlich.')
        foot.setWordWrap(True);layout.addWidget(foot)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        self.confirm=buttons.button(QDialogButtonBox.StandardButton.Ok);self.confirm.setText('Digimon ersetzen – vormerken');self.confirm.setEnabled(not plan.errors)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Abbrechen')
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);layout.addWidget(buttons)
