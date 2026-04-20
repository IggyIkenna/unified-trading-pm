---
title: Refactor G1.1 — Phase unification (no forked research / paper / live UIs)
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.1
  - codex/14-playbooks/_ssot-rules/03-same-system-principle.md
  - codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md
# Sibling refactor plans (Wave A):
#   refactor_g1_3_locked_visible_ui_service_tile_mode_2026_04_20.plan.md
#   refactor_g1_5_ml_catalogue_broken_hrefs_cleanup_2026_04_20.plan.md
#   refactor_g1_9_codex_scope_registry_2026_04_20.plan.md
#   refactor_g1_12_public_site_ia_and_briefings_polish_2026_04_20.plan.md
#   refactor_g1_14_presentation_deck_refresh_2026_04_20.plan.md
# Downstream consumer (Wave C): refactor_g1_6_derivation_engine... (consumes `phase` prop in access_control formula)
---

# Refactor G1.1 — Phase unification (no forked research / paper / live UIs)

## Context

Stage 3E §1.1 mandates that research, paper, and live trading views must share one component tree; the only thing that
branches is the data-source binding per phase. This flows from rule 03 same-system-principle sub-claims (b)–(e) and is
operationalised in `codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md`. Today's UI has partial forking (separate
research/trading lifecycle-nav sections and some duplicated service-tabs); this refactor eliminates every fork and
introduces a `phase: "research" | "paper" | "live"` prop that every phased component accepts, with pure data-source
rewiring inside — never a cloned component tree.

## Decisions locked with user (2026-04-20)

| Decision                                                            | Chosen                                                                                                      | Source                                |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Phase is a prop, never a separate component tree                    | `phase: "research" \| "paper" \| "live"` threaded through every phased component                            | rule 03 sub-claim (b) + stage-3e §1.1 |
| Data-source binding branches, DOM/JSX does not                      | Use a `usePhaseBinding(phase)` hook that swaps the fetcher; component re-renders with new data but same JSX | Kickoff §1.1 restated                 |
| Catalogue + terminal + observe are phase-toggled over the same tree | No cloned `/research/...` vs `/trading/...` page trees for the same conceptual surface                      | stage-3e §1.1                         |

## Cross-references

- **Sibling Wave A plans:** [refactor_g1_3](refactor_g1_3_locked_visible_ui_service_tile_mode_2026_04_20.plan.md),
  [refactor_g1_12](refactor_g1_12_public_site_ia_and_briefings_polish_2026_04_20.plan.md)
- **Downstream consumer (Wave C):** refactor_g1_6_derivation_engine... — `access_control(user, route, item, phase)`
  formula takes phase as an input; this refactor is the UI-side producer.
- **Rules:** `_ssot-rules/03-same-system-principle.md` (sub-claims b–e), `_ssot-rules/06-show-dont-show-discipline.md`
- **Strategy v2 parity spec:** `codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md`
- **Parent stage plan:** `plans/active/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md` §3E

## Mandatory read-set

