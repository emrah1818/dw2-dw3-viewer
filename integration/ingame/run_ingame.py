"""Reproduzierbare Spieltests des DW2 Mod Studio mit dem echten PC-Port (Linux, ohne Fenster).

Braucht: eigenes dw2.pak (+ dw2.pak.slus), DW3-Image (USA), einen Port-Build mit Bot-Schnittstelle
(tools/build_native.py, Commit aus integration/pc_port_base.txt) und dessen tools/autoplay.
Es werden keine Spieldaten erzeugt oder eingecheckt: jede Szene legt ihren Mod in einem eigenen
Arbeitsordner an und startet den Port mit diesem Ordner.

    python3 integration/ingame/run_ingame.py --port PORT/dw2 --pak dw2.pak --dw3 DW3.bin \
        --autoplay PORT_REPO/tools/autoplay --work /tmp/ingame [--only evo,domain]

Ergebnis: WORK/ingame_results.json mit passed/failed je Prüfung und Bildern unter WORK/<szene>/shots.
"""
import argparse
import json
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import android_api as api  # noqa: E402

ROSTER = 0xE4
ENTRY = 0x5C
LINE = (('M366GIRU', 84, 'Guilmon'), ('M367GRAW', 48, 'Growlmon'), ('M368MGRW', 12, 'MegaloGrowmon'))


class Checks:
    def __init__(self):
        self.items = []

    def __call__(self, scene, name, ok, **info):
        self.items.append({'scene': scene, 'check': name, 'passed': bool(ok), **info})
        print(('PASS ' if ok else 'FAIL ') + scene + ': ' + name, json.dumps(info), flush=True)
        return ok


def port_dir(args, scene):
    """Eigener Port-Ordner je Szene: Programm kopiert, Spieldateien nur verlinkt."""
    d = os.path.join(args.work, scene, 'port')
    shutil.rmtree(os.path.join(args.work, scene), ignore_errors=True)
    os.makedirs(d)
    shutil.copy2(args.port, os.path.join(d, os.path.basename(args.port)))
    for f in os.listdir(os.path.dirname(os.path.abspath(args.port))):
        if f.endswith('.json') and 'mod_api' in f:
            shutil.copy2(os.path.join(os.path.dirname(os.path.abspath(args.port)), f), d)
    for name in ('dw2.pak', 'dw2.pak.slus'):
        src = args.pak if name == 'dw2.pak' else args.pak + '.slus'
        if os.path.exists(src):
            os.symlink(os.path.abspath(src), os.path.join(d, name))
    return d


def open_studio(args, scene):
    api.configure(os.path.join(args.work, scene, 'studio'), '')
    api.open_image(args.pak)


def export(port, check, scene):
    c = api.mod_check(port)
    check(scene, 'Mod-Prüfung ohne Fehler', c['ok'] and not c['errors'], files=len(c['files']), errors=c['errors'])
    n = api.mod_export(port)['count']
    check(scene, 'Mod exportiert', n == len(c['files']), count=n)


def game(args, port, scene, extra=()):
    sys.path.insert(0, args.autoplay)
    from dw2bot import Game  # noqa: E402
    return Game(os.path.join(port, os.path.basename(args.port)), os.path.join(port, 'dw2.pak'),
                os.path.join(args.work, scene, 'run'), extra=extra)


def roster(g, i):
    raw = g.peek('Save_GameState', ROSTER + i * ENTRY, ENTRY)
    return {'state': raw[0], 'digi': raw[1], 'level': raw[0x0D], 'dp': raw[0x0E]}


