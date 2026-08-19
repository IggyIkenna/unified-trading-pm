---
doc_type: codex-ssot
title: Epic taxonomy — 9-domain service layer (2026-08-18)
summary:
  Decision record for the non-asset-group epic layer, replacing the prior implicit L1-L5 tier framing. Maps 9 named
  service/subsystem domains onto the 24 active epics, with each epic's disposition stated explicitly (kept,
  renamed, folded into a sibling, or split). The 5 asset-group L0 epics (cefi, defi, tradfi, predictions, sports)
  are a separate, orthogonal axis and are not part of this taxonomy.
status: current
nature: record
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [epics, taxonomy, plan-hygiene, plan-reconcile]
related:
  [
    /plans/epics/README.md,
    /codex/11-project-management/epic-html-report-format.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /plans/active/epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md,
  ]
created: 2026-08-18
authoritative_for: [epic domain taxonomy, epic disposition (kept/renamed/folded/split)]
referenced_by: []
code_refs:
owner:
last_reviewed: 2026-08-18
---

# Epic taxonomy — 9-domain service layer (2026-08-18)

## Why this exists

Before 2026-08-18, the non-asset-group epic layer was organized by an implicit L1-L5 "tier" (how meta/close-to-
runtime a concern is), which said nothing about WHICH service/subsystem an epic covered — `infrastructure_master`
absorbed 296 of 833 corpus-wide `parent_epic` references (35.5%) despite its own summary framing it narrowly, no
epic owned CI or UAC directly, and several epics had drifted to near-zero relevance. This doc replaces that implicit
framing with 9 named domains an operator can reason about directly, and states each epic's disposition so the
mapping is a fact you can look up, not something to re-derive from grepping `parent_epic:` frequencies each time.

**Non-goal, stated explicitly**: the 5 asset-group L0 epics — `cefi_master`, `defi_master`, `tradfi_master`,
`predictions_master`, `sports_master` — are a separate, orthogonal axis (which market/vertical, not which
service/subsystem) and are untouched by this taxonomy. A plan can belong to an asset-group epic OR one of the 9
domains below, never both, and both kinds of `parent_epic` values are equally valid.

## The 9 domains

| #   | Domain                           | Epic(s)                                                                                                                                         | Disposition                                                                                                                                                |
| --- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | AO (agent-orchestrator)          | `orchestrator_master`, `agent_operating_framework_master`                                                                                       | Kept as two files, grouped under one domain tag. Real content overlap exists (both L5/meta) — a full merge is a deferred follow-up, not done in this pass. |
| 2   | CI                               | `ci_master`                                                                                                                                     | **New**, carved out of `infrastructure_master`'s CI-topic references.                                                                                      |
| 3   | Strategy service                 | `strategy_master`                                                                                                                               | Absorbed `dart_and_promote_master` and `global_ledger_pnl_attribution_master` (both had 0 corpus references before the fold).                              |
| 4   | Deployment & observability       | `deployment_and_user_management_master`, `observability_master`                                                                                 | `observability_master` absorbed `escalation_and_disaster_recovery_master`.                                                                                 |
| 5   | Execution service                | `execution_master`, `batch_live_symmetry_master`                                                                                                | `execution_master` absorbed `trading_agent_master` (0 references before the fold).                                                                         |
| 6   | UAC & reference-data/instruments | `instruments_master`, `uac_master`                                                                                                              | `uac_master` is **new**, carved out of `infrastructure_master` and `client_isolation_and_governance_master`'s UAC-topic references.                        |
| 7   | Market data & processing         | `mtds_mdps_master`, `manifest_master`                                                                                                           | `mtds_mdps_master`'s title was fixed to match its slug (content was already correct, only the title had drifted).                                          |
| 8   | Features & ML                    | `features_and_ml_master`                                                                                                                        | No change.                                                                                                                                                 |
| 9   | Security & cross-cutting         | `security_and_cross_cutting_master` (renamed from `infrastructure_master`), `client_isolation_and_governance_master`, `system_readiness_master` | The rename absorbs whatever remains of `infrastructure_master` after the CI/UAC carve-outs.                                                                |

## Epics NOT in this taxonomy (by design)

- **Asset-group L0**: `cefi_master`, `defi_master`, `tradfi_master`, `predictions_master`, `sports_master` — see
  Non-goal above.
- **`plan_hygiene_master`** — process/tooling-about-plans itself (owns the plan-hygiene check scripts,
  `run_hygiene_sweep.sh`, and this very restructure's own parent plan). Not a service domain; stays its own thing.
- **The 4 `*_SUPERSEDED_*.md` epic files** (`cross_cutting_may_23_SUPERSEDED_2026_05_21`,
  `manifest_evolution_SUPERSEDED_2026_05_21`, `manifest_migration_SUPERSEDED_2026_05_21`,
  `strategy_and_dart_master_SUPERSEDED_2026_05_21`) — historical record only, already properly marked superseded,
  not part of any live domain.

## How to use this doc

- Deciding a new plan's `parent_epic`: find its service/subsystem in the table above, use the listed epic slug. If
  it's about which market/vertical (CeFi/DeFi/TradFi/prediction/sports) rather than which service, use the matching
  asset-group L0 epic instead — this doc doesn't cover that case.
- `/plan-reconcile <epic_slug>` (see `/codex/11-project-management/epic-html-report-format.md` for what it
  produces) accepts any epic slug from `plans/epics/` directly — the 9 domains above are a grouping convenience for
  a human reading this doc, not a scope `/plan-reconcile` itself understands as a unit (it operates per-epic-file).

## Cross-references

- `/plans/active/epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md` — the plan that executed this
  restructure; its Progress Log has the mechanical execution detail (which docs' `parent_epic` moved, commit shas).
- `/plans/epics/README.md` — the epic registry index; kept in sync with this doc's dispositions.
- `/codex/12-agent-workflow/epic-keyword-surface.yaml` — the keyword lists `check_parent_epic_alignment.py` uses to
  soft-flag a plan whose `parent_epic` doesn't match its content; extended for `ci_master`/`uac_master` alongside
  this restructure.
