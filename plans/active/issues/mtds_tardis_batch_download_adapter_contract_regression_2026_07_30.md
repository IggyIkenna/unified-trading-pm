---
doc_type: issue
title: "market-tick-data-service tardis_batch_download.py trips adapter-contract-regression baseline (7 < 11) — discovered incidentally, not investigated"
summary: >-
  While verifying an unrelated `instruments-service` fix locally (`ldr_qg_failure` escalation `agt-41a9d1`), the
  workspace-wide `check_adapter_contract_regression` STEP 5.70 check (which scans every sibling repo under
  `$WORKSPACE_ROOT`, not just the repo whose `quality-gates.sh` is running) flagged
  `market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_batch_download.py`: 7
  contract calls (`classify_venue_error`/`ADAPTER_FETCH_FAILED`/`record_captured`/`record_empty`/`record_zero_rows`/
  `record_failed`/`record_catalog_unavailable`/`record_shard_failure`) vs a baseline of 11. `market-tick-data-service`
  is clean and up to date with `origin/live-defi-rollout` (not local dirty state) — this is the actual committed
  state. Not investigated further: outside this escalation's scope (bounded to `instruments-service`), and the file's
  3 most recent commits (`064f872a`, `039cddb6`, `7a708284`) are all active LIGHTER-ZKSYNC Tardis work, closely
  matching the open `lighter_zksync_derivative_ticker_tardis_numeric_market_id_leaks_into_symbol_schema_2026_07_29.md`
  issue — plausibly an in-progress refactor whose baseline simply hasn't been regenerated yet, or a genuine
  regression; genuinely unclear which without reading the adapter code, which nobody has done yet as of this filing.
  Does not affect `instruments-service`'s own CI: its `quality-gates-v2` `dep_repos` input only clones
  `unified-trading-library unified-api-contracts`, never `market-tick-data-service`, so this workspace-wide check
  finds nothing to scan there in CI — it only surfaces in a full multi-repo local slot workspace like `.tabs/1/`.
status: open
nature: issue
asset_group: [cefi]
stage: [data-pipeline]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, adapter-contract-regression, tardis, lighter-zksync, incidental-finding]
related:
  [
    /plans/active/issues/lighter_zksync_derivative_ticker_tardis_numeric_market_id_leaks_into_symbol_schema_2026_07_29.md,
    /plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.12
assigned_role: cefi
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: "cicd-role escalation agt-41a9d1 (WALL_TYPE=ldr_qg_failure, REPO=instruments-service#1026), incidental discovery during local verification"
---

# market-tick-data-service `tardis_batch_download.py` adapter-contract-regression (7 < 11) — undiagnosed

## What was found

Running `instruments-service`'s local `scripts/quality-gates.sh` to verify an unrelated fix, STEP 5.70 ("IS-MTDS
CONTRACT INTEGRITY") — which invokes `check_adapter_contract_regression` scoped to `$WORKSPACE_ROOT` (every sibling
repo in the slot, not just the repo being gated) — reported:

```
[FAIL] market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_batch_download.py:
7 contract calls < baseline 11.
```

`market-tick-data-service` was confirmed clean (`git status` → nothing to commit, up to date with
`origin/live-defi-rollout`) — this is real committed content, not local dirty state.

## Why this wasn't investigated or fixed here

- Out of scope for the triggering escalation (`agt-41a9d1`, bounded to `instruments-service`'s `ldr_qg_failure`).
- Doesn't affect `instruments-service`'s actual CI (confirmed: that repo's `quality-gates-v2` only clones
  `unified-trading-library`/`unified-api-contracts` as deps, never `market-tick-data-service`, so this check finds
  nothing there in CI — it's a local-multi-repo-workspace-only surface).
- The file's 3 most recent commits are active LIGHTER-ZKSYNC work (self-record captured manifest rows, symbol-map
  ContextVar propagation, numeric-market_id-in-symbol-column overwrite) closely related to the open
  `lighter_zksync_derivative_ticker_tardis_numeric_market_id_leaks_into_symbol_schema_2026_07_29.md` issue — plausibly
  whoever is doing that work simply hasn't regenerated the baseline yet (legitimate), or it's a real accidental
  regression (the exact failure mode `lint_sweep_774602ea8_regression_audit_2026_05_20.md` warns about). Distinguishing
  the two requires reading the adapter code, which this filing has not done.

## Todos

- [ ] 1. [SCRIPT] P3. Read `tardis_batch_download.py`'s current error/empty/zero-rows/shard-failure handling vs. the
      baseline's 11 expected calls; determine whether the 4 missing calls are a genuine regression (restore them) or
      an intentional consequence of the in-flight LIGHTER-ZKSYNC refactor (regenerate the baseline via
      `--regenerate-baseline` with a comment citing the refactor).
- [ ] 2. [REVIEW] P3. If genuine regression: check whether it predates the 3 recent LIGHTER-ZKSYNC commits (`git log
      -p` / `git blame` on the missing call sites) to pin which commit dropped them, per the same discipline
      `lint_sweep_774602ea8_regression_audit_2026_05_20.md` used.

## Evidence

- Local `instruments-service` QG log (STEP 5.70 IS-MTDS CONTRACT INTEGRITY section), 2026-07-30, this filing.
- `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml` (the baseline the check reads).
- `market-tick-data-service` clean tree confirmed via `git status` at investigation time, HEAD = `064f872a`.

## Progress Log

- **2026-07-30** — Filed while resolving `ldr_qg_failure` escalation `agt-41a9d1` for `instruments-service`. No
  investigation beyond confirming the finding is real (committed, not local dirty state) and out of this
  escalation's scope.
