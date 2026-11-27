# Builds the "DPW Pricing Rate Bank" workbook: the tool's own rate source (DUMMY DATA).
# It is NOT a copy of the team Rate Bank. One table for all rates (export + import, dry + reefer),
# with drop-down lists, live status formulas, suspensions and margin rules that the tool reads.
# Usage: python3 build_pricing_rate_bank.py ../data/demo_data.json "../data/DPW Pricing Rate Bank (dummy).xlsx"
import json, sys, datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule

SRC, OUT = sys.argv[1], sys.argv[2]
D = json.load(open(SRC, encoding='utf-8'))
TEAL = PatternFill('solid', fgColor='0B5D63'); GREY = PatternFill('solid', fgColor='5B6670')
WH = Font(color='FFFFFF', bold=True); B = Font(bold=True); H1 = Font(bold=True, size=16, color='0B5D63')
CALC = PatternFill('solid', fgColor='EEF2F3'); THIN = Border(bottom=Side(style='thin', color='DDE2E5'))
EXTRA = 400                       # blank rows that already carry formulas, ready for new rates
TODAY = datetime.date(2026, 11, 19)
DPW_TERM = ('Nile Star', 'Gulf Bridge', 'Sahara Feeder', 'Red Sea Express')

def d(s):
    try: return datetime.datetime.strptime(s, '%Y-%m-%d')
    except Exception: return None

# ---------------- Rates ----------------
COLS = [  # (header, width, input?)  input columns are typed by people; the rest are formulas
 ('Rate ID', 12, 1), ('Direction', 10, 1), ('Cargo', 8, 1), ('Contract Type', 15, 1), ('Customer (named rates)', 18, 1),
 ('Carrier', 17, 1), ('POL', 15, 1), ('POL Terminal', 16, 1), ('POD', 17, 1), ('Via', 14, 1),
 ("20'", 8, 1), ("40'", 8, 1), ("20' RF", 8, 1), ("40' RF", 8, 1), ('Currency', 9, 1),
 ("THC 20'", 8, 1), ("THC 40'", 8, 1), ('THC Currency', 9, 1), ('Free Time', 14, 1),
 ('Valid From', 11, 1), ('Valid To', 11, 1), ('Spot Sailing (vessel / voyage)', 20, 1), ('Transit Days', 8, 1),
 ('Source', 13, 1), ('Source Ref (email subject or file)', 26, 1), ('Added By', 12, 1), ('Added On', 11, 1), ('Comment', 32, 1),
 ('Valid To (effective)', 12, 0), ('Status', 10, 0), ('Suspended', 10, 0), ('Counts for lowest', 10, 0), ("Rank on lane (40')", 10, 0), ('Lane key', 6, 0)]
C = {h: get_column_letter(i + 1) for i, (h, _, _) in enumerate(COLS)}

