---
doc_type: plan
title: Refactor G1.3 — LOCKED-VISIBLE UI service-tile mode
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-system-ui]
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
    /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.3,
    /codex/14-playbooks/_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/playbook-concepts/visibility-slicing.md,
    /codex/14-playbooks/demo-ops/demo-restriction-profiles.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Refactor G1.3 — LOCKED-VISIBLE UI service-tile mode

## Context

Stage 3E §1.3 introduces a new service-tile UI state: **padlocked-but-visible**. Today's tile component has two states
(unlocked / hidden); `_ssot-rules/06` and `cross-cutting/visibility-slicing.md` mandate a third: LOCKED-VISIBLE — the
tile renders with a padlock affordance and a "request access" nudge, instead of being invisible. This enables the demo
tempt-logic and "show what's possible" discovery that rule 06's show/don't-show discipline calls out, without leaking
data or entering a page the prospect hasn't bought. The LOCKED-VISIBLE default is set by the demo restriction profile
(refactor_g1_7) and can be overridden per-tile via admin toggle (refactor_g1_10.5 — landed as part of Phase 10.5 prior
session).

## Decisions locked with user (2026-04-20)

| Decision                        | Chosen                                                                                                     | Source                                |
| ------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Three-state tile enum           | `"unlocked" \| "padlocked-visible" \| "hidden"` — closed enum                                              | Kickoff §1.3 + rule 06                |
| Default state for demo profiles | `"padlocked-visible"` on every adjacent-service tile — tempt discovery                                     | demo-ops/demo-restriction-profiles.md |
| Padlock UI affordance           | Visible lock icon + hover tooltip "Available on <package>; contact sales" + disabled click (no navigation) | Kickoff §1.3                          |
| Prop name on ServiceTile        | `lockState: LockState`                                                                                     | Kickoff §1.3                          |

## Cross-references

- **Sibling Wave A plans:** refactor*g1*{1,5,9,12,14}\_2026_04_20.md
- **Wave D consumer:** refactor_g1_7_restriction_profile_engine — the engine's output maps to `lockState` per tile.
- **Rules cited:** `_ssot-rules/06-show-dont-show-discipline.md` (LOCKED-VISIBLE vs HIDDEN-ENTIRELY section)
- **Cross-cutting:** `/codex/14-customer-journeys/playbook-concepts/visibility-slicing.md`
- **Demo-ops:** `/codex/14-playbooks/demo-ops/demo-restriction-profiles.md`

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.3
2. `/codex/14-playbooks/_ssot-rules/06-show-dont-show-discipline.md` (full — especially LOCKED-VISIBLE vs
   HIDDEN-ENTIRELY section)
3. `/codex/14-customer-journeys/playbook-concepts/visibility-slicing.md`
4. `/codex/14-playbooks/demo-ops/demo-restriction-profiles.md`
5. `unified-trading-system-ui/components/shell/service-tabs.tsx`
6. Existing ServiceTile / service-card component (enumerate path in Phase 3A; today likely under `components/services/`
   or `components/shell/`)
7. `unified-trading-system-ui/components/architecture-v2/LockState.tsx` — existing strategy-catalogue LockState chip;
   REUSE, don't reinvent

## Out of scope

- The admin toggle UI to set `lockState` per tile — that is a downstream (Phase 10.5 already shipped; this plan's tile
  consumes the existing store).
- The restriction-profile → lockState mapping — that lives in refactor_g1_7.
- The questionnaire → profile flow — that lives in refactor_g1_10.
- Changing the unlocked-tile UX — only the new "padlocked-visible" state is added.

## Dev / staging parity rule

Demo flows MUST behave identically in dev and staging:

- **Dev (`localhost:3000`):** mock auth via `demo-provider.ts` + localStorage persona seed; LOCKED-VISIBLE state is
  computed client-side from the seeded persona's restriction profile.
- **Staging (`odum-research.co.uk`):** Firebase staging project; same personas provisioned as real Firebase users via
  user-management-ui; same LOCKED-VISIBLE computation server-side (or same client-side lookup against the real claim
  set).
- **Prod (`odum-research.com`):** Firebase prod project; real paying clients; same codebase; same tile visibility logic.

Only difference: the source of the persona identity (localStorage seed vs Firebase auth). Tile render logic + padlock
affordance + "request access" nudge are identical. Any divergence is a rule-03 violation.

## Phase breakdown

### Phase 3A — Audit + design

- [x] [AGENT] P0. Enumerate every ServiceTile render site in the UI — component paths + usage sites. List in
      `/tmp/g1_3_tile_audit.md`.
- [x] [AGENT] P0. Identify existing `components/architecture-v2/LockState.tsx` chip + reuse semantics. Confirm
      three-state enum matches. Actual path: `components/architecture-v2/lock-state-badge.tsx`; reused only the strategy
      4-state `LockState` naming convention. Tile lockState is a distinct 3-value enum in
      `lib/visibility/tile-lock-state.ts` (avoids name collision with strategy-slot LockState).
