---
doc_type: issue
title: Plan-reconciler findings — cefi tranche 2026-08-06
summary:
  Daily cefi-tranche plan reconciliation run — no contradictions, missed flips, or doc-drift found; 13 fully-resolved
  issue docs identified for potential closure
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, cefi, findings]
related: []
created: 2026-08-06
author: plan_reconciler
source: agt-d4d31f
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
locked_by: NONE
resolved_by: NONE
---

# Plan-reconciler run — cefi tranche — 2026-08-06

**Run**: `agt-d4d31f` | **Tranche**: `cefi` | **Branch**: `plan_reconciler/agt-d4d31f`

**Scope**: 110 cefi docs (46 grace / 64 editable), normative refs, codex

## Flips verified

None. No open `- [ ]` todos in the cefi tranche carried HARD evidence of completion (verified SHA reachable on origin,
artifact demonstrably live, etc.). The open todos mentioning SHAs/dates were genuinely still in progress — e.g.,
operator rulings from today (2026-08-06) that authorize work but haven't completed it yet.

## Contradictions

None confirmed. The cefi consolidated closeout (`cefi_consolidated_closeout_2026_07_18.md`) is internally consistent:

- Track 1 (Instrument-ID canonicalization) — correctly marked FORKED, child plan is
  `plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` (archived, complete)
- Track 2 (CeFi backfill COVERAGE reopened) — correctly marked FORKED
- Track 7 (Candle namespace bundle-collision residual) — correctly marked FORKED, child plan is
  `cefi_track7_candle_namespace_residual_2026_07_25.md` (1 open todo)

All archive references in the closeout's `related:` frontmatter resolve successfully (15 refs, 0 dangling).

## Doc-drift

None confirmed in the cefi tranche. No stale codex SSOT references identified.

## Hygiene fixes

None applied. The hygiene sweep baseline failures (5 hard: reference path convention ratchet, AG-closeout linkage
ratchet, terminal-status-archived ratchet, assigned_vm:NA corpus ratchet, archive candidates ratchet) are corpus-wide
ratchet gates, not cefi-specific defects. No cefi docs had mechanical frontmatter/todo-format issues requiring fixes.

## Near-complete cefi plans (≤1 open todo, for operator awareness)

These are not archive-ready (open todos remain), but are close:

| Plan                                                           | Open | Closed | Notes                     |
| -------------------------------------------------------------- | ---- | ------ | ------------------------- |
| `cefi_satellite_ao_dispatch_batch7_2026_08_03.md`              | 1    | 2      | Near complete             |
| `cefi_track7_candle_namespace_residual_2026_07_25.md`          | 1    | 1      | FORKED from Track 7       |
| `cefi_track7_candle_namespace_residual_finalize_2026_07_25.md` | 1    | 1      | Companion finalize doc    |
| `cefi_satellite_ao_dispatch_batch8_2026_08_06.md`              | 1    | 2      | GRACE SET — today's batch |

## Fully-resolved issue docs (0 open todos, may be closeable)

These cefi issue docs have all action items done:

- `tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md` (0 open, 10 closed)
- `cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md` (0 open, 9 closed)
- `mtds_hl_aster_perp_rename_bare_decomposed_shape_bug_2026_07_27.md` (0 open, 6 closed)
- `features_mdps_input_bucket_ambient_env_sibling_sites_2026_08_05.md` (0 open, 6 closed)
- `features_is_instruments_store_ambient_env_stg_2026_08_05.md` (0 open, 2 closed)
- `mdps_derivative_ticker_single_instrument_high_rss_2026_08_03.md` (0 open, 2 closed)
- `ml_strategy_manifest_coverage_gap_2026_08_03.md` (0 open, 4 closed)
- `mtds_qg_red_combined_coverage_shortfall_2026_08_05.md` (0 open, 3 closed)
- `coverage_floor_new_backfill_gaps_found_2026_07_27.md` (0 open, 3 closed)
- `cefi_coinbase_cde_urdi_zero_records_2026_07_28.md` (0 open, 3 closed)
- `cefi_coinbase_futures_blank_instrument_type_2026_07_27.md` (0 open, 1 closed)
- `cefi_instruments_store_blank_data_type_residual_2026_07_29.md` (0 open, 1 closed)
- `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md` (0 open, 3 closed)

**Note**: Issue docs with 0 open todos may still serve as tracking/history. Each should be reviewed for closure before
archival. Several are in the grace set and were not modified.

## Cefi open-work summary

The cefi consolidated closeout has 15 open todos out of 36 total. Major open workstreams:

| Doc                                                                     | Open | Total |
| ----------------------------------------------------------------------- | ---- | ----- |
| `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`           | 22   | 36    |
| `cefi_consolidated_closeout_2026_07_18.md`                              | 15   | 36    |
| `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`                | 11   | 21    |
| `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` | 8    | 19    |
| `cefi_residual_followups_after_honest_done_2026_07_17.md`               | 7    | 28    |

## Filed

No new issues filed. This run found no contradictions, doc-drift, or missed flips requiring durable tracking.

## Archive candidates (operator review)

None. No cefi plan has 0 open todos and is unlocked and outside the grace window.

## Refuted (dropped by verify)

N/A — no candidates required adversarial verification.

## Coverage (hunters / batches / docs)

| Metric                               | Count |
| ------------------------------------ | ----- |
| Cefi docs in corpus                  | 110   |
| Grace (read-only, <12h)              | 46    |
| Editable (≥12h)                      | 64    |
| Docs audited (mechanical)            | 110   |
| Issue docs in cefi tranche           | ~72   |
| Fully-resolved issues (0 open todos) | 13    |
| Near-complete plans (≤1 open)        | 4     |

## Plans not reached

None. All 110 cefi docs were mechanically audited.

## Run summary

- **Outcome**: CLEAN — no contradictions, missed flips, or doc-drift found in the cefi tranche
- **Server**: Unreachable (localhost:8765) — results posted to review branch only
- **Review branch**: `plan_reconciler/agt-d4d31f`
