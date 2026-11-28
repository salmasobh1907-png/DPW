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
| `data/demo_data.json` | The starting data of the page (the `const DATA = ...` line), as a readable file. |
| `scripts/` | Python 3 scripts (need `openpyxl`): Excel → data file → page, and back. |
| `TAB_MAP.csv` | One row per screen: data source → what it shows → what it feeds → where it is saved → production source. Opens in Excel. |
| `docs/DATA_SOURCES.csv` | Data Sources Register for the BTI meeting: one row per data source: who owns it, the cheapest way it reaches the tool, what we ask IT for, the cost, and the open question. Opens in Excel. |

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
| Inbox (Inbox, Team KPIs, Mailboxes & SLA) | Test mailbox (or sample emails inside the page) + sample cases + routing rules + mailbox list in the page | One list for every email: carrier offers and customer / sales / network requests. Each has one request number (Q-…), an owner and an SLA clock in working hours (Sun–Thu, Cairo). "Price it", "Read it into Carrier offers", reassign with log, work distribution (customer → owner), waiting-for-carriers list, KPIs by consignee / sales / network request. Sales see only their own requests and pricing's answers | Rates & offer, Offers & quotes, Carrier offers, Overview, manager KPIs |
| Rates & offer | Rate data + offers added from email + route map data | Three steps on one screen. 1 Lane and rates: map, all carrier rates on the lane, lowest standard 40', tick rates. 2 Profit and checks: buy + profit = sell for the container size of the request, terms, checks. 3 Offer email: email, PDF, send to sales. Sales see the same steps without buy and profit | Offers & quotes, decline log |
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
| `hist` | Last month's standard rates: `month`, `rows` = `carrier\|POL\|POD` → `[rate20, rate40]` | Dummy: `make_dummy_history.py`. Production: a read-only copy of the Rate Bank rows kept at each month end |
| `asof` | Date of the data | Script |

### 5.2 Shared store collections (what users save)

| Collection | Saved when | Main fields |
| --- | --- | --- |
| `quotes` | Pricing sends an offer; sales send a quote; won / lost | `dir, pol, pod, customer, eq, qty, buy, sell, car, valid, status, reason, compPrice, booking, seller, pricedBy, toCust, followUp, no, reqId, created` |
| `extraRates` | A carrier offer is added from email or file | `car, pol, pod, r20, r40, rf20, rf40, cur, valid, tt, ts, thc20, thc40, thccur, ft, ct, cmt` |
| `feedback` | Sales report what the customer said | `dir, pol, pod, type, price, eq, customer, text, status, reply, created` |
| `declines` | A carrier says it cannot serve a lane | `car, pods, reason, date, subject, by` |
| `plog` | Pricing asks a carrier or colleague for something | `type, q, cust, lane, who, src, asked, answered, note` |
| `truckRates` | A trucking rate is added | `from, port, vendor, r20, r40, cur, valid, by, created` |
| `edits` | A rate or request is fixed in the tool, or a carrier suspended | `kind (rate / req / susp), act, key, orig, set, why, until, by, created` |
| `config` | Source file settings | `export_path, import_path, status` |
| `gwWatch`, `gwGri`, `gwMkt` | Market alerts: disruptions, rate-increase notices, market index values | `area, level, note, impact, src, date` / `car, lane, kind, amt, eff, src` / `date, idx, lane, val, unit, src` |

### 5.3 Browser-only storage (per user)

Inbox cases and their settings (`csState_v2`, `csSet_v1`; `csMy_v1` only if "My shift" is ever switched on), which mailbox emails were answered or read (`ibxDone`, `ibxRead`), "My status" and leave plans (`csAvail_v1`), handovers and ops account owners (`hoState_v1`), theme, last screen, view (pricing / sales).
In production the cases must move to the database (see section 9).

## 6. Business rules built in

