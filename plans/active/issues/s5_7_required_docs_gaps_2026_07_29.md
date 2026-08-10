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
archive_exempt:
  true # 0-open-todos 2026-08-10 (last todo closed per operator ruling BLK-2b076fa9); archival
  # blocked by codex_vs_repo_docs_ssot_audit_2026_06_01.md (active, parent audit plan) still referencing this doc —
  # archive_exempt bridges until the parent plan itself reaches a terminal status
nature: notes
asset_group: [infrastructure]
stage: [meta]
repos: [market-data-processing-service, instruments-service, unified-api-contracts, agent-orchestrator, e2e-testing]
scope: [engineer, admin]
tags: [documentation-standards, s5-audit, required-docs, ssot, plan-hygiene]
related: [/plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md]
created: 2026-07-29
author: unknown
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
last_updated: "2026-08-10"
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

- [x] ✅ [DOCS] P2. **DECIDED + DONE 2026-08-08 — Tier the S5.1 required-docs set by repo type.** OPERATOR RULING: yes,
      tier it — non-data-writing repos (`agent-orchestrator`, `e2e-testing`, `system-integration-tests`,
      `ibkr-gateway-infra`, `batch-live-reconciliation-service`) mark `GCS_PATHS.md`/`SCHEMA_VALIDATION.md` as
      not-applicable instead of missing; every other repo keeps the full S5.1 set. Codified in
      `/codex/06-coding-standards/documentation-standards.md` new § S5.1a (+ S5.7/S5.10 cross-refs updated to match).
      (repo: unified-trading-pm)
- [x] ✅ [DOCS] P2. **CLOSED 2026-08-10 — operator ruling BLK-2b076fa9 option A: DELETE wins.** The
      `codex_vs_repo_docs_ssot_audit_2026_06_01.md` 2026-07-27 refreshed registry classifies
      market-data-processing-service's `DEPLOYMENT_GUIDE.md` + `TESTING.md` as DELETE — that ground-truthed audit is the
      more recent, more authoritative verification. The existing stubs (`DEPLOYMENT_GUIDE_FEMI.md` / `TESTING_GUIDE.md`)
      already cover whatever real content existed. No redirect stubs needed; the DELETE classification stands. If the
      FILL direction's author had newer evidence the two files became load-bearing again since 2026-07-27, that would
      need to be stated explicitly — which it is not. (repo: unified-trading-pm)
- [x] ✅ [DOCS] P3. **DECIDED + DONE 2026-08-08 — Reconcile instruments-service's reorganized docs against the S5.1
      filename set.** OPERATOR RULING: add thin redirect stubs at the canonical filenames pointing at the reorganized
      docs. Added 6 stub files under `instruments-service/docs/` (`ARCHITECTURE.md` → `ADAPTER_ARCHITECTURE.md`;
      `CONFIGURATION.md` → `SETUP_GUIDE.md` §4-6; `GCS_PATHS.md` → `SETUP_GUIDE.md` §7.1 + `ADAPTER_ARCHITECTURE.md`'s
      storage/bucket-resolution section; `DEPLOYMENT_GUIDE.md` → `SETUP_GUIDE.md` §2/§9; `TESTING.md` → `SETUP_GUIDE.md`
      §8; `SCHEMA_VALIDATION.md` → `ADAPTER_ARCHITECTURE.md`'s schema-validation stage +
      `/codex/02-data/schema-governance.md`), each pointing at the real reorganized content per S5.11's redirect-doc
      template. (repo: instruments-service)

## Progress Log

- **plan_reconciler infra tranche 2026-08-10 (BLK-2b076fa9 resolved)**: Operator ruled option A — DELETE wins.
  `codex_vs_repo_docs_ssot_audit_2026_06_01.md`'s 2026-07-27 ground-truthed registry is the authoritative
  classification. Todo 2 (FILL/redirect-stubs for MDPS `DEPLOYMENT_GUIDE.md`/`TESTING.md`) closed as moot — the existing
  content under different names is sufficient, and the SSOT audit's DELETE classification stands.
  `unified-trading-pm@<pending-sha>`.
