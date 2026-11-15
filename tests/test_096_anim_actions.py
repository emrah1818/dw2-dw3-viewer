"""0.96 Animationssystem: DW3-Skripte als mehrteilige DW2-Aktionen (dw3_actions), ohne Spieldaten."""
import pytest
from dw2studio import dw3_actions as A


def src(motions):
    """native_source-ähnlich: [(id, frames, end, loop_key)]."""
    return {'motions': [{'id': i, 'end': e, 'loop_key': k, 'frames': [None] * n} for i, n, e, k in motions]}


TABLE = A.motion_table(src([(1, 31, 'loop', 1), (4, 23, 'idle', -1), (5, 14, 'loop', 9), (6, 19, 'loop', 21),
                            (7, 34, 'hold', -1), (11, 41, 'hold', -1), (12, 49, 'idle', -1), (13, 46, 'loop', 49),
                            (15, 12, 'hold', -1), (16, 15, 'loop', 17), (17, 33, 'hold', -1),
                            (18, 15, 'loop', 17), (19, 19, 'idle', -1)]))
TECH = [['m', 15], ['wm'], ['m', 16], ['j', 4], ['wj'], ['m', 17], ['w', 20], ['hit'], ['wm'],
        ['m', 18], ['j', 5], ['wj'], ['m', 19], ['wm']]
SCRIPTS = [{'index': 0, 'steps': [['m', 1]]}, {'index': 1, 'steps': [['m', 4], ['wm']]},
           {'index': 2, 'steps': [['m', 5], ['j', 3], ['wj'], ['m', 6], ['j', 2], ['wj'], ['m', 7], ['wm'], ['m', 12], ['wm']]},
           {'index': 3, 'steps': [['m', 5], ['j', 3], ['wj'], ['m', 6], ['j', 2], ['wj'], ['m', 7], ['wm'], ['m', 11], ['wm']]},
           {'index': 4, 'steps': []}, {'index': 5, 'steps': TECH}]
PLACES = [('A', 0), ('B', 0), ('C', 0), ('C', 1), ('C', 2), ('F', 0), ('G', 0), ('H', 0), ('I', 0), ('J', 0), ('K', 0)]


def test_loop_frame_from_loop_key():
    assert TABLE[5]['loop_frame'] == 4 and TABLE[6]['loop_frame'] == 10 and TABLE[13]['loop_frame'] == 24
    assert TABLE[1]['loop_frame'] == 0 and TABLE[7]['end'] == 'hold'


def test_timeline_follows_jumps_and_waits():
    parts, hits = A.timeline(TECH, TABLE)
    assert [p[0] for p in parts] == [15, 16, 17, 18, 19]
    assert parts[0][1] == 24                       # 12 Bilder = 24 Ticks
    assert parts[1][1] == A.jump_ticks(4)          # Motion 16 läuft während des Sprungs
    assert parts[-1][1] is None and len(hits) == 1


def test_defaults_status_and_no_silent_guess(monkeypatch):
    monkeypatch.setattr(A, 'joints', lambda *a: 0.)          # synthetische Motions ohne Posen
    source = {'motions': [{'id': i, 'end': v['end'], 'loop_key': 2 * v['loop_frame'] + 1, 'frames': [None] * v['frames']}
                          for i, v in TABLE.items()]}
    d = A.defaults(source, SCRIPTS, PLACES)
    st = {k: v['status'] for k, v in d.items()}
    assert st[('A', 0)] == 'data' and st[('I', 0)] == 'data' and st[('K', 0)] == 'data' and st[('J', 0)] == 'data'
    assert st[('B', 0)] == 'auto'                  # DW3 kennt keine Verteidigung
    assert st[('F', 0)] == 'data'
    # keine Technikskripte 6/7 und kein Grundangriff: nicht stillschweigend F kopieren
    assert st[('G', 0)] == 'open' and st[('H', 0)] == 'open'
    assert [s['motion'] for s in d[('G', 0)]['segments']] == [1]
    f = d[('F', 0)]
    assert f['end'] == 'loop' and f['segments'][f['loop_segment']]['motion'] == 1   # danach Standby wie DW3
    assert d[('K', 0)]['end'] == 'hold' and d[('K', 0)]['segments'][0]['motion'] == 11
    for a in d.values():
        A.validate(a, TABLE)                       # jede Vorgabe ist kodierbar


