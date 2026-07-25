---
title: Refactor G3.3 — Briefings-content CMS migration
status: active
priority: P1
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  - /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md §3.3
  - refactor_g1_12_public_site_ia_and_briefings_polish_2026_04_20.plan.md
# Wave G3-α — independent, parallel with G3.2/3.4/3.5/3.6.
---

# Refactor G3.3 — Briefings-content CMS migration

## Context

Stage 3E §3.3 migrates briefings content (G1.12 polish target) from hardcoded markdown to a headless CMS + YAML-backed
store. Today pb2 briefing docs (`briefings-hub.md`, `dart-briefing.md`, `regulatory-umbrella-briefing.md`,
`im-decision-journey.md`) live as markdown in `codex/14-playbooks/experience/`. Updates require PR + merge + deploy;
sales cannot iterate briefing content without engineering.

Target: a thin `briefings-content-service` (or UI-side YAML loader) that renders briefing content from a CMS-like
source. Codex markdown becomes the canonical draft + audit record; a codex-sync agent ensures parity.

## Decisions locked with user (2026-04-20)

| Decision                                                     | Chosen                                                                 | Source                               |
| ------------------------------------------------------------ | ---------------------------------------------------------------------- | ------------------------------------ |
| Start with YAML-backed store inside the UI repo              | Low lift; iterate later to Contentful/Sanity if operator demand exists | Stage 3E §3.3 "or YAML-backed store" |
| Codex markdown remains canonical                             | Audit trail + hand-wavy copy remain traceable; CMS mirrors             | Stage 3E §3.3                        |
| Sync: codex-sync agent (G3.5) verifies parity                | Automated drift detection between codex + CMS                          | G3.5 consistency agent               |
| Briefings hub + 4 sub-pages in scope (DART + Reg + IM + hub) | Matches G1.12 polish scope                                             | G1.12                                |

## Cross-references

- **Upstream:** G1.12 public-site IA + briefings polish (`<BriefingHero>` already shipped)
- **Wave G3-α peers (parallel):** G3.2, G3.4, G3.5, G3.6
- **Codex:** `codex/14-playbooks/experience/` — briefings source of truth
- **G3.5 consistency agent:** will verify CMS/codex parity

## Mandatory read-set

