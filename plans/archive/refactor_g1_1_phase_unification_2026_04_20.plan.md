---
doc_type: plan
title: Refactor G1.1 — Phase unification (no forked research / paper / live UIs)
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
    /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.1,
    /codex/14-playbooks/_ssot-rules/03-same-system-principle.md,
    /codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Refactor G1.1 — Phase unification (no forked research / paper / live UIs)

## Context

Stage 3E §1.1 mandates that research, paper, and live trading views must share one component tree; the only thing that
branches is the data-source binding per phase. This flows from rule 03 same-system-principle sub-claims (b)–(e) and is
operationalised in `/codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md`. Today's UI has partial forking (separate
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
- **Strategy v2 parity spec:** `/codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md`
- **Parent stage plan:** `plans/active/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md` §3E

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.1
2. `/codex/14-playbooks/_ssot-rules/03-same-system-principle.md`
3. `/codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md`
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

- [x] [AGENT] P0. Enumerate every page pair under `app/` where the same conceptual surface exists in both `research/`
      and `trading/` trees (or equivalents). Write audit to `/tmp/g1_1_fork_audit.md`.
- [x] [AGENT] P0. For each forked pair, classify: true duplicate / near-duplicate (diff < 30 LOC) / intentional split
      (e.g. research = catalogue view, trading = terminal view).
- [x] [AGENT] P0. Identify every component under `components/shell/` that branches on
      `pathname.startsWith("/services/research")` vs `/services/trading/` — these become `phase`-prop sites.

### Phase 1B — Introduce `phase` prop + `usePhaseBinding` hook

- [x] [AGENT] P0. Add `type Phase = "research" | "paper" | "live"` to `lib/phase/types.ts` (new file).
- [x] [AGENT] P0. Add `usePhaseBinding(phase: Phase)` hook at `lib/phase/use-phase-binding.ts` — returns
      `{ fetcher, baseUrl, wsUrl }` swapping per phase.
- [x] [AGENT] P0. Thread `phase` prop through every phased component identified in 1A. Default prop value: infer from
      route segment (`/services/research/*` → `"research"`, etc.) via `usePhaseFromRoute()` helper.

### Phase 1C — Collapse forked page trees

- [x] [AGENT] P0. For each true-duplicate pair, delete one side and add a redirect rule in `next.config.ts` pointing the
      deleted path to the surviving path with `?phase=<X>` query param (or route-segment binding).
- [x] [AGENT] P0. For each near-duplicate pair, diff the two versions; port the delta into the survivor behind a
      `phase === "X"` conditional; delete the other.
- [x] [AGENT] P0. For each intentional-split pair, add a doc comment explaining why a split is correct (e.g. catalogue
      vs terminal are distinct surfaces, not phases of the same surface) and leave untouched.

### Phase 1D — Verify + QG

- [x] [SCRIPT] P0. Run `cd unified-trading-system-ui && CI=true npm test -- --run` — all vitest green.
- [x] [SCRIPT] P0. Run `cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build` — smoke build green.
- [x] [SCRIPT] P0. Run `cd unified-trading-system-ui && bash scripts/quality-gates.sh` — full gate green.
- [x] [AGENT] P0. Run Playwright spec `refactor-g1-1-phase-unification.spec.ts` to verify every phased surface behaves
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

**MCP Playwright during dev:** drive `localhost:3000` (UI dev server via `bash scripts/dev-tiers.sh --tier 1`) or
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
ls /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md
ls /codex/14-playbooks/_ssot-rules/03-same-system-principle.md
ls /codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md
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

Drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
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

## Micro-execution plan (sub-agent Phase 1)

Drafted 2026-04-20 in plan-mode — no code touched yet. Awaiting explicit re-entry approval before executing.

### Scope reality-check (read-only scan done during plan drafting)

- `next.config.ts` referenced in plan does NOT exist — file is actually `next.config.mjs` (lines 80–300 already contain
  a fully-wired `redirects()` block with 50+ entries). All Phase 1C redirect additions MUST land in `next.config.mjs`.
  Plan prose at line 91 + 115 + 236 is the only source of the incorrect `.ts` suffix; real file is `.mjs`. No re-point
  of the plan needed — deliverable spec in Critical Files is corrected inline in Phase 1C below.
- App-router tree is Next.js App Router with route groups: forks live under `app/(platform)/services/research/**` vs
  `app/(platform)/services/trading/**` (NOT a bare `app/services/`). Phase 1A audit path prefix is
  `app/(platform)/services/`.
