"""Standalone DW2 3D Viewer: navigation, textures, rigging and staged image edits."""
from pathlib import Path
import sys,os,time,uuid,tempfile
from PyQt6.QtCore import Qt,QThread,pyqtSignal,QSettings,QTimer,QEvent
from PyQt6.QtGui import QIcon,QPixmap
from PyQt6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,
 QSplitter,QPushButton,QLabel,QLineEdit,QListWidget,QListWidgetItem,QFileDialog,QMessageBox,
 QComboBox,QFrame,QPlainTextEdit,QCheckBox,QGroupBox,QDialog,QDialogButtonBox,QScrollArea,QTabWidget,QSpinBox,QInputDialog)
from dw2studio.i18n import translate
from dw2studio.core.disc import Disc
from dw2studio.core.auto_models import cache_key,candidate_models,selected_model_entries
from dw2studio.core.converter_locator import find_converter
from dw2studio.core.fast_loading import DiscReader,ConversionQueue,ModelRequest
from dw2studio.core.edit_session import EditSession
from dw2studio.core.digimon_names import NameRepository,NameTable,basename,FILE_INDEX
from dw2studio.core.battle_skills import AttackRepository,FILE_INDEX as ATTACK_FILE_INDEX,skill_label
from dw2studio.core.digimon_types import TypeRepository,type_name
from dw2studio.core.eye_preparation import EyePreparation
from dw2studio.core.native_rom_bridge import NativeTextureInfo,native_model_entry,write_cue_for_image
from dw2studio.core.native_tim_patch import regions,replace_tim
from dw2studio.core.model_export import export_model,supported_export_filters
from dw2studio.core.mini_assets import create_workcopy,texture_slots,replace_texture,export_texture
from dw2studio.core.model_replacements import active_replacement,set_replacement,clear_replacement,publish_replacement
from dw2studio.renderer.viewer import ModelViewer,VTK_AVAILABLE
if VTK_AVAILABLE:
 from dw2studio.renderer.viewer import VTKAnimatedViewer
CACHE=Path.home()/'.dw2_3d_viewer_studio'

def icon_file():
 root=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent));return root/'assets'/'DW2_3D_Viewer.ico'

class ImageWriter(QThread):
 done=pyqtSignal(str,str);failed=pyqtSignal(str)
 def __init__(self,session,target,overwrite):super().__init__();self.session=session;self.target=target;self.overwrite=overwrite
 def run(self):
  try:
   output,backup=self.session.save(self.target,overwrite=self.overwrite);self.done.emit(str(output),str(backup) if backup else '')
  except Exception as exc:self.failed.emit(str(exc))