# --- Szene 1: Digitation in ein importiertes und aus einem importierten Digimon ------------------
def scene_evo(args, check):
    scene = 'evo'
    port = port_dir(args, scene)
    open_studio(args, scene)
    models = {m['name']: m['id'] for m in api.open_dw3(args.dw3)['models']}
    jobs = api.dw3_batch_apply([{'source': models[n], 'target': t, 'name': name} for n, t, name in LINE])['jobs']
    check(scene, 'DW3-Linie importiert', len(jobs) == 3, targets=[j['target'] for j in jobs])
    lines = [{'id': 3, 'rows': [{'min_dp': 0, 'target': 48}], 'rank': 0},
             {'id': 48, 'rows': [{'min_dp': 0, 'target': 12}], 'rank': 1},
             {'id': 12, 'rows': api.evolution_info(12)['rows'], 'rank': 2}]
    check(scene, 'Linie Agumon > Growlmon > MegaloGrowmon gesetzt', api.evolution_line(lines)['changed'])
    # Digitationslevel je Digimon (Mods/digivolve_levels.json, ab Port 1.0): Agumon erst ab 20 (statt 11),
    # das importierte Growlmon schon ab 18 (statt 21)
    api.digivolve_level_set(3, 20)
    api.digivolve_level_set(48, 18)
    export(port, check, scene)
    check(scene, 'digivolve_levels.json mitgeschrieben', os.path.isfile(os.path.join(port, 'Mods', 'digivolve_levels.json')))

    sys.path.insert(0, args.autoplay)
    from to_city import to_city  # noqa: E402
    g, _ = to_city(os.path.join(port, os.path.basename(args.port)), os.path.join(port, 'dw2.pak'),
                   os.path.join(args.work, scene, 'run'), extra=('--cheats',))
    check(scene, 'Stadt erreicht', g.mode() == 0x32D, mode=hex(g.mode()))
    g.devedit('adddigi=3,15')
    g.run(10)
    idx = next((i for i in range(0x24) if roster(g, i)['state'] and roster(g, i)['digi'] == 3), None)
    if not check(scene, 'Agumon Lv15 angelegt', idx is not None):
        g.close()
        return
    g.devedit(f'digi={idx},dp,5')
    g.run(6)

    def lab(tag):
        for _ in range(12):  # ein offenes Labor mit Dreieck verlassen (im Spiel geprüft: 3x)
            if g.mode() != 0x32F:
                break
            g.tap('Triangle', 3, 150)
        if g.mode() != 0x301:
            g.devedit('warp=0x301,0')
            g.run(400)
        g.devedit('warp=0x32F,0')
        g.run(300)
        check(scene, f'Digi-Labor geöffnet ({tag})', g.mode() == 0x32F, mode=hex(g.mode()))
        # Liste: das Digimon steht vorne, wenn es der erste Eintrag ist; sonst nach unten gehen
        for k in range(7):
            g.tap('Cross', 3, (90, 90, 120, 120, 600, 300, 300)[k])
            g.shot(f'{tag}_{k}')

    lab('gesperrt')
    blocked = roster(g, idx)
    check(scene, 'Eigenes Mindestlevel sperrt: Agumon Lv15 < 20 digitiert nicht', blocked['digi'] == 3, slot=blocked)
    g.devedit(f'digi={idx},maxlevel,99')
    g.run(6)
    g.devedit(f'digi={idx},level,20')
    g.run(6)
    before = roster(g, idx)
    lab('in_import')
    after = roster(g, idx)
    check(scene, 'Digitation in importiertes Digimon bei Lv20 (Agumon > Growlmon #48)', after['digi'] == 48,
          before=before, after=after)
    g.devedit(f'digi={idx},level,18')
    g.run(6)
    g.devedit(f'digi={idx},dp,10')
    g.run(6)
    lab('aus_import')
    after2 = roster(g, idx)
    check(scene, 'Digitation aus importiertem Digimon bei Lv18 < Spielregel 21 (Growlmon > MegaloGrowmon #12)',
          after2['digi'] == 12, after=after2)

    # speichern, neu starten, laden: das importierte Digimon bleibt erhalten
    from save_test import save_menu, load_slot1  # noqa: E402
    for _ in range(12):
        if g.mode() != 0x32F:
            break
        g.tap('Triangle', 3, 150)
    g.run(200)
    g.devedit('warp=0x32D,0')  # Stadtkarte: von dort speichert auch save_test.py
    g.run(400)
    check(scene, 'Stadtkarte zum Speichern', g.mode() == 0x32D, mode=hex(g.mode()))
    save_menu(g)
    g.close()
    card = os.path.join(args.work, scene, 'run', 'saves', 'card1.mcd')
    check(scene, 'Spielstand geschrieben', os.path.exists(card) and os.path.getsize(card) == 131072)
    reload_dir = os.path.join(args.work, scene, 'reload')
    os.makedirs(os.path.join(reload_dir, 'saves'), exist_ok=True)
    shutil.copy(card, os.path.join(reload_dir, 'saves', 'card1.mcd'))
    sys.path.insert(0, args.autoplay)
    from dw2bot import Game  # noqa: E402
    g = Game(os.path.join(port, os.path.basename(args.port)), os.path.join(port, 'dw2.pak'), reload_dir,
             extra=('--cheats',))  # nur für den Warp ins Labor danach
    mode = load_slot1(g)
    loaded = roster(g, idx)
    g.shot('loaded')
    check(scene, 'Nach Neustart geladen: MegaloGrowmon (#12) Lv18 im Spielstand',
          (mode >> 8) == 3 and loaded['digi'] == 12 and loaded['level'] == 18, mode=hex(mode), slot=loaded)

    # Blinzeln: DW3-Augenrechteck als DW2-Augenanimation. Im Labor die VRAM-Texturseiten über 60 Bilder
    # vergleichen: Gfx_AnimateModelTex kopiert beim Blinzeln halb/zu-Rahmen über das Auge.
    g.devedit('warp=0x301,0'); g.run(400); g.devedit('warp=0x32F,0'); g.run(300)
    g.tap('Cross', 3, 90); g.tap('Cross', 3, 200)
    import numpy as np  # noqa: E402
    from PIL import Image  # noqa: E402
    frames = []
    for k in range(90):
        g.run(4)
        g.shot('blink_%02d' % k)
        frames.append(np.asarray(Image.open(os.path.join(reload_dir, 'shots', 'blink_%02d_vram.png' % k)).convert('RGB')).astype(int))
    g.close()
    changed = set()
    for k in range(1, len(frames)):
        d = np.abs(frames[k] - frames[0]).sum(2) > 0
        d[:, :640] = False                      # Bildspeicher links; Texturseiten ab x 640
        changed |= set(zip(*[a.tolist() for a in np.nonzero(d)[::-1]]))
    xs = [c[0] for c in changed]
    check(scene, 'Blinzeln im Spiel: Augenrahmen wird in die Texturseite kopiert',
          0 < len(changed) <= 64 and max(xs) - min(xs) < 16, texels=len(changed), area=sorted(changed)[:8])


