---
doc_type: codex-ssot
title: AO CI-escalation wall types — the catalog notify-slack.yml alone can't give you
summary: >-
  Full catalog of every `wall_type` server/escalation.py's WALL_TYPES accepts — what triggers it, which workflow
  dispatches it, which agent role/prompt template resolves it, and whether it's PR-scoped or a bare LDR-push wall. No
  single doc catalogued this before (agent-orchestrator-overview.md and agent-orchestrator-alerting.md both cite
  escalation.py as their own SSOT but neither lists the wall types) — this is that catalog, plus the 3-tier
  Slack-then-escalate pattern (drain-bot self-heal → debounced Slack alert → agent dispatch) used for wall types where
  most failures self-resolve before a human or an agent needs to look.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, unified-trading-ci]
scope: [engineer, admin]
tags: [escalation, ci-cd, agent-orchestrator, wall-type, quality-gates, dashboard]
related:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/04-architecture/ci-alerting.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/ci_escalation_no_coverage_for_local_ratchet_gate_breaches_2026_08_10.md,
    /plans/archive/issues/ci_escalation_wall_type_mismatch_silent_human_only_2026_07_27.md,
  ]
created: 2026-08-12
last_reviewed: 2026-08-12
authoritative_for:
  [ci-escalation wall_type catalog, AO agent-role-to-wall_type mapping, 3-tier escalation timing pattern]
referenced_by: []
owner: ""
code_refs: []
---

# AO CI-escalation wall types

**Mechanism**: a deterministic GHA workflow hits a wall it cannot fix itself and `curl`s `POST /api/escalate`
(`escalate-to-orchestrator.yml`, authed with `ORCHESTRATOR_INTERNAL_SECRET`). The orchestrator spawns a one-shot worker
on a free slot, boots it with `prompts.render(<role>, ...)` (`agents/<role>.md` in this repo), the worker resolves the
wall on the integration branch, pushes, pings the authoring slot, exits. Full mechanism doc: `server/escalation.py`'s
own module docstring. This doc is the catalog `escalation.py`'s inline comments don't present as one table.

**Dashboard visibility is already fully generic — do not add per-wall-type frontend code.** `EscalationsPanel`
(`dashboard/src/layout.tsx`) renders `e.repo`, `e.pr_number`, and the raw `e.wall_type` string for every escalation
regardless of type. The Fleet table's typed-agent badge (`RoleBadge`, same file) takes `spawn_base_role: string` with no
constrained union and renders every role with the same `rgba(99,102,241,0.15)` indigo/purple background — the visual
"this is an automated CI worker, not a plan-following one" distinction the operator wants already applies to any new
role automatically. A new wall_type + role therefore needs ZERO dashboard changes to show up correctly.

## Catalog

