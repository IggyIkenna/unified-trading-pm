---
doc_type: plan
title: Data-Engineering role — vertical pilot (first end-to-end role on the spine)
summary:
  Stand up the Data-Eng role end-to-end on the registry/broker spine — charter + /data-freshness skill + daily-audit
  workflow + wire the discarded AI triage — proving trigger→agent→escalation→answer with the most existing scaffolding.
status: complete
nature: design
asset_group: [cross-cutting]
stage: [data, meta]
repos: [agent-orchestrator, alerting-service]
scope: [engineer, admin]
tags: [role-registry, data-engineering, data-quality, daily-audit, triage, archived]
related:
  [
    ../epics/agent_operating_framework_master.md,
    /plans/archive/2026_07/role_registry_schema_and_broker_mvp_2026_06_25.md,
    /plans/active/escalation_pipeline_mvp_2026_06_25.md,
  ]
created: 2026-06-25
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only # was: orchestrator-agent — OPERATOR RULING 2026-07-12 (final Q&A, finding 9): the two-track model stands; this plan is not AO-dispatched (assigned_vm: NA), so (NA, local-only) is the valid pairing. Prior flag annotation superseded by the ruling.
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
last_updated: 2026-07-16
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: role_registry_schema_and_broker_mvp_2026_06_25
source:
assigned_role: data_engineering
drift_direction: advance-code
---

# Data-Engineering role — vertical pilot (first end-to-end role on the spine)

> **🗄️ ARCHIVED 2026-07-16 — charter delivered; pilot scope deferred; ONE live bug carved out (operator decision).**
> Phase 1 charter is DONE + loaded: `unified-trading-pm/agents/data_engineering.md` carries the `agent-role` row
> (`role: data_engineering`, `model: sonnet`, `thinking: high`, `lifecycle: scheduled`), is `docspec`-green, loads in
> `role_registry.py` (schema SSOT `scripts/docs/docspec.py`; `role-registry.md` codex doc deleted 2026-07-16). Phase 2
> `/data-freshness` shipped at MVP (documented boot-prompt command in `data_engineering.md § Available skills`). Phase 3
> (daily-audit Workflow) is deferred pilot scope — one of the 4 role pilots `agent_operating_framework_master` defers to
> next quarter. **⚠️ Phase 0 is a genuine LIVE BUG, NOT deferred pilot scope**:
> `alerting-service/alerting_service/core/claude_slack_agent.py:43` still discards the computed AI triage
> (`_ = triage_text`) instead of posting it to the `#data-pipeline-alerts` thread — a near-free, spine-independent fix
> carved out here (see Phase 0 + Progress Log); flagged to the operator to extract as an issue doc if it should stay
> tracked as active work.

