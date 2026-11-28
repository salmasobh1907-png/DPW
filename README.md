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

Three views (switch "View as" at the top): **Pricing** (daily work, sees buy rates and profit), **Sales** (sell rates only, no Today, no Team dashboard) and **Director** (opens on the Team dashboard; menu: Team dashboard, Overview, Today, Offers & feedback, Rates & offer, Rate Bank, Apps hub; sees buy rates and margins). In production the view comes from Entra ID groups (Pricing, Sales, Leads, Director), not from a switch.

**New look**: a style layer on top of the classic design (DP World navy side menu, light background, blue actions, rounder cards, smooth tab change). On by default; the sun button at the top switches back to the classic look (`newLook_v1`). No screen logic changes.

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
| **Today** (Pricing opens here) | Shared inbox cases, quotes, requests, Rate Bank, carrier emails, WhatsApp, market alerts | One list "Needs you", sorted by urgency (LATE, DUE, NEW, F/U, GAP, EXP, OFR, WA, ALR), each with one action button; 4 KPIs; **Quick price**: one line ("Sokhna Jeddah 2x40 Gulf Home" or "Q12") gives carrier, buy, margin, sell, advisor margin and the send checks; `/` opens it from anywhere | Rates & offer, Cases, Offers, Ask carriers, Data sources |
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

### 5.7 Desk assistant ("Next up") and working time

- **Next up** (top of Today): every Needs-you item gets a score: type of work (LATE 90, DUE 60, market alert 50, no rate 45, new 40, ending rate 35, follow-up 30, carrier offers 20, WhatsApp 15) + SLA urgency (over the SLA +100, under 30 min +60, under 2 h +30) + key account +15 + assigned to you +10. The top item shows with its reasons. Start (runs its action and a timer), Done (logs the time), Snooze 30 min. Plain rules, no AI.
- **Working time**: the existing shift clock now keeps a log per day of Active / Away / Break / Off with a timeline and the last 7 days. Off = computer asleep, locked, shut down or the tool closed (a gap of more than 90 s). It measures the tool only (mouse and keys in the tool, tab open), not other programs. Shown to the person (Today) and to managers (Team KPIs, "Managers only"). In the demo each browser holds only its own log. **Before real use: HR and Legal approval, and every person told what is recorded.** For presence across the whole PC, Teams presence through Microsoft Graph (Presence.Read.All) is the existing option.

### 5.8 Today tools (plain rules; email = drafts only, a person presses Send)

| Tool | What it does |
| --- | --- |
| Auto-RFQ | From a GAP or EXP item, or "Ask carriers for this lane" under Quick price: lists the carriers that quoted the destination (suspended lines left out), marks who holds a valid standard rate, one email draft each (Contacts), and logs all requests in the Pricing log |
| Morning brief | Text for the team and the manager: open cases and SLA, open requests, hit ratio, the first 5 things to do, lanes without a rate, rates ending in 7 days, carrier announcements. Copy or open as a draft |
| Hand over | Moves my open cases to a colleague with a note written in each case log |
| Focus mode | Shows only Next up and Quick price; a new LATE case breaks through with a banner and the tab title |
| End of day | Tasks done with time, time in the tool, what is left for tomorrow. Copy or draft |

### 5.9 Task cycle, leaving alert, daily history, Team dashboard

- **Cycle** (Today → "My open requests: full cycle"): Received → Assigned → Answered → Quote to customer → Won / Lost, with the next step for each request. UNREAD = nobody took it; REPLY = waiting for your reply; OPEN = answered, not closed. A request with a lane closes only at Won / Lost; an answer that needs no quote closes at Answered. The quote is matched by destination and date (production: by request reference number).
- **Leaving alert**: a pop-up when the working day ends (Mailboxes & SLA hours) with urgent items open (late, due soon or unread), from End of day → "I am leaving now", and the browser's own warning when the tool is closed. The person picks: hand over, finish from home, or leave for tomorrow, with a note. The choice and the open numbers go to today's history.
- **Daily history** (`dayHist_v1`, 60 days): per person open, late, answered, average reply time; saved every 5 minutes and when the day changes.
- **Team dashboard** (Reports, managers only, hidden from others): team totals; each person's open, late, answered, average reply (clock time), oldest open, active and away time, end-of-day choice; the last 14 days done vs left; a daily alert text for the Director (copy or draft). Demo: activity time is dummy and each browser holds its own history; production: all from the database. HR and Legal approve before real use.

