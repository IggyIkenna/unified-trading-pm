---
title: Refactor G2.9 — UAC capability declarations (remaining 10 gaps #2–#11)
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
amended: 2026-04-22
depends_on:
  - /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §2.9
  - /codex/09-strategy/architecture-v2/uac-registry-gaps.md
  - UAC commit `e6f7c6d` (2026-04-21) — V2 suffix dropped; canonical is `ArchetypeCapability` (not
    `ArchetypeCapabilityV2`)
# Wave G2-α — parallel with G2-α peers 2.1, 2.6, 2.8, 2.11. Some sub-gaps consumed by G2-γ (2.3, 2.4, 2.5).
# V2 SUFFIX AMENDMENT 2026-04-22: post `e6f7c6d` the type is `ArchetypeCapability` (no V2). References throughout this plan updated accordingly.
---

# Refactor G2.9 — UAC capability declarations (remaining 10 gaps #2–#11)

## Context

Stage 3E §2.9 ships UAC gaps #2 through #11 from the tracker at
[`uac-registry-gaps.md`](/codex/09-strategy/architecture-v2/uac-registry-gaps.md). Gap #1 (`ArchetypeCapability` —
originally shipped as `ArchetypeCapabilityV2` in G1.8; V2 suffix dropped via UAC `e6f7c6d` on 2026-04-21) shipped in
G1.8; gap #12 (`StrategyAvailabilityRegistry`) shipped in Phase 10.5. The remaining 10 declarations are additive + each
is a self-contained sub-wave with its own consumers.

The ten gaps:

- #2 `supported_signal_variants` on `VenueCapV2`
- #3 `FlashLoanReceiverRegistry`
- #4 `LiquidationBonusScheduleV2`
- #5 `EventCalendarSourceCapability`
- #6 `IvSurfaceFidelity`
- #7 `MultiLegOrderCapability`
- #8 `PricingFidelity` on DeFi
- #9 `LaySideExecutionSemantics`
- #10 `CrossVenueRoutingPolicy`
- #11 `RepresentativeFutureRegistry`

Each gap is a separate UAC module + test file + consumer-service update. Ship as 10 sub-phases; each sub-phase is
independently parallelisable by downstream agents; a single umbrella plan keeps the gap-tracker state synchronised.

## Decisions locked with user (2026-04-20)

| Decision                                                                                                     | Chosen                                                        | Source                           |
| ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------- | -------------------------------- |
| One UAC module per gap, one umbrella plan                                                                    | Keeps gap tracker coherent; per-gap sub-phases parallelisable | Stage 3E §2.9                    |
| Each gap ships declaration + ≥1 consumer + tests in the same commit                                          | Avoids orphan UAC types                                       | Rule: no orphan UAC declarations |
| Consumer priority order: #7/#10 before G2-γ (2.5 algo catalogue); #11 standalone; others as capacity permits | Unblocks Wave G2-γ                                            | Stage 3E §2.5 blockers note      |
| New modules live under `unified_api_contracts/internal/architecture_v2/` (not top-level)                     | Option X pattern                                              | Wave E closure memory            |

## Cross-references

- **Wave G2-α peers (parallel):** G2.1, G2.6, G2.8, G2.11
- **Downstream Wave G2-γ:** G2.3 (Data Catalogue), G2.4 (ML Model Catalogue), G2.5 (Execution Algo Catalogue) — each
  consumes specific gaps
- **Gap tracker:** `/codex/09-strategy/architecture-v2/uac-registry-gaps.md`
- **G1 precedent:** G1.8 `ArchetypeCapability` (gap #1, originally shipped as `ArchetypeCapabilityV2` and renamed
  2026-04-21) established the pattern

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §2.9
2. `/codex/09-strategy/architecture-v2/uac-registry-gaps.md` — all 10 open gaps
3. `/codex/09-strategy/architecture-v2/README.md` — 8 families × 18 archetypes × 7 axes
4. `unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py` (G1.8 precedent)
5. `unified-api-contracts/unified_api_contracts/registry/capability_declarations/` — per-venue pattern
6. For each gap: the gap-tracker section + consumer-service directory (varies per gap):
   - #2: `features-service/` signal-variant consumers
   - #3: `execution-service/connectors/aave.py`
   - #4: `execution-service/connectors/aave.py` (liquidation bot algo)
   - #5: `features-event-service/`
   - #6: `features-onchain-service/` (options fidelity)
   - #7: `execution-service/algo_library/`
   - #8: `execution-service/connectors/` (DeFi swap fidelity)
   - #9: `execution-service/adapters/betfair.py`
   - #10: `execution-service/algo_library/routing/`
   - #11: `features-service/representative_future.py` + `representative-future-service/`

## Out of scope

