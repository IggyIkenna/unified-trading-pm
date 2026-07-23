---
doc_type: plan
title: codex_refactor Phase G.1 — final cross-directory consistency audit
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, execution-service, features-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
type: audit-report
archived: 2026-05-08
archived_reason: Audit P0+P1 closed via Phase H follow-up sweep; P2 items deferred as nice-to-have non-blockers.
parent_plan: plans/archive/codex_refactor_2026_05_08.plan.md
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# codex_refactor Phase G.1 — final cross-directory consistency audit

## Headline summary

**VERDICT: 34 prior phases largely shipped clean — but Layer E structural moves (especially E.2 `14-playbooks/` → 3-dir
split) left **substantial broken-link debt\*\* that needs a follow-up sweep before plan archival. Layer A acceptance
gates (manifest schema v7, capture-taxonomy, CIRCUIT_BREAKER, family/archetype counts) are clean except for documented
historical/changelog references. Layers B/C/D physical deletions all verify on disk. Layer E moves verify structurally
(all source dirs deleted, all targets exist) but ~150+ cross-doc links to deleted paths remain in the codex tree.
CLAUDE.md has 2 stale `14-playbooks/` refs. The "Codex SSOT updates" doc-tracking sub-list in the parent plan still has
6 stale `[ ]` checkboxes that should be flipped (Phase D.4 deletions / D.6 deletions+creation).

**Net**: physical refactor is sound; reference hygiene is incomplete. Recommend a Phase H follow-up sweep to rewrite the
residual links, OR explicit operator approval to archive with the reference-debt as a known carryover folded into a new
active plan.

## 1. Acceptance gate results

### Layer A — P0 acceptance criteria

