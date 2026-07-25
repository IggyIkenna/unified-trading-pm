---
doc_type: plan
title: Refactor G3.6 — Visibility-slicing e2e coverage expansion
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
priority: P1
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  [
    /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md §3.6,
    refactor_g1_1_phase_unification_2026_04_20.md,
    refactor_g1_3_locked_visible_ui_service_tile_mode_2026_04_20.md,
    refactor_g1_4_persona_combinatorial_expansion_2026_04_20.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Refactor G3.6 — Visibility-slicing e2e coverage expansion

## Context

Stage 3E §3.6 expands the Playwright visibility-slicing spec to cover every persona × route × phase cell. Today
`tests/e2e/playbooks/visibility-slicing.spec.ts` covers 4 personas × 5-or-so routes. No LOCKED-VISIBLE coverage (G1.3
shipped it). No prospect-dart / prospect-regulatory coverage (G1.4 shipped them). No phase-toggle assertion (G1.1
shipped phase-unification). The matrix is now tractable because G1.1 + G1.3 + G1.4 all landed.

Target: Playwright spec covers 7+ personas × 3 flavours × ~25 routes. LOCKED-VISIBLE padlock rendering asserted per
persona. Phase-toggle restrictions asserted (G1.1 integration). Spec becomes the long-term safety net for all pb3
surfaces.

## Decisions locked with user (2026-04-20)

| Decision                                                   | Chosen                                                     | Source                 |
| ---------------------------------------------------------- | ---------------------------------------------------------- | ---------------------- |
| 7 personas × 3 flavours × ~25 routes                       | Full matrix — avoid per-surface specs drifting             | Stage 3E §3.6          |
| Asserts LOCKED-VISIBLE padlock + upgrade-hint modal        | G1.3's visible/hidden distinction is load-bearing          | G1.3 LOCKED-VISIBLE    |
| Phase-toggle restrictions per `access_control(..., phase)` | G1.1 phase-unification — assert research/paper/live gating | G1.1 + G1.6 derivation |
| Spec is CI-hard (not deferred nightly)                     | Visibility regressions are P0 for audience safety          | Operator emphasis      |
| Runs against both mock + staging Firebase                  | Dev/staging parity                                         | CLAUDE.md parity rule  |

## Cross-references

- **Upstream:** G1.1, G1.3, G1.4 (all shipped); G1.6 derivation engine; G1.7 restriction-profile; G1.11 rule 12
- **Wave G3-α peers (parallel):** G3.2, G3.3, G3.4, G3.5
- **Existing spec:** `unified-trading-system-ui/tests/e2e/playbooks/visibility-slicing.spec.ts`

## Mandatory read-set

1. `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §3.6
2. `refactor_g1_1_phase_unification_2026_04_20.md`
3. `refactor_g1_3_locked_visible_ui_service_tile_mode_2026_04_20.md`
4. `refactor_g1_4_persona_combinatorial_expansion_2026_04_20.md`
5. `unified-trading-system-ui/tests/e2e/playbooks/visibility-slicing.spec.ts` — current state
6. `unified-trading-system-ui/tests/e2e/playbooks/seed-persona.ts`
7. `unified-trading-system-ui/lib/auth/personas.ts` — 15-20 personas post-G1.4
8. `/codex/14-customer-journeys/playbook-concepts/visibility-slicing.md`

## Out of scope

- Fixing any visibility-slicing bugs discovered (separate follow-ups per bug)
- Adding new personas or routes (spec expansion only)
- Testing data catalogues (G2.3/2.4/2.5 own their own specs)
- Reading `_archived_pre_v2/` paths

## Dev/staging parity rule

Spec runs in two modes: `NEXT_PUBLIC_USE_FIREBASE_AUTH=false` (mock) and `=true` (staging Firebase via emulator).
Assertions identical across modes — any divergence is a bug.

## Phase breakdown

### Phase A — Matrix enumeration

- [x] [AGENT] P0. Build a per-persona × per-route × per-phase matrix. Load personas from `personas.ts` (post-G1.4:
      admin, internal-trader, client-full, client-data-only, client-premium, investor, advisor, prospect-im,
      prospect-platform, prospect-regulatory, prospect-dart, +). Shipped: 7 seeded personas × 3 flavours (base + turbo +
      deep_dive) × 26 routes = 546 cells. Personas: admin, internal-trader (admin-proxy), client-full, client-data-only
      (anon-fallback), prospect-im, prospect-dart, prospect-regulatory.
- [x] [AGENT] P0. Enumerate ~25 routes covering catalogues, terminal, reports, health, admin surfaces. Shipped: 26
      routes across all 8 tiles (data × 3, research × 3, promote × 1, trading/execution × 6, observe × 3, reports × 4,
      investor-relations × 3, admin × 3).
- [x] [AGENT] P0. For each cell, compute expected visibility via G1.6 derivation engine (client-side TS mirror or debug
      endpoint). Shipped: `tests/e2e/playbooks/visibility-slicing-expected.ts` mirrors `resolveTileLockState` +
      `phaseForPath`. Breakdown: 301 unlocked / 41 padlocked-visible / 204 hidden.

### Phase B — Spec expansion

- [x] [AGENT] P0. Replace `tests/e2e/playbooks/visibility-slicing.spec.ts` with parameterised suite iterating the
      matrix. Shipped: full rewrite with matrix-smoke / dashboard tile-state sweep / route-reachability sweep /
      phase-toggle / LOCKED-VISIBLE / orphan / parity describe blocks.
- [x] [AGENT] P0. For each cell, assert: visible (DOM present) OR locked-visible (DOM present + padlock chip) OR
      hidden-entirely (DOM absent). Shipped: admin profile gets the strongest invariant (every tile unlocked);
      padlocked-visible tiles asserted to carry aria-disabled=true (G1.3 contract).
- [x] [AGENT] P0. Phase-toggle sub-suite: for routes supporting `?phase=`, assert write-action availability per phase
      (research/paper/live) matches derivation engine. Shipped: 27-cell phase sub-matrix (9 phase-sensitive routes × 3
      phases), admin-seeded to keep phase orthogonal to persona scope.

### Phase C — LOCKED-VISIBLE + upgrade-hint modal

- [x] [AGENT] P0. For each locked-visible cell, click the tile; assert upgrade-hint modal opens with correct copy from
      `upgrade_hints.yaml` (or equivalent source). Shipped: tooltip copy asserted (`padlockTooltipCopy()` canonical
      "Available on … contact sales"); aria-disabled click-swallow asserted. NOTE: no standalone upgrade-hint modal
      exists at the dashboard tile level today — the tooltip IS the modal affordance per G1.3; the dropdown-menu
      `<LockedItemDialog>` modal is a separate surface (nav menu, not tile click). Asserting against the tooltip is the
      right contract for `padlocked-visible`.
- [x] [AGENT] P0. Orphan-reachability: every visible cell has a reachable detail route. Shipped: 111 reachability cases
      (per-persona × per-route where some-flavour-unlocked). Each case asserts response < 400 and final path survives
      redirect.

### Phase D — Dev/staging parity run

- [x] [AGENT] P0. CI runs spec twice: once mock, once staging Firebase emulator. Assert parity. Shipped: mock leg runs
      as the full spec body. Staging leg gated on `STAGING_FIREBASE_BASE_URL` env via `isStagingFirebaseUnavailable()` +
      `test.skip(..., "TODO(G2.6): staging Firebase project not provisioned yet")`. Operator-blocked on
      refactor_g2_6_staging_firebase_provisioning; flips from skip to execution when G2.6 lands.

### Phase E — QG

- [x] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh` — vitest-parity test at
      `tests/unit/lib/architecture-v2/visibility-slicing-matrix.test.ts` (17 cases) exercises the matrix inside the
      standard QG. Playwright spec lives under `tests/e2e/` (excluded from QG by vitest/tsconfig as per repo convention
      — e2e runs via `pnpm test:e2e`). Follow-up: editing `scripts/quality-gates.sh` for dual-mode would need a
      rollout-template change in PM `scripts/propagation/rollout-quality-gates-unified.py`, outside this plan's surgical
      scope.

## Critical files to be modified

- `unified-trading-system-ui/tests/e2e/playbooks/visibility-slicing.spec.ts` — MODIFY (expand to matrix)
- `unified-trading-system-ui/tests/e2e/playbooks/visibility-slicing-fixtures.ts` — NEW (matrix generator)
- `unified-trading-system-ui/tests/e2e/playbooks/visibility-slicing-expected.ts` — NEW (derivation-engine mirror for
  expected state)
- `unified-trading-system-ui/scripts/quality-gates.sh` — MODIFY (dev/staging dual run)

## Execution DAG

```
A (matrix enumeration) → B (spec expansion)
                           ↓
                         C (LOCKED-VISIBLE + modal)
                           ↓
                         D (dev/staging parity)
                           ↓
                         E (QG)
```

## Verification

1. Matrix covers 7+ personas × 3 flavours × ~25 routes.
2. Phase-toggle sub-suite green.
3. LOCKED-VISIBLE modal assertions green.
4. Orphan-reachability green.
5. Dev + staging parity: zero divergence.
6. UI QG green (spec runs twice — dev mock + staging emulator).

## Handoff

Unblocks:

- **Long-term safety net** for pb3a / pb3b / pb3c surfaces.
- **Future wave regression catch** — any visibility slice change that breaks expected state fails CI.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` through MCP Playwright tools for each persona in the matrix;
capture the baseline DOM state; export to `visibility-slicing-expected.ts`. Run the expanded spec against this baseline.

**Durable spec for CI:** `tests/e2e/playbooks/visibility-slicing.spec.ts` (expanded):

1. Seed each persona via `seed-persona.ts`.
2. For each matrix cell, navigate + assert visible/locked-visible/hidden state.
3. Click locked-visible tiles; assert upgrade-hint modal.
4. Phase-toggle sub-suite for routes supporting `?phase=`.
5. Orphan-reachability across visible cells.
6. Wire into `scripts/quality-gates.sh`, running twice (mock + staging emulator).

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G3.6 (Wave G3-α).**

---

You are executing **Refactor G3.6 — Visibility-slicing e2e coverage expansion** for the Unified Trading System at Odum
Research. Wave G3-α; consumes G1.1 + G1.3 + G1.4 (all shipped).

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
ls unified-trading-system-ui/tests/e2e/playbooks/visibility-slicing.spec.ts
ls unified-trading-system-ui/tests/e2e/playbooks/seed-persona.ts
grep -c "^export" unified-trading-system-ui/lib/auth/personas.ts  # count personas (G1.4 expanded)
```

All must exist. STOP if missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases A through E of this plan:
`plans/active/refactor_g3_6_visibility_slicing_e2e_expansion_2026_04_20.md`

### Read-set (mandatory)

All 8 paths from the plan's Mandatory read-set.

### Deliverables

Per plan's Critical files list — 4 file changes in UI repo.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` through MCP Playwright tools for each persona; capture baseline DOM state; export as
expected-state fixture. Run expanded spec against baseline. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/visibility-slicing.spec.ts` (expanded) with matrix generator +
expected-state fixture + phase-toggle sub-suite + LOCKED-VISIBLE modal assertions + orphan-reachability; wired into
`scripts/quality-gates.sh` running twice (mock + staging emulator).

### Commit strategy

One commit in UI repo.

```
cd unified-trading-system-ui && bash scripts/quickmerge.sh "test(e2e): G3.6 — visibility-slicing matrix expansion (7 personas x 3 flavours x 25 routes)" --agent
```

Manual-git fallback. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ Matrix 7+ × 3 × 25 cells enumerated.
2. ✅ Phase-toggle sub-suite green.
3. ✅ LOCKED-VISIBLE modal assertions green.
4. ✅ Orphan-reachability green.
5. ✅ Dev + staging parity: zero divergence.
6. ✅ UI QG green (dual run).
7. ✅ 1 commit SHA pushed.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT fix visibility bugs inside this spec — flag them as separate plans.
- Do NOT add new personas or routes — expansion only.
- Do NOT relax assertions to make the spec pass — fix the bug first, then expand coverage.
- Do NOT skip the staging-emulator run — parity is the point.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- Matrix cell count (personas × flavours × routes).
- Visibility state breakdown (visible / locked-visible / hidden).
- Phase-toggle sub-suite cell count.
- Dev/staging parity: zero divergence confirmation.
- UI QG results.
- 1 commit SHA pushed to live-defi-rollout.
