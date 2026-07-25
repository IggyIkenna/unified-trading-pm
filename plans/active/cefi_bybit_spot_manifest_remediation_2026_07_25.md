---
doc_type: plan
title: Run the already-built BYBIT-SPOT manifest corrective scripts against production (never actually applied)
summary:
  bybit_spot_manifest_stray_captures_2026_07_07.md was flipped `resolved` and archived on 2026-07-14 on checkbox-only
  evidence (all code shipped), but a 2026-07-10 live-manifest read on record in
  instruments_remaining_work_audit_2026_07_10.md found row counts byte-identical to the original 2026-07-07 diagnosis --
  the two corrective scripts that ship in that doc were built, smoke-tested in code review, and gated, but never
  actually run with --apply against the real production manifest. Both scripts already exist, already target the correct
  (twice-ruled) UPPERCASE SPOT_PAIR casing, and already carry dry-run/--smoke/--apply modes with stop-on-surprise guards
  and pre-apply snapshots -- this plan is "verify state, then run the existing tools", not new development.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [honest-coverage, denominator-audit, layer-1, data-correctness, cefi, bybit-spot, manifest-surgery, gcs-purge]
related:
  [
    /plans/archive/issues/bybit_spot_manifest_stray_captures_2026_07_07.md,
    /plans/active/issues/instruments_remaining_work_audit_2026_07_10.md,
    /plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md,
    /plans/active/cefi_misc_audits_and_hygiene_2026_07_25.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
drift_direction: advance-code
sequential: true
depends_on: []
source:
  [
    "surfaced 2026-07-25 during a deeper cross-doc investigation of cefi_layer1_denominator_gaps_2026_07_03.md's
    archival readiness; instruments_remaining_work_audit_2026_07_10.md already independently found the same gap on
    2026-07-10",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Run the already-built BYBIT-SPOT manifest corrective scripts against production

## Context (read before dispatching any todo)

`bybit_spot_manifest_stray_captures_2026_07_07.md` (archived, `status: resolved`) diagnosed 135,444 anomalous
`venue=BYBIT-SPOT` rows in the cefi production manifest
(`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`) and shipped everything
needed to fix them:

- **53,785 rows mis-stamped `instrument_type=PERPETUAL`** (should be `SPOT_PAIR`, uppercase -- twice-ruled canonical
  casing, see below) -- fix script: `market-tick-data-service/scripts/relabel_bybit_spot_perpetual_itype_2026_07_07.py`
  (`market-tick-data-service@5611d9a7`).
- **53,934 rows under spot-nonsense `data_type`s** (`derivative_ticker`/`futures_chain`/`options_chain`/`ohlcv_1m`/
  `perp_funding`/`liquidations` -- none valid for a SPOT venue), all `capture_status=empty_confirmed` with
  `instrument_type=""` (zero captured rows each -- deleting them is LOSSLESS) -- purge script:
  `market-tick-data-service/scripts/delete_bybit_spot_spot_nonsense_manifest_2026_07_07.py`
  (`market-tick-data-service@aa8bb137`). Its own runtime gate refuses to run unless
  `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` is populated (so the enumerator stops re-seeding these rows on the next
  cron cycle) -- that gate landed same-day (`unified-api-contracts@ab6bc7e5`), so the script has been unblocked since
  2026-07-07.
- The remaining ~27,725 EMPTY-`instrument_type` rows under valid spot `data_type`s (`trades`/`book_snapshot_5`) are
  historical honest-absence rows that predate the forward-path fix (`mtds@9d21b133`, `mtds@60287d3e`) -- the source doc
  scoped BOTH corrective scripts to explicitly exclude this subset (left as legitimate historical honest-absence
  records, not a defect); **out of scope for this plan**, do not add a third corrective pass for it without a fresh
  operator decision.

**Casing is NOT an open question -- do not re-litigate it.** UPPERCASE `SPOT_PAIR` is the canonical `instrument_type`
value: (1) operator ruling 2026-07-12 (`plan_reconciliation_operator_decisions_2026_07_11.md` §A2, finding 66); (2)
`unified-api-contracts/unified_api_contracts/_instrument_enums.py`'s `InstrumentType` enum states it outright
("UPPERCASE values are the canonical standard") and every member's string value already equals its uppercase name; (3)
the system-wide casing directive (`cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`) rules the same for
cefi's manifest `instrument_type` COLUMN. Both scripts above were verified 2026-07-12 to already target uppercase
`SPOT_PAIR` -- no code change needed.

**Why this plan exists instead of just re-flipping the archived doc back to open:** the archived doc's own Progress Log
confirms "this was the LAST open todo... all todos now closed... -003 is now safe to run" (2026-07-12). Everything after
that point is pure execution against production, which deserves its own dispatch-tracked plan (this one) rather than
reopening a closed diagnosis doc. **This plan's `sequential: true`** -- todo 1 (re-verify current state) gates
everything else, since 18+ days have passed since the last live check and either script may have since been run by
someone else, or the manifest shape may have shifted.

## Todos

- [x] ✅ [DATA] P1. **Re-verify current production state before touching anything.** Read the LIVE consolidated cefi
      manifest (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, via
      `measure_honest_coverage._read_manifest("cefi")` or an equivalent bounded-column/predicate-pushdown read -- do NOT
      do a naive full-frame load, see the manifest-read efficiency note in
      `/codex/02-data/four-surface-reconciliation-procedure.md`) filtered to `venue == "BYBIT-SPOT"`. Reproduce the
      exact breakdown from the 2026-07-07 diagnosis (by `instrument_type`, by `data_type`, by `capture_status`) and
      compare against it. **Done when**: a Progress Log entry states plainly whether the row counts are (a) unchanged
      (both scripts still need to run, proceed to todos 2-3), (b) partially changed (one script ran, figure out which
      and proceed only with the other), or (c) already fully remediated (close this plan with evidence, nothing further
      to do). (repo: market-tick-data-service) -- **DONE 2026-07-25 (slot-6 data_engineering) -- case (b), PARTIALLY
      changed.** See Progress Log for full breakdown + evidence.
- [x] ✅ [OPERATOR] P1. **Run the PERPETUAL→SPOT_PAIR relabel** (only if todo 1 found it still needed).
      `cd market-tick-data-service && .venv/bin/python     scripts/relabel_bybit_spot_perpetual_itype_2026_07_07.py`
      (dry-run first, read the printed plan), then `--smoke` (relabels one shard, verify the `by_venue_instrument_type`
      split shows both `PERPETUAL` (remaining) and `SPOT_PAIR` (new) before continuing), then `--apply` (snapshots the
      pre-relabel manifest to `_index/snapshots/pre_bybit_spot_relabel_<UTC>.parquet` first, per its own built-in safety
      guard). Prod-bucket manifest mutation, human-gated per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`
      -- the script's own stop-on-surprise guards (refuses if `SPOT_PAIR` rows already exist for BYBIT-SPOT, if the
      PERPETUAL count is outside `[50_000, 60_000]`, or if any shard exceeds 400 rows) are the safety mechanism, not a
      substitute for a human running `--apply`. **Done when**: `by_venue_instrument_type` for BYBIT-SPOT shows the full
      ~53,785-row split to `SPOT_PAIR`, zero remaining `PERPETUAL` rows for this venue. (repo: market-tick-data-service)
      -- **VERIFIED-ALREADY-SATISFIED 2026-07-25 (slot-6 data_engineering), NO MUTATION RUN.** Live re-read + a dry-run
      of this exact script confirm 0 `PERPETUAL` rows remain and 226,319/226,319 BYBIT-SPOT rows already carry
      `SPOT_PAIR` (including 2021-12-04-dated rows). The Gate this todo names is met organically -- most likely a
      side-effect of the a1 forward-path fix (`mtds@9d21b133`) + uppercase-casing fix (`mtds@60287d3e`) combined with
      routine manifest-consolidation reprocessing since 2026-07-12, not this script's `--apply` (which nobody ran -- see
      Progress Log). No operator action needed; closing on verified end-state per this todo's own Done-when wording.
- [ ] [OPERATOR] P1. **Run the spot-nonsense manifest purge** (only if todo 1 found it still needed; independent of todo
      2 -- disjoint row sets, but keep sequential for a clean one-mutation-at-a-time production trail).
      `cd     market-tick-data-service && .venv/bin/python     scripts/delete_bybit_spot_spot_nonsense_manifest_2026_07_07.py`
      dry-run first, then `--smoke` (deletes one `perp_funding` shard row, verify), then `--apply` (snapshots first;
      refuses if `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` is still empty -- confirm this gate reads populated before
      running, it was shipped `unified-api-contracts@ab6bc7e5` 2026-07-07). Prod-bucket manifest mutation, human-gated
      per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`. **Done when**: `by_data_type` for BYBIT-SPOT
      shows only `{trades, book_snapshot_5}`, zero rows remain under
      `derivative_ticker`/`futures_chain`/`options_chain`/ `ohlcv_1m`/`perp_funding`/`liquidations`. (repo:
      market-tick-data-service) -- **⚠️ STILL NEEDED, AND THE SCRIPT ITSELF IS NOW STALE (found 2026-07-25, slot-6
      data_engineering).** The 53,934-row spot-nonsense problem is byte-identical to 2026-07-07/07-10 (same 6
      data_types, same per-type counts, still 100% `capture_status=empty_confirmed`, still 0 captured rows -- LOSSLESS
      to delete). BUT this script's `_target_mask` hard-requires `instrument_type == ""`, and that condition no longer
      holds: a LIVE dry-run today returns "rows to delete: 0" and then STOP-ON-SURPRISE fires ("53,934 rows ... carry
      instrument_type != ''") because these rows now carry `instrument_type=SPOT_PAIR` (same organic cause as todo 2's
      note above). **Before running this todo**: the script's identity filter needs a small maintenance fix -- drop or
      relax the `instrument_type==""` guard (the real identity is
      `venue + data_type-in-{6 nonsense types} +     capture_status=empty_confirmed + row_count=0`, not the itype value)
      -- then dry-run/`--smoke`/`--apply` per the updated script. Do not hand-wave past the script's own
      stop-on-surprise refusal; it is correctly protecting against exactly this kind of drift.
- [ ] [DATA] P2. **Re-measure cefi Layer-1** (`measure_honest_coverage.py` or the current canonical entry point --
      confirm which one is live per `/codex/02-data/honest-coverage-model.md`, tooling may have moved since 2026-07-07)
      after todos 2-3 land, and confirm the BYBIT-SPOT tuple closes cleanly (matches
      `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` = `{trades, book_snapshot_5}` exactly, no stray tuples for this
      venue). Record the before/after cefi Layer-1 % in this plan's Progress Log. (repo: instruments-service) -- **NOT
      YET -- dispatched to slot-2 2026-07-25 ahead of todo 3 landing (sequential prereq-chain gap: the auto-wired
      `completed_tasks` chains each task to its immediate PLAN-ORDER predecessor, i.e. this todo's task row chains to
      todo 2's, not todo 3's, so the dispatcher offered it before its real precondition was met -- worth a dispatcher
      note, not a plan defect). Ran `measure_honest_coverage.py --asset-group cefi` anyway (cheap, read-only, tooling
      confirmed still live/current) to record the honest BEFORE state -- see Progress Log. Confirmed the tuple does NOT
      close cleanly yet: BYBIT-SPOT still carries all 6 stray tuples (the spot-nonsense data_types), 0 missing tuples,
      cefi Layer-1 = 98.59% (71 expected / 70 present). Left this checkbox UNCHECKED and skipped the task back to the
      queue (BLOCKED, citing todo 3) rather than false-close it -- re-run this measurement after todo 3's `--apply`
      actually lands.**
- [ ] [PM] P3. **Close the loop**: once todos 1-4 land, add a corrective note to
      `plans/active/cefi_misc_audits_and_hygiene_2026_07_25.md` (which already flags this exact gap) citing this plan's
      commit(s), and confirm whether `bybit_spot_manifest_stray_captures_2026_07_07.md`'s archived `status: resolved` is
      now actually TRUE (it always claimed to be, retroactively made honest by this plan) or needs its own banner
      correction noting the 2026-07-10→2026-07-25 gap between "marked resolved" and "actually executed". (repo:
      unified-trading-pm)

## Codex SSOTs

- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` -- governs both `[OPERATOR]` production-mutation todos.
- `/codex/02-data/honest-coverage-model.md` -- Layer-1 measurement + the instrument_type casing ruling.
- `/codex/02-data/four-surface-reconciliation-procedure.md` -- bounded/predicate-pushdown manifest read pattern for todo
  1 (the consolidated cefi manifest is tens of millions of rows; a naive full-frame load risks OOM).

## Progress Log

- **2026-07-25** -- **Todo 1 DONE, todo 2 VERIFIED-ALREADY-SATISFIED, todo 3 confirmed still needed + its script found
  stale** (slot-6 data_engineering). Live bounded/predicate-pushdown read of the consolidated cefi manifest
  (`read_availability_index(bucket, columns=[venue,instrument_type,data_type,capture_status], filters=[("venue","==","BYBIT-SPOT")])`
  -- NOT a naive full-frame load) against
  `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`:

  ```
  total BYBIT-SPOT rows: 226,319   (was 135,444 on 2026-07-07/07-10 -- +90,875)

  by instrument_type: {'SPOT_PAIR': 226,319}   (was {'': 81,659, 'PERPETUAL': 53,785})
    -- 0 empty-itype rows, 0 PERPETUAL rows. 100% SPOT_PAIR, including 2021-12-04-dated rows.

  by data_type:
    trades              86,201   (was 40,755 -- +45,446)
    book_snapshot_5     86,184   (was 40,755 -- +45,429)
    derivative_ticker   13,350   (unchanged)
    futures_chain       13,350   (unchanged)
    ohlcv_1m            13,350   (unchanged)
    options_chain       13,350   (unchanged)
    perp_funding           267   (unchanged)
    liquidations            267   (unchanged)

  spot-nonsense subset (the 6 invalid-for-SPOT data_types), 53,934 rows total -- IDENTICAL to 2026-07-07 diagnosis (b):
    100% capture_status=empty_confirmed, same per-data_type split (13,350 x4 + 267 x2), 0 captured rows -- still
    LOSSLESS to delete, still fully present, untouched.

  valid-spot subset (trades + book_snapshot_5) capture_status split:
    captured 64,868 / expected_unattempted 102,348 / empty_confirmed 56,984 / attempted_failed 2,119
  ```

  **Verdict: case (b), PARTIALLY changed** -- not (a) unchanged (itype state moved materially), not (c) fully remediated
  (the 53,934-row spot-nonsense purge target is untouched).

  **Which script "ran"**: neither corrective script's `--apply` has a commit/log trail, and independently the cefi-wide
  canonicalization cutover (`complete_cefi_manifest_canonical_dedup_2026_07_17.py`, the thing that WOULD rewrite
  `instrument_type` casing/values at scale) is confirmed NOT yet applied -- its own plan
  (`cefi_migration_cutover_and_track8_completion_2026_07_25.md`) is `status: draft` with its `--apply` todo still
  unchecked. Ran both BYBIT-SPOT scripts in dry-run (read-only, no writes) against the live manifest for direct
  confirmation:
  - `relabel_bybit_spot_perpetual_itype_2026_07_07.py` (no args): "rows to relabel: 0" then its own STOP-ON-SURPRISE
    fires ("226319 BYBIT-SPOT rows already carry instrument_type=SPOT_PAIR") -- i.e. the target end-state this script
    exists to produce is ALREADY true.
  - `delete_bybit_spot_spot_nonsense_manifest_2026_07_07.py` (no args): "rows to delete: 0" then its own
    STOP-ON-SURPRISE fires on the _low_ end ("target row count 0 outside expected range [45000, 60000]") -- because its
    `_target_mask` hard-requires `instrument_type == ""`, and every one of the 53,934 target rows now carries
    `instrument_type=SPOT_PAIR` instead of `""`. The script's own identity filter is stale against current production
    state; it is not able to find or delete the (still fully present) rows it was built for.

  **Most likely mechanism** (stated for context, not required to close this todo): the a1 honest-absence-writer
  forward-path fix (`mtds@9d21b133`, wired through `_resolve_instrument_type(venue, data_type)`, keyed on VENUE only)
  - the uppercase-casing fix (`mtds@60287d3e`, 2026-07-12) landed between the 2026-07-10 confirm-unchanged read and
    today. `instrument_type` is not part of the manifest shard-atom key, so as shards get re-touched by routine
    consolidation/reprocessing (and as the cefi backfill-throughput-bug fix drove a large volume of new trades/
    book_snapshot_5 captures -- consistent with +90,875 total rows being ~100% concentrated in those two valid
    data_types while the enumerator-broadcast nonsense-data_type rows stayed exactly frozen, confirming the todo-(d)
    capability gate is holding and not re-seeding them), the field coalesces to the now-correct venue-keyed value even
    for historical dates -- without anyone running either corrective script's `--apply`. Not independently confirmed
    against a consolidator-run log; flagged as the leading hypothesis only.

  **Action taken this session**: flipped todo 2 to done (Gate independently verified met, no operator mutation needed)
  and added a note to todo 3 flagging that its script needs a small maintenance fix (drop/relax the
  `instrument_type==""` guard in `_target_mask` -- the real identity is
  `venue + data_type-in-{6 nonsense types} + capture_status=empty_confirmed + row_count=0`) before an operator can run
  it; the underlying 53,934-row purge target itself is unchanged and still needed. Did NOT edit the script or run
  `--smoke`/`--apply` -- out of this task's scope (todo 1, read-only re-verification) and the mutation remains
  `[OPERATOR]`-gated per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`.

- **2026-07-25 (slot-2 data_engineering)** -- **Todo 4 dispatched ahead of todo 3 (dispatcher gap), ran the
  re-measurement anyway to record the honest BEFORE state, left the checkbox unchecked, skipped back to queue.**
  `instruments-service/scripts/measure_honest_coverage.py --asset-group cefi` is confirmed still the live canonical
  entry point per `/codex/02-data/honest-coverage-model.md` (Layer-1 completeness + Layer-2 reachable %, schema_version
  2, writes `gs://central-element-323112-honest-coverage/<date>/coverage.json`) -- no tooling move since 2026-07-07. Ran
  it read-only (no `--apply`, no mutation):

  ```
  cefi Layer-1: denominator_status=INCOMPLETE, completeness_pct=98.59 (70/71 expected tuples present)
  cefi-wide missing_tuples: 1 -- (OKX, options_chain, trades) -- unrelated to BYBIT-SPOT
  cefi-wide stray_tuples:   86 total

  BYBIT-SPOT stray tuples (filtered from the 86): 6 -- exactly the todo-3 spot-nonsense set, all now carrying
  instrument_type=SPOT_PAIR (the same organic-coalesce cause noted in todo 1's Progress Log entry, not "" anymore):
    (BYBIT-SPOT, SPOT_PAIR, derivative_ticker)
    (BYBIT-SPOT, SPOT_PAIR, futures_chain)
    (BYBIT-SPOT, SPOT_PAIR, liquidations)
    (BYBIT-SPOT, SPOT_PAIR, ohlcv_1m)
    (BYBIT-SPOT, SPOT_PAIR, options_chain)
    (BYBIT-SPOT, SPOT_PAIR, perp_funding)
  BYBIT-SPOT missing tuples: 0
  ```

  **Verdict: the BYBIT-SPOT tuple does NOT close cleanly yet** -- this todo's own Done-when ("no stray tuples for this
  venue") is not met, because todo 3 (the spot-nonsense purge) has not run. This is expected and not a new finding -- it
  directly confirms todo 3's still-needed status from the prior entry. Did not flip this checkbox; did not claim
  closure. Re-run this exact measurement after todo 3's `--apply` lands to get the real after-state.

  **Dispatch-gap note (informational, not a plan defect)**: this task (`cefi_bybit_spot_manifest_remediation-004`) was
  offered to a worker before todo 3 completed. `sequential: true`'s auto-wired `completed_tasks` chains each task to its
  immediate plan-order predecessor (todo 4 -> todo 2, todo 3 -> todo 1) rather than to every semantically-required
  earlier todo the plan prose names ("after todos 2-3 land") -- there is no per-todo custom-prereq syntax to express
  "depends on todo 3 specifically, which is two todos back in a differently-ordered chain" (CLAUDE.md: "no per-todo
  prereq syntax -- prereqs come only from sequential/gate_on_depends"). Not filing a separate issue doc for this -- it's
  a known modeling limit of the sequential-chain feature, not a bug, and the practical mitigation (skip back to queue
  with reason_code=BLOCKED once the true dependency is discovered) worked as intended.
