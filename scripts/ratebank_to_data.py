"""Read the two DEMO Rate Bank Excel files and refresh the tool's data file (demo_data.json).

Usage:
  python3 ratebank_to_data.py "<Demo Rate Bank Export.xlsx>" "<Demo Rate Bank Import.xlsx>" demo_data.json [YYYY-MM-DD]

What it reads (only these sheets, nothing else):
  Export file: "Rate Data Base" (rates), "Reference Sheet" (customer requests),
               "Bookings" (carrier volumes), "Contacts" (carrier emails)
  Import file: "Import Rate Dashboard" (import rates)
What it writes: the keys rates, reefers, imports, requests, bookings, contacts, lanes (summary per
destination) and asof inside demo_data.json. The map keys (ports, nodes, edges, choke, alts,
services) are reference data and are kept as they are.

Pricing rules applied (same as the tool):
  * Standard rates only: a row whose Contract Type is not empty or "Standard" is left out of
    "lowest rate" (it is still kept as a row). Reefer rows = 20RF/40RF filled and no dry rate.
  * A rate with no validity date is valid to the end of its month.
Needs: Python 3 + openpyxl. No network, no passwords, read-only on the Excel files.
"""
import sys, json, datetime, calendar, collections
import openpyxl

EXP, IMP, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
TODAY = datetime.date.fromisoformat(sys.argv[4]) if len(sys.argv) > 4 else datetime.date.today()
MON = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']

def table(wb, name):
    """Rows of a sheet as dicts. The first row may be a 'DEMO' banner; the header is the row
    that holds the first known column name."""
    ws = wb[name]
    rows = list(ws.iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows) if r and r[0] in ('Rate ID', 'Quotation #', 'Month', 'Carrier'))
    head = [str(h or '').strip() for h in rows[hi]]
    out = []
    for r in rows[hi + 1:]:
        if not r or all(v in (None, '') for v in r):
            continue
        d = {}
        for h, v in zip(head, r):
            if h and h not in d:          # the Export sheet has two "Currency" columns: keep the first
                d[h] = v
            elif h:
                d[h + ' 2'] = v
        out.append(d)
    return out

def iso(v):
    if isinstance(v, datetime.datetime): return v.date().isoformat()
    if isinstance(v, datetime.date): return v.isoformat()
    return ''

def num(v):
    try: return None if v in (None, '') else float(v)
    except (TypeError, ValueError): return None

def valid_to(row):
    """Validity date, or the last day of the rate's month when no date is given."""
    v = iso(row.get('Validity'))
    if v: return v
    m = str(row.get('Month') or '').strip().upper()[:3]
    if m in MON:
        mo = MON.index(m) + 1
        return datetime.date(TODAY.year, mo, calendar.monthrange(TODAY.year, mo)[1]).isoformat()
    return ''

D = json.load(open(OUT, encoding='utf-8'))
wbE = openpyxl.load_workbook(EXP, read_only=True, data_only=True)
wbI = openpyxl.load_workbook(IMP, read_only=True, data_only=True)

rates, reefers = [], []
for r in table(wbE, 'Rate Data Base'):
    rec = dict(pol=r.get('POL') or '', pod=r.get('POD') or '', car=r.get('Carrier') or '',
               cur=r.get('Currency') or 'USD', valid=valid_to(r), tt=r.get('Approx TT'),
               ts=r.get('Transshipment Port') or '', thc20=num(r.get('20 THC')), thc40=num(r.get('40 THC')),
               thccur=r.get('Currency 2') or 'USD', ft=str(r.get('Free Time') or ''), cmt=r.get('Comment') or '')
    ctype = str(r.get('Contract Type') or '').strip()
    if ctype and ctype.lower() != 'standard':
        rec['type'] = ctype                      # kept, but never counted as "lowest standard"
    if num(r.get('20 Rate')) is None and num(r.get('40 Rate')) is None and (num(r.get('20RF')) or num(r.get('40RF'))):
        rec.update(rf20=num(r.get('20RF')), rf40=num(r.get('40RF'))); reefers.append(rec)
    else:
        rec.update(r20=num(r.get('20 Rate')), r40=num(r.get('40 Rate'))); rates.append(rec)

