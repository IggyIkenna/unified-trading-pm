---
doc_type: issue
title: DERIBIT options_chain af=10,114 (cap=1) — G4 gate blocker
summary:
  Deribit options_chain nearly completely failed in wave-1 backfill. Tardis confirms 426,474 Deribit option symbols with
  options_chain data type available since 2019 — data IS there. Failure was likely transient (preemption/OOM in wave-1).
  Wave-1 reprobe VMs launched 2026-07-03 include DERIBIT light group (options_chain). G4 gate Part 2 blocked until af=0.
status: open
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [g4-gate, deribit, options_chain]
related: [plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md]
created: 2026-07-03
author: unknown
parent_epic: cefi_master
priority: P0
source: [plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md]
assigned_vm: NA
execution_scope: human
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-29
locked_by:
context_scope:
  [
    /plans/archive/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md,
    /plans/archive/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md,
    market-tick-data-service/market_tick_data_service/scripts/reclass_cefi_futures_chain_no_tardis_source.py,
    deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh,
  ]
locked_since:
resolved_by:
archive_exempt: true # 2026-08-19 (plan_reconciler) — 0 open checkboxes only because the sole real item was
  # reformatted from a bare "- [ ]" into the non-checkbox CANCELLED/SUPERSEDED disposition format (task_template.md
  # §3); the doc's own body (line ~229) explicitly says "Do NOT close it as done. Real fix is gated on Track-2." —
  # genuinely still blocked pending cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md's open
  # re-verify todo, not fully done. Re-check for real archival once that gate clears.
---

# DERIBIT `options_chain` af=10,114 (cap=1) — G4 gate blocker

## What I found

The cefi prd manifest (2026-07-03T10:41Z) shows DERIBIT options_chain:

- `attempted_failed` = 10,114
- `captured` = 1

