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

- [ ] [DATA] P1. **Re-verify current production state before touching anything.** Read the LIVE consolidated cefi
      manifest (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, via
      `measure_honest_coverage._read_manifest("cefi")` or an equivalent bounded-column/predicate-pushdown read -- do NOT
      do a naive full-frame load, see the manifest-read efficiency note in
      `/codex/02-data/four-surface-reconciliation-procedure.md`) filtered to `venue == "BYBIT-SPOT"`. Reproduce the
      exact breakdown from the 2026-07-07 diagnosis (by `instrument_type`, by `data_type`, by `capture_status`) and
      compare against it. **Done when**: a Progress Log entry states plainly whether the row counts are (a) unchanged
      (both scripts still need to run, proceed to todos 2-3), (b) partially changed (one script ran, figure out which
      and proceed only with the other), or (c) already fully remediated (close this plan with evidence, nothing further
      to do). (repo: market-tick-data-service)
- [ ] [OPERATOR] P1. **Run the PERPETUAL→SPOT_PAIR relabel** (only if todo 1 found it still needed).
      `cd market-tick-data-service && .venv/bin/python     scripts/relabel_bybit_spot_perpetual_itype_2026_07_07.py`
      (dry-run first, read the printed plan), then `--smoke` (relabels one shard, verify the `by_venue_instrument_type`
      split shows both `PERPETUAL` (remaining) and `SPOT_PAIR` (new) before continuing), then `--apply` (snapshots the
      pre-relabel manifest to `_index/snapshots/pre_bybit_spot_relabel_<UTC>.parquet` first, per its own built-in safety
      guard). Prod-bucket manifest mutation, human-gated per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`
      -- the script's own stop-on-surprise guards (refuses if `SPOT_PAIR` rows already exist for BYBIT-SPOT, if the
      PERPETUAL count is outside `[50_000, 60_000]`, or if any shard exceeds 400 rows) are the safety mechanism, not a
      substitute for a human running `--apply`. **Done when**: `by_venue_instrument_type` for BYBIT-SPOT shows the full
      ~53,785-row split to `SPOT_PAIR`, zero remaining `PERPETUAL` rows for this venue. (repo: market-tick-data-service)
- [ ] [OPERATOR] P1. **Run the spot-nonsense manifest purge** (only if todo 1 found it still needed; independent of todo
      2 -- disjoint row sets, but keep sequential for a clean one-mutation-at-a-time production trail).
      `cd     market-tick-data-service && .venv/bin/python     scripts/delete_bybit_spot_spot_nonsense_manifest_2026_07_07.py`
      dry-run first, then `--smoke` (deletes one `perp_funding` shard row, verify), then `--apply` (snapshots first;
      refuses if `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` is still empty -- confirm this gate reads populated before
      running, it was shipped `unified-api-contracts@ab6bc7e5` 2026-07-07). Prod-bucket manifest mutation, human-gated
      per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`. **Done when**: `by_data_type` for BYBIT-SPOT
      shows only `{trades, book_snapshot_5}`, zero rows remain under
      `derivative_ticker`/`futures_chain`/`options_chain`/ `ohlcv_1m`/`perp_funding`/`liquidations`. (repo:
      market-tick-data-service)
- [ ] [DATA] P2. **Re-measure cefi Layer-1** (`measure_honest_coverage.py` or the current canonical entry point --
      confirm which one is live per `/codex/02-data/honest-coverage-model.md`, tooling may have moved since 2026-07-07)
      after todos 2-3 land, and confirm the BYBIT-SPOT tuple closes cleanly (matches
      `VENUE_DATA_TYPE_CAPABILITIES["BYBIT-SPOT"]` = `{trades, book_snapshot_5}` exactly, no stray tuples for this
      venue). Record the before/after cefi Layer-1 % in this plan's Progress Log. (repo: instruments-service)
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