- Gap #1 (shipped in G1.8)
- Gap #12 (shipped in Phase 10.5)
- Building new consumer services from scratch — only add gap references to existing services
- Reading `_archived_pre_v2/` paths

## Phase breakdown — one sub-phase per gap

### Phase 2 (gap #2) — `supported_signal_variants` on `VenueCapV2`

- [ ] [AGENT] P0. Extend `VenueCapV2` with `supported_signal_variants: frozenset[SignalVariant]` field.
- [ ] [AGENT] P0. Populate per-venue; consumer: features-service signal broadcast.
- [ ] [AGENT] P0. ≥6 test cases.

### Phase 3 (gap #3) — `FlashLoanReceiverRegistry`

- [ ] [AGENT] P0. Declare `FlashLoanReceiverRegistry` with per-chain receiver addresses.
- [ ] [AGENT] P0. Consumer: `execution-service/connectors/aave.py` — on-chain validation.
- [ ] [AGENT] P0. ≥5 test cases; integration with `testnet_contracts.yaml`.

### Phase 4 (gap #4) — `LiquidationBonusScheduleV2`

- [ ] [AGENT] P0. Declare chain × asset liquidation-bonus schedule.
- [ ] [AGENT] P0. Consumer: liquidation-bot strategy (if existent) or strategy-service DeFi algo config.
- [ ] [AGENT] P0. ≥5 test cases.

### Phase 5 (gap #5) — `EventCalendarSourceCapability`

- [ ] [AGENT] P0. Declare event-calendar source metadata (NFP, FOMC, CPI, CME macro, Sports fixtures).
- [ ] [AGENT] P0. Consumer: features-event-service.
- [ ] [AGENT] P0. ≥6 test cases.

### Phase 6 (gap #6) — `IvSurfaceFidelity`

- [ ] [AGENT] P0. Declare implied-volatility surface fidelity per venue (Deribit, CME-options).
- [ ] [AGENT] P0. Consumer: features-onchain-service options analytics.
- [ ] [AGENT] P0. ≥5 test cases.

### Phase 7 (gap #7) — `MultiLegOrderCapability`

- [ ] [AGENT] P0. Declare per-venue multi-leg order support (calendar spreads, straddles, iron condors).
- [ ] [AGENT] P0. Consumer: `execution-service/algo_library/` algo capability gating.
- [ ] [AGENT] P0. ≥6 test cases.
- **Gates G2.5** execution-algo catalogue.

### Phase 8 (gap #8) — `PricingFidelity` on DeFi

- [ ] [AGENT] P0. Declare DeFi pricing fidelity (AMM quote staleness, cross-pool consistency).
- [ ] [AGENT] P0. Consumer: DeFi connectors + execution algos.
- [ ] [AGENT] P0. ≥5 test cases.

### Phase 9 (gap #9) — `LaySideExecutionSemantics`

- [ ] [AGENT] P0. Declare lay-side semantics for Betfair / Smarkets sports venues.
- [ ] [AGENT] P0. Consumer: `execution-service/adapters/betfair.py`.
- [ ] [AGENT] P0. ≥5 test cases.

### Phase 10 (gap #10) — `CrossVenueRoutingPolicy`

- [ ] [AGENT] P0. Declare cross-venue routing policies (price-priority, latency-priority, fee-priority).
- [ ] [AGENT] P0. Consumer: execution-service SOR algo.
- [ ] [AGENT] P0. ≥6 test cases.
- **Gates G2.5** execution-algo catalogue.

### Phase 11 (gap #11) — `RepresentativeFutureRegistry`

- [ ] [AGENT] P0. Declare per-underlying representative future + roll discipline (see
      `project_dated_future_rolls_architecture_2026_04_19` memory).
- [ ] [AGENT] P0. Consumer: `features-service/representative_future.py` (new or extend).
- [ ] [AGENT] P0. ≥6 test cases.

### Phase 12 — QG + gap-tracker reconciliation

- [ ] [SCRIPT] P0. UAC QG green.
- [ ] [SCRIPT] P0. Each affected consumer-service QG green.
- [ ] [AGENT] P0. Update `/codex/09-strategy/architecture-v2/uac-registry-gaps.md` — mark gaps #2–#11 as SHIPPED with
      commit SHAs.

## Critical files to be modified

- 10 new `unified_api_contracts/internal/architecture_v2/<gap_name>.py` files (one per gap)
- 10 new `unified-api-contracts/tests/internal/unit/test_<gap_name>.py` files
- Per-gap consumer updates across ~6 services (see read-set mapping)
- `/codex/09-strategy/architecture-v2/uac-registry-gaps.md` — state flip on all 10 gaps

## Execution DAG

```
Phases 2–11 can ship in parallel (each gap independent), with per-gap declaration + consumer + tests
in a single commit. Commit prioritisation: #7, #10 (gate G2.5); others as agent capacity permits.

Phase 12 (gap-tracker reconciliation) after all 10 gaps shipped.
```