**CROSS-LINK added 2026-08-18 (plan_reconciler)**: `cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md`
(2026-08-09 entry) confirms DERIBIT `futures_chain` shares the SAME canonical-write-only vulnerable path fixed for
BINANCE-FUTURES/BYBIT, but explicitly does not confirm whether DERIBIT `options_chain` (this doc's own blocker) is
covered by the same fix — worth checking against that fix before assuming this blocker needs a separate resolution.

This means the wave-1 Deribit options_chain backfill nearly completely failed. The G4 gate requires "Deribit OPTION
present as options_chain ONLY" — options_chain af>0 blocks G4.

## Root cause investigation

Tardis API confirms: 426,474 Deribit option symbols with `options_chain` data type, available since 2019-03-30. Source
data IS available (not a structural absence like `futures_chain`).

The failure was most likely:

1. Wave-1 Deribit light VMs were preempted (SPOT) and restarted, leaving incomplete coverage
2. Memory/OOM on older SPOT machine types (426K symbols bundled in-memory per date)
3. Rate limiting / transient Tardis API errors during the wave-1 run

## Mitigation

Wave-1 reprobe (2026-07-03T10:56Z) includes DERIBIT in `VENUES`, which will launch:

- `cefi-deribit-<year>-light` VMs (options_chain + derivative_ticker + futures_chain)
- Machine type: `n2-highmem-16` (registry floor for DERIBIT — sufficient memory for bundling)

After reprobe completes, expect options_chain af → 0 (or near-zero with any genuinely missing historic dates pre-2019).

## Resolution gate

Run `measure_honest_coverage.py --asset-group cefi` after reprobe VMs complete. Gate: DERIBIT options_chain
`attempted_failed` = 0.

If options_chain still shows af > 1,000 after reprobe, escalate to operator for investigation into Tardis rate limits or
machine sizing for Deribit bundling.

## Open actions

- [x] [VERIFY] P0. **[already covered by plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md, see that
      doc for execution]** Verify DERIBIT options_chain af after wave-1 reprobe VMs complete (ETA: 1-3 hours)
- [x] [MONITOR] P1. **[already covered by plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md, see that
      doc for execution]** If af > 0 after reprobe: check DERIBIT light VM logs for OOM/preemption evidence
- [x] [OPS] P1. **[already covered by plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md, see that doc
      for execution]** Close issue when DERIBIT options_chain af=0 in prd manifest

> **⚠️ CORRECTION (operator, 2026-07-18): the "structurally-absent channel" premise below is WRONG — do NOT reclass or
> writer-gate `futures_chain` to `expected_unattempted`/`empty_confirmed`.** `futures_chain`/`options_chain` are NOT
> Tardis channels — they are OUR per-underlying SHARD BUNDLES: MTDS calls Tardis PER SYMBOL (normal) for the ordinary
> data types (`trades`/`book_snapshot_5`/`derivative_ticker`/`liquidations`/`options_chain`) and AGGREGATES them by
> underlying into `…/data_type=futures_chain/underlying={U}/ticks.parquet`. The `instrument_id` type stays
> FUTURE/OPTION; the shard failure + aggregation are ON OUR SIDE. So the 112,727 / 100% `attempted_failed` is a REAL
> capture gap (the per-symbol dated-futures data didn't capture → the bundle never built — consistent with the ~350x
> throughput collapse, `cefi_tardis_throughput_collapse_350x_2026_07_17.md`), NOT a source absence. **The correct fix is
> to CAPTURE the per-symbol data + build the bundle** (now viable — throughput fixed @14 MB/s), tracked under the
> Track-2 coverage backfill (`cefi_consolidated_closeout_2026_07_18.md`). The 2026-07-12 reclass +
> `reclass_cefi_futures_chain_no_tardis_source.py` are built on the same confusion and must NOT be re-run for
> futures_chain.

- **[DATA] P0. CANCELLED — SUPERSEDED 2026-07-18 (correction banner above: `futures_chain`/`options_chain` are OUR
  bundles, not source absence; the fix is capture via the Track-2 coverage backfill, not a retry-gate/reclass).
  Reformatted 2026-08-18 (plan_reconciler) from a bare `- [ ]` into the required non-checkbox disposition marker per
  `task_template.md` §3 — the checkbox previously stayed open despite the doc's own inline "← SUPERSEDED" note.
  Original text retained below for archaeology.** `futures_chain` retry path must STOP attempting a
      structurally-absent channel (re-opened 2026-07-15, plan-reconcile §1, operator ruling A — this doc now owns it).
      `cefi_deribit_binance_futures_bundle_verification_2026_06_20.md` recorded 66,007 `attempted_failed` cells
      reclassed to `empty_confirmed`/`EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE` on 2026-07-12, treating it as settled.
      It is **NOT durable**: this doc's own 2026-07-15 triage reads **112,727 / 112,727 attempted_failed (100.0%, 0
      captured)** — the population GREW past the 66,007 that were reclassed, so each retry is re-stamping
      `attempted_failed` over the reclass. The structural finding stands (no CeFi Tardis venue exposes a `futures_chain`
      channel — verified via `GET /v1/exchanges/<exch>`), which is exactly why re-reclassifying is the wrong fix: it
      would be overwritten again. Gate the shards at the WRITER so a structurally-absent channel is never attempted
      (`expected_unattempted`, not attempt-then-fail-then-repair). Data-pipeline-correctness HARD RULE — an honest
      manifest must not carry `empty_confirmed` for cells the pipeline is actively re-failing. Likely shares a root
      cause with the `options_chain` items above (same `cefi-deribit-<year>-light` VM class bundles options_chain +
      derivative_ticker + futures_chain).

## 2026-07-15 corroboration — still unresolved 12 days later, `futures_chain` shows the identical pattern

Corroborating from a `#data-pipeline-alerts` `DP_RUN_MOSTLY_EMPTY` batch (window 2026-07-14 23:50Z–2026-07-15 00:19Z),
triaging cefi/tradfi 100%-failed cells against `market-data-tick-cefi-prd-central-element-323112`:

- **cefi `options_chain`**: 113,595/113,596 attempted_failed (99.999%) — same near-total-failure shape as this doc's
  original 2026-07-03 finding (af=10,114, captured=1), just an order of magnitude larger denominator from 12 more days
  of retry accumulation. **Still open** — no `[x]` on the "Open actions" above; the G4 gate blocker has not been
  cleared. Did not re-verify the reprobe VMs' live status in this pass (read-only manifest-count triage only) — the
  "Open actions" verify/monitor/close todos above remain the right next steps for whoever picks this up.
- **cefi `futures_chain`**: 112,727/112,727 attempted_failed (**exactly** 100.0%, 0 captured) — NOT previously tracked
  under this doc's title (which only names `options_chain`), but this doc's own "Mitigation" section already scopes the
  wave-1 reprobe VMs as `cefi-deribit-<year>-light` bundling **options_chain + derivative_ticker + futures_chain**
  together on the same machine — so a preemption/OOM root cause on that VM class would plausibly hit all three
  data_types, not just options_chain. `futures_chain`'s 100.0% (vs `options_chain`'s 99.999%) is consistent with
  `futures_chain` never having even the 1 lucky capture options_chain got. **Do not conflate this with**
  `bybit_futures_chain_write_shape_2026_07_13.md` — that doc is about BYBIT `futures_chain` rows being written to the
  WRONG PATH SHAPE (still `capture_status=captured`, just non-canonical hive layout), a completely different failure
  mode from DERIBIT `futures_chain` never capturing at all. Recommend the reprobe-verification todo above be widened to
  check `futures_chain` af alongside `options_chain` af before this issue is closed.
