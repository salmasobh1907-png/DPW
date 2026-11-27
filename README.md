# DP World Platform – pricing tool prototype (dummy data): IT handover pack

Business area: Ocean Freight Pricing, DP World Egypt · Contact: Salma Ismail (Pricing) · Date: 24 Nov 2026

**This pack holds dummy data only.** Every carrier, customer, rate, trucking price, person and email in it is invented.
It holds no passwords, keys, tokens or personal data. It is safe to open, test and read. Share inside DP World only.

- Prototype online (dummy data): https://claude.ai/artifact/5k5VfRvCKzeCJdgmtSMyH6
- What IT needs to give, task by task (IT Needs Map): https://claude.ai/artifact/FTE1xbhb5gxes5oMrKAWtQ
- Plain-words overview of the prototype: https://claude.ai/artifact/AcHuKWDAGR9TgNSBSFpe36

Contents: 1 Pack contents · 2 What the tool does · 3 Architecture · 4 Screens and data mapping · 5 Data model ·
6 Business rules · 7 Integrations: prototype vs production · 8 Security and privacy · 9 What we ask from IT ·
10 Hosting options · 11 How to test · 12 Scripts · 13 Known limits

## 1. Pack contents

| Folder / file | What it is |
| --- | --- |
| `app/DP_World_Platform_DEMO.html` | The whole prototype: one HTML page (HTML + CSS + plain JavaScript). No server code. Open in Chrome or Edge. |
| `data/Demo Rate Bank Export (dummy data).xlsx` | Dummy Rate Bank in the team layout. Sheets: Rate Data Base, Reference Sheet, Bookings, Contacts. |
| `data/Demo Rate Bank Import (dummy data).xlsx` | Dummy import rates. Sheet: Import Rate Dashboard. |
| `data/DPW Pricing Rate Bank (dummy).xlsx` | **The tool's own rate source** (recommended). One table for all rates with drop-downs, live status, Rate IDs, suspensions and margin rules. Sheets: Start here, Rates, Lists, Suspensions, Margin Rules, Lane Summary, Contacts. See 5.4. |
| `data/demo_data.json` | The starting data of the page (the `const DATA = ...` line), as a readable file. |
| `scripts/` | Python 3 scripts (need `openpyxl`): Excel → data file → page, and back. |
| `TAB_MAP.csv` | One row per screen: data source → what it shows → what it feeds → where it is saved → production source. Opens in Excel. |

## 2. What the tool does

One pricing desk for export and import requests:

1. A carrier offer or a customer request arrives by email.
2. Every email becomes a case with an owner and a response-time target (SLA).
3. Pricing opens the lane: route on a map, every carrier rate, lowest standard rate.
4. The tool adds profit (buy + profit = sell) and runs checks before sending.
5. The offer goes to the sales person; sales send the quote to the customer.
6. Sales record won or lost and feedback; managers see KPIs and reports.

Two views: **Pricing** (sees buy rates and profit) and **Sales** (sell rates only).

## 3. Architecture

```
 Prototype (today)                                   Production (proposal for IT)
 ─────────────────                                   ────────────────────────────
 Dummy Rate Bank Excel ─► scripts ─► page data        Rate Bank on SharePoint (read only) or NPM ─► scheduled job (service account) ─► API
 Test mailbox (dummy emails) ─► mail connector        M365 shared mailboxes (pricing@ …) ─► Microsoft Graph (read only, named boxes)
 Prototype host storage (small shared store)          DP World database with audit log (SharePoint Lists / Azure SQL)
 Prototype host "who is viewing"                      Entra ID single sign-on + security groups (Pricing, Sales, Leads, Network)
 One HTML page in the browser                         Same screens, hosted inside DP World; buy rates served only to Pricing
```

The page runs no AI model. All logic is plain JavaScript in the page. External libraries load from cdnjs with fixed
versions: pdf.js 3.11.174 (read PDF offers), SheetJS 0.18.5 (Excel), jsPDF 2.5.1 + autotable 3.8.2 (PDF). Fonts: Google Fonts.

## 4. Screens and data mapping (source → screen → effect)

Full table, one row per sub-screen: `TAB_MAP.csv`. Summary:

