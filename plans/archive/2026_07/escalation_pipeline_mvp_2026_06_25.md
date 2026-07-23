---
doc_type: plan
title: Escalation pipeline MVP (role-agnostic, stateful, scoped-link)
summary:
  Generalize the worker /blocked loop into a role-agnostic escalation record with open/in-progress/resolved state and a
  scoped Slack link — closing the three gaps between today's blocked loop and the
  one-alert/one-link/pre-researched-options vision.
status: superseded
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, deployment-ui]
scope: [engineer, admin]
tags: [escalation, blocked-questions, slack, alert-state, disaster-recovery]
related:
  [
    ../epics/escalation_and_disaster_recovery_master.md,
    /plans/archive/2026_07/role_registry_schema_and_broker_mvp_2026_06_25.md,
  ]
created: 2026-06-25
parent_epic: escalation_and_disaster_recovery_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3
last_updated: 2026-07-23
locked_by:
locked_since:
supersedes:
superseded_by: ../epics/escalation_and_disaster_recovery_master.md
depends_on: # (was: role_registry_schema_and_broker_mvp_2026_06_25 — that broker plan was ARCHIVED as NOT-REQUIRED
  # 2026-07-16, superseded by `assigned_role` dispatch; the dependency was stale, not real)
source:
drift_direction: advance-code
---

# Escalation pipeline MVP (role-agnostic, stateful, scoped-link)

> **📦 ARCHIVED 2026-07-23 (operator instruction) — NOT because the work is done. All 5 todos were code-verified UNBUILT
> on 2026-07-16 and remain wanted; they now live in the parent epic
> [`escalation_and_disaster_recovery_master`](../epics/escalation_and_disaster_recovery_master.md) § "P1 — escalation
> pipeline MVP", which is everlasting and carries the same pause banner.** This plan is archived as a redundant
> container: 4 of its 5 todos were ALREADY mirrored verbatim in that epic section, so keeping both was duplicate
> tracking of one workstream. The 5th (reply routing) was added to the epic during this archival, reworded per the
> 2026-07-16 audit — it does NOT need the broker; the existing `POST /api/blocked/{id}/answer` → worker-poll path
> already satisfies it. **Nothing was descoped; the epic is the single tracking home. Un-pause the epic to resume.**
> Design content below (locked design, phased DAG, success criteria) stays as the reference the epic todos point at.

> **⏸️ PAUSED per operator decision 2026-06-26** — the parent epic `escalation_and_disaster_recovery_master` carries a
> pause banner deferring this whole workstream (together with W7/W8/W9 message-broker dependency) to next quarter per
> `agent_operating_framework_master.md:62-66` re-scope. Todos remain valid. Corrected 2026-07-12 — doc-reconciliation
> autofix finding 50, `plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified" blanket ruling (same
> finding 338 sync as the epic banner). **CORRECTED 2026-07-14 (doc-reconciliation verify-rerun-2, finding 59)**: the
> frontmatter `status:` field itself was STILL `active` (never cascaded from the 2026-06-26 ruling, despite this banner
> saying so since 2026-07-12) — flipped frontmatter `status: active` → `paused` and bumped `last_updated` to match
> (finding 62). (was: frontmatter `status: active` / `last_updated: 2026-06-25`.)

> **E1** of `escalation_and_disaster_recovery_master` — the first child plan. Generalizes the existing worker `/blocked`
> loop (built end-to-end) into a **role-agnostic, stateful, scoped-link** escalation pipeline that every role uses
> identically. Depends on the message broker (`role_registry_schema_and_broker_mvp`, W9) for the reply path. Built
> **additively** — the existing `/blocked` keeps working.

## Why

The blocked loop is built but role-blind and operator-secondary (scout audit, 2026-06-25). Three gaps separate it from
the operator's vision (one alert → one scoped link → pre-researched options → always-visible/filterable):

1. **Scoped link**: the Slack alert deep-links to `/#blocked` — the _whole_ queue, not the one question. The human
   hunts.
2. **No alert state**: there is no `open / in-progress / resolved` lifecycle to filter on, and no "I'm on it"
   intermediate, so two operators can collide on the same alert.
3. **Not role-generalized**: `/blocked` is worker→main→operator; there is no uniform entry any role (Data-Eng audit,
   DevOps CI-wall, QA UAT) uses to route a decision to the human with its own pre-researched options.

The self-healing 95% is already covered (AutoSpawn / liveness / pruner + the auto-recovery matrix,
`/codex/04-architecture/autonomous-recovery-matrix.md`); this plan only sharpens the human-gated residue. SSOT for the
runtime: `/codex/04-architecture/agent-orchestrator-overview.md`.

## Locked design (operator, 2026-06-25)

- **Additive over `BlockedRow`**: a generalized escalation record
  `{ id, role, domain, question, options[], recommendation, severity, state }` — existing `/blocked` rows map onto it;
  no rewrite, no behavior loss.
- **State machine**: `open → in-progress (claimed) → resolved`. Resolved rows stay browsable + filterable (so people see
  what others already resolved). The `claim` ("I'm on it") prevents collisions — implementable as a Slack reaction hack
  OR a UI button (MVP: UI button; Slack-reaction is a fast-follow).
- **Scoped link**: the Slack alert links to `/escalation/{id}` (one question + its options), not the queue.
- **Human-primary, agent-assisted**: the main agent stays first-responder for _agent-answerable_ questions; the human is
  primary for `operator-decision` / `BLOCKED-CREDENTIALS` / `manual_unkill`. The reply routes back via the broker.
