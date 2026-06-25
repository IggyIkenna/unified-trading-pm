---
doc_type: plan
title: Escalation pipeline MVP (role-agnostic, stateful, scoped-link)
summary: Generalize the worker /blocked loop into a role-agnostic escalation record with open/in-progress/resolved state and a scoped Slack link — closing the three gaps between today's blocked loop and the one-alert/one-link/pre-researched-options vision.
status: active
nature: design
stage: [meta]
repos: [agent-orchestrator, alerting-service, deployment-ui]
scope: [engineer, admin]
tags: [escalation, blocked-questions, slack, alert-state, disaster-recovery]
related: [../epics/escalation_and_disaster_recovery_master.md, role_registry_schema_and_broker_mvp_2026_06_25.md]
created: 2026-06-25
parent_epic: escalation_and_disaster_recovery_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3
last_updated: 2026-06-25
locked_by: NA
locked_since: NA
supersedes:
superseded_by:
depends_on: role_registry_schema_and_broker_mvp_2026_06_25
source:
---

# Escalation pipeline MVP (role-agnostic, stateful, scoped-link)

> **E1** of `escalation_and_disaster_recovery_master` — the first child plan. Generalizes the existing worker `/blocked`
> loop (built end-to-end) into a **role-agnostic, stateful, scoped-link** escalation pipeline that every role uses
> identically. Depends on the message broker (`role_registry_schema_and_broker_mvp`, W9) for the reply path. Built
> **additively** — the existing `/blocked` keeps working.

## Why

The blocked loop is built but role-blind and operator-secondary (scout audit, 2026-06-25). Three gaps separate it from
the operator's vision (one alert → one scoped link → pre-researched options → always-visible/filterable):

1. **Scoped link**: the Slack alert deep-links to `/#blocked` — the *whole* queue, not the one question. The human
   hunts.
2. **No alert state**: there is no `open / in-progress / resolved` lifecycle to filter on, and no "I'm on it"
   intermediate, so two operators can collide on the same alert.
3. **Not role-generalized**: `/blocked` is worker→main→operator; there is no uniform entry any role (Data-Eng audit,
   DevOps CI-wall, QA UAT) uses to route a decision to the human with its own pre-researched options.

The self-healing 95% is already covered (AutoSpawn / liveness / pruner + the auto-recovery matrix,
`codex/04-architecture/autonomous-recovery-matrix.md`); this plan only sharpens the human-gated residue. SSOT for the
runtime: `codex/04-architecture/agent-orchestrator-overview.md`.

## Locked design (operator, 2026-06-25)

- **Additive over `BlockedRow`**: a generalized escalation record `{ id, role, domain, question, options[],
  recommendation, severity, state }` — existing `/blocked` rows map onto it; no rewrite, no behavior loss.
- **State machine**: `open → in-progress (claimed) → resolved`. Resolved rows stay browsable + filterable (so people
  see what others already resolved). The `claim` ("I'm on it") prevents collisions — implementable as a Slack reaction
  hack OR a UI button (MVP: UI button; Slack-reaction is a fast-follow).
- **Scoped link**: the Slack alert links to `/escalation/{id}` (one question + its options), not the queue.
- **Human-primary, agent-assisted**: the main agent stays first-responder for *agent-answerable* questions; the human is
  primary for `operator-decision` / `BLOCKED-CREDENTIALS` / `manual_unkill`. The reply routes back via the broker.
- **No new Slack OAuth app** in the MVP (that's E2). Keep the one-way webhook; the interactivity is the scoped link +
  the dashboard/UI resolve surface.

## Phased execution DAG

### Phase 0 — Generalized escalation record [depends: spine broker]

- [ ] [CODE] P1. Escalation record generalizing `BlockedRow` (`role`, `domain`, `severity`, `state` added; `/blocked`
      back-compat shim). **Gate**: existing blocked tests green; new fields persisted + readable.
- [ ] [CODE] P1. State machine `open → in-progress → resolved` + a `claim` transition (`POST /api/escalation/{id}/claim`).
      **Gate**: state transitions unit-tested; double-claim is rejected.

### Phase 1 — Scoped Slack link + reply routing [depends: P0]

- [ ] [CODE] P1. Slack alert links to `/escalation/{id}` (scoped) instead of `/#blocked`. **Gate**: a fired escalation's
      Slack message opens the single-question page.
- [ ] [CODE] P1. Resolution routes the answer back to the originating agent via the broker `reply_to`. **Gate**: an
      answered escalation delivers the choice to a waiting agent (end-to-end test).

### Phase 2 — deployment-ui escalation surface [depends: P0]

- [ ] [UI] P1. deployment-ui escalation tab: list with `open / in-progress / resolved` filter; each row deep-links to
      the agent-orchestrator resolution surface (defer-unify per the `agent_operating_framework_master` UI decision,
      2026-06-25). **Gate**: `pw:L2` spec — filter toggles + a deep-link click; cited regression spec.

## Success criteria

- Any role can post an escalation record `{ role, domain, options[], recommendation }`; the existing `/blocked` path
  still works (back-compat).
- The Slack alert opens a **scoped** single-question page; answering routes back to the originating agent via the broker.
- The deployment-ui tab shows `open / in-progress / resolved` with a working filter and a `claim` ("I'm on it")
  transition; resolved escalations stay browsable. UI change is `pw:L2`-gated.

## Codex SSOT updates

- `codex/04-architecture/escalation-pipeline.md` (NEW) — the role-agnostic record + state machine + scoped-link
  contract; cross-links the auto-recovery matrix (self-heal vs escalate) + the broker.
- `codex/04-architecture/agent-orchestrator-overview.md` — note the generalized escalation record beside `BlockedRow`.

## Progress Log

- 2026-06-25: Plan created as E1 of the new `escalation_and_disaster_recovery_master` epic in the operator design pass.
  Human-driven (`assigned_vm: NA`) — it modifies live escalation plumbing, so operator-driven + additive. Closes the
  three scout-found gaps (scoped-link / alert-state / role-generalization). Depends on the broker
  (`role_registry_schema_and_broker_mvp`, W9).