# --- Szene 2: Gruppe kopieren, Mitglieder ändern, auf Boot Domain 1F setzen ----------------------
def scene_domain(args, check):
    scene = 'domain'
    port = port_dir(args, scene)
    open_studio(args, scene)
    ov = api.domains_overview()
    boot = ov['domains'][29]
    src = next(s for s in boot['floors'][0]['sets'] if s)
    new = api.group_clone(src)['id']
    info = api.group_info(new)
    members = info['members']
    members[0].update({'digimon': 5, 'level': 6, 'hp': 70, 'skills': [4, 0, 0]})
    members[1].update({'digimon': 3, 'level': 4, 'hp': 50, 'skills': [1, 0, 0]})
    for m in members:
        m.pop('name', None)
    api.group_set(new, members=members)
    api.domain_set_floor(29, 0, [0, new, 0, 0, 0])
    check(scene, 'Gruppe kopiert und Boot Domain 1F zugewiesen', True, group=new, source=src)
    export(port, check, scene)

    sys.path.insert(0, args.autoplay)
    import policy  # noqa: E402
    g = game(args, port, scene)
    st = policy.Stats()
    found = {}
    orig = policy.battle

    def battle(g, st, *a, **k):
        if not found:
            g.run(400)
            g.shot('battle')
            for i in range(6):
                raw = g.peek('Stg30_Battle', 0x18 + i * ENTRY, ENTRY)
                if raw[0]:
                    found[i] = {'digi': raw[1], 'level': raw[0x0D], 'maxHp': struct.unpack_from('<h', raw, 0x14)[0],
                                'skills': list(raw[0x22:0x25])}
        return orig(g, st, *a, **k)
    policy.battle = battle
    g.run(600); g.tap('Start'); g.run(120); g.tap('Up'); g.run(20); g.tap('Cross')
    while g.wait < 40000 and not found:
        m = g.mode()
        if m == 0x32A:
            g.run(90); g.tap('Down'); g.run(20); g.tap('Cross'); g.run(60)
        elif m == 0x200:
            policy.dungeon_floor(g, st, max_waits=20000)
        elif policy.table(m) == 5:
            policy.battle(g, st)
        else:
            g.tap('Cross', 3, 17)
    policy.battle = orig
    g.close()
    enemies = [v for k, v in found.items() if k >= 3]
    want = [{'digi': 5, 'level': 6, 'maxHp': 70}, {'digi': 3, 'level': 4, 'maxHp': 50}]
    got = [{'digi': e['digi'], 'level': e['level'], 'maxHp': e['maxHp']} for e in enemies]
    check(scene, 'Geänderte Gegner erscheinen im Kampf', all(w in got for w in want), enemies=enemies)


