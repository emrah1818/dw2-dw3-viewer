"""Interactive textured OBJ/GLTF/GLB preview; never claims to decode DW2 BIN."""
from pathlib import Path
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QLabel
from dw2studio.i18n import translate
try:
 import numpy as np, trimesh, pyqtgraph.opengl as gl
 from PIL import Image
 AVAILABLE=True
except ImportError:
 AVAILABLE=False

def sample_texture_colors(mesh):
 """Sample an image at face UV centroids; preserve PS1 nearest-neighbor colors.
 Vertex colors are assigned PER TRIANGLE, avoiding texture seams at shared UVs.
 Returns (vertices, faces, colors) for GLMeshItem, or raises on invalid geometry.
 """
 v=np.asarray(mesh.vertices,dtype=np.float32)
 f=np.asarray(mesh.faces,dtype=np.int32)
 if not len(v) or not len(f):raise ValueError('Leeres 3D-Modell')
 visual=mesh.visual
 material=getattr(visual,'material',None)
 image=getattr(material,'image',None) or getattr(material,'baseColorTexture',None)
 uv=getattr(visual,'uv',None)
 if image is not None and uv is not None and len(uv)==len(v):
  tex=np.asarray(image.convert('RGBA') if hasattr(image,'convert') else Image.fromarray(np.asarray(image)).convert('RGBA'))
  # trimesh UV origin is lower left; PIL image origin is upper left.
  face_uv=np.asarray(uv,dtype=float)[f].mean(axis=1)
  x=np.clip(np.rint((face_uv[:,0]%1)*(tex.shape[1]-1)).astype(int),0,tex.shape[1]-1)
  y=np.clip(np.rint((1-(face_uv[:,1]%1))*(tex.shape[0]-1)).astype(int),0,tex.shape[0]-1)
  rgba=tex[y,x].astype(np.float32)/255.0
  return v[f].reshape(-1,3),np.arange(len(f)*3,dtype=np.uint32).reshape(-1,3),np.repeat(rgba,3,axis=0)
 # Fall back to supplied vertex colors, or neutral color; do not invent a texture.
 rgba=np.tile(np.array([[.78,.8,.84,1]],dtype=np.float32),(len(v),1))
 try:
  vc=np.asarray(visual.vertex_colors)
  if len(vc)==len(v):rgba=vc.astype(np.float32)/255.0
 except (AttributeError,ValueError):pass
 return v,f.astype(np.uint32),rgba

from dw2studio.renderer.animation_data import read_gltf_animation_durations

class ModelViewer(QWidget):
 def _t(self, source, **values):
  return translate(source, getattr(self,'ui_language','de'), **values)
 def refresh_language(self, language):
  self.ui_language=language
  loaded=getattr(self,'_loaded_info',None)
  if loaded:
   self.info.setText(self._t('{name} · {count} Teilmodell(e) · Texturfarben (UV-Sampling)',**loaded))
 def __init__(self):
  super().__init__();self.layout=QVBoxLayout(self)
  self.info=QLabel('OBJ / glTF / GLB laden – texturierte Vorschau, kein DW2-BIN-Import')
  self.layout.addWidget(self.info)
  if AVAILABLE:
   self.view=gl.GLViewWidget();self.view.setCameraPosition(distance=5);self.layout.addWidget(self.view)
  else:self.layout.addWidget(QLabel('3D-Abhängigkeiten fehlen: pip install pyqtgraph PyOpenGL trimesh numpy Pillow'))
 def load(self,path):
  if not AVAILABLE:raise RuntimeError('3D-Abhängigkeiten fehlen')
  path=Path(path)
  if path.suffix.lower() not in ('.obj','.stl','.glb','.gltf'):
   raise ValueError('Nur OBJ, STL, GLB und glTF werden unterstützt; DW2-BIN benötigt Konvertierung')
  if path.suffix.lower() in ('.gltf','.glb'):
   raise RuntimeError('Für korrekt texturierte und animierte DW2-glTF-Modelle wird VTK benötigt. Bitte requirements.txt installieren; der alte Viewer zeigt nur ungenaue Dreiecksfarben.')
  scene=trimesh.load(str(path),force='scene',process=False)
  meshes=scene.dump(concatenate=False) if isinstance(scene,trimesh.Scene) else [scene]
  chunks=[]
  for mesh in meshes:
   if isinstance(mesh,trimesh.Trimesh) and len(mesh.faces):chunks.append(sample_texture_colors(mesh))
  if not chunks:raise ValueError('Keine Dreiecke im Modell gefunden')
  all_vertices=np.concatenate([c[0] for c in chunks])
  center=(all_vertices.min(axis=0)+all_vertices.max(axis=0))/2
  span=float(np.max(np.ptp(all_vertices,axis=0)))
  scale=2.0/span if span>0 else 1.0
  self.view.clear()
  for vertices,faces,colors in chunks:
   item=gl.GLMeshItem(vertexes=(vertices-center)*scale,faces=faces,vertexColors=colors,
     smooth=False,drawEdges=False,shader='shaded',glOptions='opaque')
   self.view.addItem(item)
  self.view.setCameraPosition(distance=5)
  self._loaded_info=dict(name=path.name,count=len(chunks))
  self.info.setText(self._t('{name} · {count} Teilmodell(e) · Texturfarben (UV-Sampling)',**self._loaded_info))