def row_formulas(n):
    f = lambda h: '%s%d' % (C[h], n)
    car, pod = f('Carrier'), f('POD')
    eff = '=IF(%s="","",IF(%s<>"",%s,IF(%s<>"",EOMONTH(%s,0),IF(%s<>"",EOMONTH(%s,0),""))))' % (
        car, f('Valid To'), f('Valid To'), f('Valid From'), f('Valid From'), f('Added On'), f('Added On'))
    st = '=IF(OR(%s="",%s=""),"",IF(%s<TODAY(),"Expired",IF(%s-TODAY()<=3,"Expiring","Live")))' % (car, f('Valid To (effective)'), f('Valid To (effective)'), f('Valid To (effective)'))
    S = 'Suspensions!$A$2:$A$200,%s,Suspensions!$B$2:$B$200,%s,Suspensions!$C$2:$C$200,"<="&TODAY()' % (car, '%s')
    sus = ('=IF(%s="","",IF(COUNTIFS(%s,Suspensions!$D$2:$D$200,">="&TODAY())+COUNTIFS(%s,Suspensions!$D$2:$D$200,"")'
           '+COUNTIFS(%s,Suspensions!$D$2:$D$200,">="&TODAY())+COUNTIFS(%s,Suspensions!$D$2:$D$200,"")>0,"Yes","No"))') % (
        car, S % pod, S % pod, S % '""', S % '""')
    low = '=IF(%s="","",IF(AND(%s="Export",%s="Dry",%s="Standard",%s<>"Expired",%s="No",ISNUMBER(%s)),"Yes","No"))' % (
        car, f('Direction'), f('Cargo'), f('Contract Type'), f('Status'), f('Suspended'), f("40'"))
    rk = '=IF(%s="Yes",COUNTIFS($%s:$%s,%s,$%s:$%s,"Yes",$%s:$%s,"<"&%s)+1,"")' % (
        f('Counts for lowest'), C['POD'], C['POD'], pod, C['Counts for lowest'], C['Counts for lowest'], C["40'"], C["40'"], f("40'"))
    key = '=IF(%s="","",%s&"|"&%s)' % (f("Rank on lane (40')"), pod, f("Rank on lane (40')"))
    return [eff, st, sus, low, rk, key]

def seed_rows():
    out, n = [], 1
    def add(r, direction, cargo, ctype='Standard', cust='', sailing='', src='Seed (dummy)', ref='Demo Rate Bank', by='Pricing (demo)'):
        nonlocal n
        v = d(r.get('valid') or ''); vf = v.replace(day=1) if v else None
        term = ('DP World Sokhna' if r['car'] in DPW_TERM else 'RSCT') if r['pol'] == 'Sokhna' else ''
        rid = '%s-%05d' % ('EX' if direction == 'Export' else 'IM', n); n += 1
        out.append([rid, direction, cargo, ctype, cust, r['car'], r['pol'], term, r['pod'], r.get('ts') or '',
                    r.get('r20'), r.get('r40'), r.get('rf20'), r.get('rf40'), r.get('cur') or 'USD',
                    r.get('thc20'), r.get('thc40'), r.get('thccur') or ('USD' if r.get('thc20') or r.get('thc40') else ''),
                    r.get('ft') or '', vf, v, sailing, r.get('tt'), src, ref, by, datetime.datetime(2026, 11, 19), r.get('cmt') or ''])
    for r in D['rates']: add(r, 'Export', 'Dry')
    for r in D['reefers']: add(r, 'Export', 'Reefer', 'Reefer')
    for r in D['imports']: add(r, 'Import', 'Dry')
    # showcase rows: how special cases look (all invented)
    add({'car': 'Aurora Lines', 'pol': 'Sokhna', 'pod': 'Jeddah', 'r20': 420, 'r40': 560, 'valid': '2026-11-28', 'tt': 4, 'cmt': 'Spot: this sailing only (dummy).'},
        'Export', 'Dry', 'Spot', sailing='DEMO STAR / 046E', src='Carrier email', ref='RE: Spot offer Jeddah wk48 (dummy)')
    add({'car': 'Delta Marine', 'pol': 'Alexandria', 'pod': 'Valencia', 'r20': 700, 'r40': 900, 'valid': '2026-12-31', 'tt': 9, 'cmt': 'Named customer rate (dummy).'},
        'Export', 'Dry', 'Named customer', cust='Horus Auto Parts', src='Carrier email', ref='Special rate for Horus (dummy)')
    add({'car': 'Demo Suspended Line', 'pol': 'Sokhna', 'pod': 'Jebel Ali', 'r20': 300, 'r40': 450, 'valid': '2026-12-31', 'tt': 6, 'cmt': 'Cheap but suspended to Jebel Ali (dummy).'},
        'Export', 'Dry', src='Carrier email', ref='Jebel Ali offer (dummy)')
    return out

