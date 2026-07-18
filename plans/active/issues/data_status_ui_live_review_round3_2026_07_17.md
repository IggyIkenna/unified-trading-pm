---
doc_type: issue
title:
  Data-status page — live UI review round 3 (2026-07-17 pm) — league names, unknown-error panels, catalogue dropdowns
summary:
  Operator live-reviewed the deployed instruments-service data-status page 2026-07-17 pm and reported four UI findings.
  This doc TRACKS all of them and their fix status. (1) Fixtures browser groups by raw API-Football numeric league_id
  instead of the human canonical league name. (2) New listings + Upcoming expiries + Prediction catalogue panels show
  "Unknown error" — backend code VERIFIED WORKING against real GCS locally, so this is a deploy-lag / client-timeout
  issue, not a code bug. (3) Catalogue Explorer venue / data_type / instrument_type are free-text inputs that should be
  dropdowns of the real distinct values.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, deployment-api, unified-api-contracts]
scope: [engineer]
tags: [data-status, deployment-ui, deployment-api, ux, fixtures, prediction, catalogue, sports]
related: [data_status_page_ux_and_canonicalisation_2026_07_16.md]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
assigned_role: ui_developer
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
source: operator live UI review 2026-07-17 pm (screenshots in chat)
depends_on: []
---

# Data-status page — live UI review round 3 (2026-07-17 pm)

Operator reviewed the deployed instruments-service data-status page and reported four findings. Tracked here per the
operator's "keep adding these to docs to keep track and fix all" instruction. Each row carries its diagnosis + fix
status; updated as they land.

## Findings

### F1 — Fixtures browser: leagues shown as raw API-Football numeric IDs, not human names — `- [x]` FIXED

**SHIPPED — backend `deployment-api@7a7b608f` + UI `deployment-ui@1dbc25d` + L2 spec `deployment-ui@e67fac7` (pw:L2 ✓, 4
specs green).** Backend `fixtures_browser.py` resolves each catalogue `league_id` → human `display_name` via UAC
(`get_league_by_api_football_id` for the numeric AF id — 2 → "UEFA Champions League", 103 → "Eliteserien" — then
`get_league` for a canonical string id), returned as a `league_names` map alongside `leagues`; unresolved ids are
OMITTED (honest-absence). The UI (`FixturesBrowser.tsx`) renders the name as the group header with the raw id as a muted
subtitle; an unmapped id shows the raw id alone. 26 vitest component tests + a playwright L2 regression spec
(`fixtures-browser-league-name-103` == "Eliteserien").

The Fixtures browser grouped by `league_id` and rendered the raw API-Football numeric id as the group header (`103`,
`104`, `113`, `129`, `2`, `253`, …). Operator wants the **human canonical league name** (e.g. 103 → Eliteserien, 2 →
UEFA Champions League). **These league IDs ARE resolvable** — UAC carries
`canonical.domain.sports.league_registry.LEAGUE_REGISTRY` (keyed by canonical league_id) + a reverse
`api_football_id → league_id` map + `get_league(league_id)`. Fix direction: resolve at the **backend**
(`deployment-api/services/fixtures_browser.py` builds the `FixturesByLeagueAndDay` league keys) so the response carries
a human `league_name` alongside the id — league data is UAC data, the UI must not hardcode a mapping. Then the UI
renders the name (id as a subtitle/tooltip). Honest-absence: an id with no registry entry shows the raw id, never a
fabricated name.

### F2 — New listings + Upcoming expiries + Prediction catalogue: "Unknown error" — `- [x]` FIXED + VERIFIED (OOM)

> **VERIFIED 2026-07-18:** live revision `00198-tkc` = 16Gi/4CPU, **0 OOM** since the deploy. (Note: a SEPARATE latency
> issue on New Listings / Upcoming Expiries — 35s cold read, not OOM — was later reported + is tracked as F10.)

