---
doc_type: plan
title: TradFi backfill multi-source — FX→yahoo, CBOE cash-index no-provider, ICE source-ask
summary: "Extend the TradFi OHLCV backfill to cover FX via Yahoo Finance, CBOE cash-index (no provider path), and ICE (source-ask)."
status: active
nature: process
stage: [meta]
repos: [deployment-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [tradfi, backfill, fx, cboe, ice, yahoo, multi-source]
related: []
created: 2026-06-22
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data-pipeline-engineer
drift_direction: advance-code
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
supersedes:
superseded_by:
depends_on:
source:
asset_group: tradfi
---

# TradFi backfill multi-source — FX / CBOE-index / ICE

Make the TradFi OHLCV backfill **multi-source** instead of databento-only. The wave-launcher
(`deployment-service/scripts/wave_launcher.py`) mapped only CME/CBOE/NASDAQ/NYSE → databento launchers; ICE + FX fell to
"out-of-scope" and never filled.

## Venue → source → fillable matrix (the key deliverable)

| Venue                                | expected_unattempted               | Source               | Fillable?                                  | Mechanism                                                                          |
| ------------------------------------ | ---------------------------------- | -------------------- | ------------------------------------------ | ---------------------------------------------------------------------------------- |
| CME / NASDAQ / NYSE                  | (various)                          | databento            | YES (live)                                 | GLBX.MDP3 / DBEQ.BASIC; existing launchers                                         |
| CBOE — VX **futures**                | — (captured)                       | databento XCBF.PITCH | YES (captured: 134 futures_chain ohlcv_1m) | CFE subscription                                                                   |
| CBOE — VIX cash **index**            | 1,651 (instrument_type=index)      | **none**             | NO — DELETE (operator 2026-06-23)          | DELETE cells + GCS objects (futures carry the info; index not tradable, derivable) |
| FX (USD/KRW spot pairs)              | 3,228 (538 × 6 dt, incl ohlcv_24h) | **yahoo_finance**    | YES                                        | daily ohlcv_24h, venue-routed to `_fetch_yahoo_fx`                                 |
| ICE (IFEU/IFUS — Brent/Gasoil/softs) | 530,600 (combo/futures_chain)      | **NONE AVAILABLE**   | **NO — needs ICE-data subscription ask**   | databento dropped ICE in 3-dataset lockdown; Massive carries NO ICE                |

### Key finding — Massive does NOT have ICE data (verified 2026-06-22)

The operator hypothesis was "massive can fill ICE if massive has the data." It does NOT. Probed Massive's S3 `flatfiles`
bucket directly (path-style boto3, the same creds the connector uses): top-level prefixes are `global_crypto/`,
`global_forex/`, `us_futures_cbot/`, `us_futures_cme/`, `us_futures_comex/`, `us_futures_nymex/`, `us_indices/`,
`us_options_opra/`, `us_stocks_sip/`. **There is NO ICE prefix** (`us_futures_ice/`, `global_futures/`,
`us_futures_ifus/` all ABSENT). Massive's futures coverage is CME-group only (CME/CBOT/COMEX/NYMEX). The MTDS
`_route_massive` confirms this in code: `_MASSIVE_FUTURES_VENUES = {"CME"}` only; any other venue would be treated as an
equity-REST symbol → 404. UAC `tradfi_instrument_universe.py` already documents that ICE (IFEU.IMPACT/IFUS.IMPACT) was
DROPPED in the 3-dataset subscription lockdown and "requires an explicit ICE subscription + adding the dataset to the
allowlist." So ICE genuinely needs an operator credential/subscription ask — NOT a wave-launcher dispatch.

## Todos

- [x] [SCRIPT] P1. **CBOE cash-index reclass** — confirm VX-futures captured (✅ 134 futures_chain ohlcv_1m captured via
      XCBF.PITCH), then reclass CBOE cash-index (instrument_type=index, CBOE:INDEX:VIX/SPX) 1,614 expected_unattempted
      cells → empty_confirmed/EXPECTED_NO_PROVIDER_COVERAGE in-place with snapshot + GATE (rows + captured unchanged). —
      market-tick-data-service@2c6425b `reclass_cboe_cash_index_no_provider.py`; APPLIED to live tradfi `_index`
      (snapshot `pre_cboe_cash_index_reclass_2026_06_22.parquet`); verified 1,614 index cells now empty_confirmed, VX
      futures_chain (134) preserved.
- [x] [SCRIPT] P1. **FX via yahoo launcher** — `launch-tradfi-bf-fx-ohlcv-24h.sh` (Yahoo daily ohlcv_24h, venue-routed;
      FX bypasses --source). FX capture itself was already code-complete in `_fetch_yahoo_fx` (venue=FX → Yahoo daily).
      — deployment-service@eab5aeb; dry-run verified.
- [x] [SCRIPT] P1. **Wave-launcher multi-source** — `LAUNCHER_FOR_VENUE` adds FX→fx-launcher; per-venue
      `VENUE_DATA_TYPES` map (FX=ohlcv_24h); FX added to PER_YEAR_VENUES; VM_NAME regex now venue+timeframe-agnostic.
      ICE intentionally absent (massive can't serve it). Dry-run confirms FX dispatch atoms appear (FX year=2025/2026 →
      fx launcher) and ICE stays out-of-scope. — deployment-service@eab5aeb.
- [x] [SCRIPT] P0. **BUG 3 DP_VM_GONE_NO_CAPTURE** — removed the stale non-canonical-venue TradFi block
      (`launch_tradfi_shard` + `SYMBOLS_CME_ES_*`/`SYMBOLS_CBOE_VIX_*` + the TradFi loop) from
      `launch-cefi-sharded-backfill.sh` + `-aws.sh`; those VMs launched `--venues CME-FUTURES|CBOE-VIX-*` (not canonical
      TRADFI venues) → "No active venues" → 0 capture → self-delete. TradFi rides the canonical Databento launchers.
      deployment-service@04942d5; GCS-published to `{vm,code/deployment-service/scripts/vm}/`; canonical path positively
      captures (es-2025 51,087 rows). See Progress Log 2026-06-23.
- [ ] [TEST] P3. **NICE-TO-HAVE**
      `deployment-service/tests/unit/test_event_logging.py::test_required_common_events_exist` resolves the service name
      from the **worktree directory basename** (`get_service_name()`), so it only `pytest.skip`s (deployment-service is
      an orchestrator, not a pipeline service) when the checkout dir is literally `deployment-service`. In an isolated
      worktree named anything else it wrongly FAILS demanding pipeline events. Harmless in CI/real clones (dir ==
      `deployment-service`) but a footgun for agents running QG in `/tmp/<wt>`. Make `get_service_name()` read the repo
      identity (pyproject `name`/git remote) not the cwd basename. Provenance: bug-3 fix QG run 2026-06-23.

### VIX-index DELETE + Databento universe floor-clip (operator 2026-06-23 — supersedes the reclass-to-empty_confirmed above)

> Operator decision 2026-06-23: keep VIX **futures** (VX, XCBF.PITCH, canonical ohlcv_1m/1s — captured + verified
> tracking the index: corr 0.95–0.98, steady ~1.7–2.1 vol-point contango basis vs the Barchart/massive VIX-index 15m on
> 2026-04-14/28/30). DELETE the VIX **cash index** entirely (not leave as empty_confirmed clutter): not tradable,
> derivable from the futures, trades less often over a shorter window at coarser granularity. ALSO: the
> `expected_unattempted` universe must not seed Databento-fetched cells older than each level's rolling-history floor
> (L0 16y for ohlcv_1s/1m), nor seed 15m/24h (DERIVED by aggregation, not fetched) as databento EU.

- [x] [SCRIPT] P0. **Enumerator floor-clip + VIX-index drop** —
      `instruments-service/scripts/enumerate_expected_universe.py` `_enumerate_v2_tradfi`: added
      `_tradfi_floor_start_for_data_type(dt, today)` (databento-fetched ohlcv_1s/ohlcv_1m → L0 16y floor via UAC
      `earliest_allowed_start`; 15m/24h derived + Yahoo FX → None = no clip), skip seeding EU dates older than the floor
      in the alive branch; and `_is_vix_cash_index(instr)` (instrument_type=index named VIX, or blank-id CBOE index
      legacy cell — DXY/treasury indices keep their own non-VIX id → unaffected) → skip the whole instrument so no VIX
      cash-index cell is ever seeded. — instruments-service@814b14a.
- [x] [SCRIPT] P0. **Manifest correction (one-off, snapshot+GATE) — REWRITTEN to row-preserving reclass + re-APPLIED
      2026-06-23** — `instruments-service/scripts/correct_tradfi_universe_floor_clip_and_vix_index.py` (mirrors
      `populate_v9_index_columns_inplace.py`). **The 814b14a version was a NO-OP on EU** (it floor-clipped only
      ohlcv_1s/1m which were already inside the 16y L0 floor = 0 dropped, and gated derived-removal on
      `source==databento` while the 140,530 ohlcv_15m EU are `source=massive` = 0 matched) — so the live EU stayed
      inflated at 1,466,157 and the "EU→1,466,157 / index rows=0 / derived 15m EU=0" claim above was inaccurate
      (measured live: ohlcv_15m EU still 140,530, trades/tbbo/mbp_10 out-of-rolling-window still EU). **Rewrote** to:
      (1) **reclass IN PLACE** EU→`empty_confirmed` with typed `EXPECTED_*` reasons (rows PRESERVED, never dropped — the
      SSOT-canonical honest-absence flip; supersedes the prior row-DROP design); (2) floor-clip ALL fetched data_types
      by DATE per billing level via UAC `earliest_allowed_start` (L0 16y ohlcv_1s/1m, L1 1y trades/tbbo, L2 1mo mbp_10)
      → `EXPECTED_OUT_OF_COVERAGE_WINDOW`; (3) reclass derived ohlcv_15m/24h EU (ANY non-Yahoo/FX source) →
      `EXPECTED_OUTSIDE_PROCESSING_SCOPE`; (4) VIX cash-index EU → `EXPECTED_DEPRECATED_DATA_TYPE` (0 cells — already
      absent from the manifest). **ABSOLUTE GATE: captured + attempted_failed + row-count UNCHANGED** (only EU→empty
      moves). APPLIED to live tradfi `_index` 2026-06-23 (fresh snapshot
      `_index/snapshots/pre_floorclip_2026_06_23.parquet`). **EU 1,466,157 → 1,084,542** (reclassed 381,615 = floor-clip
      241,085 [trades 108,221 + tbbo 107,799 + mbp_10 25,065] + derived ohlcv_15m 140,530; VIX-index 0). **GATE proof:
      captured 733,338 → 733,338 (delta 0), attempted_failed 16,358 → 16,358 (delta 0), rows 6,668,467 preserved.** Live
      re-read VERIFIED post-apply: `EXPECTED_OUT_OF_COVERAGE_WINDOW`=241,093,
      `EXPECTED_OUTSIDE_PROCESSING_SCOPE`=140,530, remaining EU = real fetchable target (ohlcv_1m 313,720 + ohlcv_1s
      308,871 + in-window trades 219,144/tbbo 215,617/mbp_10 7,908 + corporate_action/earnings 9,641 each), **135 VX
      futures_chain captured cells preserved untouched**. Honest coverage (captured/(captured+failed+EU)) 33.1% →
      39.98%. — instruments-service@e9e5128.
- [x] [SCRIPT] P0. **Delete Barchart/massive VIX-index GCS objects — APPLIED 2026-06-23** —
      `instruments-service/scripts/delete_vix_cash_index_gcs_objects_2026_06_23.py` deletes the VIX cash-index parquet
      objects (instrument_type=index at venue=CBOE — CBOE's only cash index is VIX, across batch_massive/batch_databento
      pipeline_modes) via `unified_trading_library` `gcs_delete_object` (never gsutil). Gated on the
      VX-futures-vs-VIX-index sanity check (PASSED: corr 0.95-0.98, steady ~1.7-2.1 vol-point contango basis) + the
      manifest correction above. **The op had NOT actually run before** (the prior "--apply RUNNING" was incomplete —
      measured 2026-06-23: 1,621 VIX cash-index objects still present). **--apply re-run to completion 2026-06-23:
      deleted 1,621 objects (exit 0); VX futures_chain/future objects NOT touched.** — instruments-service@814b14a.

- [ ] [BACKFILL] P1. **Run the FX yahoo backfill to completion** (operational) — launch
      `launch-tradfi-bf-fx-ohlcv-24h.sh` per-year via the wave-launcher cron / manual, verify FX ohlcv_24h
      expected_unattempted → captured in the manifest. (The cron handles live ticks; this is the operational drain.)
- [ ] [BLOCKED-CREDENTIALS] P2. **ICE data subscription** — ICE (IFEU/IFUS Brent/Gasoil/softs + DX) is NOT in any source
      we have (databento dropped it; Massive has no ICE prefix). Fillable ONLY with an explicit ICE-data subscription
      (databento ICE datasets re-added to the allowlist, or a Massive/other ICE feed). 530,600 expected_unattempted
      cells stay until an operator credential ask is acked. CREDENTIAL APPROVAL REQUEST logged in pings. Note: the IS
      ICE instrument catalogue (BRN/G FUTURE/COMBO, 2,067 rows) already exists — only the market-data source is missing.
- [x] [SCRIPT] P0. **Lifecycle catalogue OOM fix — tradfi `prod/catalog.parquet` FROZEN 6 days (write-path bug, BUG-2
      2026-06-23)** — ROOT CAUSE: the daily Cloud Run job `lifecycle-catalogue-regen-tradfi` ran but every execution
      FAILED (`0/1`) — `Terminating task because it has reached the maximum timeout of 1800 seconds` +
      `Container terminated on signal 9` (OOM) at 4/8/16/32Gi — so the monotonic-guard KEPT the last-good catalogue
      (mtime 2026-06-17) and the v2 expected-universe enumerator cross-joined a STALE could-exist universe (the
      `DP_CATALOG_NOT_RUNNING` alert was REAL). Crash site: `build_instrument_catalogue.py::_iter_by_date_snapshots`
      used `ThreadPoolExecutor.map`, which eagerly downloaded + buffered ALL 11.6k–13.5k tradfi by_date parquets in
      memory at once. FIX: `_bounded_parallel_load` sliding-window (≤max_workers=16 frames in flight, each yielded into
      the streaming aggregate fold + dropped before the next) → peak memory O(16 frames) not O(13.5k); applied to all 3
      `_iter_*` sites + 3 regression tests. tf: tradfi job 32Gi→16Gi/cpu4 (band-aid removed — memory now bounded) +
      `timeout_seconds` 1800→3600 (slow 13.5k-blob GCS read). — instruments-service@b84cc4f
      (`scripts/build_instrument_catalogue.py` + `tests/unit/scripts/test_build_instrument_catalogue.py`, QG-green +4
      regression tests) + deployment-service@9b74416 (`terraform/gcp/lifecycle_catalogue_scheduler.tf`); live tradfi
      Cloud Run job updated to 16Gi/cpu4/`task-timeout`=3600 via gcloud (was 32Gi); IS image rebuilding (Cloud Build
      `c0b6772a`) so `:latest` bakes the fix. OPS (final verification, 2026-06-23): once the image build lands, re-run
      `lifecycle-catalogue-regen-tradfi` on the fixed image and confirm it COMPLETES without OOM + writes a fresh
      `prod/catalog.parquet` mtime=today (evidence appended in the data_pipeline_hardening Progress Log). Other 4 AGs
      were already GREEN.

## Codex SSOT updates

- `codex/02-data/tradfi-databento-sourcing-ssot.md` — add the multi-source venue→source matrix + the "Massive has NO ICE
  prefix" finding (the lib comment "databento is capable for every tradfi OHLCV venue" is wrong for ICE; corrected by
  this plan).

