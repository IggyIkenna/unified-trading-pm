---
doc_type: issue
title:
  phoenix_orderbook_handler.py adapter-contract-call regression — 3/6 baseline calls missing (classify_venue_error +
  ADAPTER_FETCH_FAILED entirely absent)
summary: |
  MTDS quality-gates.sh STEP 5.83 (`check_adapter_contract_regression.py`, the per-file non-shrinking contract-call
  ratchet built specifically to catch the 2026-05-20 lint-sweep regression class — see
  `plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md`) reports `[FAIL]` for
  `market-tick-data-service/market_tick_data_service/cli/handlers/phoenix_orderbook_handler.py`: baseline expects 6
  contract-pattern occurrences (`adapter_contract_baseline.yaml:383-384`), only 3 are present today
  (`record_captured` L458, `record_zero_rows` L468, `record_failed` L498). `classify_venue_error` and
  `ADAPTER_FETCH_FAILED` do not appear in the file AT ALL — meaning error classification on this handler's fetch path
  is currently silent/uncategorized, not just under-counted. **Surfaced 2026-07-26 during an unrelated DeFi-lending QG
  run** (this file was not touched by that session); this STEP 5.83 check runs AFTER the "ALL QUALITY GATES PASSED"
  banner in the current script ordering, so it did NOT block that ship — worth checking separately whether 5.83
  should be moved earlier / made hard-blocking, since as positioned it can pass silently alongside a real regression.
  **Suspect commit** (not confirmed, just the most likely candidate from file history): `cddb1226` "coverage 65→82% +
  codex violations 15→0" — a large sweep commit, the exact shape of regression this checker's docstring cites as its
  motivating incident. Not yet verified via `git log -p` / `git blame` on the removed lines.
status: open
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, contract-regression, error-handling, phoenix, adapter-contract-baseline]
related:
  [
    /plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
resolved_by:
source:
  chat finding during defi_lending_writer_retire_prerequisite_2026_07_20.md session-3, flagged to operator, fix
  requested 2026-07-27
depends_on: []
---

# phoenix_orderbook_handler.py adapter-contract-call regression

## Todos

- [ ] [CODE] P2. **Root-cause the regression** — `git log -p --follow` / `git blame` on
      `market-tick-data-service/market_tick_data_service/cli/handlers/phoenix_orderbook_handler.py` around the removed
      `classify_venue_error`/`ADAPTER_FETCH_FAILED` call sites (and whichever 3rd pattern of the 5 remaining ones —
      `record_empty`/`record_catalog_unavailable`/`record_shard_failure` — was also present at baseline-capture time) to
      confirm which commit dropped them and why (confirm or rule out `cddb1226`). (repo: market-tick-data-service)
- [ ] [CODE] P2. **Restore proper error classification on the fetch path** — add `classify_venue_error()` +
      `ADAPTER_FETCH_FAILED` emission per `/codex/04-architecture/shard-level-failure-isolation.md`'s per-shard `except`
      discipline (the SAME contract every other MTDS handler follows), verified against what the file's own surrounding
      handlers (`position_data_handler.py`, baseline count 4, is a smaller same-shape example) do today — do not just
      restore whatever the removed lines said blind; make sure it fits the CURRENT handler shape. (repo:
      market-tick-data-service)
- [ ] [TEST] P2. **Verify STEP 5.83 goes green** for this file
      (`python     scripts/quality_gates/check_adapter_contract_regression.py --workspace-root <ws>` or the full
      `quality-gates.sh` run) and add/confirm a unit test exercises the fetch-failure path so this can't silently
      regress again. (repo: market-tick-data-service)
- [ ] [PM] P3. **Check STEP 5.83's ordering in `quality-gates.sh`** — it currently runs after the "ALL QUALITY GATES
      PASSED" banner (observed 2026-07-26 MTDS run), meaning a real per-file contract regression can pass the gate.
      Confirm whether that's intentional (advisory-only by design) or a gap that should make 5.83 hard-blocking like the
      rest of STEP 5. (repo: market-tick-data-service)

## Evidence

```
[0;34m── [5.70/6] IS-MTDS CONTRACT INTEGRITY ──[0m
...
[FAIL] market-tick-data-service/market_tick_data_service/cli/handlers/phoenix_orderbook_handler.py: 3 contract calls < baseline 6. Patterns tracked: classify_venue_error | ADAPTER_FETCH_FAILED | record_captured | record_empty | record_zero_rows | record_failed | record_catalog_unavailable | record_shard_failure.
```

Baseline (`scripts/quality_gates/adapter_contract_baseline.yaml:383-384`):

```yaml
market-tick-data-service/market_tick_data_service/cli/handlers/phoenix_orderbook_handler.py:
  count: 6
```

Current file (533 lines) — only 3 of the 8 tracked patterns present: `record_captured` (L458), `record_zero_rows`
(L468), `record_failed` (L498).
