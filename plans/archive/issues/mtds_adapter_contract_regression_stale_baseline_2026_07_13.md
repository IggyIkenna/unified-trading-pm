---
doc_type: issue
title:
  market-tick-data-service QG RED — check_adapter_contract_regression baseline stale since 2026-07-08
  perp_funding_handler retirement
summary: >
  bash scripts/quality-gates.sh fails repo-wide on market-tick-data-service with "4 file(s) regressed below baseline"
  from check_adapter_contract_regression: book_microstructure_handler.py (file missing/renamed, baseline expects 8
  calls), perp_funding_handler.py (9 calls, baseline 10), unified-api-contracts/.../honest_coverage.py (38, baseline
  41), unified-api-contracts/.../source_priority.py (file missing/renamed, baseline 1). Verified pre-existing and
  unrelated to my change: my commit (2a69bf1a, adding a new BYBIT reshape script) only added one new file and touched
  nothing else. perp_funding_handler.py's contract-call count dropped from a LEGITIMATE refactor — commit ba6df0ac
  (2026-07-08, "retire standalone perp_funding for HYPERLIQUID/ASTER/PACIFICA-SOLANA/LIGHTER-ZKSYNC in favor of
  derivative_ticker.funding_rate") — that landed 5 days ago and the baseline was never regenerated afterward.
status: resolved
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [qg-red, adapter-contract-regression, repo-blocker, stale-baseline]
related: [plans/archive/2026_07/bybit_futures_chain_write_shape_migration_2026_07_13.md]
created: 2026-07-13
parent_epic: mtds_mdps_master
priority: P1
source:
  bybit_futures_chain_write_shape_migration-004 dispatch, slot 14, 2026-07-13 (blocked while shipping an unrelated
  reshape script)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
locked_by:
resolved_by: unified-trading-pm@ba098a7cc (slot 3)
---

# market-tick-data-service QG RED — adapter-contract-regression baseline stale

## What I found

`bash scripts/quality-gates.sh --no-fix` on `market-tick-data-service` at HEAD (`2a69bf1a`, my own unrelated commit
adding `scripts/reshape_bybit_futures_chain_glued_to_hive_2026_07_13.py`) fails:

```
[FAIL] market-tick-data-service/.../book_microstructure_handler.py: 0 contract calls < baseline 8 (file missing or renamed).
[FAIL] market-tick-data-service/.../perp_funding_handler.py: 9 contract calls < baseline 10.
[FAIL] unified-api-contracts/.../honest_coverage.py: 38 contract calls < baseline 41.
[FAIL] unified-api-contracts/.../source_priority.py: 0 contract calls < baseline 1 (file missing or renamed).
[check_adapter_contract_regression] 4 file(s) regressed below baseline.
```

Verified pre-existing, not caused by my commit — `git show --stat HEAD` shows my only change is the new, unrelated
reshape script; no dependency pins, handler files, or the baseline file itself were touched.

- **`book_microstructure_handler.py`**: does not exist anywhere in the current tree
  (`find . -iname book_microstructure_handler.py` — no match) — deleted at some undetermined earlier point, baseline
  never updated to match.
- **`perp_funding_handler.py`**: currently 9 contract calls (verified via direct grep), baseline expects 10. Its last
  touching commit is `ba6df0ac` (2026-07-08, "retire standalone perp_funding for HYPERLIQUID/ASTER/PACIFICA-SOLANA/
  LIGHTER-ZKSYNC in favor of derivative_ticker.funding_rate" — the SAME retirement already cross-referenced in
  `aster_cefi_data_defi_bucket_migration_2026_07_13.md` Phase 1 Todo 3's investigation this session). This is a
  LEGITIMATE refactor-driven count decrease (fewer venues handled = fewer classify/record calls needed), not an
  accidental lint-sweep wipe like the 2026-05-20 precedent this same gate cites — the baseline simply was never
  regenerated after that 5-day-old, intentional change.
- **`unified-api-contracts` files** (`honest_coverage.py`, `source_priority.py`): both exist in my tab-14 clone
  (`source_priority.py` is NOT missing in my worktree — the "file missing or renamed" message must be reading a
  different/stale reference than my live clone, not investigated further, cross-repo and out of this dispatch's scope).

## Why it matters

- Blocks EVERY subsequent commit to `market-tick-data-service` from any slot until fixed — same repo-wide green-tree
  impact as the earlier `migrate_sports_canonical_v9.py` 900-line regression this session.
- I hit this while trying to ship `scripts/reshape_bybit_futures_chain_glued_to_hive_2026_07_13.py`
  (`bybit_futures_chain_write_shape_migration_2026_07_13.md` Phase 2 Todos 1+2) — that work is DONE and committed
  locally (`2a69bf1a`) but cannot land until this clears.

## Recommended decision

Regenerate `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml` for the 3 legitimately-changed
files (`perp_funding_handler.py`'s intentional 10→9 drop, and drop/rename entries for `book_microstructure_handler.py`
if it's genuinely gone) via `--regenerate-baseline` — but ONLY after confirming each drop is a real, intentional
refactor (not a silent wipe) — the `perp_funding_handler.py` case is already confirmed intentional per `ba6df0ac`'s own
commit message; `book_microstructure_handler.py`'s disappearance and the two `unified-api-contracts` entries need a
quick history check first (out of this data_engineering dispatch's scope — a mechanical baseline-regen after a 30-second
verification per file, not a design decision, but I did not want to blindly regenerate without confirming each
individually).

## Todos

- [x] [SCRIPT] P1. Confirm `book_microstructure_handler.py`'s deletion/rename is intentional (git log the deletion
      commit), confirm `unified-api-contracts` `honest_coverage.py`/`source_priority.py`'s count drops are intentional,
      then regenerate `adapter_contract_baseline.yaml` for all 4 files via `--regenerate-baseline`. Verify
      `bash scripts/quality-gates.sh` is green afterward. (repo: unified-trading-pm + market-tick-data-service) — ✅
      unified-trading-pm@ba098a7cc. All 4 drops confirmed intentional via git history: `book_microstructure_handler.py`
      deleted in `a4fb3d13` ("retire order_flow_imbalance feature — zero real consumers, zero production rows ever
      captured"); `perp_funding_handler.py` 10→9 from `ba6df0ac` ("retire standalone perp_funding for
      HYPERLIQUID/ASTER/PACIFICA-SOLANA/LIGHTER-ZKSYNC in favor of derivative_ticker.funding_rate");
      `honest_coverage.py` 41→38 + `source_priority.py` 1→0 from `06edd868` (900-line file-size split — counts verified
      landing exactly in the new `_honest_coverage_empty_reasons.py` (3 calls) and `_source_priority_provenance.py` (1
      call), nothing lost). Regenerated baseline confirmed to contain no OTHER decreases (workspace-wide diff showed
      only increases/new-files elsewhere — non-shrinking ratchet intact). `bash scripts/quality-gates.sh` full run green
      on both market-tick-data-service (sentinel 01f23b8c) and unified-trading-pm (sentinel re-verified green 3x across
      rebases: ae9083c/9ca5de6/1a14713). Landed via direct push under CLAUDE.md carve-out (3) ("PM scripts/** & any
      .github/** change that must reach main to unblock the pipeline") after 8 quickmerge attempts were structurally
      outraced by branch churn (QG runtime 400-900s under host-wide qg-governor K=1 contention vs. ~60-180s commit
      cadence on live-defi-rollout) — confirmed via `/blocked` (BLK-b6ed5e28), operator approved.