# --- Szene 3: importiertes Digimon als Partner: Team-Menü, Kampf, eigene Technik, Kamera -----------
def scene_partner(args, check):
    scene = 'partner'
    port = port_dir(args, scene)
    open_studio(args, scene)
    models = {m['name']: m['id'] for m in api.open_dw3(args.dw3)['models']}
    jobs = api.dw3_batch_apply([{'source': models['M366GIRU'], 'target': 84, 'name': 'Guilmon'},
                                {'source': models['M368MGRW'], 'target': 131, 'name': 'MegaloGrowmon'}])['jobs']
    job = jobs[0]
    check(scene, 'Guilmon (Platz 84) und MegaloGrowmon (Platz 131, Gegner der Boot Domain) importiert, Kamera automatisch',
          [j['target'] for j in jobs] == [84, 131], cameras={j['target']: j.get('battle_camera') for j in jobs})
    tech = api.technique_create(84, 0x1F, 'Pyro Sphere', None, {'mp': 7, 'power': 90}, True, [])
    check(scene, 'Eigene Technik für Guilmon angelegt', tech['id'] > 0, id=tech['id'])
    export(port, check, scene)
    # Nur Digimon, deren automatische Kamera vom Original abweicht, stehen in der Datei (ein kleines
    # Digimon, das schon ganz im Bild ist, braucht keinen Eintrag).
    need = {str(j['target']) for j in jobs if (j.get('battle_camera') or {}).get('setting')}
    cam_file = os.path.join(port, 'Mods', 'battle_camera.json')
    written = set(json.load(open(cam_file))['digimon']) if os.path.isfile(cam_file) else set()
    check(scene, 'battle_camera.json enthält jedes Digimon mit angepasster Kamera', need and need == written,
          need=sorted(need), written=sorted(written))

    sys.path.insert(0, args.autoplay)
    import policy  # noqa: E402
    g = game(args, port, scene, extra=('--cheats',))
    st = policy.Stats()
    found, state, views = {}, {'idx': None, 'battle_done': False}, []
    orig = policy.battle

    def battle(g, st, *a, **k):
        if not found:
            for k2, w in enumerate((60, 90, 150, 200, 250)):
                g.run(w)
                g.shot('battle_%d' % k2)
                views.append(view_record(g))   # Befehlseingabe: Nahaufnahme hat Zeit zum Einschwingen
            for i in range(6):
                raw = g.peek('Stg30_Battle', 0x18 + i * ENTRY, ENTRY)
                if raw[0]:
                    found[i] = {'digi': raw[1], 'level': raw[0x0D], 'skills': list(raw[0x22:0x25])}
            run0 = g.run
            count = {'w': 0, 'k': 0}

            def run(n=1, buttons=None):
                r = run0(n, buttons)
                count['w'] += n
                if count['w'] >= 15 and count['k'] < 400:
                    count['w'] = 0
                    count['k'] += 1
                    views.append(view_record(g))
                    if count['k'] % 3 == 0:
                        g.shot('fight_%03d' % count['k'])
                return r
            g.run = run
            try:
                return orig(g, st, *a, **k)
            finally:
                g.run = run0
                state['battle_done'] = True
        return orig(g, st, *a, **k)
    policy.battle = battle
    g.run(600); g.tap('Start'); g.run(120); g.tap('Up'); g.run(20); g.tap('Cross')
    in_domain = False
    while g.wait < 70000:
        m = g.mode()
        if m == 0x32D and in_domain:
            break
        if m == 0x32A:
            if state['idx'] is None:
                # vor der ersten Domain: Guilmon ins Team, eigene Technik auf Platz 1 der Techniken
                # das Start-Team ist voll (Leih-Digimon): Partnerplatz 1 wird zu Guilmon
                g.devedit('digi=0,species,84')
                g.run(10)
                state['idx'] = 0 if roster(g, 0)['digi'] == 84 else -1
                if state['idx'] >= 0:
                    g.devedit(f"skill={state['idx']},0,{tech['id']}")
                    g.run(10)
            g.run(90); g.tap('Down'); g.run(20); g.tap('Cross'); g.run(60)
        elif m == 0x200:
            in_domain = True
            policy.dungeon_floor(g, st, max_waits=20000)
        elif policy.table(m) == 5:
            policy.battle(g, st)
        else:
            g.tap('Cross', 3, 17)
    policy.battle = orig
    check(scene, 'Guilmon steht im Team (Partnerplatz)', state['idx'] is not None and state['idx'] >= 0, slot=state['idx'])
    if g.mode() == 0x32D:
        # nach der Boot Domain gehen die Leih-Digimon; Guilmon kommt als eigener Partner ins Team
        g.run(120)
        g.devedit('adddigi=84,15')
        g.run(10)
        team = [roster(g, i) for i in range(3)]
        g.tap('Circle', 3, 60); g.tap('Down', 3, 15); g.tap('Down', 3, 15); g.tap('Cross', 3, 120)
        g.run(300)
        g.shot('team_menu_digimon')
        g.tap('Cross', 3, 300)
        g.shot('team_menu_digimon_2')
        g.run(300)
        g.shot('team_menu_digimon_3')
        check(scene, 'Guilmon als eigener Partner im Team (Spielstanddaten)', any(t['digi'] == 84 and t['state'] for t in team), team=team)
    alive, end_mode = g.proc.poll() is None, g.mode()
    g.close()
    glog = open(os.path.join(args.work, scene, 'run', 'game.log'), errors='replace').read()
    check(scene, 'Port hat die Kampfkameras gelesen', f'battle cameras for {len(need)} Digimon' in glog, need=len(need))
    party = [v for k2, v in found.items() if k2 < 3]
    check(scene, 'Guilmon (#84) kämpft als Partner mit eigener Technik', any(p['digi'] == 84 and tech['id'] in p['skills'] for p in party),
          party=party)
    check(scene, 'Kampf zu Ende gespielt, zurück in der Stadt, Spiel läuft', state['battle_done'] and alive and end_mode == 0x32D,
          mode=hex(end_mode), note='Bilder: run/shots/battle_*, fight_*')
    # Kampfkamera im Spiel gemessen: in jeder erkannten Einstellung eines importierten Digimon liegt
    # sein Modellrechteck (Gfx_ModelScreenBounds) ganz im Bild
    seen = shots_on_screen(views, {84, 131})
    json.dump(seen, open(os.path.join(args.work, scene, 'camera_shots.json'), 'w'), indent=1)
    imported = [v for v in seen if v['digi'] in (84, 131)]
    check(scene, 'Kampfkamera: importierte Digimon in jeder gemessenen Einstellung ganz im Bild',
          imported and all(v['inside'] for v in imported),
          shots=sorted({(v['digi'], v['shot'], v['position'], v['inside']) for v in imported}))


