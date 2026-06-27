---
doc_type: plan
title: Data-Engineering role — vertical pilot (first end-to-end role on the spine)
summary: Stand up the Data-Eng role end-to-end on the registry/broker spine — charter + /data-freshness skill + daily-audit workflow + wire the discarded AI triage — proving trigger→agent→escalation→answer with the most existing scaffolding.
status: active
nature: design
stage: [data, meta]
repos: [agent-orchestrator, alerting-service]
scope: [engineer, admin]
tags: [role-registry, data-engineering, data-quality, daily-audit, triage]
related: [../epics/agent_operating_framework_master.md, role_registry_schema_and_broker_mvp_2026_06_25.md, escalation_pipeline_mvp_2026_06_25.md]
created: 2026-06-25
parent_epic: agent_operating_framework_master
assigned_vm: vm-cross-cutting
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
last_updated: 2026-06-25
locked_by: NA
locked_since: NA
supersedes:
superseded_by:
depends_on: role_registry_schema_and_broker_mvp_2026_06_25
source:
---

# Data-Engineering role — vertical pilot (first end-to-end role on the spine)

> **W6 role instance** of `agent_operating_framework_master` — the **first full vertical** proving the pattern
> end-to-end. Chosen because it has the most existing scaffolding: the daily Cloud Run audit crons, the
> `#data-pipeline-alerts` Slack route, and the `data_pipeline_failure` worker already exist. This plan binds them into
> one role (charter + skill + workflow + escalation) and lands a near-free quick win.
>
> **Dispatch note**: `assigned_vm: harsh_pc` (the standalone fleet-dispatch test host — the only currently-runnable
> backend per `orchestrator_vm_registry.yaml`). Its *semantic* epic home is the data-pipeline VM (`vm-ml`), which is
> parked; re-point `assigned_vm` to `vm-ml` when the epic fleet runs. **Operator chose to dispatch this plan**
> (2026-06-25); the other three role/spine plans are human-driven.

## Why

Data-pipeline correctness is the heartbeat (`codex/02-data/data-pipeline-correctness-hard-rule.md`). Today the Data-Eng
*function* exists as disconnected pieces (scout audit, 2026-06-25):

- **Daily audit crons** (Cloud Run): `data_pipeline_daily_digest` (07:00), `manifest_hygiene_daily` (08:00 changed /
  weekly full), `reprobe_new_empty_confirmed` (09:00) → emit `DP_*` events.
- **alerting-service** routes `DP_*` → Slack `#data-pipeline-alerts`.
- **`data_pipeline_failure` worker** (`agents/data_pipeline_failure.md`) is dispatched on a `data_pipeline_failure` wall
  to diagnose + fix.
- **A bug**: `alerting-service` already computes an AI root-cause triage then **throws it away** (`claude_slack_agent.py`
  → `_ = triage_text`).

None of this is a *role* — there is no charter, no on-demand "is my data healthy?" verb, no daily audit that an agent
owns and escalates from. This plan makes Data-Eng a first-class registry row riding the spine, and proves
trigger→agent→escalation→answer. SSOT for what's a real failure vs honest absence:
`codex/02-data/availability-manifest-and-data-status.md`.

## Locked design (operator, 2026-06-25)

- **Data-Eng is a hybrid role**: `lifecycle: scheduled` for the daily audit (cron-triggered) + a `persistent`-style
  query surface for "is my data flowing?" answered against the manifest (cheap reads, no full GCS walk —
  single-walk discipline). The daily audit is a **Workflow** (fan-out over asset groups, Sonnet workers, synth at the
  end) — cheap, and the model lives in the fan-out not the orchestrator.
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
      **Gate**: a synthetic `DP_*` fire posts a triage thread reply in a test channel; QG green.

### Phase 1 — Data-Eng charter row [depends: spine Phase 1]

- [ ] [DOCS] P1. `agent-orchestrator/agents/data_engineering.md` registry row: `role: data_engineering`, `model: sonnet`,
      `thinking: high` (correctness heartbeat), `lifecycle: scheduled`, `triggers` (daily audit crons + `DP_*` walls +
      "is data healthy?" query), `does`/`does_not`, `escalation_to` (operator for credentials/decisions),
      `temperament_base: diligent`. **Gate**: `docspec --check` clean; loads in `role_registry.py`.

### Phase 2 — On-demand verb (the cross-agent Q&A) [depends: P1]

- [ ] [CODE] P1. `/data-freshness <asset_group>` skill → light JSON `{ last_captured, expected_unattempted, missing,
      stale }` read from the availability manifest (`_index/availability_index.parquet`) — **no whole-corpus GCS walk**
      (single-walk discipline). **Gate**: returns valid JSON for a known AG; matches the manifest's 4-state counts.

### Phase 3 — Daily-audit workflow (heavy fan-out) [depends: P1]

- [ ] [CODE] P1. Package the t+1 batch-vs-live availability audit as a Workflow: fan out one Sonnet worker per asset
      group (audit completeness + continuity + perf regression vs the manifest), synth a single light-JSON verdict +
      escalate REDs through E1. Reuses the existing cron checks; does not re-walk GCS. **Gate**: workflow runs over ≥2
      AGs on real manifest data, emits a verdict, a synthetic RED escalates via the pipeline.

## Success criteria

- The discarded AI triage is delivered (quick win shipped + verified on a synthetic fire).
- Data-Eng is a loadable/routable registry row; `/data-freshness` returns light JSON against the real manifest.
- The daily-audit workflow runs end-to-end on real data (manifest-verified, no new whole-corpus walk) and a RED audit
  escalates through `escalation_pipeline_mvp` — proving trigger→agent→escalation→answer for one full role.
- **Runtime-verified** on `harsh_pc` (not smoke-test green) — a real audit run with manifest-verified counts.

## Codex SSOT updates

- `codex/02-data/availability-manifest-and-data-status.md` — cross-link the Data-Eng role + `/data-freshness` reader.
- `codex/04-architecture/role-registry.md` (from the spine) — add Data-Eng as the first vertical worked example.

## Progress Log

- 2026-06-25: Plan created as the first full vertical role on the spine. Chosen for the most existing scaffolding
  (audit crons + Slack route + `data_pipeline_failure` worker) and a near-free quick win (wire the discarded
  `triage_text`). **Operator chose to dispatch this one** → `assigned_vm: harsh_pc` (runnable standalone test host;
  semantic home `vm-ml` is parked). Depends on `role_registry_schema_and_broker_mvp`; escalates via
  `escalation_pipeline_mvp`.
