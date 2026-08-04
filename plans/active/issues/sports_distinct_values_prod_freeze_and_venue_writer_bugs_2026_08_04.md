---
doc_type: issue
title:
  "Sports distinct-values panel: 4-day-frozen prod deploy (44→3 non-canonical count) — root-caused + fixed today; 3
  venues (FOOTBALL/LADBROKES_UK/SPORT888) need a historical re-stamp, not more code"
summary: >-
  Operator flagged the deployment-ui Distinct Values panel (sports) still showing ~44 non-canonical values across
  venues/instrument_types/data_types despite prior sessions already having landed the fixes in UAC + deployment-api.
  Root cause was NOT a code gap for most of them: `uts-shared-deployment-api` production traffic had been frozen on a
  pre-2026-07-31 revision for ~4 days — every automatic `deploy-shared.sh` cutover attempt since then had silently
  failed (same signature as `deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`,
  cross-referenced there with fresh evidence this session). Recovered via a direct `gcloud run services update-traffic`
  retry (confirmed live, serving correctly). That alone dropped the count from 44→12. Root-caused + fixed the remaining
  genuine gaps: (1) 5 legitimate-but-unregistered instrument_type values (bare `ASIAN_HANDICAP`/`OVER_UNDER`,
  `exchange_odds`/`fixed_odds`/`odds`) added to UAC's accepted-exceptions registry — instrument_types now 0
  non-canonical (was 37); (2) two real writer bugs found and fixed at the source: `market-tick-data-service`'s
  `venue_fetch.py` bypassed the already-existing `SPORTS_VENUE_FOLD` (raw `.upper()` instead of folding
  `ladbrokes_uk`/`sport888` to canonical `LADBROKES`/`BET888SPORT` first) and `market-data-processing-service`'s
  `live_workers.py` did a raw `instrument_id.split(":")[0]` that grabbed the SPORT token ("FOOTBALL") instead of the
  bookmaker for sports' `SPORT:BOOKMAKER:MARKET:...` id shape (mirrors an already-fixed sibling bug class,
  `_venue_token_from_canonical_id`, that just hadn't been applied at this one call site). Both writer fixes stop future
  pollution but do NOT retroactively fix already-captured rows — venues stays at 3 non-canonical
  (FOOTBALL/LADBROKES_UK/SPORT888) until a historical re-stamp runs; see Todos.
status: open
nature: issue
asset_group: [sports, cross-cutting]
stage: [data]
repos:
  [
    unified-api-contracts,
    market-tick-data-service,
    market-data-processing-service,
    deployment-api,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    sports,
    distinct-values,
    canonicalisation,
    venues,
    instrument-types,
    honest-coverage,
    cloud-run,
    deploy-freshness,
    writer-bug,
  ]
related:
  [
    /plans/active/issues/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md,
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/active/issues/honest_coverage_cron_run_job_sa_missing_actas_uts_prd_sa_2026_08_03.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-04"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
source: >-
  Operator live screenshot of the deployment-ui Distinct Values panel (sports asset_group), 2026-08-04 interactive
  session — "the fix may already have rolled out and not be visible yet but double check", "why is venue, instrument
  type... not canonical still", "trigger one [rollup] to refresh", "code needs fixing, uac needs fixing, everything
  deployed... manifest purged and re-rolled up".
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md,
    deployment-api/deployment_api/routes/data_status/_distinct_values.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py,
    market-data-processing-service/market_data_processing_service/app/core/live_workers.py,
  ]
---

# Sports distinct-values panel — 44→3 non-canonical (2026-08-04)

## What was live when this session started (verified via the raw endpoint, not just the screenshot)

`GET /api/data-status/distinct-values/sports`: venues 4/14 non-canonical (FOOTBALL, KALSHI, LADBROKES_UK, SPORT888),
instrument_types 37/37 (every ASIAN_HANDICAP*/OVER_UNDER*/MATCH_ODDS* variant plus bare forms and
exchange_odds/fixed_odds/odds), data_types 3/10 (ODDS/ODDS_MOVEMENT/ODDS_SNAPSHOT uppercase residue). Total 44.

## Cause 1 (the majority, 33 of 44) — production deploy frozen since 2026-07-31

`uts-shared-deployment-api` had 100% traffic pinned to revision `00374-4pd` (built 2026-07-31T18:39, pre-`uts-prd-sa`)
continuously since then. UAC's accepted-exceptions for KALSHI / ODDS-uppercase-residue / the original 30-value
ASIAN_HANDICAP/OVER_UNDER/MATCH_ODDS/SPORT set had already been correctly written and wired into deployment-api's
`_ACCEPTED_EXCEPTIONS` days ago (`uac` commit 2026-07-30, `deployment-api@7988451` 2026-08-03) — the code was right,
production just never received it. Confirmed via direct Cloud Run inspection: every revision built since 07-31
(`00375`..`00428`) was either never traffic-routed, or (from `00419` onward) was a recurring `IAM-FIX-RETEST` diagnostic
probe (`python3 -c "..."` command override, no real app) deployed repeatedly onto this SAME production service —
unrelated to this investigation, cross-referencing the cold-start deploy issue linked above (same doc this session added
fresh evidence to: the freeze wasn't a forgotten manual pin, it was that doc's cold-start bug silently no-op'ing every
automatic cutover attempt for 4 days straight). Recovered by building fresh (`deploy-shared.sh`) and manually forcing
`gcloud run services update-traffic` after the automatic cutover again silently failed — see that doc's Progress Log for
the full blow-by-blow. Confirmed live and stable afterward (multiple 200s across `/api/health` + two `distinct-values`
asset_groups).

## Cause 2 (5 values) — legitimate MTDS/MDPS output never registered as accepted-exception

