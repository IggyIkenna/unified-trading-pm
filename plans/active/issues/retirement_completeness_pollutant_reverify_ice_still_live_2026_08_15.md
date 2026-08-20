---
doc_type: issue
title:
  "§8 retirement completeness re-verify: ICE still writing LIVE captured databento rows today; CBOE VIX-cash + BARCHART
  stragglers remain in manifest"
summary: >-
  Re-verification of the 2026-06-24 §8 retirement-completeness pollutant list found the catalogue leg now CLEAN (zero
  ICE rows, zero CBOE VIX-cash INDEX rows) and cefi "equity-perp singles" confirmed a non-issue, but the MTDS tick-data
  manifest leg is NOT clean: fresh same-day `captured` databento rows for ICE futures_chain/ohlcv_1m written by the live
  market-tick-data-service, contradicting every code comment claiming ICE-via-databento is fully purged. Root cause
  (live re-fetch bug vs stale re-registration) undetermined — needs a dispatch-loop trace, not a manifest read. Dormant
  (non-growing) CBOE VIX-cash + BARCHART manifest stragglers also found.
status: open
nature: issue
asset_group: [tradfi] # corrected 2026-08-19 (ag-closeout-audit cross-cutting reconciliation pass) -- was
  # [cross-cutting, tradfi]; content is 100% TradFi-databento manifest pollutants (ICE/CBOE/BARCHART) -- fork-inherited
  # the cross-cutting tag from the batch13 dispatch that spawned this investigation, not genuine cross-AG scope.
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [data-correctness, retirement-completeness, ice, databento, manifest-pollution]
related:
  [
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
author: slot-11
source:
  [
    plans/active/instruments_foundation_completeness_2026_06_24.md,
    plans/active/cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md,
  ]
depends_on: []
context_scope:
  [
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    market-tick-data-service/market_tick_data_service/adapters/umi_tick_provider.py,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_tradfi_manifest.py,
  ]
---

# What I found

Task: verify the 2026-06-24 §8 retirement-completeness pollutants (tradfi ICE whole-venue, CBOE 91 SPOT_PAIR + 5
un-deleted INDEX/VIX-cash + 9 stray VX, cefi-domain equity-perp singles) are absent on all 4 legs (code+exclusion-marker
/ GCS snapshots / manifest rows / surfaces).

**Leg 1 — code+exclusion-marker: CLEAN.** `instruments-service/.../databento/symbology.py` `_DATASET_TO_VENUE` has no
ICE entry (IFEU/IFUS removed); `expected_coverage.py` narrows `"ICE": ["ohlcv_24h"]` (Yahoo DXY only, 2026-07-13
decision); `wave_launcher.py` explicitly documents "ICE is INTENTIONALLY ABSENT... NOT backfillable today". CBOE
SPOT_PAIR mis-typing was fixed 2026-07-08 (class-"S" now decomposed into COMBO legs, not dropped/mis-typed).

**Leg 2 — live catalogue (`instruments-store-tradfi-prd-.../prod/catalog.parquet`, fresh bounded read): CLEAN.** Zero
`venue='ICE'` rows, zero `instrument_id ILIKE 'ICE:%'`. CBOE has 143 COMBO / 83 FUTURE / 10 INDEX rows — the 10 INDEX
rows are legitimate Treasury-yield indices (`^TNX`/`^TYX`/`^IRX`/`^FVX`/`US10Y`/etc.), **not** VIX-cash. Zero
`CBOE:INDEX:VIX*` rows in the catalogue. **Verdict: the original 91 SPOT_PAIR + 5 INDEX pollutants are gone from the
catalogue leg.**

**Leg 3 — cefi "equity-perp singles": NOT a pollutant — re-scoped as a non-finding.** `is_equity_perp` is a deliberate,
broadly-used feature tag (114–144 rows on BINANCE-FUTURES/BITGET-FUTURES/ASTER/OKX-SWAP/etc., 15 venues total) for
crypto-venue tokenized-equity perps, not stray "singles". The 2026-06-24 note said "if any" — confirmed: none found: no
venue carries an isolated/orphaned single equity-perp instrument outside this designed category.

**Leg 4 — MTDS tick-data manifest (`market-data-tick-tradfi-prd-.../_index/availability_index.parquet`, 367MB, fresh
bounded read): NOT CLEAN — real, live pollution found, more active than the June baseline suggested:**

1. **ICE — LIVE, ACTIVE, TODAY (not stale historical debris).** `source=databento` rows for ICE exist with
   `capture_status=captured` written **today** by the live `market-tick-data-service`:
   - `data_type=futures_chain`: 661 captured rows, `attempted_at` 2026-08-15T06:17:52–06:20:55Z
   - `data_type=ohlcv_1m`: 81 captured rows, `attempted_at` 2026-08-15T06:24:31–06:25:01Z
   - Plus 373,600 `ohlcv_1s` / 11,166 `mbp_10` / 1,483 `tbbo` / 1,489 `trades` `attempted_failed` rows via databento,
     the freshest at 2026-08-15T03:01:54Z (same day).
   - This directly contradicts every code comment asserting ICE-via-databento is "purged everywhere" / "INTENTIONALLY
     ABSENT" / "no active fetch call wired". **I could not determine from the manifest alone whether this is (a) a live
     billing-relevant re-fetch bug in MTDS's dispatch loop that still iterates ICE for futures_chain/ohlcv_1m, or (b) a
     stale re-registration of pre-2026-06-25 already-captured GCS objects (attempted_at re-stamped without a fresh
     Databento API call)** — I did not find a live ICE dispatch code path in
     `databento_adapter.py`/`venue_fetch.py`/`_tradfi_manifest_shard.py` (grepped clean), which favors (b), but the
     `service_name=market-tick-data-service` provenance (not a one-off migration script name) on today's captured rows
     does not rule out (a). **This needs a live-service trace, not a manifest read, to resolve — flagging per
     CLAUDE.md's data-pipeline-correctness HARD RULE rather than guessing.**
   - Legitimate ICE activity for comparison (NOT a pollutant): `ICE:INDEX:DXY-USD` ohlcv_24h via `source=yahoo`, 1,901
     captured / 1,552 attempted_failed — matches the sanctioned Yahoo DXY path.
2. **CBOE VIX-cash INDEX stragglers — dormant but never purged from the manifest.** 15 `empty_confirmed` rows for
   `CBOE:INDEX:VIX-USD` + 2 `empty_confirmed` rows for a legacy bare `"VIX"` instrument_id, plus a legitimate 2,293
   `captured` `futures_chain` row for `CBOE:FUTURE:VIX` (the real VX-futures chain — not a pollutant). Dedicated purge
   scripts already exist in the repo
   (`market-tick-data-service/.../scripts/delete_vix_cash_index_stragglers_2026_07_13.py`,
   `reclass_cboe_cash_index_no_provider.py`) but the 17 straggler rows are still present — either never run to
   completion or the manifest has re-accumulated since. Small blast radius (17 rows, all `empty_confirmed`, zero real
   data), so this is a cheap cleanup once someone can run/re-run the existing purge script and confirm it actually
   removes them.
3. **BARCHART — dormant legacy pollutant, zero growth.** 9,119 `empty_confirmed` rows, last `attempted_at` 2026-07-07
   (over 5 weeks stale) — matches "Barchart RETIRED" (CLAUDE.md's tradfi-databento-sourcing-ssot pointer). Not actively
   growing; a straightforward manifest-cleanup candidate, no live-fetch risk. **STALE COUNT (see 2026-08-17 Progress Log
   entry for the current live figure — 4,655, not 9,119, at re-check time; still present, still a valid purge
   candidate, but this specific number has already drifted once and will drift again — re-measure at execution time
   rather than trusting either count.)**

**Leg 5 (surfaces — catalogue/data-status/UI): NOT AUDITED this session** (task budget exhausted on the manifest finding
above, which is the more urgent one). Flagging as an open gap rather than silently skipping.

# Why it matters

The 2026-06-24 plan's own retirement-completeness DoD says "a retired thing is done only when gone from
catalogue/`/data-status`/UI, not just de-enumerated" — the catalogue leg genuinely IS clean now (real progress since
June), but the manifest leg is not just un-cleaned, it shows **fresh same-day writes** for a venue every piece of code
commentary describes as fully purged. If (a) above is true (a live re-fetch bug, not stale re-registration), this is a
data-correctness + potential-billing issue on a venue that's supposed to be off the Databento subscription entirely —
exactly the class CLAUDE.md's "Data pipeline correctness is the heartbeat" HARD RULE says must not be deadline-deferred.
I'm not certain enough to declare it a live billing hit (my evidence is manifest-side, not a traced dispatch call), so
I'm filing rather than escalating past what the evidence supports.

# Recommended decision / next steps

- [x] [DIAG] P1. Trace whether MTDS's live dispatch loop still emits an ICE `futures_chain`/`ohlcv_1m` fetch for any
      code path (scheduled backfill, on-demand cache warm, a resurrected exclude-list gap) — check today's actual
      `written_at` timestamps + object existence for the 661 `futures_chain` / 81 `ohlcv_1m` ICE manifest rows against
      the GCS objects they reference; if the objects were written today (not just re-stamped), this is live and needs
      the source dispatch bug found and fixed. Repo: market-tick-data-service. **RESOLVED — root cause is (b), stale
      re-registration, NOT a live re-fetch bug.** See "DIAG follow-up" in Progress Log below.
- [ ] [OPERATOR] P2. Run the pause-consolidator → snapshot → filter → resume manifest-cleanup procedure this plan's DoD
      calls for, to purge the ICE-databento-non-24h rows, the CBOE VIX-cash 17 stragglers, and the BARCHART 9,119 rows
      from the manifest (GCS delete/filter of a prod manifest — needs delete-safety-protocol citation per CLAUDE.md,
      hence `[OPERATOR]` — see `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`, cited 2026-08-18
      plan_reconciler; this doc's own `context_scope` did not previously carry the pointer). No live-billing urgency
      (DIAG above ruled out an active fetch loop), but the stale ICE
      objects on GCS should also be deleted, not just re-purged from the manifest, or a future rebuild will re-resurrect
      the same rows. **NOTE (2026-08-18, plan_reconciler)**: the BARCHART row count/timestamp cited here (9,119 rows)
      conflicts with this same doc's own fresher 2026-08-17 Progress Log entry below (4,655 rows, different
      timestamp) — needs a fresh live remeasurement before this todo executes, do not trust either figure as-is.
- [ ] [CODE] P3. Audit the surfaces leg (catalogue API / `/data-status` / UI) for any residual ICE/CBOE-VIX-cash/BARCHART display — not checked this session.
- [x] [DIAG] P3. Cefi "equity-perp singles" — confirmed non-issue, no follow-up needed. (Tag+priority added 2026-08-16,
      plan_reconciler, tranche=tradfi, agt-a74a6a — was missing the `[TAG] Pn.` format every other todo in this corpus
      follows; no content change.)

## Progress Log

### 2026-08-15 (slot-9) — DIAG follow-up: root cause confirmed as stale re-registration, not a live re-fetch bug

**Code-path trace (static).** ICE is genuinely excluded from every live Databento dispatch surface in the current
`market-tick-data-service` code:

- `market_tick_data_service/adapters/umi_tick_provider.py::_DATABENTO_VENUES = frozenset({"CME", "NYSE", "NASDAQ", "CBOE", "ARCA", "BATS"})`
  — **ICE is not a member.** `fetch_tick_data_for_venue` routes ICE to `_route_yahoo_tradfi` (ohlcv_24h DXY only; any
  other data_type honest-empties per that function's own docstring) — it can never reach `_route_databento` by
  venue-name match, regardless of what `data_types` were requested.
- `unified_api_contracts/registry/market_data_categories.py::_VENUE_DATA_TYPE_CAPABILITIES_RAW["ICE"] = {"ohlcv_24h": "2019-01-02"}`
  (single entry) — `get_expected_data_types_for_venue("ICE", for_batch=True)` can only ever return `["ohlcv_24h"]`. The
  default (no explicit `--data-types`) dispatch path in `venue_fetch.py::_process_venue` never requests
  `futures_chain`/`ohlcv_1m` for ICE.
- (Stale, non-blocking: `unified_api_contracts/registry/venue_mapping.py::all_databento_venues` and
  `market_tick_data_service/engine/orchestrator/venue_fetch.py::_VENUE_TO_DATA_SOURCE` both still list ICE as a
  TradFi/databento venue — harmless today since `_DATABENTO_VENUES`/`VENUE_DATA_TYPE_CAPABILITIES` gate the actual
  fetch, but worth narrowing in the P3 surfaces pass so `get_venues_for_asset_groups(["TRADFI"])` stops offering ICE as
  a Databento venue at all.)

**Live evidence (GCS object timestamps vs manifest `attempted_at`).** Ran a bounded, column-projected read of the tradfi
tick-data manifest (`_index/availability_index.parquet`, filtered to venue=ICE + data_type in {futures_chain, ohlcv_1m}
at the row-group level — not a whole-manifest load) and cross-checked the 6 freshest `captured` rows (by `attempted_at`)
against their real backing GCS objects via `gcs_describe_object` (UTL, not `gsutil`):

- All 6 freshest rows share `attempted_at`/`written_at` ≈ `2026-08-15T06:1x` (today), `pipeline_mode=batch_databento`,
  `source=databento`, `service_name=market-tick-data-service`, `date=2026-01-31` (a historical trading day).
- Their backing GCS objects
  (`.../pipeline_mode=batch_databento/.../venue=ICE/instrument_type=futures_chain/ data_type=ohlcv_1m/underlying={BRENT,COCOA,COFFEE}/margin=linear/ticks.parquet`)
  **exist and are real** — but their GCS `last_modified` is **2026-07-20** (~26 days before the manifest's
  `attempted_at`), not today. No Databento API call happened today for these shards; only the manifest ROW was rewritten
  today, pointing at a pre-existing object.

**Root cause**: `market_tick_data_service/scripts/rebuild_tradfi_manifest.py` (a corpus-rescan/rebuild utility — "scans
`gs://.../raw_tick_data/by_date/day=*/…` and emits one `ManifestWriter.add()` call per parquet found, tagged
`capture_status=CAPTURED`") ran against the tradfi bucket recently (today or shortly before, judging by the
`attempted_at` cluster) and re-discovered a set of ICE `futures_chain`/`ohlcv_1m` objects that were captured **before**
the 2026-07-13 `expected_coverage.py` narrowing decision and were **never deleted from GCS** — the narrowing decision
removed the forward-dispatch capability but did not clean up the historical objects it had already written. The rebuild
script is venue-agnostic (it discovers whatever objects exist on disk, it doesn't consult
`VENUE_DATA_TYPE_CAPABILITIES`/`EXPECTED_DATA_TYPES_BY_VENUE` to decide what's "supposed" to exist), so it faithfully
re-registered these still-present-but-retired objects with a fresh `attempted_at` = the rebuild's own run time, which is
exactly the "stale re-registration of pre-2026-06-25 already-captured GCS objects" hypothesis (b) from the original
filing — confirmed, not (a).

**Practical implication for the P2 `[OPERATOR]` cleanup**: purging the manifest ROWS alone is not sufficient — the
underlying GCS objects also need deletion (per the delete-safety protocol), or the next `rebuild_tradfi_manifest.py` run
will simply re-discover and re-stamp them again. Updated the P2 todo above accordingly. No live-billing risk: zero
Databento API calls are being issued for ICE today under the current code.

Diagnostic script used (not shipped — scratch, deleted after this session): `check_ice_manifest_objects.py`,
column-projected row-group filter + `gcs_describe_object` cross-check, run via
`scripts/dev/run-bounded-analysis.sh --mem-cap 4G` per the memory-bounding HARD RULE.

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-20**: refreshed context_scope (5 entries).

### 2026-08-17 (blocked-question backlog re-verification, answering `BLK-op-retirement_completeness_pollutant_reverify_ice_still_live-adb53e8ea708`) — status-check only, no purge executed

Per operator instruction ("check current status first — not a yes/no yet"), re-ran a fresh, read-only, bounded column
read of the live tradfi tick-data manifest (`market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`,
`unified_trading_library.read_availability_index(bucket, columns=[venue, source, instrument_id, capture_status,
data_type, instrument_type, attempted_at])`, run via `scripts/dev/run-bounded-analysis.sh --mem-cap 4G` from
`market-tick-data-service`'s venv; total manifest rows at read time: 14,472,526). No writes, no deletes — read-only
verification only, per this task's explicit scope (the actual pause-consolidator→snapshot→filter→resume purge is
NOT authorized by this check and was not run).

**CBOE VIX-cash-index stragglers: still 17 rows, UNCHANGED from the 2026-08-15 finding** — 15× `CBOE:INDEX:VIX-USD` +
2× bare `VIX`, all `capture_status=empty_confirmed`, max `attempted_at` 2026-07-24T00:54:30Z. Confirmed still present,
not cleaned up.

**BARCHART: 4,655 rows currently, NOT the 9,119 the 2026-08-15 doc cited** — all `empty_confirmed`, evenly split 931
rows each across `ohlcv_15m`/`ohlcv_1m`/`ohlcv_24h`/`tbbo`/`trades`, min/max `attempted_at` both a single stamp
`2026-05-07T14:49:23.237671Z` (not `2026-07-07` as the original doc stated — a second discrepancy). This is a real
~49% drop in row count since 2026-08-15 with no purge script run found in between to attribute it to (not
investigated further this pass — flagging as an open discrepancy, not asserting cause). Still fully dormant (a single
historical timestamp, zero growth) and still a valid, unambiguous purge candidate — just at a different measured
count than originally filed.

**ICE-via-databento (source=databento, venue=ICE) non-24h rows: 401,557 total** — 742 `captured` (661 `futures_chain`
+ 81 `ohlcv_1m`, the exact same stale-reregistered-object counts the 2026-08-15 DIAG root-caused to
`rebuild_tradfi_manifest.py` re-stamping pre-2026-07-13 GCS objects — unchanged), 9,966 `empty_confirmed`, 390,849
`attempted_failed` (spread across `mbp_10`/`ohlcv_1s`/`ohlcv_15m`/`ohlcv_24h`/`tbbo`/`trades`/`macro_result` — the
`ohlcv_1s`/`mbp_10`/`tbbo`/`trades` `attempted_failed` sub-counts are all slightly HIGHER than the 2026-08-15 snapshot,
e.g. `ohlcv_1s` 370,498 vs 373,600 originally cited is actually lower but `mbp_10` 11,167 combined vs 11,166 and
`tbbo`/`trades` are within a few rows — consistent with continued periodic `rebuild_tradfi_manifest.py` re-stamping,
not a live re-fetch; the 2026-08-15 DIAG already ruled out live-billing risk and nothing here contradicts that).
`ICE max attempted_at by source=databento: 2026-08-16T03:43:46Z` — i.e. a rebuild re-stamp ran again as recently as
yesterday, consistent with (not contradicting) the "stale re-registration keeps recurring until the GCS objects are
actually deleted" finding already on record. **Not part of this pollutant set** (found this pass, informational only):
legitimate `ICE:INDEX:DXY-USD` via `source=yahoo` (10,953 rows, the sanctioned path) and `source=fred` ICE rows (1,928
rows, `ohlcv_1d`/`yield_curve`, `empty_confirmed`) — the latter wasn't evaluated by the original 2026-08-15 doc; not
established here as a pollutant or as legitimate, just noted as an unaudited adjacent finding.

**Verdict**: the retirement-completeness pollutant condition is CONFIRMED STILL LIVE as of 2026-08-17 — none of the
three categories have been cleaned up since 2026-08-15 (BARCHART's row count dropped but the rows themselves are
still all present and still stale/dormant; CBOE VIX-cash and ICE are unchanged or larger). The purge this todo calls
for is still warranted. Per this task's scope, execution was NOT performed — a prod GCS-object delete + manifest
filter needs `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a citation and dedicated operator sign-off
on the actual run, which stays a separate, still-open follow-up (this P2 todo is intentionally left unchecked).
Answered `BLK-op-retirement_completeness_pollutant_reverify_ice_still_live-adb53e8ea708` via
`POST /api/blocked/{id}/answer` with this evidence (`from_role=operator`, `disposition=final`) — the blocked-question
escalation is resolved with current status; the underlying purge action is not.
