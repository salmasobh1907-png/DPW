# Builds the DEMO Rate Bank Export / Import Excel files from the tool's dummy data file.
# Same sheet and column layout as the team Rate Bank. No real rates, carriers or customers.
# Usage: python3 make_dummy_ratebank.py demo_data.json <output folder>
import json, datetime, os, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
d=json.load(open(sys.argv[1], encoding='utf-8'))
OUT=sys.argv[2]
os.makedirs(OUT,exist_ok=True)
NAVY=PatternFill('solid',fgColor='0B2E4F'); WH=Font(color='FFFFFF',bold=True); NOTE=Font(italic=True,color='9A5600')
MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
def dt(s):
    try: return datetime.datetime.strptime(s,'%Y-%m-%d')
    except Exception: return None
def sheet(wb,title,head,rows,widths=None,first=False):
    ws=wb.active if first else wb.create_sheet()
    ws.title=title
    ws.append(head)
    for c in ws[1]: c.fill=NAVY; c.font=WH; c.alignment=Alignment(vertical='center',wrap_text=True)
    for r in rows: ws.append(r)
    ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
    for i,h in enumerate(head,1):
        ws.column_dimensions[get_column_letter(i)].width=(widths or {}).get(h,max(10,min(34,len(str(h))+4)))
    for row in ws.iter_rows(min_row=2):
        for c in row:
            if isinstance(c.value,datetime.datetime): c.number_format='DD-MMM-YY'
    return ws
def banner(ws,text):
    ws.insert_rows(1); ws['A1']=text; ws['A1'].font=NOTE; ws.freeze_panes='A3'
    ws.auto_filter.ref=None
# ---------- Export ----------
EXP=["Rate ID","Contract","Month","Carrier","POL","POD","Transshipment Port","20 Rate","40 Rate","20RF","40RF","Currency","20 THC","40 THC","Currency","Free Time","Validity","Approx TT","Contract Type","Comment"]
rows=[]
for i,r in enumerate(d['rates']+d['reefers']):
    v=dt(r.get('valid'))
    rows.append(["R-%d"%(1001+i),"",MON[v.month-1] if v else "",r['car'],r['pol'],r['pod'],r.get('ts') or "",r.get('r20'),r.get('r40'),r.get('rf20'),r.get('rf40'),r.get('cur') or 'USD',r.get('thc20'),r.get('thc40'),(r.get('thccur') or 'USD') if (r.get('thc20') or r.get('thc40')) else "",r.get('ft') or "",v,r.get('tt'),"Standard",r.get('cmt') or "Demo rate (dummy)"])
wb=Workbook()
ws=sheet(wb,"Rate Data Base",EXP,rows,{"Carrier":18,"POL":16,"POD":18,"Comment":40,"Free Time":16},first=True)
ST={'won':'WON','pending':'PEN','open':'PEN'}
REF=["Quotation #","Subject","Client Name","POL","POD","20ft","40hc","Status","Recieved","Quoted","PIC","Pricing PIC","Comment"]
rr=[]
for x in d['requests']:
    rr.append([x['q'],x['s'],x['c'],x['eg'],x['port'],x['n20'] or None,x['n40'] or None,ST.get(x['st'],'PEN') if x['st']!='open' else '',dt(x['rec']),dt(x['quo']) if x.get('quo') else None,x['sales'],x.get('pr') or 'Pricing team',x.get('cmt') or 'Demo request (dummy)'])
sheet(wb,"Reference Sheet",REF,rr,{"Subject":60,"Client Name":26,"POD":18})
BK=["Month","Carrier","Volume","Equipment","TEU","Consignee","Shipper","Source (sales)","Owner"]
sheet(wb,"Bookings",BK,[[b['m'],b['car'],b['vol'],b['eq'],b['teu'],b['cg'],b['sh'],b['src'],b['own']] for b in d['bookings']],{"Consignee":26,"Shipper":26})
CT=["Carrier","Pricing email","Sales email"]
sheet(wb,"Contacts",CT,[[k]+list(v)[:2] for k,v in d['contacts'].items()],{"Carrier":18,"Pricing email":32,"Sales email":32})
for w in wb.worksheets: banner(w,"DEMO · dummy data only · same layout as the team Rate Bank Export · no real carriers, rates or customers")
fe=os.path.join(OUT,'Demo Rate Bank Export (dummy data).xlsx'); wb.save(fe)
# ---------- Import ----------
IMP=["Rate ID","Contract","Month","Carrier","POL","POD","20 Rate","40 Rate","20RF","40RF","Currency","Free Time","Validity","Contract Type","Comment"]
ir=[]
for i,r in enumerate(d['imports']):
    v=dt(r.get('valid'))
    ir.append(["I-%d"%(1001+i),"",MON[v.month-1] if v else "",r['car'],r['pol'],r['pod'],r.get('r20'),r.get('r40'),r.get('rf20'),r.get('rf40'),r.get('cur') or 'USD',r.get('ft') or "",v,"Standard",r.get('cmt') or "Demo import rate (dummy)"])
wb2=Workbook()
sheet(wb2,"Import Rate Dashboard",IMP,ir,{"Carrier":18,"POL":16,"POD":16,"Comment":36},first=True)
for w in wb2.worksheets: banner(w,"DEMO · dummy data only · same layout as the team Rate Bank Import · no real carriers, rates or customers")
fi=os.path.join(OUT,'Demo Rate Bank Import (dummy data).xlsx'); wb2.save(fi)
print(fe,len(rows),len(rr)); print(fi,len(ir))
