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
    /plans/archive/2026_08/redemption_wallet_transfer_execution_2026_08_20.md,
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

- [x] [BACKEND] P0. Add `vehicle_type: Literal["fund", "sma"]` (required — no default, must loud-fail if unset) to the
  canonical per-client config — ✅ unified-api-contracts@60237ba19d. **Deviation from the literal instruction,
  documented per this todo's own escape hatch**: neither of the two named `ClientConfig` types was actually the right
  home. `unified_api_contracts/internal/reporting/client_config.py`'s `ClientConfig` `TypedDict` is
  tranche-router-scoped (a different concern). The suggested preference,
  `unified_api_contracts/internal/domain/strategy_service/client_config.py`'s `ClientConfigRegistry`/
  `ClientStrategyOverride`, is keyed per-**(client_id, strategy_id)** and `overrides` starts `[]` by default — it
  cannot guarantee exactly one declared `vehicle_type` per client_id (a client with zero strategy overrides would have
  none at all), which breaks "required, must loud-fail if unset" at the registry level, not just the field level.
  Investigation found a THIRD, better-fitting home the plan didn't name:
  `unified_api_contracts/internal/domain/strategy_service/client_registry.py`'s `ClientDefinition`/`CLIENT_REGISTRY` —
  already the genuine 1:1-per-client_id SSOT (used by RecordEnricher + API gateway for identity resolution), with the
  plan's own example client_ids (`acme-fund`) already seeded there. Added `vehicle_type` as a required
  (no-default) field on the frozen `ClientDefinition` dataclass — omitting it raises `TypeError` at construction time
  (Python's own dataclass enforcement), not a silent default. **Flag for todo 3's implementer**: fund-administration-
  service must look up `vehicle_type` via `CLIENT_REGISTRY.get(client_id)` from `client_registry.py`, NOT from
  `client_config.py` as todo 3's text below currently says. Evidence: quality-gates.sh passed (272s); new tests in
  `tests/internal/unit/domain/strategy_service/test_client_registry.py`
  (`test_vehicle_type_round_trips`, `test_vehicle_type_unset_raises_not_silently_defaults`).

- [x] [BACKEND] P0. Backfill `vehicle_type: "fund"` for every EXISTING client_id in the registry chosen above — ✅
  unified-api-contracts@60237ba19d (same commit as todo 1 — inseparable for this data model: `ClientDefinition` is a
  literal Python dataclass with hardcoded `_DEFAULT_CLIENTS` instances, so adding a required field without a default
  demands every existing instantiation supply it in the SAME change or the module fails to import). All 5 seeded
  entries (`odum-paper`, `odum-live`, `patrick-elysium`, `acme-fund`, `internal-prop`) backfilled `vehicle_type="fund"`
  per this todo's own rationale. Done-when satisfied two ways: Python's own required-field enforcement (stronger than
  "a script" — the module cannot even import with a missing value) + an explicit test,
  `test_every_seeded_client_has_an_explicit_vehicle_type` (iterates `CLIENT_REGISTRY.get_all_active()`), plus
  `test_default_clients_are_backfilled_fund` pinning the exact backfilled value per client_id.

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
- **2026-08-20**: [interactive session, `.tabs/5`] Items 1+2 (add `vehicle_type` field + backfill) shipped together —
  unified-api-contracts@60237ba19d, verified ancestor of origin/live-defi-rollout. Neither `ClientConfig` type the
  plan named was the right fit (see item 1's own evidence line for the full reasoning); landed on a third existing
  home, `client_registry.py`'s `ClientDefinition`/`CLIENT_REGISTRY`, which is genuinely 1:1-per-client_id. Items 1
  and 2 merged into one commit because they're mechanically inseparable for a Python dataclass with hardcoded default
  instances — a required field with no default cannot land without every existing instance supplying it in the same
  change. QG green (272s). Item 3 (routing gate) and item 4 ([REVIEW]) remain open — item 3's implementer should read
  item 1's flag about which module to import from.