# VTK 9.3+ glTF importer supports skinned animations and texture materials.
# Prefer it over the legacy per-triangle color sampler when Qt/VTK is installed.
try:
 from PyQt6.QtCore import QTimer
 from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QComboBox, QDoubleSpinBox, QCheckBox, QGroupBox, QFormLayout, QSlider, QScrollArea, QSplitter
 from PyQt6.QtCore import Qt
 from vtkmodules.vtkRenderingCore import vtkLight
 from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
 from vtkmodules.vtkIOImport import vtkGLTFImporter
 from vtkmodules.vtkRenderingCore import vtkRenderer, vtkActor, vtkPolyDataMapper
 from vtkmodules.vtkFiltersSources import vtkPlaneSource
 from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
 from vtkmodules.vtkRenderingOpenGL2 import vtkOpenGLRenderer  # noqa: F401
 VTK_AVAILABLE=True
except ImportError:
 VTK_AVAILABLE=False

if VTK_AVAILABLE:
 class VTKAnimatedViewer(QWidget):
  """In-app glTF viewer with VTK's actual glTF texture and animation importer."""
  def _t(self, source, **values):
   return translate(source, getattr(self,'ui_language','de'), **values)
  def refresh_language(self, language):
   self.ui_language=language
   if hasattr(self, 'eye_pose') and self.eye_pose.count()>1:
    index=self.eye_pose.currentIndex()
    self.eye_pose.blockSignals(True)
    self.eye_pose.setItemText(0,self._t('Automatisch'))
    self.eye_pose.setItemText(1,self._t('Augen offen (Original)'))
    for i in range(2,self.eye_pose.count()):
     self.eye_pose.setItemText(i,self._t('Augenstellung {number}',number=i-1))
    self.eye_pose.setCurrentIndex(index)
    self.eye_pose.blockSignals(False)
   # Refresh captions whose meaning also reflects playback state.
   if hasattr(self,'play_button'):
    self.play_button.setText(self._t('⏸ Pause' if self.timer.isActive() else '▶ Abspielen'))
   loaded=getattr(self,'_loaded_info',None)
   if loaded:
    blink=self._t(' · Blinkdaten erkannt; Augenframes bei unterstützten Modellen aktivierbar') if loaded['blink'] else ''
    self.info.setText(self._t('{name} · {count} Original-DW2-Animation(en) · glTF-Materialien',name=loaded['name'],count=loaded['count'])+blink)
  def __init__(self):
   super().__init__()
   layout=QVBoxLayout(self)
   self.info=QLabel('glTF laden · Animation auswählen · Play/Pause')
   layout.addWidget(self.info)
   self.widget=QVTKRenderWindowInteractor(self)
   main=QHBoxLayout()
   main.addWidget(self.widget,1)
   self.settings_panel=QScrollArea()
   self.settings_panel.setWidgetResizable(True)
   self.settings_panel.setMinimumWidth(230)
   self.settings_panel.setMaximumWidth(315)
   panel=QWidget(); form=QVBoxLayout(panel)
   camera_box=QGroupBox('Kamera · Microsoft-ähnliche Steuerung')
   camera_form=QFormLayout(camera_box)
   self.camera_projection=QComboBox(); self.camera_projection.addItems(['Perspektivisch','Orthografisch'])
   self.camera_projection.currentIndexChanged.connect(self._apply_camera)
   camera_form.addRow('Projektion',self.camera_projection)
   self.camera_fov=QDoubleSpinBox();self.camera_fov.setRange(20,90);self.camera_fov.setValue(45);self.camera_fov.setSuffix('°')
   self.camera_fov.valueChanged.connect(self._apply_camera);camera_form.addRow('Sichtfeld',self.camera_fov)
   self.camera_sensitivity=QDoubleSpinBox();self.camera_sensitivity.setRange(.2,3);self.camera_sensitivity.setSingleStep(.1);self.camera_sensitivity.setValue(1)
   self.camera_sensitivity.valueChanged.connect(self._apply_camera);camera_form.addRow('Empfindlichkeit',self.camera_sensitivity)
   self.zoom_control=QDoubleSpinBox();self.zoom_control.setRange(25,250);self.zoom_control.setSingleStep(10);self.zoom_control.setValue(100);self.zoom_control.setSuffix('%')
   self.zoom_control.valueChanged.connect(self._apply_camera);camera_form.addRow('Zoom',self.zoom_control)
   self.reset_camera_button=QPushButton('Kamera zurücksetzen');self.reset_camera_button.clicked.connect(self.reset_camera)
   camera_form.addRow(self.reset_camera_button)
   self.views=QComboBox();self.views.addItems(['Ansicht wählen','Vorne','Hinten','Links','Rechts','Oben','3D schräg'])
   self.views.currentIndexChanged.connect(self._set_view);camera_form.addRow('Perspektive',self.views)
   form.addWidget(camera_box)
   motion_box=QGroupBox('Rotation');motion_form=QFormLayout(motion_box)
   self.auto_rotation_check=QCheckBox('Automatische Rotation');self.auto_rotation_check.setChecked(True)
   self.auto_rotation_check.toggled.connect(lambda v:setattr(self,'auto_rotate',v));motion_form.addRow(self.auto_rotation_check)
   self.rotation_speed=QComboBox();self.rotation_speed.addItems(['Stufe 1 · 7,5°/s','Stufe 2 · 15°/s','Stufe 3 · 30°/s']);self.rotation_speed.setCurrentIndex(1)
   motion_form.addRow('Geschwindigkeit',self.rotation_speed);form.addWidget(motion_box)
   light_box=QGroupBox('Darstellung');light_form=QFormLayout(light_box)
   self.background_choice=QComboBox();self.background_choice.addItems(['DW2 – blau/grünes Raster','Studio – hellgrau','Neutral – dunkelblau'])
   self.background_choice.currentIndexChanged.connect(self._apply_background);light_form.addRow('Hintergrund',self.background_choice)
   self.show_texture=QCheckBox('Texturen anzeigen (aus = grünes Polygon-Drahtgitter)');self.show_texture.setChecked(True)
   self.show_texture.toggled.connect(self._apply_texture_mode);light_form.addRow(self.show_texture)
   light_form.addRow(QLabel('Ohne Textur: nur grüne Polygonkanten.'))
   form.addWidget(light_box)
   form.addWidget(QLabel('Links ziehen: drehen\nRechts ziehen: verschieben\nMausrad: zoomen'))
   form.addStretch(1)
   self.settings_panel.setWidget(panel);main.addWidget(self.settings_panel)
   layout.addLayout(main,1)
   controls=QHBoxLayout()
   self.animations=QComboBox()
   self.animations.currentIndexChanged.connect(self.select_animation)
   controls.addWidget(self.animations,1)
   self.play_button=QPushButton('▶ Abspielen')
   self.play_button.clicked.connect(self.toggle_play)
   controls.addWidget(self.play_button)
   self.loop_check=QCheckBox('Wiederholen')
   self.loop_check.setChecked(True)
   controls.addWidget(self.loop_check)
   self.speed=QDoubleSpinBox()
   self.speed.setRange(0.1,3.0)
   self.speed.setSingleStep(0.1)
   self.speed.setValue(1.0)
   self.speed.setSuffix('×')
   self.speed.setToolTip('Geschwindigkeit der Original-DW2-Animation')
   controls.addWidget(self.speed)
   layout.addLayout(controls)
   eye_controls=QHBoxLayout()
   self.eye_blink_check=QCheckBox('Augen blinzeln (experimentelle Vorschau)')
   self.eye_blink_check.setChecked(True)
   self.eye_blink_check.setEnabled(False)
   self.eye_blink_check.toggled.connect(self._update_eye_pose)
   eye_controls.addWidget(self.eye_blink_check)
   self.eye_pose=QComboBox()
   self.eye_pose.addItems(['Automatisch','Augen offen (Original)'])
   self.eye_pose.setEnabled(False)
   self.eye_pose.currentIndexChanged.connect(self._update_eye_pose)
   eye_controls.addWidget(self.eye_pose)
   layout.addLayout(eye_controls)
   self._eye_player=None
   self._blink_clock=0.0
   self.timer=QTimer(self)
   self.timer.setInterval(33)
   self.timer.timeout.connect(self.next_frame)
   self.time=0.0
   self.auto_rotate=True
   self._camera_base_distance=None
   self._extra_light=None
   from collections import OrderedDict
   self._scenes=OrderedDict();self._scene_key=None;self.scene_cache_limit=4;self.last_load_cache_hit=False;self._loading_scene=False
   self.importer=None
   self.animation_durations=[]
   self.duration=0.0
   self.renderer=vtkRenderer()
   self.renderer.SetBackground(.31,.43,.61)
   self.renderer.SetBackground2(.73,.82,.94)
   self.renderer.GradientBackgroundOn()
   self.widget.GetRenderWindow().AddRenderer(self.renderer)
   self.widget.GetRenderWindow().GetInteractor().SetInteractorStyle(vtkInteractorStyleTrackballCamera())
   self.widget.Initialize()
  def set_scene_cache_limit(self,count):
   self.scene_cache_limit=max(1,min(int(count),8))
   while len(self._scenes)>self.scene_cache_limit-1:self._scenes.popitem(last=False)
  def _remember_scene(self):
   if self.importer is None or self._scene_key is None:return
   from vtkmodules.vtkRenderingCore import vtkCamera
   camera=vtkCamera();camera.DeepCopy(self.renderer.GetActiveCamera())
   eye=self._eye_player
   self._scenes[self._scene_key]={'importer':self.importer,'renderer':self.renderer,'actors':list(self._model_actors),'materials':self._saved_materials,'background':getattr(self,'_background_texture',None),'camera':camera,'durations':self.animation_durations,'info':self._loaded_info,'eye':eye,'animation':self.animations.currentIndex(),'time':self.time}
   self._scenes.move_to_end(self._scene_key)
   while len(self._scenes)>self.scene_cache_limit-1:self._scenes.popitem(last=False)
  def clear_scene(self,message=''):
   self._remember_scene();self.timer.stop();self._clear_eye_blink();self.renderer.RemoveAllViewProps();self.importer=None;self._scene_key=None;self._model_actors=[];self._saved_materials={};self.info.setText(message)
   self.widget.GetRenderWindow().Render()
  def load(self,path):
   from dw2studio.renderer.scene_cache import scene_key
   key=scene_key(path)
   if self._scene_key==key and self.importer is not None:
    self.last_load_cache_hit=True;return
   cached=self._scenes.pop(key,None)
   self._remember_scene();self._scene_key=None;self._loading_scene=True
   try:
    if cached is None:
     self.last_load_cache_hit=False;self._load_uncached(path)
    else:
     self.last_load_cache_hit=True;self.timer.stop();self._clear_eye_blink();self.renderer.RemoveAllViewProps()
     if self.renderer is not cached['renderer']:
      self.widget.GetRenderWindow().RemoveRenderer(self.renderer);self.renderer=cached['renderer']
      if not self.widget.GetRenderWindow().GetRenderers().IsItemPresent(self.renderer):self.widget.GetRenderWindow().AddRenderer(self.renderer)
     for actor in cached['actors']:self.renderer.AddActor(actor)
     self.importer=cached['importer'];self._model_actors=cached['actors'];self._saved_materials=cached['materials'];self._background_texture=cached['background'];self.animation_durations=cached['durations'];self._loaded_info=cached['info']
     self.animations.blockSignals(True);self.animations.clear()
     for i in range(self.importer.GetNumberOfAnimations()):
      self.importer.DisableAnimation(i);self.animations.addItem(self.importer.GetAnimationName(i) or f'Animation {i+1}')
     index=cached['animation'];self.animations.setCurrentIndex(index);self.animations.blockSignals(False)
     self.time=cached['time'];self.duration=self.animation_durations[index] if 0<=index<len(self.animation_durations) else 0
     if index>=0:self.importer.EnableAnimation(index);self.importer.UpdateAtTimeValue(self.time)
     self._eye_player=cached['eye']
     if self._eye_player is not None:self._eye_controls()
     self.renderer.GetActiveCamera().DeepCopy(cached['camera']);self._camera_base_distance=self.renderer.GetActiveCamera().GetDistance();self._setup_neutral_lights();self._apply_texture_mode();self._apply_background();self.refresh_language(getattr(self,'ui_language','de'))
     if self.importer.GetNumberOfAnimations():self.timer.start();self.play_button.setText(self._t('⏸ Pause'))
     self.widget.GetRenderWindow().Render()
    self._scene_key=key
   finally:self._loading_scene=False
  def _load_uncached(self,path):
   path=Path(path)
   if path.suffix.lower() not in ('.gltf','.glb'):
    raise ValueError('Für die animierte Ansicht glTF/GLB wählen (DW2-Konverter erzeugt glTF).')
   self.timer.stop()
   self._clear_eye_blink()
   self._blink_clock=0.0
   self.play_button.setText(self._t('▶ Abspielen'))
   self.renderer.RemoveAllViewProps()
   importer=vtkGLTFImporter()
   importer.SetFileName(str(path.resolve()))
   importer.SetRenderWindow(self.widget.GetRenderWindow())
   importer.Update()
   # vtkGLTFImporter can create or select its own renderer. Camera and
   # background must target that renderer, not an unused initial one.
   imported_renderer=importer.GetRenderer()
   if imported_renderer is not None:
    self.renderer=imported_renderer
    self.renderer.SetBackground(.31,.43,.61)
    self.renderer.SetBackground2(.73,.82,.94)
    self.renderer.GradientBackgroundOn()
   self._make_opaque()
   self._setup_neutral_lights()
   from dw2studio.renderer.ground_contact import model_actors
   self._model_actors=model_actors(self.renderer)
   if not self._model_actors:raise ValueError('Keine darstellbare Geometrie im Modell gefunden.')
   self._saved_materials={}
   self._apply_lighting()
   self._apply_texture_mode()
   # Keine Bodenplattform und kein künstlicher Bodenschatten.
   from dw2studio.renderer.dw2_stage import set_dw2_backdrop
   self._background_texture=set_dw2_backdrop(self.renderer)
   self._apply_background()
   self.importer=importer
   self.animations.blockSignals(True)
   self.animations.clear()
   for i in range(importer.GetNumberOfAnimations()):
    importer.DisableAnimation(i)
    self.animations.addItem(importer.GetAnimationName(i) or self._t('Animation {number}',number=i+1))
   self.animations.blockSignals(False)
   self.time=0.0
   self.animation_durations=read_gltf_animation_durations(path)
   self.duration=self.animation_durations[0] if self.animation_durations else 0.0
   if importer.GetNumberOfAnimations():
    self.animations.setCurrentIndex(0)
    importer.EnableAnimation(0)
    importer.UpdateAtTimeValue(0)
   self.renderer.ResetCamera()
   self.renderer.GetActiveCamera().Zoom(1.22)
   self._camera_base_distance=self.renderer.GetActiveCamera().GetDistance()
   self._apply_camera()
   self.renderer.ResetCameraClippingRange()
   self.widget.GetRenderWindow().Render()
   from dw2studio.renderer.blink_data import read_blinking_data
   blink=read_blinking_data(path)
   blink_info=self._t(' · Blinkdaten erkannt; Augenframes bei unterstützten Modellen aktivierbar') if blink is not None else ''
   self._loaded_info=dict(name=path.name,count=importer.GetNumberOfAnimations(),blink=blink is not None)
   self.info.setText(self._t('{name} · {count} Original-DW2-Animation(en) · glTF-Materialien',name=path.name,count=importer.GetNumberOfAnimations())+blink_info)
   if importer.GetNumberOfAnimations():
    self.timer.start()
    self.play_button.setText(self._t('⏸ Pause'))
  def enable_native_eye_blink(self, native_model:bytes, *, layout=None,frames=None)->bool:
   """Bind verified native eye poses to the real glTF PBR image texture."""
   self._clear_eye_blink()
   from dw2studio.renderer.eye_vtk import BlinkTextures
   try:
    self._eye_player=BlinkTextures(self._model_actors,native_model,layout=layout,frames=frames)
   except (ValueError,IndexError):
    self._eye_player=None
    return False
   self._eye_controls()
   return True

  def _eye_controls(self):
   self.eye_pose.blockSignals(True)
   self.eye_pose.clear()
   self.eye_pose.addItem(self._t('Automatisch'))
   self.eye_pose.addItem(self._t('Augen offen (Original)'))
   for i in range(len(self._eye_player.frames)-1):
    self.eye_pose.addItem(self._t('Augenstellung {number}',number=i+1))
   self.eye_pose.setCurrentIndex(0)
   self.eye_pose.blockSignals(False)
   self.eye_blink_check.setEnabled(True)
   self.eye_pose.setEnabled(True)
   self._update_eye_pose()
   return True

  def _clear_eye_blink(self):
   old=getattr(self,'_eye_player',None)
   if old is not None:old.restore()
   self._eye_player=None
   if hasattr(self,'eye_pose'):self.eye_pose.setEnabled(False)
   if hasattr(self,'eye_blink_check'):self.eye_blink_check.setEnabled(False)

  def _update_eye_pose(self,*args):
   if self._eye_player is None:return
   choice=self.eye_pose.currentIndex()
   default=self._eye_player.default_frame
   frame=(default if choice<=1 else choice-2)
   self._eye_player.apply(frame if self.eye_blink_check.isChecked() else default)
   self._render()

  def _make_opaque(self):
   """Keep glTF alpha/cutouts intact. Never force alpha-masked parts opaque."""
   actors=self.renderer.GetActors()
   actors.InitTraversal()
   for _ in range(actors.GetNumberOfItems()):
    actor=actors.GetNextActor()
    if actor is not None:
     actor.ForceOpaqueOff()
     actor.ForceTranslucentOff()
     actor.GetProperty().SetSpecular(0.0)
  def _setup_neutral_lights(self):
   """Soft camera-relative illumination without changing glTF textures/PBR mode."""
   self.renderer.AutomaticLightCreationOff()
   self.renderer.RemoveAllLights()
   for position,intensity in (((-0.6,0.8,1.0),1.45),((0.9,-0.35,0.65),0.65)):
    light=vtkLight()
    light.SetLightTypeToCameraLight()
    light.SetPosition(*position)
    light.SetFocalPoint(0,0,0)
    light.SetColor(1.0,1.0,1.0)
    light.SetIntensity(intensity)
    self.renderer.AddLight(light)
  def _apply_lighting(self,*args):
   """Keep imported glTF PBR materials: Phong discards their albedo maps."""
   if not hasattr(self,'_model_actors'):return
   for actor in self._model_actors:
    prop=actor.GetProperty()
    # Do NOT call SetInterpolationToPhong here: VTK glTF materials
    # commonly store the base-color map as a PBR property texture.
    prop.SetSpecular(0.0)
    prop.SetOpacity(1.0)
   self._render()
  def _apply_texture_mode(self,*args):
   """Swap whole vtkProperty objects to preserve glTF alpha/PBR texture maps."""
   if not hasattr(self,'_model_actors'):return
   from vtkmodules.vtkRenderingCore import vtkProperty
   if not hasattr(self,'_saved_materials'):self._saved_materials={}
   visible=self.show_texture.isChecked()
   for actor in self._model_actors:
    key=id(actor)
    mapper=actor.GetMapper()
    if key not in self._saved_materials:
     original_prop=actor.GetProperty()
     wire=vtkProperty()
     wire.SetRepresentationToWireframe()
     wire.SetInterpolationToFlat()
     wire.LightingOff()
     wire.SetColor(0.05,1.0,0.02)
     wire.SetAmbientColor(0.05,1.0,0.02)
     wire.SetDiffuseColor(0.05,1.0,0.02)
     wire.SetOpacity(1.0)
     wire.SetLineWidth(1.4)
     self._saved_materials[key]=(original_prop,actor.GetTexture(),
       mapper.GetScalarVisibility() if mapper else None,wire)
    original_prop,original_texture,original_scalars,wire=self._saved_materials[key]
    if visible:
     actor.SetProperty(original_prop)
     actor.SetTexture(original_texture)
     if mapper and original_scalars is not None:mapper.SetScalarVisibility(original_scalars)
    else:
     # A separate untextured property avoids touching PBR maps and alpha masks.
     actor.SetProperty(wire)
     actor.SetTexture(None)
     if mapper:mapper.ScalarVisibilityOff()
   self._render()
  def _apply_background(self,*args):
   if not hasattr(self,'renderer'):return
   choice=self.background_choice.currentIndex()
   if choice==0:
    self.renderer.SetBackground(.13,.24,.48);self.renderer.SetBackground2(.18,.45,.68)
    self.renderer.GradientBackgroundOn()
    if getattr(self,'_background_texture',None) is not None:self.renderer.SetBackgroundTexture(self._background_texture);self.renderer.TexturedBackgroundOn()
   else:
    self.renderer.TexturedBackgroundOff()
    if choice==1:
     self.renderer.SetBackground(.72,.76,.82);self.renderer.SetBackground2(.91,.93,.96)
    else:
     self.renderer.SetBackground(.08,.12,.24);self.renderer.SetBackground2(.20,.27,.43)
    self.renderer.GradientBackgroundOn()
   self._render()
  def _apply_camera(self,*args):
   if not hasattr(self,'renderer'):return
   cam=self.renderer.GetActiveCamera()
   if self.camera_projection.currentIndex()==1:cam.ParallelProjectionOn()
   else:cam.ParallelProjectionOff();cam.SetViewAngle(self.camera_fov.value())
   if self._camera_base_distance:
    cam.SetDistance(self._camera_base_distance*100/self.zoom_control.value())
    cam.SetParallelScale(max(.001,self._camera_base_distance*0.28*100/self.zoom_control.value()))
   style=self.widget.GetRenderWindow().GetInteractor().GetInteractorStyle()
   if hasattr(style,'SetMotionFactor'):style.SetMotionFactor(10*self.camera_sensitivity.value())
   self.renderer.ResetCameraClippingRange();self._render()
  def reset_camera(self):
   if self.importer is None:return
   self.renderer.ResetCamera();self._camera_base_distance=self.renderer.GetActiveCamera().GetDistance()
   self.zoom_control.blockSignals(True);self.zoom_control.setValue(100);self.zoom_control.blockSignals(False)
   self._apply_camera()
  def _set_view(self,index):
   if index==0 or self.importer is None:return
   cam=self.renderer.GetActiveCamera();f=cam.GetFocalPoint();dist=max(cam.GetDistance(),.01)
   directions={1:(0,-1,0),2:(0,1,0),3:(-1,0,0),4:(1,0,0),5:(0,0,1),6:(1,-1,.7)}
   d=directions[index];norm=sum(v*v for v in d)**.5
   cam.SetPosition(*(f[i]+dist*d[i]/norm for i in range(3)))
   cam.SetViewUp(0,1,0) if index==5 else cam.SetViewUp(0,0,1)
   self.renderer.ResetCameraClippingRange();self._render()
  def _render(self):
   if hasattr(self,'widget') and getattr(self,'importer',None) is not None and not getattr(self,'_loading_scene',False):self.widget.GetRenderWindow().Render()
  def _add_floor(self):
   from dw2studio.renderer.dw2_stage import add_round_shadow
   bounds=self.renderer.ComputeVisiblePropBounds()
   self._platform_actors=add_round_shadow(self.renderer,bounds)
  def select_animation(self,index):
   if self.importer is None or index<0:return
   self.timer.stop();self.play_button.setText(self._t('▶ Abspielen'))
   for i in range(self.importer.GetNumberOfAnimations()):self.importer.DisableAnimation(i)
   self.importer.EnableAnimation(index)
   self.time=0.0
   self.duration=self.animation_durations[index] if index<len(self.animation_durations) else 0.0
   self.importer.UpdateAtTimeValue(0)
   self.widget.GetRenderWindow().Render()
   self.timer.start();self.play_button.setText(self._t('⏸ Pause'))
  def toggle_play(self):
   if self.importer is None or self.animations.currentIndex()<0:return
   if self.timer.isActive():
    self.timer.stop();self.play_button.setText(self._t('▶ Abspielen'))
   else:
    self.timer.start();self.play_button.setText(self._t('⏸ Pause'))
  def next_frame(self):
   if self.importer is None:return
   self.time+=self.timer.interval()/1000.0*self.speed.value()
   self._blink_clock+=self.timer.interval()/1000.0
   # VTK's importer interpolates glTF animation tracks at the given time.
   # Looping duration is read from the glTF samplers where available.
   duration=getattr(self,'duration',0.0)
   if duration>0 and self.time>=duration:
    if self.loop_check.isChecked():self.time%=duration
    else:
     self.time=duration
     self.timer.stop()
     self.play_button.setText(self._t('▶ Abspielen'))
   self.importer.UpdateAtTimeValue(self.time)
   if self._eye_player is not None and self.eye_blink_check.isChecked():
    from dw2studio.core.dw2_eyes import blink_frame_at
    frame=(blink_frame_at(self._blink_clock,frame_count=len(self._eye_player.frames))
           if self.eye_pose.currentIndex()==0 else
           (self._eye_player.default_frame if self.eye_pose.currentIndex()==1
            else self.eye_pose.currentIndex()-2))
    self._eye_player.apply(frame)
   if self.auto_rotate:
    self.renderer.GetActiveCamera().Azimuth((7.5,15.0,30.0)[self.rotation_speed.currentIndex()] * self.timer.interval()/1000.0)
    self.renderer.ResetCameraClippingRange()
   self.widget.GetRenderWindow().Render()
  def closeEvent(self,event):
   self.timer.stop()
   self._clear_eye_blink();self._scenes.clear()
   super().closeEvent(event)

 ModelViewer=VTKAnimatedViewer
