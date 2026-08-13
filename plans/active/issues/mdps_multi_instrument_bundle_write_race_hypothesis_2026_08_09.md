---
doc_type: issue
title:
  MDPS multi-instrument candle bundle write — possible last-writer-wins race even after the --force fix (code-reading
  hypothesis, not yet live-confirmed)
summary: >-
  Static code reading of market-data-processing-service's candle writer found that when 2+ underlyings (e.g. BYBIT
  futures_chain BTC + ETH) must land in the SAME shared `ticks.parquet` bundle for one day/timeframe/data_type cell,
  each underlying's raw file is written via an INDEPENDENT ThreadPoolExecutor task that builds a local temp parquet
  containing only that task's own rows and uploads it as a straight object overwrite -- no download-existing/merge/
  re-upload step exists anywhere in the write path. This means even with the now-fixed --force-forwarding bug
  (market-data-processing-service@e9f9819) correctly threaded through, concurrent per-instrument writes to the same
  bundle path could still race, with whichever write finishes last silently discarding the other instrument's rows --
  i.e. the exact "bundle-collision race" symptom Track-7 exists to fix could recur even on a POST-FIX relaunch. This is
  a hypothesis from static reading only; it has not yet been observed live because no post-fix relaunch has completed
  yet.
status: open
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [mdps, race-condition, candle-bundle, data-correctness, cefi, track-7, hypothesis]
related:
  [
    /plans/active/issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md,
    /plans/active/issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
author: slot-2 (data_engineering)
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: advance-code
depends_on: [cefi_track7_candle_bundle_regeneration_vm_2026_08_04]
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by:
source: >-
  Discovered while confirming the terminal state + relaunch of mdps-backfill-cefi-20260807-130321 /
  mdps-backfill-cefi-20260808-095136 for cefi_satellite_ao_dispatch_batch10_2026_08_08.md todo 3 and
  infra_health_audit_findings_fix_2026_08_07.md's related recheck todo.
context_scope:
  [
    market-data-processing-service/market_data_processing_service/app/core/candle_write_mixin.py,
    market-data-processing-service/market_data_processing_service/app/core/batch_workers.py,
    market-data-processing-service/market_data_processing_service/app/core/live_workers.py,
    market-data-processing-service/market_data_processing_service/app/core/live_workers_chain.py,
    market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py,
    /plans/active/issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md,
    /plans/active/issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md,
  ]
---

# MDPS multi-instrument candle bundle write — possible last-writer-wins race (hypothesis)

> **CORRECTED 2026-08-12 (/plan-reconcile)**: title/summary still frame this as an open, unconfirmed cross-write-race
> hypothesis — but the doc's own 2026-08-10 Progress Log entry already REFUTED it by code reading:
> `_blob_matches_data_type_partition` + `_build_candle_output_path` give BTC/ETH distinct output paths, so the
> hypothesized last-writer-wins collision cannot occur as described. The single-symbol SYMPTOM this doc was chasing is
> real but a DIFFERENT, broader defect (WITHIN-bundle: 7 raw contracts collapsing to 1 emitted, confirmed on both BYBIT
> and DERIBIT) — not a cross-write race, so not fixable via merge-on-write/per-cell serialization. Title/summary kept
> verbatim (existing cross-refs); see the "Hypothesis (as stated) REFUTED by current-code reading" entry below for
> ground truth. Sole remaining todo (line ~127) is still open, gated on the post-fix relaunch's per-underlying
> contract-count audit.

## What I found

While independently corroborating the Track-7 VM relaunch (`mdps-backfill-cefi-20260808-095136`) and the already-fixed
`--force`-dropped-in-subprocess-per-date bug (`mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md`, fixed in
`market-data-processing-service@e9f9819`), I dispatched a read-only investigation into WHY the BYBIT futures_chain
bundles specifically end up with exactly 1 symbol instead of 2 (BTC+ETH) — since the already-fixed bug (force silently
`False`) fully explains why 2 prior relaunches produced a completely UNCHANGED bundle (mtime frozen at
`2026-08-03T01:59:07Z`, correctly explained by the `if not force and blob_exists(): skip` gate at
`candle_write_mixin.py:200` short-circuiting on `force=False`), it does NOT by itself explain the ORIGINAL
bundle-collision defect that motivated Track-7 in the first place (i.e. why the bundle only ever had 1 symbol even
BEFORE any of these relaunch attempts, back when it was first produced).

Static code reading (`market_data_processing_service/app/core/`) found:

- `batch_workers.py::_submit_instrument_file_tasks` / `_process_files_parallel` (lines ~352-393) submits **one
  `ThreadPoolExecutor` task per raw blob_path** — for a day where BYBIT futures_chain has both `BTC.parquet` and
  `ETH.parquet` raw files, that's 2 independent, concurrently-scheduled write tasks targeting the SAME output cell.
- Each task's call chain (`live_workers.py:176` → `live_workers_chain.py:284/387` → `candle_write_mixin.py`'s
  `_write_candles` → `canonical_writer.py::write_candle_parquet`, lines ~164-665) builds a **local temp parquet
  containing only that call's own rows** (`open_candle_writer` / `_utl_write_chunk` / `finalize_local()`) and uploads it
  via `_upload_local_to_gcs` (line ~553) as a **straight object overwrite** — there is no download-existing-bundle /
  merge-by-instrument-id / re-upload step anywhere in this path (confirmed across both the batch and streaming write
  variants, `live_workers_streaming.py:415-519` merges only WITHIN one call, never across separate per-file calls).
