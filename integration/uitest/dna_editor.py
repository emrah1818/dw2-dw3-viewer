"""Click through the real DNA UI and Python API using synthetic PAK tables."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import shutil
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
import android_api as api
from fixtures017 import open_session

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

BOOT = """
window.DW2_BASE='/';
localStorage.setItem('lang','de');
window.Android={invoke(id, method, raw) {
  window.__python(method, raw).then(reply => window.__resolve(id, reply));
}};
"""

with tempfile.TemporaryDirectory() as temp:
    folder = Path(temp)
    _, _, pak = open_session(folder)
    api.configure(str(folder / 'store'), '')
    api.open_image(str(pak))
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'www')))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=os.environ.get('DW2_TEST_BROWSER') or shutil.which('google-chrome') or shutil.which('chromium'),
                args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
            page = browser.new_page(viewport={'width': 1400, 'height': 1100})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.expose_function('__python', api.call)
            page.add_init_script(BOOT)
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            page.wait_for_function('!!window.__desktop && !!window.__dw2')
            page.evaluate("""() => {
                window.__dw2.state.id=null;
                window.__dw2.state.image={source_kind:'pak', name:'synthetic.pak'};
                window.__desktop.show('page-evo');
            }""")
            page.locator('#dna-a option[value="84"]').wait_for(state='attached')
            for key, value in [('a','84'), ('b','131'), ('result','131'), ('rank','3')]:
                page.locator('#dna-' + key).select_option(value)
            page.locator('#dna-save').click()
            page.locator('[data-dna-edit="0"]').wait_for()
            assert api.S.dna_overrides == {(84, 131): (131, 3)}
            assert 'Mega' in page.locator('#dna-list').inner_text()
            # Editing the existing unordered pair replaces it, never appends a duplicate.
            page.locator('[data-dna-edit="0"]').click()
            assert page.locator('#dna-rank').input_value() == '3'
            page.locator('#dna-a').select_option('131')
            page.locator('#dna-b').select_option('84')
            page.locator('#dna-rank').select_option('2')
            page.locator('#dna-save').click()
            page.wait_for_function("document.querySelector('#dna-list').textContent.includes('Ultra')")
            assert api.S.dna_overrides == {(84, 131): (131, 2)}
            page.locator('[data-dna-delete="0"]').click()
            page.wait_for_function("!document.querySelector('[data-dna-delete]')")
            assert api.S.dna_modified and not api.S.dna_overrides
            assert 'Keine eigenen DNA-Regeln' in page.locator('#dna-note').inner_text()
            assert not errors, errors
            browser.close()
            print('DNA UI: create, reversed-pair replacement, rank editing and deletion passed')
    finally:
        server.shutdown()