def view_record(g):
    """View matrix, the six fighters' model rectangles and Digimon of one battle frame."""
    raw = g.peek('GsWSMATRIX', 0, 32)
    boxes = {}
    for i in range(6):
        r = g._call('fbox %d' % i)
        boxes[i] = list(map(int, r.split()[1:])) if r.startswith('ok') else None
    return {'m': struct.unpack_from('<9h', raw, 0), 't': struct.unpack_from('<3i', raw, 20), 'boxes': boxes,
            'digis': [g.peek('Stg30_Battle', 0x18 + i * ENTRY, 2)[1] for i in range(6)]}


def shots_on_screen(views, digis_of_interest):
    """Frames whose view matrix is one of the game's shots (battle_shots, with the exported
    Mods/battle_camera.json settings and the current close-up values): the shot's own fighter's
    rectangle against the 320 x 480 screen (centre 160 / 240). Other fighters keep stale bone
    matrices when the game does not draw them, so only the shot's own fighter is judged."""
    import numpy as np
    from dw2studio.core import battle_shots as B
    from dw2studio.core.battle_camera import CameraRepository
    repo = CameraRepository(api.S.session, api.S.entries)
    out = []
    for v in views:
        m, t = np.array(v['m']).reshape(3, 3), np.array(v['t'])
        best = None
        for i in range(6):
            d = v['digis'][i]
            if not d:
                continue
            adj = api.S.battle_camera.get(d, {})
            for name, frame in B.shots(i, repo.values(d)['field_1E']):
                a = adj.get('closeup') if frame['kind'] == 'closeup' else {k: x for k, x in adj.items() if k != 'closeup'}
                f = B.adjusted(frame, a or None)
                eye, target = B.eye_target(f)
                fw = target - eye
                fw /= np.linalg.norm(fw)
                r = np.cross([0, 1, 0], fw)
                r /= np.linalg.norm(r)
                M = np.array([r, np.cross(fw, r), fw])
                err = np.abs(M * 4096 - m).sum() + np.abs(-(M @ eye) - t).sum() / 10
                if best is None or err < best[0]:
                    best = (err, i, name)
        if best is None or best[0] > 60:
            continue
        _, i, name = best
        b = v['boxes'][i]
        if not b:
            continue
        inside = -160 <= b[0] and b[2] <= 160 and -240 <= b[1] and b[3] <= 240
        out.append({'digi': v['digis'][i], 'position': i, 'shot': name, 'box': b[:4], 'inside': inside})
    return out



