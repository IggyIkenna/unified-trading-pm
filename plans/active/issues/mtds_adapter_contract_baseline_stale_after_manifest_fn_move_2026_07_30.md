---
doc_type: issue
title:
  "market-tick-data-service adapter_contract_baseline stale after _emit_per_symbol_manifest moved files (QG 5.83 blocks
  quickmerge)"
summary:
  "quality-gates.sh STEP 5.83 (check_adapter_contract_regression.py) fails on tardis_batch_download.py (7 contract calls
  < baseline 11) because commit 064f872a legitimately MOVED _emit_per_symbol_manifest (and its classify_venue_error /
  record_failed / build_fetch_evidence / was_instrument_alive contract calls) from tardis_batch_download.py to
  tardis_cefi_shards.py, per the codex file-size ratchet — the baseline was never regenerated after the move, so the
  source file now reads as a regression even though the calls still exist, just in a different file. This is currently
  blocking ALL quickmerge pushes to market-tick-data-service, including an unrelated already-fixed STEP 5.101
  empty-string-fallback annotation (this repo's existing repo-blocker RB-88a81995 /
  mtds_empty_string_fallback_baseline_drift_2026_07_30.md)."
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, adapter-contract-regression, ci-blocking, baseline-stale]
related:
  [
    /plans/active/issues/mtds_empty_string_fallback_baseline_drift_2026_07_30.md,
    /plans/active/issues/lighter_zksync_derivative_ticker_tardis_numeric_market_id_leaks_into_symbol_schema_2026_07_29.md,
    /plans/archive/issues/mtds_adapter_contract_regression_stale_baseline_2026_07_13.md,
  ]
created: 2026-07-30
priority: P1
parent_epic: instruments_master
source:
  "mtds_empty_string_fallback_baseline_drift-001 (slot 6), 2026-07-30 — discovered while shipping the sibling STEP 5.101
  fix"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by: ""
locked_by: ""
---

# market-tick-data-service adapter_contract_baseline stale after manifest-fn move

## What I found

`bash scripts/quality-gates.sh` STEP 5.83 (`check_adapter_contract_regression.py`) fails with:

```
[FAIL] market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_batch_download.py: 7 contract calls < baseline 11.
```

Verified pre-existing and unrelated to my in-flight work (a clean `git status` on my worktree shows my own commit only
touched `tardis_cefi_shards.py`, never `tardis_batch_download.py`; the checker is a per-file static content scan, so an
edit to a different file cannot move this count). Root cause confirmed via `git show 064f872a`: that commit ("fix(cefi):
self-record captured manifest rows for LIGHTER-ZKSYNC derivative_ticker delegated Tardis path", slot-2, 2026-07-30)
moved `_emit_per_symbol_manifest` — including its `classify_venue_error` / `build_fetch_evidence` /
`was_instrument_alive` / `record_failed` / `record_zero_rows` call sites — from `tardis_batch_download.py` to
`tardis_cefi_shards.py` "per the codex file-size ratchet" (commit message, `tardis_batch_download.py` was at 893/900
lines). This is exactly the class of legitimate-refactor-not-regression the checker's own docstring anticipates
("`--regenerate-baseline` ONLY after legit refactor that intentionally changes counts — never to mask a regression").

Current baseline (`unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml`):
`tardis_batch_download.py: count: 11` (stale — pre-move). `tardis_cefi_shards.py` is not yet a baseline-tracked file at
all (the checker only reads baseline-LISTED files, so the moved-to file is currently unchecked).

Same class of issue as the archived `plans/archive/issues/mtds_adapter_contract_regression_stale_baseline_2026_07_13.md`
— a file-move without a baseline regen.

## Why it matters

Blocks every quickmerge push to `market-tick-data-service` regardless of what the push touches — currently blocking my
own already-QG-clean STEP 5.101 empty-string-fallback fix (`mtds_empty_string_fallback_baseline_drift-001`) from
shipping, and by extension keeps the existing repo-blocker `RB-88a81995` (condition
`repo-market-tick-data-service-qg-green`) open even after its own root cause is fixed — slot 14's
`tradfi_recovery_quarantine_registration_gap-003` is also waiting on that same condition.

## Recommended decision

- [ ] [SCRIPT] P1. Confirm no contract calls were silently dropped (not just moved) by diffing `064f872a` for both files
      — grep
      `classify_venue_error|ADAPTER_FETCH_FAILED|record_captured|record_empty|record_zero_rows|record_failed|record_catalog_unavailable|record_shard_failure`
      counts in `tardis_cefi_shards.py` pre/post the move landed elsewhere, and confirm the sum of
      (`tardis_batch_download.py` new count) + (`tardis_cefi_shards.py` new count) is >= the old
      `tardis_batch_download.py` baseline (11). Repo: market-tick-data-service. **Done when**: counts reconciled and
      stated in the commit message of the next todo.
- [ ] [SCRIPT] P1. Run
      `.venv/bin/python scripts/quality_gates/check_adapter_contract_regression.py --workspace-root <ws> --regenerate-baseline`
      from `unified-trading-pm` to pick up the new per-file counts (lowers `tardis_batch_download.py`, adds/raises
      `tardis_cefi_shards.py`), then commit the updated `adapter_contract_baseline.yaml` via `docs(plans):`-equivalent
      conventional commit (this is a QG baseline file, not a plan — use a `chore(qg):` prefix) + quickmerge. Repo:
      unified-trading-pm. **Done when**: `bash quality-gates.sh` in market-tick-data-service STEP 5.83 reports OK and
      the full quality-gates.sh run exits 0.
- [ ] [SCRIPT] P2. Once green, verify repo-blocker `RB-88a81995` (`repo-market-tick-data-service-qg-green`) actually
      flips green (both this issue's fix AND the sibling STEP 5.101 fix must have landed) — if the watcher doesn't
      auto-resolve within its normal poll window, escalate. Repo: agent-orchestrator (verification only, no code change
      expected). **Done when**: RB-88a81995 shows `resolved_at` set.