| wall_type                                  | Trigger                                                                                                                                  | Dispatched from                                                                    | PR-scoped?          | Prompt template / role                         | Resolution signal                                                                                                                                                 |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `merge_conflict`                           | Genuine git conflict on a promote/backmerge                                                                                              | `main-backmerge-to-ldr.yml`, `deterministic-promotion-conflict-resolve.yml`        | varies              | `conflict_resolver`                            | PR merged / conflict-PR closed                                                                                                                                    |
| `stuck_promotion_pr`                       | A promote PR sat un-mergeable                                                                                                            | `deterministic-promotion-conflict-resolve.yml`                                     | yes                 | `conflict_resolver`                            | PR merged/superseded                                                                                                                                              |
| `label_mismatch`                           | Conventional-commit label vs API diff mismatch                                                                                           | (label-check path)                                                                 | yes                 | `cicd` (generic)                               | commit/label fixed                                                                                                                                                |
| `sit_failure`                              | A SIT run failed                                                                                                                         | `sit-debounce-trigger.yml`                                                         | no                  | `cicd` (generic)                               | next SIT green                                                                                                                                                    |
| `ldr_qg_failure`                           | A repo's `live-defi-rollout` itself went QG-red (no PR — Tier-A proxy via `ldr-ci-monitor.yml`'s hourly scan)                            | `ldr-ci-monitor.yml`                                                               | no (`pr_number: 0`) | `cicd` (generic)                               | `quality-gates-v2` green on `live-defi-rollout`                                                                                                                   |
| `ldr_main_qg_failure`                      | **PM-only**: `ldr-to-main-promote.yml`'s OWN promote PR genuinely QG-failing (not superseded)                                            | `ldr-to-main-promote.yml`, every ~15min tick the failure persists (server-deduped) | yes                 | `cicd` (generic)                               | PR's `quality-gates-v2` green                                                                                                                                     |
| `main_ci_red`                              | `main` red while LDR green (fix is a promote/backport, not a re-fix)                                                                     | CIReconcile main scan                                                              | no                  | `cicd` (generic)                               | main QG green                                                                                                                                                     |
| `provenance_blocked`                       | Auto-merge refused — LDR carries a commit that bypassed quickmerge                                                                       | `ldr-to-main-promote.yml`                                                          | yes                 | `cicd` (generic)                               | provenance clean + re-armed                                                                                                                                       |
| `plan_health`                              | PM's `plan_health-agent.yml` PR→main gate has judgment-residue hygiene failures                                                          | plan_health gate                                                                   | yes/no varies       | `plan_health`                                  | hygiene sweep green                                                                                                                                               |
| `sit_retry_cap`                            | `sit-debounce-trigger.yml` hit its SIT retry budget                                                                                      | `sit-debounce-trigger.yml`                                                         | no                  | `cicd` (generic)                               | manual `drain_pending=true` or fix                                                                                                                                |
| `harness_lint`                             | `sit-gate.yml` harness-config lint failure (missing workspace file / 3 consecutive harness fails)                                        | `sit-gate.yml`                                                                     | no                  | `cicd` (generic)                               | harness lint green                                                                                                                                                |
| `data_pipeline_failure`                    | A filed DP_* data-pipeline finding                                                                                                       | data-pipeline self-monitoring                                                      | no                  | `data_pipeline_failure` (dedicated)            | issue doc resolved                                                                                                                                                |
| `cloud_build_failure`                      | A repo's Cloud Build image pipeline failing (separate from GH Actions QG)                                                                | `cloud-build-failure-watcher.yml`                                                  | no                  | `cicd` (generic)                               | **no proven auto-resolution signal** — deadline→re-escalate→unresolved(pages operator), same as plan_health/harness_lint/sit_failure/sit_retry_cap/label_mismatch |
| `backmerge_sync_failure`                   | `main-backmerge-to-ldr.yml` DECISION=error (script/auth failure, not a content conflict)                                                 | `main-backmerge-to-ldr.yml`                                                        | no                  | `cicd` (generic)                               | next backmerge run succeeds                                                                                                                                       |
| `promote_qg_failure` **(new, 2026-08-12)** | **Fleet-wide** (any repo): a `promote/*` → `main` PR's `quality-gates-v2` genuinely failing (not superseded, not a conflict) for 30+ min | `python-quality-gates-v2.yml` (unified-trading-ci, every repo)                     | yes                 | `quality_gate_resolution` **(new, dedicated)** | PR's `quality-gates-v2` green, or PR closed-as-superseded (self-heals)                                                                                            |

## The gap `promote_qg_failure` closes