- The canonical output path for futures_chain/options_chain bundles carries no `underlying=`/per-instrument segment —
  both BTC's and ETH's writes target the byte-identical `ticks.parquet` object.

**Conclusion (hypothesis, not yet live-confirmed)**: if this reading is correct, whichever of the 2 concurrent writes
finishes last wins and silently discards the other instrument's rows — this is a plausible root cause for the ORIGINAL
"race winner" bundle-collision defect (matching the doc title Track-7 was named for), and it would recur on ANY future
relaunch (including the currently-queued post-force-fix per-day-scoped relaunch in
`cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md`) regardless of `--force` correctness, because `--force` only
controls whether the write is ATTEMPTED, not whether concurrent per-instrument writes to a shared path are merged.

**Why this is still a hypothesis, not a confirmed finding**: no live relaunch has completed WITH the `--force`-forward
fix applied yet (the currently-running `mdps-backfill-cefi-20260808-095136` predates the fix, so its still-PARTIAL
bundles are already fully explained by the OTHER bug, not this one). This needs live confirmation: once the queued
per-day-scoped relaunch (Track-7 doc, todo "Once `mdps-backfill-cefi-20260808-095136` reaches a terminal state...") runs
with the fix live, check whether the resulting BYBIT bundles STILL show only 1 symbol despite `Force: True` appearing in
the per-date child log. If they do, this hypothesis is confirmed and the writer needs a genuine merge-on-write (or
single-writer-per-cell serialization) fix, not just a force-forwarding fix.

## Why it matters

If confirmed, the currently-queued Track-7 relaunch (believed by
`cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md` to be unblocked now that `--force` is fixed) will STILL fail
its own done-when bar (BYBIT bundles carrying both BTC+ETH `instrument_id`s), because the actual defect is a write-time
race, not a force-propagation gap. This would be the THIRD distinct root cause discovered for the same symptom in 5 days
(stale-object race → deleted; --force-drop → fixed; this hypothesized write race → unconfirmed), and burning a 4th
VM-relaunch cycle without checking for it first would repeat the same "looks fixed, exits 0, still broken" trap the
`--force`-drop bug itself was.

## Recommended decision

Do NOT block or change the currently-queued per-day-scoped relaunch (still worth running — it may reveal this is a
non-issue, e.g. if `_process_files_parallel` actually serializes tasks touching the same output path, which was not
fully ruled out by static reading alone). Instead: when that relaunch's post-completion audit runs, explicitly check
whether a 2-day 15s-timeframe BYBIT sample STILL shows exactly 1 symbol despite a confirmed `Force: True` in the child
log. If yes, treat this issue doc as confirmed and scope a proper fix (serialize writes per output cell, or
read-merge-write instead of overwrite) as a new P1 todo here.

