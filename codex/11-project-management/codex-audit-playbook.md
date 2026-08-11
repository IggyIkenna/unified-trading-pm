---
doc_type: codex-ssot
title: Codex Audit Playbook
summary:
  Recurring codex-doc ↔ plan alignment audit — cadence table, the 6-tag drift taxonomy
  (CODEX-MISSING/STALE/CONTRADICTS/AHEAD/BROKEN-REF/ORPHAN-EPIC-REF), and the 5-phase execution playbook (structural
  scan → epic-level audit → plan verification → delta annotation → verification).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [codex-audit, ssot-audit, audit, codex-drift, plan-hygiene]
related:
  [
    ../../plans/archive/2026_05/codex_plan_audit_differential_2026_05_22.md,
    ../../plans/epics/plan_hygiene_master.md,
    /codex/13-codex-governance/SSOT-BOUNDARY.md,
    /codex/11-project-management/plan-hygiene.md,
  ]
created: 2026-05-22
authoritative_for: [codex-plan alignment audit cadence, codex drift taxonomy]
referenced_by:
owner:
last_reviewed: 2026-05-22
code_refs:
---

# Codex Audit Playbook

Recurring audit cadence for keeping codex ↔ plan alignment. First run: 2026-05-22 (see
`plans/active/codex_plan_audit_differential_2026_05_22.md`).

## When to run

| Trigger                                 | Cadence                                    | Scope                                                  |
| --------------------------------------- | ------------------------------------------ | ------------------------------------------------------ |
| Post-Plan-Phase Codex Audit (HARD RULE) | After every major phase completes          | Touched codex docs only                                |
| Plan archival (HARD RULE)               | Before moving any plan to `plans/archive/` | All codex docs listed in plan's `Codex SSOTs:` section |
| Quarterly full-breadth audit            | Once per quarter                           | All codex docs × active plans × epics                  |
| New epic created                        | On creation                                | New epic's codex SSOT section                          |

## Taxonomy

| Tag                 | Meaning                                                 | Fix                                                   |
| ------------------- | ------------------------------------------------------- | ----------------------------------------------------- |
| `CODEX-MISSING`     | Plan decision has no codex home                         | Write stub or expand existing section                 |
| `CODEX-STALE`       | Codex says "future/planned" but plan shipped it         | Update to current; keep delta note for remaining work |
| `CODEX-CONTRADICTS` | Codex says X, plan decided Y                            | Determine canonical; update the loser                 |
| `CODEX-AHEAD`       | Codex describes aspirational state, code not there      | Add `## Current State` box with honest gap            |
| `BROKEN-REF`        | Plan or codex references a path that doesn't exist      | Create stub or fix reference                          |
| `ORPHAN-EPIC-REF`   | Active plan references SUPERSEDED epic as `parent_epic` | Re-parent to live epic                                |

Priority: P0 = agent assumption violated; P1 = next-agent confusion; P2 = cleanup.

## Standard delta box format

```markdown
> **[DELTA YYYY-MM-DD]** **Current state:** [what's shipped to live] **Planned delta:** [what active plan `<slug>` is >
>
> > delivering] **Target architecture:** [final destination]
```

## Phase 0 — Structural scan (automated)

Run against `plans/active/*.md`, `plans/epics/*.md`, `codex/**/*.md`:

```bash
# Broken-ref scan: extract codex/ path refs from plans → check existence
grep -roh 'codex/[a-zA-Z0-9/_.-]*\.md' plans/active/ plans/epics/ | sort -u | while read ref; do
  [ -f "$ref" ] || echo "BROKEN-REF: $ref"
done

# Orphan plan scan: active plans without parent_epic
grep -rL "^parent_epic:" plans/active/*.md

# SUPERSEDED doc scan: codex docs with SUPERSEDED banners
grep -rl "SUPERSEDED" codex/ --include="*.md"

# Stale delta marker scan
grep -rl "post-cutover\|future\|not yet implemented\|TODO" codex/ --include="*.md" | wc -l
```

Publish baseline counts to `plans/audit/results/codex_plan_diff_scan_<date>.md`.

## Phase 1 — Epic-level semantic audit

For each live epic: verify that the epic's shipped phases match codex current-state descriptions. Group by layer:

- **L0 asset-group epics**: `defi_master`, `cefi_master`, `tradfi_master`, `sports_master`, `predictions_master`
- **L1 pipeline epics**: `mtds_mdps_master`, `manifest_master`, `instruments_master`, `features_and_ml_master`
- **L2 functional epics**: `execution_master`, `strategy_master`, `global_ledger_pnl_attribution_master`,
  `trading_agent_master`, `client_isolation_and_governance_master`, `dart_and_promote_master`
- **L3-L5 meta epics**: `infrastructure_master`, `batch_live_symmetry_master`, `deployment_and_user_management_master`,
  `observability_master`, `orchestrator_master`, `plan_hygiene_master`

L0+L1 can run in parallel. L2+L3 can run in parallel. Each group can be fan-out to a sub-agent.

## Phase 2 — Critical-path plan→codex verification

For each active plan with `Codex SSOT:` section, read the plan's declared codex targets, read the actual doc, classify:
DONE / PARTIAL / NOT-DONE. Fix NOT-DONE inline.

Priority: LDR-locked plans first (P0), then remaining plans with Codex SSOT sections (P1).

## Phase 3 — Delta annotation + stubs + structural fixes

- Apply delta boxes to all CODEX-STALE and CODEX-AHEAD docs
- Write stubs for CODEX-MISSING P0/P1 findings
- Fix BROKEN-REF findings
- Re-parent ORPHAN-EPIC-REF active plans

Stub minimum:

- Frontmatter: `scope` + `last_reviewed`
- `## Context` section
- `## Current State` section with delta box
- `## Target` section
- `See also:` plan pointer

## Phase 4 — Verification

```bash
# Broken-ref count must be 0
grep -roh 'codex/[a-zA-Z0-9/_.-]*\.md' plans/active/ plans/epics/ | sort -u | while read ref; do
  [ -f "$ref" ] && echo "OK: $ref" || echo "BROKEN: $ref"
done | grep BROKEN | wc -l

# Every P0 finding must have a resolution
```

Publish before/after counts to `plans/audit/results/`.

## Parallelization map

- Groups L0+L1 can run as parallel sub-agents
- Groups L2+L3 can run after L0+L1 (or in parallel if no shared codex docs)
- Phase 2A (LDR-locked) can run in parallel with Phase 1
- Phase 3 runs after all Phase 1+2 complete (avoids edit conflicts)
- Phase 4 runs last

## SSOT placement (SSOT-BOUNDARY.md decision tree)

- Architectural decision → `codex/04-architecture/`
- Data schema / manifest → `codex/02-data/`
- Infrastructure / deployment → `codex/05-infrastructure/`
- Coding standards / QG → `codex/06-coding-standards/`
- Strategy architecture → `codex/09-strategy/architecture-v2/`
- Project management → `codex/11-project-management/`
- Runbooks → `codex/15-runbooks/`

## See also

- `plans/active/codex_plan_audit_differential_2026_05_22.md` — first full-breadth audit run
- `plans/epics/plan_hygiene_master.md` — parent epic
- `/codex/13-codex-governance/SSOT-BOUNDARY.md` — where to place new codex docs
- `/codex/11-project-management/plan-hygiene.md` — plan hygiene complementary process