- **ag-closeout-audit 2026-08-10 (infra tranche)**: Resolved the 2026-08-08 conflict by logic, not escalation — the
  competing claim (`codex_vs_repo_docs_ssot_audit_2026_06_01.md`'s dated, specific 2026-07-27 refreshed registry entry,
  still `status: active`) is the more authoritative, more recent, more direct evidence, and it matches the
  already-executed instruments-service precedent exactly (same redirect-stub pattern, same operator ruling session).
  Corrected the open todo below from "fill genuine gaps" to "verify + add redirect stubs," citing both sources. Not
  itself extracted into a batch this run (the corrected todo is bounded/conflict-clear, but a live per-file content
  verification is warranted before dispatch — see `infra_satellite_ao_dispatch_batch15_2026_08_10.md` if drafted).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — but with a real conflict found, not a
  clean RECLASSIFY. Re-read end-to-end; `grep -cE '^- \[ \]'` = 1, matching (the market-data-processing-service
  `DEPLOYMENT_GUIDE.md`/`TESTING.md` fill item). Today's operator ruling (item 76) is a strong candidate for closing the
  "scoping judgment" gate this todo previously cited — but conflict-checking against the active
  `codex_vs_repo_docs_ssot_audit_2026_06_01.md` (`assigned_vm: planning`, `status: active`) surfaced a direct
  contradiction: that plan's own refreshed 2026-07-27 registry classifies market-data-processing-service's
  `DEPLOYMENT_GUIDE.md` and `TESTING.md` as **DELETE** ("stub → FEMI" / "stub, `pytest` direct → TESTING_GUIDE") —
  meaning real content for these two S5.1 filenames may already live under different names (`DEPLOYMENT_GUIDE_FEMI.md`,
  `TESTING_GUIDE.md`), the SAME "naming/structure drift vs the fixed S5.1 filename set" pattern this doc's own text
  already flagged for instruments-service. If so, the correct fix here may be S5.11 redirect stubs (the exact precedent
  the operator just set for instruments-service in item 77), not net-new content — but that determination needs a real
  per-file content check this pass didn't run, and flipping `assigned_vm` on a todo that may conflict with an
  already-dispatched plan's DELETE classification would risk two active plans giving contradictory instructions for the
  same 2 files. Per "Conflict → don't flip" — leaving this open, flagging the conflict clearly rather than forcing
  either resolution. `assigned_vm: NA` stays correct pending reconciliation.
- **2026-08-08 (operator Q&A round5, infra tranche, items 76/77)**: Operator ruled both open scoping questions in one
  session — (76) tier S5.1 by repo type: yes; (77) instruments-service reorg vs S5.1 filenames: thin redirect stubs.
  Flipped both todos above to done with the ruling + evidence. The remaining open todo ("fill the genuine
  market-data-processing-service gaps") is now a bounded, worker-determinable doc-writing task (no longer scoping
  judgment) — worth a fresh RECLASSIFY look in a future na-eligibility-audit pass, not actioned this run (out of this
  session's scope).
- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid — unchanged since 2026-07-30. Re-read end-to-end;
  `grep -cE '^- \[ \]'` = 3, matching. All 3 todos remain gated on the same operator/main scoping decision (should S5.1
  tier its required-docs set by repo type) explicitly named in the doc's own text; only context-scout scope refreshes
  have touched the doc since. No new evidence.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Doc explicitly
  self-classifies as a scoping judgment ('should S5.1 tier its required set by repo type?'), not a bounded worker todo,
  per the doc's own text citing the dispatch-scope-eligibility ruling.

- **context-scout 2026-08-03**: refreshed context_scope (2 entries, unchanged — still accurate).
- **context-scout 2026-08-03** (re-scout pass, updated methodology): re-verified both entries resolve on disk (codex
  documentation-standards SSOT + the parent Phase-5 audit plan). No source-code path added — this doc is a code-free
  scoping-judgment recommendation (tiering S5.1's required-doc set by repo type), not an implementation fix, so no
  source target applies. No changes.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (2 entries), unchanged.

- **context-scout 2026-08-09**: populated/refreshed context_scope (2 entries).
