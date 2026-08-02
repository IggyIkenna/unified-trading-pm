---
doc_type: issue
title:
  TradFi manifest-consolidator staleness budget missing (same bug class as sports/defi) — false
  ManifestConsolidatorStaleError on ~95%+ of dates
summary: >-
  Found while re-running the ES/MES `process`-step backfill a third time
  (`tradfi_satellite_ao_dispatch_batch5_2026_07_29.md` todo 2, testing the `_retry_empty_day_listing` mitigation from
  `tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`). `AG_STALENESS_BUDGET_SEC`
  (`unified_trading_library/manifest_writer/_staleness_budget.py`) had entries for cefi/sports/defi (each added after
  hitting this exact false-positive class) but NOT tradfi — so every read against
  `instruments-tradfi`/`market-data-tradfi` fell back to the generic 120s default. `instruments-tradfi`'s real
  consolidator cadence is HOURLY (Terraform `manifest_consolidator_schedule["instruments-tradfi"] = "0 * * * *"`,
  confirmed live via `gcloud run jobs executions list` — successful runs at 21:00/22:00/ 23:00/00:00Z), so the 120s
  budget false-tripped `ManifestConsolidatorStaleError` on every date processed outside the ~2-3min window right after
  each hourly consolidation. Live impact confirmed: all 7 concurrent per-year ES/MES backfill shards hit this on 178-206
  of ~192-366 dates each (essentially every date since ~10min into the run), producing 0 real candles for the whole
  affected window — the VMs ran to completion (`DEPLOYMENT_FAILED`, exit_code=1) with zero data written. Fixed by adding
  `"tradfi": 7200` to `AG_STALENESS_BUDGET_SEC` (~2x margin over the real 3600s cadence, mirroring the sports/defi fix
  philosophy) — `unified-trading-library@2fa09f1d`. Killed the 7 corrupted shards and relaunched fresh; confirmed live
  the fix resolves the false trip (clean `Dependency check passed` progression, no more `Manifest consolidator appears
  DOWN` errors).
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-library]
scope: [engineer]
tags: [tradfi, manifest-consolidator, staleness-budget, data-correctness, false-positive]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md,
    /plans/archive/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md,
  ]
created: 2026-07-31
parent_epic: tradfi_master
priority: P1
source: [tradfi_satellite_ao_dispatch_batch5-001, live VM re-run 2026-07-31]
assigned_vm: planning
resolved_by: "unified-trading-library@2fa09f1d"
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-31
locked_since:
---

> **🟢 ARCHIVED 2026-08-02** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Resolution evidence carried in `resolved_by:` (unified-trading-library@2fa09f1d). Moved by
> the `/plan-reconcile` whole-corpus run of 2026-08-02, which found this doc sitting in `plans/active/issues/` at a
> terminal status — `check_terminal_status_archived` was RED at 13 violations against a baseline of 1. No content was
> rewritten.

# TradFi manifest-consolidator staleness budget missing

## What I found

While re-running the ES/MES `process`-step backfill a third time (batch5 todo 2), all 7 concurrent per-year shards
(2020-2026) started hitting
`Category processing failed: Manifest consolidator appears DOWN for bucket='instruments-store-tradfi-prd-central-element-323112'`
roughly 10 minutes into the run, and never recovered — every subsequent date produced 0 real candles.

Root cause: `AG_STALENESS_BUDGET_SEC` in `unified_trading_library/manifest_writer/_staleness_budget.py` had
per-asset_group overrides for `cefi` (86400s), `sports` (1800s), and `defi` (3600s) — each added after an
almost-identical incident (`sports_manifest_read_staleness_budget_missing_2026_07_15.md`,
`defi_manifest_consolidator_staleness_budget_missing_2026_07_29.md`) — but **no `tradfi` entry**, so every tradfi read
fell back to the generic 120s global default (`MANIFEST_CONSOLIDATED_STALENESS_SEC`, live-tick-tuned). Confirmed via
Terraform (`deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`) that `instruments-tradfi`'s real
schedule is `"0 * * * *"` (hourly) — matching the live `gcloud run jobs executions list` history (successful completions
at 21:00/22:00/23:00/00:00Z, each ~2.5min). A 120s freshness budget against an hourly-cadence consolidator is only
satisfied for ~2-3 minutes after each hourly run; every other minute of every hour, any caller with per-VM shards
present (i.e. any active backfill) sees a false "consolidator appears DOWN" and the read path fails closed by design
(`assert_consolidator_healthy` / `ManifestConsolidatorStaleError`, `manifest_consolidator_liveness_health_2026_06_01`).

