import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import pytest

@pytest.fixture(scope='session')
def qapp():
    from PyQt6.QtWidgets import QApplication
    app=QApplication.instance() or QApplication([])
    yield app

@pytest.fixture
def window(qapp,monkeypatch,tmp_path):
    import vtk
    if not hasattr(vtk,'vtkEGLRenderWindow'):pytest.skip('EGL unavailable for headless Qt/VTK verification')
    from PyQt6.QtWidgets import QWidget
    import dw2studio.renderer.viewer as renderer
    class EGLWidget(QWidget):
        def __init__(self,parent):
            super().__init__(parent);self.win=vtk.vtkEGLRenderWindow();self.win.SetOffScreenRendering(1);self.win.SetSize(400,400);self.interactor=vtk.vtkRenderWindowInteractor();self.interactor.SetRenderWindow(self.win)
        def GetRenderWindow(self):return self.win
        def Initialize(self):pass
    monkeypatch.setattr(renderer,'QVTKRenderWindowInteractor',EGLWidget)
    import studio as main
    monkeypatch.setattr(main,'CACHE',tmp_path/'cache')
    w=main.Main();w.prefetch.setChecked(False)
    errors=[]
    monkeypatch.setattr(w,'warning',lambda title,error:errors.append((title,str(error))))
    w.test_errors=errors
    yield w
    w.session=None;w.loader.stop();assert w.loader.wait(5000)
    for job in w.eye_jobs:job.requestInterruption();assert job.wait(5000)
    w.close();w.viewer.widget.GetRenderWindow().Finalize();qapp.processEvents()
