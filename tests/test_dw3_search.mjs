import assert from 'node:assert/strict';
import { dw3Matches, dw3Rank } from '../www/dw3_search.js';

const row = { id: 150, file_number: 834, fighter_ids: [359], digimon: 'Imperialdramon-F',
  name: 'M359IPDF', code: 'IPDF', file: 'M359IPDF.BIN',
  aliases: ['Imperialdramon Fighter Mode', 'Imperialdramon FM'] };
for (const q of ['', 'imperialdramon', 'Fighter Mode', 'IPDF', 'm359', '150', '#150', '834', '#834', '359']) {
  assert.equal(dw3Matches(row, q), true, q);
}
for (const q of ['Paladin', 'WarGreymon', '35', '#35', '44', '999', '!!!']) {
  assert.equal(dw3Matches(row, q), false, q);
}
assert.equal(dw3Rank(row, 'Imperialdramon Fighter Mode'), 0);
assert.equal(dw3Rank(row, 'imperial'), 1);
assert.equal(dw3Rank(row, 'IPDF'), 2);
assert.equal(dw3Matches({ id: 0, name: 'M500WAVE' }, '#0'), true);
assert.equal(dw3Matches({ id: 0, name: 'M500WAVE' }, 'wave'), true);
console.log('DW3 search: 22 checks passed');
