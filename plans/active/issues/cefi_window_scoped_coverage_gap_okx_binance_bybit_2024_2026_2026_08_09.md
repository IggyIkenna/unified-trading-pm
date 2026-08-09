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
    /plans/active/cefi_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /codex/02-data/honest-coverage-model.md,
    /plans/active/issues/cefi_fwd_backfill_vm_deleted_by_sa_within_10min_2026_08_08.md,
    /plans/active/issues/cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md,
    /plans/active/issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md,
    /plans/active/issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md,
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
`/plans/active/cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 10.

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
- [ ] [DATA] P1. **Root-cause the 0.00% `futures_chain` coverage for BINANCE-FUTURES (228 attempted_failed) and BYBIT
      (1,251 attempted_failed)** — every attempt failed, 0 captured, 0 expected_unattempted. Check the adapter/endpoint
      for a broken auth path, changed API contract, or misrouted request. Repo: market-tick-data-service. **Done when**:
      root cause identified + fixed (or filed separately if genuinely large), and a sample re-attempt for each venue
      captures successfully.
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
