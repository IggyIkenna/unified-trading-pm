---
doc_type: issue
title: >-
  Window-scoped honest-coverage measurement (OKX/BINANCE/BYBIT, 2024-01-01→present) confirms coverage NOT complete —
  48.90% overall, and the trailing 90d is WORSE (24.70%) than the full-window average
summary: >-
  cefi_satellite_ao_dispatch_batch11 todo 10 ran the blocking-prerequisite window-scoped honest-coverage measurement the
  2-year ML_DIRECTIONAL_CONTINUOUS config-grid backtest (cefi_ml_directional_continuous_live_2026_06_20.md) needs before
  it can be scheduled. Result: 48.90% reachable coverage for OKX-SPOT/-SWAP/-FUTURES + BINANCE-SPOT/-FUTURES + BYBIT
  over 2024-01-01→present (2,980,916 scoped manifest rows) — materially below complete, confirming and quantifying the
  operator's 2026-08-08 "not confirmed" finding. The gap concentrates almost entirely in `trades` and `book_snapshot_5`
  (10.6%-46.3% coverage per venue) vs. `derivative_ticker`/`liquidations` (58%-97%) — exactly the two data_types the
  grid backtest needs for LOB/trade-level fidelity. Most concerning: the trailing ~90 days (>= 2026-05-11) measure WORSE
  than the full-window average (24.70% vs 48.90% overall; OKX-SPOT 12.21%, BINANCE-SPOT 13.13%, BYBIT 18.66%) —
  backwards from what a live-capital gate needs, and a signal this may be an ongoing live/near-real-time capture health
  problem for these venue+data_type combos, not just a historical-backfill gap that the unrelated from-2019
  chronological backfill (cefi_track2_coverage_backfill_checkpoints_2026_07_25.md, currently at ~10.7% through,
  last_completed_date=2019-10-21) will eventually fix by reaching 2024-2026. Also found: `futures_chain` shows 0%
  coverage for BINANCE-FUTURES (228 attempted_failed) and BYBIT (1251 attempted_failed) — every attempt failed, not an
  absence gap, suggesting a distinct correctness bug rather than a coverage gap.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    cefi,
    honest-coverage,
    data-pipeline,
    backfill,
    trades,
    book_snapshot_5,
    futures_chain,
    live-capital-gate,
    okx,
    binance,
    bybit,
  ]
related:
  [
    /plans/active/cefi_ml_directional_continuous_live_2026_06_20.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /codex/02-data/honest-coverage-model.md,
    /plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md,
    /plans/active/issues/cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md,
    /plans/active/issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md,
    /plans/active/issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md,
  ]
context_scope:
  [
    market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py,
    instruments-service/scripts/measure_honest_coverage.py,
    /codex/02-data/honest-coverage-model.md,
  ]
created: "2026-08-09"
author: slot-5
priority: P1
parent_epic: cefi_master
source: >-
  Discovered 2026-08-09 executing cefi_satellite_ao_dispatch_batch11 todo 10 (window-scoped honest-coverage measurement,
  itself extracted from cefi_ml_directional_continuous_live_2026_06_20.md line 180). Measured by reusing
  instruments-service/scripts/measure_honest_coverage.py's bounded, column-pruned manifest reader (_read_manifest +
  _count_statuses) — a single read of the cefi availability-index parquet, filtered in-memory to the target venue set +
  date window; no new whole-corpus GCS walk.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: fix
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
resolved_by:
locked_by:
depends_on: []
---

# Window-scoped cefi honest-coverage gap — OKX/BINANCE/BYBIT, 2024-2026

## What I found

Filtered the cefi availability-index manifest (10,537,552 total rows) to venue in {OKX-SPOT, OKX-SWAP, OKX-FUTURES,
BINANCE-SPOT, BINANCE-FUTURES, BYBIT} and date >= 2024-01-01 (2,980,916 scoped rows).

**Overall**: captured=1,295,524 / attempted_failed=94,706 / expected_unattempted=1,258,908 / empty_confirmed=331,778 →
**coverage_pct = 48.90%** (reachable formula: captured / (captured + attempted_failed + expected_unattempted)).

**Per venue**: OKX-FUTURES 80.51%, OKX-SWAP 64.18%, BINANCE-FUTURES 57.46%, BINANCE-SPOT 45.25%, BYBIT 35.99%,
**OKX-SPOT 29.34%** (worst).

**Per (venue, data_type)** — the gap is concentrated:

| venue           | data_type         | coverage_pct                                                                      |
| --------------- | ----------------- | --------------------------------------------------------------------------------- |
| BINANCE-FUTURES | trades            | 12.09%                                                                            |
| BYBIT           | trades            | 10.58%                                                                            |
| BYBIT           | book_snapshot_5   | 15.90%                                                                            |
| BINANCE-FUTURES | book_snapshot_5   | 24.75%                                                                            |
| OKX-SWAP        | trades            | 23.47%                                                                            |
| OKX-SWAP        | book_snapshot_5   | 25.26%                                                                            |
| OKX-SPOT        | trades            | 27.25%                                                                            |
| OKX-SPOT        | book_snapshot_5   | 31.35%                                                                            |
| BINANCE-SPOT    | book_snapshot_5   | 44.13%                                                                            |
| BINANCE-SPOT    | trades            | 46.33%                                                                            |
| OKX-FUTURES     | trades            | 45.60%                                                                            |
| BINANCE-FUTURES | futures_chain     | **0.00%** (228 attempted_failed, 0 expected_unattempted — every attempt failed)   |
| BYBIT           | futures_chain     | **0.00%** (1,251 attempted_failed, 0 expected_unattempted — every attempt failed) |
| —               | derivative_ticker | 58%-97% (healthy across all venues)                                               |
| —               | liquidations      | 59%-78% (healthy across all venues)                                               |

**Recency check** (trailing ~90d, date >= 2026-05-11) is WORSE than the full-window average: overall 24.70% (vs. 48.90%
full-window). Per venue: OKX-SPOT 12.21%, BINANCE-SPOT 13.13%, BYBIT 18.66%, OKX-SWAP 30.51%, BINANCE-FUTURES 38.71%,
OKX-FUTURES 48.47% — every single venue's most-recent-90d number is lower than its full-window number.