`ldr_main_qg_failure` already does exactly this — but **only for `unified-trading-pm`** (its own comment: "distinct
wall_type since the promotion-PR flow it's escalated from is PM-specific... `unified-trading-pm` is staging-less,
LDR->main direct"). Every other repo's promote-PR-into-main QG failure had **zero escalation path** — confirmed live
2026-08-12 (`instruments-service` PR #1185, a genuine `pytest_socket.SocketConnectBlockedError` test failure in a merged
feature commit, alerted only to `#ci-failures`, no agent ever looked at it). `python-quality-gates-v2.yml` is the
FLEET-WIDE reusable template (`unified-trading-ci`, pulled via `@main` by every caller repo) — this is where the fix had
to land, not a per-repo workflow.

## The 3-tier pattern (why NOT dispatch instantly on every QG failure)

A promote PR's QG failure is very often a **promote-cadence race**: the branch was cut from LDR before a later,
unrelated LDR edit landed, so the promote diff would have regressed `main` relative to current LDR — not a code defect.
Measured repeatedly 2026-08-12 on `unified-trading-pm` (PRs #2850→#2872, several cycles): the drain bot's own
`ldr-to-main-promote.yml` supersede loop resolves these within ~10-16 minutes on its own, before any human or agent
needs to act. Dispatching an agent on every first-tick failure would mostly dispatch it at things that were never going
to still be broken by the time it started working — a wasted spawn, not a fix.

Three lines of defense, each firing only if the previous one didn't already clear the wall:

1. **T+0**: the drain bot's own supersede cycle (already existed; unrelated to this change) — most failures never reach
   tier 2 at all.
2. **T+15min**: a debounced `#ci-failures` CRITICAL Slack post (`debounce-promote-qg-fail` job,
   `python-quality-gates-v2.yml`) — re-checks the PR is still open + still failing before posting; silent if it
   self-resolved. No agent dispatched here — this tier is "tell a human, in case they want to look," not "try to fix
   it."
3. **T+30min**: if STILL open + STILL failing (a second, independent re-check — the PR surviving TWO supersede cycles is
   a much stronger signal this isn't just cadence-race noise), dispatch `promote_qg_failure` to a
   `quality_gate_resolution` agent.

This mirrors `ldr_main_qg_failure`'s own reasoning (fire only on a genuine, non-superseded failure) but adds the
explicit TIME gate PM's version doesn't need (PM's promote cadence is fast enough — every ~15min tick — that its own
retry-and-recheck IS the debounce; a fleet-wide repo's promote cadence varies, so `promote_qg_failure` debounces
explicitly instead of relying on tick frequency).

## `quality_gate_resolution` vs the generic `cicd` role

`cicd` already handles `ldr_qg_failure` / `ldr_main_qg_failure` (bare or PM promote-PR QG failures) with a documented
per-wall-type playbook in `agents/cicd.md`. `promote_qg_failure` is dispatched to a **separate, dedicated**
`quality_gate_resolution` role instead of an added `cicd.md` section, specifically so the AO dashboard's Fleet-table
`RoleBadge` and the Escalations panel can distinguish "an agent is fixing a genuine QG regression on some repo's promote
flow" from "an agent is resolving a git merge conflict" or "an agent is firefighting a bare LDR push" at a glance — the
operator's own stated reason for the split (2026-08-12). Behaviorally the fix is similar (diagnose root cause on
`live-defi-rollout`, fix, push, verify) — the split is about dashboard legibility across a live fleet, not a different
remediation strategy.

## Escalation coverage added 2026-08-12 (previously Slack-only, human-only)

Per an audit of every workflow posting a CRITICAL/WARNING Slack alert cross-referenced against an actual
`escalate-to-orchestrator`/`conflict-resolution-agent` dispatch call, these had zero automated fix-attempt attached
(alert-only, human is the sole line of defense) and now escalate to the generic `cicd` role via a new wall_type each
(proportionate to the ask — these are general CI/infra process failures `cicd`'s own charter already covers, not a
distinct remediation shape worth its own role):

| Workflow                                                | New wall_type                |
| ------------------------------------------------------- | ---------------------------- |
| `reconcile-release-tags.yml`                            | `release_tag_stall`          |
| `sit-gate-stuck-detector.yml`                           | `sit_gate_stuck`             |
| `semver-agent` (unified-trading-ci)                     | `semver_agent_failure`       |
| `cloud-build-router.yml` / `cloud-build-router-aws.yml` | `cloud_build_router_failure` |
| `glue-pool-starvation-monitor.yml`                      | `glue_pool_starvation`       |

Deliberately NOT touched this pass (correctly human-only by design, confirmed via the same audit):
`overnight-agent-orchestrator.yml` / `overnight-dead-man-switch.yml` (escalating to the orchestrator when the
orchestrator itself might be the thing that's dead is circular), `request-major-bump.yml` / `secret-health-check.yml`
(deliberately human-gated, not a mechanical fix), `hotfix-mode.yml` (operator-invoked by definition).

## Still-open coverage gaps (not fixed this pass)

- **Local pre-push ratchet-gate breaches** (a `quality-gates.sh` Pass-1 failure that blocks the commit before it ever
  reaches a GitHub Actions run) have NO wall_type — structurally invisible to every GH-Actions-run-based wall type, not
  just an unwired one. Filed and scoped:
  `plans/active/issues/ci_escalation_no_coverage_for_local_ratchet_gate_breaches_2026_08_10.md` (P2, needs a new
  detector, not just a new wall_type).
- `branch-health.yml`'s `no_promote_pr` / `unknown` lag causes (`promotion_lag_monitor.py::_promote_pr_cause`) have no
  dedicated escalation path — the monitor honestly flags "can't tell" rather than guessing, but nothing acts on that
  signal beyond the Slack post.
