"""Real import dialog with a synthetic bridge; no game data required.
Run: python integration/uitest/manual_selection.py
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import os
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
srv = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'www')))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BOOT = r"""
window.DW2_BASE='/';
window.Android={invoke(id, method, raw) {
  const auto={segments:[{motion:1,start:0,end:2,repeat:1},{motion:15,start:0,end:1,repeat:1}],
    end:'hold',loop_segment:0,loop_frame:0,status:'data',reason:'Automatisch'};
  const data={
    app_info:{version:'test',free_mb:100},
    dw3_models:{open:true,name:'Synthetic test',models:[{id:0,name:'M100TEST',code:'TEST',digimon:'Testmon'}]},
    dw3_native_plan:{name:'M100TEST',target:'Target',source_bones:1,target_bones:1,
      motions:[{id:1,frames:3,end:'loop',loop_frame:0},{id:15,frames:2,end:'hold'},
               {id:16,frames:3,end:'loop',loop_frame:1},{id:17,frames:3,end:'idle'}],
      assignments:['F','G','H'].map(slot=>({slot,clip:0,motion:1,loop:false,action:structuredClone(auto),reason:'Automatisch'}))}
  };
  if(method==='dw3_native_apply'){window.__submitted=JSON.parse(raw);return;}
  if(method==='prepare_model'){
    queueMicrotask(()=>window.__resolve(id,JSON.stringify({ok:false,error:'Synthetic model load failure'})));return;
  }
  queueMicrotask(()=>window.__resolve(id,JSON.stringify({ok:true,data:data[method]||{}})));
}};
"""
try:
    with sync_playwright() as p:
        browser_path = os.environ.get('DW2_TEST_BROWSER') or shutil.which('google-chrome') or shutil.which('chromium')
        browser=p.chromium.launch(executable_path=browser_path, args=[
            '--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=browser.new_page(viewport={'width':1400,'height':1100})
        errors=[]; page.on('pageerror', lambda e: errors.append(str(e)))
        page.add_init_script(BOOT)
        def open_dialog():
            page.goto(f'http://127.0.0.1:{srv.server_port}/')
            page.wait_for_function('!!window.__desktop && !!window.__dw2')
            page.evaluate("() => {window.__dw2.state.id=3; window.__dw2.state.image={source_kind:'pak'}; window.__desktop.show('page-dw3');}")
            page.locator('[data-one="0"]').click()
            page.locator('#d-apply').wait_for()
        open_dialog()
        assert page.locator('[data-motion="0"]').input_value()==''
        for i, mid, loop in [(0,15,False),(1,16,True),(2,17,True)]:
            page.locator(f'[data-motion="{i}"]').select_option(str(mid))
            assert page.locator(f'[data-loop="{i}"]').is_checked()==loop
        assert 'Bild 1' in page.locator('[data-motion-hint="1"]').inner_text()
        page.click('#d-apply'); page.wait_for_function('!!window.__submitted')
        rows=page.evaluate('window.__submitted[2]')
        assert [r['motion'] for r in rows]==[15,16,17]
        assert all(r['selection']=='motion' for r in rows)
        assert [r['loop'] for r in rows]==[False,True,True]
        open_dialog()
        page.locator('[data-motion="0"]').select_option('1')
        page.locator('[data-loop="0"]').uncheck()
        page.locator('[data-motion="1"]').select_option('16')
        page.locator('[data-motion="1"]').select_option('')
        assert not page.locator('[data-loop="1"]').is_checked()
        page.click('#d-apply'); page.wait_for_function('!!window.__submitted')
        rows=page.evaluate('window.__submitted[2]')
        assert rows[0]['selection']=='motion' and rows[0]['motion']==1 and not rows[0]['loop']
        assert 'selection' not in rows[1] and len(rows[1]['action']['segments'])==2
        assert 'selection' not in rows[2] and rows[2]['action']['status']=='data'
        # Loading a failing field model must clear the previous displayed model,
        # rather than showing it under the newly selected #304 label.
        page.reload()
        page.wait_for_function('!!window.__desktop && !!window.__dw2')
        page.evaluate("""async () => {
            const THREE=await import('/lib/three.module.js');
            const v=window.__dw2.view, s=window.__dw2.state;
            v.model=new THREE.Group(); v.scene.add(v.model);
            s.catalog=s.filtered=[{id:3,name:'Previous'},{id:304,name:'Field model'}];
            s.id=3; s.loaded={id:3}; window.__desktop.show('page-view');
        }""")
        page.click('#v-next')
        page.wait_for_function('window.__dw2.state.id===304 && window.__dw2.state.loaded===null')
        assert page.evaluate('window.__dw2.view.model===null')
        assert page.locator('#anim option').count()==0
        msg=page.locator('#stage-msg').inner_text(); assert 'nicht geladen' in msg or 'could not be loaded' in msg, msg
        assert not errors, errors
        print('PASS: import dialog, independent F/G/H, loop defaults/override, same-motion choice, reset, untouched chains; failed field load clears stale model; no JS errors')
        browser.close()
finally:
    srv.shutdown()
