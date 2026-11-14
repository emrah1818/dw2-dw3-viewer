"""Standalone navigation, stale-result guards, cache isolation and native batching."""
import json
import os
import threading
import time
from pathlib import Path
from types import SimpleNamespace
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from dw2studio.core.fast_loading import scan_image,ConversionQueue,ModelRequest
from dw2studio.core.catalog import DigimonCandidate
from dw2studio.core.edit_session import EditSession
from test_native_rom_bridge import image_fixture
from test_rig_import_v8 import project


def test_index_cache_skips_full_scan_and_invalidates_changed_image(tmp_path):
    image,cue,entry,_,_=image_fixture(tmp_path);calls=[]
    def scanner(*args):calls.append(True);return [entry]
    entries,catalog,first=scan_image(cue,tmp_path/'cache',scanner)
    _,_,second=scan_image(image,tmp_path/'cache',scanner)
    assert len(calls)==1 and not first['cached'] and second['cached']
    assert entries==[entry] and catalog[0].id==3
    # Same size, changed timestamp must invalidate the saved index.
    st=image.stat();os.utime(image,ns=(st.st_atime_ns,st.st_mtime_ns+1000000))
    assert not scan_image(cue,tmp_path/'cache',scanner)[2]['cached'];assert len(calls)==2
    index=next((tmp_path/'cache'/'indexes').glob('*.json'));index.write_text('{broken')
    assert not scan_image(image,tmp_path/'cache',scanner)[2]['cached'];assert len(calls)==3


def wait_until(predicate):
    limit=time.monotonic()+5
    while not predicate() and time.monotonic()<limit:QTest.qWait(10)
    assert predicate()


def test_latest_foreground_cancels_old_and_background_does_not_win(qapp,tmp_path):
    class Queue(ConversionQueue):
        def __init__(self):super().__init__();self.started=threading.Event();self.completed=[]
        def convert(self,job):
            if job.key=='old':
                self.started.set()
                while not self.cancelled():time.sleep(.002)
                raise RuntimeError('cancelled')
            self.completed.append(job.key);return tmp_path/job.key
    queue=Queue();ready=[];errors=[];queue.ready.connect(lambda key,*args:ready.append(key));queue.failed.connect(lambda *args:errors.append(args));queue.start()
    def request(key):return ModelRequest(key,'',[],tmp_path,None,'',{})
    try:
        queue.submit(request('old'));assert queue.started.wait(2)
        queue.submit(request('neighbor'),foreground=False);queue.submit(request('new'))
        wait_until(lambda:len(ready)==2)
        assert ready==['new','neighbor'] and not errors
    finally:queue.stop();assert queue.wait(2000)


def test_cancelled_conversion_never_publishes_partial_cache(tmp_path,monkeypatch):
    import dw2studio.core.fast_loading as module
    image,_,entry,digi,_=image_fixture(tmp_path);queue=ConversionQueue();queue.active='x'
    job=ModelRequest('x',str(image),[entry],tmp_path/'cache',digi,'fake',{})
    def convert(exe,src,dest,**kwargs):
        dest.mkdir();(dest/'M003AGUM.gltf').write_text('{partial');queue.active_cancelled=True
    monkeypatch.setattr(module,'convert_models',convert)
    with pytest.raises(RuntimeError,match='abgebrochen'):queue.convert(job)
    assert not (job.folder/'converted').exists() and not list(job.folder.glob('conversion-*'))


def test_doubleclick_and_keyboard_navigation(window,qapp,monkeypatch):
    window.catalog=[DigimonCandidate(3,'AGUM','Agumon'),DigimonCandidate(4,'BETA','Betamon')];window.refresh_list();seen=[]
    # Timer was connected at construction, so observe via a minimal request path.
    monkeypatch.setattr(window,'request_for',lambda c:SimpleNamespace(key=str(c.id),converter='fake',folder=Path('/nonexistent')))
    monkeypatch.setattr(window.loader,'submit',lambda request,*args,**kwargs:seen.append(request.key))
    window.session=SimpleNamespace(_check_source=lambda:None);window.image='dummy';window.index_key='test';window.revisions={}
    monkeypatch.setattr('main.active_replacement',lambda *args:None);monkeypatch.setattr('main.cache_key',lambda *args:'test')
    window.show();qapp.processEvents();assert not seen
    item=window.digimon.visualItemRect(window.digimon.item(0)).center()
    QTest.mouseClick(window.digimon.viewport(),Qt.MouseButton.LeftButton,pos=item)
    QTest.mouseDClick(window.digimon.viewport(),Qt.MouseButton.LeftButton,pos=item);qapp.processEvents()
    assert seen==['3']
    QTest.keyClick(window.digimon,Qt.Key.Key_Down);QTest.qWait(120)
    assert window.current.id==4 and seen==['3','4']
    QTest.keyClick(window.digimon,Qt.Key.Key_Up);QTest.qWait(120)
    assert window.current.id==3 and seen[-1]=='3'
    window.session=None