1. `codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.1
2. `codex/14-playbooks/_ssot-rules/03-same-system-principle.md`
3. `codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md`
4. `unified-trading-system-ui/components/shell/lifecycle-nav.tsx`
5. `unified-trading-system-ui/components/shell/service-tabs.tsx`
6. `unified-trading-system-ui/components/shell/spaces-nav-sections.tsx`
7. `unified-trading-system-ui/lib/lifecycle-route-mappings.ts`
8. Any existing `app/services/research/**` + `app/services/trading/**` page pairs that are the same conceptual surface
   (audit first; enumerate in Phase 1A output)

## Out of scope

- Server-side pricing-engine phase handling (that lives in refactor_g1_6).
- Adding new phases beyond research / paper / live — the enum is closed.
- Changing route slugs for top-level services (that's refactor_g1_12).
- Archiving forked pages — use delete + redirect once the unified tree is shipped, never leave stale forks.
- Observe-phase metric-generation infra (scope of a later G2 item).

## Phase breakdown

### Phase 1A — Audit forks (read-only)

- [ ] [AGENT] P0. Enumerate every page pair under `app/` where the same conceptual surface exists in both `research/`
      and `trading/` trees (or equivalents). Write audit to `/tmp/g1_1_fork_audit.md`.
- [ ] [AGENT] P0. For each forked pair, classify: true duplicate / near-duplicate (diff < 30 LOC) / intentional split
      (e.g. research = catalogue view, trading = terminal view).
- [ ] [AGENT] P0. Identify every component under `components/shell/` that branches on
      `pathname.startsWith("/services/research")` vs `/services/trading/` — these become `phase`-prop sites.

### Phase 1B — Introduce `phase` prop + `usePhaseBinding` hook

- [ ] [AGENT] P0. Add `type Phase = "research" | "paper" | "live"` to `lib/phase/types.ts` (new file).
- [ ] [AGENT] P0. Add `usePhaseBinding(phase: Phase)` hook at `lib/phase/use-phase-binding.ts` — returns
      `{ fetcher, baseUrl, wsUrl }` swapping per phase.
- [ ] [AGENT] P0. Thread `phase` prop through every phased component identified in 1A. Default prop value: infer from
      route segment (`/services/research/*` → `"research"`, etc.) via `usePhaseFromRoute()` helper.

### Phase 1C — Collapse forked page trees

- [ ] [AGENT] P0. For each true-duplicate pair, delete one side and add a redirect rule in `next.config.ts` pointing the
      deleted path to the surviving path with `?phase=<X>` query param (or route-segment binding).
- [ ] [AGENT] P0. For each near-duplicate pair, diff the two versions; port the delta into the survivor behind a
      `phase === "X"` conditional; delete the other.
- [ ] [AGENT] P0. For each intentional-split pair, add a doc comment explaining why a split is correct (e.g. catalogue
      vs terminal are distinct surfaces, not phases of the same surface) and leave untouched.

### Phase 1D — Verify + QG

- [ ] [SCRIPT] P0. Run `cd unified-trading-system-ui && CI=true npm test -- --run` — all vitest green.
- [ ] [SCRIPT] P0. Run `cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build` — smoke build green.
- [ ] [SCRIPT] P0. Run `cd unified-trading-system-ui && bash scripts/quality-gates.sh` — full gate green.
- [ ] [AGENT] P0. Run Playwright spec `refactor-g1-1-phase-unification.spec.ts` to verify every phased surface behaves
      identically under `?phase=research|paper|live` toggle with only data-source rebinding.

## Critical files to be modified

- `unified-trading-system-ui/lib/phase/types.ts` — NEW
- `unified-trading-system-ui/lib/phase/use-phase-binding.ts` — NEW
- `unified-trading-system-ui/lib/phase/use-phase-from-route.ts` — NEW
- `unified-trading-system-ui/components/shell/lifecycle-nav.tsx` — MODIFY (thread `phase` prop)
- `unified-trading-system-ui/components/shell/service-tabs.tsx` — MODIFY (thread `phase` prop)
- `unified-trading-system-ui/components/shell/spaces-nav-sections.tsx` — MODIFY (thread `phase` prop)
- `unified-trading-system-ui/lib/lifecycle-route-mappings.ts` — MODIFY (unify research/trading entries)
- `unified-trading-system-ui/next.config.ts` — MODIFY (add redirect rules)
- Forked page dirs under `app/services/` — DELETE per audit.
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-1-phase-unification.spec.ts` — NEW

## Execution DAG

```
1A (audit)  →  1B (introduce prop+hook)  →  1C (collapse forks)  →  1D (QG + Playwright)
```

Phases are strictly sequential — you cannot collapse before the prop/hook lands, and you cannot QG before collapse is
complete.

## Verification

1. `rg -n "pathname.startsWith\(['\"]/services/research" unified-trading-system-ui/` returns zero hits inside
   `components/shell/` (no route-prefix branching remains).
2. `rg -l "phase:\\s*Phase" unified-trading-system-ui/components/shell/` lists at least 3 files (prop successfully
   threaded).
3. Every fork identified in Phase 1A audit has exactly one of: (a) deletion + redirect, (b) port-delta + deletion, (c)
   doc-comment justifying intentional split.
4. UI QG passes (`scripts/quality-gates.sh`).
5. Playwright spec `refactor-g1-1-phase-unification.spec.ts` asserts identical DOM structure across phase toggles with
   only data-source differences.

## Handoff

Unblocks:

- **G1.6** — derivation engine can now consume `phase` in its `access_control` formula without ambiguity.
- **G2.x** — future observe-phase metric-generation can bind to the same component tree.
- **G2.x** — strategy-catalogue phase-toggle UX (observe vs terminal vs catalogue).

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3010` (UI dev server via `bash scripts/dev-tiers.sh --tier 1`) or
`:3100` (tier-0 static) through the MCP Playwright tools — navigate to each phased surface, toggle
`?phase=research|paper|live`, assert DOM structure matches via `browser_snapshot`. Iterate until every surface behaves.

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-1-phase-unification.spec.ts` — must:

1. Seed an `admin` persona via `tests/e2e/playbooks/seed-persona.ts` (admin sees all phases).
2. Walk the canonical click-path: landing → services portal → each phased surface → phase toggle.
3. Assert visibility-slicing against G1.6's `access_control(user, route, item, phase)` formula once G1.6 lands; until
   then, stub with a direct lookup against `lib/phase/use-phase-binding.ts` return values.
4. Include an orphan-reachability assertion — every surviving page MUST be reachable from the main nav (no
   URL-only-reachable surfaces introduced by the collapse).
5. Wired into `scripts/quality-gates.sh` Playwright step.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G1.1 (Wave A, standalone — no
dependencies on other G1 items).**

---

You are executing **Refactor G1.1 — Phase unification** for the Unified Trading System at Odum Research. This is Wave A
of the G1 refactor; it has no dependencies on other G1 items and can run in parallel with 1.3, 1.5, 1.9, 1.12,
1.14-markdown.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm
git checkout live-defi-rollout && git pull
ls codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md
ls codex/14-playbooks/_ssot-rules/03-same-system-principle.md
ls codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md
ls ../unified-trading-system-ui/components/shell/
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 1A through 1D of this plan:
`plans/active/refactor_g1_1_phase_unification_2026_04_20.plan.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 8.

### Deliverables

- New files: `lib/phase/types.ts`, `lib/phase/use-phase-binding.ts`, `lib/phase/use-phase-from-route.ts`
- Modified files: `components/shell/{lifecycle-nav,service-tabs,spaces-nav-sections}.tsx`,
  `lib/lifecycle-route-mappings.ts`, `next.config.ts`
- Deleted dirs: forked page pairs per Phase 1A audit
- New test: `tests/e2e/playbooks/refactor/refactor-g1-1-phase-unification.spec.ts`

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3010` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
Playwright tools during dev to verify every phased surface behaves identically under `?phase=research|paper|live` toggle
with only data-source rebinding. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-1-phase-unification.spec.ts` — it must seed the
admin persona via `tests/e2e/playbooks/seed-persona.ts`, walk the canonical click-path, assert visibility-slicing vs
G1.6 `access_control` formula (stub until G1.6 lands), include an orphan-reachability assertion, and wire into
`scripts/quality-gates.sh`.

### Commit strategy

UI repo (only repo touched):

```
cd unified-trading-system-ui
bash scripts/quickmerge.sh "refactor(ui): G1.1 — phase unification (no forked research/paper/live trees)" --agent
```

Fallback if quickmerge is blocked by unrelated WIP on live-defi-rollout:

```
cd unified-trading-system-ui
git add lib/phase/ components/shell/ lib/lifecycle-route-mappings.ts next.config.ts tests/e2e/playbooks/refactor/ app/
git commit -m "refactor(ui): G1.1 — phase unification (no forked research/paper/live trees)"
git push origin live-defi-rollout
```

### Success criteria

1. ✅ Every checkbox in Phases 1A–1D flipped to `- [x]`.
2. ✅ `rg "pathname.startsWith\\(['\\\"]/services/research" components/shell/` returns zero hits.
3. ✅ UI QG green (`scripts/quality-gates.sh`).
4. ✅ Playwright spec green on tier-1 dev.
5. ✅ Commit SHA pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT skip the MCP Playwright dev verification — spec alone is not enough; drive the live UI.
- Do NOT touch G2 or G3 items.
- Do NOT add new phases beyond `research | paper | live` — the enum is closed.
- Do NOT leave stale forked dirs — delete + redirect is the pattern.

### Report back

- Fork audit (from Phase 1A): table of N pairs with classifications.
- LOC delta (lines deleted vs added).
- Playwright spec path + pass status.
- Commit SHA pushed to live-defi-rollout.
- Any blockers or gaps flagged for the user.
