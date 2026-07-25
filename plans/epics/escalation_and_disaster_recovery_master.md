---
doc_type: epic
title: Escalation & Disaster Recovery Master (L4)
summary:
  Role-agnostic escalation pipeline (blocked → Slack → human-resolve → UI) + the self-healing/auto-recovery substrate
  every agent role escalates through; 95% self-resolve, the rest escalate cleanly.
status: paused
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, deployment-ui]
scope: [engineer, admin]
tags: [escalation, disaster-recovery, slack, blocked-questions, self-healing, auto-recovery]
related: [../archive/2026_07/escalation_pipeline_mvp_2026_06_25.md] # child plan archived 2026-07-23; todos absorbed into this epic
created: 2026-06-25
name: escalation_and_disaster_recovery_master
tier: L4
priority: P1
assigned_vm: planning # corrected 2026-07-21 (plan-reconcile) — legacy multi-VM host id, deprecated 2026-06-27
parent: master_to_live_defi_2026_05_23
co_operators: [ikenna, harsh]
codex_ssots:
  [/codex/04-architecture/autonomous-recovery-matrix.md, /codex/04-architecture/agent-orchestrator-overview.md]
related_plans: []
last_updated: 2026-07-12 # (was: 2026-06-25; corrected 2026-07-14 per verify-rerun-2 finding 61 — body banner (lines 29-32) + git log show the last substantive edit was 2026-07-12, not 2026-06-25)
locked_by: NA
locked_since: NA
---

> **⏸️ PAUSED per operator decision 2026-06-26** (frontmatter `status: paused` — epic schema gained the `paused` value
> 2026-07-12 per operator ruling) — deferred to next quarter together with W7/W8/W9 (message broker dependency) per
> agent_operating_framework_master.md:62-66 re-scope. Todos remain valid but MUST NOT be dispatched until un-paused.
> Synced per plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md (finding 338).

# Escalation & Disaster Recovery Master (L4)

**Owns**: the one path every agent role takes when it cannot self-resolve — and the self-healing substrate that keeps
that path rare. The design target is **95% self-resolution**: an agent exhausts its own tools + asks peer roles (via the
message broker — `agent_operating_framework_master` W9) before anything reaches a human. When it must escalate, it
escalates **once, cleanly, with options it already researched**, and the whole lifecycle is **always visible + always
resolvable** in one UI.

This epic is **role-agnostic infrastructure**. Each role (Data-Eng, DevOps, QA, …) declares its escalation triggers in
its registry charter (`agent_operating_framework_master` W6); this epic owns the _pipeline_ those triggers flow through.

## Why this epic exists

Today the blocked-question loop is built end-to-end but role-blind and operator-secondary:

- `POST /api/slots/{id}/blocked` → SQLite `BlockedRow` (question + `options[]` + `recommendation`) → Slack alert with a
  dashboard deep-link → dashboard `BlockedCard` (option buttons + "Other" free-text + role selector) →
  `POST /api/blocked/{id}/answer` → worker polls the answer. **BUILT** — see
  `/codex/04-architecture/agent-orchestrator-overview.md`.
- `alerting-service` fans `DP_*` / kill-switch / recon / deployment events to Slack `#data-pipeline-alerts` /
  `#uts-live-alerts`. **BUILT** but fire-and-forget (one-way webhook, no interactive resolution, no alert state).
- The auto-recovery matrix (`/codex/04-architecture/autonomous-recovery-matrix.md`) defines what arms/un-kills
  autonomously vs `manual_unkill` (human-only). **BUILT** as the kill-switch governance.

Three gaps separate this from the operator's vision (operator design pass, 2026-06-25):

1. **The Slack link goes to the _whole_ blocked queue, not a scoped single-question page** — the human has to hunt.
2. **No alert state** — there's no `open / in-progress / resolved` lifecycle a human can filter on; no "someone is
   working on this" intermediate so two operators don't collide.
3. **Escalation is not generalized across roles** — `/blocked` is worker→main→operator; there is no uniform "role R hit
   a wall, route the decision to the human with R's pre-researched options" entry point that any role (Data-Eng audit,
   DevOps CI-wall, QA UAT) uses identically.

## Target pipeline (role-agnostic)