| Screen | Takes data from | Shows / does | Feeds |
| --- | --- | --- | --- |
| Inbox | Test mailbox (or sample emails inside the page) | Carrier offers and customer requests; "Price it"; "Send offer to sales" | Rates & offer, Offers & quotes, Carrier offers |
| Shared inbox cases (Cases, Team KPIs, Mailboxes & SLA) | Sample emails + routing rules + mailbox list in the page | Case per email, owner, SLA clock in working hours (Sun–Thu, Cairo), reassign with log, work distribution (customer → owner), KPIs by consignee / sales / network request | Overview, manager KPIs |
| Rates & offer | Rate data + offers added from email + route map data | Map, all carrier rates on the lane, lowest standard 40', buy + profit = sell, checks, offer email and PDF | Offers & quotes, decline log |
| Offers & feedback | Shared store: quotes, feedback | Offers, quotes, won / lost, hit ratio, sales feedback and replies | Overview, Carrier volumes |
| Rate Bank (Rate Data Base, Carrier offers, Ask carriers, Pricing log, Rate check) | Dummy Rate Bank + files dropped on the page (Excel, PDF, .msg, .eml) | Rate sheet, offer → rows, monthly rate request emails, log of pricing asks, row checks | Rates & offer |
| Trucking rates | Dummy trucking tables + rates added in the tool | Pickup in Egypt (EXW) and cross-border trucks | EXW part of the offer |
| Overview (Overview, Customer requests, Market alerts, Carrier volumes) | All screens above; Reference Sheet and Bookings | Today at a glance, requests by lane, alerts, volumes | Management view |
| Alliance loops | Reference list in the page | Liner services calling Egypt | Route choice |
| Help & settings | Text + shared store (config, edits) | Help; source file; fix a rate or request; suspend a carrier on a lane | Rates & offer, Customer requests |

## 5. Data model

### 5.1 Page data (`const DATA`, also `data/demo_data.json`)

