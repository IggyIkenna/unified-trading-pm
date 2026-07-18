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

### F2 — New listings + Upcoming expiries + Prediction catalogue: "Unknown error" — `- [x]` FIXED (OOM), pending deploy-verify

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

### F5 — instrument_type axis carries NON-CANONICAL spellings → same type splits into multiple drilldown rows — `- [ ]` OPEN (data-correctness, filed)

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

### F6 — redundant legacy `COINBASE` venue (blank types) in the IS index — `- [ ]` OPEN (data-correctness, filed)

**Operator (2026-07-17): "coinbase … has so many venues which actually have data — are any redundant".** MEASURED: the
three registry venues are legitimately distinct — `COINBASE-SPOT` (spot), `COINBASE-FUTURES` (intl perps),
`COINBASE-CDE` (US Advanced-Trade derivatives, `venue_adapter_keys.py:106/108/120`). BUT the **instruments-service**
cefi index ALSO carries a bare legacy `COINBASE` venue whose only instrument_type is `['']` (blank) — a redundant alias
of `COINBASE-SPOT` with no real typed data, not present in MTDS. Secondary smell: `COINBASE-FUTURES` shows a `SPOT_PAIR`
instrument_type (a futures venue carrying spot pairs — likely miscategorised rows). **Fix direction:** drop /
consolidate the bare `COINBASE` alias into `COINBASE-SPOT` in the IS catalogue (and audit the `COINBASE-FUTURES`
SPOT_PAIR rows). Overlaps F5 (both are IS-catalogue venue/type canonicalisation). **NOTIFIED operator.**

### F7 — DRIFT (removed 2026-07-16) still shows in the DeFi drilldown — 3,556 stale IS rows — `- [ ]` OPEN (data-correctness, filed)

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

## Fix status

| #   | Finding                                 | Repo(s)                         | Status                                                                                                              |
| --- | --------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| F1  | Fixtures league human names             | deployment-api + deployment-ui  | ✅ FIXED — be `@7a7b608f` + ui `@1dbc25d` + L2 `@e67fac7` (pw:L2 ✓)                                                 |
| F2  | 3 panels "Unknown error" (OOM)          | deployment-api (`cloudbuild`)   | ✅ FIXED + VERIFIED — mem 8→16Gi + cpu 2→4 `@18a362ec`+`@861c29894`; live rev 00198 = 16Gi/4CPU, 0 OOM since deploy |
| F3  | Catalogue Explorer dropdowns            | deployment-api + deployment-ui  | ✅ FIXED — be `@2fc46ebc` + ui `@1dbc25d`+`@9f88629` + L2 `@e67fac7`                                                |
| F4  | mock/dev robustness (F1/F3)             | deployment-ui                   | ✅ FIXED — `@9f88629`                                                                                               |
| F5  | non-canonical instrument_type spellings | instruments-service (writer)    | OPEN — filed, data-correctness sweep (its own plan); operator notified                                              |
| F6  | redundant legacy COINBASE venue         | instruments-service (catalogue) | OPEN — filed, overlaps F5; operator notified                                                                        |
| F7  | DRIFT (removed) still in DeFi drilldown | deployment-api and/or IS data   | OPEN — operator chose FILTER+PURGE; converges on IS writer (see fix plan below)                                     |

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

- [ ] [BACKEND] P1. **deployment-api drilldown INTERIM (immediate, no regen)** — canonicalise `instrument_type` at the
      drilldown group-by via the UAC `InstrumentType` legacy→canonical map (collapses `spot`/`spot_pair`/`SPOT_PAIR` →
      `SPOT_PAIR`, `perpetual`/`PERPETUAL` → `PERPETUAL`, `future`/`futures_chain`/`FUTURE` → `FUTURE`; `''`/`'None'` →
      one honest `UNKNOWN` bucket), and EXCLUDE known-removed venues (DRIFT + PACIFICA/MANGO-SOLANA/ZETA-SOLANA/
      FLASH-SOLANA) from the venue axis. Fixes the operator's VISIBLE display immediately;
      `services/data_status_drilldown/`.
- [ ] [SCRIPT] P1. **IS writer — instrument_type canonicalisation (F5)** — apply the UAC `InstrumentType` map at the
      point `build_instrument_catalogue.py` stamps `instrument_type` (line ~267 `CATALOG_COLUMNS` / emission), so every
      catalogue row carries a canonical value; `''`/`None` → an explicit honest sentinel, never the string `'None'`.
      Cross-venue.
- [ ] [SCRIPT] P1. **IS writer — venue canonicalisation + removed-venue exclusion (F6/F7)** — collapse bare-vs-chain
      duplicate venues to ONE canonical form and DROP registry-removed venues (DRIFT etc.) at write time (honor
      `VENUES_BY_ASSET_GROUP` / the venue_adapter_keys active set).
- [ ] [SCRIPT] P1. **Full catalogue regen** (real-infra) after the writer fixes land — snapshot each per-AG
      `prod/catalog.parquet`, regen, INDEPENDENTLY re-read from GCS to verify DRIFT is gone + instrument_type is
      canonical + no bare-vs-chain dupes (the A4/tradfi-repair verify discipline). This IS the "purge" (F7-B) — the
      regen naturally drops DRIFT once the writer excludes it; a separate object delete is only needed if a snapshot of
      the old data is wanted first.
- [ ] [BACKEND] P2. **Removed-venue guard (F7 durable)** — once venue naming is canonical, add the general active-venue
      filter to the drilldown (honor `VENUES_BY_ASSET_GROUP`) so ANY future removed venue auto-hides, superseding the P1
      interim's hardcoded exclusion list.
- [ ] [DATA] P3. **`from 2020-01` floor-date smell** on Solana protocols — CONFIRMED a real (minor) bug (investigated
      2026-07-18). The correct launch dates EXIST in `unified_api_contracts.registry.venue_launch_dates`
      (`KAMINO-SOLANA` 2022-08-24, `JITO-SOLANA` 2022-08-16, etc.), but the drilldown shows a generic **2020-01** floor
      — instruments-service has a `_DEFAULT_TRADFI_FLOOR = datetime(2020, 1, …)` + a "generic 2020-01 floor when neither
      layer has the pair" fallback (`reference_data/utils/evm_creation_resolver.py`,
      `reference_data/adapters/tradfi/databento/`). So the DeFi listing-date derivation is falling back to the default
      floor instead of consulting `venue_launch_dates` for the protocol's real launch. **Fix direction:** thread
      `venue_launch_dates` into the DeFi `available_from` derivation (use the real launch date; the 2020-01 floor only
      when truly unknown). Low-priority display accuracy — does not block the F5/F6/F7 sweep.
