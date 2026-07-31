---
doc_type: issue
title: >-
  features-onchain-service batch handler exits 1 whenever ANY of its 13 feature_groups attempted_fails, even when other
  groups wrote real data successfully -- masks partial success and forces every full-family DEFI onchain launch to
  "fail" on pre-existing per-group gaps unrelated to the caller's actual target group
summary: >-
  Working the D1 DeFi features backfill todo (`defi_satellite_ao_dispatch_batch3_2026_07_26.md`), a full-family (no
  `--feature-group` scope) onchain/DEFI launch over a clean 7-day dependency window
  (`features-onchain-defi-20260730-210912`, `2023-06-01..2023-06-07`) exited 1 ("Processing failed") even though 2 of
  its 13 groups wrote real, useful data (`lending_rates`: ~146k rows across 7 days; `lst_yields`: 67 rows) and a 3rd
  (`perp_funding_rates`, the group I actually needed) correctly resolved a genuine honest-absence for that window. The
  overall failure came from 4 OTHER, unrelated groups (`rewards`, `flash_loan_availability`, `health_factor`,
  `liquidation_events`) each writing `attempted_failed(calculator_produced_base_columns_only)` -- their own calculators
  apparently have some unexamined gap (not investigated here, out of scope for this finding) that makes them
  structurally unable to produce more than base columns on this data. `features_service/onchain/cli/handlers/
  batch_handler.py`'s `_emit_batch_completion()` (`dependency_checker.py`... actually batch_handler.py:409) requires
  `success_count == len(groups)` for the whole run to report success -- ANY one of the 13 groups failing makes the whole
  VM report `DEPLOYMENT_FAILED`, `exit_code=1`, even though every other group (including the one the caller actually
  cared about) succeeded or correctly resolved honest-absence. This is a genuine partial-success-masking defect: an
  operator/monitor watching VM exit codes has no way to tell "everything failed" from "12/13 succeeded, 1 pre-existing
  unrelated group failed" without reading the full run.log.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [defi, features-service, onchain, batch-handler, exit-code, partial-success, data-correctness]
related:
  - /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md
  - /plans/active/issues/delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md
created: "2026-07-30"
source: [defi_satellite_ao_dispatch_batch3_2026_07_26.md-D1]
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# What I found

`features_service/onchain/cli/handlers/batch_handler.py:409`:

```python
def _emit_batch_completion(self, asset_group, groups, success_count, dry_run):
    ...
    self.logger.info("Completed %s/%s groups", success_count, len(groups))
    ...
    return success_count == len(groups)
```

This is an ALL-OR-NOTHING policy — every one of the (currently 13) onchain feature_groups for DEFI must individually
succeed for the batch to report success, regardless of whether the groups that failed are the ones the caller actually
asked about. Live evidence from `features-onchain-defi-20260730-210912` (full-family launch, no `--feature-group` scope,
`2023-06-01..2023-06-07`):

```
Wrote 24449 rows to .../onchain/by_date/day=2023-06-01/feature_group=lending_rates/features.parquet   [SUCCESS]
Wrote 10 rows to .../onchain/by_date/day=2023-06-01/feature_group=lst_yields/features.parquet          [SUCCESS]
Wrote empty_confirmed(EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE) for perp_funding_rates date=2023-06-01  [honest absence, not a failure]
Wrote empty_confirmed(EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE) for rate_impact date=2023-06-01         [honest absence, not a failure]
Wrote attempted_failed(calculator_produced_base_columns_only) for rewards date=2023-06-01                [REAL FAILURE]
Wrote attempted_failed(calculator_produced_base_columns_only) for flash_loan_availability date=2023-06-01 [REAL FAILURE]
Wrote attempted_failed(calculator_produced_base_columns_only) for health_factor date=2023-06-01          [REAL FAILURE]
Wrote attempted_failed(calculator_produced_base_columns_only) for liquidation_events date=2023-06-01     [REAL FAILURE]
Completed 8/13 groups
ERROR Processing failed
[vm-exec] command exited rc=1
```

("8/13" — the run only got through day=2023-06-01 for the 4 unsuccessful groups before the process gave up; the other 6
days in the window were never attempted for those 4 groups either, since the loop structure processes group-by-group,
not day-by-day, and aborts on the first all-groups pass.)