**CORRECTED diagnosis (2026-07-17 pm): the root cause is a container OOM, NOT deploy-lag/latency and NOT a code-logic
bug.** My first pass said "deploy-lag" — that was wrong; I confirmed it by reading the LIVE Cloud Run logs (ground
truth), not by inference. The service code is correct (all three service functions return data against real GCS:
`list_new_listings(30)` → 440,433 rows, `list_upcoming_expiries(7)` → 6,180 rows, `read_prediction_catalogue(50)` →
total 2,673,118, all OK with the A4 `question` `_READ_COLUMNS` addition). But the DEPLOYED revision (`00195-jr9`,
deployed 17:01, only ~30 min old — so promotion was NOT the issue) logged:

```
Memory limit of 8192 MiB exceeded with 8585 MiB used.  (2026-07-17T17:21:30Z)
… /api/data-status/prediction-catalogue         → 500
… /api/instruments/new-listings                 → 500
… /api/instruments/upcoming-expiries            → 500
… /api/data-status/coverage-summary (×2 svc)    → 500
… /api/capabilities/service-asset-groups        → 500   (all 500 at the SAME 17:21:14 timestamp)
```

The data-status page **mounts several heavy catalogue-reading panels simultaneously** on tab open (New listings +
Upcoming expiries read all five per-AG `prod/catalog.parquet` objects; Prediction catalogue reads the 184 MB / 2.67M-row
prediction catalogue, now 25 cols after this session's `question` backfill — so my A4 work slightly _increased_ the
footprint; coverage-summary / drilldown read the availability index). Under Cloud Run `concurrency=80`, a cold
first-mount burst packs all of them onto ONE 8 GiB instance → 8585 MiB > 8192 → the container is **killed**, taking
every in-flight request with it → the UI renders "Unknown error" on ALL panels at once (exactly the operator's
screenshot). Intermittent (1 OOM / 6h) because a warm 5-min TTL cache hit avoids the cold burst — hence "sometimes
works, sometimes Unknown error". This is the SECOND OOM on this service (the first,
`deployment_ui_data_status_drilldown_oom_and_leaf_schema_2026_07_15`, bumped it 8Gi; the page has grown since).

**Fix SHIPPED (two commits) — `deployment-api@18a362ec` then `@861c29894` (`cloudbuild.yaml`): `--memory 8Gi → 16Gi`

- `--cpu 2 → 4`.** The first commit set `--memory 16Gi` ALONE and the deploy was REJECTED (cloudbuild `16da79db`
  FAILED): Cloud Run gen2 caps memory at 8Gi for 2 CPU — 16Gi requires ≥4 CPU
  (`"For 2.0 CPU, memory must be between 128Mi and 8Gi"`). The follow-up added `--cpu 4` (which also shortens the
  concurrent-heavy-read overlap window — parquet decompress + pandas are CPU-bound, itself part of the OOM cause). Reads
  are already column-pruned + TTL-cached, so headroom is the right lever for a cold burst; a code-level in-container
  `asyncio.Semaphore` capping concurrent heavy catalogue loads (modelled on `_deploy_turbo._drilldown_build_semaphore`)
  remains the documented follow-up if it recurs at 16Gi/4CPU. **Pending: verify the promoted revision reaches
  16Gi/4CPU + no further OOM against the DEPLOYED endpoint (the 18:03 promote's deploy FAILED on the CPU/mem mismatch —
  the `@861c29894` fix must promote before it deploys).**

### F3 — Catalogue Explorer: venue / data_type / instrument_type should be dropdowns, not free-text — `- [x]` FIXED

**SHIPPED — backend `deployment-api@2fc46ebc` + UI `deployment-ui@1dbc25d` + robustness `deployment-ui@9f88629` + L2
`deployment-ui@e67fac7` (pw:L2 ✓).** New backend endpoint `GET /data-status/catalogue-filter-options` returns the sorted
distinct non-blank `venues` / `instrument_types` / `data_types` for a `(service, asset_group)` (single-walk: reuses the
same column-pruned `prod/catalog.parquet` read `/catalogue` does, de-duped to latest-per-instrument; honest-absence — an
absent/all-blank axis returns `[]`). The UI (`CatalogueExplorer.tsx`) replaced the free-text inputs with `<select>`s
populated from it (default "Any", reset + refetch on asset-group change). Robustness follow-up (`@9f88629`): guarded the
consumption with `?? []` so a malformed response can't crash the `.map`, and added the two missing `mock-api.ts`
handlers (`league_names` in `/fixtures/browse`, a dedicated `catalogue-filter-options` handler — the L2 agent found the
latter fell through to the catalogue-rows prefix and CRASHED the widget in mock/dev mode).