1. "Lowest 40'" uses standard dry rates only. Rows with a Contract Type (special, spot, reefer, DG, named customer, volume) are left out.
2. A rate with no validity date is valid to the end of its month.
3. Profit on ocean freight only. THC, B/L, telex and local charges pass at cost.
4. Profit: China dry export ports fixed USD 25 per 20' and USD 50 per 40'. Other lanes: suggested from the gap to the next carrier and the market level; pricing can edit it.
5. Offer vs quote: an offer goes to sales; it becomes a quote (and counts in hit ratio) only when sales mark it sent to the customer.
6. Checks before sending: stop on expired rate, suspended line, zero profit, offer valid after the carrier's validity. Warn when a rate ends within 3 days or a cheaper line exists.
7. Suspended carriers can be set per lane, with an end date, in Help & settings.
8. Sokhna: each Sokhna rate shows its terminal; DP World terminal rates show first; a warning appears when the picked rate loads at another terminal. In production the terminal should come from a Rate Bank column.
9. SLA per mailbox in working hours (Sun–Thu, Cairo). The clock stops at the first reply: "Send and submit" in the Inbox, "Send offer to sales" in Rates & offer, or "Read it into Carrier offers" for a carrier offer. Values are placeholders to agree with management.
12. One request number. Every email gets one number (Q-…) when it arrives, and the same number is used in the Inbox, the offer and the quotes log. Demo ranges: Q-1001… requests read from the mailbox, Q-2041… sample cases, Q-3001… carrier offers. In production one sequence gives the number when the mail connector saves the email.
13. My day. A card at the top of the Inbox, different for each viewer, built from plain rules on the tool's own data (no AI model). Pricing person: own requests over the SLA, next request due, requests with no owner, own open requests on a lane with no valid standard rate or whose lowest rate ends within 3 days, carriers that did not answer, new sales feedback, own status running longer than usual. Lead, in addition: team requests over the SLA, open requests owned by people who are not available, who is available now, leave in the next 7 days. Sales person: offers from pricing not yet sent to the customer, quotes ended with no result, follow-ups due, quotes ending soon, own requests still with pricing, answers to feedback, customers with no request for 60 days. The three most urgent lines show; the rest open under "more".
14. One search box in the top bar (shortcut: `/`). It finds requests by number, subject, sender or owner; offers and quotes by number, customer, lane, carrier or sales person; and lanes by port or carrier. Each viewer finds only what they may see: a sales person finds only their own requests and quotes, and lane results show the number of carriers, not the lowest buy rate.
15. No valid rate on a lane is never a dead end, and never a rate from memory. Rates & offer then shows: (1) the last known rates on that destination, marked "ended, reference only", with "Ask to renew"; (2) the nearest ports that do have valid rates, with the distance, to judge the level; (3) one rate request email to the carriers that serve the area, opened as a draft and added to "Waiting for carriers"; (4) "Log it as a request", which puts it in the Inbox with a number, an owner and an SLA clock. A sales user sees only the nearest ports (no buy rates) and "Ask pricing for this rate"; the open ask shows in their My day.
16. Rate history. In the Pricing view each standard buy rate shows how it moved since last month: ▲ and the amount (dearer, red), ▼ and the amount (cheaper, green), "= Oct" (no change) or "new". Sales never see it, because it is about buy rates. The last-month numbers in this pack are invented by a script.
17. Lost quotes. A reason is required. For "Price too high" the competitor price is also required, or a tick that the customer did not say it. The sales person report then shows how far our sell was above the competitor price on average.
18. Parts of a request. One email can ask for several things (FCL, LCL, EXW pickup, trucking, air). The tool finds the parts from words in the email; a person can add a part. Each part is answered on its own, or marked "cannot offer" with a reason. The request stays open and its SLA clock keeps running until every part is closed. An answer that covers only some parts says "Still to come: …" in the email, the list shows "Parts 1/3", and My day reminds the owner. An offer sent from Rates & offer closes the FCL part (and EXW pickup when the offer is EXW). LCL has no rates in this pack: the part can be tracked, but it is priced outside the tool.
19. Handover to ops (Offers & feedback › Handover to ops). A quote marked Won shows as "no handover yet". Pricing starts the handover; it is filled from the quote. Fields: Scope (OFR / Pickup / Clearance / G-set), Shipper, Cnee, Incoterms, BKG#, UCR#, Volume, POL, POD, Buying rate, Selling rate, Payment term, Vessel ETD, Carrier, Billing party, Pricing PIC, Control party, and ticks for the attached BC, SD and client thread. Rules: one handover per booking; a real booking number is required (no number = PEN, it is not sent); Buying = line net; Selling = the number the client accepted, never TBC, also for collect shipments; internal only, never to the client. It goes to the ops person who owns the account (table kept by the leads), and the email opens as a draft. Ops accept it or send it back with what is missing. A handed-over booking becomes a row in Bookings (Carrier volumes), and the request timeline gets a fifth step, "Handed to ops". Ops see buying and selling; sales cannot open the screen.
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
  In the page it is switched off by `const CS_SHIFT_ON=false`: no shift card, no Active / Away columns, no activity recorded or stored. Set it to `true` only after written approval.
