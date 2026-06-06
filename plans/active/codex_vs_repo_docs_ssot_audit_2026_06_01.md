---
name: codex_vs_repo_docs_ssot_audit
title: "Codex-vs-repo-docs SSOT audit + consolidation (all active repos)"
parent_epic: plan_hygiene_master
assigned_vm: vm-ml
priority: P1
created: 2026-06-01
estimate_class: refactor
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 3.2
status: active
execution_scope: local-only
locked_by: live-defi-rollout
model_tier: opus-required
execution_model: opus-1m
thinking: high
source:
  - unified-trading-pm/codex/06-coding-standards/documentation-standards.md
  - unified-trading-pm/codex/00-SSOT-INDEX.md
  - unified-trading-pm/plans/active/issues/repo_docs_codex_ssot_consolidation_2026_06_01.md
---

# Codex-vs-repo-docs SSOT audit + consolidation

> **Goal**: `unified-trading-pm/codex/` is the single source of truth for all canonical / cross-cutting documentation.
> Every repo `docs/` folder is audited against it; duplicated content is removed and replaced with a link to the codex
> SSOT; genuinely repo-specific essentials stay (kept light); any unique info found only in a repo doc is migrated INTO
> codex first (never lost). End state: **zero documentation duplication between codex and repo docs.** Contract:
> `codex/06-coding-standards/documentation-standards.md` **§ S5.11** (codified 2026-06-01).

## Execution model — **opus-1m** (suggested)

**Run this plan on `claude-opus` with the 1M-token context window (`opus-1m`), `thinking: high`.** Rationale (per
`codex/06-coding-standards/model-tier-selection.md`, this is `opus-required`, not `sonnet-doable`):

- **Large working set**: each repo's consolidation requires holding the relevant slice of the **800-doc codex corpus** +
  the repo's **full `docs/` tree** in context simultaneously to decide, per doc, "is this canonical content that already
  lives in codex doc X, or a genuine repo-specific delta?" — a 200k window forces lossy chunking and mis-classification.
- **Cross-repo + governance judgment**: migrate-vs-redirect-vs-delete + "migrate unique delta into codex" are
  irreversible-ish editorial calls across 20 repos. This is cross-cutting architecture/governance work — Opus-grade
  reasoning, not Sonnet.
- **Sub-agents**: per-repo audit/consolidation may fan out to sub-agents; those `Agent` calls MUST set `model`
  explicitly (`opus` for the migrate/redirect judgment passes; `sonnet` acceptable only for the mechanical FIX-STALE
  literal sweeps).
- **Self-check at task start** (mandatory per model-tier rule): confirm running model == `opus-1m`. Sonnet on this plan
  → STOP.

## Principles (operator, 2026-06-01)

1. **Codex is the SSOT.** Repo docs are updated to match codex — not the other way around.
2. **mtime safety check.** Before treating a repo doc as stale-and-duplicative, compare its git mtime / last-edit vs the
   corresponding codex doc. It is _very unlikely_ a repo doc holds newer canonical info while codex is empty — but
   verify to be safe. If a repo doc is genuinely newer AND carries info absent from codex → **migrate that delta into
   codex FIRST** (commit to codex), then slim the repo doc. Never delete unique info.
