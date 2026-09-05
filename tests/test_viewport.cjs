const { test } = require('node:test');
const assert = require('node:assert/strict');
const { fitGame } = require('../viewport.js');

test('portrait, landscape, Safari toolbars and safe areas keep all controls visible', () => {
  const sizes = [[320, 460], [375, 559], [390, 664], [430, 745],
    [667, 275], [844, 290], [932, 320], [1280, 720]];
  // Rectangles include the rightmost sound button and lowest result buttons.
  const buttons = [[368, 9, 58, 32], [430, 9, 58, 32], [562, 9, 66, 32],
    [124, 226, 188, 44], [330, 220, 110, 42], [430, 126, 86, 32]];
  for (const [width, height] of sizes) {
    const availableWidth = width - 100; // conservatively reserve both notches
    const availableHeight = height - 50;
    const frame = fitGame(availableWidth, availableHeight);
    assert.ok(frame.width <= availableWidth + 1e-8);
    assert.ok(frame.height <= availableHeight + 1e-8);
    assert.ok(Math.abs(frame.width / frame.height - 16 / 9) < 1e-8);
    for (const [x, y, w, h] of buttons) {
      assert.ok((x + w) / 640 * frame.width < availableWidth);
      assert.ok((y + h) / 360 * frame.height < availableHeight);
    }
  }
});

test('empty space during orientation change cannot create negative dimensions', () => {
  assert.deepEqual(fitGame(0, 0), { width: 0, height: 0 });
  assert.deepEqual(fitGame(390, 0), { width: 0, height: 0 });
});

test('Safari visual viewport resize updates the existing iframe without reloading', () => {
  const vm = require('node:vm');
  const fs = require('node:fs');
  const stage = { clientWidth: 382, clientHeight: 560 };
  const frame = { style: {}, src: 'player.html' };
  const box = { style: {} };
  const styles = {};
  const listeners = {};
  const view = { width: 390, height: 664, offsetLeft: 0, offsetTop: 0,
    addEventListener: (event, fn) => { listeners[event] = fn; } };
  const context = {
    document: { getElementById: id => ({stage, 'game-frame': frame, 'game-box': box})[id],
      documentElement: { style: { setProperty: (k, v) => { styles[k] = v; } } } },
    window: { visualViewport: view, addEventListener() {}, requestAnimationFrame: fn => fn() },
    ResizeObserver: class { observe() {} },
  };
  vm.runInNewContext(fs.readFileSync(require.resolve('../viewport.js'), 'utf8'), context);
  view.width = 844; view.height = 290; view.offsetTop = 12;
  stage.clientWidth = 744; stage.clientHeight = 261;
  listeners.resize();
  assert.equal(styles['--view-height'], '290px');
  assert.equal(styles['--view-top'], '12px');
  assert.equal(parseFloat(box.style.height), 261);
  assert.equal(frame.style.transform, 'scale(0.725)');
  assert.equal(frame.style.height, undefined);
  assert.equal(frame.src, 'player.html');
});