- Forks short-list (confirmed via `ls` of both dirs, to be formalised in `/tmp/g1_1_fork_audit.md`):
  - `research/strategies/page.tsx` vs `trading/strategies/{page,[id],basis-trade,grid,model-portfolios,staked-basis}` —
    **intentional split** (research = catalogue enumeration, trading = live book per strategy). Keep.
  - `research/execution/page.tsx` vs `trading/terminal/`, `trading/book/`, `trading/orders/`, `trading/positions/` —
    **intentional split** (research = execution-policy config, trading = live venue terminal). Keep with doc-comment.
  - `research/strategy/catalog/` (IM catalog) vs `strategy-catalogue/` top-level service — already split; not a phase
    fork. Keep.
  - `research/overview/` vs `trading/overview/` — **intentional split** (research landing vs trading desk landing).
  - No true-duplicate page trees detected in the scan. Audit output will likely classify all pairs as intentional splits
    (doc-comment only) or near-duplicates (port-delta + consolidation). No deletions expected.
- Shell-component branch sites (rg-confirmed):
  - `components/shell/lifecycle-nav.tsx` lines 104–112 — entitlement routing branching on
    `path.startsWith("/services/research")` / `/services/trading` / `/services/execution` — **must become phase-aware**
    via `usePhaseFromRoute()` output.
  - `components/shell/service-tabs.tsx` and `lib/lifecycle-route-mappings.ts` — both hard-code parallel
    `/services/research/*` and `/services/trading/*` tab definitions. Phase 1B must thread `phase` prop so each tab
    block can be emitted by a single data-driven generator with a phase switch (or keep parallel tab lists but resolve
    their target URLs through `usePhaseBinding(phase)`).
  - `components/shell/spaces-nav-sections.tsx` line 92 — single static `/services/research/strategy/catalog` link. Must
    be replaced with a phase-aware link that resolves via `usePhaseBinding` or at minimum documents why a static link is
    correct (catalogue is phase-agnostic IM surface).
  - `components/shell/breadcrumbs.tsx`, `trading-vertical-nav.tsx`, `notification-bell.tsx`, `command-palette.tsx` also
    reference `/services/research` and/or `/services/trading` — Phase 1A audit will classify each as either (a)
    phase-branching (must thread `phase`) or (b) static link (leave as-is, doc-comment).

### Files × line ranges × commit sequence

All edits land in `unified-trading-system-repos/unified-trading-system-ui`. No other repo touched.

**Commit 1 — Phase 1A audit artefact (read-only, no code change)**

- New file: `/tmp/g1_1_fork_audit.md` (NOT committed — scratch only; referenced by audit body embedded in commit 2
  alongside phase primitives).

**Commit 2 — Phase 1B primitives (new `lib/phase/` package; ZERO call-site changes)**

- New: `lib/phase/types.ts` (≤20 LOC) — closed enum `type Phase = "research" | "paper" | "live"` + `PHASES` tuple +
  narrowing `isPhase(x): x is Phase`.
- New: `lib/phase/use-phase-from-route.ts` (≤40 LOC) — `usePhaseFromRoute(): Phase` hook reading `usePathname()` and
  returning `research` for `/services/research/**`, `live` for `/services/trading/**` + `/services/execution/**`,
  default `research`. Paper phase is opt-in via `?phase=paper` querystring (read through `useSearchParams`).
- New: `lib/phase/use-phase-binding.ts` (≤60 LOC) — `usePhaseBinding(phase: Phase)` returns
  `{ phase, fetcher, baseUrl, wsUrl, resolvePath }` where `resolvePath(segment)` maps a phase-agnostic segment
  (`"/strategy/overview"`) to a fully-qualified phased URL (`/services/research/strategy/overview` for research,
  `/services/trading/strategy/overview` for live, `/services/trading/strategy/overview?phase=paper` for paper).
- Unit tests (vitest): `lib/phase/__tests__/phase.spec.ts` — narrowing, route-inference, `resolvePath` matrix.
- **Commit message:** `refactor(ui): G1.1 phase-B introduce closed Phase enum + usePhaseBinding hook`
- **Intended state after commit:** phase primitives exist but are NOT wired into any consumer; app behaviour unchanged;
  vitest green; build green.

**Commit 3 — Phase 1B thread (consumers accept `phase` prop; no route-string branching in shell)**

- Modify `components/shell/lifecycle-nav.tsx`:
  - Lines 87 + 139–140: add `const phase = usePhaseFromRoute();` next to `const pathname = usePathname() || "";`.
  - Lines 102–113 (`isItemAccessible`): keep entitlement gates but replace the raw
    `path.startsWith("/services/research")` checks with a derivation from the route's phase-aware mapping: compute
    `const itemPhase = phaseForPath(item.path)` via a small helper and drop the string-prefix branching on the render
    side. (The shell still needs to know which entitlement gate to apply — that's metadata on the route, not a shell
    responsibility. Move the entitlement predicate into `lib/lifecycle-route-mappings.ts` as a `requiredEntitlement`
    field on each mapping.)
  - NO JSX/DOM change — component tree identical pre/post.