Live evidence: 178-206 occurrences of the exact error string per shard (of ~192-366 dates processed), first occurrence
~10min into each run, persisting until the fix; all 7 VMs ran to completion with `DEPLOYMENT_FAILED` (exit_code=1) and 0
real candles produced for tradfi across the whole run.

## Why it matters

This is a live production data-correctness bug on the TradFi critical path — any code path that calls
`assert_consolidator_healthy` / `read_availability_index` against `instruments-store-tradfi-*` or
`market-data-tick-tradfi-*` (VM preflight checks, MDPS's `process`/`build-continuous` steps, any manifest read during a
tradfi backfill) is exposed outside the narrow post-consolidation window. It silently degrades data processing to
near-zero throughput rather than raising loudly in a way that's easy to diagnose from a VM's exit code alone (the VM
DOES exit non-zero, but the log needed close reading to find the actual mechanism vs. assuming a data-availability or
timing issue). This may also explain (or contribute to) why the hit-rate re-runs in the now-archived
`tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md` saw no doc-visible mention of this exact
error class — that doc's 2026-07-26 runs may have run at times when the consolidator happened to be freshly-cycled more
often, or this specific failure mode simply wasn't hit during those windows; not re-verified retroactively here (out of
scope for this fix), flagging for awareness only.

## Recommended decision

- [x] [AGENT] P1. Add `"tradfi": 7200` to `AG_STALENESS_BUDGET_SEC` (7200s = ~2x margin over the real 3600s hourly
      cadence, matching the defi/sports fix's margin philosophy) + a regression test asserting the override resolves
      correctly. Repo: unified-trading-library. Done when: shipped + green QG. — ✅ DONE 2026-07-31:
      `unified-trading-library@2fa09f1d` (3 commits: the override + doc history, a pre-existing-test fixture swap from
      `tradfi` to `prediction` as the "no override" example since tradfi is no longer unoverridden, and a QG-flagged
      hardcoded-prod- project-id fix in the new test). Full `quality-gates.sh` green (6872 passed, 10 skipped, 10
      xfailed). Live-verified: relaunched the 7 corrupted shards fresh with the fix live (tarball republished +
      `LC_TARBALL_FRESHNESS=enforce`) — confirmed via direct `run.log` inspection that dates now progress cleanly
      (`✅ Dependency check     passed`) with zero `Manifest consolidator appears DOWN` errors post-fix.

## Progress Log

- 2026-07-31 (slot 9, `tradfi_satellite_ao_dispatch_batch5-001`): Found mid-task while monitoring the 3rd ES/MES
  backfill re-run. Root-caused via live `gcloud run jobs executions list` + Terraform schedule cross-reference (not
  guessed). Fixed + shipped same session. Killed the 7 shards that ran corrupted (0 real candles, confirmed via
  `run.log`) and relaunched fresh with the fix live; one shard (`y2022`) hit an unrelated transient SPOT capacity
  stockout on relaunch (retried, succeeded), one (`y2021`) was SPOT-preempted ~60s after insert with zero progress
  (relaunched from scratch, no loss per the resume-from-progress rule — there was no progress to resume from). One
  duplicate `y2020` VM appeared under an untracked timestamp (`...011628`, same `github-actions-deploy` shared identity,
  exact same ES/MES scope) shortly after my own relaunch — cause not conclusively identified (no evidence of another
  slot touching this plan's git history); killed it per the established precedent
  (`tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`'s own "killed the redundant VM to avoid
  two concurrent efforts covering the identical range" reconciliation) rather than let it burn duplicate SPOT compute.
  Final state: exactly 7 shards running, one per year, all confirmed processing cleanly post-fix.

## Codex SSOTs

No new durable contract — this fixes a gap in an existing, already-documented mechanism. See
`/codex/05-infrastructure/manifest-consolidator-ssot.md` for the consolidator model; the staleness-budget module's own
docstring history (`_staleness_budget.py`) is the SSOT for this specific override registry and its sizing philosophy.
