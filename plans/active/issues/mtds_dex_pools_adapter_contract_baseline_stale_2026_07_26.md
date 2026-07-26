---
doc_type: issue
title:
  market-tick-data-service QG WARN — dex_pools_handler.py + _defi_manifest.py adapter-contract baseline stale after the
  2026-07-26 perf-bundle + catalog-freshness splits
summary: >
  check_adapter_contract_regression (quality-gates.sh 5.70/6) flags two files below their adapter_contract_baseline.yaml
  counts after the same session's/fleet's legitimate code-motion refactors: (1)
  market_tick_data_service/cli/handlers/dex_pools_handler.py drops 9→5 tracked contract calls
  (classify_venue_error/ADAPTER_FETCH_FAILED/record_captured/record_empty/record_zero_rows/record_failed/
  record_catalog_unavailable/record_shard_failure) because the defi perf-bundle todo
  (defi_satellite_ao_dispatch_batch2_2026_07_26.md) extracted the shard-build/apply loop into _dex_pools_subgraph.py's
  new build_dex_pools_shard_tasks/apply_dex_pools_shard_results (to keep dex_pools_handler.py under the codex 900-line
  file cap after adding the ParallelPerSymbolRunner fan-out) — _dex_pools_subgraph.py's own count rose 2→6 in the same
  commit, net 11→11 across the two files, verified zero calls actually lost (grep-counted both files before/after); (2)
  _defi_manifest.py drops 43→42 from an UNRELATED sibling-slot refactor (already merged to origin/live-defi-rollout
  before this session's commit landed) that extracted assert_defi_catalog_fresh + related preflight logic into a new
  _defi_catalog_freshness.py module (6 matching calls, no prior baseline entry) — same code-motion class, not
  investigated further here since it predates and is independent of the perf-bundle work. WARN-ONLY today
  (quality-gates.sh prints ⚠️ and does not set a non-zero exit) — did not block shipping the perf-bundle commit. Same
  class of issue as the resolved mtds_solana_defi_drift_adapter_contract_baseline_stale_2026_07_15.md precedent.
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [qg-warn, adapter-contract-regression, stale-baseline, dex-pools, perf-bundle]
related:
  [
    plans/active/issues/mtds_solana_defi_drift_adapter_contract_baseline_stale_2026_07_15.md,
    plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
  ]
created: 2026-07-26
parent_epic: defi_master
priority: P3
source: [defi_satellite_ao_dispatch_batch2-012 (MTDS DeFi perf bundle), quality-gates.sh run 2026-07-26]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-26
locked_since:
---

# dex_pools_handler.py + _defi_manifest.py adapter-contract baseline stale (2026-07-26)

## Facts

- `check_adapter_contract_regression` (quality-gates.sh 5.70/6) FAILs (warn-only) two files: "dex_pools_handler.py: 5
  contract calls < baseline 9" and "_defi_manifest.py: 42 contract calls < baseline 43."
- `dex_pools_handler.py` — verified pure code-motion, zero calls lost: grep-count before this session's commit was 9 (
  matching `adapter_contract_baseline.yaml`); after the perf-bundle split, `dex_pools_handler.py` itself has 5
  (`record_captured` ×1, `record_catalog_unavailable` ×1, `record_empty` ×1, `record_failed` ×1, `record_zero_rows` ×1 —
  the catalog-stale early-return path, which stayed in the facade), and the new
  `_dex_pools_subgraph.build_dex_pools_shard_tasks`/`apply_dex_pools_shard_results` functions (extracted to keep the
  facade under the codex 900-line file cap) carry 6 (`record_captured` ×4, `record_failed` ×1, `record_zero_rows` ×1).
  5 + 6 = 11 = the pre-split total across both files (9 in dex_pools_handler.py + 2 already in _dex_pools_subgraph.py's
  baseline) — no net loss.
- `_defi_manifest.py` — from an unrelated sibling-slot refactor already on `origin/live-defi-rollout` before this
  session's fresh-pull (commit `08439787`, "fix(cefi): make DERIBIT options-chain manifest shard-atom match the v6
  path..." batch): `_defi_catalog_freshness.py` is a brand-new file (no prior baseline entry) carrying 6 matching calls
  (`record_empty` ×2, `record_failed` ×4) — `_defi_manifest.py`'s own docstring line 3 now states "DeFi
  catalog-freshness preflight (`assert_defi_catalog_fresh` et al.) lives in ... _defi_catalog_freshness.py" for a moved
  `assert_defi_catalog_fresh` + preflight code path. Not investigated line-by-line beyond confirming the new file exists
  and carries offsetting calls — this predates and is independent of the perf-bundle diff, out of this task's scope to
  fully audit.
- The check is WARN-ONLY in current quality-gates.sh output (prints `⚠️  Adapter contract-call regression`, exit
  stays 0) — confirmed via the same run's `✅ ALL QUALITY GATES PASSED` banner, printed BEFORE this check executes, and
  the `.qg_last_passed_sha` sentinel write matching the shipped commit SHA.

## Recommended fix (not actioned here — outside this session's scope)

Regenerate `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml` via `--regenerate-baseline` for
`dex_pools_handler.py` + `_dex_pools_subgraph.py` (confirmed-safe code motion above), and separately for
`_defi_manifest.py` + `_defi_catalog_freshness.py` (needs its own confirmation pass by whoever owns that refactor, since
this doc did not fully verify it) — per the baseline tooling's own guidance ("re-run with --regenerate-baseline ONLY
after legit refactor that intentionally changes counts — never to mask a regression"). A single combined
`--regenerate-baseline` run covers both once both are independently confirmed safe.

## Progress log

- 2026-07-26: Filed while shipping `defi_satellite_ao_dispatch_batch2-012` (MTDS DeFi perf bundle). Discovered as a QG
  WARN after the file-size-cap-driven `_dex_pools_subgraph.py` extraction; verified my own contribution
  (dex_pools_handler <-> _dex_pools_subgraph) is pure code-motion with zero calls lost. Noted the `_defi_manifest.py`
  regression as an unrelated pre-existing condition from a sibling slot's merged work, not further audited here. Left
  open at P3 since it is warn-only and does not block shipping.