```
agent (any role) hits a wall
   → self-resolve attempts exhausted (autonomy gradient: Proceed)
   → ask peer roles via broker (W9)               ── 95% resolved here
   → still blocked → ESCALATE (autonomy gradient: Escalate-non-blocking | Gate)
       → one durable escalation record { role, domain, question, options[], recommendation, severity, state }
       → ONE Slack alert  → scoped link → /escalation/{id}  (just this question + its options)
       → human: pick an option | "Other" free-text | "I'm on it" (→ in-progress)
       → resolved → answer routed back to the originating agent (broker reply)
   → always visible in deployment-ui; filter open vs in-progress vs resolved; resolved stay browsable
```

**Self-healing first**: most "escalations" are rule-based and never need a human (dirty repo too long, stale worker,
tmux lost, CI label mismatch). Those are handled by the existing AutoSpawn / liveness / pruner mechanisms + the
auto-recovery matrix. This epic only routes to a human for the **`manual_unkill` / operator-decision** residue.

## Workstream registry (child plans)

| WS  | Child plan                                                                                                  | Scope                                                                                                                                    | Depends                                                                                                                   | Priority | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| --- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| E1  | `escalation_pipeline_mvp_2026_06_25` → [ARCHIVED](../archive/2026_07/escalation_pipeline_mvp_2026_06_25.md) | Generalize `/blocked` → role-agnostic escalation record + `open/in-progress/resolved` state + scoped Slack link + close the 3 gaps       | **none** (was: `agent_operating_framework_master` W9 broker — retired 2026-07-16, superseded by `assigned_role` dispatch) | P1       | **tracked-in-epic, paused** — child plan archived 2026-07-23 (operator) as duplicate tracking; its 5 UNBUILT todos now live in § "P1 — escalation pipeline MVP" below, the single home. Work is NOT descoped; un-pause the epic to resume. (was: paused; was: proposed — corrected 2026-07-12, doc-reconciliation autofix finding 50, `plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified" blanket ruling, cascading the epic's own 2026-06-26 pause banner above) |
| E2  | _(future)_ slack-interactive-resolve                                                                        | Real Slack app (Block Kit action buttons / `/resolve` slash) so a human answers in Slack without the dashboard hop                       | E1                                                                                                                        | P2       | deferred                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| E3  | _(future)_ dr-runbook-registry                                                                              | Disaster-recovery runbooks (owner/cadence/verifier/last_executed) wired to the auto-recovery matrix for non-self-healing failure classes | E1                                                                                                                        | P2       | deferred                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |

## Composition with other epics

- **`agent_operating_framework_master`** — owns the role registry (W6) + the message broker (W9) this pipeline rides on.
  Roles declare escalation triggers there; this epic consumes them. **E1's `Depends` is `none`, not W9** — W9
  (`role_registry_schema_and_broker_mvp`) was archived NOT-REQUIRED 2026-07-16, superseded by `assigned_role` dispatch;
  the existing `POST /api/blocked/{id}/answer` → worker-poll path already satisfies the reply-routing requirement (W6
  role registry still composes). Corrected 2026-07-23 per the Progress Log entry below.
- **`observability_master`** (vm-cross-cutting, co-tier) — the deployment-ui surfaces + alert-state rendering compose
  with the observability dashboard. The "always visible / filter open-vs-resolved" UI lands as a deployment-ui tab.
- **`client_isolation_and_governance_master`** — the `manual_unkill` / kill-switch governance that this pipeline's
  human-gated branch defers to (`/codex/04-architecture/autonomous-recovery-matrix.md`).

## Out of scope

- The message broker itself (owned by `agent_operating_framework_master` W9 — this epic _consumes_ it).
- Per-role escalation _triggers_ (declared in each role's W6 charter — this epic owns the _pipeline_, not the triggers).
- A new Slack OAuth app (E2, deferred — the MVP keeps the one-way webhook + dashboard-resolve, just scoped + stateful).

## Design input awaiting scope (not yet folded into E1)

- [`blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md`](../active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md)
  — operator-reported: insufficient context in question/options, scale (~30 open questions), duplicate questions across
  agents/sessions, and the operator unable to reach the ORIGINATING agent for follow-up once it's dead. Bigger than E1's
  scoped-link + state-machine work — read it before scoping E1 (or a wider blocked-questions redesign). Deliberately
  deferred; not actioned.

## P1 — escalation pipeline MVP

**This epic section is now the SINGLE tracking home for E1** (child plan archived 2026-07-23 as duplicate tracking — its
5 todos were absorbed here; 4 were already mirrored verbatim). The design reference (locked design, phased DAG, gates,
success criteria) lives in the archived plan:
[`../archive/2026_07/escalation_pipeline_mvp_2026_06_25.md`](../archive/2026_07/escalation_pipeline_mvp_2026_06_25.md).
Generalize the blocked loop into a role-agnostic, stateful, scoped-link escalation pipeline. **The broker (W9) is NOT a
dependency** — corrected 2026-07-16: that plan was archived as NOT-REQUIRED (superseded by `assigned_role` dispatch),
and the reply path already exists via `POST /api/blocked/{id}/answer`. All 5 todos code-verified UNBUILT 2026-07-16.

- [ ] [CODE] P1. Role-agnostic escalation record
      `{ role, domain, question, options[], recommendation, severity, state }` generalizing `BlockedRow` (additive;
      existing `/blocked` keeps working). (E1)
- [ ] [CODE] P1. `open / in-progress / resolved` state + a `claim` ("I'm on it") transition; resolved rows stay
      browsable + filterable. (E1)
- [ ] [CODE] P1. Scoped Slack link → `/escalation/{id}` (one question + its options), not the whole queue. (E1)
- [ ] [CODE] P1. Resolution routes the answer back to the originating agent — via the EXISTING
      `POST /api/blocked/{id}/answer` → worker-reads-on-next-poll path, **not** the broker `reply_to` (broker retired
      2026-07-16). **Gate**: an answered escalation delivers the choice to a waiting agent (end-to-end test). (E1 —
      migrated from the archived child plan 2026-07-23, reworded off the retired broker dependency.)
- [ ] [UI] P1. deployment-ui escalation tab: open / in-progress / resolved filter; deep-links to the agent-orchestrator
      resolution surface (defer-unify — `agent_operating_framework_master` UI decision 2026-06-25). (E1)

## P2 — deferred (own efforts)

- [ ] [CODE] P2. **E2** — Slack-interactive resolve (Block Kit buttons / slash command) so the human answers in Slack.
- [ ] [DOCS] P2. **E3** — DR runbook registry (owner/cadence/verifier/last_executed) for non-self-healing failure
      classes.

## Progress Log

- 2026-07-23: **E1's child plan `escalation_pipeline_mvp_2026_06_25` ARCHIVED (operator instruction); this epic is now
  its single tracking home.** The archival was safe because this epic's "P1 — escalation pipeline MVP" section already
  carried 4 of the plan's 5 todos verbatim — the two docs were duplicate-tracking one workstream. The 5th (reply
  routing) was added here, **reworded to drop the broker `reply_to`**: `role_registry_schema_and_broker_mvp` was
  archived NOT-REQUIRED on 2026-07-16 (superseded by `assigned_role` dispatch), and the existing
  `POST /api/blocked/{id}/answer` → worker-poll path already satisfies the requirement. **E1's `Depends` is therefore
  now `none`, not W9** — the "hard dependency: E1 needs W9" line under _Composition with other epics_ is stale for the
  reply path (W6 role registry still composes). All 5 todos were code-verified UNBUILT on 2026-07-16 and stay wanted;
  the epic's 2026-06-26 pause still governs. Design reference (locked design, phased DAG, gates) lives in the archived
  plan.
- 2026-06-25: Epic created in the operator role-registry design pass. Split out of the cross-agent escalation thread of
  `agent_operating_framework_master` because it is genuinely distinct (role-agnostic pipeline + DR substrate) and
  composes with `observability_master`. Three gaps scoped (scoped-link / alert-state / role-generalization). E1 (MVP)
  proposed as the first child plan, human-driven (`assigned_vm: NA`), depends on the broker (W9). E2/E3 deferred.

## Assigned active plans

_(no active plans currently declare `parent_epic: escalation_and_disaster_recovery_master`. Audit-pool wrapper plans for
this epic land here as they are dispatched. See [README.md](README.md) for the audit→plan→epic flow.)_