Bare `ASIAN_HANDICAP`/`OVER_UNDER` (real: `canonical_ids.py::build_instrument_id` only appends the point suffix when
`outcome.point is not None` — a null point from the vendor legitimately produces the bare token) and
`exchange_odds`/`fixed_odds`/`odds` (real: the deliberate 2026-07-27 venue-based split,
`market-tick-data-service/scripts/sports/exchange_fixed_odds_fork/`, already a registered UAC `CONTRACT_REGISTRY` key —
just never added to the distinct-values accepted-exceptions set). Added to
`SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES` (`unified-api-contracts@cb545bef`).

## Cause 3 (2 real writer bugs, still-open historical residue) — venues

- `LADBROKES_UK`/`SPORT888` (real captured data: 12,164 + 18,882 = 31,046 rows, `data_type=trades`,
  `instrument_type=odds`): `market-tick-data-service/engine/orchestrator/venue_fetch.py`'s per-league sports batch
  writer computed `bm_str = bm_raw.upper()` directly — bypassing the already-existing `SPORTS_VENUE_FOLD` dict
  (`{"ladbrokes_uk": "LADBROKES", "sport888": "BET888SPORT"}`) that two SIBLING writers (`odds_api_adapter.py`,
  `odds_api_ws.py`) already correctly apply. Fixed to `SPORTS_VENUE_FOLD.get(bm_raw, bm_raw).upper()`
  (`market-tick-data-service@edfa0615`).
- `FOOTBALL` (all `attempted_failed`, 0 captured — 75 odds_movement + 69 arbitrage_opportunity + 50 odds_snapshot = 194
  rows, no real GCS objects at risk): `market-data-processing-service/app/core/live_workers.py`'s
  `_eager_preprocess_and_recover_metadata` did `input_venue = instrument_id.split(":")[0]` unconditionally — correct for
  every other asset_group's `VENUE:TYPE:SYMBOL` id shape, wrong for sports' `SPORT:BOOKMAKER:MARKET:...` shape (position
  0 is the sport). The already-existing, asset_group-aware `_venue_token_from_canonical_id` helper (built for this exact
  bug class, `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 2) was two lines away and already imported, just not
  called at this one site. Fixed (`market-data-processing-service@595a1ff`).

Both writer fixes stop NEW pollution immediately but do not touch already-written rows — the panel will keep showing
these 3 venues until either a new capture cycle produces enough correctly-stamped rows to dominate, or (for
LADBROKES_UK/SPORT888's real captured data) a historical re-stamp runs. `FOOTBALL`'s rows are all `attempted_failed`
phantoms (no real GCS content) — may simply clear on the next natural retry now that the writer is fixed; worth
confirming before scoping a re-stamp for it.

## Shipped this session

- `unified-api-contracts@cb545bef` — 5 accepted-exception values.
- `market-tick-data-service@edfa0615` — `venue_fetch.py` SPORTS_VENUE_FOLD fix.
- `market-data-processing-service@595a1ff` — `live_workers.py` `_venue_token_from_canonical_id` fix.
- `unified-trading-pm@d211c01be` — QG baseline line-pointer correction (unrelated 1-line shift from the MTDS fix).
- `uts-shared-deployment-api` — fresh build + deploy, live traffic confirmed on `uts-prd-sa` + today's code.
- Fresh honest-coverage rollup triggered (`honest-coverage-daily-launcher` execution
  `honest-coverage-daily-launcher- bcvlr`) — VM `measure-honest-coverage-20260804-110554` running at write time; verify
  `gs://central-element-323112- honest-coverage/2026-08-04/coverage.json`'s `generated_at` advanced past `09:38:21Z`
  before trusting a fresh panel read.

## Todos

- [ ] [DATA] P2. Confirm the fresh honest-coverage rollup (triggered this session, VM
      `measure-honest-coverage-     20260804-110554`) completed and re-read `/api/data-status/distinct-values/sports` —
      expect venues 3/13 non-canonical (FOOTBALL/LADBROKES_UK/SPORT888 only), instrument_types 0, data_types 0. If
      FOOTBALL has already dropped out on its own (writer fix let the previously-`attempted_failed` shards succeed on
      retry), note that and skip the FOOTBALL half of the next todo. (repo: unified-trading-pm — verification only, no
      code)
- [ ] [DATA] P2. Historical re-stamp for LADBROKES_UK→LADBROKES / SPORT888→BET888SPORT (31,046 real captured rows,
      `data_type=trades`): rename the GCS `venue=` path segment + manifest rows, mirroring the exact pattern already
      used for this fold in `market-tick-data-service/scripts/sports/restamp_sports_bookmaker_venue_2026_07_27.py`
      (2026-07-27 precedent — extend/re-run it for the residual population this session's `venue_fetch.py` fix proves
      was still being written after that script's original pass, i.e. everything captured between 2026-07-27 and today's
      fix landing). >Few-hundred-object rename — heavy-I/O HARD RULE applies, run on a VM in-region, never locally.
      Delete-safety: this is a RENAME (copy+delete of the same content under a corrected path), not a destructive delete
      of unique data — still cite `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a before the delete
      half. [OPERATOR] tag pending — confirm AO-dispatch vs human-run before executing (this doc currently
      `assigned_vm: NA`; flip to `planning` if AO should pick this up). (repo: market-tick-data-service)
- [ ] [DATA] P3. Confirm FOOTBALL's 194 `attempted_failed` rows either cleared naturally (see first todo) or, if not,
      scope why they're still failing post-fix (may be an unrelated failure cause, not just the venue mis-stamp) before
      deciding whether they need a manifest phantom-row cleanup or are a separate live bug. (repo:
      market-data-processing-service)
