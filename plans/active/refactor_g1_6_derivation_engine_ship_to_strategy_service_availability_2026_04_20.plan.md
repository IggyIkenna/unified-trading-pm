---
title: Refactor G1.6 — Derivation engine → strategy-service availability
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.6
  - codex/14-playbooks/infra-spec/stage-3c-derivation-engine.md
  - codex/09-strategy/architecture-v2/uac-registry-gaps.md (gaps #1, #11, #12)
  - refactor_g1_8_uac_archetype_capability_v2_2026_04_20.plan.md
# Wave C — parallel with refactor_g1_2. Downstream (Wave D): refactor_g1_{7,11}.
---

# Refactor G1.6 — Derivation engine → strategy-service availability

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

- **Upstream (Wave B):** `refactor_g1_8_uac_archetype_capability_v2_2026_04_20.plan.md` — hard dep
- **Sibling Wave C:** `refactor_g1_2_instruction_schema_validation_service_2026_04_20.plan.md` — produces
  `integration_depth` signal consumed by `cost`
- **Wave A prerequisite:** `refactor_g1_1_phase_unification_2026_04_20.plan.md` — `phase` prop threaded through UI;
  `access_control` consumes it
- **Downstream Wave D:** `refactor_g1_7_restriction_profile_engine_2026_04_20.plan.md` (consumer),
  `refactor_g1_11_service_family_scope_rules_2026_04_20.plan.md` (consumer)
- **Stage 3C infra spec:** `codex/14-playbooks/infra-spec/stage-3c-derivation-engine.md` — the 4 formulas
- **UAC gaps:** `codex/09-strategy/architecture-v2/uac-registry-gaps.md` #1, #11, #12
- **Strategy v2 code (read-only):** `strategy-service/strategy_service/engine/strategies/v2/` — for `valid_pairs`
  reference and `archetype_build_registry.py`

## Mandatory read-set

1. `codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.6
2. `codex/14-playbooks/infra-spec/stage-3c-derivation-engine.md` — full, especially the 4 formula definitions
3. `codex/09-strategy/architecture-v2/uac-registry-gaps.md` — gaps #1, #11, #12 in full
4. `codex/09-strategy/architecture-v2/README.md` — 8 families × 18 archetypes
5. `codex/09-strategy/architecture-v2/category-instrument-coverage.md` — master matrix + 10 block-list groups
6. `codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md`
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

- [ ] [AGENT] P0. Read `strategy-service/strategy_service/availability/{store,watchdog,__init__}.py` in full. Note
      extension points: what's exported; what's not.
- [ ] [AGENT] P0. Read `stage-3c-derivation-engine.md` and map each of the 4 formulas to existing store data + new
      inputs.

### Phase 6B — Implement `derivation.py`

- [ ] [AGENT] P0. Create `strategy-service/strategy_service/availability/derivation.py` with these signatures:

  ```python
  def cost(combo: Combo, tier: PricingTier, integration_depth: float = 0.0) -> Price: ...
  def demo_universe(persona: Persona, flavour: DemoFlavour) -> frozenset[ArchetypeSlot]: ...
  def prod_restrictions(client: ClientId, package: PackageId) -> RestrictionProfile: ...
  def access_control(user: UserContext, route: str, item: ItemRef, phase: Phase) -> AccessDecision: ...
  ```

- [ ] [AGENT] P0. Each function pure — no global state, no I/O. Reads come from `ArchetypeCapabilityRegistry()` (G1.8) +
      `StrategyAvailabilityRegistry()` (existing Phase-10.5) + injected readonly views.
- [ ] [AGENT] P0. Implement per `stage-3c-derivation-engine.md` exactly — do not invent formulas; cite spec line for
      each branch.

### Phase 6C — Unit tests (≥ 3 worked examples per formula, matching Stage 3C success criterion)

- [ ] [AGENT] P0. `strategy-service/tests/availability/test_derivation.py` — ≥ 12 cases (3 × 4 formulas) with worked
      examples that exercise the 10 block-list groups.
- [ ] [AGENT] P0. `cost` examples cover: low integration_depth penalty; high integration_depth discount; tier-A
      cost-plus; tier-B fixed-upfront-plus-monthly.
- [ ] [AGENT] P0. `demo_universe` examples cover: prospect-im persona × "sales-pitch" flavour; admin persona × any
      flavour (full universe); client-exclusive persona (only their own slots).
- [ ] [AGENT] P0. `prod_restrictions` examples cover: IM-Reserved × SaaS-package (empty — package doesn't include IM
      slots); Reg-Umbrella client × standard package; admin × any package.
- [ ] [AGENT] P0. `access_control` examples cover: `phase = "research"` + read route → OK; `phase = "live"` + write
      route without live entitlement → DENY; `phase` axis orthogonal to maturity axis.

### Phase 6D — Wire UTL events for allocator gate + service integration

- [ ] [AGENT] P0. Wire `access_control` denial-emit into the existing `ClientAllocatorInstance` gate (shipped Phase
      10.5). Replace fallback with `access_control()` call.
- [ ] [AGENT] P0. Expose public API:
      `from strategy_service.availability import cost, demo_universe, prod_restrictions, access_control`.
- [ ] [AGENT] P0. Re-export from UAC facade — `unified_api_contracts.strategy_availability` gains a passthrough import
      for the 4 functions so non-strategy-service consumers can import from UAC.

### Phase 6E — Verify + QG

- [ ] [SCRIPT] P0. strategy-service QG green.
- [ ] [SCRIPT] P0. UAC QG green.
- [ ] [AGENT] P0. Playwright spec `refactor-g1-6-derivation-engine.spec.ts` green on tier-1 dev.

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
`plans/active/refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md`

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
