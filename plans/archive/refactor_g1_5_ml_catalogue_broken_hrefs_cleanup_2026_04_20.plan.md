---
doc_type: plan
title: Refactor G1.5 — ML Catalogue broken-hrefs cleanup (5 probable)
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
    /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md §1.5,
    /codex/14-customer-journeys/page-triage/broken-links.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Refactor G1.5 — ML Catalogue broken-hrefs cleanup (5 probable)

## Context

Stage 3E §1.5 targets the 5 probable-broken outbound hrefs captured in
`/codex/14-customer-journeys/page-triage/broken-links.md` "5 probable" block — all originating from
`unified-trading-system-ui/lib/lifecycle-route-mappings.ts` and pointing into the ML Model Catalogue surface. Each must
be decided build-or-prune with alignment to the coming G2.4 ML catalogue refactor direction; undecided links rot and
break triage discipline.

## Decisions locked with user (2026-04-20)

| Decision                                                            | Chosen                                                                          | Source                                           |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------ |
| All 5 probable-broken links get a build-or-prune decision this wave | No "wait and see"                                                               | Kickoff §1.5 + rule 06 show/don't-show           |
| Build decisions align with G2.4 ML catalogue direction              | Build only what G2.4 is definitely going to surface; prune the rest             | stage-3e §1.5                                    |
| Prune = remove href + remove orphan source record                   | No `// TODO: fix` comments; either the route exists or the reference is deleted | Kickoff §What NOT to do (no half-finished state) |

## Cross-references

- **Sibling Wave A plans:** refactor*g1*{1,3,9,12,14}\_2026_04_20.md
- **Future alignment (G2):** G2.4 ML catalogue refactor — the build decisions here should not pre-empt that refactor's
  IA choices.
- **Source of the 5 probable hrefs:** `/codex/14-customer-journeys/page-triage/broken-links.md`
- **Triage matrix:** `/codex/14-customer-journeys/page-triage/triage-matrix.md`
- **Duplicate clusters:** `/codex/14-customer-journeys/page-triage/duplicate-clusters.md`

## Mandatory read-set