### 5.10 Apps hub (links only: no passwords, no AI)

One page with the apps the team uses: Outlook, calendar, Teams, the Gmail test box (prototype), SharePoint team site, Rate Bank on SharePoint (view only), Excel and PowerPoint, NPM, CARGOES, intranet, market index, vessel schedules. Internal links start empty and are typed by the team or set by IT (no invented addresses).
- **Mail drafts open in** Gmail (prototype test box), Outlook (DP World) or the default mail app: one setting used by every draft the tool prepares (`mailDraft`).
- **Team**: Email, Teams chat, Call (phone number = company SIM; opens the phone app or Teams on a PC, the SIM on a mobile; without a number a Teams call), Meeting (new Teams meeting).
- **Carriers**: Email plus links to each carrier's website, spot quote, schedules and tracking pages (shown in Auto-RFQ too). The person logs in; the tool stores no passwords.
- Settings are kept in the browser in the demo and can be copied to colleagues; IT sets them for everyone in production.
- Level 2 and 3 (reading mail, presence, calendar, Teams Phone, SharePoint, NPM, CARGOES, carrier APIs) are in `docs/IT_Data_Sources_Request.html`.

### 5.11 Sign-in, launch summary and Responsibilities

- **Sign-in**: the app opens on a sign-in screen. Production: "Sign in with Microsoft" (Entra ID), the view comes from the person's group. Demo: pick a dummy person (Pricing, Customs & trucking, Network, Documentation, Sales, Director). No passwords anywhere. Once signed in, the view comes from the person and the Pricing / Sales / Director switch is hidden; the round button with the initials switches user. Automated tests open the page with `?skipLogin=1`.
- **Launch summary**: after sign-in (and once per browser session) a short card for that person: Pricing (things that need Pricing, late, first item, daily responsibilities, rates ending this week), Director (team open / late / not taken, responsibilities nobody owns, one-person tasks), Sales (where to start). One button to start.
- **My responsibilities** (Pricing menu): each person's list of work by area (pricing, accounts, Rate Bank and records, bookings and handover, support to colleagues, reporting, customs and trucking, documentation, network, tools, tenders), how often, minutes each × times a week (own estimate), who it supports and who shares it. Daily tasks get a tick, per-request and per-booking work a count (`tkTasks_v1`, `tkLog_v1`). End of day includes the ticks.
- **Responsibilities: who does what** (Team dashboard, managers only): load per person in hours a week (shared tasks split), tasks supporting others, done today; task-by-task matrix; "one person" tasks (no back-up) and work **nobody owns** (none in the demo); key work only one person can do is flagged first (in the demo: tenders, one person, no back-up named).
- Demo content: the split of work is a dummy example; customer names are replaced by account types and colleagues by the demo people.

### 5.12 Tool owner (admin), tickets and feedback, change log, error log

- **Admin**: only the tool owner's sign-in (demo: "You") changes tool settings: Settings & sources, Data sources, Apps hub, Mailboxes & SLA, the Responsibilities list. Everyone else sees these screens read-only with "Ask for it" (opens a ticket); people still tick their own responsibilities. The admin keeps the Pricing / Sales / Director switch to see every view and counts as a manager. Production: an Entra ID group, enforced by the server.
- **Report / feedback** button on every screen, for everyone: Problem / bug, Request / change, Idea / feedback; title, details, urgency, send to the tool owner, IT support or both. Technical details are added (screen, time, version, data source, last 5 errors), never rates or customer data. Ticket numbers `T-0001`.
- **Support** screen: each person sees their tickets, status and answers and can add details. The admin sees all tickets, changes status (New, In progress, Fixed, Closed) and replies; the status changes are written in the ticket.
- **Alerts for the admin**: the bell and the launch summary count new tickets, urgent ones, setting changes made by others and errors since the admin last looked.
- **Change log**: who changed which setting and when. **Error log**: every script error with time, screen, person and view, kept even when nobody reports it (200 entries).
- Storage in the demo: `tickets_v1`, `audit_v1`, `errLog_v1`, `admSeen_v1` (this browser). Production: database, and a mail or Teams alert to the owner and IT.

