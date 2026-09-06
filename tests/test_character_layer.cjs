const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {portraitPosition, parseCharacterState, CHARACTER_RECTS} = require('../character-layer.js');

test('all six expressions map to distinct atlas cells', () => {
  assert.deepEqual(['idle', 'celebrate', 'victory', 'hurt', 'frustrated', 'defeat'].map(portraitPosition),
    ['0% 0%', '50% 0%', '100% 0%', '0% 100%', '50% 100%', '100% 100%']);
  assert.equal(portraitPosition('unknown'), '0% 0%');
});

test('portraits are hidden on help, pause, review and restart screens', () => {
  for (const screen of ['help', 'confirm', 'resuming', 'review', 'boot']) {
    assert.equal(parseCharacterState(JSON.stringify({screen})).visible, false);
  }
  for (const screen of ['ready', 'countdown', 'playing', 'finished']) {
    assert.equal(parseCharacterState(JSON.stringify({screen})).visible, true);
  }
  assert.equal(parseCharacterState('broken'), null);
  assert.equal(parseCharacterState('null'), null);
  assert.equal(parseCharacterState('{"left":"__proto__"}').left, 'idle');
});

test('character panels never cover board or menu/result buttons', () => {
  const obstacles = [[96, 58, 453, 172], [112, 54, 416, 222], [118, 62, 404, 214],
    [158, 250, 324, 94], [222, 282, 196, 30], [182, 301, 110, 32]];
  for (const [x,y,w,h] of CHARACTER_RECTS) {
    assert.ok(x >= 0 && y >= 0 && x+w <= 640 && y+h <= 360);
    for (const [ox,oy,ow,oh] of obstacles) {
      assert.ok(x+w <= ox || x >= ox+ow || y+h <= oy || y >= oy+oh);
    }
  }
  const css = fs.readFileSync(require.resolve('../character-layer.css'), 'utf8');
  assert.match(css, /pointer-events: none/);
  assert.match(css, /prefers-reduced-motion/);
});

test('both production atlases are local 1536x1024 PNGs', () => {
  for (const name of ['rin', 'koh']) {
    const bytes = fs.readFileSync(require.resolve(`../assets/characters/${name}-atlas.png`));
    assert.equal(bytes.subarray(1,4).toString(), 'PNG');
    assert.equal(bytes.readUInt32BE(16), 1536);
    assert.equal(bytes.readUInt32BE(20), 1024);
    assert.ok(bytes.length < 4 * 1024 * 1024);
  }
});