## Verification

1. All 10 UAC gap modules exist + consumer call-sites updated.
2. Per-gap ≥5 tests green (10 gaps × ~5 = ≥50 new tests).
3. `uac-registry-gaps.md` shows all 10 gaps SHIPPED with SHAs.
4. No orphan UAC types — every declaration has at least one consumer.
5. QG green on UAC + every affected consumer service.

## Handoff

Unblocks:

- **G2.3** — Data Catalogue refactor (uses gap #5 event-calendar metadata).
- **G2.4** — ML Model Catalogue refactor (uses gap #11 representative-future registry + gap #6 IvSurface).
- **G2.5** — Execution Algo Catalogue refactor (uses gap #7 multi-leg + gap #10 cross-venue routing).
- **Future** — pricing-engine (G3.1) reads #8 DeFi pricing-fidelity.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** not primarily a UI-facing change, but any gap whose consumer surfaces in a UI view (e.g.
gap #7 multi-leg UI, gap #11 representative-future chip) must be MCP-driven at tier-1 dev to verify the consumer renders
gap metadata correctly.

**Durable spec for CI:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-9-uac-gaps.spec.ts`:

1. Seed admin persona.
2. For each UI-surfacing gap (#6 IvSurface chip, #7 multi-leg chip, #11 representative-future chip), navigate to the
   consuming UI route and assert the gap metadata renders.
3. For non-UI-surfacing gaps, no UI assertion — test-count stays on the UAC unit-test side.
4. Include orphan-reachability assertion for any new chip.
5. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G2.9 (Wave G2-α, sub-phase-
parallelisable).**

---

You are executing **Refactor G2.9 — UAC capability declarations (gaps #2–#11)** for the Unified Trading System at Odum
Research. Wave G2-α; each gap is independently shippable.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-api-contracts checkout live-defi-rollout && git -C unified-api-contracts pull
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py  # G1.8 precedent
ls /codex/09-strategy/architecture-v2/uac-registry-gaps.md
# Per-gap consumer service verification — do during execution, not upfront
```

All must exist. STOP if precedent or tracker missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 2 through 12 of this plan (each phase = one gap):
`plans/active/refactor_g2_9_uac_remaining_gaps_2026_04_20.plan.md`

Prioritise gaps #7 and #10 (they gate G2.5). Other gaps in any order.

### Read-set (mandatory)

All paths from the plan's Mandatory read-set. For each gap, also read its section in `uac-registry-gaps.md` in full
before implementing.

### Deliverables

- 10 new UAC modules + 10 new test files + per-gap consumer updates + gap tracker reconciliation.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (tier-1 dev) through MCP Playwright tools for any gap whose consumer surfaces in a UI view (#6
IvSurface chip, #7 multi-leg chip, #11 representative-future chip). Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-9-uac-gaps.spec.ts` — asserting UI-surfacing gap
metadata renders, wired into `scripts/quality-gates.sh`, including orphan-reachability for any new chip.

### Commit strategy

Per gap: one commit in UAC + one commit in consumer service (or one combined commit if single-repo). ≈10-20 commits
total across gaps. `git pull --rebase` before each push.

```
# Example for gap #7 (multi-leg)
cd unified-api-contracts && bash scripts/quickmerge.sh "feat(uac): G2.9 gap #7 — MultiLegOrderCapability" --agent
cd ../execution-service && bash scripts/quickmerge.sh "feat(algo): G2.9 gap #7 consumer — multi-leg capability gating" --agent

# Final gap-tracker reconciliation commit
cd ../unified-trading-pm && bash scripts/quickmerge.sh "docs(codex): G2.9 — mark UAC gaps #2-#11 SHIPPED with SHAs" --agent
```

Manual-git fallback per-repo. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ All 10 gaps declared in UAC with ≥5 tests each.
2. ✅ Each gap has ≥1 consumer call-site updated.
3. ✅ `uac-registry-gaps.md` shows #2-#11 SHIPPED with SHAs.
4. ✅ No orphan UAC types.
5. ✅ QG green on UAC + every affected consumer service.
6. ✅ Playwright spec green for UI-surfacing gaps.
7. ✅ ≥10 UAC commit SHAs + ~6 consumer-service commit SHAs pushed.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP.
- Do NOT ship a UAC declaration without at least one consumer reference — no orphan types.
- Do NOT bundle all 10 gaps into one commit — per-gap commits keep the gap tracker coherent.
- Do NOT skip gaps #7 or #10 if G2.5 is waiting — prioritise these.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- Per-gap: commit SHA + test count.
- Gap tracker reconciliation commit SHA.
- QG results (UAC + affected consumers).
- Playwright spec pass status.
- Downstream handoff notes for G2.3/2.4/2.5.