1. `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.5
2. `/codex/14-customer-journeys/page-triage/broken-links.md` — the "5 probable" block
3. `/codex/14-customer-journeys/page-triage/triage-matrix.md`
4. `unified-trading-system-ui/lib/lifecycle-route-mappings.ts`
5. `unified-trading-system-ui/app/services/ml/**` (or wherever ML catalogue pages live today — enumerate in Phase 5A)
6. `/codex/14-customer-journeys/playbook-concepts/catalogue-ml-model.md`

## Out of scope

- Building the G2.4 ML catalogue refactor itself — this plan only aligns.
- Fixing any non-ML broken href — those are in a separate triage backlog.
- Introducing new routes — build means "surface a route that is already justified by G2.4"; prune means "remove the
  reference".
- Archiving orphan ML catalogue pages — orphan cleanup is a separate page-triage wave.

## Phase breakdown

### Phase 5A — Enumerate and classify the 5

- [x] [AGENT] P0. Extract the 5 probable-broken hrefs from `page-triage/broken-links.md` with their source file:line.
- [x] [AGENT] P0. For each href, classify: **BUILD** (surface must exist per G2.4 direction) or **PRUNE** (reference is
      stale / page will be merged or deprecated).
- [x] [AGENT] P0. For each BUILD decision, confirm against `cross-cutting/catalogue-ml-model.md` that the target route
      is in G2.4's scope.

### Phase 5B — Execute PRUNE decisions

- [x] [AGENT] P0. For each PRUNE href, remove the entry from `lib/lifecycle-route-mappings.ts` and any component that
      renders it as a menu/link item.
- [x] [AGENT] P0. No `// TODO: removed` comments — clean deletion.
- [x] [AGENT] P0. Grep-verify the href string is gone from the UI repo:
      `rg -l "<pruned-href>" unified-trading-system-ui/` returns zero.

### Phase 5C — Execute BUILD decisions

- [x] [AGENT] P0. For each BUILD href, either (a) create the minimal stub page with a "This surface is being built as
      part of G2.4 ML catalogue refactor" notice + a `data-testid="g2-4-placeholder"` hook, or (b) redirect the href to
      an existing equivalent page via `next.config.ts`.
- [x] [AGENT] P0. Ensure every BUILD stub is reachable from the main nav (no URL-only-reachable surfaces).

### Phase 5D — Verify + QG

- [x] [SCRIPT] P0. Re-run the page-triage broken-link scan —
      `rg "href=.*(?:/ml|/models)" lib/lifecycle-route-mappings.ts` produces only links that resolve.
- [x] [SCRIPT] P0. Run UI QG — `cd unified-trading-system-ui && bash scripts/quality-gates.sh`.
- [x] [AGENT] P0. Run Playwright spec `refactor-g1-5-ml-catalogue-hrefs.spec.ts` — click every formerly-broken href;
      every one returns HTTP 200 or an intentional redirect target.

## Critical files to be modified

- `unified-trading-system-ui/lib/lifecycle-route-mappings.ts` — remove PRUNE entries, update BUILD entries
- `unified-trading-system-ui/next.config.ts` — add redirect rules for BUILD-via-redirect decisions
- `unified-trading-system-ui/app/services/ml/**` — new stub pages per BUILD-via-stub decisions
- `/codex/14-customer-journeys/page-triage/broken-links.md` — move the 5 probable entries into a "resolved 2026-04-20"
  section
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-5-ml-catalogue-hrefs.spec.ts` — NEW

## Execution DAG

```
5A (classify)  →  5B (prune) + 5C (build)  [parallel]  →  5D (QG + Playwright)
```

## Verification

1. Every one of the 5 probable-broken hrefs has a documented classification in Phase 5A output.
2. UI QG green.
3. Playwright spec: click every formerly-broken href returns HTTP 200 or intentional redirect.
4. `broken-links.md` "5 probable" block reduced to 0; resolved entries logged with 2026-04-20 stamp.

## Handoff

Unblocks:

- **G2.4 ML catalogue refactor** — starts from a clean href baseline without phantom links to non-existent pages.
- Page-triage Wave 2 — the "4 confirmed broken" block can be tackled with the same classification pattern.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` through MCP Playwright — navigate to each surface that previously
rendered one of the 5 probable hrefs, click the link, verify target page loads or redirects to intended target. Iterate
until all 5 resolve.

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-5-ml-catalogue-hrefs.spec.ts` — must:

1. Seed an `admin` persona via `tests/e2e/playbooks/seed-persona.ts`.
2. Walk the canonical click-path into the ML Model Catalogue surfaces where the 5 hrefs originate.
3. Click each formerly-broken href; assert HTTP 200 or an intentional redirect target; page renders without the
   Next.js 404.
4. Assert visibility-slicing vs G1.6 `access_control(user, route, item, phase)` formula once G1.6 lands; until then,
   admin sees all so the assertion is "rendered without auth gate".
5. Include an orphan-reachability assertion — every BUILD stub MUST be reachable from the main nav (not URL-only).
6. Wired into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G1.5 (Wave A, standalone — no
dependencies on other G1 items).**

---

You are executing **Refactor G1.5 — ML Catalogue broken-hrefs cleanup** for the Unified Trading System at Odum Research.
Wave A; parallelisable with 1.1, 1.3, 1.9, 1.12, 1.14-markdown.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm
git checkout live-defi-rollout && git pull
ls /codex/14-customer-journeys/page-triage/broken-links.md
ls /codex/14-customer-journeys/playbook-concepts/catalogue-ml-model.md
ls ../unified-trading-system-ui/lib/lifecycle-route-mappings.ts
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 5A through 5D of this plan:
`plans/active/refactor_g1_5_ml_catalogue_broken_hrefs_cleanup_2026_04_20.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 6.

### Deliverables

- Modified: `lib/lifecycle-route-mappings.ts`, `next.config.ts` (if any BUILD-via-redirect), page-triage
  `broken-links.md`.
- New (if any BUILD-via-stub): `app/services/ml/...` stub pages.
- New test: `tests/e2e/playbooks/refactor/refactor-g1-5-ml-catalogue-hrefs.spec.ts`.
- PM commit stamps the 5 probable entries as resolved.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
Playwright tools during dev to click every one of the 5 formerly-broken hrefs and verify target-page-loads or
intentional-redirect. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-5-ml-catalogue-hrefs.spec.ts` — seed admin persona
via `tests/e2e/playbooks/seed-persona.ts`, walk the canonical click-path, assert each href resolves, include
orphan-reachability assertion on any BUILD stub, wire into `scripts/quality-gates.sh`.

### Commit strategy

Two commits — UI repo + PM repo.

UI repo:

```
cd unified-trading-system-ui
bash scripts/quickmerge.sh "refactor(ui): G1.5 — ML catalogue broken-href cleanup (build/prune 5 probable)" --agent
```

PM repo:

```
cd unified-trading-pm
bash scripts/quickmerge.sh "docs(playbooks): G1.5 — stamp 5 probable-broken ML hrefs as resolved" --agent --files "/codex/14-customer-journeys/page-triage/broken-links.md"
```

Fallback if quickmerge is blocked by unrelated WIP on live-defi-rollout:

```
git add <files>
git commit -m "<msg>"
git push origin live-defi-rollout
```

### Success criteria

1. ✅ All 5 checkboxes in Phase 5A output have BUILD or PRUNE classifications.
2. ✅ `rg <pruned-href>` in UI repo returns zero hits for every PRUNE decision.
3. ✅ Every BUILD stub reachable from the main nav (no orphan).
4. ✅ UI QG green.
5. ✅ Playwright spec green on tier-1 dev.
6. ✅ Commit SHAs pushed to `origin/live-defi-rollout` (both repos).

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT introduce `// TODO: fix` comments — the link either works or the reference is deleted.
- Do NOT pre-empt G2.4's ML catalogue refactor IA — BUILD stubs are minimal.
- Do NOT touch G2 or G3 items beyond the BUILD stub alignment.

### Report back

- The 5-row classification table (href, source file:line, BUILD|PRUNE, rationale).
- LOC delta.
- Playwright spec path + pass status.
- Two commit SHAs (UI + PM) pushed to live-defi-rollout.
- Any gaps or open questions for the user.