- Modify `components/shell/service-tabs.tsx`:
  - Currently stateless — prop signature already takes `tabs: ServiceTab[]` from callers. Add a `phase?: Phase` prop
    - thread it through `TabRow` for use in `data-phase` attribute (for Playwright assertions). No URL rewriting here —
      URL rewriting happens upstream in the callers (research/trading layouts) via `usePhaseBinding`.
- Modify `components/shell/spaces-nav-sections.tsx`:
  - Line 92: `href="/services/research/strategy/catalog"` — this is the IM strategy catalogue entry point, which is
    phase-agnostic (it's a _catalogue_ of strategies across all phases). Add inline doc-comment stating the split is
    intentional-catalogue, not phase-forked; no code change.
- Modify `lib/lifecycle-route-mappings.ts`:
  - Lines 17–297 (research routes) + lines 196–297 (trading routes): add `phase: Phase` metadata field to each mapping
    so consumers can bind without string-prefix parsing.
  - Add `requiredEntitlement?: string | TradingEntitlement` field so `lifecycle-nav.tsx` no longer needs path-string
    branching for entitlement gating.
- Modify `components/shell/breadcrumbs.tsx`, `trading-vertical-nav.tsx`, `notification-bell.tsx`, `command-palette.tsx`:
  - For each `startsWith("/services/research")` / `startsWith("/services/trading")` occurrence, replace with
    `phaseForPath(pathname) === "research"` / `=== "live"` using the new helper from
    `lib/phase/use-phase-from-route.ts`.
  - No DOM change.
- Tests: extend `lib/phase/__tests__/phase.spec.ts` with route-mapping coverage + add component smoke spec for
  `lifecycle-nav` asserting `data-phase` attribute flips when pathname changes.
- **Commit message:** `refactor(ui): G1.1 phase-B thread Phase prop through shell (no DOM change)`

**Commit 4 — Phase 1C redirects + fork-collapse (DELETE only where audit classifies as true-duplicate)**

- Modify `next.config.mjs` (NOT `.ts`) within the existing `redirects()` block (~line 80–300): add `?phase=X`-preserving
  rules ONLY for forks that the Phase 1A audit classifies as true-duplicate. Current scan suggests 0 true-duplicate
  pairs — so this commit may be a no-op on `next.config.mjs`. Still run it as its own commit so the intent is
  documentable.
- Delete forked page dirs per audit — **expected to be empty set** based on current scan.
- Add doc-comments at the top of `app/(platform)/services/research/page.tsx`, `app/(platform)/services/trading/page.tsx`
  (and research vs trading overview/strategies/execution entry points) stating why each is an intentional split, not a
  phase fork.
- **Commit message:** `refactor(ui): G1.1 phase-C doc intentional splits + (redirects if any true-dup)` — message is
  adaptive based on audit outcome.

**Commit 5 — Phase 1D Playwright durable spec + QG wiring**

- New: `tests/e2e/playbooks/refactor/refactor-g1-1-phase-unification.spec.ts` — mirrors existing
  `research-and-documentation.spec.ts` shape. Must:
  1. `import { seedPersona } from "../seed-persona";` — seed `admin`.
  2. Walk canonical click-path landing → services portal → `/services/research/strategies` →
     `/services/trading/strategies` → assert identical component-tree roots via
     `expect(page.locator('[data-testid="phase-root"]')).toBeVisible()` and `getAttribute("data-phase")` flips from
     `research` → `live`.
  3. Assert visibility-slicing stub vs `usePhaseBinding` return values (G1.6 replaces with real `access_control` formula
     when it ships).
  4. Orphan-reachability: for every `/services/research/*` page reached by the crawl, assert it's reachable from main
     nav (no URL-only pages).
- Wire into `scripts/quality-gates.sh` Playwright step — check existing script first; if Playwright step is already
  generic (`npx playwright test`), no edit needed; if per-spec-listed, add the new spec filename.
- **Commit message:** `refactor(ui): G1.1 phase-D Playwright durable spec + QG wiring`

**Commit 6 — Final: quickmerge (two-pass)**

- Pass 1: `cd unified-trading-system-ui && bash scripts/quality-gates.sh` — full gate local.
- Pass 2:
  `bash scripts/quickmerge.sh "refactor(ui): G1.1 — phase unification (no forked research/paper/live trees)" --agent`.
- If WIP on live-defi-rollout blocks quickmerge, fall back to manual `git push origin live-defi-rollout` per plan's
  Commit strategy fallback.

### Playwright assertions (MCP dev loop + durable spec)

- **MCP dev loop** (pre-spec iteration on `localhost:3000` via `bash scripts/dev-tiers.sh --tier 1`):
  1. `browser_navigate` → `http://localhost:3000/services/research/strategies` → `browser_snapshot` → record DOM tree +
     `data-phase` attribute.
  2. `browser_navigate` → `http://localhost:3000/services/trading/strategies` → `browser_snapshot` → diff DOM tree:
     should be IDENTICAL modulo data-bound content (rows, counters). Only `data-phase` should flip.
  3. `browser_navigate` → `http://localhost:3000/services/research/strategies?phase=paper` → `browser_snapshot` →
     `data-phase="paper"`, same tree.
  4. Iterate until every phased surface from the audit behaves this way.
- **Durable spec assertions** (in `refactor-g1-1-phase-unification.spec.ts`):
  - `expect(getAttribute("[data-testid='phase-root']", "data-phase")).toBe("research")` after navigating research URL.
  - `expect(getAttribute("[data-testid='phase-root']", "data-phase")).toBe("live")` after navigating trading URL.
  - `expect(tree.snapshot()).toEqualForStructure(researchTree.snapshot())` — structural equality modulo data values.
  - Orphan-reachability: crawl main nav, collect reachable paths, assert superset of URLs visited in step 1.

### Guardrails (echoed from plan's "What NOT to do")

- No `_archived_pre_v2/` references.
- No `git reset --hard` / `git push --force`.
- No `--dep-branch`.
- No cherry-picking around unrelated WIP on `live-defi-rollout`.
- No skipping MCP Playwright dev loop.
- No touching G2/G3.
- No new phases beyond `research | paper | live`.
- No stale forked dirs left behind.

### Unresolved questions for operator approval

1. **Paper phase URL convention** — plan says `?phase=<X>` query param OR "route-segment binding" (line 93). The
   micro-plan proposes `research`/`live` as distinct route prefixes + `?phase=paper` as a query-param opt-in riding on
   the live tree (paper is _live execution with matching-engine fills_, not a separate service). Operator: confirm OR
   specify a dedicated `/services/paper/**` route prefix instead. **Default if no answer: `?phase=paper` on live
   prefix.**
2. **Audit outcome expectation** — current reconnaissance suggests all research/trading page pairs are intentional
   splits (catalogue vs terminal etc.), not phase forks. Expected deletions: 0. Expected redirects: 0. Operator: if you
   believe a specific pair IS a true duplicate that should collapse, name it now so Phase 1C can plan the deletion
   explicitly; otherwise proceed with "doc-only" Phase 1C.
3. **`lifecycle-route-mappings.ts` schema extension** — adding `phase` + `requiredEntitlement` fields is a breaking
   schema change for any external consumer that reads this object.
   `rg -n "lifecycle-route-mappings" unified-trading-system-ui/` will enumerate consumers before committing to the
   extension. If consumers resist the schema change, fallback is to keep the mapping dumb and introduce a separate
   `lib/phase/route-phase-registry.ts` side-table.
4. **MCP Playwright dev server** — plan mandates `localhost:3000` via `bash scripts/dev-tiers.sh --tier 1`, but port
   3010 is the non-standard dev port for tier-1 UI. Confirm this server will actually be running when the agent
   re-enters; otherwise agent must `bash scripts/dev-tiers.sh --tier 1` first and wait for readiness probe.

### Success gates (pre-quickmerge)

1. `rg -n "pathname.startsWith\(['\"]/services/research" unified-trading-system-ui/components/shell/` → zero hits.
2. `rg -n "pathname.startsWith\(['\"]/services/trading" unified-trading-system-ui/components/shell/` → zero hits (added
   as a secondary invariant).
3. `rg -l "phase:\s*Phase" unified-trading-system-ui/components/shell/` → ≥ 3 files.
4. `cd unified-trading-system-ui && CI=true npm test -- --run` → all green (existing + new vitest tests).
5. `cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build` → smoke build green. NOTE: repo is Next.js
   (checked next.config.mjs) — step should be `npx next build` instead of `npx vite build`. Flagging for operator; plan
   prose at line 101 needs the Next/Vite distinction reconciled. **Will run `npx next build` at QG time.**
6. Playwright spec green on tier-1 dev.
7. Commit SHA pushed to `origin/live-defi-rollout`.