- Not independently re-diagnosed (root cause + fix path is exactly what this doc already describes) — filed as a
  corroborating note per the triage task's instruction to annotate rather than duplicate.

## 2026-07-26 re-verify (slot-4, `data_engineering`, task `cefi_satellite_ao_dispatch_batch2-013`) — still open; NOT

## closeable yet because the remediation plan hasn't run

Fresh manifest read (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, DERIBIT
rows only, 2026-07-26):

| data_type       | `attempted_failed` | `empty_confirmed` | `captured` |
| --------------- | -----------------: | ----------------: | ---------: |
| `options_chain` |            113,615 |            10,096 |          1 |
| `futures_chain` |            112,728 |            10,983 |          0 |

Both counts are essentially unchanged from the 2026-07-15 corroboration (113,595/112,727) — 20/1 rows drifted, not a
meaningful change, and both are still ≫1,000. **Verdict: FAIL — this gate is still blocked.**

**Did NOT do either of the doc's two prescribed next steps as originally written**, because both are now stale:

1. The "Resolution gate" section above prescribes escalating to the operator for "Tardis rate limits or machine sizing"
   — that framing was already **superseded by the 2026-07-18 correction banner** in this same doc: the real cause is not
   rate-limiting/sizing, it's that `options_chain`/`futures_chain` are OUR per-underlying bundles that never captured
   the underlying per-symbol data, and the fix is the Track-2 coverage backfill. Re-escalating the old framing would
   reopen an already-debunked investigation.
2. The batch2-013 todo's fallback ("if still ~100% af after the coverage backfill ran, file a new issue doc") also does
   not apply **because the coverage backfill has not run at all yet** — traced this via a sibling task this same session
   (`cefi_satellite_ao_dispatch_batch2-008`, `issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md`'s Progress
   Log): Track 2 was forked 2026-07-25 to `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`, which is
   `status: draft` and machine-gated (`gate_on_depends: true`) on
   `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` — and that gating plan itself is
   `status: draft`, 0/5 todos done, no Progress Log. There is no "post-backfill manifest" to check yet, and filing a new
   issue doc for "the backfill didn't fix it" would misrepresent a backfill that hasn't been attempted as one that
   failed.

