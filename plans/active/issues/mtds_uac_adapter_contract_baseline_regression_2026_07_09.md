---
doc_type: issue
title: MTDS + UAC adapter-contract-call baseline regression (4 files, warn-only)
summary:
  check_adapter_contract_regression (STEP 5.70, warn-only) reports 4 files below their committed contract-call baseline
  — book_microstructure_handler.py missing/renamed, perp_funding_handler.py 9<10, and two unified-api-contracts
  crosscutting files below baseline. Pre-existing on committed HEAD, not caused by this session's Deribit migration
  work.
status: open
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [adapter-contract, baseline-regression, warn-only]
related: [mtds_adapter_contract_baseline_regression_2026_06_24]
created: 2026-07-09
parent_epic: instruments_master
assigned_vm:
resolved_by:
source: [market-tick-data-service quality-gates.sh STEP 5.70 check_adapter_contract_regression (warn-only post-gate)]
priority: P2
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

## What I found

While running `market-tick-data-service`'s `quality-gates.sh` to verify an unrelated, scoped fix (`deribit_ws.py`
live-classification bug, see `unified-trading-pm/docs` cross-link in `instruments-service/docs/CEFI_INSTRUMENTS.md`
"Live-vs-batch classification bug"), STEP 5.70 (`check_adapter_contract_regression`, warn-only — does NOT fail QG, exit
stays 0 per the 2026-06-24 precedent `plans/archive/issues/mtds_adapter_contract_baseline_regression_2026_06_24.md`)
reported 4 files below their committed adapter-contract-call baseline:

- `market-tick-data-service/market_tick_data_service/cli/handlers/book_microstructure_handler.py`: 0 contract calls <
  baseline 8 (**file missing or renamed** — does not exist on disk at HEAD)
- `market-tick-data-service/market_tick_data_service/cli/handlers/perp_funding_handler.py`: 9 contract calls < baseline
  10
- `unified-api-contracts/unified_api_contracts/canonical/crosscutting/honest_coverage.py`: 38 contract calls < baseline
  41
- `unified-api-contracts/unified_api_contracts/canonical/crosscutting/source_priority.py`: 0 contract calls < baseline 1
  (file missing or renamed)

Tracked patterns:
`classify_venue_error | ADAPTER_FETCH_FAILED | record_captured | record_empty | record_zero_rows | record_failed`.
Baseline SSOT: `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml`.

**Confirmed pre-existing, not caused by this session**: `git status --short` is clean for all 4 files in both repos at
the time of this finding (2026-07-09) — this is the committed HEAD state, not uncommitted WIP from this or any
concurrent session. This session's own diff touched only
`market-tick-data-service/market_tick_data_service/live/ connectors/deribit_ws.py` + its test file, and
`instruments-service` (catalog/by-date migration scripts + docs) — none of the 4 flagged files.

`book_microstructure_handler.py` and `source_priority.py` both being reported as "file missing or renamed" (0 real
contract calls, both below a nonzero baseline) suggests these files were deleted/renamed in a past commit without the
baseline being updated to match — the same failure mode as the 2026-06-24 precedent, but for different files. Not
independently re-diagnosed here (out of scope for the Deribit migration task that surfaced it) — needs the same
diagnose-before-fix treatment as the linked precedent: confirm whether each is a legitimate refactor (calls moved
elsewhere, baseline should be regenerated) or a real regression (contract calls actually dropped, should be restored).

## Why it matters

Same rationale as the linked 2026-06-24 precedent — this ratchet exists to catch the lint-sweep class of bug
(`lint_sweep_774602ea8_regression_audit_2026_05_20.md`: a sweep silently wiped 31 contract calls from kalshi.py +
polymarket_clob.py). A genuine drop below baseline means an adapter may no longer classify errors / emit
`ADAPTER_FETCH_FAILED` / record honest absence on every path — a data-pipeline correctness risk.

## Recommended decision

Diagnose-before-fix (read both sides) per file, then either regenerate the baseline (if calls legitimately moved) or
restore the missing contract calls (if a real regression). Non-urgent (warn-only, does not block QG/commits), but a
data-correctness-adjacent item that should not sit indefinitely — same owner class as the 2026-06-24 precedent.