wb = Workbook()
# ---------------- Start here ----------------
ws0 = wb.active; ws0.title = 'Start here'
lines = [('DPW Pricing Rate Bank (DUMMY DATA)', H1), ('The rate source of the pricing tool. Every rate, carrier and customer here is invented.', None), ('', None),
 ('How to use', B),
 ('1. Add a rate: type it on a new row of "Rates". White columns are yours; grey columns calculate by themselves.', None),
 ('2. Pick values from the drop-downs (Direction, Cargo, Contract Type, Carrier, ports, terminal, currency).', None),
 ('3. Contract Type "Standard" = a normal rate. Anything else (Spot, Special, Named customer, Volume, DG, Reefer) never counts as the lowest.', None),
 ('4. Leave "Valid To" empty when the carrier gives no date: the rate is valid to the end of its month.', None),
 ('5. A Spot rate needs "Spot Sailing" and its own "Valid To": it is valid for that sailing only.', None),
 ('6. Sokhna rates need "POL Terminal". DP World Sokhna rates come first in the tool; RSCT rates get a warning.', None),
 ('7. Stop a carrier on a lane in "Suspensions". Leave POD empty to stop it everywhere. Leave "Until" empty for no end date.', None),
 ('8. Fixed margins live in "Margin Rules". All other lanes get the margin from the gap to the next carrier.', None),
 ('9. "Lane Summary" shows the lowest standard 40\' per destination, live.', None),
 ('10. Load into the tool: python3 scripts/pricing_rate_bank_to_data.py (it also checks every row and lists problems).', None), ('', None),
 ('Rate ID', B), ('EX-00001 = export, IM-00001 = import. Never reuse or change an ID: offers and quotes point to it. New rows: next free number.', None), ('', None),
 ('Colours in "Rates"', B), ('Green rank = lowest standard rate on the lane · Amber status = ends within 3 days · Grey row = expired · Red = suspended', None), ('', None),
 ('Never store passwords, carrier portal logins or real customer data in this file.', Font(bold=True, color='9A3412'))]
for t, f in lines:
    ws0.append([t]);
    if f: ws0.cell(ws0.max_row, 1).font = f
ws0.column_dimensions['A'].width = 130

# ---------------- Rates ----------------
ws = wb.create_sheet('Rates')
ws.append([h for h, _, _ in COLS])
for i, (h, w, inp) in enumerate(COLS, 1):
    c = ws.cell(1, i); c.fill = TEAL if inp else GREY; c.font = WH; c.alignment = Alignment(wrap_text=True, vertical='center')
    ws.column_dimensions[get_column_letter(i)].width = w
ws.row_dimensions[1].height = 42
rows = seed_rows()
for k in range(len(rows) + EXTRA):
    n = k + 2
    vals = rows[k] if k < len(rows) else [None] * 28
    ws.append(list(vals) + row_formulas(n))
last = ws.max_row
for row in ws.iter_rows(min_row=2, max_row=last):
    for c in row:
        if c.column > 28: c.fill = CALC
        if c.column in (20, 21, 27, 29): c.number_format = 'DD-MMM-YY'
ws.column_dimensions[C['Lane key']].hidden = True
ws.freeze_panes = 'G2'; ws.auto_filter.ref = 'A1:%s%d' % (C["Rank on lane (40')"], last)
rng = 'A2:%s%d' % (C['Lane key'], last)
ws.conditional_formatting.add(rng, FormulaRule(formula=['$%s2="Expired"' % C['Status']], font=Font(color='9AA3AA')))
ws.conditional_formatting.add('%s2:%s%d' % (C['Status'], C['Status'], last), FormulaRule(formula=['$%s2="Expiring"' % C['Status']], fill=PatternFill('solid', fgColor='FCD9A8')))
ws.conditional_formatting.add('%s2:%s%d' % (C['Suspended'], C['Suspended'], last), FormulaRule(formula=['$%s2="Yes"' % C['Suspended']], fill=PatternFill('solid', fgColor='F7C1C1')))
ws.conditional_formatting.add('%s2:%s%d' % (C["Rank on lane (40')"], C["Rank on lane (40')"], last), FormulaRule(formula=['$%s2=1' % C["Rank on lane (40')"]], fill=PatternFill('solid', fgColor='BFE6CF')))