The Catalogue Explorer's VENUE / INSTRUMENT TYPE / DATA TYPE filters were free-text `optional` inputs. Operator wanted
**dropdowns of the real distinct values** for the selected asset_group (typing a venue exactly is error-prone). Fix: a
small backend endpoint returning the distinct venue / instrument_type / data_type values present in the selected
`(service, asset_group)` catalogue — the `_catalogue.py` read already loads the frame, so distinct-values is cheap and
single-walk-safe — then the UI renders `<select>`s populated from it, scoped to the chosen asset_group, with an
"all/any" default. `[UI]` + pw:L2.

### F4 — mock/dev-mode robustness for F1+F3 (found by the L2 playwright agent) — `- [x]` FIXED

Surfaced while writing the F1/F3 L2 spec: the app's dev/preview runs `VITE_MOCK_API=true`, whose `src/lib/mock-api.ts`
monkey-patches `window.fetch` (so Playwright `page.route()` mocks are inert — the L2 spec now injects a `window.fetch`
wrapper instead). Two real gaps in that mock: (1) `/api/fixtures/browse` never returned `league_names` (F1 could never
show a name in mock mode); (2) there was NO `/api/data-status/catalogue-filter-options` handler, so it fell through to
the `/api/data-status/catalogue` prefix and returned the rows shape (no `venues` array) → `CatalogueExplorer` CRASHED on
`.map`. **Fixed `deployment-ui@9f88629`**: added both mock handlers + hardened the real component's consumption with
`?? []` so ANY malformed response degrades to empty dropdowns instead of throwing.

### F5 — instrument_type axis carries NON-CANONICAL spellings → same type splits into multiple drilldown rows — `- [x]` FIXED

**FIXED (2026-07-18).** Drilldown DISPLAY canonicalised — `deployment-api@512180be` (`data_status_hierarchical.py`): the
instrument_type axis group-key is canonicalised via the UAC `InstrumentType` legacy map (spot/spot_pair→SPOT_PAIR,
perpetual→PERPETUAL, future/futures_chain→FUTURE; `''`/`'None'`/`nan`→a single honest `UNKNOWN` node), and merged groups
SUM their captured/empty/failed counts with `completion_pct` RECOMPUTED from the summed totals (not averaged) —
count-preserving, adversarially verified. Forward captures canonicalised at the WRITER — `instruments-service@ee19f6f3`
(`build_instrument_catalogue.py` + `writers.py`). Measured: the `prod/catalog.parquet` catalogue was ALREADY canonical
for cefi/defi/tradfi (the non-canonical spellings lived only in the availability INDEX behind the drilldown, now fixed
at display + forward at the writer).

**Operator (2026-07-17): "bybit spot appearing in two places as instrument type in the drilldown".** MEASURED against
the live cefi availability indexes (read-only, 2026-07-18):

- `COINBASE-SPOT` instrument_types = `['', 'SPOT_PAIR', 'spot', 'spot_pair']` — **three spellings of spot** + a blank.
- `BYBIT` = `['', 'FUTURE', 'PERPETUAL', 'SPOT_PAIR', 'futures_chain', 'perpetual']` — `PERPETUAL`+`perpetual`,
  `FUTURE`+`future`(via COINBASE-CDE)+`futures_chain`.
- Literal string `'None'` appears as an instrument_type value in several venues (e.g. BYBIT-SPOT, COINBASE-CDE) — a
  honest-absence violation (the string "None", not absence).