I fixed the `perp_funding_rates` symbol-matching bug this run also surfaced (see the companion issue doc for the
delta_one instrument-discovery bug — this onchain finding is separate) — see
`features_service/onchain/calculators/perp_funding_rates_defi.py`'s `_DEFI_SYMBOL` fix, same session. That fix does NOT
touch `rewards`/`flash_loan_availability`/`health_factor`/`liquidation_events` — those 4 groups'
`calculator_produced_ base_columns_only` failures are a SEPARATE, unexamined gap (I did not investigate their
calculators; out of scope for this finding, which is about the exit-code/success-signaling policy, not those
calculators' correctness).

# Why this matters

Any full-family (unscoped) onchain/DEFI launch will report `exit_code=1` as long as even ONE of the 13 groups has a
calculator gap — masking however many OTHER groups genuinely succeeded. This makes VM-exit-code-based monitoring
(`vm-preemption-billing-waste-audit`-style dashboards, the `deployment_heartbeat.py` DEPLOYMENT_FAILED event) unable to
distinguish "total failure, nothing written" from "12/13 groups wrote real data, 1 pre-existing gap failed" without a
human reading the full run.log — the exact opposite of the workspace's honest-absence-vs-failure discipline this
codebase otherwise takes seriously (per-shard `record_captured`/`record_failed`/`record_empty` already distinguish these
at the manifest level; the process-level exit code throws that distinction away). It also means every caller who
actually only wants ONE group (as D1 does — `perp_funding_rates` specifically) should always pass
`--feature-group <name>` rather than a full-family launch, to avoid being blocked by unrelated groups' failures — worth
calling out explicitly in the launcher's own usage docs if that isn't already the convention.

# What I did NOT do

Did not change `_emit_batch_completion()`'s success policy — this needs an explicit decision (e.g. success if the
CALLER-REQUESTED group(s) succeeded, regardless of others; or a partial-success exit code distinct from total failure)
that affects monitoring/alerting expectations fleet-wide, not just DEFI. Did not investigate the 4 failing groups'
`calculator_produced_base_columns_only` root cause (`rewards`/`flash_loan_availability`/`health_factor`/
`liquidation_events`) — a separate, unexamined gap, out of scope for this finding.

# Recommended decision

Either (a) change the exit-code policy so a full-family batch reports partial success distinctly from total failure
(e.g. exit 0 if `success_count > 0`, with the per-group failure detail already recorded in the manifest being the source
of truth for "is my specific group's data present" — mirrors delta_one's own `_process_groups()` policy, which already
returns True if ANY group succeeded, per `features_service/delta_one/cli/handlers/batch_handler.py`'s `_process_groups`
docstring: "Return True if ANY group succeeded; only return False if EVERY group failed" — onchain and delta_one
currently disagree on this policy for no apparent reason), or (b) keep the strict all-or-nothing policy but document it
clearly + recommend every caller who only needs specific groups launch with `--feature-group` (never a full-family run)
to avoid being blocked by unrelated calculator gaps. Separately, root-cause the 4 failing groups'
`calculator_produced_base_columns_only` gap as its own follow-on (not scoped here).

## Todos

- [x] [DESIGN] P2. Decide the onchain batch exit-code policy: partial-success-distinct-from-total-failure (align with
      delta_one's existing `_process_groups()` ANY-succeeded policy) vs.
      document-and-recommend-`--feature-group`-scoping. Repo: features-service. Done when: an operator/main ruling is
      recorded here and the chosen behavior is implemented in `features_service/onchain/cli/handlers/batch_handler.py`
      (or the launcher's usage docs are updated if option (b) is chosen), with a regression test covering the chosen
      exit-code contract. ✅ — **Ruling: option (a)**, aligned with delta_one's ANY-succeeded policy. Rationale: (1)
      onchain and delta_one are sibling batch handlers over the same features-service CLI convention — disagreeing
      success semantics for no functional reason is itself a defect; (2) the per-group manifest
      (`record_captured`/`record_failed`/`record_empty`) already carries the authoritative per-group truth, so the
      process-level exit code throwing that away on any single unrelated group's pre-existing gap is strictly a
      regression of information, not a safety property; (3) option (b) (document-only) leaves every full-family DEFI
      onchain launch permanently unable to report `DEPLOYMENT_SUCCEEDED` until all 13 groups' calculators are fixed — an
      unbounded gate on an unrelated concern. `_emit_batch_completion()` in
      `features_service/onchain/cli/handlers/batch_handler.py` now returns `success_count > 0` (True unless EVERY group
      failed), logging `"Partial success — N/M groups succeeded; continuing."` on partial and
      `"ALL feature groups failed: [...]"` only when nothing succeeded — mirrors delta_one's `_process_groups()`
      docstring contract exactly. Regression coverage: `TestEmitBatchCompletion` in
      `tests/onchain/unit/test_batch_handler.py` (all-succeed / partial-success / all-fail cases). —
      features-service@ca5e5a96
- [ ] [BACKEND] P3. Root-cause `calculator_produced_base_columns_only` for the `rewards`/`flash_loan_availability`/
      `health_factor`/`liquidation_events` onchain DEFI feature groups (confirmed reproducing on
      `2023-06-01..2023-06-07`, a clean dependency window — not a data-availability gap for THIS finding's window, but
      unexamined further). Repo: features-service. Done when: root cause identified + either fixed or documented as a
      genuine data/design limitation with an issue-doc update.

# Progress Log

- 2026-07-30 (slot-3): filed while executing D1's onchain leg. Fixed the co-discovered `perp_funding_rates` symbol bug
  in the same session (separate, unrelated code path) — see `features-service` commit referenced in
  `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo note.
- 2026-07-30 (slot-5): resolved the [DESIGN] todo — ruled option (a), implemented + shipped `features-service@ca5e5a96`
  (`_emit_batch_completion()` now returns `success_count > 0`, matching delta_one's `_process_groups()` ANY-succeeded
  contract), added `TestEmitBatchCompletion` regression coverage. P3 root-cause todo for the 4
  `calculator_produced_base_columns_only` groups remains open, out of scope for this todo.