### 5.13 Forward or reassign an email (Shared inbox cases → open a case)

Type a name → suggestions with department and email → pick the person; the department fills in and lists only its shared mailboxes; pick one; the **reason is required**. Forward opens a draft to that shared mailbox, subject "FW: … · Attn: name", body with Attn, reason, case number and the original email. The case log keeps who forwarded, to which mailbox, for whom and why. If the person is in the pricing shared inbox they also become the case owner (it counts in their KPIs); for another department the owner stays and the case shows the forward. Directory and mailboxes are dummy (`DIR_PEOPLE`, `DIR_MBX`); production: the DP World address book (Graph) and the real shared mailboxes.

### 5.14 Cycle time and capacity (Team dashboard, managers only)

Cycle time = email in → first reply (clock time) per person and per kind of work (mailbox), compared with the team median on the same kind, so hard and easy work are not mixed. Flags need at least 3 items: slower than 1.5 × team = "Training?", faster than 0.67 × team = "Good practice to share". Load = responsibilities in hours a week ÷ 40 h: under 70 % "Has room", over 100 % "Overloaded". Shown with a fairness note: a slower time can mean harder requests or support work; use it to plan training, never alone for performance decisions. HR and Legal approve before real use.

### 5.15 Levels, organisation and the Executive summary