Full raw output (overall + per-venue + per-(venue,data_type) + recency breakdown) is in this same commit's Progress Log
entry on `/plans/active/cefi_ml_directional_continuous_live_2026_06_20.md` and
`/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 10.

## Why it matters

1. **Blocks the P0 live-capital backtest-fidelity gate.** `cefi_ml_directional_continuous_live_2026_06_20.md`'s 2-year
   config-grid run cannot be scheduled until coverage for exactly this venue/window is confirmed complete (operator
   ruling, 2026-08-08). It is now confirmed — and confirmed incomplete, in exactly the two data_types (`trades` /
   `book_snapshot_5`) the LOB/trade-level backtest actually consumes.
2. **The recency regression is the more urgent signal.** A historical-backfill gap (data never captured back in
   2024/2025) is one failure mode; a WORSENING trend into the present (last-90d coverage lower than the 2-year average,
   in every single venue) is a different, more urgent one — it points at an ongoing live/near-real-time capture problem
   for `trades`/`book_snapshot_5` on these 6 venues, not just an unfinished historical backfill. If uninvestigated, the
   gap keeps growing every day rather than shrinking, and no from-2019 chronological backfill fixes an ongoing
   capture-side problem.
3. **`futures_chain` at exactly 0.00% with 100% attempted_failed** (not merely low, but every single attempt failing) on
   BINANCE-FUTURES and BYBIT is a distinct signature from a coverage gap — it reads as a broken adapter/endpoint/ auth
   path for that specific (venue, data_type), not "not yet captured."

## Recommended decision

Fix at the root per the data-pipeline-correctness HARD RULE (no deadline deferrals). Suggested split below; an operator
can re-prioritize P0 vs P1 if the live-capture investigation (item 1) surfaces something urgent enough to reorder.

## Action items

- [x] ✅ [DATA] P0. **Investigate why trailing-90d `trades`/`book_snapshot_5` coverage for OKX-SPOT/-SWAP/-FUTURES,
      BINANCE-SPOT/-FUTURES, BYBIT is WORSE than the full 2024-2026 window average** (24.70% vs. 48.90% overall, every
      venue individually worse in the recent window than its own full-window number). Check whether the live/
      near-real-time capture cron/scheduler for these venue+data_type combos is degraded, under-scoped, or was recently
      changed — this is a distinct question from "was 2024/2025 ever backfilled." Repo: market-tick-data-service. **Done
      when**: root cause identified (live-capture config/cron issue vs. genuine venue-side outage vs. something else)
      and either fixed or filed as its own more specific issue if the fix is large. — unified-trading-pm (2026-08-09,
      investigation only, no code shipped). **Root cause: NOT a single cause — a cluster of independently-confirmed
      live-capture-path failures, all concentrated inside the trailing-90-day window, none of them a "descope"** (scope
      itself — all 6 venues × both data_types — is unchanged in code today). See Progress Log for the full multi-cause
      writeup + evidence; every cause is already tracked (and several already fixed) as its own open/resolved issue doc
      (cross-linked above in `related:`) — no new issue filed, per the done_definition's "or filed as its own more
      specific issue" branch (already satisfied by the existing docs).
- [x] ✅ [DATA] P1. **DONE 2026-08-09 (slot-15, data_engineering)** — Root cause was FIVE compounding bugs in the
      canonical-write-only path (`TardisAdapter.finalise_and_write_cefi_shards`, used by the futures_chain
      per-instrument fan-out since Tardis has no working grouped endpoint for it), not a broken auth path/endpoint —
      every attempt reached Tardis fine; the manifest-write side silently misrouted or crashed after. All 5 fixed;
      end-to-end verified (real `PartitionedTickWriter` through the real `venue_fetch`/`manifest_finalize` chain, only
      the GCS byte-write stubbed — no live Tardis credentials in this environment) for BINANCE-FUTURES linear, BYBIT
      linear, and BYBIT inverse. Full writeup + files + tests in Progress Log below. market-tick-data-service@e24199df.
- [x] ✅ [DATA] P1. **DONE 2026-08-09 (slot-12, data_engineering)** — Confirmed: **scope matches (all 6 venues + both
      data_types are in the backfill's `heavy|trades;book_snapshot_5` bucket), timing does not** (chronological walk
      from 2019-01-01 is only ~1.5-17% through its ~2769-day span after 8 relaunches over 13 days — reaching 2024-2026
      is not realistic on the P0 gate's timeline, and per item 1 the trailing-90d regression is likely a separate
      ongoing live-capture issue a historical backfill can't fix regardless). Recorded in
      `/plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`'s Progress Log (2026-08-09 entry) and
      filed a targeted `[INFRA] P1` supplement-backfill todo there (2024-01-01→present, these 6 venues ×
      `trades`/`book_snapshot_5`, N=1-Tardis-cap-aware sequencing) — not duplicated here. Repo: unified-trading-pm
      (doc-only; no code change, per this todo's scope).
- [ ] [DATA] P2. **Backfill/re-attempt `trades` + `book_snapshot_5` for OKX-SPOT and BYBIT specifically** (the two
      worst-performing venues, 27-32% and 11-16% coverage respectively for these data_types) over 2024-01-01→present,
      once items 1 and 3 above determine whether this is a live-capture fix, a historical backfill, or both. Repos:
      deployment-service (VM launch), market-tick-data-service. **Done when**: a re-run of this same window-scoped
      measurement shows OKX-SPOT and BYBIT `trades`/`book_snapshot_5` coverage materially improved (cite the new %).
- [x] ✅ [DATA] P2. **DONE 2026-08-09 (slot-12, data_engineering)** — Audit whether the SAME canonical-write-only
      manifest-routing bugs fixed for item 2 above also affect OTHER CeFi venues' options_chain/futures_chain shards
      written via `TardisAdapter.finalise_and_write_cefi_shards`. **Result: branch (b) — DERIBIT IS affected.** DERIBIT
      futures_chain exercises the identical vulnerable path (Tardis has no working grouped FUTURES endpoint for DERIBIT
      either, per `tardis_bulk_download.py`'s own docstring, confirmed by `configs/venue_data_types.yaml` listing
      DERIBIT under `folders: [..., futures_chain, ...]`) and its manifest still shows the same 0%-captured signature
      (423 attempted_failed, 16,695 empty_confirmed, 0 captured as of the 2026-08-09T20:08Z snapshot) — unconfirmed
      against the fix since that fix was only unit/synthetic-verified (no live Tardis credentials in the dev sandbox).
      Also found DERIBIT-futures_chain is undeclared in the UAC `DataTypeCapability` registry despite being
      config-enabled and actively attempted (registry drift). By contrast,
      KRAKEN-FUTURES/BITGET-FUTURES/BITFINEX-FUTURES/COINBASE-FUTURES (branch (a)) have ZERO manifest rows for
      futures_chain/options_chain — registered capability, no live exposure to confirm or fix today. Follow-up fix +
      registry-drift todos filed in a new own issue doc per this todo's own instruction:
      `issues/cefi_deribit_futures_chain_canonical_write_path_exposure_2026_08_09.md`. Read-only audit — no code
      shipped, per this todo's scope. unified-trading-pm@<sha>

## Progress Log

- **2026-08-09** — filed from cefi_satellite_ao_dispatch_batch11 todo 10's window-scoped honest-coverage measurement. No
  fix applied yet — this is the findings-closure filing per RULES.md §4.5.
- **2026-08-09 (slot-12, data_engineering)** — Completed item 3 (cross-reference confirmation). Read
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` + its companion preemption issue
  (`issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`, full 8-relaunch history through 2026-08-09).
  Venue+data_type scope matches exactly; reaching the 2024-2026 window organically does not on any near-term timeline.
  Filed the targeted supplement todo in the track2 plan (not here, per that todo's own instruction). See item 3's flip
  above for the full verdict.
- **2026-08-09 (slot-13, item 1 investigation, read-only — no code shipped)**: root-caused via direct code/git-history
  tracing (`market-tick-data-service`, `deployment-service`) + live `gcloud`/`gsutil` checks against
  `central-element-323112` + a cross-read of the active plans/issues corpus. **Confirmed: nothing was descoped.** All 6
  target venues (OKX-SPOT/-SWAP/-FUTURES, BINANCE-SPOT/-FUTURES, BYBIT) and both `trades`/`book_snapshot_5` are still
  fully in scope in `configs/venue_data_types.yaml` + UAC `VENUES_BY_ASSET_GROUP["cefi"]` today — the 2026-08-04 removal
  of the bare `"OKX"` key was a denominator-correctness cleanup (0 real captures under that key since 07-10/07-21), not
  a capture-scope reduction. Instead, the trailing-90d regression is a **cluster of independently-confirmed
  live-capture- path failures**, all concentrated inside the window (2026-05-11→present), which is exactly why every
  venue's trailing-90d number reads worse than its 2-year average even though the code-declared scope hasn't shrunk:
  1. **Daily forward-poll cron reliability gap — root-caused AND FIXED same-day by a parallel session (slot-18,
     `deployment-service@0395764a`, see `cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md`'s own Progress
     Log).** `trades`/`book_snapshot_5` recent-day rows come from the daily `cefi-fwd-daily-cron-*` host VM
     (`launch-cefi-fwd-daily-cron-vm.sh`, installs a `0 9 * * *` crontab firing `launch-cefi-forward-poll.sh` for a T-1
     day capture across ALL 6 venues × ALL data_types in one run). Live GCS check (2026-08-09) showed cron-HOST
     relaunches on 08-04/08-06/08-09 but none for 08-07/08-08, and a hard cliff to 0 new objects for all 6 target venues
     on 08-06/07/08/09. TRUE root cause (found + fixed same day, after my own investigation window):
     `vm_zombie_watchdog.py`'s `PREFIX_IDLE_THRESHOLDS` had no entry more specific than the generic `"cefi-fwd-"` (a
     30min heartbeat window sized for the WORKER VM's continuous heartbeat sidecar); the cron-HOST VM boots, installs
     its crontab, then sleeps forever WITHOUT ever writing a `vm-heartbeat/<vm_name>.txt` blob — so the watchdog
     misclassified the healthy, sleeping host as a zombie and deleted it ~16min after every relaunch, silently starving
     the daily fire. Fixed by adding the watchdog's own `tier=daemon` opt-out label to the launcher (and 3 sibling
     `*-fwd-daily-cron-vm.sh` launchers sharing the identical pattern). Two compounding sub-causes also confirmed, both
     already tracked in that same doc: (a) 3 separate incidents (08-06, 08-08 ×2) of a fresh `cefi-fwd-*` WORKER VM
     (distinct from the cron host) being deleted 8-17 min after launch by a Claude Code agent copy-pasting the
     singleton-lock refusal's raw delete command — already hardened (`deployment-service@bc48b09b` removed the
     copy-pasteable command); (b) a confirmed, still-OPEN MTDS code bug at
     `market_tick_data_service/engine/orchestrator/venue_fetch.py:526-552` — when a Tardis CeFi venue (ALL 6 target
     venues qualify via `_VENUES_NEEDING_INSTRUMENT_PREFLIGHT`, confirmed in `engine/orchestrator/preflight.py:294-297`)
     has real instruments-service data available but no explicit `--instrument-ids` was passed (the daily cron's normal
     invocation shape), the code is MISSING the positive branch that populates `venue_instrument_ids` from IS — it stays
     `None`, so the atom-coverage pre-flight filter computes an empty expected-set, which trivially satisfies "already
     covered" and silently zero-writes a day that looks superficially covered (fires whenever ANY prior manifest row
     exists for that venue+date, e.g. from an earlier partial/retried run). Did not attempt this fix here — it requires
     new code to fetch+shape the correct instrument-id vocabulary from the IS parquet matching the existing atom-
     coverage contract, it's non-trivial, and it's already tracked as its own scoped `[CODE]` P2 todo in that doc.
  2. **Structural Tardis single-IP concurrency starvation (ongoing, by design, confirmed still live as of this
     writing).** `launch-cefi-forward-poll.sh` calls a hard cap=1 concurrent-authenticated-Tardis-IP guard and refuses
     outright (does not queue) whenever any historical CeFi Tardis backfill VM already holds the slot. Confirmed
     currently holding the slot: `cefi-queue-heavy-binancefutu-x17-20260809-083733`
     (VM_DATA_TYPES=trades;book_snapshot_5, VM_START_DATE=2019-01-01) — i.e. the SAME `trades`/`book_snapshot_5`
     chronological backfill item 3 above cross-references. The trailing-90-day window has been saturated with
     long-running CeFi Tardis backfill campaigns holding that single slot for days-to-weeks at a stretch, so the daily
     forward-poll has been starved by design for a meaningful fraction of the window — a dynamic that doesn't apply (or
     applies far less) over the full 2024-2026 average.
  3. **Confirmed regression with an un-backfilled historical scar
     (`cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md`, still open).** 2026-07-27
     (`market-tick-data-service@3169d25e`) flipped `validate=True` unconditionally on the CeFi Tardis write path on a
     false code-comment premise that `book_snapshot_5` had no registered UAC schema contract — it does, and the real
     contract required a fictional serialized-string column no writer ever produced, so 2026-07-27→28 **every
     `book_snapshot_5` write for essentially every CeFi venue FATAL-failed write-time validation** (~299,467
     `attempted_failed` rows, accelerating 2,563→4,809/day before being caught). Fixed in code 2026-07-28 + 2026-08-02,
     but the ~300k poisoned historical rows were explicitly never retroactively re-fetched — a permanent coverage drag
     for those specific dates, sitting inside the trailing-90-day window, tracked as that doc's own open re-backfill
     todo.
  4. **Corroborating, separate mechanism (`tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md`, still
     open).** A ~47.5h code-tarball-refresh outage (2026-07-30T13:02Z→08-01T12:42Z) left the always-on live-WS leg
     (`mtds-live-cefi-consolidated-*`) running stale code missing fixes for two real connector bugs (an ASTER
     SUBSCRIBE-frame size cliff + a per-connection 200-stream cap), independently confirmed via the manifest:
     `BINANCE-FUTURES book_snapshot_5` 100% empty on 07-30, `OKX-FUTURES book_snapshot_5`/`derivative_ticker` 100% empty
     07-30 then only ~24% recovered through 08-02 — both inside the trailing-90-day window, both since fixed in code but
     with no retroactive backfill of the affected dates either. Also corroborating (archived, same failure class, not
     separately actioned): `tardis_concurrent_ip_lockout_2026_07_12` and
     `cefi_high_attempted_failed_batch_cluster_2026_07_23` independently document chronic Tardis 403 concurrent-IP
     lockout storms driving 28.7%/34.4% `attempted_failed` for `trades`/`book_snapshot_5` respectively as of
     2026-07-22/23 — same single-IP-contention mechanism as cause 2 above, recurring rather than one-off. **None of the
     4 causes is "just an unfinished historical backfill"** — all are dated, live-capture-path health problems, which is
     why the trailing window has been getting worse even as the historical 2024-2025 backfill (item 3 of this issue)
     continues to close the older gap; cause 1's cron-reliability half is now fixed (2026-08-09), but causes 2-4 remain
     live/open and cause 1's MTDS preflight-bug half is also still open. Cross-reference note appended (not overwritten)
     to `cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md`'s own Progress Log, same session, flagging that
     its open preflight-bug + backfill-verification todos also gate this P0 backtest-fidelity blocker, not just its
     original contamination-plan scope.

