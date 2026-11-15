"""Exercise actual native animation bytes, including composed blended rows."""
import numpy as np
import pytest
from dw2studio.core.dw3_native import encode_animation
from dw2studio.core.native_anim import parse_anim_file, pose_matrix


def source():
    def frame(x):
        m = np.eye(4); m[0, 3] = x
        return [np.eye(4).T.ravel().tolist(), m.T.ravel().tolist()]
    return {'bones': [{'parent': -1, 'faces': []}, {'parent': 0, 'faces': []}],
            'motions': [{'id': 1, 'frames': [frame(0), frame(10)]},
                        {'id': 15, 'lead_blend': 10, 'frames': [frame(110)] * 7},
                        {'id': 16, 'frames': [frame(200), frame(210)]}]}


def positions(data):
    parsed = parse_anim_file(data, 1)
    clip = parsed.clips[0]
    return [pose_matrix(data, parsed.pose_offsets[0], row[0])[1][0] for row in clip.rows], clip


@pytest.mark.parametrize('end', ['hold', 'loop'])
def test_chain_export_blends_from_displayed_row_and_preserves_loop(end):
    # Truncate motion 15 while its opening blend is still running, then add
    # an explicit transition. The next blend must start at the displayed x=40,
    # rather than the unblended source pose x=110.
    action = {'segments': [{'motion': 15, 'start': 0, 'end': 1},
                           {'motion': 16, 'start': 0, 'end': 1, 'blend': 1, 'repeat': 2}],
              'end': end, 'loop_segment': 1, 'loop_frame': 1}
    xs, clip = positions(encode_animation(source(), {0: action}))
    assert xs == [20, 40, 120, 200, 210, 200, 210]
    assert clip.loop_row == (4 if end == 'loop' else None)


def test_legacy_095_encoder_remains_byte_identical():
    s = source()
    from dw2studio.dw3_actions import legacy, motion_table
    # Legacy numeric mapping has no DW3 lead-blend correction. A plain action
    # over a motion without a lead must encode identically, loop or hold.
    for loop in [False, True]:
        old = encode_animation(s, {0: 2}, loops=[0] if loop else [])
        act = legacy(motion_table(s), 16, loop)
        assert encode_animation(s, {0: act}) == old
