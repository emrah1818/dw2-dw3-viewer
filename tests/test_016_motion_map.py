"""0.16: DW3-Motions aus den Kampfskripten vorbelegen; Größe nach Standhöhe."""
import os
import pytest
from dw2studio.dw3_motion_map import defaults, apply_defaults

# Aufbau wie bei 245 von 248 DW3-Kämpfern (Skript 0 Standby, 2 Treffer, 3 K.o., 5-8 Techniken)
SCRIPTS = [{'motions': [1]}, {'motions': [4]}, {'motions': [5, 6, 7, 12]}, {'motions': [5, 6, 7, 11]},
           {'motions': [3]}, {'motions': [15, 16, 17], 'strike': 17}, {'motions': [21, 23], 'strike': 23},
           {'motions': [27, 29], 'strike': 29}, {'motions': [33, 35], 'strike': 35}]
PLACES = [('A', 0), ('B', 0), ('C', 0), ('C', 1), ('C', 2), ('F', 0), ('G', 0), ('H', 0), ('I', 0), ('J', 0), ('K', 0), ('D', 3)]


def rows():
    return [{'slot': s, 'clip': c, 'motion': 1, 'loop': False} for s, c in PLACES]


def test_battle_places_follow_the_scripts():
    got = {(r['slot'], r['clip']): r['motion'] for r in apply_defaults(rows(), SCRIPTS, set(range(1, 62)))}
    assert got == {('A', 0): 1, ('B', 0): 1, ('C', 0): 5, ('C', 1): 6, ('C', 2): 7, ('F', 0): 17, ('G', 0): 23,
                   ('H', 0): 29, ('I', 0): 1, ('J', 0): 12, ('K', 0): 11, ('D', 3): 1}


def test_every_default_names_its_source():
    out = apply_defaults(rows(), SCRIPTS, set(range(1, 62)))
    assert all(r['reason'] for r in out)
    assert 'Skript 2' in out[2]['reason'] and 'Skript 3' in out[10]['reason'] and 'nicht belegt' in out[1]['reason']


def test_short_hit_sequences_and_enemies_with_one_technique():
    short = [{'motions': [1]}, {'motions': [4]}, {'motions': [5, 12]}, {'motions': [5, 11]}, {'motions': [3]},
             {'motions': [15], 'strike': 15}, {'motions': [], 'strike': 0}]
    t = defaults(short)
    assert t[('C', 0)][0] == t[('C', 1)][0] == t[('C', 2)][0] == 5 and t[('J', 0)][0] == 12
    assert t[('F', 0)][0] == t[('G', 0)][0] == t[('H', 0)][0] == 15


def test_missing_scripts_or_motions_fall_back_to_motion_1():
    out = apply_defaults(rows(), [], {1, 2, 3})
    assert {r['motion'] for r in out} == {1} and 'Keine DW3-Kampfskripte' in out[0]['reason']
    out = apply_defaults(rows(), SCRIPTS, {1, 2, 3})        # Modell ohne die genannten Motions
    assert {r['motion'] for r in out} == {1}


@pytest.mark.skipif(not os.environ.get('DW3_TEST_DISC'), reason='Private DW3 disc not provided')
def test_real_dw3_scripts(tmp_path):
    from pathlib import Path
    from dw2studio.dw3 import Dw3Disc
    from dw2studio.dw3_fighters import script_motions, fighters
    from dw2studio.core.disc import Disc
    dw3 = Dw3Disc(os.environ['DW3_TEST_DISC'], tmp_path)
    disc = Disc(dw3.path)
    table, rows_ = fighters(disc)
    disc.close()
    assert len(rows_) == 248 and len(table) > 2000
    entry = next(e for e in dw3.entries if Path(e.path).name.startswith('M373RENA'))
    found = script_motions(dw3.path, entry, tmp_path / 's')
    assert found['fighter']['ids'] == [373]
    motions = [s['motions'] for s in found['scripts']]
    assert motions[0] == [1] and motions[2][-1] == 12 and motions[3][-1] == 11
    t = defaults(found['scripts'])
    assert t[('F', 0)][0] == 17 and t[('K', 0)][0] == 11