imports = [dict(pol=r.get('POL') or '', pod=r.get('POD') or '', car=r.get('Carrier') or '',
                r20=num(r.get('20 Rate')), r40=num(r.get('40 Rate')), valid=valid_to(r),
                cur=r.get('Currency') or 'USD', note='', ft=str(r.get('Free Time') or ''), cmt=r.get('Comment') or '')
           for r in table(wbI, 'Import Rate Dashboard')]

old_req = {x['q']: x for x in D.get('requests', [])}
ST = {'WON': 'won', 'PEN': 'pending', '': 'open'}
requests = []
for r in table(wbE, 'Reference Sheet'):
    q = str(r.get('Quotation #') or '').strip()
    n20, n40 = int(num(r.get('20ft')) or 0), int(num(r.get('40hc')) or 0)
    x = dict(old_req.get(q, {}))                 # keeps helper fields (dir, egr, far) when known
    x.update(q=q, s=r.get('Subject') or '', c=r.get('Client Name') or '', eg=r.get('POL') or '',
             port=r.get('POD') or '', n20=n20, n40=n40, teu=n20 + 2 * n40,
             st=ST.get(str(r.get('Status') or '').strip().upper(), 'pending'),
             rec=iso(r.get('Recieved')), quo=iso(r.get('Quoted')), sales=r.get('PIC') or '',
             pr=r.get('Pricing PIC') or '', cmt=r.get('Comment') or '')
    x.setdefault('dir', 'exp'); x.setdefault('egr', x['eg']); x.setdefault('far', x['port'])
    requests.append(x)

bookings = [dict(m=r.get('Month'), car=r.get('Carrier'), vol=r.get('Volume'), eq=r.get('Equipment'), teu=r.get('TEU'),
                 cg=r.get('Consignee'), sh=r.get('Shipper'), src=r.get('Source (sales)'), own=r.get('Owner'))
            for r in table(wbE, 'Bookings')]
contacts = {r['Carrier']: [r.get('Pricing email') or '', r.get('Sales email') or ''] for r in table(wbE, 'Contacts') if r.get('Carrier')}

# lane summary per destination (what the "Rates & offer" page and the Overview read first)
lanes = D.get('lanes', {})
by_pod = collections.defaultdict(list)
for r in rates: by_pod[r['pod']].append(r)
req_pod = collections.defaultdict(list)
for x in requests: req_pod[x['port']].append(x)
today = TODAY.isoformat()
for pod in set(lanes) | set(by_pod) | set(req_pod):
    L = dict(lanes.get(pod, {}))
    R = by_pod.get(pod, [])
    std = [r for r in R if not r.get('type') and r.get('r40')]
    live = [r for r in std if r['valid'] >= today]
    best = min(live, key=lambda r: r['r40'], default=None)
    anyb = min(std, key=lambda r: r['r40'], default=None)
    Q = req_pod.get(pod, [])
    L.update(rates=len(R), valid=len(live), min40=best and best['r40'], min40any=anyb and anyb['r40'],
             cheap=best and '%s ex %s (%s)' % (best['car'], best['pol'], MON[int(best['valid'][5:7]) - 1]),
             carriers=list(dict.fromkeys(r['car'] for r in R)),
             months=sorted({MON[int(r['valid'][5:7]) - 1] for r in R if r['valid']}, key=MON.index),
             req=len(Q), won=sum(1 for x in Q if x['st'] == 'won'), teu=sum(x['teu'] for x in Q))
    if R and not L.get('pol'): L['pol'] = R[0]['pol']
    L.setdefault('hist', {}); L.setdefault('tt', {})
    lanes[pod] = L

D.update(rates=rates, reefers=reefers, imports=imports, requests=requests, bookings=bookings,
         contacts=contacts, lanes=lanes, asof=TODAY.strftime('%-d %b %Y'))
json.dump(D, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('rates %d, reefers %d, imports %d, requests %d, bookings %d, lanes %d -> %s'
      % (len(rates), len(reefers), len(imports), len(requests), len(bookings), len(lanes), OUT))
