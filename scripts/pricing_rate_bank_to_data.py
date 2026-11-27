"""Load the DPW Pricing Rate Bank (the tool's own rate source, DUMMY DATA) into the tool's data file.

Usage:
  python3 pricing_rate_bank_to_data.py "<DPW Pricing Rate Bank.xlsx>" demo_data.json [YYYY-MM-DD]
  then: python3 inject_data.py ../app/DP_World_Platform_DEMO.html demo_data.json

Reads only these sheets: Rates, Suspensions, Margin Rules, Contacts. Never writes to the workbook.
Writes into demo_data.json: rates, reefers, imports, contacts, susp, mrules, lanes (lowest rate
per destination), health (row checks) and asof. Requests, bookings and map data stay as they are.

Rules (same as the tool):
  * Lowest = Export + Dry + Contract Type "Standard" + not expired + not suspended.
  * No "Valid To" = valid to the end of the month of "Valid From" (or of "Added On").
  * Spot rates need "Spot Sailing" and a "Valid To" (that sailing only).
Needs: Python 3 + openpyxl. No network.
"""
import sys, json, datetime, calendar, collections
import openpyxl

SRC, OUT = sys.argv[1], sys.argv[2]
TODAY = datetime.date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else datetime.date.today()
T = TODAY.isoformat()
MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
CRED = ('credential', 'password', 'login')

wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)

def table(name):
    ws = wb[name]; it = ws.iter_rows(values_only=True); head = [str(h or '').strip() for h in next(it)]
    for n, r in enumerate(it, 2):
        if any(v not in (None, '') for v in r): yield n, dict(zip(head, r))

def iso(v):
    if isinstance(v, datetime.datetime): return v.date().isoformat()
    if isinstance(v, datetime.date): return v.isoformat()
    try: return datetime.date.fromisoformat(str(v).strip()[:10]).isoformat()
    except Exception: return ''
def num(v):
    try: return None if v in (None, '') else float(v)
    except (TypeError, ValueError): return None
def s(v): return '' if v is None else str(v).strip()
def eom(d): d = datetime.date.fromisoformat(d); return d.replace(day=calendar.monthrange(d.year, d.month)[1]).isoformat()

# ---- suspensions and margin rules ----
susp = [dict(car=s(r.get('Carrier')), pod=s(r.get('POD (empty = all)')), since=iso(r.get('From')),
             until=iso(r.get('Until (empty = no end)')), why=s(r.get('Reason')), by=s(r.get('Set by')))
        for _, r in table('Suspensions') if s(r.get('Carrier'))]
def suspended(car, pod):
    return any(x['car'].lower() == car.lower() and (not x['pod'] or x['pod'].lower() == pod.lower())
               and (not x['since'] or x['since'] <= T) and (not x['until'] or x['until'] >= T) for x in susp)
mrules = [dict(name=s(r.get('Rule name')), dir='imp' if s(r.get('Direction')).lower() == 'import' else 'exp',
               cargo='rf' if s(r.get('Cargo')).lower() == 'reefer' else 'dry',
               pods=[p.strip() for p in s(r.get('POD contains (separate with ;)')).split(';') if p.strip()],
               m20=num(r.get("Margin 20' (USD)")), m40=num(r.get("Margin 40' (USD)")))
          for _, r in table('Margin Rules') if s(r.get('Rule name')) and s(r.get('Direction'))]
contacts = {s(r['Carrier']): [s(r.get('Pricing email')), s(r.get('Sales email'))] for _, r in table('Contacts') if s(r.get('Carrier'))}

# ---- rates + row checks ----
rates, reefers, imports, issues, ids = [], [], [], [], collections.Counter()
fill = collections.defaultdict(lambda: dict(n=0, tt=0, thc=0, ft=0, ts=0))
def issue(sev, k, n, rec, msg): issues.append(dict(sev=sev, k=k, row=n, car=rec.get('car'), pol=rec.get('pol'), pod=rec.get('pod'),
                                                   r20=rec.get('r20'), r40=rec.get('r40'), valid=rec.get('valid', ''), msg=msg))
