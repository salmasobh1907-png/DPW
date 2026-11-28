"""Adds DUMMY quote history (won / lost with margins) to demo_data.json as DATA.qhist,
so the Margin advisor has something to study. Invented numbers, fixed seed (same result every run).
In production this history comes from the quotes the team logs in the tool.
Usage: python3 make_dummy_quote_history.py ../data/demo_data.json"""
import json, sys, random, math, datetime
P = sys.argv[1]; D = json.load(open(P, encoding='utf-8')); rnd = random.Random(1907)
REASONS_PRICE = ['Price too high', 'Booked with another forwarder']
REASONS_OTHER = ['Transit time too long', 'Shipment cancelled or postponed', 'No reply from customer']
lanes = {}
for r in D['rates']:
    if r.get('type') or not r.get('r40'): continue
    lanes.setdefault(r['pod'], []).append(r)
pods = sorted(lanes, key=lambda p: -len(lanes[p]))[:24]
out, start = [], datetime.date(2026, 5, 1)
for pod in pods:
    best = min(lanes[pod], key=lambda r: r['r40'])
    sweet = rnd.choice([60, 80, 100, 120, 150])            # the margin this lane's customers accept (hidden "truth")
    for _ in range(rnd.randint(4, 14)):
        is20 = rnd.random() < 0.3
        buy = (best['r20'] or best['r40'] * 0.7) if is20 else best['r40']
        m = max(20, int(rnd.gauss(sweet * (0.6 if is20 else 1), 45) / 5) * 5)
        p_win = 1 / (1 + math.exp((m - sweet * (0.6 if is20 else 1)) / 25))   # higher margin -> lower chance to win
        won = rnd.random() < p_win * 0.85
        reason = '' if won else (rnd.choice(REASONS_PRICE) if rnd.random() < 0.75 else rnd.choice(REASONS_OTHER))
        day = start + datetime.timedelta(days=rnd.randint(0, 200))
        out.append(dict(dir='exp', pol=best['pol'], pod=pod, eq="20' DC" if is20 else "40' HC", buy=buy, sell=buy + m, car=best['car'],
                        status='won' if won else 'lost', reason=reason, created=day.isoformat(), dummy=True))
D['qhist'] = sorted(out, key=lambda x: x['created'])
json.dump(D, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('qhist: %d dummy quotes on %d lanes, %d won' % (len(out), len(pods), sum(x['status'] == 'won' for x in out)))
