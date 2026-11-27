// Business-rule tests for the DP World Platform prototype (dummy data).
// Run from the repo root:  node --test tests/
// Needs Node 18+ and Playwright (Chromium). No network: the page is opened from disk.
const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { chromium } = require('playwright');

const PAGE = 'file://' + path.resolve(__dirname, '../app/DP_World_Platform_DEMO.html');
let browser, page; const pageErrors = [];

before(async () => {
  browser = await chromium.launch();
  page = await browser.newPage();
  page.on('pageerror', e => pageErrors.push(e.message));
  // block external CDNs so the test runs offline and the same every time
  await page.route(/^https?:\/\//, r => r.abort());
  await page.goto(PAGE, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => !!window.__rules);
});
after(async () => { await browser?.close(); });

const run = (fn, arg) => page.evaluate(fn, arg);

test('page loads with no JavaScript errors', () => {
  assert.deepEqual(pageErrors, []);
});

test('rule 1: rows with a Contract Type are not standard', async () => {
  const r = await run(() => { const { isStd } = window.__rules;
    return [isStd({}), isStd({ type: '' }), isStd({ type: 'Standard' }), isStd({ type: 'Spot' }),
            isStd({ type: 'Special' }), isStd({ type: 'Reefer' }), isStd({ type: 'DG' }), isStd({ type: 'Volume' })]; });
  assert.deepEqual(r, [true, true, true, false, false, false, false, false]);
});

test('rule 1: margin gap ignores a cheaper special/spot rate', async () => {
  // buy 1000 (standard). Next standard carrier is 1200. A spot row at 1050 must be ignored.
  const g = await run(() => { const R = window.__rules; R.setCargo('dry');
    R.setOptRows([
      { car: 'A Line', r40: 1000, ok: true },
      { car: 'Spot Line', r40: 1050, ok: true, type: 'Spot' },
      { car: 'B Line', r40: 1200, ok: true },
    ]);
    const out = R.gapInfo(1000, false); R.setOptRows([]); return out; });
  assert.match(g.why, /gap to the next carrier USD 200/);
  assert.equal(g.m, 120); // 60% of 200
});

test('rule 1: expired rows do not count in the gap', async () => {
  const g = await run(() => { const R = window.__rules; R.setCargo('dry');
    R.setOptRows([{ car: 'A', r40: 1000, ok: true }, { car: 'Old', r40: 1100, ok: false }, { car: 'B', r40: 1300, ok: true }]);
    const out = R.gapInfo(1000, false); R.setOptRows([]); return out; });
  assert.match(g.why, /USD 300/);
});

test('rule 4: China dry export = USD 25 per 20\' and USD 50 per 40\'', async () => {
  const m = await run(() => { const R = window.__rules; R.setCargo('dry');
    Object.assign(R.quote, { dir: 'exp', dest: 'Shanghai' });
    return [R.ruleMargin(true, 900), R.ruleMargin(false, 1800)]; });
  assert.deepEqual(m, [25, 50]);
  // worked example from CLAUDE.md: buy 1,800 + 50 = sell 1,850
  assert.equal(1800 + m[1], 1850);
});

test('rule 4: China fixed margin does not apply to imports or reefer', async () => {
  const m = await run(() => { const R = window.__rules; R.setOptRows([]);
    Object.assign(R.quote, { dir: 'imp', dest: 'Shanghai' }); R.setCargo('dry');
    const imp = R.ruleMargin(false, 1800);
    Object.assign(R.quote, { dir: 'exp', dest: 'Shanghai' }); R.setCargo('rf');
    const rf = R.ruleMargin(false, 1800); R.setCargo('dry');
    return [imp, rf, R.MRG_DEF]; });
  assert.notEqual(m[0], 50); assert.notEqual(m[1], 50);
});

test('rule 4: non-China lane margin comes from the gap, not a fixed number', async () => {
  const m = await run(() => { const R = window.__rules; R.setCargo('dry');
    Object.assign(R.quote, { dir: 'exp', dest: 'Jeddah' });
    R.setOptRows([{ car: 'A', r40: 800, ok: true }, { car: 'B', r40: 900, ok: true }]);
    const out = R.ruleMargin(false, 800); R.setOptRows([]); return out; });
  assert.equal(m, 60); // gap 100 -> 60% = 60
});

test('rule 2: a rate with no validity date is valid to the end of the month', async () => {
  const r = await run(() => { const R = window.__rules; R.setCargo('dry');
    const d = new Date(), eom = new Date(d.getFullYear(), d.getMonth() + 1, 0);
    const want = eom.getFullYear() + '-' + String(eom.getMonth() + 1).padStart(2, '0') + '-' + String(eom.getDate()).padStart(2, '0');
    const row = { pol: 'Sokhna', pod: 'TestPort', car: 'X', r40: 1 }; DATA.rates.push(row);
    const out = R.expRows('TestPort', 'TestPort'); DATA.rates.pop();
    return { got: out[0].valid, ok: out[0].ok, want, eom: R.endOfMonth() }; });
  assert.equal(r.eom, r.want);
  assert.equal(r.got, r.want);
  assert.equal(r.ok, true);
});

test('data file: lane "lowest 40\'" uses valid standard rates only', () => {
  const D = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../data/demo_data.json'), 'utf8'));
  const asof = D.asof || '0000-00-00';
  for (const [pod, L] of Object.entries(D.lanes || {})) {
    if (L.min40 == null) continue;
    const std = (D.rates || []).filter(r => r.pod === pod && !r.type && r.r40 && r.valid >= asof);
    if (!std.length) continue;
    const min = Math.min(...std.map(r => r.r40));
    assert.ok(L.min40 <= min || std.some(r => r.r40 === L.min40), `${pod}: min40 ${L.min40} vs standard min ${min}`);
  }
});

test('rule: a line suspended to Jebel Ali is never shown as an option there', async () => {
  const r = await run(() => { const R = window.__rules; R.setCargo('dry');
    const rows = [{ pol: 'Sokhna', pod: 'Jebel Ali', car: 'Demo Suspended Line', r40: 500, valid: '2099-01-01' },
                  { pol: 'Sokhna', pod: 'Jebel Ali', car: 'OK Line', r40: 900, valid: '2099-01-01' },
                  { pol: 'Sokhna', pod: 'Jeddah', car: 'Demo Suspended Line', r40: 700, valid: '2099-01-01' }];
    DATA.rates.push(...rows);
    const jea = R.expRows('Jebel Ali', 'Jebel Ali').map(x => x.car);
    const jed = R.expRows('Jeddah', 'Jeddah').map(x => x.car);
    DATA.rates.splice(DATA.rates.length - 3, 3);
    return { jea, jed }; });
  assert.ok(!r.jea.includes('Demo Suspended Line'));
  assert.ok(r.jea.includes('OK Line'));
  assert.ok(r.jed.includes('Demo Suspended Line')); // other lanes are not affected
});