1. `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §3.3
2. `/codex/14-customer-journeys/experience/briefings-hub.md`
3. `/codex/14-customer-journeys/experience/dart-briefing.md`
4. `/codex/14-customer-journeys/experience/regulatory-umbrella-briefing.md`
5. `/codex/14-customer-journeys/experience/im-decision-journey.md`
6. `refactor_g1_12_public_site_ia_and_briefings_polish_2026_04_20.plan.md`
7. `unified-trading-system-ui/components/marketing/` — `<BriefingHero>` + related

## Out of scope

- Full headless CMS integration (Contentful/Sanity) — YAML store is v1
- Content mutation UI (sales edits markdown via PR for now)
- Localisation / i18n (future)
- Reading `_archived_pre_v2/` paths

## Phase breakdown

### Phase A — YAML store schema

- [ ] [AGENT] P0. Declare `BriefingContent` TypeScript interface + YAML schema at
      `unified-trading-system-ui/content/briefings/` (dir holds per-briefing YAML).
- [ ] [AGENT] P0. Shape: `{id, slug, title, hero, pillars: [{title, body, ctas?}], sections: [...]}`.
- [ ] [AGENT] P0. Validation script `scripts/validate-briefings-yaml.ts`.

### Phase B — Migrator + loader

- [ ] [AGENT] P0. `scripts/migrate-briefings-from-codex.ts` — reads codex markdown, parses sections, emits YAML.
      Idempotent; run once at migration + on codex changes.
- [ ] [AGENT] P0. `lib/briefings/loader.ts` — loads YAML at build time; exports typed `getBriefing(slug)`.

### Phase C — UI integration

- [ ] [AGENT] P0. `/briefings/[slug]/page.tsx` — renders from YAML via loader (replaces hardcoded imports).
- [ ] [AGENT] P0. `/briefings/page.tsx` (hub) — lists briefings from YAML index.
- [ ] [AGENT] P0. Reuse `<BriefingHero>` from G1.12.

### Phase D — Parity + CI

- [ ] [AGENT] P0. CI job: `scripts/validate-briefings-yaml.ts` + codex ↔ YAML parity check. Blocks PR on drift.
- [ ] [AGENT] P0. Codex-sync hook: on commit to `codex/14-playbooks/experience/*briefing*.md`, auto-run migrator +
      commit resulting YAML diff (G3.5 agent will formalise; manual for v1).

### Phase E — QG + verification

- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. Playwright spec `refactor-g3-3-briefings-cms.spec.ts` — briefings hub + 3 sub-pages render from YAML.

## Critical files to be modified

- `unified-trading-system-ui/content/briefings/dart.yaml` — NEW
- `unified-trading-system-ui/content/briefings/regulatory-umbrella.yaml` — NEW
- `unified-trading-system-ui/content/briefings/im-decision-journey.yaml` — NEW
- `unified-trading-system-ui/content/briefings/_hub.yaml` — NEW
- `unified-trading-system-ui/lib/briefings/loader.ts` — NEW
- `unified-trading-system-ui/lib/briefings/types.ts` — NEW
- `unified-trading-system-ui/scripts/migrate-briefings-from-codex.ts` — NEW
- `unified-trading-system-ui/scripts/validate-briefings-yaml.ts` — NEW
- `unified-trading-system-ui/app/briefings/[slug]/page.tsx` — MODIFY (read from loader)
- `unified-trading-system-ui/app/briefings/page.tsx` — MODIFY
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g3-3-briefings-cms.spec.ts` — NEW

## Execution DAG

```
A (schema) → B (migrator + loader)
               ↓
             C (UI integration)
               ↓
             D (parity CI)
               ↓
             E (QG + Playwright)
```

## Verification

1. 4 YAML briefings exist + validate.
2. Loader serves content at build time.
3. Hub + sub-pages render from YAML.
4. Codex ↔ YAML parity CI green.
5. Playwright spec green.
6. UI QG green.

## Handoff

Unblocks:

- **Sales team iteration** — update briefings via markdown PR, YAML auto-syncs.
- **Future Contentful/Sanity migration** — loader is swappable.
- **G3.5 consistency agent** — formalises parity check.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` through MCP Playwright tools; walk briefings hub → each sub-page;
assert YAML content renders.

**Durable spec for CI:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g3-3-briefings-cms.spec.ts`:

1. Navigate briefings hub.
2. Navigate DART + Reg Umbrella + IM briefings.
3. Assert rendered content matches YAML source.
4. Include orphan-reachability assertion.
5. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G3.3 (Wave G3-α).**

---

You are executing **Refactor G3.3 — Briefings-content CMS migration** for the Unified Trading System at Odum Research.
Wave G3-α; G1.12 must be shipped.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
ls /codex/14-customer-journeys/experience/dart-briefing.md
ls unified-trading-system-ui/components/marketing/  # verify G1.12 BriefingHero exists
ls unified-trading-system-ui/app/briefings/
```

All must exist. STOP if missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases A through E of this plan:
`plans/active/refactor_g3_3_briefings_cms_migration_2026_04_20.plan.md`

### Read-set (mandatory)

All 7 paths from the plan's Mandatory read-set.

### Deliverables

Per plan's Critical files list — 11 files in UI repo.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` through MCP Playwright tools; walk briefings hub + 3 sub-pages; assert YAML content renders
correctly. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g3-3-briefings-cms.spec.ts`, wired into
`scripts/quality-gates.sh`, including orphan-reachability.

### Commit strategy

One commit in UI repo.

```
cd unified-trading-system-ui && bash scripts/quickmerge.sh "feat(briefings): G3.3 — YAML store + migrator + loader + CI parity" --agent
```

Manual-git fallback. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ 4 YAML briefings validate.
2. ✅ Loader renders hub + sub-pages.
3. ✅ Codex ↔ YAML parity CI green.
4. ✅ Playwright spec green.
5. ✅ UI QG green.
6. ✅ 1 commit SHA pushed.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT integrate with external CMS (Contentful/Sanity) — YAML is v1.
- Do NOT build content-mutation UI — sales edits via markdown PR.
- Do NOT diverge YAML from codex — parity CI is the guardrail.
- Do NOT `--no-verify` pre-commit hooks.

### Report back

- 4 YAML briefing file list.
- Migrator dry-run diff.
- Parity CI job ID.
- Playwright spec pass status.
- UI QG results.
- 1 commit SHA pushed to live-defi-rollout.
