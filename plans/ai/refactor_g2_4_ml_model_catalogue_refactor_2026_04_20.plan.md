---
title: Refactor G2.4 — ML Model Catalogue refactor (four-catalogue parity)
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §2.4
  - refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md
  - refactor_g1_8_uac_archetype_capability_v2_2026_04_20.plan.md
  - refactor_g2_9_uac_remaining_gaps_2026_04_20.plan.md (gaps #6, #11 consumers)
  - refactor_g1_5_ml_catalogue_broken_hrefs_cleanup_2026_04_20.plan.md (absorbed)
# Wave G2-γ — parallel with G2.3, G2.5. Absorbs G1.5 ML stubs.
supersedes: [refactor_g1_5_ml_catalogue_broken_hrefs_cleanup_2026_04_20.plan.md]
reconciliation_supersedes_added: 2026-04-25
---

> **Reconciliation note (2026-04-25):** This plan absorbs
> [refactor_g1_5_ml_catalogue_broken_hrefs_cleanup_2026_04_20.plan.md](./refactor_g1_5_ml_catalogue_broken_hrefs_cleanup_2026_04_20.plan.md).
> G1.5 was absorbed into G2.4 per depends_on amendment 2026-04-22 See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence anchors.

# Refactor G2.4 — ML Model Catalogue refactor

## Context

Stage 3E §2.4 ships the ML Model Catalogue refactor. Today `/services/research/ml/*` is 9 routes plus 5 broken hrefs
(G1.5 shipped stubs). Fragmented routes partially overlap: config + grid-config + registry + training. No
`ModelFamilyRegistry` in UAC. No per-model-family lock state or maturity. This is the biggest single pending UI surface
per stage-3a §4.3.

Target: `/services/ml-model-catalogue/*` matching the Strategy Catalogue pattern. UAC `ModelFamilyRegistry` declares
families: `xgboost_1h, lstm_5m, transformer_event, poisson_xg, logit_eloprobs, ...`. Per-family lock state + maturity
(reusing Phase-10.5 `LockState` + `StrategyMaturity`). Cross-links from Strategy Catalogue's `ml_family_ref` field.
Absorbs G1.5 stubbed ML routes. Consumes UAC gap #6 (IvSurfaceFidelity) for options-model families and gap #11
(RepresentativeFutureRegistry) for dated-future model families.

## Decisions locked with user (2026-04-20)

| Decision                                                  | Chosen                                                         | Source                            |
| --------------------------------------------------------- | -------------------------------------------------------------- | --------------------------------- |
| Mirrors Strategy Catalogue pattern                        | Four-catalogue parity                                          | Stage 3E §2.4                     |
| `ModelFamilyRegistry` in UAC (Option X)                   | Follows G1.8 ArchetypeCapability pattern                       | Wave E closure memory — Option X  |
| Lock state + maturity reused from Phase 10.5              | Avoid new enums                                                | Phase 10.5 precedent              |
| 9 existing routes + 5 G1.5 stubs → ~7 consolidated routes | Collapse overlapping config/grid-config/registry; absorb stubs | Stage 3E §2.4 blast radius        |
| Strategy Catalogue's `ml_family_ref` field cross-links    | Bidirectional navigation                                       | Strategy Catalogue existing field |
| Model-family → (category, instrument_type) eligibility    | Mirrors ArchetypeCapability.valid_pairs semantics              | G1.8 precedent                    |

## Cross-references

- **Upstream:** G1.6 derivation engine, G1.8 ArchetypeCapability (pattern), G2.9 gap #6 + gap #11
- **Wave G2-γ peers (parallel):** G2.3, G2.5
- **Absorbed:** G1.5 ML Catalogue broken-hrefs cleanup — its 5 stub routes become the canonical detail pages
- **Codex:** `/codex/09-strategy/architecture-v2/README.md`, `codex/09-strategy/architecture-v2/cross-cutting/`
- **Strategy Catalogue precedent:** `unified-trading-system-ui/app/services/strategy-catalogue/`

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §2.4
2. `refactor_g1_5_ml_catalogue_broken_hrefs_cleanup_2026_04_20.plan.md` — absorbed scope
3. `refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md`
4. `refactor_g1_8_uac_archetype_capability_v2_2026_04_20.plan.md` — pattern to replicate
5. `unified-trading-system-ui/app/services/strategy-catalogue/` — all routes + components
6. `unified-trading-system-ui/app/services/research/ml/` — 9 existing routes + 5 G1.5 stubs
7. `unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py` (G1.8 precedent)
8. `/codex/09-strategy/architecture-v2/uac-registry-gaps.md` — gaps #6, #11

## Out of scope

- Data Catalogue (G2.3 — separate plan)
- Execution Algo Catalogue (G2.5 — separate plan)
- Training-job orchestration (out-of-scope even for G3; read-only surface)
- New ML algorithm implementations — catalogue metadata only
- Reading `_archived_pre_v2/` paths

## Dev/staging parity rule

Dev mock mode serves sample model-registry data via `VITE_MOCK_API=true`; staging hits real model registry endpoint.
Same UI code path — `useModelFamily(family_id)` hook resolves identically.

## Phase breakdown

### Phase A — UAC ModelFamilyRegistry

- [ ] [AGENT] P0. Declare `ModelFamilyEntry` at
      `unified-api-contracts/unified_api_contracts/internal/architecture_v2/model_family.py`:
      `{family_id, display_name, algo_class, supported_pairs: tuple[(Category, InstrumentType), ...], lock_state,     maturity, ml_ref_url}`.
- [ ] [AGENT] P0. `MODEL_FAMILY_REGISTRY: tuple[ModelFamilyEntry, ...]` seeded with 8+ families (xgboost_1h, lstm_5m,
      transformer_event, poisson_xg, logit_eloprobs, ...).
- [ ] [AGENT] P0. Helpers `family_for(family_id)`, `families_for_pair(category, instrument_type)`,
      `families_for_archetype(archetype_id)`.
- [ ] [AGENT] P0. ≥10 UAC tests.

### Phase B — UI routes

- [ ] [AGENT] P0. `unified-trading-system-ui/app/services/ml-model-catalogue/page.tsx` — master matrix: family ×
      (category, instrument_type) with lock-state + maturity chips.
- [ ] [AGENT] P0. `unified-trading-system-ui/app/services/ml-model-catalogue/[family_id]/page.tsx` — per-family detail
      with algo class + supported pairs + `ml_ref_url` deep-link.
- [ ] [AGENT] P0. Five G1.5 stubs → folded into canonical routes: `/services/ml-model-catalogue/overview`,
      `/ml-model-catalogue/experiments`, `/ml-model-catalogue/features`, `/ml-model-catalogue/validation`,
      `/ml-model-catalogue/deploy`.
- [ ] [AGENT] P0. Admin availability page mirroring Strategy Catalogue admin.

### Phase C — Library + hooks + cross-links

- [ ] [AGENT] P0. `unified-trading-system-ui/lib/ml-model-catalogue/registry.ts` — TypeScript mirror of UAC (auto-sync
      script or hand-synced documented).
- [ ] [AGENT] P0. Hook `useModelFamily(family_id)`.
- [ ] [AGENT] P0. Strategy Catalogue per-strategy detail pages gain `ml_family_ref` chip linking here.

### Phase D — Retire legacy + redirects

- [ ] [AGENT] P0. DELETE old `/services/research/ml/*` routes; 308 redirect to new canonical routes.
- [ ] [AGENT] P0. Update `lib/lifecycle-route-mappings.ts`.

### Phase E — QG + verification

- [ ] [SCRIPT] P0. `cd unified-api-contracts && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. Playwright spec `refactor-g2-4-ml-model-catalogue.spec.ts` — full flow + cross-link coverage.

## Critical files to be modified

- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/model_family.py` — NEW
- `unified-api-contracts/tests/internal/unit/test_model_family.py` — NEW
- `unified-trading-system-ui/app/services/ml-model-catalogue/*` — ≥7 new pages
- `unified-trading-system-ui/lib/ml-model-catalogue/registry.ts` — NEW
- `unified-trading-system-ui/app/services/research/ml/*` — DELETE
- `unified-trading-system-ui/next.config.mjs` — MODIFY (redirects)
- `unified-trading-system-ui/lib/lifecycle-route-mappings.ts` — MODIFY
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-4-ml-model-catalogue.spec.ts` — NEW

## Execution DAG

```
A (UAC registry) → B (UI routes) + C (library + cross-links) [parallel]
                     ↓
                   D (retire legacy)
                     ↓
                   E (QG + Playwright)
```

## Verification

1. `ModelFamilyRegistry` declared with ≥8 families.
2. ≥10 UAC tests green.
3. 7 new catalogue routes render.
4. Cross-links from Strategy Catalogue via `ml_family_ref` work.
5. Legacy routes 308-redirect.
6. Playwright spec green.
7. QG green on both repos.

## Handoff

Unblocks:

- **pb3c `dart-demo.md`** — ML research walkthrough.
- **pb3b `investment-management-demo.md`** — reporting on ML-backed strategies.
- **G3.3 briefings CMS** — briefings referencing ML models link to the catalogue.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` through MCP Playwright tools as admin + `client-full` personas;
walk catalogue → family detail → ml_ref_url link → cross-link to Strategy Catalogue; assert lock-state + maturity chips
render.

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-4-ml-model-catalogue.spec.ts`:

1. Seed admin persona; walk catalogue matrix.
2. Navigate per-family detail; assert chip rendering.
3. Navigate cross-link from Strategy Catalogue via `ml_family_ref`; assert bidirectional navigation.
4. Visit a legacy `/services/research/ml/*` URL; assert 308 redirect.
5. Include orphan-reachability.
6. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G2.4 (Wave G2-γ).**

---

You are executing **Refactor G2.4 — ML Model Catalogue refactor** for the Unified Trading System at Odum Research. Wave
G2-γ; gates on G1.6 + G1.8 + G2.9 gaps #6/#11.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-api-contracts checkout live-defi-rollout && git -C unified-api-contracts pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py  # G1.8
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py  # G1.6
ls unified-trading-system-ui/app/services/strategy-catalogue/  # precedent
ls unified-trading-system-ui/app/services/research/ml/  # legacy to migrate
```

All gates green. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases A through E of this plan:
`plans/active/refactor_g2_4_ml_model_catalogue_refactor_2026_04_20.plan.md`

### Read-set (mandatory)

All 8 paths from the plan's Mandatory read-set.

### Deliverables

Per plan's Critical files list — spans UAC + UI repos.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` through MCP Playwright tools as admin + `client-full` personas. Walk catalogue → family detail →
`ml_ref_url` link → cross-link to Strategy Catalogue. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-4-ml-model-catalogue.spec.ts` — full flow +
cross-link + legacy-redirect coverage, wired into `scripts/quality-gates.sh`, including orphan-reachability.

### Commit strategy

Two repos → two commits. `git pull --rebase` before each push.

```
cd unified-api-contracts && bash scripts/quickmerge.sh "feat(uac): G2.4 — ModelFamilyRegistry + helpers" --agent
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "feat(ml-model-catalogue): G2.4 — catalogue routes + retire legacy /services/research/ml" --agent
```

Manual-git fallback per-repo. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ `ModelFamilyRegistry` ≥8 families + ≥10 tests green.
2. ✅ 7 new catalogue routes render.
3. ✅ Strategy Catalogue cross-link via `ml_family_ref` works.
4. ✅ Legacy routes 308-redirect.
5. ✅ Playwright spec green.
6. ✅ QG green on both repos.
7. ✅ 2 commit SHAs pushed.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP.
- Do NOT build new chip primitives; reuse `components/architecture-v2/`.
- Do NOT implement new ML algorithms — catalogue metadata surface only.
- Do NOT leave G1.5 stubs as-is — fold into canonical ml-model-catalogue routes.
- Do NOT skip the Strategy Catalogue cross-link — bidirectional navigation required.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- Model family count + list.
- UAC test count + pass rate.
- 7 new route file list.
- Cross-link verification (Strategy ↔ ML).
- Legacy deletion + redirect count.
- Playwright spec pass status.
- QG results (both repos).
- 2 commit SHAs pushed to live-defi-rollout.