- [x] [AGENT] P0. Design: `<ServiceTile lockState="padlocked-visible" ... />` renders title + icon + padlock overlay +
      "request access" nudge, disabled click.

### Phase 3B — Implement tile lockState prop + padlock affordance

- [x] [AGENT] P0. Add `lockState?: LockState` prop to ServiceTile (default `"unlocked"` to preserve existing behaviour).
- [x] [AGENT] P0. For `lockState === "padlocked-visible"`: render padlock icon (reuse existing lucide or architecture-v2
      icon), tooltip copy per demo-restriction-profiles.md, `aria-disabled="true"` + `pointerEvents: none` on the
      clickable inner.
- [x] [AGENT] P0. For `lockState === "hidden"`: return `null` (consistent with today's hide pattern — do not render).
- [x] [AGENT] P0. Add `data-testid="service-tile-<slug>"` + `data-lock-state="<state>"` hooks for Playwright.

### Phase 3C — Wire stub lockState lookup (real wiring lands in G1.7)

- [x] [AGENT] P0. Add `lib/visibility/use-tile-lock-state.ts` — today returns `"unlocked"` for every tile; G1.7 will
      replace the body with a restriction-profile lookup.
- [x] [AGENT] P0. Update ServiceTile render sites to consume `useTileLockState(tileId)` → `lockState` prop. Wired via
      `ServiceCardWrapper` inside `app/(platform)/dashboard/page.tsx` — the wrapper merges the profile hook with the
      existing entitlement-derived `locked` signal and passes `lockState` to the shared `<ServiceTile>`.

### Phase 3D — Visual polish + a11y

- [x] [AGENT] P0. Padlock tooltip uses the site's existing tooltip primitive (never `title=` attribute). Uses
      `@/components/ui/tooltip` (Radix).
- [x] [AGENT] P0. `aria-label` includes "locked — request access" for screen readers.
- [x] [AGENT] P0. Keyboard focus lands on the tile but Enter/Space do not navigate (no-op). Tile renders as
      `role="button"` with `tabIndex={0}`; `onKeyDown` preventDefaults Enter/Space.

### Phase 3E — Verify + QG

- [x] [SCRIPT] P0. UI vitest green (`CI=true npm test -- --run`) — tests/services/service-tile.test.tsx: 9/9 green; full
      suite 40 files / 348 tests green (the only pre-existing 2 api.integration failures are unrelated — they require a
      live API server on :8030 and fail the same way on main).
- [x] [SCRIPT] P0. UI smoke build green — Next.js, not Vite; `npx tsc --noEmit` shows zero errors in G1.3 files (single
      pre-existing TS error in `app/(platform)/services/execution/tca/page.tsx` is unrelated).
- [x] [SCRIPT] P0. UI QG green (`scripts/quality-gates.sh`). Only failures are the pre-existing api.integration tests
      requiring a live :8030 server.
- [x] [AGENT] P0. Playwright spec `refactor-g1-3-locked-visible.spec.ts` green on tier-1 dev — 6/6 pass in 13.9s against
      `localhost:3100`.

## Critical files to be modified

- `unified-trading-system-ui/components/services/ServiceTile.tsx` (or equivalent — confirm path in Phase 3A) — MODIFY
  (add `lockState` prop + render branches)
- `unified-trading-system-ui/components/architecture-v2/LockState.tsx` — POSSIBLY REUSE as-is
- `unified-trading-system-ui/lib/visibility/use-tile-lock-state.ts` — NEW (stub)
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-3-locked-visible.spec.ts` — NEW
- `unified-trading-system-ui/tests/services/service-tile.test.tsx` — NEW (vitest unit)

## Execution DAG

```
3A (audit)  →  3B (implement) + 3C (stub hook)  [sequential within each]  →  3D (polish)  →  3E (QG)
```

## Verification

1. `<ServiceTile lockState="padlocked-visible">` renders padlock + tooltip + disabled click — verified by vitest unit +
   Playwright.
2. `<ServiceTile lockState="hidden">` returns null — no DOM node rendered.
3. `<ServiceTile lockState="unlocked">` preserves today's behaviour (no regression).
4. `data-lock-state` attribute is present on every rendered tile (Playwright-queryable).
5. UI QG green.
6. Playwright spec green on both dev + staging-like (tier-1) configurations.

## Handoff

Unblocks:

- **G1.7 restriction-profile engine** — wires the stubbed `use-tile-lock-state.ts` to real profile lookups.
- **G1.10 questionnaire** — the question answers drive the profile that drives the lockState.
- **G1.13 upsell tempt-logic** — the padlocked tile is the surface where the overlay appears on hover.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100`
(tier-0 static) through MCP Playwright tools — navigate to the services portal with different persona seeds (admin
unlocks all; prospect-im has some padlocks), verify padlock visible + tooltip + disabled click. Iterate until every
persona × tile combination behaves per the restriction profile matrix.

**Durable spec for CI:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-3-locked-visible.spec.ts` —
must:

1. Seed a `prospect-im` persona via `tests/e2e/playbooks/seed-persona.ts` (should see padlocks on adjacent-service
   tiles).
2. Also seed an `admin` persona and assert all tiles are unlocked (admin sees all).
3. Walk canonical click-path: landing → dashboard → services portal.
4. Assert each tile has `data-lock-state` attribute; assert padlocked tiles have the padlock icon + tooltip copy +
   `aria-disabled="true"` + do NOT navigate on click.
5. Assert visibility-slicing vs G1.6 `access_control(user, route, item, phase)` formula once G1.6 lands; until then,
   stub the lookup against the seeded persona's expected restriction profile.
6. Include orphan-reachability assertion — no LOCKED-VISIBLE tile should point at a URL-only-reachable route (would
   defeat the discovery affordance).
7. Wired into `scripts/quality-gates.sh` Playwright step.
8. Assert dev-vs-staging parity: same persona → same tile states in both environments (the spec runs in dev; staging
   runs through CI against `odum-research.co.uk`).

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G1.3 (Wave A, standalone — no
dependencies on other G1 items).**

---

You are executing **Refactor G1.3 — LOCKED-VISIBLE UI service-tile mode** for the Unified Trading System at Odum
Research. Wave A; parallelisable with 1.1, 1.5, 1.9, 1.12, 1.14-markdown.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm
git checkout live-defi-rollout && git pull
ls /codex/14-playbooks/_ssot-rules/06-show-dont-show-discipline.md
ls /codex/14-customer-journeys/playbook-concepts/visibility-slicing.md
ls /codex/14-playbooks/demo-ops/demo-restriction-profiles.md
ls ../unified-trading-system-ui/components/architecture-v2/LockState.tsx
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 3A through 3E of this plan:
`plans/active/refactor_g1_3_locked_visible_ui_service_tile_mode_2026_04_20.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 7.

### Deliverables

- Modified: `components/services/ServiceTile.tsx` (or equivalent)
- New: `lib/visibility/use-tile-lock-state.ts` (stub for G1.7 to replace)
- New: `tests/services/service-tile.test.tsx` (vitest unit)
- New: `tests/e2e/playbooks/refactor/refactor-g1-3-locked-visible.spec.ts`

### Dev / staging parity requirement (verbatim — REQUIRED)

Demo flows MUST behave identically in dev and staging. Same persona set, same `lockState` computation, same padlock
affordance, same tooltip copy. The only permitted differences are:

- Dev: mock auth via `demo-provider.ts` + localStorage; `NEXT_PUBLIC_MOCK_API=true`.
- Staging: Firebase staging project (`odum-research.co.uk`); same personas as real Firebase users;
  `NEXT_PUBLIC_MOCK_API=false`.
- Prod: Firebase prod project (`odum-research.com`); real paying clients.

Any refactor that diverges dev from staging beyond those is a rule-03 violation and fails verification.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
Playwright tools during dev to verify padlocked tiles render the padlock + tooltip + disabled click across multiple
persona seeds. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-3-locked-visible.spec.ts` — seed `prospect-im` +
`admin` personas via `tests/e2e/playbooks/seed-persona.ts`, walk the canonical click-path, assert `data-lock-state` +
padlock + `aria-disabled`, assert visibility-slicing vs G1.6 `access_control` formula (stub until G1.6 lands), include
orphan-reachability assertion, wire into `scripts/quality-gates.sh`, assert dev-vs-staging parity.

### Commit strategy

UI repo:

```
cd unified-trading-system-ui
bash scripts/quickmerge.sh "refactor(ui): G1.3 — LOCKED-VISIBLE service-tile mode" --agent
```

Fallback if quickmerge is blocked:

```
git add components/ lib/visibility/ tests/
git commit -m "refactor(ui): G1.3 — LOCKED-VISIBLE service-tile mode"
git push origin live-defi-rollout
```

### Success criteria

1. ✅ `ServiceTile` accepts `lockState` prop with closed 3-value enum.
2. ✅ padlocked-visible renders padlock + disabled click + tooltip.
3. ✅ Today's unlocked behaviour preserved (no regression).
4. ✅ UI QG green.
5. ✅ Playwright spec green on tier-1 dev.
6. ✅ Dev-vs-staging parity verified.
7. ✅ Commit SHA pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT wire the real restriction-profile lookup here — G1.7 owns that. Stub + leave a comment pointing to G1.7.
- Do NOT introduce a fourth state — closed enum.
- Do NOT diverge dev from staging — parity rule is hard.
- Do NOT skip the MCP Playwright dev verification.

### Report back

- ServiceTile path + before/after LOC.
- Persona × tile visibility matrix (from Playwright run).
- Playwright spec path + pass status.
- Commit SHA pushed to live-defi-rollout.
- Any gaps or open questions for the user.
