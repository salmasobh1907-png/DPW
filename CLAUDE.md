# CLAUDE.md: DP World Platform (pricing tool prototype, DUMMY DATA)

Owner: Salma Ismail (Sobh), Ocean Freight System & Documentation Executive, Freight Forwarding, DP World Egypt.
Manager: Asmaa. Director: Ossama ElLaban.

This folder is the pricing tool prototype ("DP World Platform"), with **invented data only**.
Read `README.md` (architecture, data model, rules) and `TAB_MAP.csv` (every screen: source → effect) before changing code.
The next step with IT is in `docs/IT_Needs_Map.html`.

## 1. How to talk to Salma

- Reply in **Egyptian Arabic** (Franco is fine), short and clear. Code, comments, app text, slides and documents for managers stay in **English**.
- Explain simply, as to a beginner, with a small worked example when there is a calculation.
- Distances in **km**, times in **days**. Never nautical miles or knots.
- Say where every number comes from: dummy Rate Bank, your own calculation, or an email offer.
- Before building or changing anything big, say in one line what you will do, then do it.
- Make a backup copy of a file before a big change (e.g. `app/backup/DEMO_before_<change>.html`).

## 2. Data and security rules (hard rules, never break)

- **Dummy data only in this folder.** Never add real rates, real customer names, real emails, real carrier contracts or real Rate Bank rows. If Salma pastes real data, warn her and ask to use dummy data instead.
- **Never read, write or touch Youssef Sakr's Rate Bank files** (Rate Bank Export.xlsx, Rate Bank Import.xlsx, Reference Sheet) or any copy of them. They are view-only for everyone and this tool must not write to them, not even "a small fix".
- **Never open the "Carrier Credentials" sheet.** Never read, copy, store or type passwords, keys or tokens. Salma logs in herself. The app already skips any sheet named like credential/password; keep that.
- Pages that show **buy rates** are shared **inside DP World only**, never "Anyone with the link".
- No AI / LLM inside the app. IT confirmed the tool must be **plain rules (keywords, formulas)**, no model calls.
- Do not send emails. "Send" buttons only open a draft (Outlook/Gmail compose) for a human to send.

## 3. Rate rules (the tool must apply these)

- **Lowest rate = standard dry rates only.** Skip any row whose Contract Type is filled (special, spot, reefer, DG, Alfalfa, named customer, volume, "subject to shipper/consignee").
- A rate **with no validity date is valid to the end of its month**.
- A **spot** rate (only if the carrier says "spot") is valid **for that sailing only**, not to month end.
- **Jebel Ali: Sea Glory, LATT and Cordelia are suspended.** Never show them as an option there until Salma says otherwise.
- **Sokhna has two terminals** (DP World's and another one). Rates must show the terminal; **DP World terminal rates come first**; flag a rate from the other terminal so sales do not quote it by mistake.
- Ocean rates are per container and exclude local charges. Truck rates are per truck (~25 t), subject to daily border passes.

### Profit (margin)

- Fixed margin **USD 25 per 20' and USD 50 per 40'** applies **only to China dry export ports**.
- All other lanes: no fixed number. Set the profit from the **gap to the other carriers' rates and to the market level** on that lane. Never use a flat guess.
- Profit goes on **ocean freight only**. THC, B/L, telex and local charges pass at cost.
- Always show **buy, profit added, sell** for every quoted rate.

Worked example (China lane, 40'): buy USD 1,800 + profit 50 = sell USD 1,850. THC stays at cost.

### Route time (Route Globe method)

- Sea days = km ÷ about 710 km per day.
- Door time = sea days + port time (max 7 days) + truck days (km ÷ 550 + 1 per border + ½).

## 4. Where the tool is going (IT context, Nov 2026)

- IT meeting 24 Nov 2026 was positive. IT wants **one web app**, hosted inside DP World, Entra ID sign-in, Pricing vs Sales roles (Sales never see buy rates).
- Future data source: the **Rate Bank on SharePoint (read only)** and later **NPM (Network Pricing Manager)**, DP World's global pricing platform. Design data loading so the source can be swapped (Excel → NPM) without changing screens.
- Mail: M365 shared mailboxes via Microsoft Graph, read only. Every rate/request must keep a reference number (IT asked how it is built: keep it documented).
- Next: meeting with the BTI team to collect data sources. Keep `README.md` and `TAB_MAP.csv` up to date when screens or data change, because IT builds from them.

## 5. Working on the code

- The app is one file: `app/DP_World_Platform_DEMO.html` (HTML + CSS + plain JavaScript, no build step). Open it in Chrome or Edge to test.
- All starting data is ONE line in the page: `const DATA = {...};`. To edit data: `python3 scripts/extract_data.py app/DP_World_Platform_DEMO.html data/demo_data.json`, edit the JSON, then `python3 scripts/inject_data.py app/DP_World_Platform_DEMO.html data/demo_data.json`.
- Dummy Rate Bank → page data: `scripts/ratebank_to_data.py` (needs `openpyxl`). New dummy Excel: `scripts/make_dummy_ratebank.py`.
- External libraries only from cdnjs with fixed versions (pdf.js 3.11.174, SheetJS 0.18.5, jsPDF 2.5.1 + autotable 3.8.2).
- After a change: open the page, click through the changed screen, check the browser console has no errors.