- "My status" (Inbox) is different from "My shift": each person presses a button to say where they are (Available, Lunch break, Prayer, Break, Mission, Coaching, Training, Q meeting) and adds their annual leave plan. Nothing is measured from the mouse, keyboard or screen. A lead sees lunch, prayer and break as one word, "Break", because a prayer status can show a person's religion (sensitive personal data). A lead can start, end and correct the times of a Q meeting only when the meeting is with them; every change keeps who made it. Auto-assign skips people who are not Available; SLA clocks do not pause. Switch: `const CS_AVAIL_ON`. It is still staff data about working time, so real use needs a staff notice and HR agreement first.
- Rehearsal controls (offline copy, reset, test email, "Signed in as") sit in one **Demo tools** menu on the Inbox. They are not part of the real tool.

## 9. What we ask from IT (details in the IT Needs Map)

1. Host the tool inside DP World, behind DP World login (Entra ID).
2. Roles from Entra ID security groups (Pricing, Sales, Leads, Network, Ops), not from the email domain. Ops see buying and selling on the handover; sales do not.
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
2. Inbox → open request Q-1002 → **Price it** → step 1 shows the rates → **Next** to step 2 (profit and checks) → **Next** to step 3 → **Send offer to sales**. Back in the Inbox the request is under **Submitted** with the clock stopped. (The offline copy of the emails loads by itself; it is also under **Demo tools**.)
3. Rates & offer: step 1 the route and the rate cards; step 2 buy / profit / sell and the checks; step 3 the offer email. "Alternatives" and "Truck all the way" open with a click on their title.
4. Switch to **Sales** at the top: buy rates and profit disappear.
5. Inbox: reassign a request, open Team KPIs, change an SLA in Mailboxes & SLA.
6. Rate Bank → Carrier offers: drop an Excel or PDF offer, see the rows it finds.
7. Run the scripts in section 12 and reload the page.

Tested on 24 Nov 2026: all menu screens open with no errors; the scripts give back the same 164 rates, 3 reefer
rates, 24 import rates, 125 requests and 36 bookings.

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
# dummy last-month rates for the rate history arrows (run after ratebank_to_data.py, before inject_data.py)
python3 make_dummy_history.py ../data/demo_data.json
```

## 13. Known limits of the prototype

- Menu (pricing): Inbox, Rates & offer (with Alliance loops), Offers & feedback, Rate Bank (with Trucking rates), Overview, Help & settings. Sales: Inbox, Find a rate (with Alliance loops), My offers & feedback, Trucking rates, Help. The map shows only on Rates & offer, Alliance loops, Overview and Customer requests.
- One HTML page; roles are a switch, not real security.
- Inbox cases (owner, SLA clock, history) live in each browser, not shared.
- Sample emails and dummy data only; no connection to DP World systems.
- Map distances and transit days are estimates for planning, not carrier schedules.