# --- Szene 4: DNA-Digitation mit importierten Digimon -----------------------------------------
# Greymon (#5, Champion) + importiertes Growlmon (#48, Champion) ergibt nach der DNA-Tabelle des Spiels
# (Stg20_DnaResultTbl: zwei Champions -> Rookie) Platz #84 = importiertes Guilmon. Also DNA mit einem
# importierten Elternteil und ein importiertes Ergebnis.
def dna_menu(g, tag, steps):
    """steps: (Taste, Wartezeit) im Digi-Labor; nach jedem Schritt ein Bild."""
    for k, (key, wait) in enumerate(steps):
        g.tap(key, 3, wait)
        g.shot(f'{tag}_{k:02d}_{key}')


def scene_dna(args, check):
    scene = 'dna'
    port = port_dir(args, scene)
    open_studio(args, scene)
    models = {m['name']: m['id'] for m in api.open_dw3(args.dw3)['models']}
    jobs = api.dw3_batch_apply([{'source': models[n], 'target': t, 'name': name} for n, t, name in LINE[:2]])['jobs']
    check(scene, 'DW3-Guilmon (#84) und -Growlmon (#48) importiert', len(jobs) == 2)
    export(port, check, scene)
    sys.path.insert(0, args.autoplay)
    from to_city import to_city  # noqa: E402
    g, _ = to_city(os.path.join(port, os.path.basename(args.port)), os.path.join(port, 'dw2.pak'),
                   os.path.join(args.work, scene, 'run'), extra=('--cheats',))
    check(scene, 'Stadt erreicht', g.mode() == 0x32D, mode=hex(g.mode()))
    for spec in ('adddigi=5,25', 'adddigi=48,25'):
        g.devedit(spec); g.run(10)
    before = [roster(g, i) for i in range(6)]
    parents = [i for i, r in enumerate(before) if r['state'] and r['digi'] in (5, 48)]
    if not check(scene, 'Eltern angelegt: Greymon Lv25 und importiertes Growlmon Lv25', len(parents) == 2, roster=before):
        g.close(); return
    g.devedit('warp=0x301,0'); g.run(400)
    g.devedit('warp=0x32F,0'); g.run(300)
    check(scene, 'Digi-Labor geöffnet', g.mode() == 0x32F, mode=hex(g.mode()))
    dna_menu(g, 'dna', DNA_STEPS)
    after = [roster(g, i) for i in range(8)]
    g.close()
    alive = [r for r in after if r['state']]
    got = [r for r in alive if r['digi'] == 84]
    gone = not any(r['digi'] in (5, 48) for r in alive)
    check(scene, 'DNA: Greymon + importiertes Growlmon -> importiertes Guilmon (#84), Eltern verschmolzen',
          bool(got) and gone, roster=alive)