# ---------------- Lists ----------------
wl = wb.create_sheet('Lists')
carriers = sorted({r['car'] for r in D['rates'] + D['reefers'] + D['imports']} | {'Demo Suspended Line'})
egy = sorted(D['egypt'].keys()); foreign = sorted({r['pod'] for r in D['rates']} | {r['pol'] for r in D['imports']})
L = {'Direction': ['Export', 'Import'], 'Cargo': ['Dry', 'Reefer'],
     'Contract Type': ['Standard', 'Spot', 'Special', 'Named customer', 'Volume', 'DG', 'Reefer', 'Subject to shipper/consignee'],
     'Carrier': carriers, 'Port': egy + foreign, 'POL Terminal': ['DP World Sokhna', 'RSCT', ''], 'Currency': ['USD', 'EUR', 'EGP'],
     'Source': ['Carrier email', 'Carrier portal', 'Rate sheet file', 'Phone (confirmed by email)', 'Seed (dummy)']}
for j, (k, vals) in enumerate(L.items(), 1):
    wl.cell(1, j, k).font = WH; wl.cell(1, j).fill = TEAL; wl.column_dimensions[get_column_letter(j)].width = 22
    for i, v in enumerate(vals, 2): wl.cell(i, j, v)
def lst(k): j = list(L).index(k) + 1; col = get_column_letter(j); return "Lists!$%s$2:$%s$%d" % (col, col, len(L[k]) + 1)
for head, key in [('Direction', 'Direction'), ('Cargo', 'Cargo'), ('Contract Type', 'Contract Type'), ('Carrier', 'Carrier'), ('POL', 'Port'), ('POD', 'Port'),
                  ('POL Terminal', 'POL Terminal'), ('Currency', 'Currency'), ('THC Currency', 'Currency'), ('Source', 'Source')]:
    dv = DataValidation(type='list', formula1='=' + lst(key), allow_blank=True, showErrorMessage=True,
                        errorTitle='Pick from the list', error='Pick a value from the list. New carrier or port? Add it to the Lists sheet first.')
    ws.add_data_validation(dv); dv.add('%s2:%s%d' % (C[head], C[head], last))
num = DataValidation(type='decimal', operator='between', formula1='0', formula2='100000', allow_blank=True, showErrorMessage=True, error='Rate must be a number of 0 or more.')
ws.add_data_validation(num)
for h in ("20'", "40'", "20' RF", "40' RF", "THC 20'", "THC 40'"): num.add('%s2:%s%d' % (C[h], C[h], last))
dte = DataValidation(type='date', operator='greaterThan', formula1='DATE(2020,1,1)', allow_blank=True, showErrorMessage=True, error='Type a date, e.g. 30-Nov-26.')
ws.add_data_validation(dte)
for h in ('Valid From', 'Valid To', 'Added On'): dte.add('%s2:%s%d' % (C[h], C[h], last))

# ---------------- Suspensions ----------------
wsu = wb.create_sheet('Suspensions')
sh = ['Carrier', 'POD (empty = all)', 'From', 'Until (empty = no end)', 'Reason', 'Set by']
wsu.append(sh)
for i, c in enumerate(wsu[1], 1): c.fill = TEAL; c.font = WH; wsu.column_dimensions[get_column_letter(i)].width = [20, 18, 12, 16, 40, 14][i - 1]
wsu.append(['Demo Suspended Line', 'Jebel Ali', datetime.datetime(2026, 10, 1), None, 'Service problems on this lane (dummy)', 'Pricing lead'])
for r in range(2, 202):
    for col in 'CD': wsu['%s%d' % (col, r)].number_format = 'DD-MMM-YY'