- **Levels**: 1 employee (own work) · 2 manager (every screen employees use, nothing hidden, plus Executive summary and Team dashboard with **only their own team's data**) · 3 Director (everything, all teams) · tool owner (admin: + settings). View as: Pricing / Sales / Manager / Director (switch kept for the tool owner only). Demo person "Pricing Manager"; production: Entra ID groups.
- **Organisation chart**: Director → team leads → members (dummy); the people whose data you see are highlighted.
- **Executive summary** (managers and Director open here), written finding first: the headline (win rate trend, late cases), then margin on won quotes and win rate (last 3 months vs the 3 before), answered within the SLA, asked lanes with a valid rate; margin won per month; **Decisions for today** (back-up for one-person work, move work from overloaded to people with room, training, ask carriers for lanes without a rate) and **Risks** (one-person work, nobody owns, overload, lanes without a rate, rates ending, market alerts, urgent tool tickets). Dummy quote history in the demo.
- **Forward / reassign**: person, shared mailbox (Pricing, Operations, Commercial, DP World Freight Forwarding, Air) and reason are all required.

### 5.16 Guide ("Ask the guide", every screen)

A chat-style panel with a fixed help list (`GUIDE`, about 20 questions) matched by keywords; no AI and no made-up answers. Suggested questions follow the current screen; each answer has steps, "Take me there", "Ask for a session" (training request: topic and preferred time, sent to the tool owner as a request in Support) and "Not helpful" / "Ask the tool owner" (sends the question as an idea ticket so the answer is added in a next update). Add or change answers in `GUIDE` in the page.

### 5.17 Dictionary (Help & settings → Dictionary)

The words the tool understands, used by Quick price, the Guide and message reading: ports (names, codes, Arabic spellings), equipment (40HQ = 40 high cube = 40' HC, 40 قدم), work words in English, Egyptian Arabic and Franco (rate = سعر = se3r = as3ar …), filler words to skip (3ayz, عايز, mn, l …). Arabic digits are read as numbers. One letter off or two letters swapped is accepted for port names (Jedah, Valencai). Quick price reads the line as typed first, then through the dictionary. The Guide ranks answers with **BM25** (a fixed ranking formula from classic search engines). "Words the tool did not understand" (from Quick price and the Guide) are listed with a count; the tool owner adds them in one click (`kb_v1`, `kbMiss_v1`; changes go to the change log). "Try it" shows how a line is read. Not AI: nothing is added without the owner. **Feeds**: unknown port names found in carrier emails and files, WhatsApp chats and data sources join the list with where they came from; ports already in the Rate Bank and the port list are understood without adding. **Import a word list**: Excel or CSV (Section, Means, Also written as) or a UN/LOCODE list (code + name); ports not in the tool's port list are skipped and counted; a template can be downloaded.

### 5.18 Quotation PDF: watermark, lock and check code

- **Brand**: platform name (default "DP World Egypt Platform") and the official logo (uploaded once by the tool owner in Settings & sources → Brand: logo and name; shown in the side menu, sign-in screen, PDF header and page title).
- **Watermark**: the official logo ( PNG/JPG up to 300 KB, from the Brand team) is printed see-through (8 %) behind the table on every page; until then the words "DP WORLD". The tool never draws the logo itself.
- **Lock**: the PDF is encrypted with a random owner password that is kept nowhere: print allowed, editing and copying not. Honest limit: jsPDF 2.5.1 uses RC4, which most readers respect but a skilled person can remove, so the check code below is the real protection.
- **Quotation number and check code** (`OF-YYMMDD-001`, `7F3A-91C2`) on top and at the bottom of every page. The code is calculated from the number, time, title, table and remarks; the tool keeps what it sent (`ofVerify_v1`). **Support → Verify a quotation**: number + code (+ optionally a rate from the document) → Matches, or "does not match / the number is not in the quotation the tool sent". Production: the record lives in the database (and can be signed on the server).
- Mail drafts cannot attach files by link: the PDF is downloaded and attached by hand; with Microsoft Graph (IT) the draft can carry the PDF.

### 5.19 Department health (scope: DP World Egypt, freight forwarding core)

Departments: Pricing, Sales / Commercial, Operations, Customs clearance & trucking, Documentation. Each KPI has a target, the value now and before, a status, and — only where a written formula exists — a loss in USD; off-target KPIs show **Where exactly** (top 3 lanes or causes) and **What to do** (fixed list of actions).
- **Real data from the tool**: win rate; margin lost on price (lost quotes "price too high" / "booked elsewhere" × average won margin, by lane); replies within the SLA; asked lanes with a valid rate; Sales: margin lost after quoting ("no reply", "validity too short"); Operations: margin lost for "no space" / "transit time". The lost-quote reason decides the department.
- **SAMPLE data** (marked) until BTI connects the source: Operations loading and demurrage & detention, Customs clearance time and storage fees, Documentation B/L corrections and amendment fees.
- **Status**: Controlled = all KPIs on target; Watch = off target but within 10 % or improving; Out of control = off target and getting worse.
- **Who sees what**: a department head sees only their department (demo heads: Pricing Manager, Hala Mostafa for Operations, Tamer Saleh for Customs & trucking); the Director and the **CEO** (new view, opens here) see the company view: every department, its status, loss in the last 3 months, the main issue and the data source, headed by the biggest pain.

### 5.20 Carrier spot rates (Rate Bank → Carrier spot rates)

A **recipe** per carrier site, saved by the tool owner: the site link, your steps (one per line) and the words that come before each value on that site (20' rate, 40' rate, valid until, vessel / voyage, ETD, transit days, currency; sensible defaults). Daily use: **Open the site** (you log in yourself: no passwords in the tool, no bot), copy the result page (Ctrl+A, Ctrl+C), paste it, **Read the rates**: each value is shown with the sentence it came from, editable. **Add** puts it in the tool as a **Spot** rate (this sailing only, never the lowest), opens an email draft to the consignee or sales with the rates, vessel, ETD and validity, and adds a row to the **Spot rates log** (download as Excel). Why not automatic: browsers do not let a page read another site, and logging in for you would need stored passwords and is usually against the carriers' terms. Fully automatic later: carrier APIs under contract, or an IT robot (Power Automate / RPA) on a company account with the carrier's consent.

### 5.21 Smart request (Quick price and "Price it" on a case)

Under the Quick price result: the **customer target** read from the line or the email ("target USD 1,000", "target rate: 950$"); **margin choices**, each written as buy + margin = sell (advisor / rule margin, meet the target, no margin); **Better rate may exist**: a special or named-customer rate cheaper than the best standard (check it applies to this customer), a cheaper spot (this sailing only), and carriers that serve the lane without a valid standard rate with **Get spot** (opens the carrier site in a window beside the tool and the spot screen filled with the lane and customer); **Draft the reply now** to the sender with the sell rate only. Opening a carrier site inside the tool and clicking through it is not possible from a web page (sites block framing; browsers block reading other sites); that needs a browser extension or an IT robot.

### 5.22 Cockpit (CEO; each Director and department head for their own team)

Managers, Directors and the CEO open here. Headline = the biggest pain. **How are we doing**: margin on won quotes (3 months vs the 3 before), win rate vs 45 %, TEU booked (last month vs the one before), replies within the SLA vs 90 % (all from the tool), revenue vs budget and receivables overdue > 60 days (**SAMPLE** until Finance is connected); a department head sees their own department's KPIs instead. **Where it hurts**: top 3 off-target items from Department health with loss, owner and fix. **Decisions for you**: from the risks (back-up for one-person work, workload, training, carriers) and fixes for out-of-control departments, with Approve / Reject recorded with who and when (`decisions_v1`), and the decided list. **Top customers** (from requests): TEU asked, won, and "down" when the last two complete months fell 30 % vs the two before (the current half month never counts). **Forecast**: margin on won quotes this month, straight line from the month so far vs the average month. **Morning brief** to copy or draft.

### 5.23 Quote checks from the market research (Rates & offer → "Before you send"; Today → Rate moves)

Pricing only, never in the email. **Rate move on the lane**: lowest *standard* rate (40', else 20') valid now vs the latest expired month on the same lane; alert at 5 % or more (`rateMoves`). The same list is a card on **Today** with what to do (up: re-check open offers; down: tell sales). **Free time and D&D**: free time per option (warns when a rate has none) and a cost line: days over free time × boxes × USD per day (default 150, market level for Egypt ports, set by Pricing in `rx_v1`). **ACI / Nafeza**: imports to Egypt need the ACID (19 digits) before loading at origin; exports show "not needed" (`aciCheck`). **Currency and FX**: flags any option not in USD; Pricing saves the bank rate (EGP per USD) with its date and name; warns when older than 7 days. The tool never fetches an FX rate.
Terms added to the quote (email, PDF, Excel): D&D after free time as per tariff; "free time as per carrier tariff" when a rate has none; currency; EGP payment at the bank rate on the invoice date with the saved reference rate and date; ACID line on imports (`rxTerms`).

### 5.24 Live Gmail (owner's private page only)

On the published page, **Inbox → Check inbox** reads the owner's Gmail through the claude.ai Gmail connector (`search_threads`, `get_thread`), last 30 days, rate / quote / booking / freight words only (query saved per browser in `ibxQ_v1`). The reply button saves a **Gmail draft** (`create_draft`) as a reply to the sender; the person opens Gmail and sends it. The tool never sends. Nothing read from Gmail is written to the repo. Without the connector the page uses the offline dummy copy. For DP World, IT replaces this with M365 shared mailboxes via Microsoft Graph (read only).

### 5.25 Gmail test box as the shared mailboxes (demo of the M365 set-up)

The Gmail test box stands in for the DP World shared mailboxes. Each mailbox has a `+tag` address on the same box: `+pricing` (routed by the Cases rules to Ocean, Key accounts, Trucking or Air), `+ops` → **Operations**, `+commercial` → **Commercial**, `+ff` → **DP World Freight Forwarding**, `+air` → **Air requests**. **Shared inbox cases → Pull from Gmail** reads the last 30 days sent to those addresses (`search_threads`, `get_thread`) and opens one case per email (id `G-…`), with SLA, distribution and forwarding as for any case. Ten dummy sample emails were prepared as Gmail drafts for the owner to send. **Draft buttons everywhere**: when Gmail is connected, a Gmail compose link opens an in-tool preview (edit To, subject, text) and **Save draft in Gmail** (`create_draft`); the person sends from Gmail. Without Gmail the links open Gmail compose as before. In production: M365 shared mailboxes via Graph, read only, same screens.

### 5.26 Role names

Views are named by role, not by person or job title: **Executive** (pricing and operations staff, sees buy rates), **Sales** (sell rates only), **Direct Manager** (own team), **Senior Management** (department / Freight Forwarding), **Top Management** (whole company). Internal ids stay `pricing`, `sales`, `manager`, `director`, `ceo`; in production each maps to an Entra ID group.

### 5.3 Browser-only storage (per user)

Shared inbox cases and their settings (`csState_v1`, `csSet_v1` incl. mailboxes added in the tool, `csMy_v1`), data sources (`dsSources_v1`, `dsRows_v1`), working-time log (`wtLog_v1`, 31 days), Apps hub settings (`apps_v1`), Next up timer and snoozes (`tdTask_v1`, `tdDone_v1`, `tdSnooze_v1`), theme, last screen, view (pricing / sales).
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
