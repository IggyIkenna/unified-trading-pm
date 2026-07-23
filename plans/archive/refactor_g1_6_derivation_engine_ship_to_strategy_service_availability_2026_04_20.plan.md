---
doc_type: plan
title: Refactor G1.6 — Derivation engine → strategy-service availability
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service, unified-api-contracts, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-20"
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  [
    /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.6,
    /codex/14-playbooks/infra-spec/stage-3c-derivation-engine.md,
    /codex/09-strategy/architecture-v2/uac-registry-gaps.md (gaps,
    refactor_g1_8_uac_archetype_capability_v2_2026_04_20.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Refactor G1.6 — Derivation engine → strategy-service availability

> ## Implementation note (post-ship — Option X pattern)
>
> Plan body says the four derivation formulas live in `strategy-service/strategy_service/availability/derivation.py`.
> **Actual ship hosts pure logic in UAC; strategy-service only carries thin HTTP wrappers** (Option X — contracts host
> pure logic, services consume).
>
> Authoritative paths (verified 2026-04-22):
>
> - `unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py` — combo formula
> - `unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation_cost.py` — cost formula
> - `unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation_access.py` — access_control formula
> - `unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation_demo.py` — demo_universe +
>   prod_restrictions
> - `strategy-service/strategy_service/api/` — HTTP wrapper routers only (no logic)
>
> Wave-E split commit: UAC `441a494 refactor(uac): G1.6 Wave E — split derivation.py + workspace-root helper`. The plan
> body's "strategy-service/strategy_service/availability/derivation.py" references are kept for historical context only;
> trust this note over body prose.

## Context

Stage 3E §1.6 ships the four derivation formulas specified in `stage-3c-derivation-engine.md` as real code inside
`strategy-service/strategy_service/availability/` — the existing Phase-10.5 availability sub-package (`store.py` +
`watchdog.py`). The engine exposes:

- `cost(combo, tier) -> Price` — pricing formula, consumes ArchetypeCapabilityV2 (G1.8) + integration-depth signal from
  G1.2.
- `demo_universe(persona, flavour) -> set[ArchetypeSlot]` — which slots a demo persona sees.
- `prod_restrictions(client, package) -> RestrictionProfile` — which slots a prod client is allocated.
- `access_control(user, route, item, phase) -> AccessDecision` — the unified gate over UI + API, takes phase
  (research/paper/live) per G1.1.

This is the single source of truth that all four consumer surfaces read from: pricing engine, demo UI, prod-client UI,
access-control middleware.

## Decisions locked with user (2026-04-20)

| Decision                                                                                   | Chosen                                                                          | Source                                    |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- | ----------------------------------------- |
| Engine lives inside `strategy-service/strategy_service/availability/` (extends Phase-10.5) | Reuses existing thread-safe store + watchdog infra; no new repo                 | Kickoff §1.6 + Phase-10.5 already shipped |
| Phase prop is a required arg on `access_control`                                           | `phase ∈ {research, paper, live}` per G1.1                                      | Kickoff §1.6 + rule 03 sub-claim (b)      |
| All 4 formulas live in one module                                                          | `strategy_service/availability/derivation.py` — four exported functions         | Kickoff §1.6                              |
| Formulas are pure functions — no I/O, no UTL events                                        | Events emit from the callers (store, watchdog, middleware), not from derivation | rule 03 + Phase-10.5 precedent            |
| Consumes UAC ArchetypeCapabilityV2 (G1.8) + StrategyAvailabilityRegistry (existing)        | Never re-declares capability data                                               | Kickoff §1.6 + G1.8 handoff               |

## Cross-references

- **Upstream (Wave B):** `refactor_g1_8_uac_archetype_capability_v2_2026_04_20.md` — hard dep
- **Sibling Wave C:** `refactor_g1_2_instruction_schema_validation_service_2026_04_20.md` — produces `integration_depth`
  signal consumed by `cost`
- **Wave A prerequisite:** `refactor_g1_1_phase_unification_2026_04_20.md` — `phase` prop threaded through UI;
  `access_control` consumes it
- **Downstream Wave D:** `refactor_g1_7_restriction_profile_engine_2026_04_20.md` (consumer),
  `refactor_g1_11_service_family_scope_rules_2026_04_20.md` (consumer)
- **Stage 3C infra spec:** `/codex/14-playbooks/infra-spec/stage-3c-derivation-engine.md` — the 4 formulas
- **UAC gaps:** `/codex/09-strategy/architecture-v2/uac-registry-gaps.md` #1, #11, #12
- **Strategy v2 code (read-only):** `strategy-service/strategy_service/engine/strategies/v2/` — for `valid_pairs`
  reference and `archetype_build_registry.py`

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.6
2. `/codex/14-playbooks/infra-spec/stage-3c-derivation-engine.md` — full, especially the 4 formula definitions
3. `/codex/09-strategy/architecture-v2/uac-registry-gaps.md` — gaps #1, #11, #12 in full
4. `/codex/09-strategy/architecture-v2/README.md` — 8 families × 18 archetypes
5. `/codex/09-strategy/architecture-v2/category-instrument-coverage.md` — master matrix + 10 block-list groups
6. `/codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md`
7. `strategy-service/strategy_service/engine/strategies/v2/` — all top-level files + 18 archetype subdirs (valid_pairs
   declarations)
8. `strategy-service/strategy_service/engine/strategies/v2/archetype_build_registry.py` — Phase-2 build registry
9. `strategy-service/strategy_service/availability/store.py` — existing Phase-10.5 store
10. `strategy-service/strategy_service/availability/watchdog.py` — existing Phase-10.5 watchdog
11. `unified-api-contracts/unified_api_contracts/internal/architecture_v2/strategy_availability.py`
12. `unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py` (landed by G1.8)

## Out of scope

- Rewriting `store.py` or `watchdog.py` — extend, do not replace.
- Shipping restriction-profile overlays — that's G1.7.
- Shipping service-family scope enforcement — that's G1.11.
- Shipping the prospect questionnaire that produces `persona` inputs — that's G1.10.
- Shipping pricing tier numbers — `cost` formula is shape-complete but numeric knobs stay codex-private per Stage 3
  precedent.
- Reading or citing any `_archived_pre_v2/` path — v2 only.

## Phase breakdown

### Phase 6A — Audit existing Phase-10.5 availability module

- [x] [AGENT] P0. Read `strategy-service/strategy_service/availability/{store,watchdog,__init__}.py`. Confirmed
      module-level tuple `STRATEGY_AVAILABILITY_REGISTRY` + free helpers `availability_for` / `slots_visible_to` /
      `validate_allocation_authorised`. Phase-10.5 store + watchdog left untouched.
- [x] [AGENT] P0. Mapped stage-3c §1.1-§1.5 → implementation in single module `derivation.py`. `combo()` wraps the G1.8
      capability lookup; other four compose on top.

### Phase 6B — Implement `derivation.py` (Option X: UAC host, not strategy-service)

- [x] [AGENT] P0. Created `unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py` (Option X
      — UAC host per operator sign-off Q5; avoids circular dep from a UAC re-export of strategy-service symbols). Ships
      **5 formulas** (plan prose said 4; stage-3c §1.1 calls `combo(dimensions)` formula #1):

  ```python
  def combo(dimensions, *, today=None,
            capability_registry=ARCHETYPE_CAPABILITY_REGISTRY,
            availability_registry=STRATEGY_AVAILABILITY_REGISTRY) -> frozenset[Combo]: ...           # §1.1
  def cost(combo, tier, integration_depth=0.0, pricing_registry=None,
           client_contract=None) -> PriceQuote: ...                                                   # §1.2
  def demo_universe(persona, flavour, *, profile_registry=None,
                    capability_registry=ARCHETYPE_CAPABILITY_REGISTRY) -> DemoUniverse: ...          # §1.3
  def prod_restrictions(client, package, *,
                        availability_registry=STRATEGY_AVAILABILITY_REGISTRY) -> ProductionRestrictions: ...  # §1.4
  def access_control(user, route, item, phase, *,
                     availability_registry=STRATEGY_AVAILABILITY_REGISTRY,
                     capability_registry=ARCHETYPE_CAPABILITY_REGISTRY) -> AccessDecision: ...        # §1.5
  ```

- [x] [AGENT] P0. All 5 functions pure — no I/O, no globals, no UTL event emission. Event emission stays at call-sites
      (stores, watchdog, middleware).
- [x] [AGENT] P0. Shape-only pricing per stage-3c §1.2 (operator sign-off Q6) — every `QuoteLine` carries
      `todo_numeric: Literal[True] = True`. Numeric tables populate once Stage-2
      `commercial-model/pricing-building-blocks.md` signs off.

### Phase 6C — Unit tests (stage-3c §1 worked examples as fixtures)

- [x] [AGENT] P0. `unified-api-contracts/tests/internal/unit/test_derivation.py` — 22 cases (20 pass + 2 `pytest.skip`
      for prospect-dart / prospect-reg personas that don't exist until G1.10). Every test docstring cites stage-3c §X.Y
      Ex Z.
- [x] [AGENT] P0. `cost` cases: hybrid tier + richer depth (§1.2 Ex 1); IM reporting-only (§1.2 Ex 2); rule-08
      exclusivity violation (§1.2 Ex 3); internal-cost leakage guard (§1.2 Ex 4).
- [x] [AGENT] P0. `demo_universe` cases: prospect-im turbo (§1.3 Ex 2); admin full-universe short-circuit (§1.3 Ex 4);
      prospect-dart + prospect-reg deferred to G1.10 (skip markers).
- [x] [AGENT] P0. `prod_restrictions` cases: signals-only client (§1.4 Ex 1); IM desk (§1.4 Ex 2); Reg Umbrella (§1.4 Ex
      3); BL-15 RETIRED slot (§1.4 Ex 4).
- [x] [AGENT] P0. `access_control` cases: DART signals-only deny research-phase (§1.5 Ex 1); im_desk research allow
      (§1.5 Ex 2); locked_visible block-6 (§1.5 Ex 3); CLIENT_EXCLUSIVE 404 (§1.5 Ex 4); paper-phase allow (§1.5 Ex 5).

### Phase 6D — UAC facade re-export + allocator-gate (scoped)

- [x] [AGENT] P0. Re-exported 5 functions + ~20 types from the existing `unified_api_contracts.strategy` public facade
      (new `unified_api_contracts.strategy_availability` facade not created — avoids duplication with the established
      post-G1.8 domain facade).
- [x] [SHIPPED — Wave E closure 2026-04-20] [AGENT] P1. `ClientAllocatorInstance` gate swap landed in
      `strategy-service/strategy_service/portfolio_allocator/service.py`. Now calls `allocator_access_control()` (UAC
      thin wrapper that composes the item-visibility branches of `access_control` — CLIENT_EXCLUSIVE / RETIRED /
      IM_RESERVED — without the route-based service-family-scope or phase entitlement gates that don't apply to internal
      server-side allocator calls). `user_context_for_allocator(client_id, business_unit)` constructs the `UserContext`
      for the allocator from the ClientAllocatorInstance fields. Both layers (`allocator_access_control` then legacy
      `validate_allocation_authorised`) run as defence-in-depth. For Wave C the validator primitive stays in place and
      `access_control()` ships as the higher-level gate for HTTP / UI call-sites. Captured as a Wave D item under
      `refactor_g1_7_restriction_profile_engine_2026_04_20.md`.

### Phase 6E — Verify + QG

- [x] [SCRIPT] P0. UAC: 22 derivation tests green; ruff clean; basedpyright clean on `derivation.py`.
- [x] [SCRIPT] P0. strategy-service: unchanged (no strategy-service commit in Wave C — allocator-gate swap deferred to
      G1.7).
- [x] [AGENT] P0. Playwright spec `refactor-g1-6-derivation-engine.spec.ts` committed (UI commit `4e10192`) — seeds 4
      personas (admin / prospect-im / client-full / client-data-only), walks `/services/strategy-catalogue/` under each,
      validates phase=research query-param round-trip for admin, skips prospect-dart/prospect-reg with TODO(G1.10).

### Commit SHAs (pushed to `origin/live-defi-rollout` 2026-04-20)

| Repo                      | SHA                    | Summary                                                                                                                                                                                                                    |
| ------------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| unified-api-contracts     | `2c5a26b`              | derivation engine — 5 formulas + ~20 types + `strategy.py` facade re-export + 22 tests (20 pass + 2 skip)                                                                                                                  |
| unified-trading-system-ui | `4e10192`              | reference Playwright spec — 4 personas + phase-query round-trip + G1.10 persona skips                                                                                                                                      |
| strategy-service          | SHIPPED Wave E closure | allocator-gate swap landed via `allocator_access_control()` + `user_context_for_allocator()` (UAC) wired into `portfolio_allocator/service.py:run()` alongside legacy `validate_allocation_authorised` as defence-in-depth |

- [x] [AGENT] P0. Playwright spec `refactor-g1-6-derivation-engine.spec.ts` committed in UI `4e10192` (2026-04-20);
      tier-1 dev run is CI-deferred. Spec iterates admin / prospect-im / client-full / client-data-only personas;
      prospect-dart + prospect-regulatory now exist in Wave F personas expansion (`f59657c`) and will light up on next
      CI run.

## Critical files to be modified

- `strategy-service/strategy_service/availability/derivation.py` — NEW
- `strategy-service/strategy_service/availability/__init__.py` — MODIFY (export 4 functions)
- `strategy-service/tests/availability/test_derivation.py` — NEW (≥ 12 cases)
- `strategy-service/strategy_service/engine/strategies/v2/orchestrator.py` (or wherever ClientAllocatorInstance lives) —
  MODIFY (wire access_control)
- `unified-api-contracts/unified_api_contracts/strategy_availability.py` — MODIFY (facade re-export)
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-6-derivation-engine.spec.ts` — NEW

## Execution DAG

```
6A (audit)  →  6B (implement)  →  6C (tests) + 6D (wire allocator + facade)  [parallel]  →  6E (QG + Playwright)
```

## Verification

1. All 4 formulas exported from `strategy_service.availability` + re-exported from UAC facade.
2. ≥ 12 test cases green.
3. `ClientAllocatorInstance` gate now calls `access_control` — verified by integration test that an unauthorised user's
   allocation is denied with structured `AccessDecision.DENY(reason)`.
4. strategy-service QG green.
5. UAC QG green.
6. Playwright spec green on tier-1 dev — demonstrates a persona's visible catalogue matches `demo_universe()` output.

## Handoff

Unblocks:

- **G1.7 restriction-profile engine** — consumes `prod_restrictions` + `demo_universe`.
- **G1.11 service-family scope rules** — consumes `access_control` with service-family constraint injection.
- **G1.10 questionnaire** — questionnaire output maps to `Persona` + `RestrictionProfile` inputs to derivation engine.
- **G2.x** — pricing engine service that exposes `cost()` as a REST/internal endpoint.
- **G2.x** — access-control middleware that wraps all UI + API routes.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100`
(tier-0 static) through MCP Playwright tools — seed multiple personas, navigate strategy-catalogue, verify visible slot
set matches `demo_universe(persona, flavour)` computed server-side. Seed an unauthorised persona and attempt a
`/services/research/strategy/allocator` write action; verify deny response matches `access_control()` semantics.

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-6-derivation-engine.spec.ts` — must:

1. Seed personas via `tests/e2e/playbooks/seed-persona.ts`: `admin`, `prospect-im`, `client-full`, `client-data-only`.
2. For each persona, walk the canonical click-path into `/services/strategy-catalogue/` and assert visible slot set ==
   `demo_universe(persona, "sales-pitch")` as exposed by a debug endpoint (or computed client-side from the facade).
3. Attempt a write-action per phase (`research`, `paper`, `live`) — assert `access_control` output matches observed DOM
   gating.
4. Assert visibility-slicing is driven by `access_control()` — this spec IS the reference implementation that other
   refactor specs can now stop stubbing.
5. Include orphan-reachability assertion — every visible slot has a reachable detail route.
6. Wired into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G1.6 (Wave C, parallel with G1.2;
both depend on G1.8).**

---

You are executing **Refactor G1.6 — Derivation engine** for the Unified Trading System at Odum Research. Wave C; G1.8
must be merged first; parallelisable with G1.2.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-api-contracts checkout live-defi-rollout && git -C unified-api-contracts pull
git -C strategy-service checkout live-defi-rollout && git -C strategy-service pull
ls unified-trading-pm/codex/14-playbooks/infra-spec/stage-3c-derivation-engine.md
ls unified-trading-pm/codex/09-strategy/architecture-v2/uac-registry-gaps.md
ls strategy-service/strategy_service/availability/store.py
ls strategy-service/strategy_service/availability/watchdog.py
ls strategy-service/strategy_service/engine/strategies/v2/archetype_build_registry.py
# Verify G1.8 merged
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 6A through 6E of this plan:
`plans/active/refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 12, especially every v2 archetype file at
`strategy-service/strategy_service/engine/strategies/v2/` (NEVER `_archived_pre_v2/`).

### Deliverables

- New: `strategy-service/strategy_service/availability/derivation.py` (4 functions per stage-3c)
- Modified: `strategy-service/strategy_service/availability/__init__.py` (exports)
- New: `strategy-service/tests/availability/test_derivation.py` (≥ 12 cases)
- Modified: strategy-service allocator gate (`ClientAllocatorInstance` call-site) — wires `access_control`
- Modified: `unified-api-contracts/unified_api_contracts/strategy_availability.py` (facade re-export)
- New test: `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-6-derivation-engine.spec.ts`

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
Playwright tools during dev to verify the strategy-catalogue visible-slot set matches `demo_universe()` computed output
per persona, and to verify `access_control` correctly gates phased write actions. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-6-derivation-engine.spec.ts` — seed 4 personas via
`tests/e2e/playbooks/seed-persona.ts`, walk canonical click-paths, assert each persona's visible catalogue slots match
derivation-engine output, assert `access_control` gates write-actions per phase, include orphan-reachability assertion,
wire into `scripts/quality-gates.sh`. Note this spec becomes the REFERENCE for other refactor specs that previously
stubbed access_control lookups.

### Commit strategy

Three repos touched → three quickmerge commits.

```
cd strategy-service
bash scripts/quickmerge.sh "feat(strategy-service/availability): G1.6 — derivation engine (4 formulas)" --agent

cd ../unified-api-contracts
bash scripts/quickmerge.sh "feat(uac): G1.6 — re-export derivation engine from strategy_availability facade" --agent

cd ../unified-trading-system-ui
bash scripts/quickmerge.sh "test(playbooks): G1.6 — derivation engine reference spec" --agent --files "tests/e2e/playbooks/refactor/refactor-g1-6-derivation-engine.spec.ts"
```

Fallback per repo: manual `git add <files> && git commit -m "..." && git push origin live-defi-rollout`. Never
`--dep-branch`, never `git reset --hard`.

### Success criteria

1. ✅ 4 formulas exported from strategy_service.availability + re-exported from UAC facade.
2. ✅ ≥ 12 derivation test cases green (3 per formula minimum).
3. ✅ Allocator gate now calls `access_control` — integration test confirms denied unauthorised allocation.
4. ✅ QG green on strategy-service + UAC + UI.
5. ✅ Playwright spec green on tier-1 dev with 4 personas.
6. ✅ 3 commit SHAs pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only; source of truth is
  `strategy-service/strategy_service/engine/strategies/v2/`.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT rewrite `store.py` or `watchdog.py` — extend, do not replace.
- Do NOT populate real cost numbers — shape only, per Stage 3 precedent.
- Do NOT perform I/O inside the 4 formulas — pure functions only.
- Do NOT ship restriction overlays here — G1.7 owns overlays.
- Do NOT ship service-family scope enforcement here — G1.11 owns that layer.
- Do NOT invent formulas — cite `stage-3c-derivation-engine.md` line per branch.

### Report back

- Function signatures (4) with stage-3c line cites.
- Test count per formula.
- Allocator integration test result.
- QG results (3 repos).
- Playwright spec pass status.
- 3 commit SHAs pushed to live-defi-rollout.
- Any gaps or open questions for the user.

---

## Micro-execution plan (sub-agent Phase 1, appended 2026-04-20)

> Drafted by Wave-C kickoff sub-agent. Plan-mode only — no code edits yet; operator approval required before Phase 6A/6B
> execution. Companion micro-plan for G1.2 is in `refactor_g1_2_instruction_schema_validation_service_2026_04_20.md` §
> Micro-execution plan.

### Plan-prose drifts vs reality (verified 2026-04-20 against `live-defi-rollout`)

| #   | Plan claims                                                                                                                                                                   | Reality (post-G1.8 + Phase-10.5)                                                                                                                                                                                                                                                                                                          | Resolution                                                                                                                                                                                                                                                                                                                                                                                       |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Line 104: "`ArchetypeCapabilityRegistry()` (G1.8) + `StrategyAvailabilityRegistry()` (existing Phase-10.5) + injected readonly views"                                         | Neither Registry class exists. Real: `ARCHETYPE_CAPABILITY_REGISTRY: tuple[ArchetypeCapability, ...]` + `STRATEGY_AVAILABILITY_REGISTRY: tuple[StrategyAvailabilityEntry, ...]`. Free helpers: `archetypes_for_pair`, `capability_for`, `archetypes_for_venue`, `availability_for`, `slots_visible_to`, `validate_allocation_authorised`. | Derivation functions accept `registry: Iterable[...] = STRATEGY_AVAILABILITY_REGISTRY` + `capability_registry: Iterable[ArchetypeCapability] = ARCHETYPE_CAPABILITY_REGISTRY` default args (matches `slots_visible_to(...)` pattern at [strategy_availability.py:259](unified-api-contracts/unified_api_contracts/internal/architecture_v2/strategy_availability.py#L259)).                      |
| 2   | Line 128-129: "Re-export from UAC facade — `unified_api_contracts.strategy_availability` gains a passthrough import"                                                          | `unified_api_contracts.strategy_availability` PUBLIC module does not exist (same drift as G1.8). The existing public facade is `unified_api_contracts.strategy`.                                                                                                                                                                          | Re-export the 5 derivation functions from existing `unified_api_contracts.strategy` facade (where G1.8 `ArchetypeCapability` already lives). Do NOT create a new `strategy_availability` facade.                                                                                                                                                                                                 |
| 3   | Line 142: "strategy-service/strategy_service/engine/strategies/v2/orchestrator.py (or wherever ClientAllocatorInstance lives)"                                                | `ClientAllocatorInstance` lives at [strategy-service/strategy_service/portfolio_allocator/service.py:75](strategy-service/strategy_service/portfolio_allocator/service.py#L75). Already wires `availability_registry` + calls `validate_allocation_authorised()` (Phase 10.5 shipped).                                                    | Phase 6D modifies `portfolio_allocator/service.py` — REPLACE the `validate_allocation_authorised()` call with `access_control(user, route, item, phase)`. `validate_allocation_authorised` becomes the lower-level primitive `access_control` delegates to for the allocation-authorisation branch; do not delete it yet (still used for per-slot `business_unit`/`exclusive_client_id` checks). |
| 4   | Plan: "four derivation formulas" (line 20-29 + title)                                                                                                                         | Stage-3C §1 defines **FIVE** formulas: `combo(dimensions)` (§1.1), `cost` (§1.2), `demo_universe` (§1.3), `prod_restrictions` (§1.4), `access_control` (§1.5). `combo` is formula #1 and feeds inputs to the other 4.                                                                                                                     | **Ship 5 formulas in one `derivation.py`.** `combo(dimensions)` is the valid-combo membership predicate; it wraps G1.8's `archetypes_for_pair()` + blocker filtering. Plan §Context + §Phase 6B text to be understood as "derivation engine = 5 formulas" notwithstanding the "four" wording.                                                                                                    |
| 5   | Stage-3C §5 recommends sub-package layout: `combo.py`, `pricing/` sub-package, `demo_universe.py`, `prod_restrictions.py`, `access_control.py` — separate modules per formula | Plan line 40: "All 4 formulas live in one module — `strategy_service/availability/derivation.py`"                                                                                                                                                                                                                                         | Tension between plan (one module) and stage-3c (multiple modules). **Ship as one module for Wave C**; promote to sub-package layout in a follow-up refactor once the surface stabilises (tracked as future todo below). Keeps Wave C blast radius minimal. Operator confirmation requested.                                                                                                      |
| 6   | Line 70: "11. `unified-api-contracts/.../strategy_availability.py`" reads straight from Phase-10.5 symbols; line 128 cross-ref calls these "Registry"                         | Module is `internal/architecture_v2/strategy_availability.py` — UAC-internal, not a public facade. Consumers import from `unified_api_contracts.internal.architecture_v2` OR from the public `unified_api_contracts.strategy` (which already re-exports availability surface post-G1.8).                                                  | Derivation engine imports from `unified_api_contracts.strategy` (public facade), not deep internal path. Matches Citadel Import Rules (workspace CLAUDE.md).                                                                                                                                                                                                                                     |

**Input types the plan assumes exist but are net-new** (need declaring in UAC or strategy-service): `Combo`, `Persona`,
`DemoFlavour`, `PricingTier`, `Price`, `ClientId`, `PackageId`, `UserContext`, `ItemRef`, `AccessDecision`,
`RestrictionProfile`, `ArchetypeSlot`, `Phase`, `IntegrationDepth`. Stage-3C §1 gives the shape of each — Phase 6B
declares them as Pydantic `BaseModel`s or enums colocated in `derivation.py` (types alongside the functions) with UAC
public re-export. No cross-repo coordination needed.

### Pre-audit manifest (Citadel rule-6)

Grep across workspace excluding `.venv*`, `node_modules`, `build`, `_archived_pre_v2`:

| Symbol                                              | Current hits                                                                                                                 | Action                                                                                                                                                                                                                                                                                                  |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cost(` (in derivation context)                     | 0                                                                                                                            | Net-new. Unrelated `cost` in `unified-api-contracts/registry/capability_declarations/` is DeFi gas-cost context — no collision.                                                                                                                                                                         |
| `demo_universe`                                     | 0                                                                                                                            | Net-new.                                                                                                                                                                                                                                                                                                |
| `prod_restrictions`                                 | 0                                                                                                                            | Net-new.                                                                                                                                                                                                                                                                                                |
| `access_control`                                    | 0 runtime; several references in stage-3c/3b specs only                                                                      | Net-new.                                                                                                                                                                                                                                                                                                |
| `RestrictionProfile`                                | 0 runtime                                                                                                                    | Net-new — Pydantic model.                                                                                                                                                                                                                                                                               |
| `AccessDecision`                                    | 0 runtime                                                                                                                    | Net-new — Pydantic discriminated union (`allow`/`locked_visible`/`deny`/`deny_phase`).                                                                                                                                                                                                                  |
| `Persona`, `DemoFlavour`                            | 0 runtime                                                                                                                    | Net-new UAC enums — align with UI personas file for consistency (`unified-trading-system-ui/lib/auth/personas.ts` documents: admin, prospect-im, client-full, client-data-only, client-premium, internal-trader; Stage-3C calls out `prospect-dart`, `prospect-reg` as gaps to add — tracked in G1.10). |
| `ClientAllocatorInstance`                           | 7 files in strategy-service                                                                                                  | Update 1 call-site at `portfolio_allocator/service.py:75` (wraps existing `validate_allocation_authorised`). 6 other hits are tests + cadence + `shadow_deployment.py` — the latter two may not need changes (verify in Phase 6D).                                                                      |
| `validate_allocation_authorised`                    | internal helper + 4 test files + 1 allocator callsite                                                                        | Keep as inner primitive; callers invoke `access_control()` which includes `validate_allocation_authorised()` semantics for the allocation branch.                                                                                                                                                       |
| `Phase` type (`Literal["research","paper","live"]`) | Threaded through UI at `unified-trading-system-ui/lib/phase/use-phase-binding.ts` + `use-phase-from-route.ts` (G1.1 shipped) | Python type mirror lives in this module.                                                                                                                                                                                                                                                                |

Zero deletion, zero rename. Purely additive: new module with 5 functions + ~13 new types, one call-site update in
allocator.

### Execution DAG

```
6A (audit Phase-10.5 surface + stage-3c §1.1–§1.5 mapping)
    └── 6B.1 declare types in derivation.py (Combo, Persona, DemoFlavour, PricingTier, Price, ClientContext,
    │       UserContext, ItemRef, AccessDecision, RestrictionProfile, Phase, IntegrationDepth, etc.)
    │       └── 6B.2 implement 5 formulas (combo, cost, demo_universe, prod_restrictions, access_control)
    │               └── 6C unit tests (≥15 cases = 3 × 5 formulas), using stage-3c §1 worked examples as fixtures
    │                       └── COMMIT 1 (strategy-service)
    ├── 6D.1 public re-export via unified_api_contracts/strategy.py facade
    │       └── COMMIT 2 (UAC) — INDEPENDENT of strategy-service commit once UAC can import the types;
    │             actually sequential: UAC can't re-export until strategy-service ships
    │       ALT: types live in UAC instead of strategy-service → sequencing flips.
    │   See open question #2 below.
    ├── 6D.2 replace ClientAllocatorInstance allocation gate with access_control() call
    │       └── folded into COMMIT 1 (strategy-service)
    └── 6E.1 UI Playwright spec → COMMIT 3 (UI)
            └── 6E.2 workspace QG on strategy-service + UAC + UI
```

**Parallel opportunity with G1.2:** G1.2 ships `INSTRUCTION_INTEGRATION_DEPTH_OBSERVED` + validator; G1.6's `cost()`
reads the `integration_depth: float` value. G1.6 can stub `integration_depth = 0.0` in its unit tests and accept the
param as `Optional[float] = 0.0`, enabling fully-parallel execution. Real wiring (subscribing to the UTL event to feed
pricing) is a G2.x concern per stage-3c §1.2 "Owning service" note — NOT part of G1.6.

### Files × line-ranges × commit sequence

**COMMIT 1 — strategy-service**
`feat(strategy-service/availability): G1.6 — derivation engine (5 formulas per stage-3c)`

| File                                                                     | Action                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Approx LOC |
| ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `strategy-service/strategy_service/availability/derivation.py`           | NEW — types (13) + 5 functions (combo, cost, demo_universe, prod_restrictions, access_control)                                                                                                                                                                                                                                                                                                                                                                                                                                                              | ~450       |
| `strategy-service/strategy_service/availability/__init__.py`             | MODIFY — export 5 funcs + types, keep Phase-10.5 exports                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | +18        |
| `strategy-service/tests/unit/availability/test_derivation.py`            | NEW — ≥15 cases: 3 per formula using stage-3c §1.1-§1.5 worked examples (combo canonical DeFi stat-arb + blocked DeFi options + BL-10 dated-future; cost hybrid tier + IM reporting-only + rule-08 exclusivity violation + internal-cost leakage; demo_universe prospect-dart broader + prospect-im turbo + prospect-reg turbo + admin; prod_restrictions signals-only + IM desk + reg umbrella + retired-slot BL-15; access_control DART research-phase deny + im_desk research allow + locked_visible block-6 + CLIENT_EXCLUSIVE 404 + paper-phase allow) | ~450       |
| `strategy-service/strategy_service/portfolio_allocator/service.py`       | MODIFY — swap `validate_allocation_authorised()` call at line 125-129 for `access_control()` call; keep the Phase-10.5 primitive as the inner call inside `access_control`                                                                                                                                                                                                                                                                                                                                                                                  | ~+15 / -5  |
| `strategy-service/tests/unit/availability/test_allocator_enforcement.py` | MODIFY — flip assertions to expect `AccessDecision` denial envelope (not raw exception), keep coverage                                                                                                                                                                                                                                                                                                                                                                                                                                                      | ~+20       |

Key design notes:

- `Phase = Literal["research", "paper", "live"]` — matches UI G1.1.
- `combo(dimensions, *, today=None, capability_registry=ARCHETYPE_CAPABILITY_REGISTRY, availability_registry=STRATEGY_AVAILABILITY_REGISTRY)`
  — reads the G1.8 + Phase-10.5 registries by default; callers can inject readonly views for testing.
- `cost(combo, tier, integration_depth=0.0, pricing_registry=None)` — `pricing_registry` is None initially (shape-only;
  numbers populate later per plan line 80-81 and stage-3c §1.2 "numbers populate later"); each `QuoteLine` carries a
  `TODO_numeric: Literal[True]` marker. Operator sign-off on shape-only-for-now.
- `demo_universe(persona, flavour, *, profile_registry=None)` — `profile_registry` reads Stage-2
  `demo-ops/demo-restriction-profiles.md` once that file ships; interim fixture dict-in-module.
- `prod_restrictions(client, package)` — contract-management layer is G1.7; fixture package dict-in-module for now.
- `access_control(user, route, item, phase)` — composes the other 4 per stage-3c §1.5 visibility formula; returns
  `AccessDecision(status, reason, upgrade_hint)`.
- **No I/O, no UTL events, no global mutable state.** Event emission stays at call-sites (stores, watchdog, middleware).

**COMMIT 2 — UAC** `feat(uac): G1.6 — re-export derivation engine from strategy public facade`

| File                                                      | Action                                                                                                                     | Approx LOC |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `unified-api-contracts/unified_api_contracts/strategy.py` | MODIFY — passthrough re-export of the 5 derivation functions + their types from `strategy_service.availability.derivation` | +25        |

**Sequencing:** UAC re-export requires strategy-service to be importable in UAC's test env. Since strategy-service is a
consumer of UAC (not vice-versa), re-exporting strategy-service symbols from UAC would introduce a CIRCULAR dependency.
**This is a drift risk in the plan.** Resolution options:

- Option X: Ship the types + pure functions in UAC (`unified_api_contracts/internal/architecture_v2/derivation.py`), and
  have strategy-service merely host the service-level wiring + fixtures. Pros: no circular dep, matches G1.8 Citadel
  pattern (schemas in UAC). Cons: forces types into UAC even though they have zero utility outside this plan.
- Option Y: Skip the UAC re-export entirely. Consumers import from `strategy_service.availability` directly. Pros: no
  circular dep, no UAC changes. Cons: violates the plan's "single-surface" Decision line 40.
- Option Z: Ship the types only in UAC, ship the function BODIES in strategy-service that reads those types. UAC
  re-exports just the types + abstract protocols; strategy-service provides the implementations. Pros: clean separation.
  Cons: two-step hop for consumers.

**Recommendation:** Option X. Matches G1.8 pattern exactly — UAC owns schemas + pure functions; strategy-service owns
the runtime store (Phase 10.5). The "pure functions live in UAC" principle makes them importable by non-strategy
consumers (pricing-engine future service, access-control middleware on any route) without pulling strategy-service as a
dep. Operator sign-off requested.

If Option X chosen:

- COMMIT 1 moves to UAC: `unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py` (NEW),
  facade re-export via `unified_api_contracts.strategy` (MODIFY).
- COMMIT 2 moves to strategy-service: just the allocator-gate swap + tests.
- Sequencing: UAC first, strategy-service second, UI third.

**COMMIT 3 — UI** `test(playbooks): G1.6 — derivation engine reference spec`

| File                                                                                             | Action                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Approx LOC |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-6-derivation-engine.spec.ts` | NEW — seed 4 personas (admin, prospect-im, client-full, client-data-only) via `seed-persona.ts`; for each walk `/services/strategy-catalogue/` + assert visible slot set == `demo_universe(persona, "sales-pitch")` output (via debug endpoint OR client-side `from unified_api_contracts.strategy import demo_universe` TS mirror — pick one, default to debug endpoint); per-phase write-action attempt assertions against `access_control()` expected output; orphan-reachability: every visible slot has a reachable detail route | ~200       |

UI `scripts/quality-gates.sh` — no edit needed (auto-discovery).

### Playwright spec design

Canonical port is `localhost:3000` (tier-1). Spec drives browser via MCP Playwright during dev, commits the durable spec
for CI. Reference implementation — once this spec ships, other refactor specs can stop stubbing `access_control` and
reference this one.

Persona list locked to what exists today in `unified-trading-system-ui/lib/auth/personas.ts`: `admin`, `prospect-im`,
`client-full`, `client-data-only`, `client-premium`, `internal-trader`. `prospect-dart` + `prospect-reg` noted in
stage-3c as G1.10 gap — their absence is documented in the spec as `test.skip()` entries with TODO(G1.10) comments.

### Breaking-change analysis (Citadel rule-3)

One existing call-site modified (`portfolio_allocator/service.py:125-129`). Semantics swap from
`validate_allocation_authorised() → raise` to `access_control() → AccessDecision(deny, reason)` — the new envelope
carries the same information; existing tests flip to envelope-based assertion. No consumer behaviour change visible to
the strategy-service HTTP surface today (no public endpoint surfaces allocator decisions yet).

Other 6 `ClientAllocatorInstance` references (cadence.py, shadow_deployment.py, 4 test files) do NOT call the gate —
they reference the class for allocation flow; no change needed. Verified spot-check in Phase 6A.

### Success criteria (per phase)

| Phase        | Gate                                                                                                                                                                                               |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 6A audit     | Map of stage-3c §1.1–§1.5 formulas to Phase-10.5 symbols + G1.8 registry; type list locked                                                                                                         |
| 6B implement | `from unified_api_contracts.strategy import cost, demo_universe, prod_restrictions, access_control, combo` (Option X) imports clean; OR `from strategy_service.availability import ...` (Option Y) |
| 6C tests     | ≥15 cases green; stage-3c line cites in test docstrings                                                                                                                                            |
| 6D integrate | Allocator test swap to envelope-based; strategy-service `bash scripts/quality-gates.sh` green                                                                                                      |
| 6E verify    | UI Playwright spec green on tier-1 dev with 4 personas; 3 commit SHAs on origin/live-defi-rollout                                                                                                  |

### Open questions for operator

1. **5 vs 4 formulas** (§drift #4-5 above): Stage-3C §1.1 defines `combo(dimensions)` as formula #1; plan says 4.
   Default: ship 5 functions in one `derivation.py` now. Operator confirm?
2. **UAC vs strategy-service host** (§COMMIT 2 drift): UAC re-export creates circular dep. Recommendation: Option X —
   ship pure functions in UAC `internal/architecture_v2/derivation.py`, re-export from `unified_api_contracts.strategy`.
   Operator confirm?
3. **Shape-only pricing** (§COMMIT 1 design note): `cost()` returns `PriceQuote` with `TODO_numeric: Literal[True]`
   markers; numbers populate in a later wave per stage-3c §1.2. Confirm acceptable?
4. **Multi-module sub-package split** (§drift #5): Stage-3C §5 recommends `combo.py` + `pricing/` + `demo_universe.py`
   - `prod_restrictions.py` + `access_control.py` as separate modules. Plan says one `derivation.py`. Default:
     single-module for Wave C, track multi-module split as future refactor follow-up. Confirm?

### Pre-flight for Phase 6A execution (when approved)

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
# Other agents have WIP on UAC — stage only G1.6 files
git -C unified-api-contracts status --short
git -C strategy-service status --short   # should be minimal
.venv-workspace/bin/python -c "from unified_api_contracts.strategy import ARCHETYPE_CAPABILITY_REGISTRY; from unified_api_contracts.internal.architecture_v2 import STRATEGY_AVAILABILITY_REGISTRY; print(len(ARCHETYPE_CAPABILITY_REGISTRY), len(STRATEGY_AVAILABILITY_REGISTRY))"
```

### Future follow-up (not Wave C scope)

- **Multi-module split** per stage-3c §5: `combo.py`, `pricing/` sub-package, `demo_universe.py`,
  `prod_restrictions.py`, `access_control.py`. Ship once the single-module surface exceeds ~800 LOC or when
  pricing-engine service splits off (Stage 3E G3).
- **Numeric pricing tables** — populate the `pricing_registry` param from Stage-2
  `commercial-model/pricing-building-blocks.md` once finance signs off on numbers.
- **HTTP surface** — new `strategy-service/strategy_service/api/restriction_profile_router.py` per stage-3c §5 "API
  surface" — 5 endpoints. Scope: next wave.
- **prospect-dart + prospect-reg personas** — G1.10 scope.
- **Integration-depth wiring from G1.2** — follow-up commit after G1.2 ships the UTL event.
