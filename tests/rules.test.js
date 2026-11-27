// Business-rule tests for the DP World Platform prototype (dummy data).
// Run from the repo root:  node --test tests/rules.test.js
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

test('rule 4: no dearer carrier -> reuse the newest margin quoted on this lane (option B)', async () => {
  const r = await run(() => { const R = window.__rules; R.setCargo('dry');
    Object.assign(R.quote, { dir: 'exp', dest: 'Jeddah' });
    R.setOptRows([{ car: 'Only Line', r40: 800, ok: true }]);
    const keep = R.QT.items; R.QT.items = [
      { dir: 'exp', pod: 'Jeddah', eq: "40' HC", buy: 750, sell: 820, created: '2026-10-01' },
      { dir: 'exp', pod: 'Jeddah', eq: "40' HC", buy: 760, sell: 845, created: '2026-11-10' }, // newest -> 85
      { dir: 'exp', pod: 'Jeddah', eq: "20' DC", buy: 500, sell: 540, created: '2026-11-20' }, // other size
      { dir: 'imp', pod: 'Jeddah', eq: "40' HC", buy: 700, sell: 900, created: '2026-11-25' }, // other direction
    ];
    const g = R.gapInfo(800, false), m = R.ruleMargin(false, 800);
    R.QT.items = keep; R.setOptRows([]); return { g, m }; });
  assert.equal(r.m, 85);
  assert.equal(r.g.src, 'hist');
  assert.match(r.g.why, /last margin used on this lane, USD 85/);
});

test('rule 4: no dearer carrier and no past quote -> no flat number, margin must be typed (option A)', async () => {
  const r = await run(() => { const R = window.__rules; R.setCargo('dry');
    Object.assign(R.quote, { dir: 'exp', dest: 'Jeddah' });
    R.setOptRows([{ car: 'Only Line', r40: 800, ok: true }]);
    const keep = R.QT.items; R.QT.items = [];
    const m = R.ruleMargin(false, 800), g = R.gapInfo(800, false), noBuy = R.ruleMargin(false);
    R.QT.items = keep; R.setOptRows([]); return { m: String(m), noBuy: String(noBuy), src: g.src, shown: R.money(800 + m) }; });
  assert.equal(r.m, 'NaN');
  assert.equal(r.noBuy, 'NaN');
  assert.equal(r.src, 'none');
  assert.equal(r.shown, '—'); // a sell price is never shown as the bare buy rate
});