DNA_STEPS = [('Right', 90), ('Cross', 200)] + [('Cross', 150)] * 4 + [('Down', 60), ('Cross', 150)] + \
            [('Cross', 150)] * 6 + [('Cross', 400)] * 4

# --- Szene 5: geänderte Gegner auf anderen Domains und Etagen, importiertes Digimon als Gegner -----------
# Je Domain eine Gruppe der Etage kopieren, erstes Mitglied = importiertes MegaloGrowmon (#12) mit eigenem
# Level/HP, alle Gruppenplätze der Etage auf die Kopie. Im Spiel: Domain betreten, auf die Etage springen
# (Entwickler-Bearbeitung floor=), bis zum ersten Kampf laufen und den Kampfspeicher lesen.
DOMAIN_TESTS = ((0, 1), (15, 2), (27, 3))     # (Domain-Index, Etage ab 0): SCSI 2F, Laser 3F, Core Tower 4F


def enter(g, d, f):
    """Aus der Stadt in Domain D, dann auf Etage F springen (Entwickler-Bearbeitung). Der Digi-Beetle
    bekommt volle HP (Testaufbau): mit 0 HP bricht jeder Schritt die Domain ab."""
    for spec in ('beetle=maxhp,9999', 'beetle=hp,9999', 'beetle=maxep,9999', 'beetle=ep,9999'):
        g.devedit(spec); g.run(6)
    for _ in range(30):
        g.devedit('warp=0x200,%d' % d); g.run(60)
        if g.mode() == 0x200 or (g.mode() >> 8) != 3:
            break
    for _ in range(400):
        if g.mode() == 0x200 and g.dung() is not None:
            break
        g.tap('Cross', 3, 7)
    for _ in range(40):            # floor= nur beim Laufen (nicht während des Eingangsereignisses)
        d0 = g.dung()
        if d0 is not None and d0['floor'] == f:
            break
        g.devedit('floor=%d' % f); g.run(200)
        g.tap('Cross', 3, 30)
    g.shot('floor')