def test_stale_converter_result_does_not_replace_selected_model(window,monkeypatch,tmp_path):
    window.index_key='disc';window.wanted='disc/004BETA/0';window.current=DigimonCandidate(4,'BETA','Betamon');seen=[]
    monkeypatch.setattr(window,'display_for',lambda *args,**kwargs:seen.append(args))
    window.model_ready('disc/003AGUM/0',str(tmp_path/'a.gltf'),.1)
    window.model_ready('other/004BETA/0',str(tmp_path/'b.gltf'),.1)
    assert not seen and '004BETA' not in window.model_paths
    window.revisions['004BETA']=1;window.model_ready('disc/004BETA/0','old.gltf',.1);assert not seen


def test_real_vtk_scene_reuse_preserves_model_animation_and_external_dependencies(window,tmp_path):
    p=project(tmp_path);p.assignment[:]=[0,1];a=tmp_path/'a.gltf';p.export_gltf(a)
    p.scale=2.;b=tmp_path/'b.gltf';p.export_gltf(b)
    viewer=window.viewer;start=time.perf_counter();viewer.load(a);first=time.perf_counter()-start;viewer.timer.stop();importer=viewer.importer;actors=viewer._model_actors[:]
    viewer.load(b);viewer.timer.stop();assert not viewer.last_load_cache_hit;assert viewer.importer is not importer
    start=time.perf_counter();viewer.load(a);warm=time.perf_counter()-start;viewer.timer.stop()
    assert viewer.last_load_cache_hit and viewer.importer is importer
    assert all(x is y for x,y in zip(actors,viewer._model_actors))
    importer.EnableAnimation(0);importer.UpdateAtTimeValue(0);before=[actor.GetBounds() for actor in actors];importer.UpdateAtTimeValue(1/30)
    assert [actor.GetBounds() for actor in actors]!=before
    viewer.load(b);viewer.timer.stop()
    doc=json.loads(a.read_text());uri=doc.get('images',[{}])[0].get('uri','')
    if uri and not uri.startswith('data:'):
        dependency=a.parent/uri;st=dependency.stat();os.utime(dependency,ns=(st.st_atime_ns,st.st_mtime_ns+1000000));viewer.load(a);viewer.timer.stop();assert not viewer.last_load_cache_hit
    viewer.set_scene_cache_limit(1);assert not viewer._scenes
    print(f'\nVTK synthetic two-bone rig: first={first:.4f}s RAM={warm:.4f}s')


def test_save_waits_for_reader_and_rejects_wrong_extension(window,tmp_path,monkeypatch):
    image=tmp_path/'game.iso';image.write_bytes(b'A'*4096);window.session=EditSession(image,2048);window.image_path=image
    from dw2studio.core.disc import Entry
    window.session.stage(Entry('m',0,20,False),b'B'*20)
    window.write_image(tmp_path/'bad.bin');assert window.test_errors and not (tmp_path/'bad.bin').exists()
    window.loader.active='busy';window.write_image(tmp_path/'new.iso');assert window.writer is None and window._pending_write
    window.loader.active=None;wait_until(lambda:(tmp_path/'new.iso').exists());wait_until(lambda:window.writer.isFinished());wait_until(lambda:window.session.source==tmp_path/'new.iso')
    assert (tmp_path/'new.iso').stat().st_size==4096 and image.read_bytes()==b'A'*4096


def test_native_eye_button_stages_repeated_edits_without_writing_image(window,tmp_path,monkeypatch):
    from PIL import Image
    from PyQt6.QtWidgets import QFileDialog
    from test_eye_variants_v26 import synthetic_agumon_style
    from dw2studio.core.disc import Entry
    from dw2studio.core.dw2_eyes import eye_layout
    model=synthetic_agumon_style();image=tmp_path/'eyes.iso';original=model.ljust(20480,b'\0');image.write_bytes(original)
    entry=Entry('M003TEST.BIN',0,len(model),False);digi=DigimonCandidate(3,'TEST','Test',[entry])
    window.image=str(image);window.image_path=image;window.entries=[entry];window.current=window.loaded_digimon=digi;window.active_digimon_key='003TEST';window.session=EditSession(image,2048)
    monkeypatch.setattr(window,'_confirm_native_colors',lambda *args,**kwargs:True);monkeypatch.setattr(window,'load_digimon',lambda:None)
    layout=eye_layout(model);png=tmp_path/'eyes.png';incoming=window.native_image(window._native_selection(),True)
    for color in ((0,255,0,255),(0,0,255,255)):
        for x,y,w,h in layout.sources+(layout.target,):incoming.paste(color,(x,y,x+w,y+h))
        incoming.save(png);monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *args,**kwargs:(str(png),''));window.write_game_eyes()
        assert not window.test_errors and len(window.session.edits)==1 and image.read_bytes()==original
        decoded=window.native_image(window._native_selection(),True)
        x,y,w,h=layout.target;actual=decoded.getpixel((x+w//2,y+h//2));assert all(abs(a-b)<=8 for a,b in zip(actual,color))
    assert len(window.session.current(entry))==len(model)


def test_quick_return_to_cancelled_active_model_requeues_it(tmp_path):
    queue=ConversionQueue();queue.active='a';queue.priority='a'
    def request(key):return ModelRequest(key,'',[],tmp_path,None,'',{})
    queue.submit(request('b'));assert queue.active_cancelled
    queue.submit(request('a'));assert 'a' in queue.jobs and queue.priority=='a' and 'b' not in queue.jobs
    queue.clear();queue.submit(request('a'));assert 'a' in queue.jobs