The data-status drilldown groups by the RAW `instrument_type` value, so one real type (spot) fans out into `SPOT_PAIR` /
`spot` / `spot_pair` rows — exactly the operator's "two places". **Root cause: the instrument_type is not canonicalised
to the UAC uppercase vocabulary at the writer** (mixed casing + legacy spellings + literal `None`/blank persisted in the
availability index / IS catalogue). **Fix direction (bigger — its own plan):** canonicalise `instrument_type` at the
WRITE path (IS rollup / MTDS manifest) to the UAC canonical set, and/or canonicalise in the drilldown group-by as an
interim; treat `''`/`'None'` as honest-absence (a single "unknown" bucket, never fabricated). Cross-venue (not just
bybit/coinbase) — a data-correctness sweep. **NOTIFIED operator.**

### F6 — redundant legacy `COINBASE` venue + bare-vs-chain duplicate venues — `- [x]` FIXED

**FIXED (2026-07-18).** Drilldown DISPLAY collapses bare-vs-chain duplicate venues to one canonical node
(`deployment-api@512180be`: `JITO`+`JITO-SOLANA`→`JITO-SOLANA`, `RAYDIUM`/`MARINADE` likewise — conservative exact
3-pair map, count-preserving relabel-before-groupby, NOT a blanket bare→Solana rule). Forward writer collapses the same
(`instruments-service@ee19f6f3`). Measured: the `prod/catalog.parquet` catalogue carries NO bare-vs-chain dupes (only
the bare forms exist there; the dupes are in the availability index → handled at display). The bare `COINBASE` alias is
already re-keyed away in `VENUES_BY_ASSET_GROUP` (`market_data_categories.py:303`) so it is excluded from the active
universe.

**Operator (2026-07-17): "coinbase … has so many venues which actually have data — are any redundant".** MEASURED: the
three registry venues are legitimately distinct — `COINBASE-SPOT` (spot), `COINBASE-FUTURES` (intl perps),
`COINBASE-CDE` (US Advanced-Trade derivatives, `venue_adapter_keys.py:106/108/120`). BUT the **instruments-service**
cefi index ALSO carries a bare legacy `COINBASE` venue whose only instrument_type is `['']` (blank) — a redundant alias
of `COINBASE-SPOT` with no real typed data, not present in MTDS. Secondary smell: `COINBASE-FUTURES` shows a `SPOT_PAIR`
instrument_type (a futures venue carrying spot pairs — likely miscategorised rows). **Fix direction:** drop /
consolidate the bare `COINBASE` alias into `COINBASE-SPOT` in the IS catalogue (and audit the `COINBASE-FUTURES`
SPOT_PAIR rows). Overlaps F5 (both are IS-catalogue venue/type canonicalisation). **NOTIFIED operator.**

### F7 — DRIFT (removed 2026-07-16) still shows in the DeFi drilldown — `- [x]` FIXED (filter + purge, verified)

**FIXED (2026-07-18) — operator's "filter + purge" done both ways.** (1) FILTER: the drilldown excludes the removed
Solana perp DEXes (`deployment-api@512180be`: `_REMOVED_VENUE_BASES` = DRIFT/PACIFICA/MANGO/ZETA/FLASH, base-prefix
match so bare + `-SOLANA` forms both go, applied globally before aggregation so root totals stay consistent). (2) PURGE:
surgically dropped the removed-venue rows from the live `prod/catalog.parquet` — **defi 11,787→11,724 (63 DRIFT rows),
cefi 425,170→425,160 (10 PACIFICA-SOLANA rows mislabeled into cefi)** — using the shipped writer's own
`_is_removed_venue` helper for consistency; snapshots saved (`catalog.20260718T0900Z.canonicalise.<ag>.bak.parquet`);
**INDEPENDENTLY re-read live GCS: DRIFT=0, PACIFICA=0, row counts exact.** Forward writer excludes them
(`instruments-service@ee19f6f3`).

**NOTE — did NOT run `--mode full` regen (verify-before-write caught a data-loss trap):** the defi full-mode dry-run
produced 9,418 rows vs the current 11,787 = a 2,369-row shrink, but only 63 are DRIFT — the other **2,306 are a
`--mode full` vs `--mode incremental` delta** (a full re-walk yields fewer instruments than the accumulated frozen-tail
catalogue). Overriding the monotonic guard would have deleted 2,306 legit rows. The surgical purge (exactly 63+10
removed-venue rows) is provably safe; the full-vs-incremental delta is filed below as a SEPARATE finding to investigate
before any full rebuild.