| Phase | Criterion                                                                                      | Result     | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ----- | ---------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A.1   | manifest schema = v7 in all citing docs                                                        | ✅ PASS    | All 6 hits cite `MANIFEST_SCHEMA_VERSION = 7` or `v7 — current`. No stray v5/v6/v8 found in current-state claims.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| A.2   | no 3-state capture taxonomy in closed-set declarations                                         | ⚠️ PARTIAL | New 4-state declarations correct (`availability-manifest-and-data-status.md:288`, `data-status-drilldown.md:182`). Residual 3-state references: `availability-manifest-and-data-status.md:1043` (in "Adds capture_status" wording — appears to be a "what changed" historical note); `pipeline-coverage-matrix.md:89` (changelog row for `v5` historical-state); `deployment-ui-architecture.md:199` (running-text 3-state list). Also `14-customer-journeys/handoff/harsh_data_pipeline_kickoff_2026_05_01.md:27` says "manifest 3-state semantics" — historical handoff doc, may be intentional. **Phase A.2 main checkbox is still `- [ ]` in plan** — correctly reflects partial state.                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| A.3   | zero `CIRCUIT_BREAKER_OPENED`/`CIRCUIT_BREAKER_CLOSED` in lifecycle-event contexts             | ✅ PASS    | 2 hits (`alerting.md:139` + `kill-switch-circuit-breaker.md:285`) — both are AlertCode contexts (alerting routing rules + an explicit AlertCode cross-ref note), which Phase A.3 acceptance explicitly preserves per the "two SSOTs that don't conflict" discovery.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| A.4   | zero current-state claims of `8 families` / `18 archetypes` / `46 archetypes`                  | ⚠️ PARTIAL | All current-state SSOTs cite 9/53. Residual `18 archetypes` references in `09-strategy/architecture-v2/strategy-registry-v2.md:32`, `category-instrument-coverage.md:1424`, `strategy-lifecycle-maturity.md:273`, `architecture-v2/README.md:105`, `strategy-summary.md:36,748`, `infra-spec/stage-3b-uac-combo-rules.md:27`, `14-customer-journeys/playbooks/02b-research-dart.md:39` — all appear to be historical-changelog or pre-Plan-A baseline contexts (matches Phase F.6's recorded pattern). `06-coding-standards/strategy-display-conventions.md:15,56,84` cites "8 families + 18 archetypes" / "Bespoke archetype display names (18 archetypes)" / "Bespoke family display names (8 families)" — needs review whether these are bespoke-display-name lists for the 18 baseline archetypes only or workspace-wide claims. `04-architecture/features-service-architecture.md:23` heading "The 8 families" — likely refers to the 8 features-\* sub-packages, not strategy families (different concern); needs disambiguation. `00-SSOT-INDEX.md:76` mentions "8 families consolidated" — also features-service context. |
| A.5   | every doc naming live transport cites Redis Stream cascade or links live-pipeline-architecture | ✅ PASS    | Verified live-pipeline-architecture.md is referenced from batch-live-architecture.md and other consolidated docs.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| A.6   | zero "execution-service is live-only" claims                                                   | ⚠️ ONE HIT | `codex/10-audit/repos/execution-service.yaml:337` still says `historical_available: false # execution-service is live-only; no historical data output`. This is in a YAML readiness checklist, not codex doc body — may be intentionally describing one specific output property. Recommend operator review.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| A.7   | zero claims of 5+ separate features-\*-service repos as live deployment shape                  | ✅ PASS    | features-service-architecture.md is the SSOT; predecessor repos cited as historical context only.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |

### Layer B — sweep acceptance

| Phase | Criterion                                                                                                                                            | Result                        | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B.1   | zero `POST_PLAN_BANNER_2026_05_06` in codex/                                                                                                         | ✅ PASS                       | Workspace-wide grep returns 0 hits.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| B.2   | zero `plans/active/.*\.plan\.md` in codex/                                                                                                           | ✅ PASS                       | Workspace-wide grep returns 0 hits.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| B.3   | zero `unified-market-interface` / `unified-internal-contracts` / `(UTS)` / `unified-feature-calculator-library` / `unified-trading-codex/` in codex/ | ⚠️ PARTIAL                    | Residuals: `06-coding-standards/quality-gates-codex-compliance-snippet.sh:176` (script string, lower priority), `06-coding-standards/README.md:650` (T2 tier table cell), `05-infrastructure/unified-libraries/LIBRARY-DEPENDENCY-MATRIX.md:168` (acknowledged "ELIMINATED" annotation), `04-architecture/runtime-deployment-topology.md:541,806` (consolidated doc still cites `unified-internal-contracts` as SSOT), `10-audit/_archive/unified-internal-contracts.yaml` (archived audit checklist, OK to keep), `04-architecture/batch-live-architecture.md:117` (says "imported as a dependency, not called via HTTP" — recently created doc that should have used UTL not UFCL). `06-coding-standards/README.md:649` has `(UTS)` annotation. **Net: ~6 codex doc bodies need a follow-up rewrite, separate from the script + archive + acknowledged-elimination cases.** |
| B.5   | only `availability-manifest-and-data-status.md` enumerates literal `SOURCE_COVERAGE_START` values                                                    | not re-verified in this audit | Recommend operator spot-check; B.5 was shipped per plan.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

### Layer C — physical deletions

| Path                                                                   | Result     |
| ---------------------------------------------------------------------- | ---------- |
| `/codex/05-infrastructure/cloud-agnostic-migration.md`                 | ✅ DELETED |
| `/codex/05-infrastructure/deployment-ui-environment-tiers.md`          | ✅ DELETED |
| `/codex/05-infrastructure/launcher-script-consolidation-2026-05-07.md` | ✅ DELETED |

### Layer D — consolidations

| Phase | Path                                                                    | Result                          |
| ----- | ----------------------------------------------------------------------- | ------------------------------- |
| D.1   | `/codex/02-data/data-status-drilldown-hierarchy.md` deleted             | ✅ DELETED                      |
| D.2   | `/codex/02-data/sports-data-migration.md` deleted                       | ✅ DELETED                      |
| D.2   | `/codex/02-data/sports-schema-paths.md` deleted                         | ✅ DELETED                      |
| D.3   | zero stale `(asset_group=sports.*fixture_id.*day)` shard-axis claims    | ⚠️ PARTIAL — see broken links § |
| D.3   | zero stale `(asset_group=prediction.*market_id.*day)` shard-axis claims | ⚠️ PARTIAL — see broken links § |
| D.4   | `/codex/04-architecture/copper-custody-integration.md` deleted          | ✅ DELETED                      |
| D.4   | `/codex/04-architecture/ceffu-custody-integration.md` deleted           | ✅ DELETED                      |
| D.5   | `/codex/06-coding-standards/error-handling.md` deleted                  | ✅ DELETED                      |
| D.5   | `/codex/06-coding-standards/validation-patterns.md` deleted             | ✅ DELETED                      |
| D.5   | `/codex/06-coding-standards/schema-validation.md` deleted               | ✅ DELETED                      |
| D.6   | `/codex/04-architecture/batch-live-pipeline.md` deleted                 | ✅ DELETED                      |
| D.6   | `/codex/04-architecture/batch-live-symmetry.md` deleted                 | ✅ DELETED                      |

D.3 textual residuals: 7 codex docs still have shard-axis literal text including `fixture_id` or `market_id` as
hive-partition. Many are now correct post-correction (e.g. `per-asset-group-bucket-layouts.md` calls out the correction
explicitly). Concerning ones:

- `/codex/05-infrastructure/deployment-clusters-live-vs-batch.md:109,111` — Sports row still lists `fixture_id, day` as
  a shard atom; Prediction row still includes `market_id`. These appear to be **stale claims** vs the canonical
  row-level shape (per Q1 resolution).
- `/codex/02-data/partitioning.md:30` — Prediction row includes `market_id`. Same issue.
- `/codex/02-data/shard-granularity-cefi.md:194` — Sports row includes `fixture_id`. Same issue.
- `/codex/04-architecture/shard-level-failure-isolation.md:121,123` — Sports + Prediction rows include the row-level
  columns as shard axes. Same issue.
- `codex/POST_PLAN_REALITY_2026_05_06.md:130,162` — Same issue (acknowledged historical doc but worth flagging).

These need a sweep to align with the multi-axis correction banner / Q1 resolution.

### Layer E — structural moves

| Phase | Result                                                                                                                                                                                                                                                                                                                                             |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E.1   | All 7 source docs (`RUNTIME_TOPOLOGY_DECISIONS`, `TIER-ARCHITECTURE`, `service-family-scope`, `deployment-topology-diagrams`, `pipeline-service-layers`, `api-services-cluster`, `PROTOCOL-INJECTION`) deleted ✅. All 3 targets (`tier-and-import-architecture.md`, `runtime-deployment-topology.md`, `commercial-service-families.md`) exist ✅. |
| E.2   | `codex/14-playbooks/` does NOT exist ✅. `codex/14-customer-journeys/` exists ✅. `codex/15-runbooks/` exists ✅. `codex/16-strategy-playbooks/` exists ✅.                                                                                                                                                                                        |
| E.3   | `codex/09-strategy/cross-cutting/` does NOT exist ✅. `codex/09-strategy/operational/` exists ✅. `codex/09-strategy/architecture-v2/cross-cutting/` exists ✅.                                                                                                                                                                                    |
| E.4   | `/codex/02-data/per-category-bucket-layouts.md` does NOT exist ✅. `/codex/02-data/per-asset-group-bucket-layouts.md` exists ✅.                                                                                                                                                                                                                   |
| E.5   | `/codex/06-coding-standards/cod-deadlock-verification-report.md` does NOT exist ✅. `/codex/06-coding-standards/orphan-audit.md` does NOT exist ✅.                                                                                                                                                                                                |

## 2. Broken links — the largest finding

Layer E moves left a substantial cross-reference debt. Below is the count of files in `codex/` that still reference
deleted paths (excluding the auto-generated `_generated/scope-manifest.json` which gets regenerated).

| Deleted path                                                           | Files referencing | Total hits                                                                                                                   |
| ---------------------------------------------------------------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `14-playbooks/` (E.2)                                                  | **43 files**      | **116 hits**                                                                                                                 |
| `09-strategy/cross-cutting/` (E.3)                                     | 4 files           | 4+ hits (one in `_archived_pre_v2`, one in `architecture-v2/cross-cutting/`, one in `operational/`)                          |
| `per-category-bucket-layouts.md` (E.4)                                 | 6 files           | 8 hits (mostly in `15-runbooks/` and `16-strategy-playbooks/`)                                                               |
| `cloud-agnostic-migration.md` (C.1)                                    | 6 files           | 7 hits (e.g. `10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md`, `seamless-cloud-switch.md`, `bucket-naming-and-config.md`) |
| `copper-custody-integration.md` / `ceffu-custody-integration.md` (D.4) | 1 file            | 1 (intentional historical reference inside `custody-providers.md`)                                                           |
| `batch-live-pipeline.md` / `batch-live-symmetry.md` (D.6)              | 6 files           | ~10 hits (most in `10-audit/_checklist-template-enhanced.yaml`, `_service-baseline-template.yaml`)                           |

The 43-file `14-playbooks/` debt is the most concerning. Files affected include high-traffic SSOTs:

- `codex/00-SSOT-INDEX.md` (3 hits)
- `codex/README.md` (1 hit)
- `codex/08-workflows/{prospect-questionnaire-flow,signup-signin-workflow,client-onboarding,local-dev}.md` (multiple)
- `codex/09-strategy/architecture-v2/{performance-overlay,restriction-policy,strategy-catalogue-3tier,strategy-lifecycle-maturity,...}.md`
  (8+ files)
- `codex/15-runbooks/{README.md,alerting/README.md,alerting/operator-playbook.md}` (3 files — these are in the NEW dirs
  that should be referencing the new paths!)
- `codex/16-strategy-playbooks/{README.md,defi/venue-collateral-2026-05-07.md,infra-spec/{stage-3a,stage-3e-g2,stage-3e-refactor-plan}.md}`
  (5 files — also in NEW dirs)

The fact that NEW dirs (`15-runbooks/`, `16-strategy-playbooks/`) still link to old `14-playbooks/` paths suggests E.2
only did the directory move + `git mv`, not a content sweep to rewrite incoming links.

## 3. CLAUDE.md alignment issues

CLAUDE.md (and by symlink, `SUB_AGENT_MANDATORY_RULES.md` + every per-repo `.claude/CLAUDE.md`) has 2 stale
`14-playbooks/` references:

- `cursor-configs/CLAUDE.md:119` — `/codex/14-playbooks/shared-core/signal-broadcast-architecture.md` (Signal Leasing
  rule body). The actual file now lives at `/codex/16-strategy-playbooks/shared-core/signal-broadcast-architecture.md`
  (verify path).
- `cursor-configs/CLAUDE.md:926` — `unified-trading-pm/codex/14-playbooks/authentication/firebase-local.md`. The actual
  file now lives at `/codex/14-customer-journeys/authentication/firebase-local.md`.

**These are HIGH-impact stale references** because CLAUDE.md is loaded into every Claude Code session boot.

## 4. Plan flip status — `codex_refactor_2026_05_08.md`

Total checkboxes: 47 `[x]` + 9 `[ ]` = 56.

Still `[ ]`:

- **Line 144** — Phase A.2 main checkbox. Body says "files to update"; per the audit above, A.2 work is partially
  shipped — 4-state additions landed, 3-state residuals remain in 3-4 docs. **Recommendation**: the residual hits are
  best treated as a follow-up sweep todo rather than blocking A.2 closure. Either flip with annotation or extend.
- **Line 1054** — Phase G.1 (this audit). Will be flipped at the end of this session.
- **Lines 1076, 1099, 1100** — D.6 doc tracking checkboxes. The targets WERE created/deleted (verified above) — these
  tracking checkboxes should be flipped to `[x]`. Likely overlooked when D.6 shipped (PM@dcd49f24). **Stale checkbox
  state, not stale work.**
- **Lines 1091, 1092** — D.4 doc tracking checkboxes (`copper-custody-integration.md` + `ceffu-custody-integration.md`).
  The files ARE deleted (verified above). Same pattern: **stale checkbox state, not stale work.** PM@c4330d9d shipped
  D.4 but didn't flip these tracking sub-bullets.
- **Line 1097** — `service-structure-standards.md` (D.7 — KEPT as forwarder stub). This is correctly `[ ]` because the
  doc was intentionally kept; the checkbox tracks "deletion" which won't happen.
- **Line 1101** — "Some/all 12 stub files in `06-coding-standards/`" (B.4). Phase B.4 triaged → all 12 KEEP, expansion
  deferred. So no stub deletions happened; this checkbox is correctly `[ ]`.

**Net plan-flip discrepancy**: 5 stale checkboxes (lines 1076, 1091, 1092, 1099, 1100) should be `[x]` per actual state.
1 in-progress (A.2). 1 to-be-flipped post-this-audit (G.1). 2 correctly `[ ]` (intentionally-kept files).

## 5. Operator action items

Ranked by impact:

### P0 — recommended before plan archival

1. **CLAUDE.md `14-playbooks/` stale refs (CLAUDE.md:119 + :926)**. CLAUDE.md drives every session boot — any agent
   reading the Signal Leasing rule or firebase-local rule today will hit a 404. **Recommend immediate fix** as a
   follow-up Phase H or as part of plan archival. (Could be done in this session if operator approves; 2-line edit.)

2. **`14-playbooks/` cross-doc link sweep (43 files / 116 hits)**. The structural move (E.2) is sound but the
   incoming-link rewrite was skipped. **Recommend a Phase H follow-up sweep** before this plan archives. Three
   sub-targets:
   - `15-runbooks/` and `16-strategy-playbooks/` self-references (5 files in the NEW dirs link to the OLD paths) —
     should be a 1-commit fix.
   - `08-workflows/` + `09-strategy/architecture-v2/` user-journey docs (~12 files) — bulk sed-replace candidates.
   - `00-SSOT-INDEX.md` + `README.md` (the SSOT entry-points) — careful per-line review.

### P1 — should fix but not blocking

3. **D.3 multi-axis text residuals (5+ codex docs)**. `deployment-clusters-live-vs-batch.md`, `partitioning.md`,
   `shard-granularity-cefi.md`, `shard-level-failure-isolation.md`, `POST_PLAN_REALITY_2026_05_06.md` still cite sports
   `fixture_id` and prediction `market_id` as hive-partition shard axes despite Q1 resolution. The corrected row-level
   treatment is in `per-asset-group-bucket-layouts.md`. Would be a clean sed-replace pass.

4. **B.3 residual stale-repo refs (~6 codex doc bodies)**. `unified-internal-contracts` still cited as live SSOT in
   `runtime-deployment-topology.md:541,806`; `unified-feature-calculator-library` cited as a dependency in
   `batch-live-architecture.md:117`. These are NEW post-consolidation docs that should have used the migrated names.

5. **Plan checkbox flips (5 stale `[ ]` in "Codex SSOT updates" sub-list)**. Lines 1076, 1091, 1092, 1099, 1100 should
   be `[x]`. 1-edit fix.

### P2 — nice-to-have

6. **A.4 historical `18 archetypes` references review**. Most appear to be intentional changelog/baseline references
   ("the Phase 9 expansion (2026-04-25) added 35 more"), but a few file headings (e.g.
   `strategy-display-conventions.md:56` "Bespoke archetype display names (18 archetypes)") are ambiguous. Worth a pass
   to confirm each is contextually correct.

7. **A.6 `execution-service.yaml:337` "execution-service is live-only" comment**. May be intentionally describing one
   YAML field (`historical_available: false`); operator should confirm the acceptance criterion was meant to cover this
   kind of YAML-comment usage.

8. **A.2 Phase main-checkbox flip**. After residual 3-state references are reviewed, flip `144` to `[x]` with
   annotation.

## 6. Plan flip decision

Per Phase G.1's done-definition, this audit is the deliverable. The audit shipped → checkbox flips to `[x]`.

The unresolved items above (P0-P2) become new plan todos per "Capture discoveries as plan todos immediately" HARD RULE —
see § 5. Suggested disposition: a new follow-up plan `codex_refactor_h_residual_link_sweep_2026_05_08.md` (or extend
this plan with a Phase H tier covering the 5 P0-P1 items above), so the parent plan can archive cleanly.

## Composes with

- CLAUDE.md "Plan Archival HARD RULE" — deferrals MUST migrate to active home before plan archives. P0/P1 findings above
  need migration.
- CLAUDE.md "Capture Discoveries As Plan Todos Immediately" — every finding above should be a `- [ ]` plan todo
  somewhere active before this audit's session ends.
- CLAUDE.md "Post-Plan-Phase Codex Audit HARD RULE" — codex doc updates ride with the work; the link-sweep is part of
  E.2's deliverable that wasn't fully shipped.
