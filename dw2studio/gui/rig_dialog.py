"""OBJ import → explicit body-part mapping, native animation and blink editor."""
from pathlib import Path
import time
import uuid
import numpy as np
from PyQt6.QtCore import Qt,QTimer
from PyQt6.QtGui import QImage,QPixmap
from PyQt6.QtWidgets import (QDialog,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QSplitter,QLabel,QPushButton,
 QTreeWidget,QTreeWidgetItem,QListWidget,QTabWidget,QScrollArea,QFormLayout,QComboBox,QDoubleSpinBox,QSpinBox,
 QSlider,QCheckBox,QFileDialog,QMessageBox,QDialogButtonBox)
from .rig_canvas import RigCanvas
from ..core.rig_import import RigProject

BODY_PARTS=['Unbenannt','Körper / Rumpf','Kopf','Unterkiefer / Mund','Arm links','Unterarm links','Hand links',
 'Arm rechts','Unterarm rechts','Hand rechts','Bein links','Fuß links','Bein rechts','Fuß rechts','Schwanz','Flügel links','Flügel rechts']

class RigImportDialog(QDialog):
    def __init__(self,project,destination,parent=None):
        super().__init__(parent);self.project=project;self.destination=Path(destination);self.native_result=None;self.animation_results={};self.preview_path=None;self.ready=False;self.history=[];self.playing=False;self.frame_fraction=0.
        self.setWindowTitle('OBJ-Import · Skelett, Bewegungen & Augen');self.resize(min(1420,max(1060,self.screen().availableGeometry().width()-40)),min(900,max(650,self.screen().availableGeometry().height()-80)))
        root=QVBoxLayout(self);title=QLabel('1. Ausrichten  →  2. Flächen Knochen zuordnen  →  3. Bewegung prüfen  →  4. Vormerken');title.setWordWrap(True);root.addWidget(title)
        help_text=QLabel('OBJ enthält kein Skelett. Weise Flächen den bestehenden DW2-Knochen zu. Knochen- und Clipnummern sind belegt; Körperteilnamen vergibst du selbst. Rechteckauswahl erfasst auch verdeckte Flächen.');help_text.setWordWrap(True);root.addWidget(help_text)
        split=QSplitter(Qt.Orientation.Horizontal);root.addWidget(split,1)
        left=QWidget();lv=QVBoxLayout(left);left.setMinimumWidth(220);left.setMaximumWidth(330)
        bone_hint=QLabel('Zielskelett · Zielknochen wählen');bone_hint.setWordWrap(True);lv.addWidget(bone_hint)
        self.bones=QTreeWidget();self.bones.setHeaderLabels(['Knochen','Körperteil']);self.bones.setColumnWidth(0,75);lv.addWidget(self.bones,1)
        self.bone_items=[]
        for i,parent_id in enumerate(project.parents):
            item=QTreeWidgetItem([str(i),project.settings[i].label]);item.setData(0,Qt.ItemDataRole.UserRole,i)
            if parent_id<0:self.bones.addTopLevelItem(item)
            else:self.bone_items[parent_id].addChild(item)
            self.bone_items.append(item)
        self.bones.expandAll();self.bones.currentItemChanged.connect(self.bone_changed)
        lv.addWidget(QLabel('OBJ-Gruppen'))
        self.groups=QListWidget();self.groups.addItems(project.mesh.groups);self.groups.currentTextChanged.connect(self.select_group);lv.addWidget(self.groups)
        for text,slot in [('Alle Flächen markieren',self.select_all),('Unzugeordnete markieren',self.select_unassigned),('Auswahl aufheben',self.clear_selection),('Auswahl → Knochen',self.assign_selection),('Auswahlzuordnung lösen',self.unassign_selection),('Zuordnung rückgängig',self.undo_assignment)]:
            button=QPushButton(text);button.clicked.connect(slot);lv.addWidget(button)
        split.addWidget(left)
        center=QWidget();cv=QVBoxLayout(center);cv.setContentsMargins(0,0,0,0)
        self.canvas=RigCanvas(project);self.canvas.selectionChanged.connect(self.update_status);cv.addWidget(self.canvas,1)
        view=QHBoxLayout();self.view_choice=QComboBox();self.view_choice.addItems(['3D','Vorne','Hinten','Links','Rechts','Oben']);self.view_choice.currentIndexChanged.connect(self.change_view);view.addWidget(self.view_choice)
        reset=QPushButton('Ansicht einpassen');reset.clicked.connect(self.canvas.reset_camera);view.addWidget(reset)
        self.texture_check=QCheckBox('Texturvorschau');self.texture_check.toggled.connect(lambda flag:(setattr(self.canvas,'show_texture',flag),self.canvas.update()));view.addWidget(self.texture_check);cv.addLayout(view)
        anim=QHBoxLayout();self.animation_file=QComboBox();self.animation_file.addItems(list(project.animations));self.animation_file.currentTextChanged.connect(self.clip_list_changed);anim.addWidget(self.animation_file,2)
        self.clip=QComboBox();self.clip.currentIndexChanged.connect(self.clip_changed);anim.addWidget(self.clip,1)
        self.play=QPushButton('▶ Abspielen');self.play.clicked.connect(self.toggle_play);anim.addWidget(self.play)
        self.speed=QDoubleSpinBox();self.speed.setRange(.1,3);self.speed.setValue(1);self.speed.setSuffix('× Vorschau');anim.addWidget(self.speed);cv.addLayout(anim)
        frame=QHBoxLayout();self.frame=QSlider(Qt.Orientation.Horizontal);self.frame.valueChanged.connect(self.refresh_pose);frame.addWidget(self.frame,1);self.frame_label=QLabel();frame.addWidget(self.frame_label);cv.addLayout(frame)
        bind=QPushButton('Aktuellen Frame als Referenzpose für den Import verwenden');bind.clicked.connect(self.set_reference);cv.addWidget(bind)
        self.reference_label=QLabel();self.reference_label.setWordWrap(True);cv.addWidget(self.reference_label)
        split.addWidget(center)
        tabs=QTabWidget();tabs.setMinimumWidth(295);tabs.setMaximumWidth(400);split.addWidget(tabs)
        def panel(name):
            scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);widget=QWidget();form=QFormLayout(widget);form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows);form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow);scroll.setWidget(widget);tabs.addTab(scroll,name);return form
        align=panel('Modell')
        self.scale=self.spin(.0001,100000,1,4);self.scale.valueChanged.connect(self.transform_changed);align.addRow('Skalierung',self.scale)
        self.rotation=self.vector(align,'Drehen °',-360,360,self.transform_changed)
        self.offset=self.vector(align,'Verschieben',-32767,32767,self.transform_changed)
        fit=QPushButton('Auf Zielgröße einpassen');fit.clicked.connect(self.fit_model);align.addRow(fit)
        self.original_check=QCheckBox('Zielmodell als Drahtgitter');self.original_check.toggled.connect(lambda flag:(setattr(self.canvas,'show_reference',flag),self.canvas.update()));align.addRow(self.original_check)
        self.uv=QComboBox();self.uv.addItems(['UV für 128×256-Atlas','UV auf 128×224 Nutzpixel einpassen']);self.uv.currentIndexChanged.connect(self.uv_changed);align.addRow('UV-Abbildung',self.uv)
        load_texture=QPushButton('PNG auswählen (1×–4×)');load_texture.clicked.connect(self.load_texture);align.addRow(load_texture)
        self.texture_label=QLabel('Ohne neue PNG wird die vorhandene native Textur verwendet.');self.texture_label.setWordWrap(True);align.addRow(self.texture_label)
        self.palette=self.integer(0,61,0);self.palette.valueChanged.connect(self.palette_changed);align.addRow('Palette gewählter Knochen',self.palette)
        hint=QLabel('Grenzen: 256 Vertices/Normalen je Knochen; Geometrie muss in den vorhandenen Modellplatz passen. Flächen werden starr an einen Knochen gebunden. UVs und Textur müssen zusammenpassen.');hint.setWordWrap(True);align.addRow(hint)
        bone=panel('Bewegung')
        self.label=QComboBox();self.label.setEditable(True);self.label.addItems(BODY_PARTS);self.label.currentTextChanged.connect(self.adjustment_changed);bone.addRow('Körperteilname',self.label)
        self.motion=self.spin(0,3,1);self.motion.valueChanged.connect(self.adjustment_changed);bone.addRow('Rotationsbewegung ×',self.motion)
        self.translation=self.spin(0,3,1);self.translation.valueChanged.connect(self.adjustment_changed);bone.addRow('Verschiebebewegung ×',self.translation)
        self.bone_rotation=self.vector(bone,'Achsenkorrektur °',-180,180,self.adjustment_changed)
        self.bone_offset=self.vector(bone,'Gelenkversatz',-32767,32767,self.adjustment_changed)
        pivot=QPushButton('Gelenk → Auswahlzentrum');pivot.clicked.connect(self.pivot_to_selection);bone.addRow(pivot)
        text=QLabel('Korrekturen gelten für alle vorhandenen Clips aller A–K-Dateien dieses Digimon. Keyframeanzahl, Timing und Dateigröße bleiben erhalten. Die Vorschaugeschwindigkeit wird nicht ins Spiel geschrieben.');text.setWordWrap(True);bone.addRow(text)
        eyes=panel('Augen')
        self.edit_blink=QCheckBox('Augenrecords bearbeiten');self.edit_blink.toggled.connect(self.blink_changed);eyes.addRow(self.edit_blink)
        self.eye_fields=[]
        for i in range(2):
            title=QLabel(f'Augenrecord {i+1} (manuell prüfen)');eyes.addRow(title)
            fields={};fields['enabled']=QCheckBox('Aktiv');fields['enabled'].toggled.connect(self.blink_changed);eyes.addRow(fields['enabled'])
            pos=project.model.blink_offset+i*10;x,y,w,h,ox,oy,hx,hy,cx,cy=project.original[pos:pos+10]
            native={'x':x*4,'y':y,'w':w*4,'h':h,'open_x':ox*4,'open_y':oy,'half_x':hx*4,'half_y':hy,'closed_x':cx*4,'closed_y':cy}
            fields['enabled'].setChecked(x<254)
            for key,label in [('x','Ziel X'),('y','Ziel Y'),('w','Breite'),('h','Höhe'),('open_x','Offen X'),('open_y','Offen Y'),('half_x','Halb X'),('half_y','Halb Y'),('closed_x','Zu X'),('closed_y','Zu Y')]:
                field=self.integer(0,224 if key.endswith('y') or key in ('y','h') else 128,min(native[key],224 if key.endswith('y') or key in ('y','h') else 128));field.valueChanged.connect(self.blink_changed);fields[key]=field;eyes.addRow(label,field)
            self.eye_fields.append(fields)
        self.blink_preview=QComboBox();self.blink_preview.addItems(['Augen offen','Augen halb geschlossen','Augen geschlossen','Blinkfolge (nur Vorschau)']);self.blink_preview.currentIndexChanged.connect(self.refresh_pose);eyes.addRow('Vorschauzustand',self.blink_preview)
        self.eye_preview=QLabel();self.eye_preview.setMinimumHeight(100);eyes.addRow(self.eye_preview)
        note=QLabel('Alle Angaben in nativen Pixeln. X und Breite in 4er-Schritten. Ein Record kann beide sichtbaren Augen enthalten. Blinktempo/zufällige Auslösung steuert das Spiel; hier werden Texturquellen und Ziele geändert.');note.setWordWrap(True);eyes.addRow(note)
        split.setSizes([240,800,330]);split.setStretchFactor(1,1)
        self.status=QLabel();self.status.setWordWrap(True);root.addWidget(self.status)
        actions=QHBoxLayout()
        for text,slot in [('Zuordnung speichern',self.save_mapping),('Zuordnung laden',self.load_mapping),('Rig + Animationen als glTF exportieren',self.export_gltf),('Nativen Platz prüfen',self.check_native)]:
            button=QPushButton(text);button.clicked.connect(slot);actions.addWidget(button)
        root.addLayout(actions)
        self.buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel);self.commit_button=self.buttons.addButton('Modell + Animationen vormerken',QDialogButtonBox.ButtonRole.AcceptRole);self.buttons.accepted.connect(self.commit);self.buttons.rejected.connect(self.reject);root.addWidget(self.buttons)
        self.timer=QTimer(self);self.timer.setInterval(33);self.timer.timeout.connect(self.tick)
        self.ready=True;self.bones.setCurrentItem(self.bone_items[0]);self.clip_list_changed();self.refresh_reference_label();self.update_status();self.refresh_pose();self.blink_changed();self.fit_model()

    def spin(self,low,high,value,decimals=2):
        spin=QDoubleSpinBox();spin.setRange(low,high);spin.setDecimals(decimals);spin.setValue(value);spin.setSingleStep(.1 if decimals else 1);return spin
    def integer(self,low,high,value):
        spin=QSpinBox();spin.setRange(low,high);spin.setValue(value);return spin
    def vector(self,form,label,low,high,slot):
        row=QWidget();layout=QGridLayout(row);layout.setContentsMargins(0,0,0,0);fields=[]
        for i,axis in enumerate('XYZ'):
            spin=self.spin(low,high,0);spin.valueChanged.connect(slot);layout.addWidget(QLabel(axis),i,0);layout.addWidget(spin,i,1);fields.append(spin)
        form.addRow(label,row);return fields
    def bone_id(self):
        item=self.bones.currentItem();return int(item.data(0,Qt.ItemDataRole.UserRole)) if item else 0
    def values(self,fields):return [field.value() for field in fields]
    def set_values(self,fields,values):
        for field,value in zip(fields,values):field.setValue(value)
    def bone_changed(self,*args):
        if not self.ready:return
        self.ready=False;i=self.bone_id();self.canvas.active_bone=i;self.canvas.update();setting=self.project.settings[i]
        self.label.setCurrentText(setting.label);self.motion.setValue(setting.motion_scale);self.translation.setValue(setting.translation_scale);self.set_values(self.bone_rotation,setting.rotation);self.set_values(self.bone_offset,setting.offset)
        clut=self.project.palette_by_bone[i];self.palette.setValue((((clut>>6)-224)*2)+(clut&1));self.ready=True
    def adjustment_changed(self,*args):
        if not self.ready:return
        i=self.bone_id();setting=self.project.settings[i];setting.label=self.label.currentText();setting.motion_scale=self.motion.value();setting.translation_scale=self.translation.value();setting.rotation=self.values(self.bone_rotation);setting.offset=self.values(self.bone_offset);self.bone_items[i].setText(1,setting.label);self.refresh_pose()
    def transform_changed(self,*args):
        if not self.ready:return
        self.project.scale=self.scale.value();self.project.rotation=self.values(self.rotation);self.project.offset=self.values(self.offset);self.refresh_pose()
    def palette_changed(self,*args):
        if self.ready:self.project.palette_by_bone[self.bone_id()]=((224+self.palette.value()//2)<<6)|(self.palette.value()%2)
    def uv_changed(self,*args):
        if self.ready:self.project.uv_mode='fit224' if self.uv.currentIndex() else 'atlas256';self.canvas.update()
    def select_group(self,name):
        self.canvas.selected={i for i,face in enumerate(self.project.mesh.faces) if face.group==name};self.canvas.update();self.update_status()
    def select_all(self):self.canvas.selected=set(range(len(self.project.mesh.faces)));self.canvas.update();self.update_status()
    def select_unassigned(self):self.canvas.selected=set(np.where(self.project.assignment<0)[0]);self.canvas.update();self.update_status()
    def clear_selection(self):self.canvas.selected.clear();self.canvas.update();self.update_status()
    def remember(self):self.history.append(self.project.assignment.copy());self.history=self.history[-30:]
    def assign_selection(self):
        if not self.canvas.selected:return
        self.remember();self.project.assignment[list(self.canvas.selected)]=self.bone_id();self.refresh_pose();self.update_status()
    def unassign_selection(self):
        if not self.canvas.selected:return
        self.remember();self.project.assignment[list(self.canvas.selected)]=-1;self.refresh_pose();self.update_status()
    def undo_assignment(self):
        if self.history:self.project.assignment=self.history.pop();self.refresh_pose();self.update_status()
    def update_status(self):
        if not self.ready:return
        missing=int(np.count_nonzero(self.project.assignment<0));self.status.setText(f'{len(self.canvas.selected)} Flächen ausgewählt · {missing} von {len(self.project.mesh.faces)} noch ohne Knochen · Quelle: {self.project.mesh.path.name}');self.commit_button.setEnabled(missing==0)
    def change_view(self,index):
        self.canvas.yaw,self.canvas.pitch=[(.45,-.15),(0,0),(np.pi,0),(np.pi/2,0),(-np.pi/2,0),(0,np.pi/2)][index];self.canvas.update()
    def clip_list_changed(self,*args):
        if not self.ready:return
        self.clip.blockSignals(True);self.clip.clear();animation=self.project.animations[self.animation_file.currentText()]
        for i,clip in enumerate(animation.clips):self.clip.addItem(f'Clip {i} · {len(clip.indices)} Frames')
        self.clip.blockSignals(False);self.clip.setCurrentIndex(0);self.clip_changed()
    def clip_changed(self,*args):
        if not self.ready or self.clip.currentIndex()<0:return
        animation=self.project.animations[self.animation_file.currentText()];self.frame.setRange(0,len(animation.clips[self.clip.currentIndex()].indices)-1);self.frame.setValue(0);self.refresh_pose()
    def refresh_pose(self,*args):
        if not self.ready or self.clip.currentIndex()<0:return
        try:
            triangles,bones=self.project.preview(self.animation_file.currentText(),self.clip.currentIndex(),self.frame.value());self.canvas.set_pose(triangles,bones);self.frame_label.setText(f'Frame {self.frame.value()} / {self.frame.maximum()}');self.refresh_blink_preview()
        except Exception as exc:self.status.setText(str(exc));self.timer.stop();self.playing=False;self.play.setText('▶ Abspielen')
    def toggle_play(self):
        self.playing=not self.playing;self.play.setText('⏸ Pause' if self.playing else '▶ Abspielen');self.last_tick=time.monotonic();self.timer.start() if self.playing else self.timer.stop()
    def tick(self):
        now=time.monotonic();self.frame_fraction+=min(now-self.last_tick,.2)*30*self.speed.value();self.last_tick=now;steps=int(self.frame_fraction);self.frame_fraction-=steps
        if steps:self.frame.setValue((self.frame.value()+steps)%(self.frame.maximum()+1));self.refresh_blink_preview()
    def set_reference(self):
        self.project.reference_name=self.animation_file.currentText();self.project.reference_clip=self.clip.currentIndex();self.project.reference_frame=self.frame.value();self.refresh_reference_label();self.refresh_pose()
    def refresh_reference_label(self):self.reference_label.setText(f'Referenzpose: {self.project.reference_name} · Clip {self.project.reference_clip} · Frame {self.project.reference_frame}')
    def fit_model(self):
        p=self.project;world=p.binding_world();points=[]
        import struct
        from ..core.rig_animation import D
        for i,part in enumerate(p.model.parts):
            v=np.array([struct.unpack_from('<hhh',p.original,part.vertices+6+j*6) for j in range(part.vertex_count)],dtype=float)@D
            points.extend((np.c_[v,np.ones(len(v))]@world[i].T)[:,:3])
        points=np.asarray(points);source=p.mesh.vertices;extent=np.ptp(source,axis=0);axis=int(np.argmax(np.ptp(points,axis=0)));scale=np.ptp(points,axis=0)[axis]/max(extent[axis],1e-6)
        self.ready=False;self.scale.setValue(scale);self.set_values(self.rotation,[0,0,0]);self.set_values(self.offset,(points.min(0)+points.max(0))/2-(source.min(0)+source.max(0))/2*scale);self.ready=True;self.transform_changed();self.canvas.reset_camera()
    def pivot_to_selection(self):
        if not self.canvas.selected:return
        from ..core.rig_animation import rotation_xyz
        p=self.project;i=self.bone_id();indices=np.unique(p.mesh.face_indices[list(self.canvas.selected)].flatten());center=p.source_vertices()[indices].mean(0)
        world=p.binding_world();parent=p.parents[i];local=center if parent<0 else (np.linalg.inv(world[parent])@np.r_[center,1])[:3]
        current=p.adjusted_animations()[p.reference_name].local_pose(p.reference_clip,p.reference_frame)[i,:3,3]
        self.set_values(self.bone_offset,np.asarray(p.settings[i].offset)+local-current)
    def blink_changed(self,*args):
        if not self.ready:return
        for fields in self.eye_fields:
            for field in fields.values():field.setEnabled(self.edit_blink.isChecked())
        if not self.edit_blink.isChecked():self.project.blink_records=None
        else:self.project.blink_records=[{key:(field.isChecked() if key=='enabled' else field.value()) for key,field in fields.items()} for fields in self.eye_fields]
        try:self.project._blink_bytes();self.refresh_blink_preview()
        except ValueError as exc:self.status.setText(str(exc))
    def refresh_blink_preview(self):
        if not hasattr(self,'eye_preview'):return
        try:
            from ..core.native_texture import NativeTexture
            from ..core.native_model import NativeModel
            from PIL.ImageQt import ImageQt
            blink=self.project._blink_bytes();signature=(self.project.assignment.tobytes(),tuple(self.project.palette_by_bone),self.project.uv_mode,self.project.texture_png,blink)
            key=(signature,getattr(self,'_native_texture_key',None)==signature)
            if key!=getattr(self,'_blink_cache_key',None):
                if getattr(self,'_native_texture_key',None)==signature:
                    base=self._native_preview_atlas.copy()
                elif self.project.texture_png:
                    from PIL import Image
                    with Image.open(self.project.texture_png) as source:base=source.convert('RGBA').copy()
                else:
                    if not hasattr(self,'_original_atlas'):self._original_atlas=NativeTexture(self.project.original).to_image()
                    base=self._original_atlas.copy()
                data=bytearray(self.project.original);pos=self.project.model.blink_offset;data[pos:pos+20]=blink
                try:eyes=NativeModel(data).eyes()
                except ValueError:eyes=()
                self._blink_base=base;self._preview_eyes=eyes;self._blink_cache_key=key
            image=self._blink_base.copy();stage=self.blink_preview.currentIndex()
            if stage==3:stage=(0,1,2,1)[(self.frame.value()//3)%4]
            for eye in self._preview_eyes:
                sx,sy=eye.frames[stage];x,y=eye.destination;image.paste(image.crop((sx,sy,sx+eye.width,sy+eye.height)),(x,y))
            qimage=ImageQt(image).copy();self.canvas.texture=qimage;self.eye_preview.setPixmap(QPixmap.fromImage(qimage).scaled(190,230,Qt.AspectRatioMode.KeepAspectRatio))
        except (ValueError,OSError) as exc:self.eye_preview.setText(str(exc))
    def load_texture(self):
        filename,_=QFileDialog.getOpenFileName(self,'PNG für natives Modell (1×–4×)','','PNG (*.png)')
        if not filename:return
        try:
            from .texture_size_dialog import prepare_native_png
            from PIL.ImageQt import ImageQt
            prepared=prepare_native_png(filename,(128,256),self)
            if prepared is None:return
            folder=self.destination/'native_textures';folder.mkdir(parents=True,exist_ok=True)
            target=folder/(uuid.uuid4().hex+'.png');prepared.save(target,'PNG')
            self.project.texture_png=str(target);self._native_texture_key=None;self._blink_cache_key=None;self.canvas.texture=ImageQt(prepared).copy();self.texture_check.setChecked(True);self.texture_label.setText(Path(filename).name+' → 128×256 für das Spiel');self.refresh_blink_preview()
        except Exception as exc:QMessageBox.warning(self,'Textur',str(exc))
    def check_native(self):
        try:
            data,report=self.project.build_native();self.project.adjusted_animation_bytes()
            from ..core.native_texture import NativeTexture
            self._native_preview_atlas=NativeTexture(data).to_image();self._native_texture_key=(self.project.assignment.tobytes(),tuple(self.project.palette_by_bone),self.project.uv_mode,self.project.texture_png,self.project._blink_bytes());self._blink_cache_key=None;self.refresh_blink_preview();self.canvas.update()
            self.status.setText(f'Formatprüfung bestanden: {report["geometry_used"]}/{report["geometry_budget"]} Geometriebytes · {report["triangles"]} Dreiecke. Spieltest weiterhin erforderlich.')
        except Exception as exc:QMessageBox.warning(self,'Native Prüfung',str(exc))
    def save_mapping(self):
        filename,_=QFileDialog.getSaveFileName(self,'Zuordnung und Korrekturen speichern',self.project.mesh.path.stem+'.dw2rig','DW2-Rig (*.dw2rig)')
        if filename:
            try:self.project.save(filename);self.status.setText('Zuordnung gespeichert. OBJ und Zielmodell müssen beim Laden dieselben Dateien sein.')
            except Exception as exc:QMessageBox.warning(self,'Zuordnung speichern',str(exc))
    def load_mapping(self):
        filename,_=QFileDialog.getOpenFileName(self,'Zuordnung laden','','DW2-Rig (*.dw2rig)')
        if not filename:return
        try:
            self.project.load(filename);self.ready=False;self.scale.setValue(self.project.scale);self.set_values(self.rotation,self.project.rotation);self.set_values(self.offset,self.project.offset);self.uv.setCurrentIndex(self.project.uv_mode=='fit224');self.ready=True
            for i,item in enumerate(self.bone_items):item.setText(1,self.project.settings[i].label)
            self.ready=False;self.edit_blink.setChecked(self.project.blink_records is not None)
            if self.project.blink_records is not None:
                for fields,record in zip(self.eye_fields,self.project.blink_records):
                    for key,field in fields.items():
                        field.setChecked(record[key]) if key=='enabled' else field.setValue(record[key])
            self.ready=True;self._blink_cache_key=None;self.blink_changed();self.bone_changed();self.refresh_reference_label();self.refresh_pose();self.update_status()
        except Exception as exc:QMessageBox.warning(self,'Zuordnung laden',str(exc))
    def export_gltf(self):
        filename,_=QFileDialog.getSaveFileName(self,'Modell mit allen Clips exportieren',self.project.mesh.path.stem+'_rig.gltf','glTF mit Animationen (*.gltf)')
        if filename:
            try:self.project.export_gltf(filename);self.status.setText('Rig-glTF mit allen vorhandenen Animationsclips exportiert.')
            except Exception as exc:QMessageBox.warning(self,'Rig-Export',str(exc))
    def commit(self):
        try:
            native,report=self.project.build_native();animations=self.project.adjusted_animation_bytes();folder=self.destination/('rig_'+uuid.uuid4().hex);folder.mkdir(parents=True,exist_ok=True)
            self.preview_path,_=self.project.export_gltf(folder/'rigged.gltf');self.project.save(folder/'mapping.dw2rig');self.native_result=native;self.animation_results=animations;self.timer.stop();self.accept()
        except Exception as exc:QMessageBox.warning(self,'Import noch nicht möglich',str(exc))
    def done(self,result):
        if hasattr(self,'timer'):self.timer.stop()
        super().done(result)
