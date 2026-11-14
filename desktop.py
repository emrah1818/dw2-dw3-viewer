"""Native Qt window, asynchronous Python bridge, and local read-only asset server."""
from dw2studio.version import VERSION
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit
import json
import os
import shutil
import sys
import threading
import uuid

from PyQt6.QtCore import (QObject, QThread, QUrl, QFile, QIODevice, QStandardPaths,
                         pyqtSignal, pyqtSlot, QTimer)
from PyQt6.QtGui import QAction, QIcon, QDesktopServices
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import (QWebEnginePage, QWebEngineProfile, QWebEngineScript,
                                   QWebEngineUrlRequestInterceptor)
from PyQt6.QtWebEngineWidgets import QWebEngineView
import android_api as api

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))


class AssetServer:
    """Only packaged UI and generated viewer data are exposed; no Python RPC over HTTP."""
    def __init__(self, www, cache):
        roots = {'www': Path(www).resolve(), 'viewer': Path(cache).resolve()}
        self.token = uuid.uuid4().hex
        token = self.token
        class Handler(SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                parts = unquote(urlsplit(self.path).path).strip('/').split('/')
                if len(parts) < 3 or parts[0] != token or parts[1] not in roots:
                    self.send_error(404); return
                base = roots[parts[1]]
                target = base.joinpath(*parts[2:]).resolve()
                if not target.is_relative_to(base) or not target.is_file():
                    self.send_error(404); return
                self._target = target
                super().do_GET()

            def do_HEAD(self):
                self.send_error(405)

            def translate_path(self, path):
                return str(self._target)

            def end_headers(self):
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                super().end_headers()

        Handler.extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                                  '.js': 'text/javascript', '.gltf': 'model/gltf+json',
                                  '.glb': 'model/gltf-binary'}
        self.http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f'http://127.0.0.1:{self.http.server_port}'
        self.base = self.origin + '/' + token + '/'

    def close(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(timeout=2)


def copy_export(source, target):
    """Prepare and fsync before publication; dialog owns overwrite authorization."""
    source, target = Path(source).resolve(), Path(target).resolve()
    if source == target:
        raise ValueError('Bitte einen anderen Zielpfad wählen.')
    if api.S.image_path and target == api.S.image_path.resolve():
        raise ValueError('Für das Original-Image bitte „Original überschreiben“ verwenden.')
    stamp = target.stat() if target.exists() else None
    temp = target.with_name('.' + target.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with source.open('rb') as inp, temp.open('xb') as out:
            shutil.copyfileobj(inp, out, 4 << 20)
            out.flush(); os.fsync(out.fileno())
        if stamp is None:
            from dw2studio.core.safe_publish import publish_new
            publish_new(temp, target)
        else:
            now = target.stat()
            if (now.st_size, now.st_mtime_ns, now.st_ino) != (stamp.st_size, stamp.st_mtime_ns, stamp.st_ino):
                raise ValueError('Zieldatei wurde inzwischen verändert.')
            os.replace(temp, target)
    finally:
        temp.unlink(missing_ok=True)
    return True


class Worker(QObject):
    resolved = pyqtSignal(str, str)
    active = pyqtSignal(bool)

    @pyqtSlot(str, str, str)
    def run(self, call_id, method, raw):
        self.active.emit(True)
        try:
            args = json.loads(raw)
            if method == '_save_export':
                value = copy_export(*args)
            elif method == 'overwrite_original':
                source = api._need_session().source
                _, backup = api._need_session().save(source, overwrite=True)
                value = api.open_image(str(source))
                api.UNDO.clear(); api.REDO.clear()
                value['backup'] = str(backup) if backup else None
            else:
                self.resolved.emit(call_id, api.call(method, raw))
                return
            result = {'ok': True, 'data': value}
        except Exception as exc:
            result = {'ok': False, 'error': str(exc)}
        finally:
            self.active.emit(False)
        self.resolved.emit(call_id, json.dumps(result, ensure_ascii=False))


class Bridge(QObject):
    response = pyqtSignal(str, str)
    request = pyqtSignal(str, str, str)

    def __init__(self, window, storage):
        super().__init__(window)
        self.window, self.storage = window, storage
        self.pending = 0

    def reply(self, call_id, data=None, error=None):
        self.response.emit(call_id, json.dumps({'ok': error is None, 'data': data, 'error': error}, ensure_ascii=False))

    def queue(self, call_id, method, args):
        self.pending += 1
        self.request.emit(call_id, method, json.dumps(args))

    @pyqtSlot(str, str)
    def finished(self, call_id, response):
        self.pending -= 1
        self.response.emit(call_id, response)

    @pyqtSlot(str, str, str)
    def invoke(self, call_id, method, raw):
        try:
            args = json.loads(raw)
            if method == 'app_info':
                self.reply(call_id, {'version': VERSION + ' PC', 'free_mb': shutil.disk_usage(self.storage).free >> 20})
            elif method == 'open_studio':
                self.window.open_studio()
                self.reply(call_id, True)
            elif method == 'export_hd_dialog':
                identifier=args[0]
                name,_=QFileDialog.getOpenFileName(self.window,'HD-PNG wählen (z. B. 512×1024)','','PNG (*.png)')
                if not name:self.reply(call_id);return
                port=QFileDialog.getExistingDirectory(self.window,'PC-Port-Ordner wählen')
                if not port:self.reply(call_id);return
                self.queue(call_id,'export_hd_pack',[identifier,name,port])
            elif method == 'export_port_dialog':
                if not api._need_session().edits:
                    raise ValueError('Keine Änderungen vorgemerkt.')
                pak_path = None
                if not hasattr(api.S.session, 'pak'):
                    pak_path, _ = QFileDialog.getOpenFileName(self.window, 'Passende dw2.pak wählen', '', 'DW2 PAK (*.pak)')
                    if not pak_path:
                        self.reply(call_id); return
                port = QFileDialog.getExistingDirectory(self.window, 'PC-Port-Ordner mit dw2.exe wählen')
                if not port:
                    self.reply(call_id); return
                self.queue(call_id, 'export_port_mod', [port, pak_path])
            elif method == 'port_mods_dialog':
                # Ordner wird nur über den nativen Dialog gewählt; die Oberfläche übergibt keine Pfade.
                action = args[0] if args else 'status'
                actions = {'status': 'port_mod_status', 'disable': 'port_mod_disable', 'enable': 'port_mod_enable',
                           'check': 'mod_check', 'export': 'mod_export', 'replace': 'mod_export_replace', 'import': 'mod_import',
                           'import_force': 'mod_import_force'}
                if action not in actions:
                    raise ValueError('Unbekannte Mod-Aktion.')
                if action in ('check', 'export', 'replace') and not api._need_session().edits \
                        and not api.S.digivolve_levels and not api.S.battle_camera:
                    raise ValueError('Keine Änderungen vorgemerkt.')
                port = self.last_port if action in ('export', 'replace', 'import_force') and args[1:] == ['last'] and getattr(self, 'last_port', None) \
                    else QFileDialog.getExistingDirectory(self.window, 'PC-Port-Ordner mit dw2.exe wählen')
                if not port:
                    self.reply(call_id); return
                self.last_port = port
                self.queue(call_id, actions[action], [port])
            elif method.startswith('pick_'):
                filters = {
                    'pick_image': 'DW2 Image / PAK (*.pak *.bin *.iso *.img *.cue);;Alle Dateien (*)',
                    'pick_dw3': 'DW3 / DW2003 Image (*.bin *.iso *.img *.cue);;Alle Dateien (*)',
                    'pick_file': 'Modelle / Texturen (*.glb *.gltf *.obj *.bin *.png);;Alle Dateien (*)',
                    'pick_project': 'DW2 Mod-Projekt (*.dw2mod);;Alle Dateien (*)',
                    'pick_roster': 'Spielstand / Memory Card (*.mcr *.mcd *.bin *.sav);;Alle Dateien (*)'}
                if method not in filters:
                    raise ValueError('Unbekannter Dateidialog.')
                if method == 'pick_image' and api.S.session and api.S.session.edits:
                    if QMessageBox.question(self.window, 'Image wechseln', 'Vorgemerkte Änderungen verwerfen und ein anderes Image öffnen?') != QMessageBox.StandardButton.Yes:
                        self.reply(call_id); return
                name, _ = QFileDialog.getOpenFileName(self.window, 'Datei öffnen', '', filters[method])
                if not name:
                    self.reply(call_id); return
                if method == 'pick_file':
                    self.reply(call_id, {'path': name, 'name': Path(name).name})
                else:
                    action = {'pick_image': 'open_image', 'pick_dw3': 'open_dw3', 'pick_roster': 'roster_open', 'pick_project': 'load_project'}[method]
                    self.queue(call_id, action, [name])
            elif method == 'save_export':
                source, suggested = args
                name, _ = QFileDialog.getSaveFileName(self.window, 'Datei speichern', str(Path.home() / Path(suggested).name))
                if not name:
                    self.reply(call_id, False); return
                self.queue(call_id, '_save_export', [source, name])
            elif method in api._METHODS or method == 'overwrite_original':
                # Configuration and source paths are controlled by native file dialogs.
                if method in {'configure', 'open_image', 'open_dw3', 'export_port_mod', 'export_hd_pack', 'port_mod_status', 'port_mod_disable', 'port_mod_enable', 'mod_check', 'mod_export', 'mod_export_replace', 'mod_import', 'mod_import_force', 'adopt_image'}:
                    raise ValueError('Diese Methode ist dem Desktop vorbehalten.')
                self.queue(call_id, method, args)
            else:
                raise ValueError('Unbekannte Desktop-Methode: ' + method)
        except Exception as exc:
            self.reply(call_id, error=str(exc))


class LocalOnly(QWebEngineUrlRequestInterceptor):
    def __init__(self, origin, parent=None):
        super().__init__(parent); self.origin = origin

    def interceptRequest(self, info):
        u = info.requestUrl()
        if u.scheme() in ('data', 'blob', 'qrc', 'about'):
            return
        if f'{u.scheme()}://{u.host()}:{u.port()}' != self.origin:
            info.block(True)


class Page(QWebEnginePage):
    def __init__(self, profile, origin, parent):
        super().__init__(profile, parent); self.origin = origin

    def acceptNavigationRequest(self, url, kind, main):
        return url.toString().startswith(self.origin + '/') or url.scheme() == 'about'

    def javaScriptConsoleMessage(self, level, message, line, source):
        print(f'Web: {message} ({source}:{line})', file=sys.stderr)


class Desktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DW2 Mod Studio ' + VERSION)
        self.resize(1540, 940)
        self.setMinimumSize(800, 600)
        self.setWindowIcon(QIcon(str(ROOT / 'assets/DW2_3D_Viewer.ico')))
        storage = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / '4.0'
        storage.mkdir(parents=True, exist_ok=True)
        api.configure(str(storage), '', str(ROOT / 'data'))
        self.server = AssetServer(ROOT / 'www', api.CACHE)
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)
        self.profile = QWebEngineProfile('DW2Desktop40', self)
        self.profile.setPersistentStoragePath(str(storage / 'browser'))
        self.profile.setCachePath(str(storage / 'browser-cache'))
        self.interceptor = LocalOnly(self.server.origin, self.profile)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        self.page = Page(self.profile, self.server.origin, self.view)
        self.view.setPage(self.page)
        self.bridge = Bridge(self, storage)
        self.worker_thread = QThread(self)
        self.worker = Worker()
        self.worker.moveToThread(self.worker_thread)
        self.bridge.request.connect(self.worker.run)
        self.worker.resolved.connect(self.bridge.finished)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.start()
        self.channel = QWebChannel(self.page)
        self.channel.registerObject('desktop', self.bridge)
        self.page.setWebChannel(self.channel)
        resource = QFile(':/qtwebchannel/qwebchannel.js')
        if not resource.open(QIODevice.OpenModeFlag.ReadOnly):
            raise RuntimeError('Qt WebChannel JavaScript fehlt.')
        javascript = bytes(resource.readAll()).decode('utf-8')
        resource.close()
        javascript += '\nwindow.DW2_DESKTOP=true; window.DW2_BASE=' + json.dumps(self.server.base + 'viewer/') + ';\n'
        javascript += '''window.__desktopReady = new Promise(resolve => {
          new QWebChannel(qt.webChannelTransport, channel => {
            const bridge = channel.objects.desktop;
            window.Android = {invoke: (id, method, args) => bridge.invoke(id, method, args)};
            bridge.response.connect((id, result) => window.__resolve?.(id, result));
            resolve();
          });
        });'''
        script = QWebEngineScript()
        script.setName('DW2 Desktop bridge')
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setSourceCode(javascript)
        self.page.scripts().insert(script)
        menu = self.menuBar().addMenu('PC-Werkzeuge')
        action = QAction('Mod Studio · 3D-Import / Rigging / Vollfarben', self)
        action.triggered.connect(self.open_studio); menu.addAction(action)
        fullscreen = QAction('Vollbild', self)
        fullscreen.setShortcut('F11')
        fullscreen.triggered.connect(lambda: self.showNormal() if self.isFullScreen() else self.showFullScreen())
        menu.addAction(fullscreen)
        self.studios = []
        self.view.setUrl(QUrl(self.server.base + 'www/index.html'))

    def open_studio(self):
        from studio import Main
        window = Main()
        window.setAttribute(__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.WidgetAttribute.WA_DeleteOnClose)
        self.studios.append(window)
        window.destroyed.connect(lambda: self.studios.remove(window) if window in self.studios else None)
        window.show()
        # Deliberately separate edit sessions: transfer staged changes with .dw2mod projects.

    def closeEvent(self, event):
        if self.bridge.pending:
            QMessageBox.information(self, 'Vorgang läuft', 'Bitte den laufenden Vorgang abschließen lassen.')
            event.ignore(); return
        dirty = (api.S.session and api.S.session.edits) or (api.S.roster and api.S.roster.dirty) \
            or api.S.digivolve_levels or api.S.battle_camera
        if dirty and QMessageBox.question(self, 'Ungespeicherte Änderungen', 'Schließen und vorgemerkte Änderungen verwerfen? Zum Sichern abbrechen und ein Mod-Projekt speichern.') != QMessageBox.StandardButton.Yes:
            event.ignore(); return
        for studio in list(self.studios):
            if not studio.close():
                event.ignore(); return
        self.worker_thread.quit()
        self.worker_thread.wait()
        self.view.stop()
        self.server.close()
        super().closeEvent(event)
