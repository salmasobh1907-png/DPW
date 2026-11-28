"""Add DUMMY last-month rates to the tool's data file, so the page can show how each rate moved.

Usage:
  python3 make_dummy_history.py demo_data.json

What it writes: the key "hist" inside demo_data.json:
  "hist": {"month": "2026-10", "rows": {"<carrier>|<POL>|<POD>": [rate20, rate40]}}
A rate with no row in "rows" is shown as "new" in the page.

The numbers are invented from the current dummy rates with a fixed rule (same input, same output).
They are not real history. In production the scheduled job keeps a copy of the Rate Bank rows at
each month end (read only) and fills this key from that copy.
Needs: Python 3. No network.
"""
import sys, json, hashlib, datetime

OUT = sys.argv[1]
D = json.load(open(OUT, encoding='utf-8'))


def pick(key, n):
    """A stable number 0..n-1 from a text key."""
    return int(hashlib.sha256(key.encode('utf-8')).hexdigest()[:8], 16) % n


def as_date(s):
    for f in ('%Y-%m-%d', '%d %b %Y', '%d %B %Y'):
        try:
            return datetime.datetime.strptime(s, f).date()
        except (ValueError, TypeError):
            pass
    return datetime.date.today()


first = as_date(D.get('asof')).replace(day=1)
month = (first - datetime.timedelta(days=1)).strftime('%Y-%m')

rows = {}
for r in D.get('rates', []):
    if r.get('type'):                        # standard dry rates only, as for "lowest rate"
        continue
    key = '|'.join([r['car'], r['pol'], r['pod']])
    if pick('new' + key, 10) == 0:           # about 1 rate in 10 is new this month
        continue
    step = [-3, -2, -1, -1, 0, 0, 0, 1, 1, 2, 3][pick('move' + key, 11)]   # in steps of 25 USD per 20'
    prev = []
    for k, unit in (('r20', 25), ('r40', 50)):
        v = r.get(k)
        prev.append(None if v is None else max(unit, v - step * unit))
    rows[key] = prev

D['hist'] = {'month': month, 'rows': rows}
json.dump(D, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('history month', month, '· rows', len(rows), 'of', len([r for r in D.get('rates', []) if not r.get('type')]))
