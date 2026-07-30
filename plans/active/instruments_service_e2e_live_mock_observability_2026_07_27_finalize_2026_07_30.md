---
doc_type: plan
title: Finalize — instruments-service E2E live/mock/observability (Phases 5-7) close-out
summary: >-
  Gated close-out twin for `instruments_service_e2e_live_mock_observability_2026_07_27.md`, which was reclassified
  `assigned_vm: NA → planning` by the 2026-07-30 `/na-eligibility-audit cross-cutting` run. Holds the archival ritual +
  the post-run reconciliation that must happen once that plan's 4 verification todos (Phase 5 live-mode clock alignment,
  Phase 6 mock-mode failure scenarios, Phase 7 observability, and the 2026-03-23 six-bug re-verify) have all run and
  been evidenced. Stays `status: draft` until the source plan's last todo flips.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer]
tags: [ao-dispatch, close-out, reclassification, na-audit, e2e-testing, instruments-service]
related:
  [
    /plans/active/instruments_service_e2e_live_mock_observability_2026_07_27.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: none
depends_on: [instruments_service_e2e_live_mock_observability_2026_07_27]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  /na-eligibility-audit cross-cutting, 2026-07-30 — RECLASSIFY verdict on
  instruments_service_e2e_live_mock_observability_2026_07_27.md (Phase-2 conflict-check CLEAR: the only citation is the
  cross-cutting consolidated closeout's digest, which the shared conflict-check SSOT § 3 explicitly defines as a digest,
  not a dispatch claim).
---

# Finalize — instruments-service E2E live/mock/observability close-out

> **Gated twin** (`gate_on_depends: true`). Do NOT start until every todo in
> [`/plans/active/instruments_service_e2e_live_mock_observability_2026_07_27.md`](/plans/active/instruments_service_e2e_live_mock_observability_2026_07_27.md)
> is `- [x]` with cited evidence. Authored by the 2026-07-30 `/na-eligibility-audit` reclassification pass per
> [`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`](/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md)
> § 1(b) — retroactive reclassification keeps the source doc's name and gains this bolt-on finalize sibling.

## Why this exists

The source plan re-scopes Phases 5-7 of the archived 2026-03 instruments-service E2E audit. Its 4 todos are bounded
verification RUNS with explicit per-item done-when checklists, which is why the NA audit reclassified it. But a
verification pass that finds real defects must not silently end at "ran the checks" — this twin holds the reconciliation
that turns those findings into tracked work and closes the plan properly.

## Todos

- [ ] [REVIEW] P2. **Reconcile every Phase 5/6/7 sub-check against its recorded outcome.** For each numbered sub-check
      (5.1-5.4, 6.1-6.7, 7.1-7.6) confirm the source plan records a PASS/FAIL verdict with the command that produced it
      — not a blanket "phase green". Any sub-check that could not be run (e.g. a scenario the current CLI no longer
      supports) is recorded as an explicit honest-absence with its reason, never silently dropped. **Done when**: every
      one of the 17 sub-checks has a recorded verdict + evidence in the source plan. Repo: unified-trading-pm.
- [ ] [REVIEW] P2. **Triage the [VALIDATE] P3 six-bug re-verify outcome.** The source plan's last todo re-checks the 6
      bugs from the 2026-03-23 DEFI E2E audit (Balancer 400, Aster lowercase-category, Hyperliquid 0-instruments,
      missing data-catalogue entries, a Pydantic warning, CFE-not-in-UAC). Per the findings-triage HARD RULE, each bug
      that is STILL real becomes a tracked `- [ ]` todo (in the source plan if in-scope, else
      `plans/active/issues/<slug>_<date>.md`) — never prose, never a re-filed duplicate of an already-open issue doc
      (grep `plans/active/issues/` first). **Done when**: each of the 6 is recorded as fixed-incidentally /
      still-real-and-now-tracked / no-longer-applicable, with the tracking location named. Repo: unified-trading-pm.
- [ ] [PLANNING] P3. **Archive the source plan per the 6-step ritual.** Once both reviews above are done and the source
      plan has zero open todos and no `locked_by:`, run the standard archival ritual from
      [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md)
      (dated archive folder, `status: complete`, every corpus referrer repointed, inventory regenerated), then archive
      this finalize twin alongside it. **Done when**: both docs are under `plans/archive/2026_07/` and
      `regenerate_active_plan_inventory.py` reports 0 new orphans. Repo: unified-trading-pm.

## Codex SSOTs

- [`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`](/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md)
  — the naming/pairing convention this doc follows and the conflict-check that cleared the reclassification.
- [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md)
  — the 6-step archival ritual todo 3 runs.
- [`/codex/04-architecture/shard-level-failure-isolation.md`](/codex/04-architecture/shard-level-failure-isolation.md) —
  the shard-isolation contract Phase 7's check 7.3 verifies.

## Progress Log

- **2026-07-30** — Authored by the `/na-eligibility-audit cross-cutting` tranche run as the paired finalize twin for the
  `NA → planning` reclassification of `instruments_service_e2e_live_mock_observability_2026_07_27.md`. No work executed
  here; `status: draft` + `gate_on_depends: true` hold it until the source plan's todos land.
