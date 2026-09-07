const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const { isModernReadyMessage } = require('../viewport.js');

function shell({ fullscreenSupported = false } = {}) {
  const listeners = {};
  const attrs = {};
  const timers = [];
  const buttons = {};
  let reloads = 0;
  let fullscreenRequests = 0;
  const root = { style: { setProperty() {} }, setAttribute: (key, value) => { attrs[key] = value; } };
  if (fullscreenSupported) root.requestFullscreen = () => { fullscreenRequests += 1; };
  const stage = { clientWidth: 382, clientHeight: 560 };
  const frame = { style: {}, src: 'player.html', contentWindow: {} };
  const box = { style: {} };
  const status = { textContent: '' };
  const help = { hidden: true };
  const reload = { addEventListener: (name, fn) => { buttons[name] = fn; } };
  const fullscreen = { hidden: true,
    addEventListener: (name, fn) => { buttons[`fullscreen:${name}`] = fn; } };
  const elements = { stage, 'game-frame': frame, 'game-box': box,
    'loading-status': status, 'connection-help': help, 'reload-button': reload,
    'fullscreen-button': fullscreen };
  const context = {
    document: { documentElement: root, getElementById: id => elements[id],
      fullscreenEnabled: fullscreenSupported },
    window: { innerWidth: 390, innerHeight: 664,
      location: { origin: 'http://localhost:8018', reload: () => { reloads += 1; } },
      addEventListener: (name, fn) => { listeners[name] = fn; },
      requestAnimationFrame: fn => fn(),
      setTimeout: fn => { timers.push(fn); return timers.length; },
      clearTimeout: id => { timers[id - 1] = null; } },
    ResizeObserver: class { observe() {} },
  };
  vm.runInNewContext(fs.readFileSync(require.resolve('../viewport.js'), 'utf8'), context);
  return { listeners, attrs, stage, frame, box, status, help, timers, buttons,
    fullscreen, fullscreenRequests: () => fullscreenRequests,
    reloads: () => reloads, origin: context.window.location.origin };
}

test('responsive readiness is accepted only from the game iframe on this origin', () => {
  const source = {};
  const data = { type: 'number-rush-modern-ready' };
  const origin = 'https://example.com';
  assert.equal(isModernReadyMessage({ source, origin, data }, source, origin), true);
  for (const event of [null, {}, { source: {}, origin, data },
    { source, origin: 'https://other.example', data }, { source, origin, data: null },
    { source, origin, data: { type: 'ready' } }]) {
    assert.equal(isModernReadyMessage(event, source, origin), false);
  }
  assert.equal(isModernReadyMessage({ source, origin: 'null', data }, source, 'null'), false);
  assert.equal(isModernReadyMessage({ source: undefined, origin, data }, undefined, origin), false);
});

test('fallback remains scaled until a trusted first engine state, then uses real viewport', () => {
  const app = shell();
  assert.match(app.frame.style.transform, /^scale\(/);
  assert.equal(app.frame.style.height, undefined);
  app.listeners.message({ source: {}, origin: app.origin, data: { type: 'number-rush-modern-ready' } });
  assert.equal(app.attrs['data-app-ready'], undefined);
  app.listeners.message({ source: app.frame.contentWindow, origin: app.origin,
    data: { type: 'number-rush-modern-ready' } });
  assert.equal(app.attrs['data-app-ready'], 'true');
  assert.equal(app.frame.style.width, '382px');
  assert.equal(app.frame.style.height, '560px');
  assert.equal(app.frame.style.transform, 'none');
  assert.equal(app.timers[0], null);
  app.stage.clientWidth = 744;
  app.stage.clientHeight = 261;
  app.listeners.resize();
  assert.equal(app.frame.style.width, '744px');
  assert.equal(app.frame.style.height, '261px');
  assert.equal(app.frame.src, 'player.html');
  assert.equal(app.reloads(), 0);
});

test('slow startup offers help without automatically reloading the game', () => {
  const app = shell();
  app.timers[0]();
  assert.equal(app.help.hidden, false);
  assert.equal(app.status.textContent, '起動を待っています。');
  assert.equal(app.reloads(), 0);
  app.buttons.click();
  assert.equal(app.reloads(), 1);
});

test('trusted runtime failure restores the fixed Pyxel viewport without reload', () => {
  const app = shell();
  app.listeners.message({ source: app.frame.contentWindow, origin: app.origin,
    data: { type: 'number-rush-modern-ready' } });
  const fallback = { type: 'number-rush-modern-fallback' };
  app.listeners.message({ source: {}, origin: app.origin, data: fallback });
  app.listeners.message({ source: app.frame.contentWindow, origin: 'https://other.example', data: fallback });
  assert.equal(app.attrs['data-app-ready'], 'true');
  assert.equal(app.frame.style.transform, 'none');
  app.listeners.message({ source: app.frame.contentWindow, origin: app.origin, data: fallback });
  assert.equal(app.attrs['data-app-ready'], 'false');
  assert.equal(app.frame.style.width, '640px');
  assert.equal(app.frame.style.height, '360px');
  assert.equal(app.frame.style.transform, 'scale(0.596875)');
  assert.equal(app.status.textContent, '軽量表示に切り替えました');
  assert.equal(app.help.hidden, true);
  assert.equal(app.reloads(), 0);
  app.stage.clientWidth = 744;
  app.stage.clientHeight = 261;
  app.listeners.resize();
  assert.equal(app.frame.style.width, '640px');
  assert.equal(app.frame.style.height, '360px');
  assert.equal(app.frame.style.transform, 'scale(0.725)');
  assert.equal(app.frame.src, 'player.html');
});

test('fullscreen is offered only when supported and starts only on user click', async () => {
  assert.equal(shell().fullscreen.hidden, true);
  const app = shell({ fullscreenSupported: true });
  assert.equal(app.fullscreen.hidden, false);
  assert.equal(app.fullscreenRequests(), 0);
  await app.buttons['fullscreen:click']();
  assert.equal(app.fullscreenRequests(), 1);
});

test('startup information does not overlay the iframe or advertise offline support', () => {
  const html = fs.readFileSync(require.resolve('../index.html'), 'utf8');
  assert.match(html, /初回は通信が必要/);
  assert.match(html, /aria-live="polite"/);
  assert.match(html, /html\[data-app-ready="true"\] header/);
  assert.match(html, /safe-area-inset-bottom/);
  assert.ok(html.indexOf('id="loading-status"') < html.indexOf('<section id="stage"'));
  assert.doesNotMatch(html, /serviceWorker|オフラインで/);
});