test('publish rule: no AI / LLM calls inside the page, external hosts are only the allowed CDNs', () => {
  const s = fs.readFileSync(path.resolve(__dirname, '../app/DP_World_Platform_DEMO.html'), 'utf8');
  for (const bad of [/api\.anthropic\.com/i, /api\.openai\.com/i, /generativelanguage\.googleapis/i, /\/v1\/(messages|chat\/completions|completions)/i,
                     /claude\.use\(\s*["']ai["']/i, /claude\.(complete|ask|prompt)\s*\(/i])
    assert.ok(!bad.test(s), 'found AI/LLM call: ' + bad);
  const hosts = new Set([...s.matchAll(/https?:\/\/([a-z0-9.-]+)/gi)].map(m => m[1].toLowerCase()));
  const allowed = new Set(['cdnjs.cloudflare.com', 'fonts.googleapis.com', 'fonts.gstatic.com', 'mail.google.com', 'outlook.office.com', 'www.w3.org']);
  for (const h of hosts) assert.ok(allowed.has(h), 'unexpected external host: ' + h);
});

test('rate bank: suspensions come from the Rate Bank "Suspensions" sheet (with dates)', async () => {
  const r = await run(() => { const R = window.__rules, keep = DATA.susp;
    DATA.susp = [{ car: 'Aurora Lines', pod: 'Jeddah', since: '2020-01-01', until: '' },
                 { car: 'Delta Marine', pod: '', since: '2020-01-01', until: '2020-12-31' },   // ended: not suspended
                 { car: 'Pharos Line', pod: '', since: '2020-01-01', until: '' }];           // empty POD = all lanes
    const out = [!!R.rbSuspended('Aurora Lines', 'Jeddah'), !!R.rbSuspended('Aurora Lines', 'Valencia'),
                 !!R.rbSuspended('Delta Marine', 'Jeddah'), !!R.rbSuspended('Pharos Line', 'Anywhere')];
    DATA.susp = keep; return out; });
  assert.deepEqual(r, [true, false, false, true]);
});

test('rate bank: the seeded suspension hides the cheap suspended line at Jebel Ali', async () => {
  const cars = await run(() => window.__rules.expRows('Jebel Ali', 'Jebel Ali').map(r => r.car));
  assert.ok(cars.length > 0);
  assert.ok(!cars.includes('Demo Suspended Line'));
});

test('rate bank: margin rules come from the "Margin Rules" sheet', async () => {
  const r = await run(() => { const R = window.__rules; return { n: R.MARGIN_RULES.length, name: R.MARGIN_RULES[0].name, src: Array.isArray(DATA.mrules) }; });
  assert.equal(r.src, true); assert.equal(r.name, 'Dry export to China');
});

test('rate bank: every rate row carries a unique Rate ID', () => {
  const D = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../data/demo_data.json'), 'utf8'));
  const all = [...D.rates, ...D.reefers, ...D.imports];
  assert.ok(all.every(r => /^(EX|IM)-\d{5}$/.test(r.id)), 'missing or malformed Rate ID');
  assert.equal(new Set(all.map(r => r.id)).size, all.length, 'duplicate Rate ID');
});

test('rate bank: the converter flags bad rows', () => {
  const { execFileSync } = require('node:child_process');
  const os = require('node:os');
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'rb-'));
  const xl = path.join(tmp, 'rb.xlsx'), js = path.join(tmp, 'd.json');
  fs.copyFileSync(path.resolve(__dirname, '../data/demo_data.json'), js);
  // build a small workbook with known mistakes
  execFileSync('python3', ['-c', `
import openpyxl,datetime,sys
wb=openpyxl.Workbook(); ws=wb.active; ws.title='Rates'
ws.append(['Rate ID','Direction','Cargo','Contract Type','Customer (named rates)','Carrier','POL','POL Terminal','POD','Via',"20'","40'","20' RF","40' RF",'Currency',"THC 20'","THC 40'",'THC Currency','Free Time','Valid From','Valid To','Spot Sailing (vessel / voyage)','Transit Days','Source','Source Ref (email subject or file)','Added By','Added On','Comment'])
ws.append(['EX-00001','Export','Dry','Standard','','A Line','Sokhna','','Jeddah','',900,700,None,None,'USD',None,None,'','','','','','','','','',datetime.datetime(2026,11,1),''])
ws.append(['EX-00001','Export','Dry','Spot','','B Line','Alexandria','','Valencia','',500,800,None,None,'USD',None,None,'','','','','','','','','',datetime.datetime(2026,11,1),''])
for n,h in (('Suspensions',['Carrier','POD (empty = all)','From','Until (empty = no end)','Reason','Set by']),('Margin Rules',['Rule name','Direction','Cargo','POD contains (separate with ;)',"Margin 20' (USD)","Margin 40' (USD)",'Note']),('Contacts',['Carrier','Pricing email','Sales email'])):
    wb.create_sheet(n).append(h)
wb.save(sys.argv[1])`, xl]);
  execFileSync('python3', [path.resolve(__dirname, '../scripts/pricing_rate_bank_to_data.py'), xl, js, '2026-11-19']);
  const k = JSON.parse(fs.readFileSync(js, 'utf8')).health.issues.map(i => i.k).sort();
  assert.deepEqual(k, ['dup', 'dup', 'r40lt20', 'spot', 'term']); // both rows that share an ID are flagged
});

test('rule 1 (screen): the default buy rate on a lane is the lowest STANDARD rate, not a spot rate', async () => {
  const pg = await browser.newPage(); await pg.route(/^https?:\/\//, x => x.abort()); await pg.goto(PAGE); await pg.waitForFunction(() => !!window.__rules);
  const r = await pg.evaluate(() => new Promise(res => { const t = document.getElementById('to'); t.value = 'Jeddah'; t.dispatchEvent(new Event('change'));
    setTimeout(() => res({ buy: document.getElementById('q-buy').value, car: document.getElementById('q-car').value,
      spot: DATA.rates.find(x => x.pod === 'Jeddah' && x.type === 'Spot').r40, min: DATA.lanes.Jeddah.min40 }), 600); }));
  assert.ok(+r.spot < +r.min, 'test data needs a spot rate cheaper than the lowest standard');
  assert.equal(+r.buy, +r.min);
  await pg.close();
});

test('data sources: any table with Carrier, POL, POD and a rate column is read; contract type kept', async () => {
  const r = await run(() => window.__rules.dsNormalize([
    ['Rates for December (dummy)'], [],
    ['Line', 'Port of Loading', 'Destination', "40'HC", "20'", 'Validity', 'Contract Type', 'Remarks'],
    ['Zeta Line', 'Sokhna', 'Jeddah', '1,200', 800, '2026-12-31', '', 'ok'],
    ['Zeta Line', 'Sokhna', 'Jeddah', 900, 600, '', 'Spot', ''],
    ['', 'Sokhna', 'Jeddah', 900, 600, '', '', ''],
  ]));
  assert.equal(r.rates.length, 2); assert.equal(r.skip, 1);
  assert.equal(r.rates[0].r40, 1200); assert.equal(r.rates[0].valid, '2026-12-31'); assert.ok(!r.rates[0].type);
  assert.equal(r.rates[1].type, 'Spot'); assert.ok(r.rates[1].validAssumed);
});

test('data sources: WhatsApp chat export -> rates (marked) and announcements', async () => {
  const txt = fs.readFileSync(path.resolve(__dirname, '../data/Demo WhatsApp chat (dummy).txt'), 'utf8');
  const r = await run(t => window.__rules.dsWhatsApp(t, ''), txt);
  assert.equal(r.msgs, 6);
  assert.deepEqual(r.rates.map(x => [x.car, x.pod, x.r20, x.r40, x.valid, x.wa]),
    [['Aurora Lines', 'Jeddah', 600, 780, '2026-12-31', true], ['Aurora Lines', 'Jebel Ali', 900, 1300, '2026-12-31', true]]);
  assert.deepEqual(r.news.map(n => n.tag).sort(), ['BLANK SAILING', 'GRI']);
  assert.equal(r.nocar, 1); // "Zeta NVOCC" is not a known carrier: rate not used
});

test('data sources: a higher source wins on the same carrier, lane, type and month', async () => {
  const r = await run(() => { const R = window.__rules, D = R.DS, keep = [D.list, D.rows];
    D.list = [{ id: 't1', name: 'Test link', kind: 'url', on: true }];
    D.rows = { t1: { rates: [{ car: 'Sahara Feeder', pol: 'Sokhna', pod: 'Jeddah', r20: 600, r40: 800, cur: 'USD', valid: '2026-12-20' },
                             { car: 'New Line', pol: 'Sokhna', pod: 'Jeddah', r20: 500, r40: 700, cur: 'USD', valid: '2099-12-31' }], imports: [] } };
    R.dsApply(); const used = DATA.rates.filter(x => x.src === 'Test link').map(x => x.car), conf = D.conf.length;
    D.list = keep[0]; D.rows = keep[1]; R.dsApply(); return { used, conf, after: DATA.rates.some(x => x.src === 'Test link') }; });
  assert.deepEqual(r.used, ['New Line']); assert.equal(r.conf, 1); assert.equal(r.after, false);
});

test('margin advisor: picks the margin band with the best expected profit, capped by the next carrier and market', async () => {
  const r = await run(() => { const S = window.__rules.marginStudy;
    const hist = [];  // lane history: 50s win often, 100s win half, 200s rarely
    for (let i = 0; i < 10; i++) hist.push({ m: 50, won: i < 8, reason: 'Price too high', lane: true });
    for (let i = 0; i < 10; i++) hist.push({ m: 120, won: i < 6, reason: 'Price too high', lane: true });
    for (let i = 0; i < 10; i++) hist.push({ m: 220, won: i < 1, reason: 'Price too high', lane: true });
    for (let i = 0; i < 5; i++) hist.push({ m: 300, won: false, reason: 'Shipment cancelled or postponed', lane: true }); // not about price: ignored
    const base = { buy: 1000, others: [{ car: 'B', v: 1300 }], market: { val: 1200, src: 'test' }, hist, fb: [] };
    return { free: S(base), capped: S({ ...base, others: [{ car: 'B', v: 1080 }] }), target: S({ ...base, fb: [{ target: 1090 }] }),
             china: S({ ...base, rule: { name: 'Dry export to China', m: 50 } }), none: S({ buy: 1000, others: [], hist: [], fb: [] }) }; });
  assert.equal(r.free.rec, 120);               // 120 x 60% beats 50 x 80% and 220 x 10%
  assert.equal(r.free.n, 30);                  // the 5 cancelled quotes are not counted
  assert.equal(r.free.conf, 'High');
  assert.equal(r.capped.rec, 75);              // next carrier only USD 80 above: stay under its cost
  assert.equal(r.target.rec, 90);              // customer target 1090
  assert.equal(r.china.rec, 50); assert.equal(r.china.fixed, true);
  assert.equal(r.none.rec, null);              // no data: no number invented
});

test('data layer: the lane summary built in the page equals the converter\'s', async () => {
  const diff = await run(() => { const L = window.__rules.buildLanes(DATA, {}); return Object.keys(DATA.lanes).filter(p => (DATA.lanes[p].min40 ?? null) !== (L[p] ? L[p].min40 ?? null : null)); });
  assert.deepEqual(diff, []);
});

test('data layer: the contract check stops bad data', async () => {
  const r = await run(() => { const C = window.__rules.dataCheck;
    return { good: C(DATA).ok, noRates: C({}).ok, bad: C({ rates: [{ car: 'A', pol: 'Sokhna', pod: '', r40: '900', valid: '30/11/2026' }] }).errs,
             dup: C({ rates: [{ id: 'X', car: 'A', pol: 'P', pod: 'Q', r40: 1 }, { id: 'X', car: 'B', pol: 'P', pod: 'Q', r40: 2 }] }).errs }; });
  assert.equal(r.good, true); assert.equal(r.noRates, false);
  assert.ok(r.bad.some(e => /pod is missing/.test(e)) && r.bad.some(e => /r40 must be a number/.test(e)) && r.bad.some(e => /YYYY-MM-DD/.test(e)));
  assert.ok(r.dup.some(e => /not unique/.test(e)));
});

test('data layer: NPM fields map to the contract (assumed names)', async () => {
  const m = await run(() => window.__rules.npmMap({ rates: [
    { rateId: 'N1', carrierName: 'Aurora Lines', originPort: 'Sokhna', destinationPort: 'Jeddah', containerRates: { '20GP': 600, '40HC': 800 }, currency: 'USD', validTo: '2026-12-31T00:00:00Z', contractType: 'Spot' },
    { rateId: 'N2', carrierName: 'Orion Lines', originPort: 'Shanghai', destinationPort: 'Sokhna', direction: 'IMPORT', containerRates: { '40HC': 1300 } },
    { rateId: 'N3', carrierName: 'Red Sea Express', originPort: 'Sokhna', destinationPort: 'Jeddah', containerRates: { '40RF': 1650 } }] }));
  assert.deepEqual([m.rates.length, m.imports.length, m.reefers.length], [1, 1, 1]);
  assert.deepEqual([m.rates[0].r20, m.rates[0].r40, m.rates[0].valid, m.rates[0].type], [600, 800, '2026-12-31', 'Spot']);
});

test('data layer: switching the main source to a JSON link changes every screen; bad data is refused', async () => {
  const base = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../data/demo_data.json'), 'utf8'));
  const good = JSON.parse(JSON.stringify(base)); delete good.lanes;
  good.rates.find(r => r.pod === 'Jeddah' && r.car === 'Sahara Feeder').r40 = 700; good.asof = '2026-11-28';
  const pg = await browser.newPage();
  await pg.route(/^https?:\/\//, r => { const u = r.request().url();
    if (u === 'https://data.example/good.json') return r.fulfill({ status: 200, headers: { 'content-type': 'application/json', 'access-control-allow-origin': '*' }, body: JSON.stringify(good) });
    if (u === 'https://data.example/bad.json') return r.fulfill({ status: 200, headers: { 'content-type': 'application/json', 'access-control-allow-origin': '*' }, body: JSON.stringify({ rates: [{ car: 'X' }] }) });
    return r.abort(); });
  await pg.goto(PAGE); await pg.waitForFunction(() => !!window.__rules);
  const bad = await pg.evaluate(async () => { const ok = await window.__rules.dataBoot({ source: 'json', url: 'https://data.example/bad.json' }); return { ok, min: DATA.lanes.Jeddah.min40 }; });
  assert.equal(bad.ok, false); assert.equal(bad.min, 850);           // kept the data inside the page
  const r = await pg.evaluate(async () => { const ok = await window.__rules.dataBoot({ source: 'json', url: 'https://data.example/good.json' });
    const t = document.getElementById('to'); t.value = 'Jeddah'; t.dispatchEvent(new Event('change')); await new Promise(z => setTimeout(z, 600));
    return { ok, min: DATA.lanes.Jeddah.min40, buy: document.getElementById('q-buy').value, asof: DATA.dataAsof }; });
  assert.deepEqual(r, { ok: true, min: 700, buy: '700', asof: '2026-11-28' });
  await pg.close();
});

test('quick price: one line is read into Egyptian port, destination, containers and customer', async () => {
  const r = await run(() => { const P = window.__rules.tdParse;
    return [P('Sokhna Jeddah 2x40 Gulf Home Retail'), P('3x20 Damietta to Jeddah Nile Valley Foods'), P('Alexandria Valencia 1x40RF'),
            P('Free time extension for Q-1004 booking'), P('Q2')]; });
  assert.deepEqual([r[0].egy, r[0].dest, r[0].qty, r[0].eq, r[0].cust], ['Sokhna', 'Jeddah', 2, "40' HC", 'Gulf Home Retail']);
  assert.deepEqual([r[1].egy, r[1].dest, r[1].qty, r[1].eq, r[1].cust], ['Damietta', 'Jeddah', 3, "20' DC", 'Nile Valley Foods']);
  assert.equal(r[2].eq, "40' RF");
  assert.ok(r[3].err || !r[3].egyFound);          // not a lane: no "Price it"
  assert.equal(r[4].q, 'Q2'); assert.ok(r[4].dest);
});

test('today: every item has a tag, a title and one action', async () => {
  const I = await run(() => window.__rules.tdItems().map(x => ({ tag: x.tag, title: x.title, act: x.act, go: typeof x.go })));
  assert.ok(I.length > 0);
  assert.ok(I.every(x => x.tag && x.title && x.act && x.go === 'function'));
});

test('quick price: a foreign port before the Egyptian one is an import, not priced as export', async () => {
  const r = await run(() => window.__rules.tdParse('Back-to-back rate Jebel Ali to Sokhna 2x20'));
  assert.equal(r.imp, true); assert.equal(r.dest, 'Jebel Ali'); assert.equal(r.egy, 'Sokhna');
});

test('assistant: the most urgent item comes first, with its reasons', async () => {
  const r = await run(() => { const now = Date.now(), A = window.__rules.asNext([
      { tag: 'OFR', title: 'offers', sub: '' },
      { tag: 'NEW', title: 'new key account request', sub: '', due: now + 20 * 6e4, key: true },
      { tag: 'LATE', title: 'late case', sub: '', due: now - 30 * 6e4 },
      { tag: 'GAP', title: 'no rate', sub: '' }]);
    return A.map(x => [x.title, x.why.join(' / ')]); });
  assert.deepEqual(r.map(x => x[0]), ['late case', 'new key account request', 'no rate', 'offers']);
  assert.match(r[0][1], /30 min over the SLA/); assert.match(r[1][1], /Key account/);
});

test('working time: segments are stored per day and add up by state', async () => {
  const r = await run(() => { const R = window.__rules, k = 'wtLog_v1', keep = localStorage.getItem(k); localStorage.removeItem(k);
    const t0 = new Date(2026, 10, 25, 9, 0).getTime(), m = 6e4;
    R.wtSeg(t0, t0 + 30 * m, 'active'); R.wtSeg(t0 + 30 * m, t0 + 40 * m, 'away'); R.wtSeg(t0 + 40 * m, t0 + 100 * m, 'off'); R.wtSeg(t0 + 100 * m, t0 + 130 * m, 'active');
    const D = R.wtDay('2026-11-25'); if (keep) localStorage.setItem(k, keep); else localStorage.removeItem(k);
    return [D.active / m, D.away / m, D.off / m, D.segs.length]; });
  assert.deepEqual(r, [60, 10, 60, 4]);
});

test('today tools: Auto-RFQ drafts one email per carrier on the lane, never a suspended one', async () => {
  const r = await run(() => { const R = window.__rules; return { jed: R.rfqPlan('Jeddah', "40' HC"), jea: R.rfqPlan('Jebel Ali').map(x => x.car) }; });
  assert.ok(r.jed.length >= 2);
  assert.ok(r.jed.every(x => x.href.startsWith('mailto:') && /Jeddah/.test(decodeURIComponent(x.href))));
  assert.ok(!r.jea.includes('Demo Suspended Line'));
});

test('today tools: morning brief and end of day are plain text with the key lines', async () => {
  const r = await run(() => ({ b: window.__rules.briefText(), e: window.__rules.eodText() }));
  assert.match(r.b, /Pricing morning brief/); assert.match(r.b, /Open cases: \d+/); assert.match(r.b, /First things to do:\n1\. \[/);
  assert.match(r.e, /End of day/); assert.match(r.e, /Left for tomorrow/);
});

test('today tools: hand over moves only my open cases and writes it in each case log', async () => {
  const r = await run(() => { const L = window.__rules.csLoad().cases, mine = L.filter(c => !c.sub && c.who === 'me').map(c => c.id), others = L.filter(c => c.who !== 'me').map(c => [c.id, c.who]);
    const n = window.__rules.handOver('nour', 'Waiting for Aurora');
    const moved = L.filter(c => mine.includes(c.id)), last = moved[0] && moved[0].log[moved[0].log.length - 1][1];
    return { n, mine: mine.length, allNour: moved.every(c => c.who === 'nour'), othersSame: others.every(([id, w]) => L.find(c => c.id === id).who === w), last }; });
  assert.equal(r.n, r.mine); assert.ok(r.n > 0); assert.ok(r.allNour); assert.ok(r.othersSame);
  assert.match(r.last, /Handed over by .* to Nour Adel: Waiting for Aurora/);
});

test('task cycle: a request moves Received → Assigned → Answered → Quote to customer → Won/Lost', async () => {
  const r = await run(() => { const R = window.__rules, t = Date.now() - 36e5;
    const c = { subj: 'Rate request 2x40 Sokhna to Jeddah', recv: t };
    const s0 = R.cyStage(c); c.who = 'me'; const s1 = R.cyStage(c); c.sub = Date.now(); const s2 = R.cyStage(c);
    const keep = window.__rules.QT.items; window.__rules.QT.items = [{ pod: 'Jeddah', created: new Date().toISOString(), toCust: true, status: 'pending' }];
    const s3 = R.cyStage(c); window.__rules.QT.items[0].status = 'won'; const s4 = R.cyStage(c);
    const other = R.cyStage({ subj: 'Free time extension for Q-1004 booking', recv: t, who: 'me', sub: Date.now() });
    window.__rules.QT.items = keep;
    return [s0, s1, s2, s3, s4].map(x => [x.i, x.closed]).concat([[other.i, other.closed]]); });
  assert.deepEqual(r, [[0, false], [1, false], [2, false], [3, false], [4, true], [2, true]]);
});

test('team: per-person numbers add up to the cases, and the leaving choice goes to the history', async () => {
  const r = await run(() => { const R = window.__rules, S = R.teamStats(), L = R.csLoad().cases;
    const sum = Object.values(S.people).reduce((a, x) => ({ open: a.open + x.open, ans: a.ans + x.answered }), { open: 0, ans: 0 });
    R.histEod('home', 'Waiting for Aurora');
    const H = JSON.parse(localStorage.getItem('dayHist_v1')), d = Object.keys(H).sort().pop();
    return { open: sum.open + S.unassigned, ans: sum.ans, casesOpen: L.filter(c => !c.sub).length, casesAns: L.filter(c => c.sub && c.who).length,
             eod: H[d].eod.me.choice, note: H[d].eod.me.note, snap: !!H[d].people, alert: R.teamAlert(S, H[d].eod.me) }; });
  assert.equal(r.open, r.casesOpen); assert.equal(r.ans, r.casesAns);
  assert.equal(r.eod, 'home'); assert.equal(r.note, 'Waiting for Aurora'); assert.ok(r.snap);
  assert.match(r.alert, /Will finish from home \(Waiting for Aurora\)/);
});
