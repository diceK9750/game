const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

// Matching the canonical LF bytes preserves the approved artwork, including SVG
// fragment references, and ensures a failed asset request cannot blank a card.
test('all ten embedded card pictures exactly match their source SVGs', () => {
  const css = fs.readFileSync(path.join(__dirname, '..', 'shiritori-ui.css'), 'utf8');
  for (const name of ['daruma', 'top', 'ramune', 'zucchini', 'medaka',
                      'snow_crab', 'blocks', 'parsley', 'mushroom', 'paint']) {
    const selector = name === 'daruma' ? 'sh-daruma' : `sh-art-${name}`;
    const rule = css.match(new RegExp(`\\.${selector}\\s*\\{[^}]*url\\('data:image/svg\\+xml;base64,([^']+)'\\)`));
    assert.ok(rule, `${name} must have embedded SVG data`);
    const original = Buffer.from(fs.readFileSync(path.join(__dirname, '..', 'assets', 'shiritori', `${name}.svg`), 'utf8').replace(/\r\n/g, '\n'), 'utf8');
    assert.deepEqual(Buffer.from(rule[1], 'base64'), original, `${name} must match the source bytes`);
    assert.ok(!css.includes(`url('assets/shiritori/${name}.svg')`), `${name} must not require a separate request`);
  }
});
