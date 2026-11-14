import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication,QFileDialog,QDialog,QMessageBox
from test_rig_import_v8 import project,native_model,animation_bytes,obj_file
from dw2studio.gui.rig_dialog import RigImportDialog
from dw2studio.core.catalog import DigimonCandidate
from dw2studio.core.disc import Entry
from dw2studio.core.edit_session import EditSession
from dw2studio.core.gltf_document import pack_glb


@pytest.fixture
def dialog(tmp_path,qapp):
    app=qapp;w=RigImportDialog(project(tmp_path),tmp_path/'cache');w.resize(1320,760);w.show();app.processEvents()
    yield w
    w.reject();app.processEvents()


def test_body_assignment_undo_and_animation_controls(dialog):
    w=dialog;assert not w.commit_button.isEnabled()
    w.select_group('body');w.assign_selection();assert w.project.assignment.tolist()==[0,-1]
    w.bones.setCurrentItem(w.bone_items[1]);w.select_group('head');w.assign_selection();assert w.commit_button.isEnabled()
    w.undo_assignment();assert w.project.assignment.tolist()==[0,-1]
    w.assign_selection();w.label.setCurrentText('Kopf / Mund');w.motion.setValue(.5);w.frame.setValue(1)
    assert w.project.settings[1].label=='Kopf / Mund' and w.project.settings[1].motion_scale==.5
    initial,_=w.project.preview('A003TEST.BIN',0,0);moved,_=w.project.preview('A003TEST.BIN',0,1)
    assert not np.allclose(moved[1],initial[1])
    w.commit();assert w.result()==QDialog.DialogCode.Accepted and w.preview_path.is_file()
    assert w.animation_results['A003TEST.BIN']!=animation_bytes()


def test_blink_controls_and_mapping_restore(dialog,tmp_path,monkeypatch):
    w=dialog;w.project.assignment[:]=[0,1];w.edit_blink.setChecked(True);fields=w.eye_fields[0]
    for key,value in {'x':0,'y':0,'w':8,'h':4,'open_x':8,'open_y':0,'half_x':16,'half_y':0,'closed_x':24,'closed_y':0}.items():fields[key].setValue(value)
    fields['enabled'].setChecked(True);assert w.project._blink_bytes()[:4]==bytes([0,0,2,4])
    filename=tmp_path/'saved.dw2rig';w.project.save(filename)
    w.project.assignment[:]=-1
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *args,**kwargs:(str(filename),''))
    w.load_mapping();assert w.project.assignment.tolist()==[0,1] and w.eye_fields[0]['w'].value()==8


def test_import_button_opens_dialog_and_stages_model_and_animation(window,tmp_path,monkeypatch):
    import dw2studio.gui.rig_dialog as module
    model=native_model();animation=animation_bytes();image=tmp_path/'game.iso';payload=bytearray(65536);payload[:len(model)]=model;payload[12*2048:12*2048+len(animation)]=animation;image.write_bytes(payload)
    m=Entry('AAA/4.AAA/MODEL/M003TEST.BIN',0,len(model),False);a=Entry('AAA/4.AAA/MODEL/A003TEST.BIN',12,len(animation),False)
    window.image=str(image);window.image_path=image;window.index_key='test';window.session=EditSession(image,2048);window.entries=[m,a];window.catalog=[DigimonCandidate(3,'TEST','Test',[m,a])]
    window.refresh_list();path=obj_file(tmp_path)
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *args,**kwargs:(str(path),''))
    seen=[]
    def exec_dialog(self):
        seen.append(True);assert image.read_bytes()==payload
        self.project.assignment[:]=[0,1];self.project.settings[1].motion_scale=.5;self.commit();return self.result()
    monkeypatch.setattr(module.RigImportDialog,'exec',exec_dialog)
    window.import_model();assert seen and len(window.session.edits)==2 and image.read_bytes()==payload
    assert window.session.current(a)!=animation and window.session.current(m)!=model
    output,_=window.session.save(tmp_path/'mod.iso');loaded=EditSession(output,2048)
    assert loaded.current(a)==window.session.current(a) and output.stat().st_size==len(payload)


@pytest.mark.parametrize('binary',[False,True])
def test_exported_rig_plays_in_real_vtk(tmp_path,binary):
    import vtk
    if not hasattr(vtk,'vtkEGLRenderWindow'):pytest.skip('EGL render context unavailable.')
    p=project(tmp_path);p.assignment[:]=[0,1];gltf=tmp_path/'rig.gltf';p.export_gltf(gltf)
    if binary:pack_glb(gltf,tmp_path/'rig.glb');gltf=tmp_path/'rig.glb'
    win=vtk.vtkEGLRenderWindow();win.SetOffScreenRendering(1);renderer=vtk.vtkRenderer();win.AddRenderer(renderer)
    importer=vtk.vtkGLTFImporter();importer.SetFileName(str(gltf));importer.SetRenderWindow(win);importer.Update()
    try:
        assert importer.GetNumberOfAnimations()==2;importer.EnableAnimation(0);importer.UpdateAtTimeValue(0)
        actors=importer.GetRenderer().GetActors();actors.InitTraversal();items=[actors.GetNextActor() for _ in range(actors.GetNumberOfItems())]
        assert len(items)==2
        before=min(item.GetBounds()[0] for item in items);importer.UpdateAtTimeValue(1/30)
        after=min(item.GetBounds()[0] for item in items);assert after<before-5
        win.Render()
    finally:win.Finalize()