dvc = DataValidation(type='list', formula1='=' + lst('Carrier'), allow_blank=True); wsu.add_data_validation(dvc); dvc.add('A2:A200')
dvp = DataValidation(type='list', formula1='=' + lst('Port'), allow_blank=True); wsu.add_data_validation(dvp); dvp.add('B2:B200')

# ---------------- Margin Rules ----------------
wm = wb.create_sheet('Margin Rules')
wm.append(['Rule name', 'Direction', 'Cargo', 'POD contains (separate with ;)', "Margin 20' (USD)", "Margin 40' (USD)", 'Note'])
for i, c in enumerate(wm[1], 1): c.fill = TEAL; c.font = WH; wm.column_dimensions[get_column_letter(i)].width = [24, 10, 8, 70, 12, 12, 40][i - 1]
china = ['Shanghai', 'Ningbo', 'Qingdao', 'Xiamen', 'Shekou', 'Yantian', 'Nansha', 'Dalian', 'Fuzhou', 'Tianjin', 'Xingang', 'Guangzhou', 'Shenzhen', 'Lianyungang', 'Taicang', 'Zhuhai', 'Shantou', 'Huangpu', 'Nanjing', 'Nantong', 'Qinzhou', 'Wuhan', 'Chongqing', 'Foshan', 'Jiangmen', 'Zhongshan', 'Sanshan', 'Wuhu']
wm.append(['Dry export to China', 'Export', 'Dry', '; '.join(china), 25, 50, 'Fixed margin. Profit on ocean freight only; THC and local charges at cost.'])
wm.append([]); wm.append(['All other lanes: no fixed margin. The tool sets it from the gap to the next carrier, or the last margin used on the lane.'])
wm.cell(wm.max_row, 1).font = Font(italic=True, color='5B6670')

# ---------------- Lane Summary ----------------
wsl = wb.create_sheet('Lane Summary')
wsl.append(['POD', "Lowest standard 40' (USD)", 'Carrier', 'POL', 'Live standard rates', 'Expiring in 3 days', 'Suspended rows'])
for i, c in enumerate(wsl[1], 1): c.fill = TEAL; c.font = WH; wsl.column_dimensions[get_column_letter(i)].width = [18, 14, 18, 16, 12, 12, 12][i - 1]
R = lambda h: 'Rates!$%s$2:$%s$%d' % (C[h], C[h], last)
for k, pod in enumerate(sorted({r['pod'] for r in D['rates']}), 2):
    wsl.append([pod,
        '=IF(COUNTIFS(%s,A%d,%s,"Yes")=0,"",_xlfn.MINIFS(%s,%s,A%d,%s,"Yes"))' % (R('POD'), k, R('Counts for lowest'), R("40'"), R('POD'), k, R('Counts for lowest')),
        '=IFERROR(INDEX(%s,MATCH(A%d&"|1",%s,0)),"")' % (R('Carrier'), k, R('Lane key')),
        '=IFERROR(INDEX(%s,MATCH(A%d&"|1",%s,0)),"")' % (R('POL'), k, R('Lane key')),
        '=COUNTIFS(%s,A%d,%s,"Yes")' % (R('POD'), k, R('Counts for lowest')),
        '=COUNTIFS(%s,A%d,%s,"Expiring")' % (R('POD'), k, R('Status')),
        '=COUNTIFS(%s,A%d,%s,"Yes")' % (R('POD'), k, R('Suspended'))])
wsl.freeze_panes = 'A2'

# ---------------- Contacts ----------------
wc = wb.create_sheet('Contacts')
wc.append(['Carrier', 'Pricing email', 'Sales email'])
for i, c in enumerate(wc[1], 1): c.fill = TEAL; c.font = WH; wc.column_dimensions[get_column_letter(i)].width = 32
for car, (pe, se) in sorted(D['contacts'].items()): wc.append([car, pe, se])

wb.save(OUT)
print('Saved', OUT, '·', len(rows), 'rates +', EXTRA, 'ready rows')
