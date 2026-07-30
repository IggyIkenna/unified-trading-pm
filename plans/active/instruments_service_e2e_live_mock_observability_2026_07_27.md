---
doc_type: plan
title: instruments-service E2E — live mode, mock scenarios, observability (Phases 5-7)
summary:
  Re-scoped from the never-completed Phases 5-7 of the archived 2026-03 instruments-service E2E audit
  (plans/archive/2026_07/e2e_testing_001_instruments_service_2026_03_22.md) — live-mode 15-min clock alignment,
  mock-mode failure scenarios, and observability/logging checks, none of which were ever run.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer]
tags: [e2e-testing, instruments-service, live-mode, mock-mode, observability]
related: []
created: 2026-07-27
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1
last_updated: 2026-07-27
supersedes: []
superseded_by:
locked_by:
locked_since:
depends_on:
source: [plans/archive/2026_07/e2e_testing_001_instruments_service_2026_03_22.md]
assigned_role: backend_engineer
drift_direction: none
---

# instruments-service E2E — live mode, mock scenarios, observability

## Context

The original instruments-service E2E audit (2026-03-21, archived 2026-07-27) completed Phases 1-4 plus a real 2026-03-23
DEFI-category audit that found 6 real bugs, but never ran Phases 5-7. Re-verify against current instruments-service
before assuming any of the below is still accurate — 4+ months have passed.

## Todos

- [ ] [SCRIPT] P1. **Phase 5 — Live mode clock alignment.** Run `--operation live --mode batch --interval 15` and
      verify: (5.1) waits for the next 15-min UTC boundary before running; (5.2) runs only at :00/:15/:30/:45; (5.3) UEI
      events fire correctly (STARTED, per-venue COMPLETED/FAILED, final COMPLETED); (5.4) Ctrl-C during the wait exits
      cleanly with no partial writes.
- [ ] [SCRIPT] P2. **Phase 6 — Mock-mode failure scenarios.** Run and verify: (6.1) `--scenario default` normal mock
      generation; (6.2) `--scenario stress` (10x cardinality) — memory + writes succeed; (6.3) `--scenario missing_data`
      (instruments disappear mid-day) — downstream handles empty gracefully; (6.4) injected fake symbol
      (`FAKE-EXCHANGE:SPOT:NOSYMBOL`) — clean skip/error, no crash; (6.5) missing entire DEFI category —
      market-tick-data-service gets nothing for DEFI and skips cleanly; (6.6) corrupt expiry date
      (`expiry="not-a-date"`) — parser warns, doesn't crash; (6.7) `CLOUD_MOCK_MODE=true` → `config_source=local`, no
      GCS reads.
- [ ] [SCRIPT] P2. **Phase 7 — Observability.** Verify: (7.1) ServiceRuntime log line has all dimensions; (7.2) UEI
      STARTED/COMPLETED/per-venue events fire; (7.3) shard-level isolation (one venue failure doesn't crash others);
      (7.4) dry-run warning logged ("DRY RUN" + "UCI dry-run mode ACTIVE"); (7.5) `ADAPTER_FETCH_FAILED` events classify
      failed venues correctly; (7.6) "Memory watchdog started" logged.
- [ ] [VALIDATE] P3. **Re-verify the 6 bugs from the 2026-03-23 DEFI E2E audit are still real** (Balancer 400, Aster
      lowercase-category bug, Hyperliquid 0-instruments, missing data-catalogue entries, a Pydantic warning,
      CFE-not-in-UAC) before re-filing any of them — 4 months have passed and some may already be fixed incidentally.

## Progress Log

- 2026-07-27: Plan created, re-scoping the never-run Phases 5-7 out of the archived 2026-03 instruments-service E2E
  audit doc per operator decision (pre-June-1 stale-plans audit).

- **na-eligibility-audit 2026-07-30**: RECLASSIFY NA → planning — all 4 todos are bounded verification RUNS with
  explicit per-item done-when checklists (Phase 5 clock-alignment 5.1-5.4, Phase 6 mock scenarios 6.1-6.7, Phase 7
  observability 7.1-7.6, the 6-bug re-verify) — determinable by a worker alone.