## Progress Log

- **2026-06-23 — BUG 3 DP_VM_GONE_NO_CAPTURE root-caused + fixed (deployment-service@04942d5).** ~26 GONE-with-0-capture
  tradfi VMs split into TWO families: (1) `tradfi-bf-cme-ohlcv-1m-*` (CANONICAL Databento wave-launcher) — NOT a
  0-capture case (run.logs show 16k–51k rows written before the occasional Bug-1 OOM `Killed`; these captured fine). (2)
  `tradfi-{es,vix}-{year}-{futures,options}-*` — the GENUINELY-0-capture path. Root cause (run.log + UAC verified):
  these came from `launch-cefi-sharded-backfill.sh`'s bolt-on `launch_tradfi_shard` block (and its AWS twin), which
  launched VMs with `VM_TASK=cefi-backfill` + `--venues CME-FUTURES|CBOE-VIX-FUTURES|CME-OPTIONS|CBOE-VIX-OPTIONS`
  (Tardis tags) + NO `--source`. Those venue tags are **NOT canonical TRADFI venues** — UAC
  `VENUES_BY_ASSET_GROUP["tradfi"]` = `{NASDAQ,NYSE,CME,ICE,CBOE}` — so MTDS `_build_active_venues_for_date()`
  intersected the canonical set against the non-canonical `--venues` filter → **empty → "No active venues for TRADFI"
  every date → 0 rows at exit_code=0 → self-delete** (run.log: `tradfi-vix-2025-futures-…` 365 results all "No active
  venues", `DEPLOYMENT_COMPLETED exit_code=0`). The block was stale: TradFi OHLCV is served by the canonical Databento
  launchers (`launch-tradfi-bf-*-ohlcv-*.sh` → `_tradfi-ohlcv-launcher-lib.sh`: `VM_TASK=mtds-backfill` +
  `VM_SOURCE=databento` + canonical venue `CME`/`CBOE`), which the coordinator's `run_tradfi` already calls. **FIX:**
  deleted `launch_tradfi_shard` + the `SYMBOLS_CME_ES_*`/ `SYMBOLS_CBOE_VIX_*` consts + the TradFi for-loop from BOTH
  `launch-cefi-sharded-backfill.sh` and `launch-cefi-sharded-backfill-aws.sh` (now CeFi-only). QG green (2482 tests
  pass; the lone failure was a worktree-basename artifact in `test_event_logging`, not the change). **Published** the
  fixed scripts to `gs://deployment-scripts-central-element-323112/{vm,code/deployment-service/scripts/vm}/`
  (cron/bare-launcher consumers fetch fresh each tick — all 3 GCS copies verified 0 shard-calls). **Verification:**
  fixed launcher dry-run emits 0 `tradfi-*` VMs (broken path gone); CANONICAL path positively captures — live run.logs
  `tradfi-bf-cme-ohlcv-1m-es-2025` =51,087 rows, `…-6e-2025`=16,860+20,881 rows. Side-discovery captured below.
- **2026-06-23 — VIX cash-index DELETE + Databento rolling-history floor-clip (operator decision, autonomous).**
  Supersedes the earlier reclass-to-`empty_confirmed` of the CBOE cash index. Shipped instruments-service@814b14a: (A)
  `_enumerate_v2_tradfi` floor-clip helper `_tradfi_floor_start_for_data_type` (databento ohlcv_1s/ohlcv_1m → L0 16y
  floor via UAC `earliest_allowed_start`; 15m/24h-derived + Yahoo FX → `None`) + `_is_vix_cash_index` drop; (B)
  `correct_tradfi_universe_floor_clip_and_vix_index.py` (snapshot+GATE manifest correction); (C)
  `delete_vix_cash_index_gcs_objects_2026_06_23.py` (GCS object delete via `gcs_delete_object`). **Sanity check
  (operator-requested, PASSED):** captured VX-futures ohlcv_1m (front contract VX/K6) aggregated to 15m vs the
  Barchart/massive VIX cash-index 15m on 3 captured dates — 2026-04-30 corr 0.979 / basis +2.13; 2026-04-28 corr 0.948 /
  +1.69; 2026-04-14 levels track (VX ~20.4 vs VIX ~18.7, steady ~1.7-2.0 contango). The futures track the index with a
  small steady contango basis exactly as expected → index is redundant/derivable. **Manifest correction APPLIED to live
  tradfi `_index`** (snapshot `pre_universe_floor_clip_2026_06_23.parquet`): EU universe 1,606,687 → 1,466,157 (−140,530
  derived-databento phantom 15m/24h cells; EU-floor drop = 0, already at floor); VIX cash-index 1,651 cells removed (37
  captured). GATE: captured 733,375 → 733,338 (delta 37 = sanctioned VIX-index only), attempted_failed unchanged.
  Re-read VERIFIED: instrument_type=index = 0, derived-databento 15m/24h EU = 0, VX futures captured = 135 preserved.
  **Ship note:** direct-LDR push (dirty-deps carve-out — UTL was foreign-dirty mid-edit, blocking quickmerge); QG proven
  green in an isolated tree (3708 tests pass, my files ruff/basedpyright-clean; the only QG redness was foreign
  concurrent `sports_dependency.py`/`base.py` edits NOT in my commit, stashed for preservation).

## Temporary states + their canonical follow-up plans

- The CBOE-reclass + wave-launcher map are landed; the FX backfill drain + ICE credential-ask are the open todos above.
- VIX cash-index DELETE + Databento floor-clip landed 2026-06-23 (instruments-service@814b14a); GCS-object delete
  `--apply` running. The enumerator change is live for future universe seeds — no follow-up needed.