def test_frames_of_loop_row_and_repeat():
    act = {'segments': [{'motion': 15, 'start': 0, 'end': 3, 'repeat': 1},
                        {'motion': 16, 'start': 8, 'end': 10, 'repeat': 2, 'blend': 2}],
           'end': 'loop', 'loop_segment': 1, 'loop_frame': 9}
    rows, loop = A.frames_of(act)
    assert len(rows) == 4 + 2 + 6
    assert rows[4][2] == (15, 3) and 0 < rows[4][3] < 1      # Übergangsbilder blenden aus dem letzten Bild
    assert loop == 4 + 2 + 1 and rows[loop][:2] == (16, 9)
    hold = dict(act, end='hold')
    assert A.frames_of(hold)[1] is None


def test_validate_rejects_bad_ranges():
    bad = {'segments': [{'motion': 15, 'start': 5, 'end': 40, 'repeat': 1}], 'end': 'loop', 'loop_segment': 0, 'loop_frame': 2}
    with pytest.raises(ValueError):
        A.validate(bad, TABLE)
    ok = dict(bad, segments=[{'motion': 15, 'start': 0, 'end': 11, 'repeat': 1}], loop_frame=20)
    with pytest.raises(ValueError, match='Loop'):
        A.validate(ok, TABLE)


def test_dw3_opening_blend_starts_from_shown_pose():
    t = A.motion_table({'motions': [{'id': 1, 'end': 'loop', 'loop_key': 1, 'lead_blend': 0, 'frames': [None] * 10},
                                    {'id': 15, 'end': 'hold', 'loop_key': -1, 'lead_blend': 10, 'frames': [None] * 20}]})
    assert t[15]['lead'] == 5 and t[1]['lead'] == 0
    act = {'segments': [{'motion': 1, 'start': 0, 'end': 9, 'repeat': 1}, {'motion': 15, 'start': 0, 'end': 19, 'repeat': 1}],
           'end': 'hold', 'loop_segment': 0, 'loop_frame': 0}
    rows, _ = A.frames_of(act, t)
    assert rows[10][:3] == (15, 5, ('row', 9))          # blendet aus dem zuletzt gezeigten Bild
    assert [round(r[3], 3) for r in rows[10:15]] == [round((2 * f + 2) / 11, 3) for f in range(5)]
    assert rows[15] == (15, 5, None, 1.0)
    first, _ = A.frames_of(dict(act, segments=act['segments'][1:]), t)
    assert first[0][2] == ('idle', None)                # Aktionsbeginn: aus dem Standby
    assert A.frames_of(act)[0][10] == (15, 0, None, 1.0)  # ohne Tabelle: wie bisher


def test_hard_cut_gets_marked_blend(monkeypatch):
    monkeypatch.setattr(A, 'joints', lambda *a: 86.)
    act = {'segments': [{'motion': 15, 'start': 0, 'end': 11, 'repeat': 1}, {'motion': 1, 'start': 0, 'end': 30, 'repeat': 1}],
           'end': 'loop', 'loop_segment': 1, 'loop_frame': 0, 'status': 'data', 'reason': 'Technik'}
    src = {'motions': [{'id': 15}, {'id': 1}]}
    A._smooth_cuts(src, TABLE, act)
    assert act['segments'][1]['blend'] == A.CUT_BLEND and 'hart' in act['reason']


def test_getup_enters_from_lying_pose(monkeypatch):
    monkeypatch.setattr(A, 'joints', lambda *a: 0.)
    source = {'motions': [{'id': i, 'end': v['end'], 'loop_key': 2 * v['loop_frame'] + 1, 'lead_blend': 10,
                           'frames': [None] * v['frames']} for i, v in TABLE.items()]}
    d = A.defaults(source, SCRIPTS, PLACES)
    assert d[('J', 0)]['enter'] == [7, 33] and d[('K', 0)]['enter'] == [7, 33]
    rows, _ = A.frames_of(d[('J', 0)], A.motion_table(source))
    assert rows[0][2] == (7, 33)
    A.validate(d[('J', 0)], A.motion_table(source))
