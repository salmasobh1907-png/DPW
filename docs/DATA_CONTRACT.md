# Data contract: what any main source must give the pricing tool

The screens read only one data object (`DATA`). Any main source (the file inside the page today, a JSON file made by a
scheduled job, NPM later) must give this shape. The page checks it (`dataCheck`) before it switches; if the check fails
it keeps the data file inside the page and shows why on **Help & settings → Data sources**.

Dummy example: `data/demo_data.json` (built by `scripts/pricing_rate_bank_to_data.py`).

## Sources

| Source | Setting | Who makes the data |
| --- | --- | --- |
| Data file inside the page | `{"source":"embedded"}` (default) | `pricing_rate_bank_to_data.py` + `inject_data.py` |
| Data file (JSON) from a link | `{"source":"json","url":"https://…/pricing-data.json"}` | Scheduled job on a DP World service account: reads the Pricing Rate Bank on SharePoint (read only), runs the same converter, writes the JSON to a SharePoint library or an API |
| NPM (Network Pricing Manager) | `{"source":"npm","url":"https://…"}` | NPM API; `npmMap()` turns its records into this contract. **Field names are assumptions to confirm with the NPM team.** |

IT sets the default for everyone in `DPW_CONFIG` at the top of the data layer in the page. A pricing lead can switch on
the Data sources screen (saved in that browser only). Links must be `https://` and must allow the tool to read them
(same DP World sign-in, or CORS for the tool's address).

## Required

| Key | Type | Notes |
| --- | --- | --- |
| `rates` | list of rate rows | Export dry (and special) rates |

## Optional (kept from the page when missing)

| Key | Type | Notes |
| --- | --- | --- |
| `reefers` | list of rate rows | Uses `rf20` / `rf40` |
| `imports` | list of rate rows | `pol` = foreign port, `pod` = Egyptian port |
| `contacts` | `{carrier: [pricing email, sales email]}` | |
| `susp` | list of `{car, pod, since, until, why, by}` | `pod` empty = all lanes; dates `YYYY-MM-DD` or empty |
| `mrules` | list of `{name, dir: exp/imp, cargo: dry/rf, pods: [..], m20, m40}` | Fixed margins (China) |
| `requests`, `bookings`, `qhist`, `health` | as in README 5.1 | |
| `lanes` | object | Calculated by the page (`buildLanes`) when missing, with the same rule as the converter |
| `rbsrc` | text | Name shown for the source |
| `asof` | `YYYY-MM-DD` | Date of the data |

## Rate row

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `car`, `pol`, `pod` | text | yes | Not empty |
| `r20`, `r40`, `rf20`, `rf40` | number > 0 | at least one | Per container, USD unless `cur` says otherwise |
| `valid` | `YYYY-MM-DD` or empty | no | Empty = valid to the end of the month |
| `id` | text | recommended | Rate ID, unique across `rates`, `reefers`, `imports` (`EX-00001`, `IM-00001`) |
| `type` | text | no | Contract type. Empty or "Standard" = standard; anything else never counts as the lowest |
| `cur`, `tt`, `ts`, `ft`, `thc20`, `thc40`, `thccur`, `term`, `cust`, `sailing`, `cmt`, `src`, `ref` | | no | `term`: "DP World" or "Other" for Sokhna |

## Checks that stop a switch

Missing `rates` · a row without `car`, `pol` or `pod` · no rate column · a rate that is not a number above 0 ·
a date not in `YYYY-MM-DD` · duplicate Rate IDs · a suspension without carrier · a margin rule without name or ports.
Warnings only: currency not USD, 40' lower than 20'.

## NPM: assumed fields (to confirm)

`rateId`, `carrierName`, `originPort`, `destinationPort`, `direction` (EXPORT / IMPORT),
`containerRates` {`20GP`/`20DC`, `40HC`/`40GP`/`40DC`, `20RF`, `40RF`}, `currency`, `validTo`, `contractType`,
`transitDays`, `via`, `freeTime`, `remarks`.
