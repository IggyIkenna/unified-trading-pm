---
title: Refactor G2.5 — Execution Algo Catalogue refactor (four-catalogue parity)
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md §2.5
  - refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md
  - refactor_g2_9_uac_remaining_gaps_2026_04_20.plan.md (gaps #7 + #10 hard deps)
# Wave G2-γ — parallel with G2.3, G2.4. Gates on G2.9 gaps #7 + #10.
---

# Refactor G2.5 — Execution Algo Catalogue refactor

## Context

Stage 3E §2.5 ships the Execution Algo Catalogue refactor. Today `/services/execution/*` has 7 sub-routes (algos,
benchmarks, candidates, handoff, overview, tca, venues) + `[executionId]`. `algos` is a flat list without archetype
hierarchy (TWAP / VWAP / POV / iceberg / SOR / sniper / liquidation-bot / flash-loan-bundle / calendar-spread-combo /
limit-passive / market / leader-hedge). `venues` duplicates `/services/data/venues`. `candidates` + `handoff` arguably
belong in the Strategy Catalogue's promotion-ledger flow.

Target: `/services/execution-algo-catalogue/*` matching the Strategy Catalogue pattern. UAC `ExecutionAlgoCatalogV2`.
Venue consolidation (finally) folds `/services/execution/venues` + `/services/data/venues` into
`/services/execution-algo-catalogue/venues`. `candidates` + `handoff` migrate into Strategy Catalogue's existing
promotion-ledger UI. Requires UAC gaps #7 (MultiLegOrderCapability) + #10 (CrossVenueRoutingPolicy) from G2.9.

## Decisions locked with user (2026-04-20)

| Decision                                                               | Chosen                                                                                                                     | Source                       |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| Mirrors Strategy Catalogue + ML Catalogue pattern                      | Four-catalogue parity                                                                                                      | Stage 3E §2.5                |
| Execution algo archetype hierarchy                                     | TWAP/VWAP/POV/iceberg/SOR/sniper/liquidation-bot/flash-loan-bundle/calendar-spread-combo/limit-passive/market/leader-hedge | Stage 3E §2.5 archetype list |
| Venue consolidation: data/venues + execution/venues → catalogue/venues | Single venue SSOT in catalogue namespace                                                                                   | Stage 3E §2.5                |
| `candidates` + `handoff` relocated to Strategy Catalogue               | Promotion-ledger flow belongs with strategies, not execution                                                               | Stage 3E §2.5 rationale      |
| Hard dependencies: UAC #7 + #10                                        | MultiLegOrderCapability + CrossVenueRoutingPolicy gate algo-archetype surface                                              | Stage 3E §2.5 blockers       |

## Cross-references

- **Upstream:** G1.6 derivation engine, G2.9 gap #7 + gap #10 (hard)
- **Wave G2-γ peers (parallel):** G2.3 (retains `/services/data/venues` for G2.5 to consume), G2.4 (ML Catalogue)
- **Strategy Catalogue:** existing `/services/strategy-catalogue/` — absorbs `candidates` + `handoff`
- **Codex:** `codex/04-architecture/` — execution-service layout

## Mandatory read-set

1. `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §2.5
2. `refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md`
3. `refactor_g2_9_uac_remaining_gaps_2026_04_20.plan.md` — gaps #7 + #10 sections
4. `unified-trading-system-ui/app/services/execution/` — 7 current routes
5. `unified-trading-system-ui/app/services/strategy-catalogue/` — pattern + `candidates`/`handoff` absorption target
6. `execution-service/algo_library/` — source of truth for algo definitions
7. `/codex/09-strategy/architecture-v2/uac-registry-gaps.md` — gaps #7, #10

## Out of scope

- Data Catalogue (G2.3)
- ML Model Catalogue (G2.4)
- New execution algos (catalogue metadata surface only)
- Execution-service HTTP endpoints beyond metadata
- Reading `_archived_pre_v2/` paths

## Dev/staging parity rule

Dev mock mode serves sample algo-metadata; staging hits execution-service algo-metadata endpoint. Identical UI path.

## Phase breakdown

### Phase A — UAC ExecutionAlgoCatalogV2

- [ ] [AGENT] P0. Declare `ExecutionAlgoEntry` at
      `unified-api-contracts/unified_api_contracts/internal/architecture_v2/execution_algo.py`:
      `{algo_id, archetype, display_name, supported_venues[], supports_multi_leg, routing_policy, lock_state, maturity}`.
- [ ] [AGENT] P0. `EXECUTION_ALGO_REGISTRY: tuple[ExecutionAlgoEntry, ...]` seeded with 12+ algos per the archetype
      list.
- [ ] [AGENT] P0. Helpers `algo_for(algo_id)`, `algos_for_archetype(arch)`, `algos_for_venue(venue)`.
- [ ] [AGENT] P0. ≥10 UAC tests; consumes gap #7 (`MultiLegOrderCapability`) + gap #10 (`CrossVenueRoutingPolicy`).

### Phase B — UI routes

- [ ] [AGENT] P0. `unified-trading-system-ui/app/services/execution-algo-catalogue/page.tsx` — master matrix: algo ×
      archetype × venue.
- [ ] [AGENT] P0. `.../[archetype]/page.tsx` — archetype detail.
- [ ] [AGENT] P0. `.../[archetype]/[algo_id]/page.tsx` — per-algo detail.
- [ ] [AGENT] P0. `.../venues/page.tsx` — venue list (consolidated from data + execution).
- [ ] [AGENT] P0. `.../tca/page.tsx` — TCA surface (upgraded from stub).

### Phase C — Library + cross-links

- [ ] [AGENT] P0. `unified-trading-system-ui/lib/execution-algo-catalogue/registry.ts` — TS mirror (auto-sync).
- [ ] [AGENT] P0. Strategy Catalogue per-strategy detail page: reference a default execution-algo via
      `execution_algo_ref` chip.

### Phase D — `candidates` + `handoff` absorption + venue consolidation + legacy retire

- [ ] [AGENT] P0. Move `/services/execution/candidates` → `/services/strategy-catalogue/candidates` (promotion-ledger).
- [ ] [AGENT] P0. Move `/services/execution/handoff` → `/services/strategy-catalogue/handoff`.
- [ ] [AGENT] P0. DELETE `/services/data/venues` + `/services/execution/venues`; 308 →
      `/services/execution-algo-catalogue/venues`.
- [ ] [AGENT] P0. DELETE remaining old `/services/execution/*` routes; 308 → new counterparts.
- [ ] [AGENT] P0. Update `lib/lifecycle-route-mappings.ts`.

### Phase E — QG + verification

- [ ] [SCRIPT] P0. `cd unified-api-contracts && bash scripts/quality-gates.sh`
- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. Playwright spec `refactor-g2-5-execution-algo-catalogue.spec.ts` — full flow.

## Critical files to be modified

- `unified-api-contracts/unified_api_contracts/internal/architecture_v2/execution_algo.py` — NEW
- `unified-api-contracts/tests/internal/unit/test_execution_algo.py` — NEW
- `unified-trading-system-ui/app/services/execution-algo-catalogue/*` — 5+ new pages
- `unified-trading-system-ui/lib/execution-algo-catalogue/registry.ts` — NEW
- `unified-trading-system-ui/app/services/strategy-catalogue/{candidates,handoff}/page.tsx` — NEW (moved)
- `unified-trading-system-ui/app/services/execution/*` — DELETE
- `unified-trading-system-ui/app/services/data/venues/page.tsx` — DELETE
- `unified-trading-system-ui/next.config.mjs` — MODIFY (redirects)
- `unified-trading-system-ui/lib/lifecycle-route-mappings.ts` — MODIFY
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-5-execution-algo-catalogue.spec.ts` — NEW

## Execution DAG

```
A (UAC registry — depends on G2.9 #7 + #10) → B (UI routes) + C (library + cross-links) [parallel]
                                                 ↓
                                               D (candidates + handoff move + venue consolidation + legacy retire)
                                                 ↓
                                               E (QG + Playwright)
```

## Verification

1. `ExecutionAlgoCatalogV2` + registry with ≥12 algos.
2. ≥10 UAC tests green.
3. 5+ new `/services/execution-algo-catalogue/*` routes.
4. `candidates` + `handoff` in Strategy Catalogue namespace.
5. Venue consolidation: one SSOT at catalogue/venues.
6. Legacy routes 308-redirect.
7. Playwright spec green.
8. QG green on both repos.

## Handoff

Unblocks:

- **pb3c `dart-demo.md`** — execution-algo walkthrough.
- **G3.1 pricing-engine** — integration-depth pricing reads algo metadata.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` through MCP Playwright tools as admin persona. Walk archetype
matrix → algo detail → venue list → TCA. Visit legacy URLs; assert redirects. Navigate `candidates` + `handoff` in new
Strategy Catalogue location.

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-5-execution-algo-catalogue.spec.ts`:

1. Seed admin persona; walk catalogue matrix.
2. Per-algo detail; assert `supports_multi_leg` + `routing_policy` chips.
3. Venue list; assert single SSOT (no duplicates with data-catalogue).
4. Navigate `candidates` + `handoff`; assert Strategy Catalogue namespace.
5. Visit legacy URLs; assert redirects.
6. Include orphan-reachability.
7. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G2.5 (Wave G2-γ).**

---

You are executing **Refactor G2.5 — Execution Algo Catalogue refactor** for the Unified Trading System at Odum Research.
Wave G2-γ; hard deps on G1.6 + G2.9 gaps #7 + #10.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-api-contracts checkout live-defi-rollout && git -C unified-api-contracts pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
# Verify G2.9 gap #7 + #10 shipped
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/multi_leg_order_capability.py 2>/dev/null || echo "G2.9 gap #7 NOT SHIPPED"
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/cross_venue_routing_policy.py 2>/dev/null || echo "G2.9 gap #10 NOT SHIPPED"
ls unified-trading-system-ui/app/services/execution/  # legacy to migrate
```

All gates green. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases A through E of this plan:
`plans/active/refactor_g2_5_execution_algo_catalogue_refactor_2026_04_20.plan.md`

### Read-set (mandatory)

All 7 paths from the plan's Mandatory read-set.

### Deliverables

Per plan's Critical files list — spans UAC + UI repos.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` through MCP Playwright tools as admin persona; walk catalogue → archetype → algo detail → venue
list → TCA. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-5-execution-algo-catalogue.spec.ts` — full flow

- candidates/handoff migration + venue consolidation + legacy-redirect coverage, wired into `scripts/quality-gates.sh`,
  including orphan-reachability.

### Commit strategy

Two repos → two commits. `git pull --rebase` before each push.

```
cd unified-api-contracts && bash scripts/quickmerge.sh "feat(uac): G2.5 — ExecutionAlgoCatalogV2 + helpers" --agent
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "feat(execution-algo-catalogue): G2.5 — catalogue routes + candidates/handoff migration + venue consolidation" --agent
```

Manual-git fallback per-repo. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ `ExecutionAlgoCatalogV2` ≥12 algos + ≥10 tests green.
2. ✅ 5+ new catalogue routes render.
3. ✅ `candidates` + `handoff` in Strategy Catalogue namespace.
4. ✅ Venue consolidation: data/venues + execution/venues → catalogue/venues.
5. ✅ Legacy routes 308-redirect.
6. ✅ Playwright spec green.
7. ✅ QG green on both repos.
8. ✅ 2 commit SHAs pushed.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP.
- Do NOT build new chip primitives; reuse `components/architecture-v2/`.
- Do NOT implement new execution algos — catalogue metadata only.
- Do NOT leave `candidates` or `handoff` in the execution namespace — move them.
- Do NOT keep `/services/data/venues` or `/services/execution/venues` — consolidate.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- Algo registry count + archetype list.
- UAC test count + pass rate.
- 5+ new route file list.
- Candidates/handoff migration verification.
- Venue consolidation verification (single SSOT).
- Legacy deletion + redirect count.
- Playwright spec pass status.
- QG results (both repos).
- 2 commit SHAs pushed to live-defi-rollout.
