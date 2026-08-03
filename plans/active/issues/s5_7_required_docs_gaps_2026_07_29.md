---
doc_type: issue
title:
  "S5.7 required-docs audit (Phase 5 of codex_vs_repo_docs_ssot_audit): 9 of 17 service/library repos miss one or more
  S5.1/S5.2 required docs — most are legitimately-absent for non-data-writing repos, so the actionable output is a
  scoping decision on whether S5.1 should tier by repo type, not a blanket doc-creation sweep"
summary:
  "Running the S5.7 required-docs audit across the in-scope service/library repos (Phase 5 verify step of
  codex_vs_repo_docs_ssot_audit_2026_06_01.md) found 9/17 repos missing >=1 required doc. But the gaps split two ways:
  genuine gaps in data-writing services (market-data-processing-service missing DEPLOYMENT_GUIDE/TESTING) vs
  legitimately-absent docs in non-data-writing repos (agent-orchestrator, e2e-testing, system-integration-tests,
  batch-live-reconciliation-service, ibkr-gateway-infra have no GCS write path / no schema, so GCS_PATHS.md +
  SCHEMA_VALIDATION.md do not apply). The prior required-docs enforcement effort
  (documentation_standards_enforcement.plan.md, phase0_standards_enforcement.plan.md) is ARCHIVED, so nothing active
  tracks this. This is a scoping judgment (should S5.1 tier its required set by repo type?), not a bounded worker todo —
  captured here per the findings-closure HARD RULE."
status: open
nature: notes
asset_group: [infrastructure]
stage: [meta]
repos: [market-data-processing-service, instruments-service, unified-api-contracts, agent-orchestrator, e2e-testing]
scope: [engineer, admin]
tags: [documentation-standards, s5-audit, required-docs, ssot, plan-hygiene]
related: [/plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md]
created: 2026-07-29
parent_epic: plan_hygiene_master
priority: P2
source:
  "Phase 5 (verify + enforce) of codex_vs_repo_docs_ssot_audit_2026_06_01.md, 2026-07-29 — the S5.7 audit is an explicit
  Phase-5 verify step; its output (required-docs gaps) is a real finding outside this plan's SSOT-dedup scope."
assigned_vm: NA
resolved_by:
locked_by:
context_scope:
  [/codex/06-coding-standards/documentation-standards.md, /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md]
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
last_updated: 2026-07-29
supersedes:
superseded_by:
drift_direction: advance-code
depends_on: []
---

# S5.7 required-docs audit gaps (Phase 5 verify output)

## What I found

Ran the S5.7 audit script (`/codex/06-coding-standards/documentation-standards.md` § S5.7) across the 16 in-scope
service repos + 1 library repo of `codex_vs_repo_docs_ssot_audit_2026_06_01.md`. Snapshot 2026-07-29 (a required doc is
"missing" if absent or a <=3-line stub):

| Repo                              | Missing/stub required docs                                                               |
| --------------------------------- | ---------------------------------------------------------------------------------------- |
| deployment-service                | — (OK)                                                                                   |
| execution-service                 | — (OK)                                                                                   |
| market-tick-data-service          | — (OK)                                                                                   |
| strategy-service                  | — (OK)                                                                                   |
| deployment-api                    | — (OK)                                                                                   |
| client-reporting-api              | — (OK)                                                                                   |
| alerting-service                  | — (OK)                                                                                   |
| trading-agent-service             | — (OK)                                                                                   |
| unified-trading-library (lib)     | — (OK)                                                                                   |
| market-data-processing-service    | DEPLOYMENT_GUIDE, TESTING                                                                |
| unified-api-contracts             | GCS_PATHS, DEPLOYMENT_GUIDE, SCHEMA_VALIDATION                                           |
| instruments-service               | ARCHITECTURE, CONFIGURATION, GCS_PATHS, DEPLOYMENT_GUIDE, TESTING, SCHEMA_VAL            |
| ibkr-gateway-infra                | CONFIGURATION, GCS_PATHS, TESTING, SCHEMA_VALIDATION                                     |
| e2e-testing                       | ARCHITECTURE, CONFIGURATION, GCS_PATHS, DEPLOYMENT_GUIDE, TESTING, SCHEMA_VAL, QG_BYPASS |
| agent-orchestrator                | ARCHITECTURE, CONFIGURATION, GCS_PATHS, DEPLOYMENT_GUIDE, TESTING, SCHEMA_VAL, QG_BYPASS |
| system-integration-tests          | ARCHITECTURE, CONFIGURATION, GCS_PATHS, DEPLOYMENT_GUIDE, TESTING, SCHEMA_VAL            |
| batch-live-reconciliation-service | README, ARCHITECTURE, CONFIGURATION, DEPLOYMENT_GUIDE, TESTING, SCHEMA_VAL               |

Note: `instruments-service` reorganized its docs (per the plan's Appendix B refresh — `ARCHITECTURE` folded into
`ADAPTER_ARCHITECTURE.md` + per-asset docs; `specs/` dir removed), so several "missing" rows there are naming/structure
drift vs the fixed S5.1 filename set, not truly absent content.

## Why it matters

The S5.1/S5.2 required-docs set is uniform across all `*-service`/`*-api` repos, but the set assumes a
data-writing-service shape. Several in-scope repos legitimately have no GCS write path (agent-orchestrator = an
orchestration server; e2e-testing / system-integration-tests = test harnesses; ibkr-gateway-infra = infra) and no owned
schema, so `GCS_PATHS.md` and `SCHEMA_VALIDATION.md` do not apply. Blanket-creating those docs would produce exactly the
empty/stub docs S5.4 counts as _missing_ anyway — churn with no signal. Conversely, the genuine gaps
(market-data-processing-service's DEPLOYMENT_GUIDE/TESTING) are real and worth filling. The prior enforcement plans that
would have tracked this (`documentation_standards_enforcement.plan.md`, `phase0_standards_enforcement.plan.md`) are
archived, so nothing active owns it.

This is out of scope for `codex_vs_repo_docs_ssot_audit_2026_06_01.md` (that plan is SSOT-**deduplication**, not
required-docs **presence**) — recorded here so the Phase-5 audit output is tracked, not lost in a pane.

## Recommended decision

Operator/main scoping call (not an AO-dispatchable bounded todo — "which repos need which docs" is a judgment call per
the dispatch-scope-eligibility ruling):

- [ ] [DOCS] P2. **Tier the S5.1 required-docs set by repo type** — split into "data-writing service" (keeps GCS_PATHS +
      SCHEMA_VALIDATION) vs "compute/orchestration/test/infra" (GCS_PATHS + SCHEMA_VALIDATION become N/A, marked
      explicitly not-applicable rather than missing). Codify the tiering in
      `/codex/06-coding-standards/documentation-standards.md` § S5.1. (repo: unified-trading-pm) — OPERATOR/main scoping
      decision first.
- [ ] [DOCS] P2. **Fill the genuine data-service gaps** once tiering is decided: market-data-processing-service
      `DEPLOYMENT_GUIDE.md` + `TESTING.md` (real service, docs genuinely absent). (repo: market-data-processing-service)
- [ ] [DOCS] P3. **Reconcile instruments-service's reorganized docs against the S5.1 filename set** — either add thin
      redirect stubs at the canonical filenames pointing at the reorganized docs, or update S5.1 to accept the
      reorganized layout. (repo: instruments-service, unified-trading-pm)

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Doc explicitly
  self-classifies as a scoping judgment ('should S5.1 tier its required set by repo type?'), not a bounded worker todo,
  per the doc's own text citing the dispatch-scope-eligibility ruling.
