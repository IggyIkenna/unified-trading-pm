---
doc_type: plan
title: tradfi venue e2e wiring batch 1 — 2026-08-16
summary: >-
  Fresh carve-out from venue_e2e_wiring_2026_08_16.md's "Fork per-asset-group dispatch batches" P0 todo — walks
  contract steps 1-9 across every tradfi (venue, data_type) row from `unified-api-contracts/scripts/
  generate_venue_work_list.py` (16 rows, measured 2026-08-16; re-run the script, this count is not a constant).
  Not an extraction from another source doc — no operator-gated item mixed in, per task_template.md §3 finding Y.
status: active
nature: process
asset_group: [tradfi]
stage: [data, features, strategy, execution]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    instruments-service,
    market-tick-data-service,
    features-service,
    strategy-service,
    execution-service,
  ]
scope: [engineer]
tags: [venue-readiness, e2e-wiring, tradfi, ao-dispatch, satellite-batch]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 0.96
assigned_role: backend_engineer
effort: medium
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    unified-api-contracts/scripts/generate_venue_work_list.py,
  ]
source: >-
  Forked from `venue_e2e_wiring_2026_08_16.md`'s "Fork per-asset-group dispatch batches" P0 todo, 2026-08-16
  interactive session, per the operator-selected "per contract-step-group" decomposition.
---

# tradfi venue e2e wiring batch 1 — 2026-08-16

> **Parent**: [`/plans/active/venue_e2e_wiring_2026_08_16.md`](/plans/active/venue_e2e_wiring_2026_08_16.md) (W4).
> The contract steps this plan walks, and the hard rules it must not violate, live in the parent — not restated here.
> Row list: `unified-api-contracts/scripts/generate_venue_work_list.py --csv PATH` filtered to `asset_group=tradfi`.

## Todos

- [ ] [BACKEND] P0. **Steps 1-5 per unit — declaration through features**, across tradfi's 16 (venue, data_type)
      rows. Declared in the UAC capability record; instruments-service resolves instruments with coverage windows;
      MTDS captures every declared data type and the manifest reconciles; a live adapter exists for every batch
      adapter; the venue's data reaches the feature groups that consume it. Done-when: every row has a stated
      per-step verdict (pass/fail/unverified — never silently absent), with any gap recorded as a tracked todo per
      the P1 item below.
- [ ] [BACKEND] P0. **Steps 6-8 per unit — strategy and execution**, across the same 16 rows. A position adapter
      resolves in batch, live AND paper; the venue is declared in the archetype/slot catalogues that can legitimately
      trade it; an execution adaptor handles every `InstructionActionV2` those archetypes emit. **Expect most or all
      tradfi rows to show `archetype_consumers=NONE`** per `generate_venue_work_list.py` — the 5 confirmed
      `StrategyArchetype` members today (`ARCHETYPE_FEATURE_GROUPS`) are all DeFi yield archetypes, so this step
      cannot pass for tradfi until the archetype-declaration backlog covers a tradfi-consuming archetype; record as
      `BLOCKED-ON:archetype-declaration-backlog`, never silently skip. Done-when: same per-row verdict discipline.
- [ ] [BACKEND] P0. **Step 9 per unit — transfers**, across the same 16 rows. Every applicable `BusTransferType`
      has a working rail, instruments-service through execution-service. Done-when: same per-row verdict discipline.
- [ ] [BACKEND] P1. **Record every gap found across steps 1-9 above as its own tracked todo** in this file (or a
      dated same-AG follow-up doc if adding them here would breach the line cap) — never as prose only.
- [ ] [BACKEND] P0. **Confirm the parent plan's hard rules held across steps 1-3 above**: strategy-service never
      read MTDS directly; execution fails closed on granularity (`refuse_unservable`, never silently clamped);
      credentials gated RUNNING not BUILDING; no new service-to-service dependency was introduced. Done-when: a
      clean `quality-gates.sh` run across every repo touched by this batch.

## Progress Log
