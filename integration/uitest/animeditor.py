"""Animationseditor durch die echte Oberfläche (headless Chrome): DW3-Import, Editor öffnen, Plätze und
Status, Bild-für-Bild, Start/Ende/Loop setzen, Übernehmen (Clip im DW2-Format prüfen), DW3-Motion ansehen,
Kampfaktion simulieren.   animeditor.py WORKDIR DW2_PAK DW3_BIN NAME:TARGET OUTDIR"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from serve import make
from playwright.sync_api import sync_playwright
work, pak, dw3 = sys.argv[1:4]
name, target = sys.argv[4].split(':'); target = int(target)
out = Path(sys.argv[5]); out.mkdir(parents=True, exist_ok=True)
srv = make(work, pak, dw3)
fails = 0
def check(what, ok, detail=''):
    global fails; fails += not ok
    print(('PASS ' if ok else 'FAIL ') + what + (' | ' + str(detail) if detail != '' else ''), flush=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_page(viewport={'width': 1400, 'height': 1100})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{srv.server_port}/'); pg.wait_for_function('window.__dw2 !== undefined')
    N = lambda m, *a: pg.evaluate('([m, a]) => window.__dw2.native(m, ...a)', [m, list(a)])
    pg.click('#btn-open'); pg.wait_for_function('window.__dw2.state.catalog.length > 0', timeout=120000)
    models = {m['name']: m['id'] for m in N('pick_dw3')['models']}
    plan = N('dw3_native_plan', models[name], target)
    N('dw3_native_apply', models[name], target, plan['assignments'], 1, 0, None, 'dw2')
    pg.evaluate('() => document.querySelector("#search").dispatchEvent(new Event("input"))')
    pg.locator(f'#list .item[data-id="{target}"]').click()
    pg.wait_for_function('() => window.__dw2.view.native && !document.querySelector("#dw3q-card").hidden', timeout=120000)
    pg.evaluate('() => { document.querySelector("#dw3q-card").open = true; }')
    pg.click('#b-anim-editor')
    pg.wait_for_selector('.ae-places tr', timeout=120000)
    rows = pg.locator('.ae-places tr').count()
    check('Editor zeigt alle Kampfplätze', rows >= 11, rows)
    st = pg.evaluate('() => [...document.querySelectorAll(".ae-places tr")].map(r => r.cells[0].textContent + ":" + r.cells[2].innerText)')
    check('Status je Platz sichtbar', all(':' in s and len(s) > 4 for s in st), st)
    pg.wait_for_function('() => document.querySelector("#ae-check").textContent.length > 3', timeout=60000)
    check('Prüfung: Bildzahl und Loop', 'Bilder' in pg.inner_text('#ae-check') or 'frames' in pg.inner_text('#ae-check'), pg.inner_text('#ae-check'))
    pg.locator('#ae-body').screenshot(path=str(out / 'editor_A0.png'))
    # F0 (Attacke 1): mehrteilig, Loop
    pg.locator('.ae-places tr', has_text='F0').first.click(); pg.wait_for_timeout(600)
    segs = pg.locator('.ae-segs tr[data-s]').count()
    check('Attacke 1 ist eine Kette aus mehreren Abschnitten', segs >= 2, segs)
    pg.wait_for_function('() => /Loop|⟲|loop/i.test(document.querySelector("#ae-check").textContent)', timeout=60000)
    pg.locator('#ae-body').screenshot(path=str(out / 'editor_F0.png'))
    # Bild für Bild
    pg.click('#ae-first'); r0 = pg.evaluate('() => window.__dw2.view.nativeRow()')
    for _ in range(5): pg.click('#ae-next')
    r5 = pg.evaluate('() => window.__dw2.view.nativeRow()')
    pg.click('#ae-prev'); r4 = pg.evaluate('() => window.__dw2.view.nativeRow()')
    check('Bild vor/zurück', (r0, r5, r4) == (0, 5, 4), (r0, r5, r4))
    # Ende des ersten Abschnitts auf aktuelles Bild, Loop ab hier, übernehmen
    pg.click('#ae-set-end'); pg.wait_for_timeout(300)
    end0 = pg.locator('.ae-segs tr[data-s="0"] input[data-f="end"]').input_value()
    check('„Ende = dieses Bild“ setzt das Ende', end0 == '4', end0)
    pg.click('#ae-first'); pg.click('#ae-next'); pg.click('#ae-next'); pg.click('#ae-set-loop'); pg.wait_for_timeout(300)
    check('Status wird „Manuell zugeordnet“', any(w in pg.locator('.ae-places tr.sel').inner_text() for w in ('Manuell', 'manually')), pg.locator('.ae-places tr.sel').inner_text())
    pg.click('#ae-apply')
    pg.wait_for_function('() => !document.querySelector(".ae-places tr.sel")?.innerText.includes("✎") && window.__dw2.view.native', timeout=180000)
    pg.wait_for_timeout(1500)
    info = pg.evaluate('''() => { const v = window.__dw2.view, a = v.native.payload.anims; const i = a.findIndex(x => x.id === 50); return i < 0 ? null : v.nativeClipInfo(i); }''')
    check('Übernommen: F0 im DW2-Format mit Loop ab Bild 2', info and info['loop'] == 2, info)
    ed = N('anim_editor', target)
    f0 = [x for x in ed['places'] if x['slot'] + str(x['clip']) == 'F0'][0]['action']
    check('Gespeichert als manuell, Ende 4', f0['status'] == 'manual' and f0['segments'][0]['end'] == 4, (f0['status'], f0['segments'][0]))
    # DW3-Original ansehen
    pg.evaluate('() => { document.querySelector(".ae-motions").open = true; }')
    pg.locator('[data-view]').first.click()
    pg.wait_for_function('() => /DW3-Motion/.test(document.querySelector("#ae-pos").textContent)', timeout=120000)
    pg.click('#ae-next'); pg.click('#ae-next')
    check('DW3-Motion Bild für Bild', any(w + ' 2 ' in pg.inner_text('#ae-pos') for w in ('Bild', 'Frame', 'frame')), pg.inner_text('#ae-pos'))
    # Kampfaktion simulieren (Treffer: Fallen und Aufstehen)
    pg.select_option('#ae-sim', index=4); pg.click('#ae-simgo')
    pg.wait_for_function('() => window.__dw2.view.native', timeout=120000)
    seen = set()
    for _ in range(120):
        pg.wait_for_timeout(250)
        seen.add(pg.evaluate('() => window.__dw2.view.native?.anim?.id'))
    check('Simulation spielt die Abfolge (A0, C0, C1, C2, J0)', {0, 20, 22, 90} <= seen, sorted(x for x in seen if x is not None))
    pg.screenshot(path=str(out / 'sim.png'))
    # Standard zurück
    pg.locator('.ae-places tr', has_text='F0').first.click(); pg.wait_for_timeout(400); pg.click('#ae-default')
    check('DW3-Vorgabe wiederhergestellt', any(w in pg.locator('.ae-places tr.sel').inner_text() for w in ('Durch Daten', 'by data')), pg.locator('.ae-places tr.sel').inner_text())
    check('keine JS-Fehler', not errs, errs[:3])
    b.close()
print('FAILS', fails)