**Not closing this doc.** `status` stays `open`; this is not a fresh finding needing a new issue doc, it is the same
already-tracked blocker (this doc's own correction banner + the Track-1→Track-2 dependency chain) still pending its
prerequisite. The correct re-check trigger is the Track-2 plan's own POST-BACKFILL `/data-pipeline-check-mtds`
checkpoint todo landing — whoever runs that checkpoint should re-read DERIBIT `options_chain`/`futures_chain` af
specifically (the checkpoint's own scope doesn't name DERIBIT explicitly, per batch2-013's own note) and update this doc
then.

## 2026-07-29 — `data_pipeline_failure` escalation worker near-miss (agt-79063c): re-ran the banned reclass, caught + reverted same session

A fresh `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) CRITICAL page fired for `asset_group=cefi data_type=futures_chain`
(115,661/115,661 attempted_failed, 100% ratio) and dispatched a one-shot `data_pipeline_failure` escalation worker with
**no issue doc pre-linked in its boot context** (context said "Filed issue: none — alert carries the details"). Without
first grepping `plans/active/issues/` for existing futures_chain/DERIBIT coverage, the worker independently re-derived
the STALE 2026-07-03 premise from `reclass_cefi_futures_chain_no_tardis_source.py`'s own docstring (Tardis has no
futures_chain channel for CeFi venues) and took two actions that this doc's own 2026-07-18 correction banner explicitly
prohibits:

1. Removed `futures_chain` from `DATA_LIGHT_PERPS`/`DATA_LIGHT_DERIBIT` in both
   `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh` and its AWS twin (shipped
   `deployment-service@5c172dc`).
2. Ran `reclass_cefi_futures_chain_no_tardis_source.py --apply` against the live prod cefi manifest, flipping exactly
   115,661 `attempted_failed` cells to `empty_confirmed/EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE` — the SAME script this
   doc's banner says "must NOT be re-run for futures_chain."

**Caught in the same session** while reading this doc as part of triaging the sibling cluster doc
(`cefi_high_attempted_failed_batch_cluster_2026_07_23.md`, which cross-links here). Reverted both actions before session
end:

- **Manifest**: reconstructed the exact revert mask (data_type=futures_chain AND capture_status=empty_confirmed AND
  error_reason=EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE), gate-checked (rows/captured unchanged, af delta = empty delta
  = 115,661), applied directly to
  `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`. Post-revert
  `capture_status` counts (`attempted_failed=997,332`, `empty_confirmed=1,318,000`) are byte-identical to the
  pre-mistake baseline read at session start. Original `error_reason` was reconstructed with high confidence for 112,700
  of the 115,661 rows (exact day+venue match to this doc's own documented 2026-07-03/07-04 DERIBIT 403-storm population
  → restored `UNCLASSIFIED:Tardis HTTP 403`) and 2,442 rows (exact day+venue match to the sibling doc's documented
  2026-07-15/07-16 404 tail → restored `UNCLASSIFIED:404 GET https`); the remaining 519 rows (small daily
  2026-07-26..07-29 batches, newer than any existing investigation) could not be attributed with confidence and were
  honestly labeled `RECLASS_REVERT_ORIGINAL_REASON_UNKNOWN_2026_07_29` rather than guessed. Snapshot of the post-mistake
  (pre-revert) state preserved at `_index/snapshots/pre_futures_chain_erroneous_reclass_revert_20260729.parquet` before
  writing.
- **Code**: `deployment-service@d6dcb97` (`revert: undo erroneous futures_chain removal from cefi Tardis launchers`,
  reverts `5c172dc`) — both launchers restored to including `futures_chain` in their light bundles, QG-green, shipped
  via quickmerge.

**No net change to the manifest or launcher config from this escalation** — this doc's blocker is UNCHANGED and still
gated on Track-2 exactly as before. **Process gap this exposes**: a `data_pipeline_failure` escalation worker's boot
context did not include a pre-dispatch check against `plans/active/issues/` for an already-open, already-corrected
investigation on the exact `(asset_group, data_type)` tuple — this is the SAME gap already filed in
`dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md` (there scoped to redundant re-diagnosis; this incident
additionally shows the gap can lead to a worker actively UN-doing an already-shipped correction, which is a stronger
argument for that issue's Option A). Cross-linked from there.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - the one open todo is deliberately
  left unchecked as SUPERSEDED-by-correction-banner (ruled-out, not completed); a 2026-07-29 escalation worker already
  re-ran the banned reclass from it and had to revert. Do NOT close it as done. Real fix is gated on Track-2.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — dropped a stale, unreferenced
  `utl_uac_skew_fleet_audit_2026_07_15.md` entry and added the two source scripts this doc's Progress Log names directly
  (the banned reclass script + the light-VM launcher that was edited/reverted 2026-07-29).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — genuine data-pipeline-correctness
  blocker (DERIBIT options/futures chain ~100% attempted_failed); the doc's own 2026-07-18 correction banner rules out
  the literal action in its remaining open checkbox, leaving no bounded dispatchable action.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA-STALE (already-duplicated), citation-fix only —
  this doc's remaining ground (the futures_chain/options_chain gate, pending Track-2 actually running) is fully claimed
  by `cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md` (confirmed independently by
  `cefi_satellite_ao_dispatch_batch10_2026_08_08.md`'s "Archivable-after-planned-work" section, same-day, separate
  `/ag-closeout-audit` run: "fully claimed by `cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md`").
  Added that finalize doc to `related:`/`context_scope` below (was previously only citing the non-finalize
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`). Not reclassified (`assigned_vm` stays `NA`) — this is a
  stale-citation correction, not a dispatch decision, and the doc also carries `locked_by: live-defi-rollout` /
  `locked_since: 2026-05-21`, noted but not touched (no archival attempted here).

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — sole item's closure is gated on
  cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md's still-open [REVIEW] P2 re-verification todo (that
  todo explicitly re-checks the manifest and conditionally closes this doc; verified `- [ ]` open, not yet executed as
  of this run). Not yet ready to close here ahead of that gate.
**context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-19** [body-hash:8f46aa4e51f16a68]: N/A — 0 open checkboxes (the sole historical item is a non-checkbox CANCELLED/SUPERSEDED disposition marker, not a tracked todo). `archive_exempt: true` carries a same-day (2026-08-19, plan_reconciler) inline justification confirming this is correct: the doc's own body explicitly states the real fix is still gated on Track-2's open re-verify todo, genuinely not done. No verdict action needed beyond this confirmation.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