## Todos

- [ ] [DATA] P1. Once the Track-7 per-day-scoped post-fix relaunch (queued in
      `cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md`) completes and is audited, check whether BYBIT 15s/1m
      bundles for the 6 target days still show only 1 `instrument_id` despite `Force: True` confirmed in the per-date
      child log. **Done when**: either (a) confirmed FIXED — bundles carry both BTC+ETH legs, this doc is closed as a
      non-issue (the concurrent-write race did not manifest, e.g. because tasks per output path are actually serialized
      somewhere this reading missed), or (b) confirmed BROKEN — bundles still single-symbol with force correctly true,
      in which case scope + implement the genuine fix (see the **2026-08-10 slot-27** Progress Log entry — the
      cross-write-race hypothesis is REFUTED by current-code reading; the confirmed defect is WITHIN-bundle symbol
      truncation, so the fix is expected in the streaming symbol-accumulation / eager-fallback path
      (`live_workers_streaming.py`, `candle_write_mixin.py`), not merge-on-write or per-cell serialization) as a new P1
      follow-up todo appended here, cross-linking `cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md`.

## Progress Log

- **2026-08-09 (slot-2 data_engineering)**: Filed after a read-only Explore-agent code investigation
  (`market_data_processing_service/app/core/*`) surfaced this as a plausible, previously-undiscussed additional root
  cause for the Track-7 bundle-collision symptom, distinct from the already-fixed `--force`-drop bug. Not yet
  live-confirmed — filed as a flagged risk against the currently-queued relaunch rather than blocking it.

- **2026-08-09T01:49Z (slot-25, data_engineering, dispatched on the sole todo above)**: Gate not yet met — verified
  live: `gcloud compute instances describe mdps-backfill-cefi-20260808-095136` → still `RUNNING` (SPOT, created
  2026-08-08T08:57:00Z), i.e. this pre-fix VM has NOT reached a terminal state yet. `GET /api/backlog` confirms the
  Track-7 per-day-scoped post-fix relaunch todo (`cefi_track7_candle_bundle_regeneration_vm-004`, the "once
  mdps-backfill-cefi-20260808-095136 reaches a terminal state, relaunch scoped PER-DAY" todo in
  `cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md`) is `status: queued, dispatched_to: None` — not even
  started, let alone completed+audited. This todo's own done-when ("once that relaunch completes and is audited, check
  whether BYBIT bundles still show only 1 instrument_id") cannot be evaluated yet. Declining and skipping via
  `reason_code: "GATED"` — no code change made (nothing to check yet); re-dispatch once the per-day relaunch has run and
  its post-completion audit has posted a result.