| Key | Content | Built from |
| --- | --- | --- |
| `rates` | Export dry rates: `car, pol, pod, r20, r40, cur, valid, tt, ts, thc20, thc40, thccur, ft, cmt`, optional `type` (contract type) | Rate Data Base |
| `reefers` | Same, with `rf20, rf40` | Rate Data Base (reefer rows) |
| `imports` | Import rates: `car, pol, pod, r20, r40, cur, valid, ft, cmt` | Import Rate Dashboard |
| `requests` | Customer requests: `q` (number), `s` subject, `c` customer, `eg` Egypt port, `port` foreign port, `n20, n40, teu, st` (open / pending / won), `rec, quo` dates, `sales, pr, cmt` | Reference Sheet |
| `bookings` | `m` month, `car, vol, eq, teu, cg` consignee, `sh` shipper, `src, own` | Bookings |
| `contacts` | Carrier → [pricing email, sales email] (all `.example`) | Contacts |
| `lanes` | Summary per destination: rate count, valid count, lowest 40', cheapest carrier, carriers, months, requests, won, TEU, transit days | Calculated by `ratebank_to_data.py` |
| `egypt, ports, nodes, edges, attach, choke, alts, services` | Map: ports with lat/lon, sea network, chokepoints (Suez, Bab el-Mandeb …), alternative ports, liner services | Reference data (kept as is) |
| `health` | Row checks on the Rate Data Base | Calculated |
| `qhist` | DUMMY closed quotes for the Margin advisor: `dir, pol, pod, eq, buy, sell, car, status, reason, created` | `make_dummy_quote_history.py` (production: the team's logged quotes) |
| `susp` | Suspended carriers: `car, pod` (empty = all lanes), `since, until, why, by` | Pricing Rate Bank → Suspensions |
| `mrules` | Fixed margin rules: `name, dir, cargo, pods[], m20, m40` | Pricing Rate Bank → Margin Rules |

With the Pricing Rate Bank, each rate row also carries `id` (Rate ID, `EX-00001` / `IM-00001`), `term` (Sokhna terminal), `src`, `ref` (email subject or file), and for special rows `type`, `cust`, `sailing`. A logged quote keeps `rateId`, so every quote points to the rate row it used.
| `asof` | Date of the data | Script |

### 5.2 Shared store collections (what users save)

| Collection | Saved when | Main fields |
| --- | --- | --- |
| `quotes` | Pricing sends an offer; sales send a quote; won / lost | `dir, pol, pod, customer, eq, qty, buy, sell, car, valid, status, reason, booking, seller, pricedBy, toCust, followUp, no, reqId, created` |
| `extraRates` | A carrier offer is added from email or file | `car, pol, pod, r20, r40, rf20, rf40, cur, valid, tt, ts, thc20, thc40, thccur, ft, ct, cmt` |
| `feedback` | Sales report what the customer said | `dir, pol, pod, type, price, eq, customer, text, status, reply, created` |
| `declines` | A carrier says it cannot serve a lane | `car, pods, reason, date, subject, by` |
| `plog` | Pricing asks a carrier or colleague for something | `type, q, cust, lane, who, src, asked, answered, note` |
| `truckRates` | A trucking rate is added | `from, port, vendor, r20, r40, cur, valid, by, created` |
| `edits` | A rate or request is fixed in the tool, or a carrier suspended | `kind (rate / req / susp), act, key, orig, set, why, until, by, created` |
| `config` | Source file settings | `export_path, import_path, status` |
| `gwWatch`, `gwGri`, `gwMkt` | Market alerts: disruptions, rate-increase notices, market index values | `area, level, note, impact, src, date` / `car, lane, kind, amt, eff, src` / `date, idx, lane, val, unit, src` |

### 5.4 DPW Pricing Rate Bank (the tool's own source)

Built for the tool, not a copy of the team Rate Bank. Dummy data only.

| Sheet | What it holds | What the tool does with it |
| --- | --- | --- |
| Rates | One row per rate: Rate ID, Direction, Cargo, Contract Type, Customer, Carrier, POL, POL Terminal, POD, Via, 20' / 40' / 20' RF / 40' RF, THC, Free Time, Valid From / To, Spot Sailing, Transit Days, Source, Source Ref, Added By / On, Comment. Grey columns calculate: effective validity, Status (Live / Expiring / Expired), Suspended, Counts for lowest, Rank on lane | All rate screens; lowest rate; checks; offers |
| Lists | Drop-down values: carriers, ports, terminals, contract types, currencies, sources | Keeps names identical, so lanes match |
| Suspensions | Carrier, POD (empty = all), From, Until, Reason, Set by | Suspended lines never show as an option and are stopped before sending |
| Margin Rules | Fixed margins by direction, cargo and destination list (China USD 25 / 50) | Margin suggestion |
| Lane Summary | Lowest standard 40' per destination, carrier, POL, counts | Check in Excel; the tool calculates the same |
| Contacts | Carrier pricing and sales emails | Rate request emails |

Load it: `python3 scripts/pricing_rate_bank_to_data.py "data/DPW Pricing Rate Bank (dummy).xlsx" data/demo_data.json`, then `inject_data.py`. The script reads only Rates, Suspensions, Margin Rules and Contacts, never writes to the workbook, and lists every row problem (duplicate Rate ID, 40' below 20', spot without sailing, Sokhna without terminal, dates, currency). Rebuild the dummy workbook: `scripts/build_pricing_rate_bank.py`. In production the same columns can be a SharePoint List or a database table; the screens do not change.

### 5.6 Data layer (swap the main source without changing screens)

All screens read one object, `DATA`. The data layer loads it from the main source, checks it against the contract
(`docs/DATA_CONTRACT.md`), fills the lane summary when missing (`buildLanes`, same rule as the converter) and swaps it in.
Sources: the data file inside the page (default) · a JSON data file from a link (made by a scheduled job from the Rate Bank
on SharePoint) · NPM (`npmMap`, assumed field names). IT sets the default in `DPW_CONFIG`; a pricing lead can switch on
Data sources → Main source. Bad data is refused and the page keeps its own file.

### 5.5 Data sources screen (Help & settings → Data sources)

One list of every place rates come from, in priority order: 1 Pricing Rate Bank (built in), 2 carrier emails (Carrier offers), then sources added on the screen:

| Type | How it updates | Notes |
| --- | --- | --- |
| Online link (CSV, JSON or Excel) | By itself every 15 min / hour / 6 h / day while the tool is open, or on "Refresh" | Direct download links only (SharePoint `?download=1`, internal API, carrier tariff file). Production: scheduled job on a service account |
| Excel / CSV file | When Pricing uploads a new version | Any sheet, any column order; sheets named like credential or password are never opened |
| WhatsApp chat (.txt from "Export chat") | When Pricing uploads a new export | Rate lines become rates marked `wa` (offer check warns "confirm by email"); GRI, surcharge, suspension, blank sailing, delay messages listed as announcements. Production option: WhatsApp Business Platform on a DP World number |

Column names read (any order): Carrier/Line, POL/Port of Loading, POD/Destination, 20', 40' (HC), 20' RF, 40' RF, Currency, Valid From, Valid To/Validity, Contract Type, Customer, Transit days, Via, Free Time, POL Terminal, Spot Sailing, Rate ID, Direction, Comment.
Merge rule: the same carrier + POL + POD + contract type + validity month in two sources → the higher source is used and the other is listed as a conflict; exact duplicates are skipped.

### 5.3 Browser-only storage (per user)

Shared inbox cases and their settings (`csState_v1`, `csSet_v1` incl. mailboxes added in the tool, `csMy_v1`), data sources (`dsSources_v1`, `dsRows_v1`), theme, last screen, view (pricing / sales).
In production the cases must move to the database (see section 9).

## 6. Business rules built in

1. "Lowest 40'" uses standard dry rates only. Rows with a Contract Type (special, spot, reefer, DG, named customer, volume) are left out.
2. A rate with no validity date is valid to the end of its month.
3. Profit on ocean freight only. THC, B/L, telex and local charges pass at cost.
4. Profit: China dry export ports fixed USD 25 per 20' and USD 50 per 40'. Other lanes: suggested from the gap to the next carrier and the market level; pricing can edit it. When no carrier on the lane is dearer, the tool reuses the newest margin quoted on the same lane (same direction, size and cargo) and says so; with no past quote the margin box stays empty and the offer is stopped until pricing types a margin. No flat default.
4b. **Margin advisor** (Rates & offer, Pricing only, never Sales): suggests a margin, an accepted range, a confidence level and an estimated win chance, with each input and its source shown. Plain statistics, no AI:
   (1) next dearer standard carrier on the lane: keep the sell under its cost; (2) market level: latest Market alerts index for the lane, else an estimate (average carrier rate + 6 %); (3) won / lost history of the same direction and size, on this lane when it has 6 or more decided quotes, else all lanes: win rate per margin band (smoothed toward the overall rate), best band = highest margin × win chance among bands with a win; only quotes won or lost on price count; (4) customer target prices from sales feedback. The lowest ceiling wins. China dry export stays fixed by policy. With no data it gives no number. Demo history is dummy (`qhist`, `scripts/make_dummy_quote_history.py`).
5. Offer vs quote: an offer goes to sales; it becomes a quote (and counts in hit ratio) only when sales mark it sent to the customer.
6. Checks before sending: stop on expired rate, suspended line, zero profit, offer valid after the carrier's validity. Warn when a rate ends within 3 days or a cheaper line exists.
7. Suspended carriers can be set per lane, with an end date, in Help & settings.
8. Sokhna: each Sokhna rate shows its terminal; DP World terminal rates show first; a warning appears when the picked rate loads at another terminal. In production the terminal should come from a Rate Bank column.
9. SLA per mailbox in working hours (Sun–Thu, Cairo). The clock stops at the first reply. Values are placeholders to agree with management.
10. Spot rates only when the carrier says spot; valid for that sailing only.
11. Sales never see buy rates, profit or the market band.

## 7. Integrations: prototype vs production

The prototype runs as one page on a prototyping platform that gives the page a few small services through
`window.claude.use(...)`. Each one has a DP World replacement:

| Call in the code | Prototype | Production |
| --- | --- | --- |
| `use("db")` | Small shared store (collections in 5.2) | DP World database with audit log, behind an API |
| `use("user")` | Name and id of the viewer | Entra ID single sign-on; roles from security groups |
| `use("mcp")` → mail tools `search_threads`, `get_thread`, `send_message` | Reads a **test mailbox with dummy emails**; sends the offer to a second test mailbox after a click | Microsoft Graph on M365 shared mailboxes: read only, limited to named boxes; reply "Send As" pricing@; drafts only, a person presses Send |
| `use("downloads")` | Saves Excel / CSV / PDF | Normal browser download |
| `use("permissions")` | User allows the mail connection | Not needed (access given centrally) |

Test mailbox addresses are set in two constants (`IBX_PRICING`, `IBX_SALES`), shown as placeholders in this pack.
If these services are missing, the page still opens, shows the sample emails and saves in the browser. So IT can test it offline.

## 8. Security and privacy

- Dummy data only. No real rates, customers, contracts, staff data or mailboxes in the pack.
- No passwords, keys or tokens in the code or data.
- The tool only reads the Rate Bank. It never writes to it.
- No automatic email: every send needs a person's click.
- The page runs no AI model and sends no data to an AI service at run time.
- In production: buy rates must stay on the server and reach Pricing users only; role switch in the page is not protection.
- "My shift" (active / away time inside the tool) must stay OFF until HR and Legal approve (Egypt Personal Data Protection Law 151 of 2020).

## 9. What we ask from IT (details in the IT Needs Map)

1. Host the tool inside DP World, behind DP World login (Entra ID).
2. Roles from Entra ID security groups (Pricing, Sales, Leads, Network), not from the email domain.
3. A database for team data (quotes, cases, feedback, logs) with an audit log.
4. Read-only access to the pricing shared mailboxes and the Rate Bank files, limited to named items (Exchange RBAC for Applications, Graph Sites.Selected).
5. Shared mailboxes: "Send As" for the team and a copy of sent mail saved in the shared box, so the SLA clock can stop.
6. Emails sent to one person directly: an Outlook rule that copies pricing requests to pricing@ (no reading of personal mailboxes).
7. Scheduled jobs (Rate Bank refresh, mail listener) on a company service account.
8. Security review before any real data; HR and Legal decision on "My shift".
9. Later: rates from NPM (Network Pricing Manager), bookings to CARGOES, a market index feed.

## 10. Hosting options (for IT to choose)

| Option | Fits when |
| --- | --- |
| SharePoint page + SharePoint Lists + Power Automate | Fast start, low code, team-size data |
| Power Apps (Power Platform) + Dataverse | IT prefers low code with stronger roles |
| Azure Static Web App + Azure Functions + Azure SQL | Full control, scale, buy rates kept server side |

## 11. How to test (about 10 minutes)

1. Open `app/DP_World_Platform_DEMO.html` in Chrome or Edge (or the online link).
2. Inbox → "Use offline copy" → open a request → **Price it**.
3. Rates & offer: check the route, the rate cards, buy / profit / sell, the checks, then the offer email.
4. Switch to **Sales** at the top: buy rates and profit disappear.
5. Shared inbox cases: reassign a case, open Team KPIs, change an SLA in Mailboxes & SLA.
6. Rate Bank → Carrier offers: drop an Excel or PDF offer, see the rows it finds.
7. Run the scripts in section 12 and reload the page.

Tested on 24 Nov 2026: all 9 menu screens open with no errors; the scripts give back the same 164 rates, 3 reefer
rates, 24 import rates, 125 requests and 36 bookings.

### Automated rule tests

`tests/rules.test.js` checks the business rules in the page (needs Node 18+ and Playwright with Chromium; runs offline):

```
node --test tests/rules.test.js
```

It covers: standard-only rows for "lowest" and margin gaps (rule 1), no validity date = end of month (rule 2),
China dry export margin USD 25 / 50 and gap-based margin elsewhere (rule 4), and the lane "lowest 40'" in `data/demo_data.json`.
The page exposes `window.__rules` (read-only helpers) for these tests.

## 12. Scripts (Python 3 + openpyxl, no network)

```
cd scripts
# Excel → data file (reads only the named sheets, never writes to the Excel files)
python3 ratebank_to_data.py "../data/Demo Rate Bank Export (dummy data).xlsx" "../data/Demo Rate Bank Import (dummy data).xlsx" ../data/demo_data.json
# data file → page (replaces only the const DATA line)
python3 inject_data.py ../app/DP_World_Platform_DEMO.html ../data/demo_data.json
# page → data file, and data file → dummy Excel
python3 extract_data.py ../app/DP_World_Platform_DEMO.html ../data/demo_data.json
python3 make_dummy_ratebank.py ../data/demo_data.json ../data
```

## 13. Known limits of the prototype

- One HTML page; roles are a switch, not real security.
- Shared inbox cases live in each browser, not shared.
- Sample emails and dummy data only; no connection to DP World systems.
- Map distances and transit days are estimates for planning, not carrier schedules.