- **No new Slack OAuth app** in the MVP (that's E2). Keep the one-way webhook; the interactivity is the scoped link +
  the dashboard/UI resolve surface.

## Phased execution DAG

> **🔁 ALL 5 TODOS MIGRATED 2026-07-23** →
> [`escalation_and_disaster_recovery_master`](../epics/escalation_and_disaster_recovery_master.md) § "P1 — escalation
> pipeline MVP". Checkboxes are removed here so this archived plan cannot double-count them; the phase structure, gates
> and dependency order below remain the authoritative design the epic todos execute against.

### Phase 0 — Generalized escalation record [depends: none — see banner; the broker dep was stale]

🔁 **MOVED → epic.** Escalation record generalizing `BlockedRow` (`role`, `domain`, `severity`, `state` added;
`/blocked` back-compat shim). **Gate**: existing blocked tests green; new fields persisted + readable.

🔁 **MOVED → epic.** State machine `open → in-progress → resolved` + a `claim` transition
(`POST /api/escalation/{id}/claim`). **Gate**: state transitions unit-tested; double-claim is rejected.

### Phase 1 — Scoped Slack link + reply routing [depends: P0]

🔁 **MOVED → epic.** Slack alert links to `/escalation/{id}` (scoped) instead of `/#blocked`. **Gate**: a fired
escalation's Slack message opens the single-question page.

🔁 **MOVED → epic (reworded).** Resolution routes the answer back to the originating agent. **The broker `reply_to` is
NOT required** — per the 2026-07-16 audit the existing `POST /api/blocked/{id}/answer` → worker-reads-on-next-poll path
already delivers this; the epic todo names that path. **Gate**: an answered escalation delivers the choice to a waiting
agent (end-to-end test).

### Phase 2 — deployment-ui escalation surface [depends: P0]

🔁 **MOVED → epic.** deployment-ui escalation tab: list with `open / in-progress / resolved` filter; each row deep-links
to the agent-orchestrator resolution surface (defer-unify per the `agent_operating_framework_master` UI decision,
2026-06-25). **Gate**: `pw:L2` spec — filter toggles + a deep-link click; cited regression spec.

## Success criteria

- Any role can post an escalation record `{ role, domain, options[], recommendation }`; the existing `/blocked` path
  still works (back-compat).
- The Slack alert opens a **scoped** single-question page; answering routes back to the originating agent via the
  broker.
- The deployment-ui tab shows `open / in-progress / resolved` with a working filter and a `claim` ("I'm on it")
  transition; resolved escalations stay browsable. UI change is `pw:L2`-gated.

## Codex SSOT updates

- `/codex/04-architecture/escalation-pipeline.md` (NEW — **never created**; this plan was archived with the code
  unbuilt, so the epic inherits this deliverable) — the role-agnostic record + state machine + scoped-link contract;
  cross-links the auto-recovery matrix (self-heal vs escalate) + the broker.
- `/codex/04-architecture/agent-orchestrator-overview.md` — note the generalized escalation record beside `BlockedRow`.

## Progress Log

- 2026-06-25: Plan created as E1 of the new `escalation_and_disaster_recovery_master` epic in the operator design pass.
  Human-driven (`assigned_vm: NA`) — it modifies live escalation plumbing, so operator-driven + additive. Closes the
  three scout-found gaps (scoped-link / alert-state / role-generalization). Depends on the broker
  (`role_registry_schema_and_broker_mvp`, W9).
- 2026-07-23: **ARCHIVED per operator instruction — 5-step ritual run.** (1) The 5 open todos were NOT stranded: they
  migrated to the parent epic's "P1 — escalation pipeline MVP" section, which already carried 4 of the 5 verbatim
  (tagged `(E1)`) — this plan was duplicate tracking of one workstream. The 5th (reply routing) was ADDED to the epic,
  reworded to drop the retired broker dependency per the 2026-07-16 audit. (2) No DEFERRED prose remains — the "Deferred
  next step (operator, keep-for-now)" item from 2026-07-16 is discharged here: the stale
  `depends_on: role_registry_schema_and_broker_mvp` is removed and Phase 1b is reworded to reuse `/blocked`. (3) Banner
  - `status: superseded` + `superseded_by:` the epic. (4) **Codex-alignment: nothing to update** — the two SSOTs this
    plan would have written (`codex/04-architecture/escalation-pipeline.md` NEW — never created, and the
    `agent-orchestrator-overview.md` note beside `BlockedRow`) were contingent on the code landing, and the code is
    unbuilt; the epic inherits those codex deliverables. (5) No lock to clear (`locked_by:` was empty). Inbound
    references repointed at the archive path.
- 2026-07-16: **Audited — KEPT (not archived); genuine unstarted work.** Code-verified all 5 todos are UNBUILT:
  `BlockedRow` (`server/orm.py:163`) is still bare (no `role`/`domain`/`severity`/`state`); no `EscalationRow`, no state
  machine, no `POST /api/escalation/{id}/claim`; no scoped `/escalation/{id}` Slack link (the alert still links to the
  dashboard/queue); no deployment-ui escalation tab. It sharpens the human-gated 5% (self-heal 95% already covered).
  **Stale dependency to fix when we resume**: `depends_on: role_registry_schema_and_broker_mvp` names the message broker
  that was ARCHIVED as NOT-REQUIRED (2026-07-16, superseded by `assigned_role` dispatch). The plan is NOT actually
  blocked — the reply path (Phase 1b) already exists via the `/blocked` answer mechanism
  (`POST /api/blocked/{id}/answer` → worker reads on next poll), and Phases 0/1a/2 (record + state + scoped link + UI)
  need no broker at all. **Deferred next step (operator, keep-for-now):** drop the broker `depends_on` + reword Phase 1b
  to reuse `/blocked`, then reprioritize off `status: paused`.
