// Opens the standalone page with the seed data and prints the allocation as text.
// Usage: node tests/render_test.js [--shots]
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
const ROOT = path.join(__dirname, '..');
(async () => {
  const b = await chromium.launch();
  const shots = process.argv.includes('--shots');
  for (const [w, scheme] of shots ? [[1280, 'light'], [400, 'dark']] : [[1280, 'light']]) {
    const p = await b.newPage({ viewport: { width: w, height: 1000 }, colorScheme: scheme });
    p.on('pageerror', e => console.log('PAGEERR', e.message));
    await p.route('http://local/**', r => {
      const u = new URL(r.request().url()); const f = u.pathname === '/' ? 'index.html' : u.pathname.slice(1);
      r.fulfill({ path: path.join(ROOT, f) });
    });
    await p.goto('http://local/'); await p.waitForTimeout(1200);
    if (!shots) {
      console.log(await p.evaluate(() => [...document.querySelectorAll('#view-result .ship, #view-result .shared, #view-result h2, #view-result .summary')].map(e => e.innerText.replace(/\n+/g, ' | ')).join('\n')));
    } else {
      await p.screenshot({ path: path.join(ROOT, 'tests', 'shot_' + w + '_result.png') });
      await p.click('#tab-fleets'); await p.waitForTimeout(200); await p.screenshot({ path: path.join(ROOT, 'tests', 'shot_' + w + '_fleets.png') });
      await p.click('#tab-inv'); await p.waitForTimeout(300); await p.screenshot({ path: path.join(ROOT, 'tests', 'shot_' + w + '_inv.png') });
    }
    await p.close();
  }
  await b.close();
})();
