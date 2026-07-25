---
doc_type: plan
title: Refactor G1.8 — UAC ArchetypeCapabilityV2 (gap
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
    /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md §1.8,
    /codex/09-strategy/architecture-v2/uac-registry-gaps.md (gap,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Refactor G1.8 — UAC ArchetypeCapabilityV2 (gap #1)

## Context

Stage 3E §1.8 ships UAC gap #1 from `/codex/09-strategy/architecture-v2/uac-registry-gaps.md`: **`ArchetypeCapabilityV2`
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
- **UAC gap source:** `/codex/09-strategy/architecture-v2/uac-registry-gaps.md` — Gap #1 ("ArchetypeCapabilityV2 —
  queryable archetype → (category, instrument) support map")
- **Architecture-v2 README:** `/codex/09-strategy/architecture-v2/README.md` — 8 families × 18 archetypes × 7 axes, 10
  cross-cutting concerns
- **V2 code (source of truth — read only):** `strategy-service/strategy_service/engine/strategies/v2/`
- **Existing UAC pattern to follow:**
  `unified-api-contracts/unified_api_contracts/internal/architecture_v2/strategy_availability.py`
- **Per-venue capability pattern:** `unified-api-contracts/unified_api_contracts/registry/capability_declarations/`

## Mandatory read-set

1. `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.8
2. `/codex/09-strategy/architecture-v2/uac-registry-gaps.md` — especially Gap #1 in full
3. `/codex/09-strategy/architecture-v2/README.md` — 18 archetypes + 8 families + 7 axes
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

- [x] [AGENT] P0. Audit surfaced that v2 archetype modules do NOT declare `valid_pairs` inline — they declare only
      `ARCHETYPE` and `FAMILY` class vars. The matrix lives in `coverage.ts` (UI) and `category-instrument-coverage.md`
      (codex narrative). SSOT flipped to option C (Python SSOT in UAC) per operator.
- [x] [AGENT] P0. Seed data for the SSOT extracted from `coverage.ts` by a one-shot builder (non-canonical, disposable)
      into `archetype_capability_manifest.json`.
- [x] [AGENT] P0. Archetype-id + family mapping captured: 18 archetypes × 8 families, matches `ARCHETYPE_TO_FAMILY` in
      `internal/architecture_v2/enums.py`.

### Phase 8B — Design the UAC type

- [x] [AGENT] P0. `ArchetypeCapability` (no V2 suffix — operator decision 2026-04-20) is a Pydantic BaseModel
      (`frozen=True, extra="forbid"`) with fields: `archetype_id: StrategyArchetypeV2`, `family: StrategyFamilyV2`,
      `uses_rolling_futures: bool`, `cells: tuple[ArchetypeCapabilityCell, ...]`. Derived properties `supported_pairs`,
      `partial_pairs`, `blocked_pairs`, `supported_venues` replace the proposed `axis_defaults` / `supported_venues` /
      `supported_pairs` fields (richer surface per coverage.ts).
- [x] [AGENT] P0. Module-level tuple `ARCHETYPE_CAPABILITY_REGISTRY` + free functions `capability_for`,
      `all_capabilities`, `archetypes_for_pair(include_partial=True|False)`, `archetypes_for_venue`. Mirrors
      `strategy_availability.py` pattern — no Lock/thread-safety needed (immutable post-load).
- [x] [AGENT] P0. JSON manifest at `unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json`
      is committed SSOT; loaded via `importlib.resources` at module init.

### Phase 8C — Implement + wire facade

- [x] [AGENT] P0. `unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py` created
      with the type, registry, loader, and 4 query helpers.
- [x] [AGENT] P0. Re-export added to existing domain facade `unified-api-contracts/unified_api_contracts/strategy.py` —
      consumers use
      `from unified_api_contracts.strategy import ArchetypeCapability, ARCHETYPE_CAPABILITY_REGISTRY, ...`. Also
      re-exported from `internal/architecture_v2/__init__.py` for internal paths.
- [x] [AGENT] P0. Serialiser/drift-checker script at
      `unified-api-contracts/scripts/generate_archetype_capability_manifest.py` (`--write` rewrites, default `--check`
      exits 1 on drift).
- [x] [AGENT] P0. Manifest committed at UAC commit `2a4fff4`.

### Phase 8D — Drift-detection + parity + QG

- [x] [AGENT] P0. UAC parity test at `tests/internal/unit/test_archetype_capability_manifest_parity.py` with 15 asserts
      covering: 18-archetype count, every `StrategyArchetypeV2` enum member represented, family mapping matches
      canonical `ARCHETYPE_TO_FAMILY`, pair-status cell coverage, BLOCKED cells carry block-list refs, SUPPORTED cells
      carry venues, `EVENT_DRIVEN` archetype/family disambiguation, manifest round-trip stability, **codex markdown
      structural parity** (section per archetype, family groupings, archetype-under-correct-family).
- [x] [SCRIPT] P0. UAC quality-gates: lint + typecheck green. Single pre-existing size violation on
      `internal/schemas/contracts.py` (+40 LOC WIP from another agent) is out-of-scope — not caused by G1.8.

### Phase 8E — PM sync script + UI QG wiring + Playwright spec

- [x] [AGENT] P0. PM sync script `unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh` (+ Python
      body `sync_archetype_capability_to_ui.py`) reads the UAC manifest and renders
      `unified-trading-system-ui/lib/architecture-v2/coverage.ts` with an AUTO-GENERATED banner. `--check` (default)
      exits 1 on drift, `--write` rewrites. Committed at PM commit `9b954c0b`.
- [x] [AGENT] P0. `unified-trading-system-ui/scripts/quality-gates.sh` updated with a pre-base-ui hook — every UI push
      hits `bash <PM>/scripts/propagation/sync-archetype-capability-to-ui.sh --check` and aborts on drift. **Explicit
      hook line**:

      ```bash
                                                                      # G1.8 — archetype-capability UAC <-> UI coverage.ts parity.
                                                                      SYNC_ARCHETYPE_CAPABILITY="${WORKSPACE_ROOT}/unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh"
                                                                      if [[ -f "$SYNC_ARCHETYPE_CAPABILITY" ]]; then
                                                                        bash "$SYNC_ARCHETYPE_CAPABILITY" --check || exit 1
                                                                      fi
                                                                      ```

- [x] [AGENT] P0. `lib/architecture-v2/coverage.ts` regenerated via `--write` — now carries the AUTO-GENERATED banner,
      matches the UAC manifest byte-for-byte.
- [x] [AGENT] P0. Playwright spec `tests/e2e/playbooks/refactor/refactor-g1-8-uac-archetype-capability.spec.ts` asserts:
      canonical paths exist, manifest has 18 archetypes, `sync --check` exits 0, AUTO-GEN banner present, every
      archetype_id in the mapping, admin persona reaches `/services/strategy-catalogue/` without redirect-off. Committed
      at UI commit `fd1895c`.

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

---

## Micro-execution plan (sub-agent Phase 1 — 2026-04-20)

Operator-approved via plan-mode exit. Full copy lives at `~/.claude/plans/cozy-shimmying-cookie.md`. Summary below for
in-repo discoverability.

### SSOT decision (resolved 2026-04-20)

Plan prose (§Context, §Phase 8A, §Verification) assumed each v2 archetype declares `valid_pairs` inline in Python —
`rg valid_pairs strategy-service/.../v2/` returns **0 hits**. v2 classes only declare `ARCHETYPE` + `FAMILY` class vars.
The real matrix lives in `/codex/09-strategy/architecture-v2/category-instrument-coverage.md` + UI
`lib/architecture-v2/coverage.ts`.

**Operator confirmed: Python SSOT inline in UAC `archetype_capability.py`.** UI `coverage.ts` becomes a downstream
consumer; codex markdown stays human-authored with parity-check against the UAC manifest in UAC QG. A **new PM-repo sync
script** (`scripts/propagation/ sync-archetype-capability-to-ui.sh --check|--write`) enforces UAC-manifest →
UI-`coverage.ts` parity and is wired into `unified-trading-system-ui/scripts/quality-gates.sh` so every UI push catches
drift.

### Downstream consumer audit (Citadel rule-6)

Grep across all 60+ repos (excluding `.venv*`, `node_modules`, `build`, `_archived_pre_v2`):

- `ArchetypeCapability` (no V2): **0 hits** → name free.
- `ArchetypeCapabilityV2`: plan docs + UI `coverage.ts` type-alias → no runtime consumers.
- `ArchetypeCapabilityRegistry`: plan docs only → no runtime consumers.
- `for_pair(`: **0 hits** → new API surface.
- `from unified_api_contracts.strategy_availability import`: 0 runtime, 2 tests → facade naming defaults to existing
  `unified_api_contracts.strategy`.
- `valid_pairs` outside v2/: **0 hits** → no leaky consumers.
- `supported_pairs`: 1 hit in `registry/capability_declarations/_altdata.py` (different data-source context) → no
  collision.

**Conclusion: zero existing runtime consumers.** Wave C/D plans (G1.2, G1.6, G1.11) are the future consumers — they
don't exist yet as running code. No backwards-compat shim needed.

### Revised 3-commit flow (supersedes §Commit strategy above)

1. **UAC** — `feat(uac): G1.8 — ArchetypeCapabilityV2 registry + generator + manifest`
   - `internal/architecture_v2/archetype_capability.py` (NEW, ~180 LOC, Pydantic BaseModel pattern mirrored from
     `strategy_availability.py:128-172`, module-level tuple `ARCHETYPE_CAPABILITY_REGISTRY`, free-function helpers
     `capability_for`, `archetypes_for_pair`, `archetypes_for_venue`, `all_capabilities`).
   - `internal/architecture_v2/archetype_capability_manifest.json` (NEW, generated, ~400 LOC).
   - `internal/architecture_v2/__init__.py` (+4 — re-export).
   - `strategy.py` domain facade (+2 — re-export; default to existing facade not a new `strategy_availability.py` public
     module unless operator pushes back).
   - `scripts/generate_archetype_capability_manifest.py` (NEW, ~120 LOC).
   - `tests/internal/unit/test_archetype_capability_manifest_parity.py` (NEW, ~80 LOC — regenerates in-process, asserts
     `len == 18`, asserts every `StrategyArchetypeV2` enum member has exactly one entry, spot-checks
     `archetypes_for_pair(CEFI, PERPETUAL)`).

2. **PM** — `feat(pm): G1.8 — UAC↔UI archetype-capability sync script`
   - `scripts/propagation/sync-archetype-capability-to-ui.sh` (NEW, ~40 LOC — shell wrapper mirroring
     `rollout-workflow-templates.sh` pattern).
   - `scripts/propagation/sync_archetype_capability_to_ui.py` (NEW, ~120 LOC — reads UAC manifest JSON, renders UI
     `coverage.ts` from deterministic TS template with AUTO-GEN header, `--check` diffs and exits 1 on drift, `--write`
     overwrites).

3. **UI** — `test(playbooks): G1.8 — UAC ArchetypeCapabilityV2 smoke spec + coverage.ts parity`
   - `tests/e2e/playbooks/refactor/refactor-g1-8-uac-archetype-capability.spec.ts` (NEW, ~60 LOC — mirrors
     `refactor-g1-9-codex-scope-registry.spec.ts` pattern).
   - `lib/architecture-v2/coverage.ts` (REGENERATED via PM `--write`, gains AUTO-GEN header).
   - `scripts/quality-gates.sh` (+5 — invoke PM sync-check step before Playwright:
     `bash "${WORKSPACE_ROOT}/unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh" --check`).

### Phase DAG (strict order)

```
8A audit → 8B design → 8C.1 gen + SSOT → 8C.2 type+registry+facade → 8C.3 manifest → 8D.1 UAC→codex parity → 8D.2 UAC QG → COMMIT 1 (UAC)
                                                                                                                           ↓
                                                                                                     8E.1 PM sync script → COMMIT 3 (PM)
                                                                                                                           ↓
                                                                                    8E.2 wire into UI QG → 8E.3 UI spec → UI QG → COMMIT 2 (UI)
```

UAC ships first (manifest authoritative), PM script second (reads UAC manifest from sibling repo), UI last (depends on
PM script existing + coverage.ts regeneration).

### Playwright assertions (tier-1, `localhost:3000`)

1. `seedPersona(page, 'admin')` → `page.goto('http://localhost:3000/services/strategy-catalogue/')`.
2. `expect(page.locator('[data-testid="archetype-tile"]')).toHaveCount(18)` — regression gate for UAC change breaking
   the catalogue.
3. For one archetype per family (8 total), assert detail route
   `/services/strategy-catalogue/strategies/<archetype>/<slot>` → HTTP 200 (orphan-reachability).
4. Visibility-slicing stub: comment-only TODO pointing to G1.6 — admin sees all today.
5. `coverage.ts` AUTO-GEN banner assertion — catches hand-edits.

Port canon: `localhost:3000` (tier-1 default per `scripts/dev-tiers.sh`). No stale `:3010` references in this plan.

### Breaking-change / shim analysis (Citadel rule-3)

Zero existing runtime consumers → **zero shims**. Purely additive: new module, new facade re-export, new manifest, new
test, new spec. No rename, no deletion.

### Remaining operator questions (non-blocking — can default)

1. **Domain facade for re-export.** Plan §Decisions line 34 says
   `from unified_api_contracts.strategy_availability import ArchetypeCapabilityV2`. No such public module exists.
   Default: re-export from existing `unified_api_contracts/strategy.py`.
2. **`supported_venues` source.** V2 archetypes don't declare venues. Default: deduce from `MarketCategory` × existing
   UAC venue registry (every venue tagged with category).
3. **`StrategyArchetypeV2.EVENT_DRIVEN` naming collision with family `EVENT_DRIVEN`.** Acceptable — will disambiguate in
   test assertions.

### Success criteria (final)

- `len(ARCHETYPE_CAPABILITY_REGISTRY) == 18`; every `StrategyArchetypeV2` member covered.
- UAC→codex parity test green; UAC QG green.
- `bash sync-archetype-capability-to-ui.sh --check` fails pre-regeneration, passes after `--write`.
- UI Playwright spec green on tier-1; existing `screenshots.spec.ts` + `visibility-slicing.spec.ts` unaffected.
- 3 SHAs visible in `git log origin/live-defi-rollout --oneline -20` (UAC + PM + UI).
