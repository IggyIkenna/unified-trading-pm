---
title: MTDS defi lending/liquidations handlers below adapter-contract-call baseline
created: 2026-06-24
author: ikennaigboaka [slot-1·planning]
source:
  - instruments-service quality-gates STEP 5.70 check_adapter_contract_regression (warn-only post-gate)
  - market-tick-data-service@02e50cb2
locked_by: live-defi-rollout
---

## What I found

`instruments-service` `quality-gates.sh` STEP 5.70 (`check_adapter_contract_regression`, a cross-repo
post-gate that scans `market-tick-data-service`) reports two MTDS handlers below their committed
adapter-contract-call baseline (warn-only — does NOT fail QG, exit stays 0):

- `market_tick_data_service/cli/handlers/lending_indices_handler.py`: **4 contract calls < baseline 5**
- `market_tick_data_service/cli/handlers/liquidations_handler.py`: **5 contract calls < baseline 6**

Tracked patterns: `classify_venue_error | ADAPTER_FETCH_FAILED | record_captured | record_empty |
record_zero_rows | record_failed`. Baseline SSOT:
`unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml`.

Pre-existing (NOT introduced by the sports work that surfaced it). The likely origin is
`market-tick-data-service@02e50cb2` ("per-instrument manifest grain for 6 lending/oracle handlers —
shared `_lending_grain.py` per-market + oracle per-feed") — a refactor that may have **legitimately**
extracted contract calls into a shared module, lowering the per-file count. MTDS tree is clean
(committed, not foreign WIP).

## Why it matters

The ratchet exists to catch the lint-sweep class of bug (incident
`lint_sweep_774602ea8_regression_audit_2026_05_20.md`: a sweep silently wiped 31 contract calls from
kalshi.py + polymarket_clob.py). A genuine drop below baseline means an adapter may no longer
classify errors / emit `ADAPTER_FETCH_FAILED` / record honest absence on every path — a data-pipeline
correctness risk for the defi lending/liquidations cells. BUT if 02e50cb2 moved the calls into
`_lending_grain.py` (per-market) the count drop is benign and the baseline should be regenerated.

## Recommended decision

Diagnose-before-fix (read both sides), then ONE of:

1. **Legit refactor** — if the contract calls now live in the shared `_lending_grain.py` / oracle
   per-feed helper that these two handlers call, regenerate the baseline:
   `adapter_contract_baseline.yaml` via the documented `--regenerate-baseline` path (ONLY after
   confirming the calls genuinely moved, never to mask a real regression).
2. **Real regression** — restore the missing `classify_venue_error` / `ADAPTER_FETCH_FAILED` /
   `record_*` calls in the two handlers so each fetch path classifies + emits honest absence.

Owner: MTDS / defi data-pipeline epic (`mtds_mdps_master`). Non-urgent (warn-only), but a defi
data-correctness item — should not sit indefinitely.