class Main(QMainWindow):
    def __init__(self):
        super().__init__();self.resize(1480,860);self.settings=QSettings('DW2 3D Viewer Studio','Preferences');self.language=str(self.settings.value('language','de'))
        if self.language not in ('de','en'):self.language='de'
        if icon_file().is_file():self.setWindowIcon(QIcon(str(icon_file())))
        self.image=None;self.image_path=None;self.entries=[];self.catalog=[];self.visible=[];self.current=None;self.loaded_digimon=None;self.active_digimon_key=None;self.active_native=False;self.project_model=None;self.display_model=None;self.session=None;self.index_key=None;self.name_repository=None;self._source_names={};self.rgb_namespace=None
        self.reader=None;self.writer=None;self.eye_jobs=[];self._pending_write=None;self.model_paths={};self.raw_models={};self.revisions={};self.wanted=None;self._closing=False
        self.setStyleSheet('''QMainWindow,QWidget{background:#0f1929;color:#edf5ff;font:12px "Segoe UI";} QLabel#title{font-size:21px;font-weight:700;} QLabel#sub{color:#a2b6ce;} QLineEdit,QListWidget,QComboBox,QPlainTextEdit,QSpinBox{background:#17263b;border:1px solid #304862;border-radius:6px;padding:6px;} QPushButton{background:#1c344d;border:1px solid #365575;padding:9px;border-radius:7px;font-weight:600;} QPushButton:hover{background:#294d70;} QPushButton:disabled{color:#738296;} QPushButton#primary{background:#0876d8;} QTabWidget::pane{border:1px solid #304862;} QTabBar::tab{padding:9px 8px;background:#1b2d43;} QTabBar::tab:selected{background:#0876d8;} QSplitter::handle{background:#263b53;}''')
        central=QWidget();self.setCentralWidget(central);root=QVBoxLayout(central);bar=QHBoxLayout();heading=QLabel('DW2 · MOD STUDIO 4.0');heading.setObjectName('title');bar.addWidget(heading);bar.addStretch()
        studio_note=QLabel('Mod Studio: eigenes Projekt · Änderungen mit .dw2mod übertragen');studio_note.setWordWrap(True);root.addWidget(studio_note)
        self.open_image=QPushButton('BIN / ISO öffnen');self.open_image.setObjectName('primary');self.open_image.clicked.connect(self.choose_image);bar.addWidget(self.open_image)
        self.open_model=QPushButton('3D-Datei importieren');self.open_model.clicked.connect(self.import_model);bar.addWidget(self.open_model)
        self.language_combo=QComboBox();self.language_combo.addItem('Deutsch','de');self.language_combo.addItem('Englisch','en');self.language_combo.setCurrentIndex(0 if self.language=='de' else 1);bar.addWidget(self.language_combo);root.addLayout(bar)
        split=QSplitter(Qt.Orientation.Horizontal);split.setChildrenCollapsible(False);root.addWidget(split,1)
        side=QWidget();side.setMinimumWidth(210);side.setMaximumWidth(330);left=QVBoxLayout(side);left.addWidget(QLabel('DIGIMON / MODELLE'))
        self.search=QLineEdit();self.search.setPlaceholderText('Digimon suchen …');self.search.textChanged.connect(self.refresh_list);left.addWidget(self.search)
        self.digimon=QListWidget();self.digimon.currentRowChanged.connect(self.select_digimon);self.digimon.itemDoubleClicked.connect(lambda item:self.load_digimon());self.digimon.installEventFilter(self);left.addWidget(self.digimon,1)
        self.rename_button=QPushButton('Namen ändern');self.rename_button.setObjectName('renameDigimon');self.rename_button.clicked.connect(self.rename_digimon);left.addWidget(self.rename_button)
        self.type_button=QPushButton('Typ ändern');self.type_button.setObjectName('changeDigimonType');self.type_button.clicked.connect(self.change_digimon_type);left.addWidget(self.type_button)
        self.type_summary=QLabel('Typ: Spiel-Image und Digimon wählen');self.type_summary.setWordWrap(True);self.type_summary.setObjectName('sub');left.addWidget(self.type_summary)
        self.attack_button=QPushButton('Attacken bearbeiten');self.attack_button.setObjectName('editBattleSkills');self.attack_button.clicked.connect(self.edit_attacks);left.addWidget(self.attack_button)
        self.attack_summary=QLabel('Spiel-Image und Digimon wählen');self.attack_summary.setWordWrap(True);self.attack_summary.setObjectName('sub');left.addWidget(self.attack_summary)
        hint=QLabel('Doppelklick: öffnen\n↑ / ↓: sofort zum nächsten Modell');hint.setWordWrap(True);left.addWidget(hint)
        self.disc_status=QLabel('Spiel-Image öffnen oder externe 3D-Datei laden');self.disc_status.setWordWrap(True);self.disc_status.setObjectName('sub');left.addWidget(self.disc_status);split.addWidget(side)
        center_widget=QWidget();center=QVBoxLayout(center_widget);center.setContentsMargins(0,0,0,0)
        self.viewer=VTKAnimatedViewer() if VTK_AVAILABLE else ModelViewer();center.addWidget(self.viewer,1)
        self.model_status=QLabel('Bereit');self.model_status.setObjectName('sub');self.model_status.setWordWrap(True);center.addWidget(self.model_status)
        grid=QGridLayout();self.model_buttons=[]
        for i,(text,slot) in enumerate([('PNG importieren',self.replace_png),('PNG exportieren',self.export_png),('Augen vollständig ersetzen',self.write_game_eyes),('OBJ importieren & riggen',self.import_model),('3D-Datei exportieren',self.export_model),('Originalmodell wiederherstellen',self.restore_original)]):
            button=QPushButton(text);button.clicked.connect(slot);grid.addWidget(button,i//3,i%3)
            if i in (0,1,2,4,5):self.model_buttons.append(button)
        center.addLayout(grid);split.addWidget(center_widget)
        self.tabs=QTabWidget();self.tabs.setMinimumWidth(290);self.tabs.setMaximumWidth(380);split.addWidget(self.tabs)
        changes=QWidget();cv=QVBoxLayout(changes);self.pending_status=QLabel('0 Dateien vorgemerkt');cv.addWidget(self.pending_status);self.pending=QListWidget();cv.addWidget(self.pending,1)
        for text,slot in [('Neues Image exportieren',self.export_image),('Image überschreiben …',self.overwrite_image),('Ausgewählte Änderung verwerfen',self.discard_selected),('Mod-Projekt speichern',self.save_project),('Mod-Projekt laden',self.load_project),('Vollfarben-Projekt speichern',self.save_rgb_project),('Vollfarben-Projekt laden',self.load_rgb_project)]:
            button=QPushButton(text);button.clicked.connect(slot);cv.addWidget(button)
            if text=='Neues Image exportieren':button.setObjectName('primary')
        note=QLabel('Vollfarben-Texturen: Viewer-Projekt / 3D-Export. Native Änderungen: PS1-Image. Beide werden getrennt aufgeführt.');note.setWordWrap(True);cv.addWidget(note);self.tabs.addTab(changes,'Änderungen')
        self.replace_digimon_button=QPushButton('Digimon ersetzen · Modell + Animationen');self.replace_digimon_button.setObjectName('replaceDigimon');self.replace_digimon_button.clicked.connect(self.replace_digimon);center.addWidget(self.replace_digimon_button)
        textures=QWidget();tv=QVBoxLayout(textures);self.model_label=QLabel('Noch kein Modell');self.model_label.setWordWrap(True);tv.addWidget(self.model_label);self.texture_combo=QComboBox();tv.addWidget(self.texture_combo)
        self.texture_buttons=[];self.native_texture_buttons=[]
        for text,slot in [('PNG importieren',self.replace_png),('Vollfarben nur im Viewer ersetzen',self.replace_preview_png),('Externe 3D-Datei ansehen',self.import_free_model)]:
            button=QPushButton(text);button.clicked.connect(slot);tv.addWidget(button)
            if slot in (self.replace_png,self.replace_preview_png):self.texture_buttons.append(button)
        note=QLabel('PNG importieren ersetzt bei einem Spiel-Digimon die native Textur samt Paletten wie in v3.1. Vorschau prüfen, vormerken, weitere Digimon bearbeiten und am Ende das Image speichern.');note.setWordWrap(True);tv.addWidget(note)
        native_group=QGroupBox('Spieltextur · Paletten');native_layout=QVBoxLayout(native_group)
        for text,slot in [('Native PNG-Vorlage exportieren',self.export_native_tim),('Nativen Augenatlas exportieren',self.export_eye_atlas),('PNG ins PS1-Image importieren …',self.import_native_png)]:
            button=QPushButton(text);button.clicked.connect(slot);native_layout.addWidget(button);self.native_texture_buttons.append(button)
        self.palette_mode=QComboBox();self.palette_mode.addItem('Wie v3.1 · automatische Paletten','v31');self.palette_mode.addItem('Farbschutz · kleine Änderungen bevorzugen','protect');self.palette_mode.addItem('Exakt RGB555 · nur wenn alle Farben passen','exact');native_layout.addWidget(self.palette_mode)
        self.native_notice=QLabel('Standard: Verfahren aus v3.1. Viele PNG-Farben werden automatisch auf neue Teilpaletten verteilt und angenähert. Die Vorschau zeigt das tatsächliche Ergebnis, bevor Änderungen vorgemerkt werden.');self.native_notice.setWordWrap(True);native_layout.addWidget(self.native_notice);tv.addWidget(native_group);tv.addStretch();self.tabs.addTab(textures,'Texturen')
        settings_page=QWidget();sv=QVBoxLayout(settings_page)
        if hasattr(self.viewer,'settings_panel'):sv.addWidget(self.viewer.settings_panel,1)
        self.prefetch=QCheckBox('Nachbarmodelle im Hintergrund vorbereiten');self.prefetch.setChecked(True);sv.addWidget(self.prefetch)
        row=QHBoxLayout();row.addWidget(QLabel('3D-Szenen im RAM'));self.scene_limit=QSpinBox();self.scene_limit.setRange(1,8);self.scene_limit.setValue(4);row.addWidget(self.scene_limit);sv.addLayout(row)
        if hasattr(self.viewer,'set_scene_cache_limit'):self.scene_limit.valueChanged.connect(self.viewer.set_scene_cache_limit)
        self.tabs.addTab(settings_page,'Ansicht');self.log=QPlainTextEdit();self.log.setReadOnly(True);self.tabs.addTab(self.log,'Protokoll')
        split.setSizes([230,910,330]);split.setStretchFactor(1,1)
        self.navigation_timer=QTimer(self);self.navigation_timer.setSingleShot(True);self.navigation_timer.setInterval(80);self.navigation_timer.timeout.connect(self.load_digimon)
        self.loader=ConversionQueue();self.loader.ready.connect(self.model_ready);self.loader.failed.connect(self.model_failed);self.loader.start()
        self.language_combo.currentIndexChanged.connect(self.change_language);self.retranslate_ui();self.update_actions()
    def t(self, source, **fields):
        return translate(source, self.language, **fields)

    def change_language(self, index):
        new_language=self.language_combo.itemData(index)
        if new_language not in ('de','en'):return
        self.language=new_language
        self.settings.setValue('language', self.language)
        self.retranslate_ui()

    def retranslate_ui(self):
        """Translate widgets in place without rebuilding the VTK render window.

        Original German captions are captured once, so changing the language
        never resets selected Digimon, camera settings, textures or animations.
        Dynamic status text is left intact unless it is a known static caption.
        """
        self.setWindowTitle(self.t('DW2 · 3D Viewer v4.0'))
        if hasattr(self, 'viewer'):
            self.viewer.ui_language=self.language
        for widget in self.findChildren(QWidget):
            if isinstance(widget, QGroupBox):
                source=getattr(widget, '_lang_title', None)
                if source is None:
                    source=widget.title();widget._lang_title=source
                widget.setTitle(self.t(source))
            elif isinstance(widget, (QLabel,QPushButton,QCheckBox)):
                source=getattr(widget, '_lang_caption', None)
                if source is None:
                    source=widget.text();widget._lang_caption=source
                live=getattr(widget,'_live_translation',None)
                if live:
                    widget.setText(self.t(live[0],**live[1]))
                elif widget.text() in (source, translate(source, 'en')):
                    widget.setText(self.t(source))
            if isinstance(widget,QLineEdit):
                source=getattr(widget,'_lang_placeholder',None)
                if source is None:
                    source=widget.placeholderText();widget._lang_placeholder=source
                widget.setPlaceholderText(self.t(source))
            if isinstance(widget,QComboBox):
                # Fixed option labels may be translated; dynamically added
                # model names are preserved because they are not in the glossary.
                sources=getattr(widget,'_lang_choices',None)
                if sources is None or len(sources)!=widget.count():
                    sources=[widget.itemText(i) for i in range(widget.count())]
                    widget._lang_choices=sources
                for i,original in enumerate(sources):
                    if original in ('Deutsch','Englisch') or translate(original,'en')!=original:
                        widget.setItemText(i,self.t(original))
            if hasattr(widget,'toolTip'):
                source=getattr(widget,'_lang_tooltip',None)
                if source is None:
                    source=widget.toolTip();widget._lang_tooltip=source
                if source:
                    widget.setToolTip(self.t(source))
        for i,label in enumerate(('Änderungen','Texturen','Ansicht','Protokoll')):self.tabs.setTabText(i,self.t(label))
        if hasattr(self.viewer,'refresh_language'):
            self.viewer.refresh_language(self.language)
        self.statusBar().showMessage(self.t('Bereit · DW2 3D Viewer'))

    def set_localized_text(self, widget, source, **fields):
        """Keep dynamically formatted status labels current when locale changes."""
        widget._live_translation=(source,fields)
        widget.setText(self.t(source,**fields))

    def write_log(self,message):self.log.appendPlainText(str(message))

    def warning(self,title,exc):
        title=self.t(title)
        explanation=self.t(str(exc))
        self.write_log(f'{title}: {explanation}')
        self._show_message(QMessageBox.Icon.Warning,title,explanation)

    def inform(self,title,message):
        self._show_message(QMessageBox.Icon.Information,self.t(title),self.t(message))

    def _show_message(self,kind,title,message):
        box=QMessageBox(self)
        box.setIcon(kind)
        box.setWindowTitle(title)
        box.setText(message)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.button(QMessageBox.StandardButton.Ok).setText(self.t('OK'))
        box.exec()

    def ask(self,title,message,buttons,default):
        # Explicit button captions: switching the UI language also affects
        # Yes/No/Cancel even if the Windows system locale is different.
        box=QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(self.t(title))
        box.setText(self.t(message))
        box.setStandardButtons(buttons)
        box.setDefaultButton(default)
        for code,text in ((QMessageBox.StandardButton.Yes,'Ja'),
                          (QMessageBox.StandardButton.No,'Nein'),
                          (QMessageBox.StandardButton.Cancel,'Abbrechen')):
            button=box.button(code)
            if button is not None: button.setText(self.t(text))
        return QMessageBox.StandardButton(box.exec())

    def _log_skipped_references(self,model):
        try:
            import json
            info=json.loads((Path(model).parent/'model_import.json').read_text(encoding='utf-8'))
            for name in info.get('skipped_references',[]):
                self.write_log(self.t('Hinweis: Referenzierte Datei nicht gefunden und übersprungen: {name}',name=name))
        except (OSError,ValueError):pass

    def export_model(self):
        if not self.project_model:return self.warning('Kein Modell','Bitte zuerst ein Modell öffnen.')
        model=self.project_model
        filt=supported_export_filters()
        if self.language=='en':
            filt=(filt.replace('Animationen erhalten','animations preserved')
                      .replace('statisch, ohne Animationen','static, no animations'))
        name,selected_filter=QFileDialog.getSaveFileName(self,self.t('Modell exportieren'),str(Path.home()/(model.stem+model.suffix)),filt)
        if not name:return
        try:
            dest=Path(name)
            if dest.resolve()==model.resolve():raise ValueError('Original-/Projektdatei bitte nicht überschreiben.')
            if dest.suffix.lower() not in {'.gltf','.glb','.obj'}:
                ext='.gltf' if '(*.gltf)' in selected_filter else '.glb' if '(*.glb)' in selected_filter else '.obj'
                dest=dest.with_suffix(ext)
            payload=self.transfer_export_payload() if dest.suffix.lower() in ('.gltf','.glb') else None
            if payload is not None:
                from dw2studio.core.digimon_transfer import export_exchange
                export_exchange(model,dest,payload)
            elif dest.suffix.lower()=='.glb' and model.suffix.lower()=='.glb':
                import shutil;shutil.copy2(model,dest)
            else:export_model(model,dest)
            if payload is not None:
                self.write_log('Modell, Texturen und native A–K-Animationen als Austauschdaten eingebettet.')
            self.write_log(self.t('3D exportiert: {path}',path=dest))
        except Exception as e:self.warning('Export fehlgeschlagen',e)

    def _confirm_native_colors(self, info, png, *, eye_frames=False, palette_mode='v31'):
        """Compare source PNG against *encoded and re-decoded* PS1 pixels.

        This is deliberately checked BEFORE allocating/copying a 460 MB image.
        No image is written until the user sees and accepts the PS1 result.
        """
        from PIL import Image
        from io import BytesIO
        from dw2studio.assets.tim import TIM
        from dw2studio.core.dw2_native_atlas import is_native_dw2_tim
        tim = TIM(info.native_bytes[info.region.offset:])
        if not is_native_dw2_tim(tim):
            return True  # Generic TIMs have their own fixed-layout encoder.
        from dw2studio.core.dw2_palette_recolor import preview_native_texture
        with Image.open(png) as image:
            desired = image.convert('RGBA').copy()
        from dw2studio.core.dw2_palette_recolor import native_edit_report
        skipped = native_edit_report(info.native_bytes, info.region.offset,
                                     desired, eye_frames=eye_frames)
        native_bytes, encoded, quality = preview_native_texture(
            info.native_bytes, info.region.offset, desired, recolor=True, eye_frames=eye_frames, palette_mode=palette_mode
        )
        if native_bytes == tim.data[:tim.end]:
            raise ValueError(self.t(
                'Die PNG enthält keine wirksamen Änderungen an den Körper- oder Augenflächen. '
                'Änderungen außerhalb dieser Flächen bzw. in den unteren 32 Palette-Zeilen '
                'werden aus Sicherheitsgründen nicht ins Spiel geschrieben.'))
        # The original is displayed for context; the image on the right is
        # always decoded from the *actual* bytes that would go into the BIN.
        from dw2studio.core.dw2_native_atlas import decode_native_atlas
        original = decode_native_atlas(info.native_bytes, info.region.offset,include_eye_frames=eye_frames)
        dlg = QDialog(self)
        dlg.setWindowTitle(self.t('Native DW2-Textur – Vorschau vor dem Vormerken'))
        available=self.screen().availableGeometry()
        dlg.resize(min(980,max(620,available.width()-40)),min(900,max(500,available.height()-60)))
        outer=QVBoxLayout(dlg);scroll=QScrollArea();scroll.setWidgetResizable(True)
        body=QWidget();layout=QVBoxLayout(body);scroll.setWidget(body);outer.addWidget(scroll,1)
        comparison_note=QLabel(self.t(
            'Vergleich: Original / bearbeitete PNG / tatsächliches PS1-Ergebnis. '
            'Die PlayStation unterstützt nur 16 Farben pro Teilpalette.'))
        comparison_note.setWordWrap(True);layout.addWidget(comparison_note)
        mode_labels={'v31':'wie v3.1 – Index-Rekolorierung / Median-Cut, kleinere Gesamtabweichung gewinnt','protect':'kleine bearbeitete Farbbereiche schützen; zusätzliche Annäherung möglich','exact':'exakte RGB555-Farben, ohne weitere Reduktion'}
        mode_note=QLabel('Farbmodus: '+mode_labels[palette_mode])
        mode_note.setWordWrap(True);layout.addWidget(mode_note)
        pictures = QHBoxLayout()
        for title, image in (
            (self.t('Original im Spiel'), original),
            (self.t('Deine bearbeitete PNG'), desired),
            (self.t('Erwartetes Ergebnis im Spiel'), encoded),
        ):
            column = QVBoxLayout()
            name = QLabel(title)
            name.setAlignment(Qt.AlignmentFlag.AlignHCenter);name.setWordWrap(True)
            column.addWidget(name)
            io = BytesIO()
            image.save(io, 'PNG')
            pix = QPixmap()
            if not pix.loadFromData(io.getvalue(), 'PNG'):
                raise RuntimeError('Native Farb-Vorschau konnte nicht erzeugt werden.')
            tile = QLabel()
            tile.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            preview_width=max(128,min(256,(available.width()-140)//3))
            tile.setPixmap(pix.scaled(preview_width, preview_width*2, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.FastTransformation))
            column.addWidget(tile)
            pictures.addLayout(column)
        layout.addLayout(pictures)
        if skipped.palette_storage_ignored or skipped.unmapped_texture_ignored:
            skipped_note = QLabel(self.t(
                'Hinweis: {locked} geänderte Pixel in den unteren 32 Paletten-Zeilen '
                'und {unmapped} Pixel außerhalb gültiger Modell-/Augenflächen '
                'werden bewusst ignoriert. Sie sind im nativen DW2-Format nicht '
                'als normale Textur beschreibbar. Maßgeblich ist die rechte PS1-Vorschau.',
                locked=skipped.palette_storage_ignored,
                unmapped=skipped.unmapped_texture_ignored))
            skipped_note.setWordWrap(True)
            skipped_note.setStyleSheet('color: #f3c875; padding: 8px;')
            layout.addWidget(skipped_note)
        details = QLabel(self.t(
            'Mittlerer Farbfehler: {error}/255 | Starke Farbabweichungen: {bad:.1%} '
            '| Geänderte Paletten: {palettes} | Neue Palettenfarben: {colors}',
            error=quality.mean_rgb_error, bad=quality.bad_pixel_fraction,
            palettes=quality.palettes_rewritten, colors=quality.colors_rewritten,
        ))
        details.setWordWrap(True)
        layout.addWidget(details)
        edited_details=QLabel(f'Bearbeitete Pixel: {quality.edited_pixels_checked} | Farbfehler dort: {quality.edited_mean_rgb_error}/255 | Starke Abweichungen dort: {quality.edited_bad_pixel_fraction:.1%} | Entfärbte bearbeitete Pixel: {quality.edited_chroma_lost}')
        edited_details.setWordWrap(True);layout.addWidget(edited_details)
        if palette_mode=='v31' and (quality.edited_chroma_lost or quality.edited_mean_rgb_error>18 or quality.edited_bad_pixel_fraction>.10):
            local_note=QLabel('Einzelne bearbeitete Bereiche weichen deutlich ab. Die Vorschau wird wie in v3.1 trotzdem angeboten. Bei entfärbten Augen gegebenenfalls den Modus Farbschutz wählen. Nur übernehmen, wenn das rechte Bild passt.')
            local_note.setWordWrap(True);local_note.setStyleSheet('color: #f3c875;');layout.addWidget(local_note)
        layout.addWidget(QLabel(self.t(
            'Nur fortfahren, wenn die rechte Vorschau deinen gewünschten Farben entspricht. '
            'Die Original-BIN bleibt unverändert.')))
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.t('Farben stimmen – vormerken'))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.t('Abbrechen'))
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        outer.addWidget(buttons)
        return dlg.exec() == QDialog.DialogCode.Accepted

    def key_for(self,c):return f'{c.id:03d}{c.code}'
    def current_key(self):return self.key_for(self.current) if self.current else None
    def eventFilter(self,obj,event):
        if obj is self.digimon and event.type()==QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Up,Qt.Key.Key_Down):self.navigation_timer.start()
            elif event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):self.load_digimon();return True
        return super().eventFilter(obj,event)
    def choose_image(self):
        if self.writer and self.writer.isRunning():return
        if self.session and self.session.edits and self.ask('Ungespeicherte Änderungen','Image wechseln und vorgemerkte Änderungen verwerfen?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        if self.reader and self.reader.isRunning():return
        path,_=QFileDialog.getOpenFileName(self,'Spiel-Image öffnen','','PlayStation-Image (*.bin *.iso *.cue *.img *.ccd)')
        if not path:return
        self.loader.clear();self.navigation_timer.stop();self._opening_source=path;self.open_image.setEnabled(False);self.disc_status.setText('Image-Dateien werden eingelesen …')
        self.reader=DiscReader(path,CACHE);self.reader.done.connect(self.image_loaded);self.reader.failed.connect(self.scan_failed);self.reader.start()
    def scan_failed(self,reason):self.open_image.setEnabled(True);self.warning('Image konnte nicht gelesen werden',reason)
    def image_loaded(self,entries,catalog,info):
        if self._closing:return
        self.image=getattr(self,'_opening_source',info['path']);self.image_path=Path(info['path']);self.index_key=info['cache_key'];self.session=EditSession(self.image_path,info['sector_size']);self.entries=entries;self.catalog=catalog;self.current=None;self.loaded_digimon=None;self.active_digimon_key=None;self.active_native=False;self.project_model=None;self.display_model=None;self.model_paths.clear();self.raw_models.clear();self.revisions.clear();self.wanted=None
        self.name_repository=None;self.rgb_namespace=self.index_key;self._source_names={c.id:c.name for c in self.catalog}
        if info.get('name_error'):self.write_log('Namenstabelle: '+info['name_error'])
        self.open_image.setEnabled(True);self.refresh_list();self.update_pending();self.viewer.clear_scene('Digimon per Doppelklick öffnen') if hasattr(self.viewer,'clear_scene') else None
        self.disc_status.setText(f'{Path(self.image).name}\n{len(catalog)} Digimon · {"gespeicherter Index" if info["cached"] else "neu analysiert"} · {info["seconds"]:.2f} s');self.update_actions()
    def refresh_list(self):
        previous=self.current_key();term=self.search.text().lower().strip();self.visible=[c for c in self.catalog if term in f'{c.id:03} {c.code} {c.name}'.lower()]
        self.digimon.blockSignals(True);self.digimon.clear()
        for c in self.visible:self.digimon.addItem(f'#{c.id:03}   {c.name}   · {c.code}')
        self.digimon.blockSignals(False)
        if self.visible:self.digimon.setCurrentRow(next((i for i,c in enumerate(self.visible) if self.key_for(c)==previous),0))
        else:self.current=None;self.wanted=None;self.navigation_timer.stop();self.model_status.setText('Kein Digimon gefunden');self.update_actions()
    def select_digimon(self,index):
        self.current=self.visible[index] if 0<=index<len(self.visible) else None
        if self.current:self.model_status.setText(f'{self.current.name} ausgewählt · Doppelklick oder ↑ / ↓ öffnet das Modell')
        self.refresh_attack_summary()
        self.refresh_type_summary()
        self.update_actions()
    def files_for(self,c):
        unique={}
        for entry in selected_model_entries(self.entries,c):unique[(entry.lba,entry.size,Path(entry.path.replace('\\','/')).name.upper())]=entry
        return list(unique.values())
    def request_for(self,c):
        key=self.key_for(c);revision=self.revisions.get(key,0);folder=CACHE/'models'/self.index_key/key
        files=self.files_for(c);overrides={}
        for e in files:
            edit=self.session.edits.get((e.path,e.lba))
            if edit:overrides[Path(e.path.replace('\\','/')).name]=edit.replacement
        if overrides:
            # A revision counter restarts each session. Reusing edits/1 could
            # therefore show last session's texture after a different import.
            import hashlib
            digest=hashlib.sha256()
            for name,data in sorted(overrides.items()):
                encoded=name.encode('utf-8');digest.update(len(encoded).to_bytes(4,'little'));digest.update(encoded)
                digest.update(len(data).to_bytes(8,'little'));digest.update(data)
            folder=folder/'edits'/digest.hexdigest()
        return ModelRequest(f'{self.index_key}/{key}/{revision}',str(self.image_path),files,folder,c,str(find_converter() or ''),overrides)
    def load_digimon(self):
        self.navigation_timer.stop()
        if not self.current or not self.session or self._closing:return
        c=self.current;key=self.key_for(c);request=self.request_for(c);self.wanted=request.key
        try:self.session._check_source()
        except Exception as exc:self.warning('Image verändert',exc);return
        replacement=active_replacement(self._rgb_root()/key)
        if replacement:self.display_for(c,replacement,native=False);return
        path=self.model_paths.get(key)
        if path and Path(path).is_file():self.display_for(c,path,native=True);return
        if not self.revisions.get(key,0):
            replacement=active_replacement(CACHE/'replacements'/cache_key(self.image)/key)
            if replacement:self.display_for(c,replacement,native=False);return
        found=candidate_models(request.folder/'converted',c)
        if not found and not self.revisions.get(key,0):
            # Reuse earlier standalone caches made from the CUE path itself.
            old=CACHE/'models'/cache_key(self.image)/key/'converted';found=candidate_models(old,c)
        if found:
            try:
                if found[0].suffix.lower()=='.gltf':__import__('json').loads(found[0].read_text(encoding='utf-8'))
                self.model_paths[key]=found[0];self.display_for(c,found[0],native=True);return
            except (OSError,ValueError):pass
        if not request.converter:return self.warning('Konverter fehlt','dw2_model_converter.exe nicht gefunden.')
        self.model_status.setText(f'{c.name} · Modell wird vorbereitet …');self.update_actions(loading=True);self.loader.submit(request)
    def model_ready(self,key,path,seconds):
        if self._closing or not self.index_key or not key.startswith(self.index_key+'/'):return
        parts=key.split('/');model_key=parts[-2];revision=int(parts[-1])
        if revision!=self.revisions.get(model_key,0):return
        self.model_paths[model_key]=Path(path);self.write_log(f'{model_key}: Konvertierung {seconds:.3f} s')
        if self.wanted==key and self.current and self.current_key()==model_key:
            rgb=active_replacement(self._rgb_root()/model_key)
            self.display_for(self.current,rgb or Path(path),native=rgb is None)
    def model_failed(self,key,reason):
        if key==self.wanted and not self._closing:self.update_actions(loading=True);self.warning('Modell konnte nicht vorbereitet werden',reason)
    def display_for(self,c,path,native):
        self.loaded_digimon=c;self.active_digimon_key=self.key_for(c);self.active_native=native
        if self.load_model(path):
            self.update_actions();self.digimon.setFocus(Qt.FocusReason.OtherFocusReason);self.prefetch_neighbors()
        else:
            self.project_model=None;self.display_model=None;self.active_native=False;self.loaded_digimon=None;self.update_actions()
    def load_model(self,path):
        path=Path(path);started=time.perf_counter()
        try:
            display=path
            if path.suffix.lower() in ('.obj','.stl') and VTK_AVAILABLE:
                import trimesh
                from dw2studio.renderer.scene_cache import scene_key
                signature=str(scene_key(path));tag=__import__('hashlib').sha256(signature.encode()).hexdigest()[:16];folder=CACHE/'external_previews';folder.mkdir(parents=True,exist_ok=True);display=folder/(tag+'.glb')
                if not display.exists():display.write_bytes(trimesh.load(str(path),force='scene',process=False).export(file_type='glb'))
            self.viewer.load(str(display));self.project_model=path;self.display_model=display;self.model_label.setText(path.name);self.texture_combo.clear()
            for name,_ in texture_slots(path):self.texture_combo.addItem(name)
            kind='RAM-Szene' if getattr(self.viewer,'last_load_cache_hit',False) else 'Datei'
            self.model_status.setText(f'{self.loaded_digimon.name if self.loaded_digimon else path.name} · {kind} · {time.perf_counter()-started:.3f} s'+(' · native Fassung' if self.active_native else ' · Vollfarben-Viewer-Modell'))
            self.write_log('Geladen: '+str(path));self.update_actions()
            if self.active_native:self.start_eyes()
            return True
        except Exception as exc:self.warning('3D-Modell konnte nicht geladen werden',exc);return False
    def prefetch_neighbors(self):
        if not self.prefetch.isChecked() or not self.current or not self.image:return
        row=self.digimon.currentRow()
        for index in (row+1,row-1):
            if not 0<=index<len(self.visible):continue
            c=self.visible[index];key=self.key_for(c)
            if key in self.model_paths:continue
            request=self.request_for(c)
            if request.converter:self.loader.submit(request,foreground=False)
    def start_eyes(self):
        if not VTK_AVAILABLE or getattr(self.viewer,'_eye_player',None) is not None:return
        try:
            entry=native_model_entry(self.entries,self.loaded_digimon);key=self.request_for(self.loaded_digimon).key
            edit=self.session.edits.get((entry.path,entry.lba));data=edit.replacement if edit else self.raw_models.get((entry.path,entry.lba))
            if any(job.key==key and job.isRunning() for job in self.eye_jobs):return
            job=EyePreparation(key,str(self.image_path),entry,data);self.eye_jobs.append(job);job.ready.connect(self.eyes_ready);job.failed.connect(lambda key,reason:self.write_log('Augenvorschau: '+reason));job.start()
        except Exception as exc:self.write_log('Augenvorschau: '+str(exc))
    def eyes_ready(self,key,data,layout,frames):
        if key!=self.wanted or not self.active_native or self._closing:return
        entry=native_model_entry(self.entries,self.loaded_digimon);self.raw_models[(entry.path,entry.lba)]=data
        if layout and frames:
            try:self.viewer.enable_native_eye_blink(data,layout=layout,frames=frames)
            except Exception as exc:self.write_log('Augenvorschau: '+str(exc))
        self.eye_jobs=[job for job in self.eye_jobs if job.isRunning()]
    def update_actions(self,loading=False):
        self.type_button.setEnabled(self.session is not None and self.current is not None and not self._closing)
        if not self.session or not self.current:self.type_summary.setText('Typ: Spiel-Image und Digimon wählen')
        self.attack_button.setEnabled(self.session is not None and self.current is not None and not self._closing)
        if not self.session or not self.current:self.attack_summary.setText('Spiel-Image und Digimon wählen')
        self.rename_button.setEnabled(self.session is not None and self.current is not None and not self._closing)
        self.replace_digimon_button.setEnabled(self.session is not None and self.current is not None and not self._closing)
        valid=self.project_model is not None and not loading and (self.loaded_digimon is None or self.active_digimon_key==self.current_key())
        for button in self.model_buttons:button.setEnabled(valid)
        native=valid and self.session is not None and self.loaded_digimon is not None
        for i in (2,4):self.model_buttons[i].setEnabled(native)
        for button in self.texture_buttons:button.setEnabled(valid)
        for button in self.native_texture_buttons:button.setEnabled(native)
    def get_name_repository(self):
        if not self.session:raise ValueError('Bitte zuerst ein Spiel-Image öffnen.')
        if self.name_repository is None or self.name_repository.session is not self.session:
            self.name_repository=NameRepository(self.session,self.entries)
        return self.name_repository
    def get_attack_repository(self):
        if not self.session:raise ValueError('Bitte zuerst ein Spiel-Image öffnen.')
        repository=getattr(self,'attack_repository',None)
        if repository is None or repository.session is not self.session:
            self.attack_repository=AttackRepository(self.session,self.entries)
        return self.attack_repository
    def get_type_repository(self):
        if not self.session:raise ValueError('Bitte zuerst ein Spiel-Image öffnen.')
        repository=getattr(self,'type_repository',None)
        if repository is None or repository.session is not self.session:
            self.type_repository=TypeRepository(self.session,self.entries)
        return self.type_repository
    def refresh_type_summary(self):
        if not self.session or not self.current:
            self.type_summary.setText('Typ: Spiel-Image und Digimon wählen');return
        try:
            repository=self.get_type_repository();entry=repository.entry
            token=(self.session,self.session.edits.get((entry.path,entry.lba)))
            if getattr(self,'_type_summary_token',None)!=token:
                table=repository.table()
                self._type_summary_types={i:table.type_of(i) for i in table.records}
                self._type_summary_token=token
            code=self._type_summary_types.get(self.current.id)
            self.type_summary.setText('Typ: '+(type_name(code) if code is not None else 'kein Basiseintrag'))
            self.type_summary.setToolTip('Digimon-Typ aus dem geöffneten Image einschließlich vorgemerkter Änderungen.')
        except (ValueError,OSError) as exc:
            self.type_summary.setText('Typ: nicht lesbar');self.type_summary.setToolTip(str(exc))
    def change_digimon_type(self):
        if not self.current or not self.session:return
        if self.reader and self.reader.isRunning():return self.inform('Typ ändern','Bitte das Einlesen des Images abwarten.')
        try:
            from dw2studio.gui.type_dialog import TypeDialog
            c=self.current;repository=self.get_type_repository()
            dialog=TypeDialog(c.id,c.name,repository.table(),repository.original_type(c.id),repository.entry.path,self)
            self.type_dialog=dialog
            if dialog.exec()!=QDialog.DialogCode.Accepted:return
            self.apply_digimon_type(c.id,dialog.new_type)
        except Exception as exc:self.warning('Typ konnte nicht geändert werden',exc)
    def apply_digimon_type(self,identifier,new_type):
        changed=self.get_type_repository().change(identifier,new_type)
        self.update_pending();self.refresh_type_summary()
        if changed:
            self.model_status.setText(f'Typ #{identifier:03} vorgemerkt: {type_name(new_type)} · Image zum Übernehmen exportieren oder speichern.')
            self.write_log(f'Typ #{identifier:03} → {type_name(new_type)}; noch nicht ins Image geschrieben.')
        return changed
    def refresh_attack_summary(self):
        if not self.session or not self.current:
            self.attack_summary.setText('Spiel-Image und Digimon wählen');return
        # One small native-table read per session/revision, not per arrow key.
        token=(self.session,tuple(e for e in self.session.edits.values() if basename(e.path) in ATTACK_FILE_INDEX))
        if getattr(self,'_attack_summary_token',None)!=token:
            names={};reason=''
            try:
                skills,base,_=self.get_attack_repository().tables()
                names={identifier:(skill_label(skills.records[skill]) if skill in skills.records else f'{skill:02X} · unbekannte Technik · MP/AP unbekannt') for identifier,(_,skill) in base.records.items()}
            except (ValueError,OSError) as exc:reason=str(exc)
            self._attack_summary_token=token;self._attack_summary_names=names;self._attack_summary_error=reason
        found=self._attack_summary_names.get(self.current.id)
        self.attack_summary.setText(f'Standard: {found}' if found else 'Standardtechnik: im Attackeneditor prüfen')
        self.attack_summary.setToolTip(self._attack_summary_error or 'Standardtechnik aus dem geöffneten Image einschließlich vorgemerkter Änderungen. Gegner können je Begegnung weitere Techniken besitzen.')
    def edit_attacks(self):
        if not self.current or not self.session:return
        if self.reader and self.reader.isRunning():return self.inform('Attacken bearbeiten','Bitte das Einlesen des Images abwarten.')
        try:
            from dw2studio.gui.attack_dialog import AttackDialog
            c=self.current;repository=self.get_attack_repository()
            dialog=AttackDialog(c.id,c.name,repository,self.catalog,self);self.attack_dialog=dialog
            if dialog.exec()!=QDialog.DialogCode.Accepted:return
            self.apply_attack_plan(dialog.plan())
        except Exception as exc:self.warning('Attacken konnten nicht geändert werden',exc)
    def apply_attack_plan(self,plan):
        count=self.get_attack_repository().apply(plan)
        self.update_pending()
        self.refresh_attack_summary()
        if count:
            self.model_status.setText(f'Attacken #{plan.identifier:03} vorgemerkt · {count} native Datei(en). Image zum Übernehmen exportieren oder speichern.')
            self.write_log(f'Attacken #{plan.identifier:03}: Standard-/Gegnerzuordnung und globale Technikwerte vorgemerkt. Gespeicherte Lernplätze bleiben im Spielstand.')
        return count
    def refresh_names(self):
        if not self.session:return
        names=self.get_name_repository().names()
        for c in self.catalog:c.name=names.get(c.id,self._source_names.get(c.id,c.name))
        if self.loaded_digimon:
            match=next((c for c in self.catalog if self.key_for(c)==self.active_digimon_key),None)
            if match:self.loaded_digimon=match
        selected=self.current
        if selected and self.search.text().strip().lower() not in f'{selected.id:03} {selected.code} {selected.name}'.lower():
            self.search.blockSignals(True);self.search.clear();self.search.blockSignals(False)
        self.refresh_list()
    def rename_digimon(self):
        if not self.current or not self.session:return
        if self.reader and self.reader.isRunning():return self.inform('Namen ändern','Bitte das Einlesen des Images abwarten.')
        try:
            from dw2studio.gui.name_dialog import RenameDialog
            c=self.current;repository=self.get_name_repository();entry,table=repository.lookup(c.id)
            dialog=RenameDialog(c.id,table,entry.path,repository.original_name(c.id),self)
            self.name_dialog=dialog
            if dialog.exec()!=QDialog.DialogCode.Accepted:return
            self.apply_digimon_name(c.id,dialog.new_name)
        except Exception as exc:self.warning('Name konnte nicht geändert werden',exc)
    def apply_digimon_name(self,identifier,text):
        repository=self.get_name_repository();before=self.session.edits.copy()
        try:
            changed=repository.rename(identifier,text)
            self.refresh_names()
        except Exception:
            self.session.edits=before;raise
        self.update_pending()
        if changed:
            self.model_status.setText(f'Name #{identifier:03} vorgemerkt: {text} · Image zum Übernehmen exportieren oder speichern.')
            self.write_log(f'Nativer Name #{identifier:03} → {text}; noch nicht ins Image geschrieben.')
        return changed
    def _rgb_root(self):
        namespace=self.rgb_namespace or self.index_key or 'freie_modelle'
        return CACHE/'replacements'/namespace
    def _replacement_root(self):return self._rgb_root()/(self.active_digimon_key or '000FREE')
    def rgb_models(self):
        from dw2studio.core.rgb_project import list_rgb_models
        return list_rgb_models(self._rgb_root(),[self.key_for(c) for c in self.catalog]+['000FREE'])
    def save_rgb_project(self):
        models=self.rgb_models()
        if not models:return self.inform('Vollfarben-Projekt','Zuerst eine PNG als Vollfarbtextur ersetzen.')
        filename,_=QFileDialog.getSaveFileName(self,'Vollfarben-Viewer-Projekt speichern','dw2_vollfarben.dw2rgb','Viewer-Projekt (*.dw2rgb)')
        if filename:
            try:
                from dw2studio.core.rgb_project import save_rgb_project
                save_rgb_project(filename,models);self.write_log('Vollfarben-Projekt gespeichert: '+filename)
            except Exception as exc:self.warning('Viewer-Projekt speichern',exc)
    def load_rgb_project(self):
        filename,_=QFileDialog.getOpenFileName(self,'Vollfarben-Viewer-Projekt laden','','Viewer-Projekt (*.dw2rgb)')
        if filename:
            try:
                from dw2studio.core.rgb_project import load_rgb_project
                loaded=load_rgb_project(filename,self._rgb_root(),{self.key_for(c) for c in self.catalog}|{'000FREE'})
                self.update_pending()
                if self.current:self.load_digimon()
                elif '000FREE' in loaded:
                    self.loaded_digimon=None;self.active_digimon_key=None;self.active_native=False;self.load_model(loaded['000FREE'])
            except Exception as exc:self.warning('Viewer-Projekt laden',exc)
    def import_free_model(self):self.import_model(force_free=True)
    def transfer_export_payload(self):
        from dw2studio.core.digimon_transfer import make_payload,read_transfer,role,KEY
        if self.active_native and self.session and self.loaded_digimon:
            if self.active_digimon_key!=self.current_key():raise ValueError('Bitte das zu exportierende Quell-Digimon zuerst öffnen.')
            files={}
            for entry in self.files_for(self.loaded_digimon):
                r=role(entry);data=self.session.current(entry)
                if r in files and files[r]!=data:raise ValueError('Mehrdeutige Quell-Dateirolle: '+r)
                files[r]=data
            return make_payload(self.loaded_digimon,files)
        if self.project_model and Path(self.project_model).suffix.lower() in ('.gltf','.glb'):
            from dw2studio.core.gltf_document import read_document
            extras=read_document(self.project_model).get('extras',{})
            if isinstance(extras,dict) and KEY in extras:return read_transfer(self.project_model).payload
        return None
    def replace_digimon(self,checked=False,path=None):
        if not self.session or not self.current:return self.inform('Digimon ersetzen','Bitte ein Spiel-Image öffnen und links das zu ersetzende Ziel-Digimon auswählen.')
        if path is None:
            path,_=QFileDialog.getOpenFileName(self,'Exportiertes Digimon mit Animationen wählen','','DW2-Austauschmodell (*.glb *.gltf)')
        if not path:return
        try:
            from dw2studio.core.digimon_transfer import read_transfer,plan_transfer
            from dw2studio.gui.digimon_transfer_dialog import DigimonTransferDialog
            target=self.current
            plan=plan_transfer(read_transfer(path),self.files_for(target),self.session)
            dialog=DigimonTransferDialog(plan,target,self);self.transfer_dialog=dialog
            if dialog.exec()!=QDialog.DialogCode.Accepted:return
            if plan.errors:raise ValueError('\n'.join(plan.errors))
            # Stage all native companions atomically; then use the native
            # converter rather than the donor glTF as a target preview.
            self.stage_files(plan.changes,target,relocations=plan.relocated)
            self.write_log(f'Digimon-Ersatz vorgemerkt: {plan.transfer.source["name"]} → {target.name}; {len(plan.changes)} Datei(en).')
        except Exception as exc:self.warning('Digimon konnte nicht ersetzt werden',exc)
    def import_model(self,checked=False,force_free=False):
        path,_=QFileDialog.getOpenFileName(self,'3D-Datei importieren','','Modelle (*.obj *.gltf *.glb *.stl *.bin)')
        if not path:return
        try:
            if not force_free and self.current and self.session and Path(path).suffix.lower() in ('.gltf','.glb'):
                self.replace_digimon(path=path);return
            if not force_free and self.current and self.session and Path(path).suffix.lower()=='.obj':self.import_rigged(path);return
            if not force_free and self.current and self.session and Path(path).suffix.lower()=='.bin':
                from dw2studio.core.native_model import validate_replacement
                entry=native_model_entry(self.entries,self.current);data=self.session.current(entry)
                if Path(path).stat().st_size!=len(data):raise ValueError(f'Native BIN muss exakt {len(data)} Bytes haben.')
                self.stage_files([(entry,validate_replacement(data,Path(path).read_bytes()),'Native Modell-BIN')],self.current);return
            copied=create_workcopy(path,CACHE/'imports');self.loaded_digimon=None;self.active_digimon_key=None;self.active_native=False;self.wanted=None;self._log_skipped_references(copied);self.load_model(copied)
        except Exception as exc:self.warning('Import fehlgeschlagen',exc)
    def import_rigged(self,path):
        from dw2studio.core.rig_import import RigProject,ObjMesh
        from dw2studio.gui.rig_dialog import RigImportDialog
        c=self.current;entry=native_model_entry(self.entries,c);companions={}
        for e in self.files_for(c):
            if e.path==entry.path and e.lba==entry.lba:continue
            companions[Path(e.path.replace('\\','/')).name]=(e,self.session.current(e))
        project=RigProject(ObjMesh(path),self.session.current(entry),{name:data for name,(e,data) in companions.items()})
        dialog=RigImportDialog(project,CACHE/'rig_imports'/self.index_key/self.key_for(c),self);self.rig_dialog=dialog
        if dialog.exec()!=QDialog.DialogCode.Accepted:return
        staged=[(entry,dialog.native_result,'OBJ mit Knochenzuordnung')]
        for name,data in dialog.animation_results.items():
            e,original=companions[name]
            if data!=original:staged.append((e,data,'Animationskorrektur'))
        self.stage_files(staged,c,preview=dialog.preview_path)
    def stage_files(self,files,c,preview=None,relocations=()):
        before=self.session.edits.copy()
        try:
            for entry,data,label in files:
                if (entry.path,entry.lba) in relocations:self.session.stage(entry,data,label,relocate=True)
                else:self.session.stage(entry,data,label)
        except Exception:self.session.edits=before;raise
        key=self.key_for(c);clear_replacement(self._rgb_root()/key);self.revisions[key]=self.revisions.get(key,0)+1;self.model_paths.pop(key,None)
        self.raw_models={k:v for k,v in self.raw_models.items() if k not in {(entry.path,entry.lba) for entry,data,label in files}}
        if preview:self.model_paths[key]=preview
        self.update_pending();self.current=c;self.load_digimon()
    def _native_selection(self):
        if not self.session or not self.loaded_digimon:raise ValueError('Bitte zuerst ein Digimon aus dem Spiel-Image öffnen.')
        self.session._check_source();entry=native_model_entry(self.entries,self.loaded_digimon);edit=self.session.edits.get((entry.path,entry.lba));data=edit.replacement if edit else self.raw_models.get((entry.path,entry.lba))
        if data is None:data=self.session.current(entry);self.raw_models[(entry.path,entry.lba)]=data
        found=regions(data)
        if not found:raise ValueError('Kein nativer TIM-Block erkannt.')
        return NativeTextureInfo(entry,found[0],0,self.image_path,data)
    def export_native_tim(self,checked=False,eyes=False):
        try:
            info=self._native_selection();from_image=self.native_image(info,eyes)
            target,_=QFileDialog.getSaveFileName(self,'Native PNG exportieren',self.active_digimon_key+('_Augen.png' if eyes else '_Native.png'),'PNG (*.png)')
            if target:
                choices=[f'{k}× · {from_image.width*k}×{from_image.height*k}' for k in (1,2,3,4)]
                selected,ok=QInputDialog.getItem(self,'PNG-Vorlage exportieren','Arbeitsauflösung (Spiel bleibt nativ):',choices,0,False)
                if not ok:return
                from dw2studio.core.texture_resolution import export_template
                factor=choices.index(selected)+1;export_template(from_image,target,factor);self.write_log(f'PNG-Arbeitsvorlage {factor}× exportiert: '+target)
        except Exception as exc:self.warning('PNG-Export',exc)
    def export_eye_atlas(self):self.export_native_tim(eyes=True)
    def native_image(self,info,eyes=True):
        from dw2studio.assets.tim import TIM
        from dw2studio.core.dw2_native_atlas import decode_native_atlas,is_native_dw2_tim
        from dw2studio.core.dw2_eyes import eye_layout
        tim=TIM(info.native_bytes[info.region.offset:])
        return decode_native_atlas(info.native_bytes,info.region.offset,include_eye_frames=bool(eyes and eye_layout(info.native_bytes))) if is_native_dw2_tim(tim) else tim.to_image()
    def export_png(self):
        if self.active_native:self.export_native_tim(eyes=True);return
        if not self.project_model:return
        target,_=QFileDialog.getSaveFileName(self,'Modelltextur exportieren',self.project_model.stem+'.png','PNG (*.png)')
        if target:
            try:export_texture(self.project_model,self.texture_combo.currentIndex(),target)
            except Exception as exc:self.warning('PNG-Export',exc)
    def replace_png(self):
        if self.session and self.loaded_digimon:
            if self.active_digimon_key!=self.current_key():return
            self.import_native_png();return
        self.replace_preview_png()
    def replace_preview_png(self):
        if not self.project_model:return
        source,_=QFileDialog.getOpenFileName(self,'PNG ersetzen – unveränderte Farben und Auflösung','','PNG (*.png)')
        if source:
            try:self.apply_rgb_png(source,self.texture_combo.currentIndex())
            except Exception as exc:self.warning('PNG ersetzen',exc)
    def apply_rgb_png(self,source,slot=0):
        from dw2studio.core.png_source import verified_png
        _,info=verified_png(source)
        if not self.project_model:raise ValueError('Bitte zuerst ein Modell öffnen.')
        root=self._replacement_root();copy=create_workcopy(self.project_model,root)
        replace_texture(copy,slot,source)
        # The rendered workcopy, persisted registry and exports all point to
        # the same original PNG bytes, not to a palette-reduced surrogate.
        previous_native=self.active_native;previous_model=self.project_model;self.active_native=False
        if not self.load_model(copy):
            self.active_native=previous_native;self.load_model(previous_model);raise ValueError('Vollfarben-Modell konnte nicht angezeigt werden.')
        publish_replacement(copy,root);self.update_pending()
        size=info['size'];self.model_status.setText(f'PNG unverändert: {size[0]}×{size[1]} · Vollfarben im Viewer-Projekt · kein nativer PS1-Patch')
        self.write_log('Original-PNG als Vollfarbtextur gespeichert: '+str(source));return copy
    def write_game_eyes(self):self.import_native_png(eyes_only=True)
    def import_native_png(self,eyes_only=False):
        from PIL import Image
        try:
            info=self._native_selection();source,_=QFileDialog.getOpenFileName(self,'PNG wählen (1×, 2×, 3× oder 4×) – native Änderung vormerken','','PNG (*.png)')
            if not source:return
            from dw2studio.core.dw2_eyes import eye_layout,infer_full_eye_atlas
            layout=eye_layout(info.native_bytes)
            from dw2studio.gui.texture_size_dialog import prepare_native_png
            incoming=prepare_native_png(source,(info.region.width,info.region.height),self)
            if incoming is None:return
            eye_frames=bool(layout and (eyes_only or infer_full_eye_atlas(info.native_bytes,incoming)))
            if eyes_only:
                if layout is None:raise ValueError('Keine sicheren Augenbereiche für dieses Modell.')
                if incoming.size!=(128,256):raise ValueError('Augenatlas muss exakt 128×256 Pixel haben.')
                masked=self.native_image(info,True)
                for x,y,w,h in set(layout.sources+(layout.target,)):masked.paste(incoming.crop((x,y,x+w,y+h)),(x,y))
                incoming=masked
            folder=CACHE/'native_imports';folder.mkdir(parents=True,exist_ok=True);prepared=folder/(uuid.uuid4().hex+'.png');incoming.save(prepared)
            try:
                palette_mode=self.palette_mode.currentData()
                if not self._confirm_native_colors(info,prepared,eye_frames=eye_frames,palette_mode=palette_mode):return
                changed,_=replace_tim(info.native_bytes,prepared,info.tim_index,recolor=True,eye_frames=eye_frames,palette_mode=palette_mode)
            finally:prepared.unlink(missing_ok=True)
            if changed==info.native_bytes:self.model_status.setText('PNG enthält keine wirksame Änderung.');return
            self.stage_files([(info.entry,changed,'Augen vollständig ersetzt' if eyes_only else 'Native PNG inkl. erkannter Augen')],self.loaded_digimon)
        except Exception as exc:self.warning('Native PNG',exc)
    def restore_original(self):
        if not self.loaded_digimon or not self.session:return
        c=self.loaded_digimon;files=self.files_for(c);keys={(e.path,e.lba) for e in files}
        if any(key in self.session.edits for key in keys) and self.ask('Original wiederherstellen','Modell- und Animationsänderungen für dieses Digimon verwerfen?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        for key in keys:self.session.remove(key)
        clear_replacement(self._replacement_root());key=self.key_for(c);self.revisions.pop(key,None);self.model_paths.pop(key,None);self.current=c;self.raw_models.clear();self.update_pending();self.load_digimon()
    def update_pending(self):
        self.pending.clear();edits=list(self.session.edits.values()) if self.session else []
        for e in edits:
            label=e.label;detail=e.label
            if basename(e.path) in FILE_INDEX:
                try:
                    old,new=NameTable(e.original),NameTable(e.replacement)
                    changes=[f'#{i:03}: {r.text} → {new.record(i).text}' for i,r in old.records.items() if new.record(i).text!=r.text]
                    if changes:label=f'{len(changes)} Name(n) vorgemerkt';detail='\n'.join(changes)
                except ValueError:pass
                detail+='\nVerwerfen setzt alle Namen dieser Datei zurück. Einzelne Namen über Namen ändern zurücksetzen.'
            if e.relocate:label+=' · neuer Dateibereich';detail+='\nDateiverlagerung: Lade- und ISO-Verweise werden beim Image-Speichern aktualisiert.'
            if basename(e.path) in ATTACK_FILE_INDEX:detail+='\nGemeinsame Tabelle: Verwerfen setzt ALLE vorgemerkten Typ-/Attackenänderungen dieser Datei zurück. Einzelne Typen über Typ ändern wiederherstellen; einzelne Attacken im Attackeneditor zurücksetzen.'
            item=QListWidgetItem(f'{Path(e.path).name}\n{label}');item.setToolTip(detail);item.setData(Qt.ItemDataRole.UserRole,(e.path,e.lba));self.pending.addItem(item)
            if 'Digimon ersetzt: ' in e.label:item.setToolTip(detail+'\nVerwerfen setzt Modell und alle Animationen dieses Digimon zusammen zurück.')
        rgb=self.rgb_models()
        for key,path in rgb.items():
            item=QListWidgetItem(f'{key} · Vollfarben-Modell');item.setData(Qt.ItemDataRole.UserRole,('fullcolor',key));item.setToolTip('Unveränderte PNG-Dateien im Viewer-Projekt. Über Vollfarben-Projekt oder 3D-Modell exportieren.');self.pending.addItem(item)
        self.pending_status.setText(f'{len(edits)} native Datei(en) · {len(rgb)} Vollfarbmodell(e)')
    def discard_selected(self):
        item=self.pending.currentItem()
        if not item:return
        key=tuple(item.data(Qt.ItemDataRole.UserRole))
        if key[0]=='fullcolor':
            clear_replacement(self._rgb_root()/key[1]);self.update_pending()
            if self.current and self.current_key()==key[1]:self.load_digimon()
            return
        edit=self.session.edits.get(key)
        if edit and 'Digimon ersetzt: ' in edit.label:
            target=next((c for c in self.catalog if any((e.path,e.lba)==key for e in self.files_for(c))),None)
            if target is None:return self.warning('Änderung verwerfen','Die zusammengehörigen Digimon-Dateien konnten nicht eindeutig gefunden werden.')
            for entry in self.files_for(target):self.session.remove((entry.path,entry.lba))
            model_key=self.key_for(target);self.revisions[model_key]=self.revisions.get(model_key,0)+1;self.model_paths.pop(model_key,None);self.raw_models.clear();self.update_pending()
            if self.current and self.current_key()==model_key:self.load_digimon()
            return
        is_name=basename(key[0]) in FILE_INDEX
        if basename(key[0]) in ATTACK_FILE_INDEX:
            if self.ask('Typ-/Attackenänderungen verwerfen','Alle vorgemerkten Änderungen dieser gemeinsamen Typ-/Attackentabelle verwerfen? Einzelne Typen über Typ ändern wiederherstellen; einzelne Attacken im Attackeneditor zurücksetzen.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
            self.session.remove(key);self.update_pending();self.refresh_attack_summary();self.refresh_type_summary();return
        if is_name and self.ask('Namensänderungen verwerfen','Alle vorgemerkten Namen dieser MODELDT-Datei verwerfen? Einen einzelnen Namen kannst du über Namen ändern zurücksetzen.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        self.session.remove(key)
        if is_name:
            try:self.refresh_names()
            except Exception as exc:self.warning('Namen aktualisieren',exc)
            self.update_pending();return
        self.revisions={key:revision+1 for key,revision in self.revisions.items()};self.model_paths.clear();self.raw_models.clear();self.update_pending();self.load_digimon()
    def save_project(self):
        if not self.session:return
        name,_=QFileDialog.getSaveFileName(self,'Native Änderungen speichern','dw2_viewer.dw2mod','DW2-Mod-Projekt (*.dw2mod)')
        if name:
            try:self.session.export_project(name)
            except Exception as exc:self.warning('Projekt speichern',exc)
    def load_project(self):
        if not self.session:return
        name,_=QFileDialog.getOpenFileName(self,'Native Änderungen laden','','DW2-Mod-Projekt (*.dw2mod)')
        if name:
            try:
                before=self.session.edits.copy()
                try:
                    # Private-table files must be addressable even when this is
                    # the first attack action after opening the image.
                    import zipfile,json
                    with zipfile.ZipFile(name) as archive:
                        if archive.getinfo('project.json').file_size>4*1024*1024:raise ValueError('Projektmanifest zu groß.')
                        manifest=json.loads(archive.read('project.json'))
                    data_files={basename(item.get('path','')) for item in manifest.get('files',[])} & ATTACK_FILE_INDEX.keys()
                    if data_files-{'DIGIMNDT.BIN'}:self.get_attack_repository()
                    elif data_files:self.get_type_repository()
                    self.session.import_project(name,self.entries)
                    if data_files-{'DIGIMNDT.BIN'}:self.get_attack_repository().tables()
                    elif data_files:self.get_type_repository().table()
                    self.refresh_names()
                    self.refresh_type_summary()
                except Exception:
                    self.session.edits=before;raise
                for c in self.catalog:
                    if any((e.path,e.lba) in self.session.edits for e in self.files_for(c)):self.revisions[self.key_for(c)]=self.revisions.get(self.key_for(c),0)+1
                self.model_paths.clear();self.raw_models.clear();self.update_pending();self.load_digimon()
            except Exception as exc:self.warning('Projekt laden',exc)
    def export_image(self):
        if not self.session:return self.inform('Image speichern','Bitte zuerst ein Spiel-Image öffnen.')
        if not self.session.edits:
            message='Es gibt noch keine vorgemerkten Spieländerungen. Nach PNG importieren die rechte Vorschau prüfen und Farben stimmen – vormerken drücken.'
            if self.rgb_models():message+=' Vollfarben nur im Viewer ersetzt keine Spieltexturen; solche Modelle lassen sich separat als Vollfarben-Projekt speichern.'
            return self.inform('Image speichern',message)
        ext='.bin' if self.session.sector_size==2352 else '.iso';target,_=QFileDialog.getSaveFileName(self,'Alle Änderungen in Image exportieren',str(self.image_path.with_name(self.image_path.stem+'_bearbeitet'+ext)),f'Image (*{ext})',options=QFileDialog.Option.DontConfirmOverwrite)
        if target:self.write_image(target)
    def overwrite_image(self):
        if self.session and self.session.edits:self.write_image(self.image_path)
    def write_image(self,target):
        if self._pending_write or (self.writer and self.writer.isRunning()):return
        if any(e.relocate for e in self.session.edits.values()) and self.image and Path(self.image).suffix.lower()=='.cue':
            import re
            tracks=re.findall(r'^\s*TRACK\s+\d+\s+(\S+)',Path(self.image).read_text(errors='replace'),re.M|re.I)
            if len(tracks)!=1 or tracks[0].upper()!='MODE2/2352':return self.warning('Image speichern','Dateiverlagerung unterstützt eine CUE mit einem MODE2/2352-Datentrack. Die vorhandene Trackaufteilung wird nicht automatisch umgebaut.')
        target=Path(target).resolve()
        suffix='.bin' if self.session.sector_size==2352 else '.iso'
        if not target.suffix:target=target.with_suffix(suffix)
        if target.suffix.lower() not in (('.bin','.img') if self.session.sector_size==2352 else ('.iso',)):
            return self.warning('Image speichern',f'Dieses Image benötigt die Dateiendung {suffix}.')
        overwrite=target.exists()
        if overwrite and self.ask('Überschreiben bestätigen',f'{target.name} wirklich überschreiben?'+('\nVorher wird eine Sicherung angelegt.' if target==self.image_path else ''),QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        self.loader.clear();self.navigation_timer.stop();self.centralWidget().setEnabled(False);self.model_status.setText('Image wird geprüft und gespeichert …')
        self._pending_write=(target,overwrite)
        for job in self.eye_jobs:
            if job.isRunning():job.requestInterruption()
        self._start_image_write_when_idle()
    def _start_image_write_when_idle(self):
        if self._closing:self._pending_write=None;return
        if self.loader.active is not None or any(job.isRunning() for job in self.eye_jobs):
            QTimer.singleShot(80,self._start_image_write_when_idle);return
        target,overwrite=self._pending_write;self._pending_write=None
        self.writer=ImageWriter(self.session,target,overwrite);self.writer.done.connect(self.image_written);self.writer.failed.connect(self.image_write_failed);self.writer.start()
    def image_written(self,path,backup):
        source=self.image;sector_size=self.session.sector_size;rgb=self.rgb_models();previous_namespace=self.rgb_namespace
        mappings=getattr(self.session,'last_relocations',{})
        aliases={(basename(name),lba):value for (name,lba),value in mappings.items()}
        for entry in self.entries+[e for c in self.catalog for e in c.files]:
            mapped=mappings.get((entry.path,entry.lba)) or aliases.get((basename(entry.path),entry.lba))
            if mapped:entry.lba=mapped[0];entry.size=mapped[1]
        self.image_path=Path(path);self.image=path;self.index_key=cache_key(path);self.session=EditSession(path,sector_size);self.name_repository=None;self._source_names={c.id:c.name for c in self.catalog};self.wanted=None;self.raw_models.clear();self.revisions.clear();self.model_paths.clear();self.update_pending();self.centralWidget().setEnabled(True);self.model_status.setText('Alle vorgemerkten Dateien gespeichert: '+Path(path).name)
        self.rgb_namespace=self.index_key
        try:
            for key,model in rgb.items():set_replacement(model,self._rgb_root()/key)
        except Exception as exc:self.rgb_namespace=previous_namespace;self.write_log('Vollfarben-Projekt bleibt unter dem bisherigen Image erhalten: '+str(exc))
        self.update_pending()
        if backup:self.write_log('Sicherung: '+backup)
        if sector_size==2352 and Path(source).suffix.lower()=='.cue' and Path(source).resolve()!=Path(path).with_suffix('.cue').resolve():
            cue=Path(path).with_suffix('.cue')
            if not cue.exists():
                try:write_cue_for_image(source,path)
                except Exception as exc:self.write_log('BIN gespeichert; CUE bitte manuell anpassen: '+str(exc))
            else:self.write_log('BIN gespeichert; vorhandene CUE nicht verändert: '+str(cue))
        if not self._closing:self.load_digimon()
    def image_write_failed(self,reason):self.centralWidget().setEnabled(True);self.warning('Image speichern',reason)
    def closeEvent(self,event):
        if not self._closing and self.session and self.session.edits:
            if self.ask('Ungespeicherte Änderungen','Schließen und vorgemerkte Änderungen verwerfen? Zum Sichern abbrechen und Mod-Projekt speichern.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:event.ignore();return
        self._closing=True;self.navigation_timer.stop();self.loader.stop()
        if self.reader and self.reader.isRunning():self.reader.requestInterruption()
        for job in self.eye_jobs:
            if job.isRunning():job.requestInterruption()
        workers=[self.loader,self.reader,self.writer]+self.eye_jobs
        if any(job and job.isRunning() for job in workers):self.centralWidget().setEnabled(False);event.ignore();QTimer.singleShot(150,self.close);return
        if hasattr(self.viewer,'timer'):self.viewer.timer.stop()
        self.viewer.close();super().closeEvent(event)

if __name__=='__main__':
    app=QApplication(sys.argv);app.setStyle('Fusion')
    win=Main();win.show();sys.exit(app.exec())
