---
doc_type: plan
title: TradFi backfill multi-source — FX→yahoo, CBOE cash-index no-provider, ICE source-ask
summary:
  Extend the TradFi OHLCV backfill to cover FX via Yahoo Finance, CBOE cash-index (no provider path), and ICE
  (source-ask).
status: active
nature: process
asset_group: [tradfi]
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
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-22
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
drift_direction: advance-code
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
      `ohlcv_1s/1m` which were already inside the 16y L0 floor = 0 dropped, and gated derived-removal on
      `source==databento` while the 140,530 `ohlcv_15m` EU are `source=massive` = 0 matched) — so the live EU stayed
      inflated at 1,466,157 and the "EU→1,466,157 / index rows=0 / derived 15m EU=0" claim above was inaccurate
      (measured live: `ohlcv_15m` EU still 140,530, trades/tbbo/`mbp_10` out-of-rolling-window still EU). **Rewrote**
      to: (1) **reclass IN PLACE** EU→`empty_confirmed` with typed `EXPECTED_*` reasons (rows PRESERVED, never dropped —
      the SSOT-canonical honest-absence flip; supersedes the prior row-DROP design); (2) floor-clip ALL fetched
      `data_types` by DATE per billing level via UAC `earliest_allowed_start` (L0 16y `ohlcv_1s/1m`, L1 1y trades/tbbo,
      L2 1mo `mbp_10`) → `EXPECTED_OUT_OF_COVERAGE_WINDOW`; (3) reclass derived `ohlcv_15m/24h` EU (ANY non-Yahoo/FX
      source) → `EXPECTED_OUTSIDE_PROCESSING_SCOPE`; (4) VIX cash-index EU → `EXPECTED_DEPRECATED_DATA_TYPE` (0 cells —
      already absent from the manifest). **ABSOLUTE GATE: captured + `attempted_failed` + row-count UNCHANGED** (only
      EU→empty moves).

      APPLIED to live tradfi `_index` 2026-06-23 (fresh snapshot
                                                                                                                                                          `_index/snapshots/pre_floorclip_2026_06_23.parquet`). **EU 1,466,157 → 1,084,542** (reclassed 381,615 =
                                                                                                                                                          floor-clip 241,085 [trades 108,221 + tbbo 107,799 + `mbp_10` 25,065] + derived `ohlcv_15m` 140,530; VIX-index 0).
                                                                                                                                                          **GATE proof: captured 733,338 → 733,338 (delta 0), `attempted_failed` 16,358 → 16,358 (delta 0), rows 6,668,467
                                                                                                                                                          preserved.** Live re-read VERIFIED post-apply: `EXPECTED_OUT_OF_COVERAGE_WINDOW`=241,093,
                                                                                                                                                          `EXPECTED_OUTSIDE_PROCESSING_SCOPE`=140,530, remaining EU = real fetchable target (`ohlcv_1m` 313,720 +
                                                                                                                                                          `ohlcv_1s` 308,871 + in-window trades 219,144/tbbo 215,617/`mbp_10` 7,908 + `corporate_action`/earnings 9,641
                                                                                                                                                          each), **135 VX `futures_chain` captured cells preserved untouched**. Honest coverage
                                                                                                                                                          (captured/(captured+failed+EU)) 33.1% → 39.98%. — instruments-service@e9e5128.

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
- [x] ✅ [BLOCKED-CREDENTIALS] P2. **ICE data subscription — RESOLVED BY OPERATOR DESCOPE 2026-07-14** (verbatim ruling:
      "ICE isn't in MVP outside 24h bars from Yahoo Finance, so those can be purged from manifest and honest status and
      GCS data — all the other granularities. Indeed we don't have a subscription for them."). No credential ask; ICE
      keeps ONLY `ohlcv_24h` (Yahoo-DXY route, `ICE:INDEX:DXY-USD`, built 2026-07-13 per
      `issues/tradfi_ice_ohlcv_1m_no_working_fetch_path_2026_07_13.md`). The historical residue was purged 2026-07-14
      via market-tick-data-service@fffd7f82 `scripts/purge_tradfi_ice_non_24h_2026_07_14.py` — Evidence: live manifest
      reclass captured 1,620,826→1,608,382 (delta exactly −12,444) + attempted*failed 342,211→342,134 (delta exactly
      −77), all → `empty_confirmed`/`EXPECTED_NO_PROVIDER_COVERAGE`, total rows 5,090,813 UNCHANGED (row-preserving
      GATE); snapshot `_index/snapshots/pre_ice_purge_2026_07_14.parquet` (crc32c y53yfw==); 10,918 non-24h ICE GCS
      objects deleted (post-delete re-list: 0 remain; 0 ohlcv_24h objects existed/touched); consolidator cron
      `uts-prod-manifest-consolidator-market-data-tradfi-cron` paused 11:06:16Z → resumed 11:12:43Z, first post-resume
      run Completed=True 11:13:59Z. Note: the original "530,600 expected_unattempted" figure was stale — the 2026-06-23
      floor-clip had already reclassed ICE's EU to `empty_confirmed[EXPECTED*\*]`; the live anomaly purged today was
      12,444 captured + 77 attempted_failed. The 2026-07-13 "preserve, never delete" ruling for the 9 day=2025-01-06 ICE
      futures_chain snapshots was explicitly OVERRIDDEN by the operator ("delete the 9; for the dollar index we're gonna
      use the daily Yahoo Finance") — superseded banner added to
      `instruments_mtds_subset_consistency_remediation_2026_06_17.md` §ICE/CME-tail (that section now lives in
      `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md` — the 2026-06-17 doc was trimmed to a pure
      entry-point index + archived 2026-07-26).
- [x] [SCRIPT] P0. **Lifecycle catalogue OOM fix — tradfi `prod/catalog.parquet` FROZEN 6 days (write-path bug, BUG-2
      2026-06-23)** — ROOT CAUSE: the daily Cloud Run job `lifecycle-catalogue-regen-tradfi` ran but every execution
      FAILED (`0/1`) — `Terminating task because it has reached the maximum timeout of 1800 seconds` +
      `Container terminated on signal 9` (OOM) at 4/8/16/32Gi — so the monotonic-guard KEPT the last-good catalogue
      (mtime 2026-06-17) and the v2 expected-universe enumerator cross-joined a STALE could-exist universe (the
      `DP_CATALOG_NOT_RUNNING` alert was REAL). Crash site: `build_instrument_catalogue.py::_iter_by_date_snapshots`
      used `ThreadPoolExecutor.map`, which eagerly downloaded + buffered ALL 11.6k–13.5k tradfi `by_date` parquets in
      memory at once. FIX: `_bounded_parallel_load` sliding-window (≤`max_workers`=16 frames in flight, each yielded
      into the streaming aggregate fold + dropped before the next) → peak memory O(16 frames) not O(13.5k); applied to
      all 3 `_iter_*` sites + 3 regression tests.

      tf: tradfi job 32Gi→16Gi/cpu4 (band-aid removed — memory now bounded) + `timeout_seconds` 1800→3600 (slow
                                                                                                                                                          13.5k-blob GCS read). — instruments-service@b84cc4f (`scripts/build_instrument_catalogue.py` +
                                                                                                                                                          `tests/unit/scripts/test_build_instrument_catalogue.py`, QG-green +4 regression tests) +
                                                                                                                                                          deployment-service@9b74416 (`terraform/gcp/lifecycle_catalogue_scheduler.tf`); live tradfi Cloud Run job updated
                                                                                                                                                          to 16Gi/cpu4/`task-timeout`=3600 via gcloud (was 32Gi); IS image rebuilding (Cloud Build `c0b6772a`) so `:latest`
                                                                                                                                                          bakes the fix. OPS (final verification, 2026-06-23): once the image build lands, re-run
                                                                                                                                                          `lifecycle-catalogue-regen-tradfi` on the fixed image and confirm it COMPLETES without OOM + writes a fresh
                                                                                                                                                          `prod/catalog.parquet` mtime=today (evidence appended in the `data_pipeline_hardening` Progress Log). Other 4 AGs
                                                                                                                                                          were already GREEN.

## Codex SSOT updates

- `/codex/02-data/tradfi-databento-sourcing-ssot.md` — add the multi-source venue→source matrix + the "Massive has NO
  ICE prefix" finding (the lib comment "databento is capable for every tradfi OHLCV venue" is wrong for ICE; corrected
  by this plan).

## Progress Log

- **2026-06-23 — BUG 3 DP_VM_GONE_NO_CAPTURE root-caused + fixed (deployment-service@04942d5).** ~26 GONE-with-0-capture
  tradfi VMs were the stale `launch_tradfi_shard` bolt-on in `launch-cefi-sharded-backfill.sh{,-aws.sh}` launching
  `--venues CME-FUTURES|CBOE-VIX-*` (Tardis tags, NOT canonical TRADFI venues `{NASDAQ,NYSE,CME,ICE,CBOE}`) → MTDS "No
  active venues" → 0-row self-delete. FIX: deleted the block (now CeFi-only) + republished GCS scripts; canonical
  Databento launchers (`VM_TASK=mtds-backfill`/`VM_SOURCE=databento`) positively capture (es-2025 51,087 rows). QG
  green.
- **2026-06-23 — VIX cash-index DELETE + Databento rolling-history floor-clip (operator decision;
  instruments-service@814b14a + @e9e5128 + @b84cc4f).** Supersedes the reclass-to-`empty_confirmed`. (A)
  `_enumerate_v2_tradfi` floor-clip + `_is_vix_cash_index` drop; (B) row-preserving manifest reclass (snapshot+GATE —
  captured/attempted_failed/rows UNCHANGED, EU 1,466,157→1,084,542 via floor-clip+derived reclass); (C) GCS delete of
  1,621 VIX cash-index objects via `gcs_delete_object`. VX-futures-vs-VIX sanity PASSED (corr 0.95-0.98, steady ~1.7-2.1
  contango basis on 2026-04-14/28/30); 135 VX futures_chain captured cells preserved. Honest coverage 33.1%→39.98%.
  SSOT-aligned with `/codex/02-data/tradfi-databento-sourcing-ssot.md` (databento XCBF.PITCH for VX; VIX cash index has
  no provider).

### VIX 15m bare-index stragglers of the 2026-06-23 deletion — VERIFY-THEN-DELETE — DONE (2026-07-13)

> Operator ruling 2026-07-13: ~20 `day=/data_type=ohlcv_15m/indices/CBOE|bare/...VIX...` objects survived the 2026-06-23
> VIX-cash-index deletion (`delete_vix_cash_index_gcs_objects_2026_06_23.py`) — verify BOTH premises (genuinely VIX cash
> index, not VX futures; VX-futures Databento coverage exists with no holes) before deleting.

**Why they survived the 2026-06-23 sweep**: that script globbed the canonical hive shape
(`venue=CBOE/instrument_type=index/...`, per its own docstring "instrument_type=index at venue=CBOE"). These ~20 objects
are a DIFFERENT, non-hive "LEGACY shape D" layout
(`raw_tick_data/by_date/day={D}/data_type=ohlcv_15m/indices/CBOE[/CBOE:INDEX:VIX-USD].parquet` — no `venue=`/
`instrument_type=` keys at all), so the 2026-06-23 sweep's glob never matched them — a path-shape miss, not a deliberate
exclusion.

**Live-verified count**: 20 objects across 13 distinct dates (2025-01-02/03/06/07/08/09/10, 2025-11-03/04/05/06/07/10) —
2 path-shape variants (`indices/CBOE/{file}` and bare `indices/{file}`) on 7 of the 13 dates, 1 variant on the other 6.

**(1) Content verdict — VIX CASH INDEX, confirmed, not VX futures.** Read all 20 files (footer+content, not sampled):
every file carries `instrument_key`/filename `CBOE:INDEX:VIX-USD` (18/20 rows have the explicit `instrument_key` column;
the 2 that don't carry the identical filename stem, unambiguous), close values 15-22 (typical VIX-index level),
**`volume=0.0` on every single row across all 20 files** (an index is never a tradable instrument with real volume —
this alone rules out VX futures, which trade with real volume). 1,006 total rows. **PASS.**

**(2) VX-futures Databento coverage — confirmed, zero holes.** Live tradfi manifest query (not the 2026-06-23 snapshot's
"135 preserved" claim re-asserted — re-derived fresh 2026-07-13): venue=CBOE, instrument_type=futures_chain,
data_type=ohlcv_1m, capture_status=captured → **1,434 captured cells** (2,868 incl. the `ohlcv_1s` sibling), 100%
source=databento/pipeline_mode=batch_databento, date range **2020-06-01 .. 2026-07-10** (1,306 distinct captured dates).
Explicitly checked all 13 straggler dates individually against this set — **13/13 covered, 0 holes.** **PASS.**

**Both premises hold → executed the snapshot-first delete**, citing "stragglers of the 2026-06-23 VIX-cash ruling
(`tradfi_multisource_backfill_2026_06_22.md` §VIX) + operator re-confirmation 2026-07-13":
market-tick-data-service@(uncommitted this session) `scripts/delete_vix_cash_index_stragglers_2026_07_13.py`. Snapshot
`_index/snapshots/pre_vix_straggler_delete_2026_07_13.parquet` written before any change. Manifest reclass (row-
preserving, GATE-checked): the 13 matching manifest cells
(`venue=CBOE, instrument_type=index, data_type=ohlcv_15m, instrument_id=CBOE:INDEX:VIX-USD`, one per straggler date)
`captured` → `empty_confirmed` / `error_reason=EXPECTED_DEPRECATED_DATA_TYPE` — the SAME reason string
`instruments-service/scripts/correct_tradfi_universe_floor_clip_and_vix_index.py` already uses for every other
VIX-cash-index cell, so these converge on the sanctioned taxonomy instead of staying anomalous `captured` outliers.
**GATE verified**: total rows unchanged (5,089,639 → 5,089,639), `captured` delta exactly −13 (1,620,839 → 1,620,826).
Then the 20 GCS objects deleted (only after the manifest reclass landed). **Independently re-verified post-apply**: live
re-list of the 13 date-prefixes returns 0 remaining objects; live re-read of the 13 manifest cells confirms
`empty_confirmed`/`EXPECTED_DEPRECATED_DATA_TYPE` on all 13.

- [x] ✅ [DATA] P2. **VIX 15m bare-index stragglers — verify-then-delete — DONE 2026-07-13.** Both gating premises
      independently re-verified (content = VIX cash index not VX futures; VX-futures Databento coverage 1,434 captured
      cells 2020-06-01→2026-07-10, 0 holes over the 13 straggler dates) → deleted 20 GCS objects (snapshot-first) +
      reclassed 13 manifest cells captured→empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE (GATE: rows unchanged, captured
      delta=-13 exact). — market-tick-data-service `scripts/delete_vix_cash_index_stragglers_2026_07_13.py`

## Temporary states + their canonical follow-up plans

- The CBOE-reclass + wave-launcher map are landed; the FX backfill drain + ICE credential-ask are the open todos above.
- VIX cash-index DELETE + Databento floor-clip landed 2026-06-23 (instruments-service@814b14a); GCS-object delete
  `--apply` completed 2026-06-23 (1,621 objects deleted, exit 0); non-hive-shape stragglers verify-then-deleted
  2026-07-13 (20 objects, 0 remaining). The enumerator change is live for future universe seeds — no follow-up needed.
- VIX 15m bare-index stragglers (a different, non-hive path shape the 2026-06-23 sweep's glob missed)
  verify-then-deleted 2026-07-13 — see §VIX above. No further stragglers expected (live-verified 0 remaining objects at
  that shape).
