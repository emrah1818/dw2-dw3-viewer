"""DW3-Namen durch die echte Oberfläche (headless Chrome): Liste mit Namen, Suche, Ansehen mit Vorschaubild,
erneutes Öffnen, Name im Animationseditor.   dw3names.py WORKDIR DW2_PAK DW3_BIN OUTDIR"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from serve import make
from playwright.sync_api import sync_playwright
work, pak, dw3 = sys.argv[1:4]
out = Path(sys.argv[4]); out.mkdir(parents=True, exist_ok=True)
srv = make(work, pak, dw3)
fails = 0
def check(what, ok, detail=''):
    global fails; fails += not ok
    print(('PASS ' if ok else 'FAIL ') + what + (' | ' + str(detail) if detail != '' else ''), flush=True)
def first_names(pg, n=4):
    return pg.evaluate(f'() => [...document.querySelectorAll("#dw3-list .dw3-item b")].slice(0, {n}).map(b => b.textContent)')
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_page(viewport={'width': 1400, 'height': 1100})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{srv.server_port}/'); pg.wait_for_function('window.__dw2 !== undefined')
    N = lambda m, *a: pg.evaluate('([m, a]) => window.__dw2.native(m, ...a)', [m, list(a)])
    pg.click('#btn-open'); pg.wait_for_function('window.__dw2.state.catalog.length > 0', timeout=120000)
    pg.click('button[data-page="page-dw3"]'); pg.click('#dw3-open')
    pg.wait_for_function('() => document.querySelectorAll("#dw3-list .dw3-item").length > 200', timeout=180000)
    n = pg.locator('#dw3-list .dw3-item').count()
    check('Liste zeigt alle Modelle', n == 249, n)
    named = pg.evaluate('() => [...document.querySelectorAll("#dw3-list .dw3-item b")].filter(b => !/^M\\d{3}/.test(b.textContent)).length')
    check('Modelle mit Digimon-Namen', named == 248, named)
    def search(q):
        pg.fill('#dw3-q', q); pg.wait_for_timeout(200); return first_names(pg)
    r = search('WarGreymon'); check('Suche „WarGreymon“: WarGreymon zuerst', r[:1] == ['WarGreymon'], r)
    r = search('wargreymon'); check('Groß-/Kleinschreibung egal', r[:1] == ['WarGreymon'], r)
    r = search('Imperialdramon'); check('Suche „Imperialdramon“: beide Formen', {'Imperialdramon-F', 'Imperialdramon-P'} <= set(first_names(pg, 6)), first_names(pg, 6))
    r = search('Fighter Mode'); check('Alternative Schreibweise „Fighter Mode“', r == ['Imperialdramon-F'], r)
    r = search('Paladin'); check('Alternative Schreibweise „Paladin“', r == ['Imperialdramon-P'], r)
    r = search('mera'); check('Teilname „mera“ findet Meramon', 'Meramon' in r, r)
    r = search('WGRE'); check('Dateikürzel „WGRE“', r == ['WarGreymon'], r)
    r = search('213'); check('Modell-ID „213“ (exakt: Katalog-ID, Dateinummer oder Kämpfer-ID, 0.98.1)', r[:1] == ['WarGreymon'] or 'WarGreymon' in r, r)
    r = search('Birdramon'); check('„Birdramon“: kein DW3-Modell (nicht erfunden)', r == [], r)
    info = pg.inner_text('#dw3-list .dw3-item') if False else None
    search('WarGreymon')
    txt = pg.locator('#dw3-list .dw3-item').first.inner_text()
    check('Zeile zeigt Dateikürzel und Modell-ID', 'WGRE' in txt and '213' in txt, txt.replace('\n', ' / '))
    pg.locator('#dw3-list .dw3-item').first.screenshot(path=str(out / 'dw3_row.png'))
    pg.locator('#dw3-list .dw3-item').first.click()
    pg.wait_for_function('() => /WarGreymon/.test(document.querySelector("#v-name").textContent)', timeout=180000)
    pg.wait_for_timeout(2500)
    check('Klick zeigt das Modell im 3D-Viewer', 'WarGreymon' in pg.inner_text('#v-name'), pg.inner_text('#v-name'))
    pg.screenshot(path=str(out / 'viewer_wargreymon.png'))
    thumb = [m for m in N('dw3_models')['models'] if m['name'] == 'M213WGRE'][0].get('thumb')
    check('Vorschaubild gespeichert', bool(thumb), thumb)
    pg.click('button[data-page="page-dw3"]'); pg.wait_for_timeout(800); search('WarGreymon'); pg.wait_for_timeout(500)
    check('Vorschaubild in der Liste', pg.locator('#dw3-list .dw3-item img').count() >= 1)
    pg.locator('#dw3-list').screenshot(path=str(out / 'dw3_list_wargreymon.png'))
    # erneut öffnen: gleiche Namen aus dem Zwischenspeicher
    before = N('dw3_models')['models']
    pg.click('#dw3-open'); pg.wait_for_timeout(1500)
    after = N('dw3_models')['models']
    check('Erneutes Laden: gleiche Namen', [m['digimon'] for m in before] == [m['digimon'] for m in after])
    # Animationseditor zeigt den Namen
    models = {m['name']: m['id'] for m in after}
    plan = N('dw3_native_plan', models['M359IPDF'], 150)
    N('dw3_native_apply', models['M359IPDF'], 150, plan['assignments'], 1, 0, None, 'dw2')
    ed = N('anim_editor', 150)
    check('Animationseditor: Name, Modell-ID, Motions', ed['digimon'] == 'Imperialdramon-F' and ed['model_id'] == 359 and len(ed['motions']) > 10,
          (ed['digimon'], ed['model_id'], len(ed['motions'])))
    check('keine JS-Fehler', not errs, errs[:3])
    b.close()
print('FAILS', fails)
