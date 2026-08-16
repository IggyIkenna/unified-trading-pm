---
doc_type: issue
title: instruments-service process_write.py → process_write_venue.py split leaves adapter_contract_baseline stale (QG red)
summary: >-
  A same-day legit refactor split process_write.py into two files without regenerating
  adapter_contract_baseline.yaml, causing check_adapter_contract_regression to false-positive-fail
  instruments-service's quality-gates.sh for every change until the baseline is regenerated.
status: open
nature: issue
asset_group: [tradfi, cefi, defi]
stage: [data]
repos: [instruments-service, unified-trading-pm]
scope: [engineer]
tags: [quality-gates, adapter-contract-regression, false-positive, baseline-stale]
related: []
created: "2026-08-16"
assigned_vm: planning
parent_epic: instruments_master
priority: P1
resolved_by:
locked_by:
source: >-
  Discovered while shipping tradfi_satellite_ao_dispatch_batch9_2026_08_09.md todo 1 (unrelated new script,
  scripts/purge_tradfi_ice_dropped_universe_parquets_2026_08_16.py) — Pass-1 quality-gates.sh on instruments-service
  fails STEP "IS-MTDS CONTRACT INTEGRITY" / check_adapter_contract_regression, blocking quickmerge for any
  instruments-service change until fixed.
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# instruments-service process_write.py split leaves adapter_contract_baseline stale

## What I found

`bash scripts/quality-gates.sh` on instruments-service (live-defi-rollout HEAD) fails at the very end with:

```
[FAIL] instruments-service/instruments_service/engine/orchestrator/process_write.py: 6 contract calls < baseline 14.
[check_adapter_contract_regression] 1 file(s) regressed below baseline.
```

Root cause: commit `b421ea77` ("feat(is): add per-venue exception isolation to process_write's write loop",
authored ~04:23:44Z 2026-08-16, slot-6) refactored `process_write.py` — extracting the per-venue write-routing
body (`_write_one_venue`) into a **new** file, `process_write_venue.py`, to keep `process_write.py` under the QG
size caps after adding the per-venue try/except + `classify_venue_error()` wrap. This is a legitimate,
intentional refactor, not a content-loss regression (unlike the 2026-05-20 lint-sweep incident this check exists
to catch): `process_write.py` now carries 6 of the tracked contract-call patterns and the new
`process_write_venue.py` carries 9 (15 total vs. the old single-file baseline of 14 — no material loss, the small
delta is consistent with the wrap's own new `classify_venue_error()` call).

`check_adapter_contract_regression` (baseline: `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml`)
evidently checks each tracked file independently against its own stale baseline and has no entry (or a 0 baseline)
for the new `process_write_venue.py`, so it only sees `process_write.py`'s count drop and flags a false-positive
regression.

## Why it matters

This is a fleet-wide-visible RED on instruments-service's QG — blocks quickmerge for every instructions-service
change (including this session's own unrelated script) until the baseline is regenerated. Declared as a
`qg_red` repo-blocker (`POST /api/repo-blockers`) so the RepoHealthWatcher tracks resolution and notifies waiters.

## Recommended decision

Re-run `check_adapter_contract_regression --regenerate-baseline` (or the equivalent baseline-update entrypoint in
`unified-trading-pm/scripts/quality_gates/`) for instruments-service now that `process_write_venue.py` exists as a
tracked file — this is precisely the "legit refactor that intentionally changes counts" case the script's own
guidance names as the one time `--regenerate-baseline` is appropriate (never to mask a genuine wipe). Verify
post-regen that both files' counts are captured (6 + 9 = 15, or whatever fresh count a live re-scan shows) before
committing the updated baseline.

## Todos

- [ ] [SCRIPT] P1. Regenerate `adapter_contract_baseline.yaml` for instruments-service post the
      `process_write.py`→`process_write_venue.py` split (commit `b421ea77`), verifying both files' contract-call
      counts are captured and no genuine call was lost — confirm `quality-gates.sh` on instruments-service is green
      after. Repo: unified-trading-pm (baseline file) + instruments-service (verify). Source: this doc.

## Progress Log

- 2026-08-16 (worker, slot-25, data_engineering, dispatched on an unrelated task): found instruments-service QG red
  at the very last check, root-caused to a same-day peer refactor (b421ea77) splitting process_write.py without a
  baseline regen; confirmed the split preserved the contract calls (6+9=15 vs the stale 14 baseline) rather than
  losing them. Filed this issue doc + declared a `qg_red` repo-blocker; not fixing inline (baseline-file ownership
  is PM/gate-infra scope, outside this task's repos) per the repo-blocker protocol in
  `unified-trading-pm/agents/worker.md` § 4b.
- 2026-08-16 (worker, slot-23, data_engineering): independently hit the same red via a DIFFERENT entry point —
  `market-tick-data-service`'s own `quality-gates.sh` runs the cross-repo "IS-MTDS CONTRACT INTEGRITY" check, which
  fails identically (`process_write.py: 6 contract calls < baseline 14`) and blocks Pass-1 QG for an unrelated MTDS
  commit (`4aa781a2`, a delete-only purge script for `sports_league_legacy_orphan_purge_followup_2026_08_15.md`
  todo 2). Confirmed on a clean instruments-service tree (no local diff, HEAD=b421ea77, matches this doc's own
  root-cause). Not re-declaring a duplicate repo-blocker (this doc's is already open); noting here as corroborating
  evidence that the blast radius extends beyond instruments-service itself to any repo whose QG suite runs this
  cross-repo check. Confirms this is genuinely fleet-wide, not instruments-service-local.
