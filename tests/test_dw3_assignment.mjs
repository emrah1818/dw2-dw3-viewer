import assert from 'node:assert/strict';
import { chooseMotion, motionEndText } from '../www/dw3_assignment.js';
const original = {slot: 'F', clip: 0, motion: 1, loop: true,
  action: {segments: [{motion: 1}, {motion: 15}], end: 'loop'}};
for (const [id, end, loop] of [[1, 'loop', true], [16, 'loop', true], [17, 'idle', true], [15, 'hold', false]]) {
  const result = chooseMotion(original, {id, end});
  assert.equal(result.selection, 'motion');
  assert.equal(result.motion, id);
  assert.equal(result.loop, loop);
}
assert.equal(original.motion, 1);
assert.equal(original.action.segments.length, 2);
assert.match(motionEndText({end: 'loop', loop_frame: 7}), /Bild 7/);
assert.match(motionEndText({end: 'idle'}), /Standby/);
assert.match(motionEndText({end: 'hold'}), /halten/);
console.log('Manual motion selection: 17 checks passed');
