"""DW2 Mod Studio desktop entry point (window title; the storage name stays 'DW2 3D Viewer')."""
from dw2studio.version import VERSION
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QGuiApplication


def main():
    # Chromium and the retained VTK studio share OpenGL contexts.
    QGuiApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName('DW2 3D Viewer')
    app.setApplicationVersion(VERSION)
    app.setOrganizationName('DW2 3D Viewer')
    from desktop import Desktop
    window = Desktop()
    window.show()
    if '--smoke-test' in sys.argv:
        from PyQt6.QtCore import QTimer
        from pathlib import Path
        import json
        report = next((x.split('=', 1)[1] for x in sys.argv if x.startswith('--smoke-report=')), 'smoke-report.json')
        finished = False
        def finish(value):
            nonlocal finished
            if finished:
                return
            finished = True
            ok = bool(value)
            Path(report).write_text(json.dumps({'ok': ok, 'version': VERSION, 'check': 'frozen Qt / WebEngine / WebGL / Python bridge / nine areas'}), encoding='utf-8')
            window.close()
            app.exit(0 if ok else 1)
        def check(ok):
            if not ok:
                finish(False)
            else:
                QTimer.singleShot(3000, lambda: window.page.runJavaScript('!!window.__dw2view && !!window.Android && !!document.getElementById("b-port-mod") && document.querySelectorAll("#tabs .tab").length >= 9 && ["page-files","page-attacks","page-evo","page-domains","page-dw3"].every(id => !!document.getElementById(id))', finish))
        window.view.loadFinished.connect(check)
        QTimer.singleShot(30000, lambda: finish(False))
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
