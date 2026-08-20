---
doc_type: plan
title: Client Vehicle Type (SMA vs Pooled Fund) — Gate Fund-Administration Redemptions
summary:
  Resolved 2026-08-20 (operator Q&A, interactive session) — vehicle eligibility collapses to a plain per-client_id
  field, not a per-archetype capability matrix — each client_id maps to exactly ONE vehicle (strict 1:1), a client
  needing both gets two distinct client_ids (e.g. "acme-fund"/"acme-sma", reusing the existing per-client-isolation
  model with zero new identity machinery), and eligibility is a soft per-client business choice, not a hard
  per-archetype constraint. Adds a `vehicle_type` field to the canonical client config and gates
  fund-administration-service's redemption-creation endpoint on it — an SMA-typed client never creates an
  AllocatorRedemption; that vehicle's withdrawals are a direct execution-service concern, out of scope here.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy]
repos: [strategy-service, fund-administration-service, unified-api-contracts]
scope: [engineer]
tags: [strategy-agnostic, vehicle-eligibility, sma, fund-administration, client-config]
related:
  [
    /plans/archive/2026_08/fund_administration_redemption_cadence_engine_2026_08_20.md,
    /plans/active/redemption_wallet_transfer_execution_2026_08_20.md,
    /plans/epics/strategy_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
depends_on: [fund_administration_redemption_cadence_engine_2026_08_20]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: operator conversation relay (Greg/Patrick SMA-redemption chat) + interactive Q&A, session slot 5, 2026-08-20
context_scope:
  [
    strategy-service/strategy_service/client_context.py,
    unified-api-contracts/unified_api_contracts/internal/reporting/client_config.py,
    unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/client_config.py,
    fund-administration-service/fund_administration_service/api/main.py,
    fund-administration-service/fund_administration_service/redemption/state_machine.py,
    /plans/archive/2026_08/fund_administration_redemption_cadence_engine_2026_08_20.md,
  ]
---

# Client Vehicle Type (SMA vs Pooled Fund) — Gate Fund-Administration Redemptions

**Why this doc exists**: originally authored as a LOCAL design doc capturing an open product question — whether a
client's investment vehicle (SMA vs pooled fund) is a function of the client alone, the archetype alone, or both. The
three blocking questions were resolved interactively with the operator the same day (see Resolved decisions below),
which collapsed the design from a 2-axis (client × archetype) capability-matrix problem down to a 1-axis (client
alone) field — so this is now a small, bounded implementation plan, not a design doc.

**Resolved decisions (2026-08-20, operator Q&A, interactive session slot 5 — do not re-litigate)**:

1. **Mapping is strict 1:1** — each `(client, archetype)` relationship runs under exactly one vehicle.
2. **Eligibility is a SOFT per-client business choice**, not a hard per-archetype constraint — no archetype is
   structurally blocked from either vehicle. Consequence: no `ARCHETYPE_CAPABILITY_REGISTRY` axis is needed for this;
   that was the original design doc's proposed shape and is now explicitly out of scope.
3. **A client holding both vehicles gets two distinct `client_id`s** (e.g. `acme-fund` / `acme-sma`), reusing the
   existing per-client-isolation model with zero new identity machinery.

Combined, (1)+(3) mean every `client_id` maps to exactly one vehicle for ALL archetypes it runs — `vehicle_type`
is a plain field on the client's own config, not a per-relationship or per-archetype matrix.

**Why `gate_on_depends: true` on `fund_administration_redemption_cadence_engine_2026_08_20`**: todo 3 below edits the
same file (`fund_administration_service/api/main.py`) that plan's DI-wiring todo edits — gating avoids a genuine
cross-plan same-file collision rather than relying on `sequential: true` alone (which only orders within THIS plan).

## Todos

- [ ] [BACKEND] P0. Add `vehicle_type: Literal["fund", "sma"]` (required — no default, must loud-fail if unset) to the
  canonical per-client config. Two `ClientConfig` types currently exist in UAC:
  `unified_api_contracts/internal/reporting/client_config.py` (`TypedDict`, consumed by
  `client-reporting-api/client_reporting_api/core/tranche_router.py`'s registry) and
  `unified_api_contracts/internal/domain/strategy_service/client_config.py`'s `ClientConfigRegistry` (`BaseModel`,
  the closer relative of `clients.yaml`/`ClientRuntimeContext`). Prefer the strategy_service one — `vehicle_type` is a
  property of the same relationship `ClientRuntimeContext` already binds — unless investigation shows
  fund-administration-service (Tier-4, no service-to-service imports) needs its own independent copy, in which case
  state that finding explicitly rather than silently picking one. Done-when: the field round-trips through the chosen
  model and an unset value raises, not silently defaults.

- [ ] [BACKEND] P0. Backfill `vehicle_type: "fund"` for every EXISTING client_id in the registry chosen above — every
  current client predates this field and is, by construction, running the only path that existed (pooled fund).
  Done-when: every client_id in the live registry has an explicit `vehicle_type`, zero blanks, verified by a script
  that fails loudly on any missing value.

- [ ] [BACKEND] P0. Add the routing gate at fund-administration-service's redemption-creation endpoint
  (`fund_administration_service/api/main.py`, the handler that calls `create_redemption()` from
  `fund_administration_service/redemption/state_machine.py`) — look up the requesting client's `vehicle_type` from
  the config chosen in todo 1; an `sma`-typed client_id is rejected at this endpoint (a clear 4xx, not a silent
  accept) — that vehicle never creates an `AllocatorRedemption`, its withdrawals are a direct execution-service
  concern entirely outside fund-administration-service, out of this plan's scope. `fund`-typed clients proceed exactly
  as today. Done-when: a test posting a redemption request for an `sma`-typed client_id gets a clear rejection, and a
  `fund`-typed client_id's request is unaffected (existing `tests/unit/test_api_end_to_end.py` stays green).

- [ ] [REVIEW] P1. Confirm no regression: run `bash scripts/quality-gates.sh` in both the UAC/strategy-service config
  repo and fund-administration-service after the above land, and cite the green runs.

## Progress Log

- **2026-08-20**: Doc authored as a LOCAL design doc (`assigned_vm: NA`) with 3 blocking `[OPERATOR]` questions.
  Resolved the same session via interactive Q&A — flipped to `assigned_vm: planning` and rewritten as a bounded
  4-todo implementation plan against the resolved (client-alone, soft, two-client-ids) design.
