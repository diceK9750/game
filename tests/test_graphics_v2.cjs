const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

test('shared modern graphics use locally shipped, bounded high-resolution assets', () => {
  const css = fs.readFileSync(path.join(__dirname, '../modern-ui.css'), 'utf8');
  for (const file of ['characters/rin-portraits-v2.png', 'characters/luna-portraits-v2.png', 'backgrounds/lantern-forest-v2.png']) {
    assert.ok(css.includes('assets/' + file));
    const png = fs.readFileSync(path.join(__dirname, '../assets', file));
    assert.equal(png.subarray(1,4).toString(), 'PNG');
    assert.ok(png.length < 4 * 1024 * 1024, file + ' download budget');
    if (file.startsWith('characters')) {
      assert.equal(png.readUInt32BE(16), 1536);
      assert.equal(png.readUInt32BE(20), 1024);
    } else {
      assert.ok(png.readUInt32BE(16) >= 1500);
      assert.ok(png.readUInt32BE(16) / png.readUInt32BE(20) > 1.7);
    }
  }
  assert.match(css, /background-size: 300% 200%/);
  assert.match(fs.readFileSync(path.join(__dirname,'../.github/workflows/pages.yml'),'utf8'), /cp -r assets _site/);
});
