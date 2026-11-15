"""DW3 original vs Studio import in the Studio's own viewer (headless Chrome, same framing):
    compare.py WORKDIR DW2_PAK DW3_BIN OUTDIR NAME:TARGET [NAME:TARGET ...]
Per model: <NAME>_orig.png, _hd.png, _hd_pixel.png, _1x.png, _hd_blink.png and report.json (the quality card's data)."""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from serve import make
from playwright.sync_api import sync_playwright
work, pak, dw3, out = sys.argv[1:5]
jobs = [a.split(':') for a in sys.argv[5:]]
Path(out).mkdir(parents=True, exist_ok=True)
srv = make(work, pak, dw3)
url = f'http://127.0.0.1:{srv.server_port}/'
report = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_page(viewport={'width': 1600, 'height': 1200})
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    pg.goto(url); pg.wait_for_function('window.__dw2 !== undefined')
    N = lambda m, *a: pg.evaluate('([m, a]) => window.__dw2.native(m, ...a)', [m, list(a)])
    pg.click('#btn-open'); pg.wait_for_function('window.__dw2.state.catalog.length > 0', timeout=120000)
    models = {m['name']: m['id'] for m in N('pick_dw3')['models']}
    names = {c['id']: c['name'] for c in pg.evaluate('window.__dw2.state.catalog')}
    plans = {n: N('dw3_native_plan', models[n], int(t)) for n, t in jobs}
    r = N('dw3_batch_apply', [{'source': models[n], 'target': int(t)} for n, t in jobs])
    def shot(tag):
        pg.wait_for_timeout(400)
        pg.locator('#gl').screenshot(path=f'{out}/{tag}.png')
    def pose(hd, nearest, blink=None):
        pg.evaluate('''async ([hd, nearest, blink]) => { const v = window.__dw2.view, s = window.__dw2.state;
            v.nearest = nearest; v.applyMaterial();
            if (!hd) v.clearHdPreview();
            else if (!v.native.hd) { const h = await window.__dw2.native('hd_active', s.id); await v.setHdPreview('/viewer/' + h.url); }
            v.playing = false; v.play(0); v.framePose();
            const t = v.native.tex;
            if (t && blink !== null) { t.reset(); v.refreshTextures([[0, 0, 128, 256]]);
              if (blink) { const e = t.anim.eyes.find(x => x); if (e) { t.move(e.uv[4], e.uv[5], e.w, e.h, e.dx, e.dy); t.lastMoves = [[e.uv[4], e.uv[5], e.w, e.h, e.dx, e.dy]]; v.refreshTextures([[e.dx * 4, e.dy, (e.dx + e.w) * 4, e.dy + e.h]]); } } }
        }''', [hd, nearest, blink])
    for (n, t), job in zip(jobs, r['jobs']):
        t = int(t)
        pg.evaluate('id => { window.__dw2.state.id = id; }', t)
        pg.locator(f'#list .item[data-id="{t}"]').click()
        pg.wait_for_function('id => window.__dw2.state.loaded === id || (window.__dw2.view.native && document.querySelector("#dw3q-card") && !document.querySelector("#dw3q-card").hidden)', arg=t, timeout=120000)
        pg.wait_for_timeout(1500)
        info = pg.evaluate('() => ({ names: [...document.querySelectorAll("#anim option")].map(o => o.textContent).slice(0, 12), card: document.querySelector("#dw3q-info").innerText, hd: !!window.__dw2.view.native?.hd, anims: document.querySelectorAll("#anim option").length })')
        pose(True, False, False); shot(f'{n}_hd')
        pose(True, True, False); shot(f'{n}_hd_pixel')
        pose(True, False, True); shot(f'{n}_hd_blink')
        pose(False, True, False); shot(f'{n}_1x')
        pose(True, False, False)
        pg.evaluate('() => { document.querySelector("#dw3q-card").open = true; }'); pg.click('#b-dw3-source')
        pg.wait_for_timeout(2500)
        # the DW3 original: same framing (the viewer frames every model by its bounds), first motion, frame 0
        idle = next(a['motion'] for a in plans[n]['assignments'] if a['slot'] == 'A' and a['clip'] == 0)
        idx = next(i for i, m in enumerate(plans[n]['motions']) if m['id'] == idle)
        onames = pg.evaluate('''(idx) => { const v = window.__dw2.view; v.nearest = false; v.applyMaterial(); v.playing = false;
            if (v.actions && v.actions[idx]) { v.actions.forEach(x => x.stop()); v.actions[idx].reset().play(); v.mixer.setTime(0); v.mixer.update(0); }
            // frame like the converted model: bounds of this pose
            v.framePose(); return v.actions.map(a => a.getClip().name).slice(0, 4); }''', idx)
        shot(f'{n}_orig')
        pg.click('#b-dw3-back'); pg.wait_for_timeout(1500)
        report[n] = {'target': t, 'replaced': names.get(t), 'quality': job.get('quality'), 'triangles': job.get('triangles'), 'hd_size': job.get('hd_size'),
                     'card_shown': bool(info['card']), 'hd_auto': info['hd'], 'animations': info['anims'], 'anim_names': info['names'], 'idle_motion': idle, 'orig_anim_names': onames, 'camera': job.get('camera')}
    report['_errors'] = errors[:20]
    b.close()
Path(out, 'report.json').write_text(json.dumps(report, indent=1, ensure_ascii=False))
print(json.dumps({k: (v if k == '_errors' else {x: v[x] for x in ('target', 'replaced', 'triangles', 'hd_size', 'card_shown', 'hd_auto', 'animations')}) for k, v in report.items()}, ensure_ascii=False))
