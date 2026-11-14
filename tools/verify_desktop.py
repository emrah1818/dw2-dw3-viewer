import sys, os, json, tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(root),str(root/'tests')]
from test_native_anim import make_iso
folder=Path(tempfile.mkdtemp());image=make_iso(folder)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QGuiApplication
QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
from PyQt6.QtWidgets import QApplication,QFileDialog
from desktop import Desktop
app=QApplication(['dw2-integration']); w=Desktop(); w.view.resize(1540,850); passed=False
QFileDialog.getOpenFileName=lambda *args: (str(image),'')
def begin():
 w.page.runJavaScript("document.getElementById('btn-open').click()")
 QTimer.singleShot(2500,select)
def select():
 w.page.runJavaScript("document.querySelector('#list .item')?.click()")
 QTimer.singleShot(3000,check)
def check():
 w.page.runJavaScript("JSON.stringify({ready:!!window.__dw2view,bridge:!!window.Android,models:document.querySelectorAll('#list .item').length,name:document.getElementById('v-name').textContent,animations:document.getElementById('anim').options.length,log:document.getElementById('log').textContent,toast:document.getElementById('toast').textContent,inspector:document.getElementById('page-tools').classList.contains('active'),viewport:innerWidth})",done)
def done(value):
 global passed
 data=json.loads(value)
 passed=data['ready'] and data['bridge'] and data['models']==2 and data['name']=='Agumon' and data['animations']==4 and not data['toast']
 print('INTEGRATION_RESULT',value,flush=True)
 w.close();app.quit()
w.view.loadFinished.connect(lambda ok: QTimer.singleShot(1000,begin))
QTimer.singleShot(20000,app.quit);app.exec()
sys.exit(0 if passed else 1)