> **W6 role instance** of `agent_operating_framework_master` — the **first full vertical** proving the pattern
> end-to-end. Chosen because it has the most existing scaffolding: the daily Cloud Run audit crons, the
> `#data-pipeline-alerts` Slack route, and the `data_pipeline_failure` worker already exist. This plan binds them into
> one role (charter + skill + workflow + escalation) and lands a near-free quick win.
>
> **Dispatch note (HISTORICAL — corrected 2026-07-12, doc-reconciliation autofix finding 8,
> `plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified" blanket ruling)**: this note was written
> 2026-06-25, two days before the 2026-06-27 single-VM architecture retirement
> (`/codex/12-agent-workflow/orchestrator-multi-vm-topology.md`) fixed `assigned_vm` to `{planning, NA}` only — host-id
> values like `harsh_pc` are no longer valid. It was never revisited after that retirement. The frontmatter
> `assigned_vm: NA` (line 15) is therefore already correct under current rules; the text below is preserved as
> historical dispatch context, not a live value. (was: `assigned_vm: harsh_pc` (the standalone fleet-dispatch test host
> — the only currently-runnable backend per `orchestrator_vm_registry.yaml`). Its _semantic_ epic home is the
> data-pipeline VM (`vm-ml`), which is parked; re-point `assigned_vm` to `vm-ml` when the epic fleet runs. **Operator
> chose to dispatch this plan** (2026-06-25); the other three role/spine plans are human-driven.) Current dispatch now
> routes via `assigned_role: data-pipeline-engineer` (line 28), not VM assignment.

## Why

Data-pipeline correctness is the heartbeat (`/codex/02-data/data-pipeline-correctness-hard-rule.md`). Today the Data-Eng
_function_ exists as disconnected pieces (scout audit, 2026-06-25):

- **Daily audit crons** (Cloud Run): `data_pipeline_daily_digest` (07:00), `manifest_hygiene_daily` (08:00 changed /
  weekly full), `reprobe_new_empty_confirmed` (09:00) → emit `DP_*` events.
- **alerting-service** routes `DP_*` → Slack `#data-pipeline-alerts`.
- **`data_pipeline_failure` worker** (`agents/data_pipeline_failure.md`) is dispatched on a `data_pipeline_failure` wall
  to diagnose + fix.
- **A bug**: `alerting-service` already computes an AI root-cause triage then **throws it away**
  (`claude_slack_agent.py` → `_ = triage_text`).

None of this is a _role_ — there is no charter, no on-demand "is my data healthy?" verb, no daily audit that an agent
owns and escalates from. This plan makes Data-Eng a first-class registry row riding the spine, and proves
trigger→agent→escalation→answer. SSOT for what's a real failure vs honest absence:
`/codex/02-data/availability-manifest-and-data-status.md`.

## Locked design (operator, 2026-06-25)

- **Data-Eng is a hybrid role**: `lifecycle: scheduled` for the daily audit (cron-triggered) + a `persistent`-style
  query surface for "is my data flowing?" answered against the manifest (cheap reads, no full GCS walk — single-walk
  discipline). The daily audit is a **Workflow** (fan-out over asset groups, Sonnet workers, synth at the end) — cheap,
  and the model lives in the fan-out not the orchestrator.
- **Diligence dial is context-dependent**: paranoid on live-traded asset groups, relaxed on un-traded ones —
  `temperament_base × criticality(asset_group, env, critical_path)`. v1 = a static criticality field; v2 = the
  criticality registry (W10). **No deadline-deferral of a RED data audit** (correctness HARD RULE).
- **Escalates through the generalized pipeline** (`escalation_pipeline_mvp`, E1): a `BLOCKED-CREDENTIALS` /
  operator-decision residue routes to the human with pre-researched options; everything else self-resolves or files a
  `data_pipeline_failure` fix.

## Phased execution DAG

### Phase 0 — Quick win (near-free, unblocks value immediately) [no dep]

- [ ] [CODE] P1. Wire the discarded AI triage: in `alerting-service/.../claude_slack_agent.py` deliver `triage_text` as
      the Slack thread reply (replace `_ = triage_text`) so `DP_*` alerts carry root-cause + suggested actions.
      **Gate**: a synthetic `DP_*` fire posts a triage thread reply in a test channel; QG green. — **⚠️ LIVE BUG, CARVED
      OUT (not deferred pilot scope).** Verified 2026-07-16: `claude_slack_agent.py:43` still does `_ = triage_text`.
      Near-free fix, independent of the registry/broker spine — preserved as a finding on archival; extract to an issue
      doc if it should be tracked as active work.

### Phase 1 — Data-Eng charter row [depends: spine Phase 1]

- [x] ✅ [DOCS] P1. `unified-trading-pm/agents/data_engineering.md` registry row: `role: data_engineering`,
      `model: sonnet`, `thinking: high` (correctness heartbeat), `lifecycle: scheduled`, `triggers` (daily audit crons +
      `DP_*` walls + "is data healthy?" query), `does`/`does_not`, `escalation_to` (operator for credentials/decisions),
      `temperament_base: diligent`. **Gate**: `docspec --check` clean; loads in `role_registry.py`. — DONE: charter
      carries `role: data_engineering` / `sonnet` / `thinking: high` / `lifecycle: scheduled`, docspec-green, loads in
      `role_registry.py`. (`temperament_base`/`escalation_to` left unfilled — elective, not blocking.)

### Phase 2 — On-demand verb (the cross-agent Q&A) [depends: P1]

- [ ] [CODE] P1. `/data-freshness <asset_group>` skill → light JSON
      `{ last_captured, expected_unattempted, missing,     stale }` read from the availability manifest
      (`_index/availability_index.parquet`) — **no whole-corpus GCS walk** (single-walk discipline). **Gate**: returns
      valid JSON for a known AG; matches the manifest's 4-state counts. — MVP-DONE as a documented boot-prompt command
      (`data_engineering.md § Available skills`); backend light-JSON endpoint deferred. NOT REQUIRED for archival.

### Phase 3 — Daily-audit workflow (heavy fan-out) [depends: P1]

- [ ] [CODE] P1. Package the t+1 batch-vs-live availability audit as a Workflow: fan out one Sonnet worker per asset
      group (audit completeness + continuity + perf regression vs the manifest), synth a single light-JSON verdict +
      escalate REDs through E1. Reuses the existing cron checks; does not re-walk GCS. **Gate**: workflow runs over ≥2
      AGs on real manifest data, emits a verdict, a synthetic RED escalates via the pipeline. — DEFERRED pilot scope
      (heavy fan-out build; not built — no such Workflow exists). Not on the make-AO-usable critical path per the epic;
      next quarter.

## Success criteria

- The discarded AI triage is delivered (quick win shipped + verified on a synthetic fire).
- Data-Eng is a loadable/routable registry row; `/data-freshness` returns light JSON against the real manifest.
- The daily-audit workflow runs end-to-end on real data (manifest-verified, no new whole-corpus walk) and a RED audit
  escalates through `escalation_pipeline_mvp` — proving trigger→agent→escalation→answer for one full role.
- **Runtime-verified** on `harsh_pc` (not smoke-test green) — a real audit run with manifest-verified counts.

## Codex SSOT updates

- `/codex/02-data/availability-manifest-and-data-status.md` — cross-link the Data-Eng role + `/data-freshness` reader.
- `unified-trading-pm/agents/data_engineering.md` is the Data-Eng worked-example registry row (`agent-role` schema
  enforced by `scripts/docs/docspec.py`; the `/codex/04-architecture/role-registry.md` doc was retired 2026-07-16,
  consolidated into docspec + the charters).

## Progress Log

- 2026-06-25: Plan created as the first full vertical role on the spine. Chosen for the most existing scaffolding (audit
  crons + Slack route + `data_pipeline_failure` worker) and a near-free quick win (wire the discarded `triage_text`).
  **Operator chose to dispatch this one** → `assigned_vm: harsh_pc` (runnable standalone test host; semantic home
  `vm-ml` is parked) (HISTORICAL — superseded by the 2026-06-27 single-VM architecture retirement; `assigned_vm` is now
  `{planning, NA}` only, dispatch routes via `assigned_role` instead. Corrected 2026-07-12, doc-reconciliation autofix
  finding 8, `plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified" blanket ruling). Depends on
  `role_registry_schema_and_broker_mvp`; escalates via `escalation_pipeline_mvp`.
- 2026-07-16: **ARCHIVED** (operator decision). Phase 1 charter delivered + loaded (`agents/data_engineering.md`,
  `role: data_engineering`, `lifecycle: scheduled`, docspec-green); Phase 2 `/data-freshness` at MVP (documented
  command). Phase 3 daily-audit Workflow = deferred pilot scope (next quarter, per `agent_operating_framework_master`).
  **Phase 0 (discarded AI triage) is a genuine live bug carved out on archival** — `alerting-service` still does
  `_ = triage_text` (`claude_slack_agent.py:43`), throwing away the computed root-cause triage instead of posting it to
  `#data-pipeline-alerts`; a near-free fix independent of the spine (flagged to operator to extract as an issue doc if
  tracked). Moved to `plans/archive/2026_07/`.
