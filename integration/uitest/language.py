"""Automatische Sprache: Oberfläche folgt der Browser-/Systemsprache (de -> Deutsch, sonst Englisch),
Umschalten in beide Richtungen stellt auch zur Laufzeit gebaute Texte richtig.   language.py WORKDIR DW2_PAK"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from serve import make
from playwright.sync_api import sync_playwright
work, pak = sys.argv[1:3]
srv = make(work, pak)
fails = 0
def check(what, ok, detail=''):
    global fails; fails += not ok
    print(('PASS ' if ok else 'FAIL ') + what + (' | ' + str(detail) if detail != '' else ''), flush=True)
TXT = '() => [document.documentElement.lang, document.querySelector("[data-page=page-files]")?.textContent.trim(), [...document.querySelectorAll("button")].map(b => b.textContent.trim()).find(t => /Gewähltes Digimon bearbeiten|Edit selected Digimon/.test(t)) || "", document.querySelector("#b-hd-off")?.textContent]'
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    for loc, want in (('de-DE', 'de'), ('en-US', 'en'), ('fr-FR', 'en')):
        pg = b.new_context(locale=loc).new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{srv.server_port}/'); pg.wait_for_function('window.__dw2 !== undefined'); pg.wait_for_timeout(500)
        r = pg.evaluate(TXT)
        check(f'Systemsprache {loc} -> {want}', r[0] == want, r)
        if loc == 'de-DE':
            check('Deutsche Texte', 'Dateien' in r[1] and 'Gewähltes Digimon bearbeiten' in r[2] and r[3] == 'HD-Vorschau aus', r)
            pg.evaluate("() => { const s = document.querySelector('#lang'); s.value = 'en'; s.dispatchEvent(new Event('change')); }"); pg.wait_for_timeout(300); r2 = pg.evaluate(TXT)
            check('Umschalten auf Englisch', 'Files' in r2[1] and 'Edit selected Digimon' in r2[2] and r2[3] == 'HD preview off', r2)
            pg.evaluate("() => { const s = document.querySelector('#lang'); s.value = 'de'; s.dispatchEvent(new Event('change')); }"); pg.wait_for_timeout(300); r3 = pg.evaluate(TXT)
            check('Zurück auf Deutsch', r3 == r, r3)
            pg.evaluate("() => { const s = document.querySelector('#lang'); s.value = 'en'; s.dispatchEvent(new Event('change')); }"); pg.reload(); pg.wait_for_function('window.__dw2 !== undefined'); pg.wait_for_timeout(300)
            check('Eigene Wahl bleibt gespeichert', pg.evaluate(TXT)[0] == 'en')
        else:
            check('Englische Texte', 'Files' in r[1] and 'Edit selected Digimon' in r[2] and r[3] == 'HD preview off', r)
        check(f'keine JS-Fehler ({loc})', not errs, errs)
        pg.context.close()
    b.close()
print('FAILS', fails); sys.exit(1 if fails else 0)