- **2026-08-09T02:16Z (slot-5, data_engineering, dispatched on the sole todo above)**: Re-checked ~27 min after
  slot-25's decline — gate still unmet, unchanged: `mdps-backfill-cefi-20260808-095136` still `RUNNING` live
  (`gcloud compute instances describe`), and the per-day-scoped relaunch todo
  (`cefi_track7_candle_bundle_regeneration_vm-7eb3b7e1186c`, same todo slot-25 checked) is still
  `status: queued, dispatched_to: null` per live `GET /api/backlog` — confirmed ELIGIBLE for dispatch to any slot (not
  itself prereq-gated in the backlog system; the "once the VM reaches terminal state" condition is prose only, so
  whichever worker eventually picks up THAT todo will need to independently re-verify VM state too, same as this check).
  This task round-tripped back to a brand-new slot only 27 min after slot-25's identical GATED decline — the exact
  redispatch churn `park_now` exists to prevent (`server/auto_park.py`), and the real gate here is VM-completion-scale
  (measured processing rate implies this pre-fix VM won't reach a terminal state for hours-to-days, not minutes), well
  past the 12-60min dispatch-cooldown windows. Declining via `reason_code: "GATED"` WITH `park_now: true` this time to
  durably park rather than re-offering this to another fresh slot every cooldown cycle. **To unpark once the per-day
  relaunch has genuinely run + been audited**:
  `POST /api/prerequisites/auto_unpark__mdps_multi_instrument_bundle_write_race_hypothesis-c9274b858947 {"value": true}`.

- **2026-08-10 (slot-27, data_engineering, dispatched on the sole todo above)**: Gate still unmet — re-verified live:
  the per-day post-fix relaunch todo (`cefi_track7_candle_bundle_regeneration_vm-7eb3b7e1186c`) is still
  `status: queued` (priority 50), and the pre-fix VM `mdps-backfill-cefi-20260808-095136` is STILL `RUNNING`
  (asia-northeast1-c, created 2026-08-08). Two VMs launched 2026-08-10 (`mdps-backfill-cefi-20260810-114949`, `-115835`)
  are UNRELATED CEFI backfills (derivative_ticker/1h 2026-07-27→08-03, BITGET-FUTURES/1h 2026-04-20→04-30, both
  `FORCE=false` per their LAUNCH_PARAMS.json) — NOT the Track-7 relaunch. So the post-fix relaunch has not completed +
  been audited → nothing to check live yet. Performed a code-reading + GCS verification of the write path that
  materially REFINES the hypothesis, captured so the post-fix audit checks the right thing:
  - **Hypothesis (as stated) REFUTED by current-code reading**:
    `orchestration_scanner.py::_blob_matches_data_type_partition` admits ONLY
    `instrument_type=futures_chain/underlying={U}/ticks.parquet` blobs into futures_chain processing (per-contract
    `instrument_type=future/` files are EXCLUDED), and each such blob carries its own `underlying=` root →
    `_build_candle_output_path` emits a DISTINCT `.../venue=BYBIT/underlying={U}/ticks.parquet` per root. BTC and ETH
    writes do NOT share a path under current code, so the hypothesized last-writer-wins cross-write race cannot occur as
    described.
  - **But the single-symbol SYMPTOM is CONFIRMED and broader**: GCS ground truth for 2023-06-01/15s — raw BYBIT
    futures_chain BTC bundle holds 7 contracts (`BTC-29DEC23` … `BTC-02JUN23`) and raw DERIBIT BTC bundle holds 7
    (`DERIBIT:FUTURE:BTC-USD-inverse-*`), yet BOTH processed bundles contain exactly 1 (`BYBIT:FUTURE:BTC-20231229` at
    the no-underlying `venue=BYBIT/ticks.parquet`, mtime 2026-08-03T01:59:07Z; `DERIBIT:FUTURE:BTC-USD-inverse-20240329`
    at `underlying=BTC/ticks.parquet`, mtime 2026-07-22T21:06:26Z). The 2026-08-08 audit's "DERIBIT OK (1 instrument per
    underlying-partitioned file)" label is WRONG — DERIBIT shows the SAME truncation, not the intended design. The real
    defect is WITHIN-bundle (7 raw contracts → 1 emitted), not a cross-write race.
  - **Current streaming code appears correct**: `live_workers_streaming.py::_process_chain_bundle_streaming` accumulates
    every `_iter_chain_symbol_dfs` slice into `candles_by_tf` and writes ONE parquet with all symbols; the stale
    1-contract bundles (both predating the force fix) were written by older/different code and may be fixed by the
    current code — unverifiable without the live post-fix relaunch. **The post-fix audit MUST check per-underlying
    CONTRACT COUNT (all contracts present), not just BTC+ETH presence, and must include DERIBIT (also truncated).** If
    still 1-of-7, the fix is within-bundle symbol accumulation / the eager-fallback path, NOT merge-on-write/per-cell
    serialization (todo (b) text corrected above).
  - Declining via `reason_code: "GATED"` + `park_now: true` — same external gate as slot-25/slot-5 (per-day relaunch not
    yet run); re-check once the relaunch's post-completion audit posts. No code change to market-data-processing-service
    (gate not met; implementing a fix now would be speculative).
