"""Regression: simple import controls must not be masked by automatic actions."""
from copy import deepcopy
from types import SimpleNamespace
import numpy as np
import pytest
from dw2studio import dw3_actions as A
from dw2studio.core.dw3_native import encode_animation
from dw2studio.core.native_anim import parse_anim_file


def make_source(tmp_path):
    from test_015_native import source
    s = source(tmp_path)
    def frame(x):
        m = np.eye(4); m[0, 3] = x
        return [np.eye(4).T.ravel().tolist(), m.T.ravel().tolist()]
    s['motions'] = [
        {'id': 1, 'end': 'loop', 'loop_key': 1, 'frames': [frame(0), frame(1), frame(0)]},
        {'id': 15, 'end': 'hold', 'frames': [frame(10), frame(20)]},
        {'id': 16, 'end': 'loop', 'loop_key': 3, 'frames': [frame(30), frame(40), frame(50)]},
        {'id': 17, 'end': 'idle', 'frames': [frame(60), frame(70), frame(80)]},
    ]
    return s


def automatic(table):
    return A.from_script([['m', 1], ['w', 6], ['m', 15]], table, 'data', 'Automatisch')


@pytest.mark.parametrize('mid,loop,expected', [(1, True, 0), (15, False, None), (15, True, 0),
                                             (16, True, 1), (16, False, None), (17, True, 3)])
def test_manual_choice_replaces_chain_and_uses_selected_loop(tmp_path, mid, loop, expected):
    s = make_source(tmp_path); table = A.motion_table(s)
    row = {'slot': 'F', 'clip': 0, 'motion': mid, 'loop': loop,
           'selection': 'motion', 'action': automatic(table)}
    before = deepcopy(row)
    resolved = A.resolve_assignment(row, table)
    assert row == before                         # no modification to defaults / another slot
    assert 'selection' not in resolved
    assert resolved['action']['status'] == 'manual'
    assert resolved['action']['segments'][0]['motion'] == mid
    data = encode_animation(s, {0: resolved['action']})
    assert parse_anim_file(data, 1).clips[0].loop_row == expected
    assert A.resolve_assignment(resolved, table) == resolved  # reapply/resize keeps choice


def test_old_client_motion_and_checkbox_override_stale_action(tmp_path):
    table = A.motion_table(make_source(tmp_path))
    auto = automatic(table)
    row = {'motion': 16, 'loop': True, 'action': auto}
    chosen = A.resolve_assignment(row, table)
    assert chosen['action']['segments'][0]['motion'] == 16
    assert chosen['action']['loop_frame'] == 1
    off = A.resolve_assignment(dict(chosen, loop=False), table)
    on = A.resolve_assignment(dict(off, loop=True), table)
    assert off['action']['end'] == 'hold'
    assert on['action']['loop_frame'] == 1 and on['action']['end'] == 'loop'
    assert A.resolve_assignment({'motion': 1, 'loop': False, 'action': auto}, table)['action']['end'] == 'hold'


def test_unmodified_auto_and_legacy_assignments_stay_unchanged(tmp_path):
    table = A.motion_table(make_source(tmp_path))
    row = {'motion': 1, 'loop': False, 'action': automatic(table)}
    assert A.resolve_assignment(row, table) == row
    old = {'motion': 16, 'loop': True}
    assert A.resolve_assignment(old, table) == old
    with pytest.raises(ValueError, match='Motion'):
        A.resolve_assignment(dict(old, motion=999, selection='motion'), table)


def test_import_persists_independent_F_G_H_and_reimport_keeps_them(tmp_path, monkeypatch):
    from dw2studio import dw3_import as I
    from dw2studio.pak_workspace import PakSession
    from dw2studio.core.disc import Entry
    s = make_source(tmp_path); table = A.motion_table(s)
    class Session(PakSession):
        def __init__(self): self.edits = {}; self.hd_files = {}
        def stage(self, entry, payload, label): self.edits[entry.path] = payload
    session = Session()
    api = SimpleNamespace(_need_session=lambda: session,
                          S=SimpleNamespace(dw3_imports={}, battle_camera={}))
    assignments = [{'slot': slot, 'clip': 0, 'motion': mid, 'loop': True,
                    'selection': 'motion', 'action': automatic(table)}
                   for slot, mid in zip('FGH', [1, 16, 17])]
    prepared = {'source': s, 'folder': tmp_path, 'model': Entry('M003AGUM.BIN', 1, 1, False),
                'animations': {slot: (Entry(f'{slot}003AGUM.BIN', i + 2, 1, False), None)
                               for i, slot in enumerate('FGH')},
                'info': {'scale': 1., 'scale_dw3': 1., 'name': 'M100TEST', 'assignments': assignments}}
    monkeypatch.setattr(I, 'prepare', lambda *args: prepared)
    monkeypatch.setattr(I, '_camera_plan', lambda *args: {'repo': SimpleNamespace(set=lambda *a: False),
                                                        'field_1E': 1000, 'hit_fx_y': 500})
    I.apply(api, 0, 3, assignments)
    saved = deepcopy(api.S.dw3_imports[3]['assignments'])
    first = {slot: session.edits[f'{slot}003AGUM.BIN'] for slot in 'FGH'}
    assert len(set(first.values())) == 3
    assert [parse_anim_file(first[slot], 1).clips[0].loop_row for slot in 'FGH'] == [0, 1, 3]
    assert all(row['action']['status'] == 'manual' and 'selection' not in row for row in saved)
    I.apply(api, 0, 3, saved)
    assert {slot: session.edits[f'{slot}003AGUM.BIN'] for slot in 'FGH'} == first
    changed = deepcopy(saved)
    for row, mid, loop in zip(changed, [15, 17, 16], [False, True, True]):
        row.update(motion=mid, loop=loop)          # old clients still send the previous action
    I.apply(api, 0, 3, changed)
    assert [parse_anim_file(session.edits[f'{slot}003AGUM.BIN'], 1).clips[0].loop_row
            for slot in 'FGH'] == [None, 3, 1]
    assert all(session.edits[f'{slot}003AGUM.BIN'] != first[slot] for slot in 'FGH')
    assert assignments[0]['action']['status'] == 'data'  # defaults not mutated
