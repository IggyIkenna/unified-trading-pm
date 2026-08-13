---
doc_type: plan
title: Expand AO Escalation Coverage — quality_gate_resolution Role + 6 New Wall Types
summary: >-
  Retroactive record (HARD RULE: fan-out work is a tracked plan, never verbal dispatch — this session shipped it
  directly without authoring the plan first). Built a 3-tier debounce/escalate pattern for promote-PR QG failures
  (instant Slack for non-promote contexts, 15min-then-escalate for promote-PR contexts since a drain-bot resolution
  often lands 10-11min later on its own) and closed an audit gap — six standing CI monitors (reconcile-release-tags,
  sit-gate-stuck-detector, semver-agent, cloud-build-router, cloud-build-router-aws, glue-pool-starvation-monitor)
  posted to Slack on failure but never escalated to an AO agent. Added a new quality_gate_resolution AgentKind +
  wall_type family, a boot prompt, and dashboard support so these escalations render distinctly (purple cicd-style
  badge) from a regular plan worker inside the existing Escalations panel.
status: complete
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, unified-trading-ci]
scope: [engineer]
tags: [agent-orchestrator, escalation, ci-cd, quality-gates, dashboard, wall-type]
related:
  [
    /codex/04-architecture/agent-orchestrator-ci-escalation-wall-types.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: "2026-08-12"
last_updated: 2026-08-13
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
context_scope:
  [
    /codex/04-architecture/agent-orchestrator-ci-escalation-wall-types.md,
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/models/escalation.py,
    agent-orchestrator/server/prompts.py,
    agent-orchestrator/server/state_store/slots.py,
    unified-trading-pm/agents/quality_gate_resolution.md,
  ]
supersedes:
superseded_by:
depends_on:
source: operator-directed
assigned_role: infra
drift_direction: advance-code
---

# Expand AO Escalation Coverage — quality_gate_resolution Role + 6 New Wall Types

> **ARCHIVED 2026-08-13** — authored retroactively, already fully shipped and verified at authoring time (operator
> ruling: large fanned-out work must be tracked even after the fact). Every todo below cites its shipped commit; no
> further action needed. See Progress Log for the verification pass that confirmed each repo's commit actually reached
> `main` (or, for `agent-orchestrator`, is live via its `ldr_terminal` self-pull deploy model).

## Why this plan exists (after the fact)

Operator observed (2026-08-12) that `promote_qg_failure` Slack alerts sometimes had no AO agent working them (a no-op
dispatch risk), and separately that six other standing CI monitors posted CRITICAL/WARNING to Slack with zero escalation
path to a human OR an agent. Directed: build a 3-tier pattern for the promote-PR case (drain-bot auto-fixes most cases
within ~10-11min; only escalate if genuinely still broken after 15min, then again if unresolved after 30min) and wire
the same escalation mechanism onto the other six.

## Todos

- [x] [BACKEND] P1. Add `quality_gate_resolution` to `AgentKind` + `WALL_TYPES`, route `promote_qg_failure` + 5 new wall
      types to it, extend `_poll_wall_resolution()`'s auto-resolution signal to cover it. Evidence:
      `agent-orchestrator@a20f39ddcf` (server/models/_types.py, server/escalation.py, server/models/escalation.py,
      server/prompts.py, server/state_store/slots.py).
- [x] [FRONTEND] P1. Dashboard support — `AgentKind` TS union, purple cicd-style badge label, `KINDS_ORDER` entry so the
      Agents panel groups these distinctly from a regular plan worker. Evidence: `agent-orchestrator@a20f39ddcf`
      (dashboard/src/types.ts, dashboard/src/layout.tsx). Verified: 3532 backend tests passed / 2 skipped,
      `npm run typecheck` exit 0, 295 frontend tests passed.
- [x] [DEVOPS] P1. 3-tier debounce/escalate for `python-quality-gates-v2.yml`'s promote-PR QG-failure alert: instant
      Slack for non-promote-PR contexts (unchanged); for promote-PR contexts, a 15-min debounce-and-recheck job before
      the CRITICAL post fires at all; a second, chained 15-min recheck (30min total) that dispatches
      `wall_type=promote_qg_failure` to AO only if still genuinely unresolved. Evidence: `unified-trading-ci@45eabc244b`
      (initial debounce), `unified-trading-ci@e499f9d642` (tier-3 escalate job).
- [x] [DEVOPS] P2. Wire the same escalation dispatch onto `semver-agent.yml`'s 3 CRITICAL points (bump-rate circuit
      breaker + 2 version-bump-dispatch-FAILED variants), `wall_type=semver_agent_failure`. Evidence:
      `unified-trading-ci@f99a0abfda`.
