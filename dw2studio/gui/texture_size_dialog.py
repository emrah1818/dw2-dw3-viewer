"""Show the native resolution loss before accepting a large game-atlas PNG."""
from PyQt6.QtWidgets import (QDialog,QVBoxLayout,QLabel,QComboBox,QDialogButtonBox)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PIL.ImageQt import ImageQt
from ..core.texture_resolution import native_scale,reduce_for_native


class NativeTextureSizeDialog(QDialog):
    def __init__(self,image,target=(128,256),parent=None):
        super().__init__(parent);self.source=image;self.target=target;self.factor=native_scale(image.size,target)
        self.setWindowTitle('Große PNG → native Spieltextur');self.resize(590,530)
        layout=QVBoxLayout(self)
        heading=QLabel(f'Quelle: {image.width}×{image.height} · {self.factor}× je Achse\nSpieltextur nach Import: {target[0]}×{target[1]}')
        heading.setWordWrap(True);layout.addWidget(heading)
        notice=QLabel('Für das vorhandene PS1-Modell wird diese PNG verkleinert. Details gehen dabei verloren. Die höhere Auflösung wird nicht ins Spiel-Image geschrieben. Die anschließende Farbvorschau zeigt das kodierte PS1-Ergebnis. Für die volle Auflösung im Viewer: Texturen → Vollfarben nur im Viewer ersetzen verwenden.')
        notice.setWordWrap(True);layout.addWidget(notice)
        self.filter=QComboBox();self.filter.addItem('Flächenmittel (BOX) – mittelt die Quellpixel','BOX');self.filter.addItem('Pixelgrafik (NEAREST) – erhält einzelne Quellfarben','NEAREST');layout.addWidget(self.filter)
        self.preview=QLabel();self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.addWidget(self.preview,1)
        self.buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(f'Auf {target[0]}×{target[1]} verkleinern und prüfen')
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText('Abbrechen')
        self.buttons.accepted.connect(self.accept);self.buttons.rejected.connect(self.reject);layout.addWidget(self.buttons)
        self.filter.currentIndexChanged.connect(self.refresh);self.refresh()

    @property
    def normalized_image(self):return reduce_for_native(self.source,self.target,self.filter.currentData())

    def refresh(self):
        result=self.normalized_image;pixmap=QPixmap.fromImage(ImageQt(result).copy())
        self.preview.setPixmap(pixmap.scaled(220,260,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.FastTransformation))


def prepare_native_png(path,target=(128,256),parent=None):
    """Return native RGBA only after explicit confirmation; None on cancellation."""
    from ..core.texture_resolution import read_png
    image=read_png(path);factor=native_scale(image.size,target)
    if factor==1:return image
    dialog=NativeTextureSizeDialog(image,target,parent)
    if dialog.exec()!=QDialog.DialogCode.Accepted:return None
    return dialog.normalized_image
