const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  const fs = require('fs');
  const inv = JSON.parse(fs.readFileSync('seed/inventory.json')).counts, fl = JSON.parse(fs.readFileSync('seed/fleets.json')).fleets;
  p.on('console', m => console.log('CONSOLE', m.type(), m.text()));
  p.on('pageerror', e => console.log('PAGEERR', e.message));
  await p.route('http://local/', r => r.fulfill({ contentType: 'text/html', body: '<!doctype html><meta charset=utf-8><body>' + fs.readFileSync('al_gear_planner.html', 'utf8') }));
  await p.goto('http://local/');
  await p.evaluate(([a, b]) => { localStorage.setItem('al-inv', JSON.stringify(a)); localStorage.setItem('al-fleets', JSON.stringify(b)); }, [inv, fl]);
  await p.reload(); await p.waitForTimeout(800);
  const txt = await p.evaluate(() => [...document.querySelectorAll('#view-result .ship, #view-result .shared, #view-result h2, #view-result .summary')].map(e => e.innerText.replace(/\n+/g, ' | ')).join('\n'));
  console.log(txt);
  await p.setViewportSize({ width: 1280, height: 900 }); 
  await b.close();
})();