- [x] [DEVOPS] P2. Add `escalate` jobs to `reconcile-release-tags.yml` (`release_tag_stall`),
      `sit-gate-stuck-detector.yml` (`sit_gate_stuck`), `glue-pool-starvation-monitor.yml` (`glue_pool_starvation`) —
      each gated on the same condition as its existing Slack notify job. Evidence: `unified-trading-pm@d6647b907a`.
- [x] [DEVOPS] P2. Add `escalate-*` jobs to `cloud-build-router.yml` (10 jobs, one per distinct failure condition —
      tier-check, health-check-failed, smoke-test-failed, emergency-resume, regional-fallback, build-failed,
      build-poll-exhausted, build-not-configured, permission-denied, utl-base-image-not-configured) and
      `cloud-build-router-aws.yml` (3 jobs), `wall_type=cloud_build_router_failure`. Deliberately did NOT mirror the
      `notify-instruments-build-data-pipeline` (would double-dispatch the same condition) or the green-bookend
      `notify-utl-base-image-recovered` job. Evidence: `unified-trading-pm@d6647b907a`.
- [x] [DEVOPS] P2. New agent boot prompt `agents/quality_gate_resolution.md` (frontmatter
      `role:     quality_gate_resolution`, `model: sonnet`, `thinking: high`, `lifecycle: one_shot`), mirroring
      `cicd.md`'s structure (heartbeat discipline, backgrounded quality-gates.sh pattern, `/blocked` protocol, `/done`
      on completion). Evidence: `unified-trading-pm@d6647b907a`.
- [x] [DOCS] P2. Consolidated architecture doc cataloguing every wall_type -> AgentKind mapping and the 3-tier timing
      pattern, so a future addition has one place to update instead of re-deriving the 8-location hardcoded-sync-point
      pattern from scratch. Evidence: `unified-trading-pm@d6647b907a` —
      `/codex/04-architecture/agent-orchestrator-ci-escalation-wall-types.md`.
- [x] [DEVOPS] P3. Add the 6 new wall types to `escalate-to-orchestrator.yml`'s bash `case` validator (both the pattern
      list and the error message) so a caller using an unrecognized wall_type still gets a clear rejection instead of a
      silent pass-through. Evidence: `unified-trading-pm@d6647b907a`.

## Progress Log

- **2026-08-12/13** — Shipped across 3 repos in the original working session (see the session's own conversation for the
  full multi-attempt shipping history: 6 distinct pre-existing gate failures diagnosed and resolved along the way, none
  of them caused by this plan's own content — codex-doc-freshness YAML-parse-error swallowing, a pre-existing unrelated
  fabricated commit-SHA citation, missing frontmatter fields, a dangling reference path, host RAM contention). Final PM
  commit `unified-trading-pm@d6647b907a`.
- **2026-08-13** — This plan authored retroactively per operator direction ("write one retroactively, marked done, for
  the record — that's the rule for large work"). Verification pass at authoring time, run fresh rather than trusted from
  memory:
  - `unified-trading-pm@d6647b907a` — confirmed ancestor of `origin/main` (`git merge-base --is-ancestor`).
  - `unified-trading-ci@f99a0abfda` — confirmed ancestor of `origin/main`.
  - `agent-orchestrator@a20f39ddcf` — confirmed ancestor of `origin/live-defi-rollout`, **not yet** an ancestor of
    `origin/main`. Investigated rather than assumed broken: `agent-orchestrator` runs `promotion_model: ldr_terminal`
    (confirmed live via `ldr-to-main-promote-fleet.yml`'s own run log:
    `SKIP agent-orchestrator: promotion_model='ldr_terminal' (not ldr_main; staging→main model active)`) — LDR is this
    repo's deliberately-terminal, self-deployed branch (`ao-self-pull.sh`, 15-min cron); it never promotes to `main` via
    the fleet mechanism at all, so the feature is genuinely live in production despite `main` never catching up.
  - Directly grepped all 6 target workflow files for their `escalate`/`escalate-*` job counts (1, 1, 1, 10, 3, plus 7
    `dispatches` references in `semver-agent.yml`) to confirm the wiring is real content on disk, not just a claimed
    diff.