def scene_domains(args, check):
    scene = 'domains'
    port = port_dir(args, scene)
    open_studio(args, scene)
    models = {m['name']: m['id'] for m in api.open_dw3(args.dw3)['models']}
    api.dw3_batch_apply([{'source': models['M368MGRW'], 'target': 12, 'name': 'MegaloGrowmon'}])
    ov = api.domains_overview()
    want = {}
    for k, (d, f) in enumerate(DOMAIN_TESTS):
        sets = ov['domains'][d]['floors'][f]['sets']
        src = next(x for x in sets[1:] if x)
        new = api.group_clone(src)['id']
        members = api.group_info(new)['members']
        members[0].update({'digimon': 12, 'level': 7 + k, 'hp': 171 + k})
        for m in members:
            m.pop('name', None)
        api.group_set(new, members=members)
        api.domain_set_floor(d, f, [sets[0], new, new, new, new])
        want[d] = {'digi': 12, 'level': 7 + k, 'maxHp': 171 + k, 'group': new, 'floor': f}
    check(scene, 'Gruppen kopiert, importiertes MegaloGrowmon als Gegner, Etagen zugewiesen', len(want) == 3, want=want)
    export(port, check, scene)

    sys.path.insert(0, args.autoplay)
    from to_city import to_city  # noqa: E402
    from save_test import save_menu, load_slot1  # noqa: E402
    import policy  # noqa: E402
    from dw2bot import Game  # noqa: E402
    exe, pak = os.path.join(port, os.path.basename(args.port)), os.path.join(port, 'dw2.pak')
    base = os.path.join(args.work, scene, 'base')
    g, _ = to_city(exe, pak, base, extra=('--cheats',))
    for sp in (3, 4, 5):     # starke Testgruppe (nur Testaufbau), Plätze 3..5 = Kampfgruppe
        g.devedit('adddigi=%d,40,99,999,999,700,700,700' % sp); g.run(10)
    pos = 3
    for i in range(0x24):
        if pos > 5:
            break
        if g.u8('Save_GameState', ROSTER + i * ENTRY) != 0:
            g.poke('Save_GameState', ROSTER + i * ENTRY, bytes([pos])); pos += 1
    g.run(30)
    save_menu(g)
    g.close()
    card = os.path.join(base, 'saves', 'card1.mcd')
    for d, f in DOMAIN_TESTS:
        work = os.path.join(args.work, scene, 'd%02d' % d)
        os.makedirs(os.path.join(work, 'saves'), exist_ok=True)
        shutil.copy(card, os.path.join(work, 'saves', 'card1.mcd'))
        g = Game(exe, pak, work, extra=('--cheats',))
        found, info = {}, {}
        try:
            load_slot1(g); g.run(240)
            enter(g, d, f)
            info['floor'] = (g.dung() or {}).get('floor')
            st = policy.Stats()
            orig = policy.battle

            def battle(g, st, *a, **k):
                if not found:
                    g.run(400)
                    g.shot('battle')
                    for i in range(6):
                        raw = g.peek('Stg30_Battle', 0x18 + i * ENTRY, ENTRY)
                        if raw[0]:
                            found[i] = {'digi': raw[1], 'level': raw[0x0D], 'maxHp': struct.unpack_from('<h', raw, 0x14)[0]}
                return orig(g, st, *a, **k)
            policy.battle = battle
            start = g.wait
            while g.wait - start < 30000 and not found:
                if (g.mode() >> 8) == 3:   # der Weg führte zurück in die Stadt: erneut hinein
                    info['reentered'] = info.get('reentered', 0) + 1
                    g.run(300)
                    enter(g, d, f)
                elif g.mode() == 0x200:
                    d1 = g.dung()
                    if d1 is not None:
                        info.setdefault('floors', []).append(d1['floor'])
                        if d1['floor'] != f:   # über eine Treppe weiter: zurück auf die Testetage
                            g.devedit('floor=%d' % f); g.run(200)
                            continue
                    policy.dungeon_floor(g, st, max_waits=1500)
                elif policy.table(g.mode()) == 5:
                    policy.battle(g, st)
                else:
                    g.tap('Cross', 3, 17)
            policy.battle = orig
            info['alive'] = g.proc.poll() is None
        finally:
            g.close()
        w = want[d]
        enemies = [v for k, v in found.items() if k >= 3]
        check(scene, f'Domain {d} Etage {f + 1}: importiertes MegaloGrowmon Lv{w["level"]} / {w["maxHp"]} HP im Kampf',
              info.get('floor') == f and {'digi': 12, 'level': w['level'], 'maxHp': w['maxHp']} in enemies,
              floor=info.get('floor'), floors=sorted(set(info.get('floors', []))), reentered=info.get('reentered', 0),
              enemies=enemies)


SCENES = {'evo': scene_evo, 'domain': scene_domain, 'partner': scene_partner, 'dna': scene_dna, 'domains': scene_domains}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--port', required=True)
    p.add_argument('--pak', required=True)
    p.add_argument('--dw3', required=True)
    p.add_argument('--autoplay', required=True)
    p.add_argument('--work', required=True)
    p.add_argument('--only', default=','.join(SCENES))
    args = p.parse_args()
    os.makedirs(args.work, exist_ok=True)
    check = Checks()
    for name in args.only.split(','):
        try:
            SCENES[name](args, check)
        except Exception as e:  # eine Szene darf die anderen nicht verhindern
            check(name, 'Szene ohne Ausnahme', False, error=repr(e))
    out = os.path.join(args.work, 'ingame_results.json')
    json.dump({'checks': check.items, 'passed': sum(c['passed'] for c in check.items),
               'failed': sum(not c['passed'] for c in check.items)}, open(out, 'w'), indent=1, ensure_ascii=False)
    print('RESULT', out)
    return 1 if any(not c['passed'] for c in check.items) else 0


if __name__ == '__main__':
    sys.exit(main())