rows = list(table('Rates'))
for n, r in rows: ids[s(r.get('Rate ID'))] += 1
for n, r in rows:
    car = s(r.get('Carrier'))
    if not car: continue
    rid, dirn, cargo, ctype = s(r.get('Rate ID')), s(r.get('Direction')), s(r.get('Cargo')) or 'Dry', s(r.get('Contract Type')) or 'Standard'
    vf, vt, added = iso(r.get('Valid From')), iso(r.get('Valid To')), iso(r.get('Added On'))
    valid = vt or (eom(vf) if vf else eom(added) if added else '')
    term = s(r.get('POL Terminal'))
    rec = dict(id=rid or 'ROW-%d' % n, car=car, pol=s(r.get('POL')), pod=s(r.get('POD')),
               r20=num(r.get("20'")), r40=num(r.get("40'")), rf20=num(r.get("20' RF")), rf40=num(r.get("40' RF")),
               cur=s(r.get('Currency')) or 'USD', valid=valid, ft=s(r.get('Free Time')), cmt=s(r.get('Comment')),
               src=s(r.get('Source')), ref=s(r.get('Source Ref (email subject or file)')))
    if ctype.lower() != 'standard': rec['type'] = ctype
    if s(r.get('Customer (named rates)')): rec['cust'] = s(r.get('Customer (named rates)'))
    if s(r.get('Spot Sailing (vessel / voyage)')): rec['sailing'] = s(r.get('Spot Sailing (vessel / voyage)'))
    if rec['pol'] == 'Sokhna' and term: rec['term'] = 'DP World' if 'dp world' in term.lower() else 'Other'
    # checks (shown on the tool's "Rate check" screen)
    if not rid: issue('fix', 'id', n, rec, 'No Rate ID: give the row the next free number')
    elif ids[rid] > 1: issue('fix', 'dup', n, rec, 'Rate ID %s is used on more than one row' % rid)
    if dirn not in ('Export', 'Import'): issue('fix', 'dir', n, rec, 'Direction must be Export or Import')
    if not rec['pol'] or not rec['pod']: issue('fix', 'port', n, rec, 'POL or POD is empty')
    if not any(rec[k] is not None for k in ('r20', 'r40', 'rf20', 'rf40')): issue('fix', 'norate', n, rec, 'No rate in any container column')
    if rec['r20'] and rec['r40'] and rec['r40'] < rec['r20']: issue('fix', 'r40lt20', n, rec, "40' rate is lower than 20' rate: check the columns")
    if vf and vt and vt < vf: issue('fix', 'dates', n, rec, 'Valid To is before Valid From')
    if ctype.lower() == 'spot' and (not vt or 'sailing' not in rec): issue('fix', 'spot', n, rec, 'Spot rate needs "Spot Sailing" and its own "Valid To" (that sailing only)')
    if ctype.lower() == 'standard' and 'spot' in rec['cmt'].lower(): issue('fix', 'hint', n, rec, 'Contract Type is Standard but the comment says "spot": set Contract Type, or it counts as the lowest')
    if rec['pol'] == 'Sokhna' and dirn == 'Export' and not term: issue('fix', 'term', n, rec, 'Sokhna rate without POL Terminal (DP World Sokhna or RSCT)')
    if valid and valid > (TODAY + datetime.timedelta(days=120)).isoformat(): issue('check', 'far', n, rec, 'Validity %s is more than 4 months away: typo?' % valid)
    if rec['cur'] not in ('USD',): issue('check', 'cur', n, rec, 'Currency is %s, not USD' % rec['cur'])
    if dirn == 'Import':
        imports.append({k: rec[k] for k in rec if k not in ('rf20', 'rf40') or rec[k] is not None}); continue
    rec.update(ts=s(r.get('Via')), tt=int(num(r.get('Transit Days'))) if num(r.get('Transit Days')) else None,
               thc20=num(r.get("THC 20'")), thc40=num(r.get("THC 40'")), thccur=s(r.get('THC Currency')) or 'USD')
    F = fill[car]; F['n'] += 1; F['tt'] += rec['tt'] is not None; F['thc'] += rec['thc40'] is not None; F['ft'] += bool(rec['ft']); F['ts'] += bool(rec['ts'])
    (reefers if cargo == 'Reefer' else rates).append(rec)

# ---- lane summary (lowest standard 40' per destination) ----
D = json.load(open(OUT, encoding='utf-8'))
lanes, by_pod, req_pod = D.get('lanes', {}), collections.defaultdict(list), collections.defaultdict(list)
for r in rates: by_pod[r['pod']].append(r)
for x in D.get('requests', []): req_pod[x['port']].append(x)
for pod in set(lanes) | set(by_pod):
    L, R = dict(lanes.get(pod, {})), by_pod.get(pod, [])
    std = [r for r in R if not r.get('type') and r.get('r40') and not suspended(r['car'], pod)]
    live = [r for r in std if r['valid'] >= T]
    best, anyb = min(live, key=lambda r: r['r40'], default=None), min(std, key=lambda r: r['r40'], default=None)
    Q = req_pod.get(pod, [])
    L.update(rates=len(R), valid=len(live), min40=best and best['r40'], min40any=anyb and anyb['r40'],
             cheap=best and '%s ex %s (%s)' % (best['car'], best['pol'], MON[int(best['valid'][5:7]) - 1]),
             carriers=list(dict.fromkeys(r['car'] for r in R)),
             months=sorted({MON[int(r['valid'][5:7]) - 1] for r in R if r['valid']}, key=MON.index),
             req=len(Q), won=sum(1 for x in Q if x['st'] == 'won'), teu=sum(x['teu'] for x in Q))
    if R and not L.get('pol'): L['pol'] = R[0]['pol']
    L.setdefault('hist', {}); L.setdefault('tt', {}); lanes[pod] = L

D.update(rates=rates, reefers=reefers, imports=imports, contacts=contacts or D.get('contacts', {}), susp=susp, mrules=mrules, lanes=lanes,
         health=dict(rows=len(rates) + len(reefers), more=0, checked=T, fill=dict(fill), issues=issues),
         rbsrc='DPW Pricing Rate Bank', asof=TODAY.strftime('%-d %b %Y'))
json.dump(D, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('rates %d, reefers %d, imports %d, suspensions %d, margin rules %d, lanes %d -> %s'
      % (len(rates), len(reefers), len(imports), len(susp), len(mrules), len(lanes), OUT))
fix = [i for i in issues if i['sev'] == 'fix']
print('row checks: %d to fix, %d to check' % (len(fix), len(issues) - len(fix)))
for i in issues[:15]: print('  row %s %s %s→%s: %s' % (i['row'], i['car'], i['pol'], i['pod'], i['msg']))
