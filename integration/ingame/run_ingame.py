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
    export(port, check, scene)

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

    before = roster(g, idx)
    lab('in_import')
    after = roster(g, idx)
    check(scene, 'Digitation in importiertes Digimon (Agumon > Growlmon #48)', after['digi'] == 48,
          before=before, after=after)
    g.devedit(f'digi={idx},maxlevel,99')
    g.run(6)
    g.devedit(f'digi={idx},level,25')
    g.run(6)
    g.devedit(f'digi={idx},dp,10')
    g.run(6)
    lab('aus_import')
    after2 = roster(g, idx)
    check(scene, 'Digitation aus importiertem Digimon (Growlmon > MegaloGrowmon #12)', after2['digi'] == 12,
          after=after2)

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
    check(scene, 'Nach Neustart geladen: MegaloGrowmon (#12) Lv25 im Spielstand',
          (mode >> 8) == 3 and loaded['digi'] == 12 and loaded['level'] == 25, mode=hex(mode), slot=loaded)

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


SCENES = {'evo': scene_evo, 'domain': scene_domain}


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