3. **Keep repo docs light.** Repo `docs/` carry only the minimum essential, repo-specific information. If canonical info
   is missing from codex, **add it to codex** (don't leave it duplicated in the repo doc).
4. **Redirect, don't duplicate.** A repo doc whose content is canonical becomes a thin redirect to the appropriate codex
   doc(s) (S5.11 redirect template — still substantive enough to clear the S5.4 stub gate). No content appears in both
   places.
5. **All active repos.** Every repo in the workspace with a `docs/` folder (or per-family doc dirs) is in scope.

## Method (per repo)

For each repo, run the loop:

1. **Inventory** — `find <repo> -name '*.md' -not -path '*/node_modules/*' -not -path '*/.venv*/*'` (includes per-family
   dirs like `features_service/*/docs/`). Record git mtime (`git log -1 --format=%cI -- <file>`) per doc.
2. **Classify** each doc against codex (consult `00-SSOT-INDEX.md` + the relevant `codex/<area>/` docs):
   - `KEEP-ESSENTIAL` — genuinely repo-specific, low/no codex overlap → keep, slim if bloated.
   - `REDIRECT` — content is canonical/duplicated → migrate any unique delta to codex, then convert to the S5.11
     redirect template.
   - `DELETE` — pure duplicate / dead one-off dump, zero unique value → migrate nothing, remove (git history =
     rollback).
   - `FIX-STALE` — correct shape but wrong literals (bucket names, hyphen partitions, retired names) → fix in place.
   - `MIGRATE-TO-CODEX` — repo doc is newer (mtime) and holds canonical info **missing** from codex → write/extend the
     codex doc first, then REDIRECT/DELETE the repo copy.
3. **mtime gate** (principle 2): for every REDIRECT/DELETE, confirm the repo doc is not the unique source of newer info.
   If unsure, diff against codex and migrate the delta before removing.
4. **Apply**: codex edits first (migrations) → then repo-doc redirects/deletes/fixes.
5. **Verify**: S5.7 doc-audit script passes (no missing/stub required docs); `rg` finds no codex table/contract
   duplicated in repo docs; all redirect links resolve to existing codex docs; repo builds.

## Contract (already codified — S5.11)

`pm/codex/` = SSOT for canonical/cross-cutting content. Repo `docs/` = repo-specific essentials + codex links; never
duplicate. Required docs (S5.1/2/3) whose content is entirely canonical collapse to the redirect template; non-required
pure-dups are deleted (after migrating unique deltas). Full per-doc-type split + redirect template:
`codex/06-coding-standards/documentation-standards.md` § S5.11.

## Scope — all active repos with docs (20)

Service/library/infra (codex-overlap heavy → audit first): `deployment-service`, `unified-api-contracts`,
`market-data-processing-service`, `execution-service`, `instruments-service`, `market-tick-data-service`,
`strategy-service`, `unified-trading-library`, `e2e-testing`, `agent-orchestrator`, `deployment-api`,
`client-reporting-api`, `alerting-service`, `trading-agent-service`, `ibkr-gateway-infra`,
`batch-live-reconciliation-service`, `system-integration-tests`, `features-service` (per-family doc dirs). UI (mostly
UI-specific — audit only the data/path/contract docs, leave genuine UI docs): `unified-trading-system-ui`,
`deployment-ui`, `user-management-ui`.

> `unified-trading-pm` itself is NOT a target — it _is_ the codex/plans SSOT. Its `plans/*` are historical records (do
> not rewrite). Repo `issues/*` + `*_LOG-REVIEW.md` + vendored `context/codex|pm/*` mirrors are records/mirrors, not
> living docs — out of scope (mirrors re-sync from canonical codex).

## Phases

- **Phase 0 — already shipped (2026-06-01)**: S5.11 contract codified; read-only audit registry for 8 core repos +
  FIX-STALE pass-1 (~340 literal fixes across 9 repos on `live-defi-rollout`). Evidence + 8-repo registry + per-repo
  rollout list folded into **Appendix A** below (migrated 2026-06-01 from the now-archived
  `issues/repo_docs_codex_ssot_consolidation_2026_06_01.md`).
- [ ] [DOCS] P0. **Phase 1 — audit-complete the remaining 12 repos** (read-only): agent-orchestrator, deployment-api,
      client-reporting-api, alerting-service, trading-agent-service, ibkr-gateway-infra,
      batch-live-reconciliation-service, system-integration-tests, deployment-ui, user-management-ui,
      unified-trading-system-ui (data/path docs only), + finish features-service audit. Produce the full per-doc
      registry (extend the pass-1 registry).
- [ ] [DOCS] P0. **Phase 2 — migrate unique deltas into codex.** For every MIGRATE-TO-CODEX doc (mtime-newer +
      codex-missing), write/extend the codex SSOT doc first. Commit codex changes. This must precede any
      REDIRECT/DELETE.
- [ ] [DOCS] P1. **Phase 3 — redirect + slim.** Convert REDIRECT docs to the S5.11 template; slim KEEP-ESSENTIAL docs to
      repo-local + codex links. Per-repo commit + push (PR where LDR is branch-protected — e.g. features-service).
- [ ] [DOCS] P1. **Phase 4 — delete pure-dups.** Remove DELETE-class docs (migration already done in Phase 2). Update
      any `INDEX.md` / README doc-index links.
- [ ] [DOCS] P2. **Phase 5 — verify + enforce.** Run S5.7 audit per repo; add a QG/CI check that flags repo docs
      duplicating a codex table/contract (or hardcoding a resolver-owned literal); confirm all redirect links resolve.

## Success criteria

- Every in-scope repo: `rg` finds no codex table/contract/path-template duplicated in its `docs/`; every required doc is
  either KEEP-ESSENTIAL (repo-specific) or an S5.11 redirect; no DELETE-class dumps remain.
- Zero unique info lost: every MIGRATE-TO-CODEX delta is in codex before its repo copy was removed (mtime-gated).
- S5.7 doc-audit passes for all service/library repos (no missing/stub required docs).
- All redirect links resolve to existing codex docs.

## Out of scope / guardrails

- No git surgery on shared/foreign branches (no cherry-pick/rebase-of-others/force-push/revert). If a repo's LDR is
  branch-protected or another agent is active, land via a clean PR or defer + flag — never untangle by hand.
- `unified-trading-pm/plans/*`, repo `issues/*`, `*_LOG-REVIEW.md`, vendored `context/*` mirrors: not rewritten.

---

## Appendix A — pass-1 evidence + 8-repo audit registry (migrated 2026-06-01 from archived issue)

> Folded here so PM stays SSOT after `issues/repo_docs_codex_ssot_consolidation_2026_06_01.md` was archived. The Phase
> 1–5 todos above are the live work breakdown; the per-repo rollout list below is the per-repo target inventory that
> feeds them. **Caveat**: audit agents proposed codex SSOT targets by grep — **verify each target exists before
> redirecting** (some proposed paths e.g. `codex/05-infrastructure/gcs-lifecycle-policies.md`,
> `codex/04-architecture/concurrency.md`, `codex/02-data/bucket-naming-and-config.md` may need creating/remapping).

### Per-repo rollout (20 repos with docs/, ~520 docs) — ordered by codex-duplication likelihood

- [x] ✅ **market-tick-data-service** (31) — `GCS_PATHS.md` env-tiered + hive-canonical + codex pointer (mtds@9acbee1);
      remaining: DEPLOYMENT_GUIDE_FEMI/SHAHRIYAR delete-redirect (P1 below).
- [ ] [DOCS] P1. **market-tick-data-service finish**: `DEPLOYMENT_GUIDE_FEMI.md` (person-named onboarding dup) +
      `SHAHRIYAR_DEPLOYMENT_INFRA_SPEC.md` (infra-spec dup) → migrate unique delta, replace with redirect to
      `codex/05-infrastructure` + `codex/08-workflows`, delete the dumps. Slim `DEPENDENCIES.md` / `ARCHITECTURE.md`.
- [ ] [DOCS] P0. **deployment-service** (79) — deploy-flow/infra/bucket/VM-tarball docs vs `codex/05-infrastructure`,
      `codex/08-workflows`. Highest duplication surface.
- [ ] [DOCS] P0. **unified-api-contracts** (36) — schema/contract docs vs `codex/02-data`.
- [ ] [DOCS] P0. **market-data-processing-service** (22) — path/manifest/candle docs vs `codex/02-data`.
- [ ] [DOCS] P0. **execution-service** (20) — execution-arch/venue docs vs `codex/04-architecture`, `codex/02-venues`.
- [ ] [DOCS] P0. **instruments-service** (19) — IS→MTDS contract/path docs vs `codex/04-architecture`, `codex/02-data`.
- [ ] [DOCS] P1. **strategy-service** (15) — archetype/promote docs vs `codex/09-strategy`, `codex/04-architecture`.
- [ ] [DOCS] P1. **unified-trading-library** (15) — events/cloud/bucket docs.
- [ ] [DOCS] P1. **e2e-testing** (21) — defi/sports/prediction runbooks vs `codex/08-workflows`, `codex/15-runbooks`.
- [ ] [DOCS] P1. **agent-orchestrator** (10) — vs `codex/12-agent-workflow`, `codex/04-architecture`.
- [ ] [DOCS] P2. **deployment-api** (8) / **client-reporting-api** (8) / **alerting-service** (8).
- [ ] [DOCS] P2. **trading-agent-service** (7) / **ibkr-gateway-infra** (4) / **batch-live-reconciliation-service** (1)
      / **system-integration-tests** (1).
- [ ] [DOCS] P2. **deployment-ui** (3) / **user-management-ui**.
- [ ] [DOCS] P3. **unified-trading-system-ui** (152) — audit only data/path/contract docs; leave genuine UI docs.

### FIX-STALE pass-1 — landed 2026-06-01 (operator chose FIX-STALE-only; DELETEs/REDIRECTs held), ~340 fixes on LDR

deployment-service@`9627260`; instruments-service@`8bea654`+`9ecc4b2`; execution-service@`4b0ea42f`;
market-data-processing-service@`89161dc`; strategy-service@`80d298fe`; e2e-testing@`0de5471`;
unified-trading-library@`168e649`+`c88278b`; market-tick-data-service@`d97ca3c`.

- [ ] [DOCS] P2. **Follow-up: URDI still in instruments-service CODE** — docs URDI refs fixed, but code still uses URDI
      symbols (`URDI` is a phantom name per CLAUDE.md). Audit + rename in instruments-service.
- [ ] [DOCS] P2. **AUDIT-03 F-45 codex update** (from `archive/issues/audit03_ikenna_review_routing_2026_05_22.md`):
      code wins — events GCS path keys on `instance_id`; `correlation_id` is a column, NOT a path key. Update the codex
      doc(s) that say correlation_id is a path key to match the implemented `instance_id` path semantics.
- [ ] [DOCS] P2. **AUDIT-03 F-06 codex FIX-STALE** (from same): declare `codex/04-architecture/custody-providers.md` the
      **entity-governance SSOT**; entities = **Odum Research UK** + **Odum Group Cayman**; **scrub all stale Elysium
      references** (Elysium is a removed provider per CLAUDE.md).
- [ ] [DOCS] P2. **gcs_hive partition-path doc FIX-STALE** (from
      `archive/issues/gcs_hive_partition_malformed_paths_remediation_2026_06_01.md` — operator: doc-fix only; the GCS
      data remediation stays operator-deferred): fix the malformed hive-partition path examples in the relevant codex
      doc to canonical `key=value` form.
- **Parked — features-service**: another agent active; LDR branch-protected. Docs commit `b9b4103e` on
  `origin/tab/hk/10`; PR #4 bundles a foreign commit (`603c2b9c`) — do NOT merge as-is. Left for the owning agent; no
  git surgery.

### 8-repo read-only audit registry (DELETE / FIX-STALE / REDIRECT / KEEP)

**deployment-service (~52)** — DELETE: MASTER_ML_IMPLEMENTATION_PLAN, ML_IMPLEMENTATION, MASTER_IMPLEMENTATION_INDEX,
GCS_LIFECYCLE_AGGRESSIVE_STRATEGY, GCS_LIFECYCLE_COST_OPTIMIZATION, BIGQUERY_INTEGRATION_GUIDE,
MAX_WORKERS_UNIFIED_IMPLEMENTATION_PLAN, IMPLEMENTATION_MAX_WORKERS, RESOURCE_MONITORING_AND_RIGHTSIZING, SPECS,
UI_TYPESCRIPT_TYPES, specs/PLANS_ALIGNMENT, specs/README, archive/\*. FIX-STALE: TESTING, setup, INFRASTRUCTURE,
local-dev/local-run-guide, INDEX, README. REDIRECT: COST, HARDENING, MIGRATION, CLOUD_AGNOSTIC_MIGRATION, RUNBOOKS,
GCS_PATHS, SCHEMA_VALIDATION, GCS_AND_SCHEMA, CACHE_AND_STATE, LIVE_MODE, CLOUD_BUILD_SUCCESS_CHECKLIST,
GITHUB_TOKEN_CLOUD_BUILD, STANDARDIZED_EVENT_LOGGING, COMPREHENSIVE_SERVICE_AUDIT_FRAMEWORK, E2E_SPECS, UI_SPEC. KEEP:
SHARDING_AND_DATA_ALIGNMENT, VM_HEALTH_AND_GCSFUSE_OPTIMIZATION, hybrid-live-seam, dev-environment, CONFIGURATION,
ARCHITECTURE, DEPLOYMENT_GUIDE, cli, service-bundling-review, resource-profiles/\*.

**unified-api-contracts (36)** — FIX-STALE: SCHEMA_GOVERNANCE (deleted `canonical/normalize/`+`schemas/`), MOCKS_AND_VCR
(old cassette path), SCHEMA_CHANGELOG (deleted flat modules). DELETE: ICLOUD_REPO_MIGRATION_PROMPT,
SCHEMA_NORMALIZATION_GAPS_AUDIT, UAC_FULL_GAP_ANALYSIS_AND_BATCH_LIVE_SYMMETRY, VIX_LIVE_RESEARCH. REDIRECT:
PACKAGE_LAYOUT_AND_SCOPE, BATCH_LIVE_SYMMETRY, canonical-instrument-ids. KEEP: README, ARCHITECTURE, SCHEMA_AUDIT_MATRIX
(generated), TESTING, archive/\*.

**market-data-processing-service (22)** — FIX-STALE: DEPLOYMENT_GUIDE_FEMI (un-tiered + hyphen partitions), GCS_PATHS
(un-tiered), DEPENDENCIES (`{category}` vocab + un-tiered). DELETE: REFACTORING_STANDARDS_COMPLIANCE,
specs/PLANS_ALIGNMENT, DEPLOYMENT_GUIDE (stub), TESTING (stub). REDIRECT: SCHEMA_VALIDATION_AND_TIMEFRAME_SUFFIXING_E2E,
UNIFIED_SCHEMA_AND_CLIENT_USAGE_GUIDE, TIMEFRAME_AGGREGATION_SPECIFICATION.

**execution-service (20)** — DELETE: UNIFIED_BATCH_LIVE_ARCHITECTURE (deleted codex file),
CLEAN_ALGORITHM_INTERFACE_DESIGN, DEFI_INTEGRATION_TODO. FIX-STALE: ARCHITECTURE (split execution-store-\* bucket
literals), README (py3.11 vs 3.13), BACKTEST_DEPLOYMENT (SHAHRIYAR spec). REDIRECT: GCS_PATHS, ROUTING_MATRIX,
CONFIGURATION, ERROR_HANDLING, DEPLOYMENT_GUIDE. KEEP: TESTING, SCHEMA_VALIDATION, BACKTEST_QUICKSTART, DEPENDENCIES,
TROUBLESHOOTING, TRADE_ANALYTICS_INTEGRATION, VISUALIZER_QUICKSTART, specs/\*.

**instruments-service (19)** — FIX-STALE: instrument-catalogue (un-tiered + URDI + `category=`), README (URDI ×9).
DELETE: specs/CLOUD_OPERATIONS, specs/COMMAND_FLOW_ANALYSIS, specs/COMMAND_FLOW_DIAGRAM (dead
`unified-trading-services`), specs/CORPORATE_ACTIONS, specs/SETUP_GUIDE, specs/TEST_ALIGNMENT. REDIRECT:
specs/MVP_INSTRUMENTS, specs/SECRETS_SETUP, specs/INSTRUMENT_SPECIFICATION. KEEP:
{CEFI,DEFI,TRADFI,SPORTS}\_INSTRUMENTS, POLYMARKET_PREDICTION, ARCHITECTURE.

**unified-trading-library (15)** — FIX-STALE: CLOUD_API_PATTERNS (`client.bucket()` anti-pattern), README
(`setup_cloud_logging` + pip). REDIRECT: ERROR_HANDLING, ARCHITECTURE, PATTERNS, ID_NAMING_CONVENTIONS, DEPENDENCIES,
CONFIGURATION, DEV_SETUP, data-sink-validation. DELETE: specs/README (stub). KEEP: TESTING, CLOUD_BUILD_TRIGGER_SETUP,
UTL_ADOPTION_MATRIX, README, specs/PLANS_ALIGNMENT.

**strategy-service (15)** — FIX-STALE/REDIRECT: STRATEGY_MODES (retired `basis-strategy-v1` + dead links), CLI_REFERENCE
(`batch only` violates batch=live). DELETE: BACKTEST_ENGINE (dup). REDIRECT: BACKTESTS, ARCHITECTURE, GCS_PATHS. KEEP:
archetype_registry_discovery, DEPLOYMENT_GUIDE, CONFIGURATION, CONFIG_SCHEMA, SCHEMA_VALIDATION, DEPENDENCIES, TESTING,
ERROR_HANDLING, specs/\*, README.

**e2e-testing (21)** — DELETE: defi/UI_DEMO_WALKTHROUGH (Elysium/removed-provider creds). FIX-STALE: VM_BACKFILL_GUIDE
(missing lifecycle_class + gsutil), sports/ROADMAP (past trial dates → migrate to epic). REDIRECT:
defi/PAPER_LIVE_CONVERGENCE, E2E_PIPELINE_GUIDE, architecture. KEEP: sports/LIVE_ODDS_PROVIDERS, \*/progress, \*/issues,
coverage-matrix, \*/per-strategy-acceptance, \*/smoke-test-baseline.
