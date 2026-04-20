---
title: Refactor G1.8 — UAC ArchetypeCapabilityV2 (gap #1)
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.8
  - codex/09-strategy/architecture-v2/uac-registry-gaps.md (gap #1)
# Wave B — single item; Wave A must merge first (1.1/1.3/1.5/1.9/1.12/1.14).
# Downstream consumers (Wave C): refactor_g1_{2,6}; (Wave D): refactor_g1_11.
---

# Refactor G1.8 — UAC ArchetypeCapabilityV2 (gap #1)

## Context

Stage 3E §1.8 ships UAC gap #1 from `codex/09-strategy/architecture-v2/uac-registry-gaps.md`: **`ArchetypeCapabilityV2`
— queryable archetype → (category, instrument) support map**. Today, each v2 archetype declares its own `valid_pairs`
(category × instrument_type) inline in the archetype module under
`strategy-service/strategy_service/engine/strategies/v2/`. Consumers (pricing engine, derivation engine, UI catalogue,
restriction-profile engine) have no contract-side way to query "what archetypes support (CeFi, Perpetual)?" without
reaching into strategy-service code. G1.8 surfaces a declarative UAC type + queryable registry that mirrors every v2
archetype's declaration, so pricing engine (G1.2 → G1.6) and derivation engine (G1.6) and service-family scope rules
(G1.11) consume one stable contract.

## Decisions locked with user (2026-04-20)

| Decision                                                                                          | Chosen                                                                                                                              | Source                                            |
| ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| Type lives in UAC internal architecture_v2                                                        | `unified_api_contracts/internal/architecture_v2/archetype_capability.py` — beside existing `strategy_availability.py`               | Kickoff §1.8 + UAC layout confirmed in pre-flight |
| Mirrored from v2 code, not independently written                                                  | Read `valid_pairs` declarations from each v2 archetype file; UAC is the query surface, strategy-service code is the source of truth | Kickoff §1.8 + stage-3e §1.8                      |
| Public import via `from unified_api_contracts.strategy_availability import ArchetypeCapabilityV2` | Follows Citadel Import Rules — deep internal paths stay internal; facade re-exports                                                 | CLAUDE.md §Citadel Import Rules                   |
| Registry is thread-safe, read-mostly, append-only on load                                         | Matches existing StrategyAvailabilityRegistry pattern                                                                               | Kickoff §1.8                                      |

## Cross-references

- **Wave A prerequisite (soft — must have merged first):** all of refactor*g1*{1,3,5,9,12,14}\_2026_04_20.
- **Wave C consumers:** refactor_g1_2_instruction_schema_validation_service,
  refactor_g1_6_derivation_engine_ship_to_strategy_service_availability
- **Wave D consumer:** refactor_g1_11_service_family_scope_rules
- **UAC gap source:** `codex/09-strategy/architecture-v2/uac-registry-gaps.md` — Gap #1 ("ArchetypeCapabilityV2 —
  queryable archetype → (category, instrument) support map")
- **Architecture-v2 README:** `codex/09-strategy/architecture-v2/README.md` — 8 families × 18 archetypes × 7 axes, 10
  cross-cutting concerns
- **V2 code (source of truth — read only):** `strategy-service/strategy_service/engine/strategies/v2/`
- **Existing UAC pattern to follow:**
  `unified-api-contracts/unified_api_contracts/internal/architecture_v2/strategy_availability.py`
- **Per-venue capability pattern:** `unified-api-contracts/unified_api_contracts/registry/capability_declarations/`

## Mandatory read-set

1. `codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.8
2. `codex/09-strategy/architecture-v2/uac-registry-gaps.md` — especially Gap #1 in full
3. `codex/09-strategy/architecture-v2/README.md` — 18 archetypes + 8 families + 7 axes
4. Every archetype declaration in `strategy-service/strategy_service/engine/strategies/v2/`:
   - `strategy-service/strategy_service/engine/strategies/v2/ml_directional/`
   - `strategy-service/strategy_service/engine/strategies/v2/rules_directional/`
   - `strategy-service/strategy_service/engine/strategies/v2/stat_arb_pairs/`
   - `strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/`
   - `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/`
   - `strategy-service/strategy_service/engine/strategies/v2/event_driven/`
   - `strategy-service/strategy_service/engine/strategies/v2/market_making/`
   - `strategy-service/strategy_service/engine/strategies/v2/vol_trading/`
   - `strategy-service/strategy_service/engine/strategies/v2/target_universe/`
   - `strategy-service/strategy_service/engine/strategies/v2/registry.py`, `factory.py`, `base.py`, `slot_label.py`,
     `archetype_defaults.py`
5. `unified-api-contracts/unified_api_contracts/internal/architecture_v2/strategy_availability.py` — pattern to follow
6. `unified-api-contracts/unified_api_contracts/registry/capability_declarations/` — the per-venue pattern for sanity
   check

## Out of scope

- Rewriting archetype `valid_pairs` declarations in strategy-service — strategy-service code stays source of truth.
- Shipping the `access_control` / `cost` / `demo_universe` / `prod_restrictions` formulas that consume this capability —
  that's refactor_g1_6.
- Adding new archetypes — scope is to mirror the existing 18.
- Adding new families or axes — mirror only.
- Deleting or modifying `_archived_pre_v2/` paths — read nothing from there.

## Phase breakdown

### Phase 8A — Audit v2 archetype declarations

- [ ] [AGENT] P0. For each of the 18 v2 archetypes (enumerate from
      `strategy-service/strategy_service/engine/strategies/v2/`), extract the `valid_pairs` declaration (or equivalent
      capability-shaping field).
- [ ] [AGENT] P0. Build a table: archetype_id → family → supported (category, instrument_type) pairs → supported venues
      → axis defaults.
- [ ] [AGENT] P0. Write the table to `/tmp/g1_8_archetype_capability_audit.md` for reference.

### Phase 8B — Design the UAC type

- [ ] [AGENT] P0. Define `ArchetypeCapabilityV2` as a frozen dataclass (or `BaseModel`) matching the existing
      strategy_availability.py pattern:
  - `archetype_id: str`
  - `family: ArchetypeFamily`
  - `supported_pairs: frozenset[tuple[Category, InstrumentType]]`
  - `supported_venues: frozenset[VenueId]`
  - `axis_defaults: Mapping[Axis, Any]`
  - (+ any additional fields surfaced in audit)
- [ ] [AGENT] P0. Define `ArchetypeCapabilityRegistry` as a thread-safe, read-mostly registry with
      `get(archetype_id) -> ArchetypeCapabilityV2` + `all() -> Sequence[ArchetypeCapabilityV2]` +
      `for_pair(category, instrument) -> Sequence[ArchetypeCapabilityV2]` +
      `for_venue(venue) -> Sequence[ArchetypeCapabilityV2]`.
- [ ] [AGENT] P0. Loader loads from a generated manifest (JSON/YAML under
      `unified_api_contracts/internal/architecture_v2/`) that's emitted by a one-shot script that reads v2 archetype
      declarations; manifest is committed and checked for drift.

### Phase 8C — Implement + wire facade

- [ ] [AGENT] P0. Create `unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py`
      with the type + registry + loader.
- [ ] [AGENT] P0. Re-export from the strategy_availability facade:
      `unified-api-contracts/unified_api_contracts/strategy_availability.py` (or wherever the public facade lives;
      confirm in Phase 8A) adds
      `from .internal.architecture_v2.archetype_capability import ArchetypeCapabilityV2, ArchetypeCapabilityRegistry`.
- [ ] [AGENT] P0. Add one-shot generator script at
      `unified-api-contracts/scripts/generate_archetype_capability_manifest.py` that reads v2 code and emits the
      JSON/YAML manifest.
- [ ] [AGENT] P0. Commit the generated manifest.

### Phase 8D — Drift-detection + QG

- [ ] [AGENT] P0. Add a UAC test that re-runs the generator in-process, compares to the committed manifest, and fails on
      drift. Lives at `unified-api-contracts/tests/internal/unit/test_archetype_capability_manifest_parity.py`.
- [ ] [SCRIPT] P0. UAC quality-gates green (`cd unified-api-contracts && bash scripts/quality-gates.sh`).

## Critical files to be modified

- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py` — NEW
- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json` (or .yaml) —
  GENERATED + COMMITTED
- `unified-api-contracts/unified_api_contracts/strategy_availability.py` (or facade equivalent) — MODIFY (re-export)
- `unified-api-contracts/scripts/generate_archetype_capability_manifest.py` — NEW
- `unified-api-contracts/tests/internal/unit/test_archetype_capability_manifest_parity.py` — NEW
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-8-uac-archetype-capability.spec.ts` — NEW
  (smoke-level)

## Execution DAG

```
8A (audit)  →  8B (design)  →  8C (implement + manifest)  →  8D (drift test + QG)
```

Strictly sequential — cannot design without audit, cannot implement without design, cannot drift-test without
implementation.

## Verification

1. `rg "valid_pairs" strategy-service/strategy_service/engine/strategies/v2/` — count equals audit row count.
2. `from unified_api_contracts.strategy_availability import ArchetypeCapabilityV2, ArchetypeCapabilityRegistry`
   succeeds.
3. `ArchetypeCapabilityRegistry().all()` returns 18 entries.
4. `ArchetypeCapabilityRegistry().for_pair("CeFi", "Perpetual")` returns the expected subset (spot-check 3 entries
   against audit).
5. Drift-detection test passes on first run.
6. UAC QG green.

## Handoff

Unblocks:

- **G1.2 instruction-schema validation service** — can query UAC for "does this archetype support this (category,
  instrument)?" before validating client instructions.
- **G1.6 derivation engine** — `cost` / `demo_universe` / `prod_restrictions` / `access_control` formulas all consume
  `ArchetypeCapabilityRegistry`.
- **G1.11 service-family scope rules** — the `observe ∈ {DART}` / `reporting ∈ {IM, DART-reporting-only, Reg Umbrella}`
  constraints apply per archetype × service-family; G1.11's rule consumes this registry.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** This is a UAC contract change; no UI directly exercises it in G1.8. However, the UI
catalogue (strategy-catalogue routes) consumes strategy_availability for visibility today and will consume
ArchetypeCapabilityV2 in G1.6. MCP Playwright in dev: drive `localhost:3000/services/strategy-catalogue` and verify the
matrix page still renders post-UAC change (no import regression).

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-8-uac-archetype-capability.spec.ts` — must:

1. Seed an `admin` persona via `tests/e2e/playbooks/seed-persona.ts`.
2. Navigate to `/services/strategy-catalogue/` and verify the catalogue renders 18 archetypes (no regression from the
   UAC change).
3. (Optional future hook) when G1.6 lands, extend this spec to verify `for_pair()` queries from the UI map to visible
   tiles.
4. Assert visibility-slicing vs G1.6 `access_control` formula once G1.6 lands; admin sees all so stub until then.
5. Include orphan-reachability assertion — every archetype shown in the catalogue has a reachable detail route.
6. Wired into `scripts/quality-gates.sh` Playwright step.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G1.8 (Wave B, single item; Wave A
must be merged first).**

---

You are executing **Refactor G1.8 — UAC ArchetypeCapabilityV2** for the Unified Trading System at Odum Research. Wave B
— this is the bridge between the UI-only Wave A work and the formula-heavy Wave C derivation engine + instruction
validation. Wave A must be merged before you start (for clean rebase), and Wave C depends on this landing.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-api-contracts checkout live-defi-rollout && git -C unified-api-contracts pull
git -C strategy-service checkout live-defi-rollout && git -C strategy-service pull
ls unified-trading-pm/codex/09-strategy/architecture-v2/uac-registry-gaps.md
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/strategy_availability.py
ls strategy-service/strategy_service/engine/strategies/v2/
# Verify Wave A has merged (spot-check any one)
ls unified-trading-pm/plans/active/refactor_g1_1_phase_unification_2026_04_20.plan.md
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 8A through 8D of this plan:
`plans/active/refactor_g1_8_uac_archetype_capability_v2_2026_04_20.plan.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 6 sections, especially every file under
`strategy-service/strategy_service/engine/strategies/v2/` (18 archetype declarations).

### Deliverables

- New: `unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py`
- New: `unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json`
- Modified: `unified-api-contracts/unified_api_contracts/strategy_availability.py` (facade re-export)
- New: `unified-api-contracts/scripts/generate_archetype_capability_manifest.py`
- New: `unified-api-contracts/tests/internal/unit/test_archetype_capability_manifest_parity.py`
- New: `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-8-uac-archetype-capability.spec.ts`

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000/services/strategy-catalogue` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0
static) through MCP Playwright tools during dev to verify the strategy-catalogue matrix page still renders 18 archetypes
post-UAC change (no import regression). Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-8-uac-archetype-capability.spec.ts` — seed admin
persona via `tests/e2e/playbooks/seed-persona.ts`, walk the canonical click-path, assert 18 archetype tiles visible,
assert visibility-slicing stub (G1.6 lookup deferred), include orphan-reachability assertion, wire into
`scripts/quality-gates.sh`.

### Commit strategy

Three repos touched → three commits.

UAC repo:

```
cd unified-api-contracts
bash scripts/quickmerge.sh "feat(uac): G1.8 — ArchetypeCapabilityV2 registry + generator + manifest" --agent
```

UI repo (Playwright spec only):

```
cd unified-trading-system-ui
bash scripts/quickmerge.sh "test(playbooks): G1.8 — UAC ArchetypeCapabilityV2 smoke spec" --agent --files "tests/e2e/playbooks/refactor/refactor-g1-8-uac-archetype-capability.spec.ts"
```

Strategy-service: NO CHANGES (read-only — source of truth).

Fallback if quickmerge blocked: manual `git add <files> && git commit -m "..." && git push origin live-defi-rollout`.
Never `--dep-branch`, never `git reset --hard`.

### Success criteria

1. ✅ `ArchetypeCapabilityRegistry().all()` returns exactly 18 entries.
2. ✅ Drift-detection test passes — UAC manifest matches regenerated-from-v2 output.
3. ✅ UAC QG green.
4. ✅ UI Playwright spec green on tier-1 dev.
5. ✅ 2 commit SHAs pushed to `origin/live-defi-rollout` (UAC + UI).

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT modify any file under `strategy-service/strategy_service/engine/strategies/v2/` — source of truth is read-only.
- Do NOT invent archetype entries — mirror exactly what v2 declares.
- Do NOT ship the cost/demo-universe/access-control formulas — those are G1.6's scope.
- Do NOT add new archetypes or families or axes — mirror only.

### Report back

- Audit table: 18 rows (archetype_id, family, supported_pairs count, supported_venues count).
- Generator script path + committed manifest path + line count.
- Drift-test result.
- UAC QG result.
- Playwright spec path + pass status.
- 2 commit SHAs (UAC + UI) pushed to live-defi-rollout.
- Any gaps or open questions for the user.
