"""Real Linux game test: install DNA mod, use lab, save, restart, load.

Requires a dev PC-port executable (for --start-mode), its source checkout (bot
helpers), and the user's own PAK/SLUS. No game data or memory cards are committed.
Test setup uses dev edits for parents/location; DNA and card saving use game menus.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import android_api as api


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--port-source', type=Path, required=True)
    parser.add_argument('--pak', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    args.work = args.work.resolve()
    args.work.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(args.port_source.resolve() / 'tools/autoplay'))
    from dw2bot import Game
    from save_test import save_menu, load_slot1

    runtime = args.work / 'runtime'
    runtime.mkdir(exist_ok=True)
    exe = runtime / 'dw2'
    shutil.copy2(args.exe.resolve(), exe)
    (runtime / 'dw2_mod_api.json').write_bytes(subprocess.check_output([str(exe), '--mod-api']))
    api.configure(str(args.work / 'studio-cache'), '')
    api.open_image(str(args.pak.resolve()))
    api.dna_set(213, 196, 150, 3)
    api.mod_export_replace(str(runtime))

    def roster(game):
        return [{'state': game.u8('Save_GameState', 0xE4+i*0x5C),
                 'id': game.u8('Save_GameState', 0xE4+i*0x5C+1),
                 'level': game.u8('Save_GameState', 0xE4+i*0x5C+0xD)} for i in range(36)]

    def dna_run(name, no_mods=False, save=False):
        work = args.work / name
        extra = ['--start-mode', '0x301'] + (['--no-mods'] if no_mods else [])
        game = Game(str(exe), str(args.pak.resolve()), str(work), extra=extra)
        try:
            game.run(600)
            # A disposable test session, never an existing player memory card.
            game.poke('Save_GameState', 0xE4, bytes(36*0x5C))
            for ident in (213, 196):
                game.devedit(f'adddigi={ident},41,99,300,200,120,100,80')
                game.run(6)
            game.devedit('warp=0x32F,0')
            game.run(180)
            assert game.mode() == 0x32F
            for key in ['Right', 'Cross', 'Cross', 'Cross', 'Down', 'Cross']:
                game.tap(key, 3, 60)
            game.shot('dna_preview')
            game.tap('Cross', 3, 60)
            game.run(1500)
            game.tap('Start', 3, 30)
            game.tap('Cross', 3, 120)
            game.shot('offspring_info')
            child = [r for r in roster(game) if r['state']]
            assert len(child) == 1, child
            if save:
                for _ in range(10):
                    if game.mode() != 0x32F:
                        break
                    game.tap('Triangle', 3, 90)
                game.devedit('warp=0x32D,0')
                game.run(240)
                assert game.mode() == 0x32D
                save_menu(game)
                card = work / 'saves/card1.mcd'
                assert card.is_file() and card.stat().st_size == 131072
            return child[0]
        finally:
            game.close()

    baseline = dna_run('vanilla', no_mods=True)
    installed = dna_run('installed', save=True)
    assert installed['id'] == 150 and installed['level'] == 31, installed
    assert (baseline['id'], baseline['level']) != (150, 31), baseline
    reload_dir = args.work / 'reload'
    (reload_dir / 'saves').mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.work / 'installed/saves/card1.mcd', reload_dir / 'saves/card1.mcd')
    game = Game(str(exe), str(args.pak.resolve()), str(reload_dir))
    try:
        assert load_slot1(game) == 0x32D
        reloaded = [r for r in roster(game) if r['state']]
        assert len(reloaded) == 1 and reloaded[0]['id'] == 150 and reloaded[0]['level'] == 31, reloaded
        game.shot('reloaded')
    finally:
        game.close()
    result = {'vanilla': baseline, 'installed': installed, 'reloaded': reloaded[0], 'passed': True}
    (args.work / 'dna_ingame.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
