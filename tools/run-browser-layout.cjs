/* Runs the same real-DOM regression fixture used for interactive debugging. */
const { chromium } = require('playwright');

async function main() {
  const url = process.argv[2] || 'http://127.0.0.1:8765/tests/browser-layout.html';
  const errors = [];
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.CHROMIUM_BINARY ? { executablePath: process.env.CHROMIUM_BINARY } : {}),
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });
    page.on('pageerror', error => errors.push(error.message));
    // Allow the local HTTP server a moment to start; no external services are used.
    let lastError;
    for (let attempt = 0; attempt < 30; attempt++) {
      try { await page.goto(url, { waitUntil: 'load', timeout: 5000 }); lastError = null; break; }
      catch (error) { lastError = error; await new Promise(resolve => setTimeout(resolve, 200)); }
    }
    if (lastError) throw lastError;
    await page.locator('#run').click();
    await page.waitForFunction(() => document.querySelector('#status').textContent.startsWith('DONE:'), null, { timeout: 180000 });
    const layout = JSON.parse(await page.locator('#report').textContent());
    console.log(await page.locator('#status').textContent());
    if (!layout.total || layout.failed || !layout.detectsOldHud || !layout.independence.length || layout.independence.some(result => !result.stable)) {
      throw new Error(`Layout regression failed: ${JSON.stringify({ failed: layout.failures, detectsOldHud: layout.detectsOldHud, unstable: layout.independence.filter(result => !result.stable) })}`);
    }
    await page.locator('#run-fx').click();
    await page.waitForFunction(() => document.querySelector('#status').textContent.startsWith('HIGHLIGHT:'), null, { timeout: 180000 });
    const highlights = JSON.parse(await page.locator('#report').textContent());
    console.log(await page.locator('#status').textContent());
    if (!highlights.total || highlights.failed) throw new Error(`Highlight regression failed: ${JSON.stringify(highlights.failures)}`);
    if (errors.length) throw new Error(`Uncaught browser errors: ${errors.join('; ')}`);
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
