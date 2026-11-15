"""Headless test bridge for the Studio UI: serves www/ and the cache, answers the UI's native()
calls over HTTP with android_api (the same dispatcher as the desktop app). No game data inside.
    serve.py WORKDIR DW2_IMAGE [DW3_IMAGE] [PORT]"""
import json, sys, threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import android_api as api

BOOT = """<script>
window.DW2_BASE = '/viewer/'; window.DW2_DESKTOP = true;
window.Android = { invoke(id, method, raw) {
  fetch('/api', { method: 'POST', body: JSON.stringify({ method, raw }) }).then(r => r.text()).then(j => window.__resolve(id, j))
    .catch(e => window.__resolve(id, JSON.stringify({ ok: false, error: String(e) }))); } };
</script>"""


def make(work, image, dw3=None, port=0):
    api.configure(work, '')
    picks = {'pick_image': ('open_image', image), 'pick_dw3': ('open_dw3', dw3)}
    opened = {}

    class H(SimpleHTTPRequestHandler):
        def log_message(self, *a): pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            method, raw = body['method'], body['raw']
            if method in picks:
                real, path = picks[method]
                if method not in opened:        # opening again would drop the session's edits
                    opened[method] = api.call(real, json.dumps([path]))
                out = opened[method]
            else:
                out = api.call(method, raw)
            data = out.encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)

        def do_GET(self):
            path = self.path.split('?')[0]
            if path in ('/', '/index.html'):
                html = (ROOT / 'www/index.html').read_text(encoding='utf-8').replace('<head>', '<head>' + BOOT, 1).encode()
                self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(html))); self.end_headers(); self.wfile.write(html); return
            base = api.CACHE if path.startswith('/viewer/') else ROOT / 'www'
            rel = path[len('/viewer/'):] if path.startswith('/viewer/') else path.lstrip('/')
            target = (base / rel).resolve()
            if not target.is_relative_to(Path(base).resolve()) or not target.is_file():
                self.send_error(404); return
            data = target.read_bytes()
            kind = {'.js': 'text/javascript', '.css': 'text/css', '.glb': 'model/gltf-binary', '.png': 'image/png',
                    '.json': 'application/json', '.html': 'text/html'}.get(target.suffix.lower(), 'application/octet-stream')
            self.send_response(200); self.send_header('Content-Type', kind); self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)

    srv = ThreadingHTTPServer(('127.0.0.1', port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


if __name__ == '__main__':
    s = make(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None, int(sys.argv[4]) if len(sys.argv) > 4 else 8765)
    print('http://127.0.0.1:%d/' % s.server_port, flush=True)
    threading.Event().wait()
