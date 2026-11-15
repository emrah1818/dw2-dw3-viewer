"""Studio functions through the real UI bridge (headless Chrome): DW3 import, quality card, HD on/off,
blink in the HD preview, rename, resize, project save/load, mod export.
    functions.py WORKDIR DW2_PAK DW3_BIN PORT_DIR NAME:TARGET   -> JSON lines 'check: PASS/FAIL detail'"""
import json, sys, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from serve import make
from playwright.sync_api import sync_playwright
work, pak, dw3, port = sys.argv[1:5]
name, target = sys.argv[5].split(':'); target = int(target)
srv = make(work, pak, dw3)
res = []
def check(what, ok, detail=''):
    res.append((what, bool(ok), detail)); print(('PASS ' if ok else 'FAIL ') + what + (' | ' + str(detail) if detail != '' else ''), flush=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_page(viewport={'width': 1400, 'height': 1000})
    errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{srv.server_port}/'); pg.wait_for_function('window.__dw2 !== undefined')
    N = lambda m, *a: pg.evaluate('([m, a]) => window.__dw2.native(m, ...a)', [m, list(a)])
    pg.click('#btn-open'); pg.wait_for_function('window.__dw2.state.catalog.length > 0', timeout=120000)
    check('DW2 pak geöffnet (Modus A)', pg.evaluate('window.__dw2.state.image.source_kind') == 'pak')
    models = {m['name']: m['id'] for m in N('pick_dw3')['models']}
    check('DW3-Abbild geöffnet', len(models) > 200, len(models))
    plan = N('dw3_native_plan', models[name], target)
    job = N('dw3_native_apply', models[name], target, plan['assignments'], 1, 0, None, 'dw2')
    q = job.get('quality') or {}
    check('DW3-Import: alle Dreiecke', q.get('source', {}).get('triangles') == q.get('converted', {}).get('triangles') == job['triangles'], job['triangles'])
    def select():
        pg.evaluate('() => { window.__dw2.view.clear(); }')
        pg.locator(f'#list .item[data-id="{target}"]').click()
        pg.wait_for_function('() => window.__dw2.view.native && window.__dw2.view.native.hd', timeout=120000)
        pg.wait_for_timeout(800)
    pg.evaluate('() => document.querySelector("#search").dispatchEvent(new Event("input"))')
    select()
    check('Viewer zeigt das importierte Modell mit HD-Textur (automatisch)', pg.evaluate('() => !!window.__dw2.view.native.hd'))
    check('Qualitätskarte sichtbar', pg.evaluate('() => !document.querySelector("#dw3q-card").hidden && document.querySelector("#dw3q-info").textContent.length > 50'))
    check('Animationen vorhanden', pg.evaluate('() => window.__dw2.view.native.payload.anims.length') >= 5, pg.evaluate('() => window.__dw2.view.native.payload.anims.length'))
    # animations move bones
    moved = pg.evaluate('''() => { const v = window.__dw2.view; const out = [];
        for (let i = 0; i < v.native.payload.anims.length; i++) { v.playing = false; v.play(i);
          const a = v.native.bones.map(b => b.matrix.elements.slice()); v.playing = true; for (let k = 0; k < 40; k++) v.stepNative(1 / 60); v.playing = false;
          const c = v.native.bones.map(b => b.matrix.elements.slice());
          out.push(a.some((m, j) => m.some((x, e) => Math.abs(x - c[j][e]) > 1e-4))); }
        return out; }''')
    check('jede Animation bewegt das Skelett', all(moved), f'{sum(moved)} von {len(moved)}')
    # blink in the HD preview
    blink = pg.evaluate('''() => { const v = window.__dw2.view, t = v.native.tex, h = v.native.hdCanvas;
        if (!t || !h) return { eyes: 0 };
        const grab = () => h.ctx.getImageData(0, 0, h.base.width, h.base.height).data;
        const diff = (a, b) => { let n = 0; for (let i = 0; i < a.length; i += 4) if (a[i] !== b[i] || a[i + 1] !== b[i + 1] || a[i + 2] !== b[i + 2]) n++; return n; };
        t.reset(); v.refreshTextures([[0, 0, 128, 256]]); const open = grab().slice();
        const e = t.anim.eyes.find(x => x); if (!e) return { eyes: 0 };
        const r = t.move(e.uv[4], e.uv[5], e.w, e.h, e.dx, e.dy); t.lastMoves = [[e.uv[4], e.uv[5], e.w, e.h, e.dx, e.dy]];
        v.refreshTextures([[e.dx * 4, e.dy, (e.dx + e.w) * 4, e.dy + e.h]]); const closed = grab().slice();
        t.reset(); v.refreshTextures([[0, 0, 128, 256]]); const again = grab();
        // natural blinking over 600 game frames
        let frames = 0; v.play(0); v.playing = true; const seen = {};
        for (let k = 0; k < 600; k++) { v.stepNative(1 / 60); if (k % 2 === 0) { const d = diff(grab(), open); seen[d] = (seen[d] || 0) + 1; if (d > 0) frames++; } }
        const cyc = t.anim.cycles.length + t.anim.extended.length;
        return { eyes: t.anim.eyes.filter(x => x).length, changed: diff(open, closed), restored: diff(open, again), rect: [e.w * 4 * h.k, e.h * h.k], blinkFrames: frames, seen, cyc }; }''')
    check('HD-Vorschau: Augenbild wechselt beim Blinzeln', blink.get('changed', 0) > 0, blink)
    check('HD-Vorschau: Auge öffnet sich wieder (Bild wie vorher)', blink.get('restored', 1) == 0)
    check('HD-Vorschau: blinzelt im normalen Ablauf', blink.get('blinkFrames', 0) > 0, blink.get('blinkFrames'))
    # HD off / pixel look independent
    st = pg.evaluate('''() => { const v = window.__dw2.view; const hd = v.native.hd;
        const f = () => [v.native.hd ? v.native.hd.magFilter : null, v.native.textures[0].tex.magFilter];
        document.querySelector('#o-nearest').checked = true; document.querySelector('#o-nearest').dispatchEvent(new Event('change')); const a = f();
        document.querySelector('#o-nearest').checked = false; document.querySelector('#o-nearest').dispatchEvent(new Event('change')); const b2 = f();
        v.clearHdPreview(); return { a, b: b2, off: v.native.hd === null, map1x: v.native.textures[0].mat.map === v.native.textures[0].tex }; }''')
    check('Pixel-Look schaltet nur den Filter (HD bleibt an)', st['a'][0] != st['b'][0] and st['a'][0] is not None, st)
    check('HD-Textur abschaltbar (1x-Textur wird gezeigt)', st['off'] and st['map1x'])
    # rename
    N('rename', target, 'WarGreyTest'); cat = {c['id']: c['name'] for c in N('catalog')}
    check('Name bearbeiten', cat[target] == 'WarGreyTest', cat[target])
    # resize
    s0 = N('size_info', target); r = N('dw3_resize', target, 1.5); s1 = N('size_info', target)
    check('Modellgröße ändern (Faktor 1,5)', abs(s1['height'] / max(s0['height'], 1) - 1.5) < 0.05, (s0['height'], s1['height']))
    N('dw3_resize', target, 1.0); s2 = N('size_info', target)
    check('Modellgröße zurück (Faktor 1,0)', abs(s2['height'] - s0['height']) <= 2, (s0['height'], s2['height']))
    # project save / load
    edits0 = len(N('pending')) if True else 0
    prj = N('save_project', 'uitest')
    check('Projekt speichern', Path(prj['path']).is_file(), Path(prj['path']).name)
    while N('pending'):
        try: N('undo')
        except Exception: break
        if len(N('pending')) == edits0: break
    N('load_project', prj['path']); cat = {c['id']: c['name'] for c in N('catalog')}
    check('Projekt laden: Änderungen und Name wieder da', len(N('pending')) == edits0 and cat[target] == 'WarGreyTest', (edits0, len(N('pending')), cat[target]))
    select()
    check('nach dem Laden: Modell mit HD und Qualitätskarte', pg.evaluate('() => !!window.__dw2.view.native.hd && !document.querySelector("#dw3q-card").hidden'))
    # mod export
    shutil.rmtree(Path(port) / 'Mods', ignore_errors=True)
    c = N('mod_check', port); e = N('mod_export', port)
    pngs = list((Path(port) / 'Mods' / 'Textures').rglob('*.png'))
    check('Mod-Prüfung ohne Fehler', c['ok'], c['errors'][:2])
    check('Mod für den PC-Port exportiert (Dateien + HD-Textur)', e['count'] > 0 and len(pngs) >= 1 and (Path(port) / 'Mods' / 'dw2studio_mod.json').is_file(), (e['count'], len(pngs)))
    check('keine JavaScript-Fehler', not errs, errs[:3])
    b.close()
bad = [r for r in res if not r[1]]
print(json.dumps({'passed': len(res) - len(bad), 'failed': [r[0] for r in bad]}, ensure_ascii=False))