### F8 — `--mode full` catalogue regen is lossy vs the incremental catalogue (2,306-row delta) — `- [ ]` OPEN (found 2026-07-18)

Discovered while verifying F7: a `build_instrument_catalogue.py --asset-group defi --mode full` dry-run rolls up
**9,418** rows, but the live (incrementally-built) catalogue holds **11,787** — a full re-walk produces ~2,306 FEWER
instruments than the accumulated incremental frozen tail. Either the frozen tail has accumulated stale rows the full
walk correctly drops (→ full is the corrective truth), or the full walk under-covers history the frozen tail rightly
preserves (→ full is lossy). Until this is understood, **`--mode full` on any asset group is unsafe** (it would trip the
monotonic guard for a large, unexplained shrink). Investigate: diff the full-mode row set vs the incremental catalogue
by instrument_id + check whether the missing 2,306 have extant `by_date` source objects.

**Operator (2026-07-17): "i thought we got rid of some of these dsol venues like DRIFT as they got hacked".** CONFIRMED:
DRIFT was removed from the venue registry 2026-07-16 (operator ruling — hacked ~$280M, rebranded Velocity DEX; all
Solana perp DEXes dropped; `venue_adapter_keys.py:196`, SSOT `codex/04-architecture/solana-defi-coverage.md`). Of the 8
Solana protocols the operator saw (DRIFT, JITO, KAMINO, MARGINFI, MARINADE, ORCA, RAYDIUM, SOLEND), **only DRIFT is
removed-but-still-showing** — the other 7 are in the ACTIVE registry (staking/lending/AMM, not perp DEXes) and are
legitimately kept. MEASURED (2026-07-18): DRIFT = **0 rows in the MTDS defi index** but **3,556 rows in the
instruments-service defi index** (`instrument_type ['', 'PERPETUAL', 'SPOT_PAIR']`) — the drilldown reads the IS index,
which was never purged of DRIFT's historical rows when the adapter mapping was removed. **Fix direction (options, needs
operator decision):** (A) filter the data-status drilldown to honor the UAC active-venue set (`VENUES_BY_ASSET_GROUP`)
so any registry-removed venue is auto-excluded from the monitoring view — general, no data loss, deployment-api code
only [RECOMMENDED]; (B) purge DRIFT's 3,556 rows from the IS defi catalogue/index (real-infra cleanup, matches the
"removed" intent but loses audit history); (C) both. The "from 2020-01" floor date on these Solana protocols is a
secondary date-floor smell (Solana DeFi didn't exist Jan 2020). **NOTIFIED operator.**

### F9 — sports LEAGUE filter is exact/case-sensitive + Upcoming Fixtures shows raw league ids — `- [x]` FIXED

**SHIPPED — `deployment-api@eeb23b13` + `deployment-ui@680e4139`/`e643a5c` (pw:L2 ✓, 2 specs green).** A shared
`league_matches_filter` (in `upcoming_fixtures.py`, the imported-from module — no circular import) resolves each
DISTINCT raw `league_id` once and matches the filter as a case-insensitive SUBSTRING against either the raw id OR the
UAC `display_name` (mirroring the team filter) — so "allsven"/"Allsvenskan"/"ALLSVENSKAN" all match league 113
(verified: `league_matches_filter('113','allsven')` → True). Applied to BOTH the fixtures browser and upcoming fixtures;
`/fixtures/upcoming` now also returns a `league_names` map and the Upcoming Fixtures UI renders the human name (raw id
subtitle, honest-absence fallback), matching F1; both League-id placeholders now read "e.g. EPL or Allsvenskan".
Adversarially verified.

Operator: typing "Allsvenskan" (a league human NAME) in the fixtures-browser LEAGUE filter returns 0; a team name
("Halmstad") matches. Root cause (measured): the LEAGUE filter is an EXACT, case-sensitive match on the raw `league_id`
(`fixtures_browser.py:258` + `upcoming_fixtures.py:303`: `df["league_id"].astype(str) == league_filter`), while the TEAM
filter already does case-insensitive substring (`_matches_team`, `.lower()` + `in`) and the catalogue instrument_id
search already does `.str.lower().str.contains` — so those two are fine; only the LEAGUE filter is the outlier.
Operator's general theme: **all filters should be case-insensitive + PARTIAL (substring / "first half of the word")**,
matching human names too. Also (screenshot): **Upcoming Fixtures still renders raw league ids (113/114)** — it needs the
F1 human-name treatment. **Fix (round4 workflow `wf_fbac7262`):** LEAGUE filter → case-insensitive substring on
league_id OR resolved human display_name (shared helper in `upcoming_fixtures.py`, distinct-resolve not per-row) +
Upcoming Fixtures renders human league names.

### F10 — New Listings + Upcoming Expiries very slow / "Unknown error" (latency, NOT OOM) — `- [x]` FIXED

**SHIPPED — `deployment-api@4df2a93e` + `deployment-ui@e643a5c`.** Three levers in `catalogue_lifecycle.py`: (1)
**pagination** — `list_new_listings_page`/`list_upcoming_expiries_page` return `(page_rows, total_count)` and build only
the 50-row page (the prior UNBOUNDED 644,380-row dict build was the actual cause of the 500s — now eliminated); (2)
**parallel reads** — the 5 per-AG catalogue reads fan out on a bounded ThreadPool (cold **35s → 22.9s**, now bounded by
the slowest single AG, not the serial sum); (3) a **background warm task** refreshes the default-params cache every 270s
so user requests hit the warm path (~0s) in steady state, and even a cold miss (~22s) stays under the 120s client
timeout. `total_count=644,380` matches the pre-fix baseline EXACTLY (honest same result set, just paged). Adversarially
verified. Follow-up (open risk): the warm task only warms DEFAULT params — a non-default asset_group/venue filter still
pays a cold read.

Operator: New Listings + Upcoming Expiries very slow to load "if it's using catalogue" + New Listings shows "Unknown
error". Diagnosed (measured live 2026-07-18): **NOT OOM** — the F2 16Gi/4CPU fix holds (0 OOM in 2h). It is pure
LATENCY: `catalogue_lifecycle.list_new_listings(30)` = **35s**, `list_upcoming_expiries(5)` = **31s** — it reads ALL
FIVE per-AG `prod/catalog.parquet` COLD serially (prediction alone = **2.9M rows / 17s**; tradfi 1.17M) on every 5-min
TTL cache miss AND returns **644,380 rows unbounded**; 35s > the Cloud Run / browser fetch timeout → 500 "Unknown
error". NOT previously flagged with a specific fix (F2 covered only the OOM; there is a general `ui_build_warm_cache`
plan). **Fix (round4 workflow `wf_fbac7262`):** pagination (limit/offset, `total_count`, page-only row build, mirroring
A5's `/catalogue`) + parallelise the 5 per-AG reads (cold ≈ slowest single ≈ 17s not 35s serial) + warm the cache off
the request path (prime at startup + background refresh under the TTL) so a user request never does the cold read
synchronously.

## Fix status

| #   | Finding                                                             | Repo(s)                              | Status                                                                                                                 |
| --- | ------------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| F1  | Fixtures league human names                                         | deployment-api + deployment-ui       | ✅ FIXED — be `@7a7b608f` + ui `@1dbc25d` + L2 `@e67fac7` (pw:L2 ✓)                                                    |
| F2  | 3 panels "Unknown error" (OOM)                                      | deployment-api (`cloudbuild`)        | ✅ FIXED + VERIFIED — mem 8→16Gi + cpu 2→4 `@18a362ec`+`@861c29894`; live rev 00198 = 16Gi/4CPU, 0 OOM since deploy    |
| F3  | Catalogue Explorer dropdowns                                        | deployment-api + deployment-ui       | ✅ FIXED — be `@2fc46ebc` + ui `@1dbc25d`+`@9f88629` + L2 `@e67fac7`                                                   |
| F4  | mock/dev robustness (F1/F3)                                         | deployment-ui                        | ✅ FIXED — `@9f88629`                                                                                                  |
| F5  | non-canonical instrument_type spellings                             | deployment-api + instruments-service | ✅ FIXED — drilldown display `@512180be` + writer `@ee19f6f3` (catalogue was already canonical)                        |
| F6  | redundant COINBASE + bare-vs-chain dup                              | deployment-api + instruments-service | ✅ FIXED — display collapse `@512180be` + writer `@ee19f6f3`                                                           |
| F7  | DRIFT (removed) still in DeFi drilldown                             | deployment-api + IS catalogue        | ✅ FIXED — filter `@512180be` + purge (defi 63/cefi 10 rows, GCS-verified) + writer `@ee19f6f3`                        |
| F8  | `--mode full` regen lossy (2,306 delta)                             | instruments-service                  | OPEN — found while verifying F7; definitive full-vs-live diff running to root-cause                                    |
| F9  | league filter exact/case-sensitive + upcoming-fixtures raw ids      | deployment-api + deployment-ui       | ✅ FIXED — be `@eeb23b13` + ui `@680e4139`/`@e643a5c` (pw:L2 ✓); name+partial+case-insensitive match, upcoming names   |
| F10 | New Listings/Upcoming Expiries slow (35s cold, unbounded) → timeout | deployment-api + deployment-ui       | ✅ FIXED — be `@4df2a93e` + ui `@e643a5c`; pagination (killed 644K-row build) + parallel reads (35→22.9s) + warm cache |

## Fix plan — F5/F6/F7 IS-catalogue canonicalisation sweep (operator-decided 2026-07-18)

Operator decisions: **F7 = filter-now + purge; F5/F6 = start the canonicalisation sweep now.** Deeper investigation
(measured 2026-07-18) shows all three converge on the **instruments-service catalogue writer**
(`instruments-service/scripts/build_instrument_catalogue.py`) + a **full catalogue regen** — plus an immediate
deployment-api display fix. Grounded facts + the expanded scope:

- **The canonical mechanism EXISTS**: `unified_api_contracts._instrument_enums.InstrumentType` (StrEnum) is the SSOT
  vocabulary (`SPOT_PAIR`/`PERPETUAL`/`FUTURE`/`OPTION`/`POOL`/`LENDING`/`LST`/…) with a documented legacy→canonical map
  (`spot→SPOT_PAIR, perp→PERPETUAL, futures→FUTURE, …`). The fix is to APPLY it, not invent one.
- **A catalogue PURGE alone won't stick**: the `prod/catalog.parquet` is DERIVED by the rollup from the per-date
  `by_date/day=/venue=/instruments.parquet` objects, which still carry DRIFT / non-canonical types. So the durable fix
  is at the WRITER (exclude removed venues + canonicalise), then regen — a one-off catalogue delete would be re-created
  on the next rollup.
- **F6 is broader than coinbase** (measured on the live IS defi index): bare-vs-chain DUPLICATE venues —
  `JITO`+`JITO-SOLANA`, `RAYDIUM`+`RAYDIUM-SOLANA`, `MARINADE`+`MARINADE-SOLANA` all appear as separate venues; plus the
  cefi bare `COINBASE` (blank types) redundant with `COINBASE-SPOT` (already re-keyed away in `VENUES_BY_ASSET_GROUP`,
  `market_data_categories.py:303`). DRIFT shows as bare `DRIFT`.

**Todos (execute as tracked units — writer + regen is real-infra, coordinate on the HOT-contended
`build_instrument_catalogue.py`):**

- [x] [BACKEND] P1. **deployment-api drilldown display canonicalisation** — DONE `deployment-api@512180be`
      (`data_status_hierarchical.py`): instrument_type canonical merge (count-preserving, `%` recomputed from sums) +
      removed-venue exclusion (`_REMOVED_VENUE_BASES` base-prefix) + bare-vs-chain collapse. Adversarially verified.
- [x] [SCRIPT] P1. **IS writer — instrument_type canonicalisation (F5)** — DONE `instruments-service@ee19f6f3`
      (`_canonicalize_instrument_type` + `INSTRUMENT_TYPE_UNKNOWN` at the emission point + `writers.py` forward). NB the
      `prod/catalog.parquet` was MEASURED already-canonical for cefi/defi/tradfi — this is defensive + fixes forward
      availability-index captures; the non-canonical values were in the availability index (drilldown), handled by P1.
- [x] [SCRIPT] P1. **IS writer — venue canonicalisation + removed-venue exclusion (F6/F7)** — DONE
      `instruments-service@ee19f6f3` (`_REMOVED_VENUES` frozenset + `_DUPLICATE_VENUE_ALIASES` conservative 3-pair
      collapse).
- [x] [SCRIPT] P1. **Catalogue purge (F7-B)** — DONE via a SURGICAL in-place drop (NOT `--mode full` regen — see F8):
      dropped the removed-venue rows from the live `prod/catalog.parquet` using the shipped writer's own
      `_is_removed_venue` — **defi 63 (DRIFT), cefi 10 (PACIFICA-SOLANA)**, snapshots saved, INDEPENDENTLY GCS-verified
      (DRIFT=0/PACIFICA=0, exact row counts). tradfi = no-op (0 removed, already canonical). One-off script:
      `scratchpad/surgical_catalogue_fix.py` (imports the writer helpers for byte-consistency).
- [x] [BACKEND] P2. **Removed-venue guard (F7 durable) — made the explicit set a UAC SSOT.** DONE
      `unified-api-contracts@77aa6818` + `deployment-api@a6d8b8c`. The general `VENUES_BY_ASSET_GROUP`
      active-set-intersection filter stays UNSAFE (unchanged conclusion — availability-index venue names don't cleanly
      match the registry, bare vs `-<CHAIN>`, so a naive intersection would OVER-hide legit venues); instead moved the
      P1 explicit `_REMOVED_VENUE_BASES` set OFF the deployment-api local hardcode and onto a new UAC export
      `unified_api_contracts.registry.venue_adapter_keys.DECOMMISSIONED_VENUE_BASES` (base names, uppercased, each
      commented with removal date + reason, sourced from the same DRIFT/PACIFICA/MANGO/ZETA/FLASH removal records
      already documented in `venue_adapter_keys.py`). deployment-api's `_REMOVED_VENUE_BASES` now `is`
      `DECOMMISSIONED_VENUE_BASES` (asserted by a new test) — display behavior is byte-identical (same 5 bases, same
      base-prefix match), but a future venue removal now auto-propagates from the one UAC SSOT instead of needing a
      parallel deployment-api edit. Tests added both sides (UAC: membership + no-active-venue-collision gates;
      deployment-api: SSOT-identity test); both repos' `quality-gates.sh` green.
- [x] [DATA] P3. **Solana DeFi launch-date accuracy — FIXED `instruments-service@0b1f0cad`.** The real bug was more
      specific than the "2020-01 floor" hypothesis:
      `reference_data/adapters/defi/_solana_utils.py::get_protocol_floor_date` (which every Solana adapter calls to seed
      its `available_from_datetime`) consulted ONLY a **stale local hardcoded dict** that had drifted from reality
      (kamino local=2024-01-01 vs real 2022-08-24; jito local=2021-11-01 vs 2022-08-16; orca local=2022-03-01 vs
      2021-02-09) — never touching the UAC SSOT. Fix threads `venue_launch_dates.get_venue_launch_date("defi", venue)`
      as the PRIMARY lookup (chain-suffixed `{PROTOCOL}-SOLANA` then bare), falling back to the local dict only for
      protocols UAC doesn't cover, then the existing honest `KeyError` guard (never fabricates a date). Adversarially
      verified, QG green. **Forward** (new rollups); a regen would refresh historical `available_from` (gated on F8 —
      see the `--mode full` safety finding). **Follow-up filed:** `uac_defi_launch_date_registry_drift_2026_07_18.md` —
      UAC has TWO disagreeing DeFi launch-date registries (`venue_launch_dates.DEFI_VENUE_LAUNCH_DATES` vs
      `chain_env.PROTOCOL_LAUNCH_DATES`, disagree on AAVE_V3-ETHEREUM 2022-03-16 vs audited-correct 2023-01-27) — a real
      SSOT contradiction the P3 agent surfaced.