- **2026-08-09 (slot-15, data_engineering)** — item 2 (`futures_chain` 0.00% for BINANCE-FUTURES/BYBIT), root-caused +
  fixed. **Not** a broken auth path or changed API contract per the todo's own hypothesis — every Tardis fetch reached
  the vendor and returned real rows; the failure was entirely on the manifest-write side, after a successful GCS
  persist. Found via direct execution tracing (real functions, synthetic data — no live Tardis credentials in this
  sandboxed dev environment), not log-reading, since the manifest doesn't record which of these mechanisms produced a
  given `attempted_failed` row. Five compounding bugs, all in the canonical-write-only path
  (`TardisAdapter.finalise_and_write_cefi_shards` → `_write_one_cefi_shard`, used by the futures_chain per-instrument
  fan-out in `_download_futures_per_instrument` since Tardis has no working grouped `FUTURES.csv.gz` endpoint):
  1. **Itype-vocabulary mismatch** — `record_shard_count`/`record_instrument` passed the raw `InstrumentType` enum value
     ("FUTURE"/"OPTION") instead of the wrapper string ("futures_chain"/"options_chain") `shard.path` actually encodes.
     `venue_fetch._record_venue_shard_counts`'s `is_derivative` check only recognises the wrapper strings, so every such
     shard was misclassified as a plain single-instrument shard — its "underlying" grouping discarded, `instrument_id`
     set to the bare underlying token ("BTC") canonicalised as if it were a raw symbol.
  2. **`BUNDLED_DATA_TYPES` gate mismatch** — `manifest_finalize._write_shard_counts_to_manifest` additionally required
     `data_type_key in BUNDLED_DATA_TYPES` (a UAC registry —
     `unified_api_contracts.canonical.crosscutting. _honest_coverage_clusters` — where `options_chain`/`futures_chain`
     are literal `data_type` values, alongside
     `prediction_canonical_question_group`/`sports_fixture_bundle`/`event_contract`). CeFi ALWAYS normalises the chain
     wrapper's `data_type` to its real schema value ("trades") before writing — `TardisAdapter._canonical_data_type`'s
     documented, tested contract — which is never itself a `BUNDLED_DATA_TYPES` member. This made the bundle manifest
     path (`_write_bundle_shard_row`) structurally unreachable for EVERY CeFi Tardis chain-bundle shard, independent of
     bug 1. Fix: dropped the redundant clause — `itype_key in _UNDERLYING_PARTITIONED_TYPES and itype_key != "combo"`
     already fully identifies a chain-bundle shard on its own.
  3. **Missing cluster/envelope bookkeeping** — the canonical-write-only path never populated `cluster_counts` /
     `chain_available_at_envelope` at all (only the live `write_chunk` path did), so even a correctly-routed shard's
     manifest row hit `record_failed(error="missing_available_at_envelope")` unconditionally. Fix: new
     `PartitionedTickWriter.record_cluster_count` (via a `ClusterBookkeepingMixin`, split into
     `engine/orchestrator/_cluster_bookkeeping.py` — `partitioned_writer.py` was already at the 900-line file-size
     ratchet cap), called from `_write_one_cefi_shard` alongside the existing `record_shard_count`/`record_instrument`.
  4. **Wrong cluster-bucket derivation** — the futures_chain cluster key used raw symbols instead of front/back/spread
     (`FUTURES_CHAIN_BUCKETS`). UAC's `futures_expiry_bucket`/`parse_futures_expiry` only recognise CME-style month-code
     symbols (`ESM6`) and treat ANY "-" as a calendar-spread marker before even trying to parse it — every CeFi
     dated-future symbol uses "-"/"_" as its OWN date separator (Binance `BTCUSDT_250627`, Bybit `BTC-07FEB25`/
     `BTCUSDT-26DEC25`, OKX `BTC-USD-260403`). Fix: new standalone leaf module
     `market_tick_data_service/cefi_futures_chain_symbology.py` (no imports from `engine`/`market_interface` —
     `engine.orchestrator`'s own package `__init__.py` transitively imports `market_interface`, so a reverse import from
     `market_interface` back into any `engine.orchestrator` submodule closes an import cycle; confirmed by hitting it
     while wiring this up) with a CeFi-aware bucketer, used by both `partitioned_writer.py` (live path) and
     `tardis_cefi_shards.py` (canonical-write-only path).
  5. **Expiry-derivation fallback gap** — `tardis_shared._populate_chain_fields`'s futures_chain branch only tried the
     Deribit/Bybit DDMMMYY-shape parser (`parse_deribit_future_symbol`), never Binance's underscore-YYMMDD shape,
     leaving `expiry_date` as `pd.NaT` (not absent) for Binance symbols. Because pandas `NaT` satisfies
     `isinstance(_, datetime.date)`, `derive_row_instrument_id`'s OWN already-correct 3-tier fallback (which reads
     `row.get("expiry_date")` first) never even ran its `if expiry is None` gate — the `NaT` propagated uncaught into
     `expiry_date.strftime(...)`, crashing every BINANCE-FUTURES multi-symbol bundle (2+ active quarterly contracts —
     the normal case, confirmed live Binance USDⓈ-M convention) inside `finalise_rows_and_path`, before ever reaching
     bugs 1-4. Bybit was unaffected by this specific bug (its DDMMMYY shape already parses via the Deribit-shaped
     regex). Fix: extended `_populate_chain_fields`'s fallback chain to match `derive_row_instrument_id`'s own tiers
     (`_parse_numeric_futures_expiry` → `_parse_month_code_futures_expiry`, both already existed + already imported,
     just never called from this second, independent derivation site).

  **Verification** (no live Tardis credentials in this sandboxed dev environment — direct execution of the real
  production functions with synthetic input rows is the closest available substitute for "a sample re-attempt captures
  successfully"): built a real `PartitionedTickWriter` + called the real `TardisAdapter.finalise_and_write_cefi_shards`
  → real `venue_fetch._record_venue_shard_counts` → real `manifest_finalize._write_shard_counts_to_manifest`, for
  2-symbol (front+back quarterly) futures_chain bundles on BINANCE-FUTURES linear, BYBIT linear, and BYBIT inverse (all
  3 documented `derive_settlement_dimensions` margin conventions this task's 2 venues actually use) — every scenario now
  reaches `record_captured_from_counts` with `observed_clusters={"front": 1, "back": 1}` and the correct
  `underlying`/`quote_asset`/`margin_type`/`instrument_id` shape, never `record_failed` and never a misrouted `.add()`.
  Regression-tested with 1 new unit test file (`test_cefi_futures_chain_symbology.py`) + additions to 3 existing test
  files (cluster-bucketing, the id-derivation crash, and the full manifest-routing chain) + 1 pre-existing test fixed
  (`test_orchestrator_shard_key_per_instrument. py::test_derivative_emits_bundled_underlying_row` asserted on the OLD,
  bug-2-shaped `.add()` routing for a DERIBIT options_chain shard — updated to assert on `record_captured_from_counts`
  instead, which is what a genuine derivative bundle with real cluster/envelope bookkeeping now correctly reaches). Full
  local `quality-gates.sh` green (10,353 tests passed, 0 failed). **Filed a new P2 follow-up todo above**: bugs 1-3 are
  NOT futures_chain- specific — they're bugs in the shared canonical-write-only manifest-routing infrastructure any CeFi
  options_chain/futures_chain shard would hit via this exact code path; this issue only measured OKX/BINANCE/BYBIT, so
  whether any OTHER venue (DERIBIT, most plausibly) is also silently affected is unconfirmed and worth a follow-up
  audit, per CLAUDE.md's "big finding... NOTIFY OPERATOR + issue doc" — flagging it here rather than silently absorbing
  it as out-of-scope.

  Files changed (market-tick-data-service@e24199df): `engine/orchestrator/manifest_finalize.py`,
  `engine/orchestrator/partitioned_writer.py`, `engine/orchestrator/_cluster_bookkeeping.py` (new),
  `market_interface/adapters/cefi/tardis_shared.py`, `market_interface/adapters/tradfi/tardis_cefi_shards.py`,
  `cefi_futures_chain_symbology.py` (new), + the 4 test files above.

- **2026-08-09 (slot-15, data_engineering, item 4 — dispatched on this issue's own P2 todo)**: Investigated launching
  the targeted OKX-SPOT + BYBIT `trades`/`book_snapshot_5` backfill (2024-01-01→present). **Blocked on the Tardis N=1
  concurrent-VM cap — confirmed a real, active, legitimate occupant, not a stale/dead claim**:
  - `gcloud compute instances describe cefi-queue-heavy-binancefutu-x17-20260809-083733` → `RUNNING`, created
    2026-08-09T08:37:39Z (this session's launch, presumably the latest of the 8+ relaunches tracked in
    `issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`).
  - `PROGRESS.json`: `{"last_completed_date":"2020-05-25","monotonic":true,"updated":"2026-08-09T13:17:43Z"}` —
    genuinely advancing (checkpoint mechanism confirmed real and working, addressing the earlier "no PROGRESS.json"
    gap). `run.log` tail confirms live Tardis streaming writes for `date=2020-05-27` at check time, across multiple
    venues including OKX-FUTURES.
  - `LAUNCH_PARAMS.json` confirms this VM's scope is the FULL chronological walk — all 16 CeFi venues (including
    OKX-SPOT and BYBIT), `heavy` group, no year/date restriction (natural per-venue genesis start).
  - Day ~512/2769 (~18.5%) of the 2019-01-01→present span — consistent with (slightly ahead of) the 2026-08-09 item-3
    cross-reference's 1.5-17% reading. At the previously-measured ~3 days/hr rate, reaching 2024-01-01 (day ~1827) is
    still many days out — confirms item 3's "not reachable on the P0 gate's timeline" conclusion still holds for this
    narrower 2-venue scope too, since both venues ride the SAME single combined VM.
  - `tardis-concurrency-guard.sh` (read in full) REFUSES rather than queues a second Tardis VM — confirmed via source,
    not by triggering a live refusal (no throwaway launch attempt). `FORCE=1` would bypass it but is explicitly
    documented as accepting "the 403-storm + false-attempted_failed-row risk" (measured elsewhere in this same doc's
    Progress Log: N=3 lease-on produced +37,212 false `attempted_failed` rows and coverage went BACKWARD) — not an
    acceptable trade for a P2 todo against a CORRECTNESS-north-star craft rule.
  - **Prepared and DRY_RUN-validated the exact ready-to-fire recipe** (from `deployment-service/`):
    `VENUES="OKX-SPOT BYBIT" YEARS="2024 2025 2026" LAUNCH_GROUPS=heavy SINGLE_VM_QUEUE=1 TARDIS_CONCURRENCY_LEASE=1 TARDIS_MAX_CONCURRENT_DOWNLOADS=32 bash scripts/vm/launch-cefi-sharded-backfill.sh`
    — confirmed via `DRY_RUN=1` (bypasses the cap check entirely, so safe to run regardless of current VM state) to
    correctly bundle into ONE combined VM (`cefi-queue-heavy-okxspot-x2-*`, `e2-highmem-16`) spanning exactly
    `start=2024-01-01 end=2026-08-08`, `data_types=trades;book_snapshot_5`, both venues. **Do NOT add a `START_DATE`
    override for this multi-year launch** — found (by reading `launch_cefi_shard`, not by reproducing it live) that
    `START_DATE` is validated per-shard against `^${year}-[0-9]{2}-[0-9]{2}$`, so a single global
    `START_DATE=2024-01-01` would pass validation for `year=2024` but FAIL it for `year=2025`/`2026` and abort the whole
    script under `set -e` partway through the queue-accumulation loop — a latent bug, not exercised here since the
    un-overridden per-year default (`${year}-01-01`) already equals the target start for every year in this range,
    making the override unnecessary. Not fixed (adjacent, not blocking, and a proper fix needs testing across both the
    per-shard and `SINGLE_VM_QUEUE` code paths) — flagging here for a future P3 script-robustness todo rather than
    silently absorbing it.
  - **Decision: did NOT force (`FORCE=1`) or interrupt the running chronological VM.** Killing it would free the slot
    immediately (and the checkpoint above means it's genuinely resumable, not a total-loss), but it is tracked by a
    DIFFERENT plan (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`) whose own todos -004/-005 are durably
    parked on this exact VM's measured self-termination (`cefi-track2-backfill-vm-terminated` prerequisite, applied by
    main 2026-07-28 after an identical fork was raised via `/blocked` by slot-13 on 2026-07-28) — manually terminating
    it would flip that condition on a truncated, non-representative run, exactly the misrepresentation the operator's
    prior ruling on that same doc guarded against. This is a cross-plan-consequential, genuinely-either-way judgment
    call (not a pure execution matter), so filing `/blocked` rather than deciding unilaterally, mirroring the
    established precedent in this exact plan family. Recommendation: durably park this todo the same way (reuse the SAME
    `cefi-track2-backfill-vm-terminated` prerequisite rather than mint a new one — it's the identical real-world
    condition), so this todo and track2's own broader 6-venue supplement (todo 6 there) both become dispatchable the
    moment a genuine slot-opening is confirmed. Todo checkbox left UNCHECKED (no coverage-% improvement is measurable
    yet — flipping it now would misrepresent progress the same way the operator's park precedent exists to prevent).

- **2026-08-09 (slot-12, data_engineering, item 4 audit)** — Confirmed DERIBIT futures_chain exercises the SAME
  vulnerable canonical-write-only path (`_download_futures_per_instrument` -> `finalise_and_write_cefi_shards`) fixed
  for BINANCE-FUTURES/BYBIT — Tardis has no working grouped FUTURES endpoint for DERIBIT either (per
  `tardis_bulk_download.py`'s own docstring), and `configs/venue_data_types.yaml` confirms DERIBIT futures_chain is a
  real, config-enabled capture surface. Manifest snapshot (2026-08-09T20:08Z) shows DERIBIT still at the same
  0%-captured signature (423 attempted_failed, 16,695 empty_confirmed, 0 captured) as the pre-fix state — unconfirmed
  against the 2026-08-09 fix (only unit/synthetic-verified, no live Tardis creds available). Also found
  DERIBIT-futures_chain undeclared in the UAC `DataTypeCapability` registry despite being real and actively attempted
  (registry drift vs. `configs/venue_data_types.yaml` + the manifest ground truth).
  KRAKEN-FUTURES/BITGET-FUTURES/BITFINEX-FUTURES/COINBASE-FUTURES: zero manifest rows for futures_chain or options_chain
  — capability-registered but no live capture attempt has reached the manifest yet, so no exposure to confirm/fix there
  today. Filed follow-up fix + registry-drift todos in a new issue doc per this todo's own instruction:
  `issues/cefi_deribit_futures_chain_canonical_write_path_exposure_2026_08_09.md`. Read-only audit — no code shipped,
  per this todo's scope. **CROSS-LINK added 2026-08-18 (plan_reconciler)**: this confirms the SAME
  canonical-write-only vulnerable path for DERIBIT `futures_chain`; whether it ALSO explains DERIBIT `options_chain`'s
  100% attempted_failed (this repo's `deribit_options_chain_af_g4_blocker_2026_07_03.md`, gated separately on the
  Track-2 coverage backfill) is not yet confirmed either way — that doc should be checked against this fix rather
  than treated as an independent blocker.
- **context-scout 2026-08-14**: populated context_scope (3 entries).
- **context-scout 2026-08-20**: refreshed context_scope (3 entries) — all existing entries still resolve (the manifest
  finalize path, the measurement script, and the honest-coverage-model SSOT).
