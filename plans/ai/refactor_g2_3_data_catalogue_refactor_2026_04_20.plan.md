---
title: Refactor G2.3 — Data Catalogue refactor (four-catalogue parity)
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §2.3
  - refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md
  - refactor_g2_9_uac_remaining_gaps_2026_04_20.plan.md (gap #5 consumer)
# Wave G2-γ — parallel with G2.4, G2.5. Gates on G1.6 + selective G2.9 gaps. Independent of G2-α/β.
---

# Refactor G2.3 — Data Catalogue refactor

## Context

Stage 3E §2.3 ships the Data Catalogue refactor as part of the four-catalogue parity effort (Data + Strategy + ML
Model + Execution Algo). Today `/services/data/*` is 13 routes of ad-hoc lists — instruments, venues, coverage,
completeness, gaps, missing, events, logs, processing, raw, valuation, markets. Three concept-duplicates (completeness

- missing + gaps). No queryable master matrix. No archetype × instrument × venue × chain dimension navigation like the
  Strategy Catalogue. No codex deep-link.

Target: `/services/data-catalogue/*` matching the Strategy Catalogue pattern — master matrix, filter facets,
per-instrument detail, admin availability axis, codex GitHub deep-link. Three concept-duplicates consolidated into
`/services/data-catalogue/coverage/gaps` with tabs. Reuses `LockState` + `StrategyMaturity` chip primitives for
data-availability metadata.

## Decisions locked with user (2026-04-20)

| Decision                                                                                 | Chosen                                                                                                 | Source                     |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | -------------------------- |
| Mirrors Strategy Catalogue pattern exactly                                               | Four-catalogue parity is the point — deviations defeat the rationale                                   | Stage 3E §2.3              |
| 13 routes → 7 consolidated routes                                                        | Coverage + missing + gaps → single tabbed page; venues deduplicated with execution/venues later (G2.5) | Stage 3E §2.3 blast radius |
| `DataCoverageStatus` uses same status enum as strategy (`SUPPORTED / BLOCKED / PENDING`) | Chip primitive reuse                                                                                   | Phase 10 UI precedent      |
| Data-status reads from `StrategyAvailabilityRegistry` + derivation engine                | No separate data-availability store                                                                    | G1.6 derivation engine     |
| Event-calendar coverage uses UAC gap #5 (`EventCalendarSourceCapability`)                | Sourced from G2.9                                                                                      | G2.9 gap #5                |

## Cross-references

- **Upstream:** G1.6 derivation engine, G2.9 gap #5 (EventCalendarSourceCapability)
- **Wave G2-γ peers (parallel):** G2.4 ML Model Catalogue, G2.5 Execution Algo Catalogue
- **Codex:** `/codex/02-data/availability-manifest-and-data-status.md` — SSOT doc that the catalogue will deep-link to
- **Precedent:** Strategy Catalogue under `unified-trading-system-ui/app/services/strategy-catalogue/` (Phase 10
  shipped)

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §2.3
2. `/codex/02-data/availability-manifest-and-data-status.md`
3. `refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.plan.md`
4. `/codex/09-strategy/architecture-v2/category-instrument-coverage.md` — master matrix precedent
5. `unified-trading-system-ui/app/services/strategy-catalogue/` — all routes + components
6. `unified-trading-system-ui/components/architecture-v2/` — chip primitives
7. `unified-trading-system-ui/app/services/data/` — 13 current routes
8. `/codex/09-strategy/architecture-v2/uac-registry-gaps.md` — gap #5

## Out of scope

- Execution Algo Catalogue (G2.5 — separate plan)
- ML Model Catalogue (G2.4 — separate plan)
- Venue consolidation (defer to G2.5 since both Data + Execution list venues)
- Building new data APIs — read-only surfaces over existing endpoints
- Reading `_archived_pre_v2/` paths

## Dev/staging parity rule

Dev mock mode serves `VITE_MOCK_API=true` sample data; staging hits real availability endpoints. Both routes render
identically (mirror Strategy Catalogue's pattern).

## Phase breakdown

### Phase A — Route scaffolding

- [ ] [AGENT] P0. `unified-trading-system-ui/app/services/data-catalogue/page.tsx` — landing page: archetype (instrument
      type) × venue × chain matrix with filter facets.
- [ ] [AGENT] P0. `unified-trading-system-ui/app/services/data-catalogue/coverage/gaps/page.tsx` — 3-tab page
      (Completeness, Missing, Gaps) replacing three current routes.
- [ ] [AGENT] P0. `unified-trading-system-ui/app/services/data-catalogue/[instrument_type]/[venue]/page.tsx` —
      per-instrument detail.
- [ ] [AGENT] P0. `unified-trading-system-ui/app/services/data-catalogue/events/page.tsx` — consumes gap #5
      `EventCalendarSourceCapability`.
- [ ] [AGENT] P0. `unified-trading-system-ui/app/services/data-catalogue/admin/page.tsx` — admin availability axis
      mirroring Strategy Catalogue admin page.

### Phase B — Library + hooks

- [ ] [AGENT] P0. `unified-trading-system-ui/lib/data-catalogue/coverage.ts` — typed coverage-matrix computation
      mirroring `lib/architecture-v2/coverage.ts`.
- [ ] [AGENT] P0. Hooks `useDataCoverage(instrument_type, venue)`, `useDataGaps(facets)`, `useEventCalendarSources()`.

### Phase C — Chip primitive reuse

- [ ] [AGENT] P0. Reuse `<StatusChip>`, `<VenueChip>`, `<InstrumentChip>` from `components/architecture-v2/`.
- [ ] [AGENT] P0. Codex deep-link button → `/codex/02-data/availability-manifest-and-data-status.md`.

### Phase D — Retirement of legacy routes

- [ ] [AGENT] P0. 308 redirect from old `/services/data/*` routes to new `/services/data-catalogue/*` counterparts in
      `next.config.mjs`.
- [ ] [AGENT] P0. DELETE legacy page files in `app/services/data/` (except `/venues` — defer to G2.5).
- [ ] [AGENT] P0. Update `lib/lifecycle-route-mappings.ts`.

### Phase E — QG + verification

- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. Playwright spec `refactor-g2-3-data-catalogue.spec.ts` — matrix + gaps + per-instrument + admin +
      event-calendar + legacy-redirect coverage.

## Critical files to be modified

- `unified-trading-system-ui/app/services/data-catalogue/page.tsx` — NEW
- `unified-trading-system-ui/app/services/data-catalogue/coverage/gaps/page.tsx` — NEW
- `unified-trading-system-ui/app/services/data-catalogue/[instrument_type]/[venue]/page.tsx` — NEW
- `unified-trading-system-ui/app/services/data-catalogue/events/page.tsx` — NEW
- `unified-trading-system-ui/app/services/data-catalogue/admin/page.tsx` — NEW
- `unified-trading-system-ui/lib/data-catalogue/coverage.ts` — NEW
- Legacy `app/services/data/*` — DELETE (except `/venues`)
- `unified-trading-system-ui/next.config.mjs` — MODIFY (redirects)
- `unified-trading-system-ui/lib/lifecycle-route-mappings.ts` — MODIFY
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-3-data-catalogue.spec.ts` — NEW

## Execution DAG

```
A (routes) → B (library + hooks) + C (chip reuse) [parallel]
               ↓
             D (retire legacy + redirects)
               ↓
             E (QG + Playwright)
```

## Verification

1. 5 new catalogue routes render.
2. Coverage/missing/gaps consolidated into one 3-tab page.
3. Data-status pulled from StrategyAvailabilityRegistry + derivation engine.
4. Event-calendar surface consumes gap #5 UAC data.
5. Legacy routes 308-redirect.
6. Playwright spec green.
7. UI QG green.

## Handoff

Unblocks:

- **pb3c `dart-demo.md`** — data-exploration walkthrough.
- **G2.5** — venue consolidation reference (G2.3 retains `/venues` for G2.5 to consume).
- **G3.1** pricing engine — cost formula can reference data-coverage metadata.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` through MCP Playwright tools as `client-data-only` persona; walk
catalogue matrix → filter by venue → detail page → gaps tab; assert data-status chips render per derivation engine.
Visit a legacy `/services/data/*` URL; assert 308 redirect.

**Durable spec for CI:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-3-data-catalogue.spec.ts`:

1. Seed `client-data-only` persona.
2. Navigate catalogue matrix; assert ≥1 cell per supported instrument_type × venue.
3. Navigate 3-tab gaps page; assert tab switching preserves filters.
4. Navigate per-instrument detail; assert data-status chips.
5. Seed admin persona; navigate `/admin` page; assert per-venue availability axis.
6. Visit legacy URL; assert 308.
7. Include orphan-reachability.
8. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G2.3 (Wave G2-γ).**

---

You are executing **Refactor G2.3 — Data Catalogue refactor** for the Unified Trading System at Odum Research. Wave
G2-γ; gates on G1.6 + G2.9 gap #5.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
# Verify G1.6 + G2.9 gap #5 shipped
ls unified-api-contracts/unified_api_contracts/internal/architecture_v2/derivation.py
ls unified-trading-system-ui/app/services/strategy-catalogue/  # precedent
ls unified-trading-system-ui/app/services/data/  # must exist to migrate
```

All gates green. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases A through E of this plan:
`plans/active/refactor_g2_3_data_catalogue_refactor_2026_04_20.plan.md`

### Read-set (mandatory)

All 8 paths from the plan's Mandatory read-set. Read Strategy Catalogue source fully — G2.3 is a structural copy.

### Deliverables

Per plan's Critical files list — 10 file changes in UI repo.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` through MCP Playwright tools as `client-data-only` + admin personas. Walk the full catalogue flow
(matrix → gaps → detail → admin), verify data-status chips render from derivation engine, visit legacy URLs to verify
308 redirects. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-3-data-catalogue.spec.ts` — 2 personas, full flow,
legacy-redirect coverage, wired into `scripts/quality-gates.sh`, including orphan-reachability.

### Commit strategy

Primarily UI — one commit.

```
cd unified-trading-system-ui && bash scripts/quickmerge.sh "feat(data-catalogue): G2.3 — data-catalogue routes + retire legacy /services/data" --agent
```

Manual-git fallback. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ 5 new `/services/data-catalogue/*` routes.
2. ✅ Legacy 13 routes retired (except `/venues`) with 308 redirects.
3. ✅ 3-tab gaps page consolidates coverage/missing/gaps.
4. ✅ Derivation-engine-driven data-status chips.
5. ✅ Playwright spec green.
6. ✅ UI QG green.
7. ✅ 1 commit SHA pushed.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP.
- Do NOT deviate from Strategy Catalogue structural pattern — parity is the goal.
- Do NOT build new chip primitives; reuse `components/architecture-v2/` chips.
- Do NOT delete `/services/data/venues` — deferred to G2.5.
- Do NOT hit data APIs outside `VITE_MOCK_API=true` in dev — CI credential-free.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- 5 new route file list.
- Legacy route deletion + redirect count.
- Playwright spec pass status.
- UI QG results.
- 1 commit SHA pushed to live-defi-rollout.
