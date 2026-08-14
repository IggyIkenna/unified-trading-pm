---
doc_type: plan
title: ui satellite AO dispatch batch 4 — 2026-08-13
summary: >-
  Extraction batch from the ui tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep — 11
  conflict-cleared, bounded/deterministic items pulled directly from 5 source docs (RECLASSIFY_SPLIT bounded items from
  the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each todo
  cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation back
  into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [ui]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ui, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md,
    /plans/active/issues/plan_reconciler_findings_2026_08_07.md,
    /plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md,
    /plans/active/issues/plan_reconciler_findings_ui_2026_08_11.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.6
estimate_calibrated_ai_days: 1.3
assigned_role: ui_developer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# ui satellite AO dispatch batch 4 — 2026-08-13

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] ✅ [CODE] P2. Re-run pw:L2 full smoke suite and flip the 3 CODE-SHIPPED todos (venue-filter frontend, duplicate
      available/available-dates panel collapse, pagination visible-count selector) if it exits 0 — exit 0 confirmed
      (450/450), 3 items flipped in the source doc. A pre-existing unrelated blocker (stale hardcoded
      `capability_tab.spec.ts` manifest counts, missed by fix(capability) 6a323bf) was root-caused + fixed inline:
      deployment-ui@`d95f1934ef`. Source: `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md`
- [x] ✅ [CODE] P2. Ship the small Rollup-difference-clarity UI tooltip/note (audit §F, by-design explainer) —
      CODE-SHIPPED deployment-ui@`8033b83651`. Extended the existing `InstrumentsServiceShardModal` note
      (`DataStatusDrilldown.tsx`) with a hover-tooltip explainer + inline text: IS's per-venue/day drilldown has no
      data_type axis by design (reference data), vs MTDS's 5-axis market-data shards — so the structural difference
      reads as intentional, not broken. **pw:L2 ✓** (full `tests/smoke/` re-run, 450/450 passed via 2-shard split) |
      regression: `tests/unit/components/DataStatusDrilldown.test.tsx` (new test: "explains the by-design structural
      difference vs MTDS's 5-axis shards for instruments-service"). Source:
      `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md`
- [x] ✅ [CODE] P2. Investigate + resolve the Yahoo/Kalshi market-tick-view out-of-scope registry check (add to
      EXPECTED_COVERAGE_BY_ASSET_GROUP if genuinely provided, else confirm correct-by-design) Source:
      `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md`. **CONFIRMED CORRECT-BY-DESIGN, no code
      change needed** — both cases investigated live against current code (2026-08-14): 1. **YAHOO_FINANCE**: the
      June-reported symptom is structurally impossible today — `YAHOO_FINANCE` was removed as a venue token entirely on
      2026-07-15 (`data_status_tab_and_downloads_remediation_2026_06_16.md`'s todo predates that fix), an UNRELATED
      source-as-venue modeling correction (Yahoo is a SOURCE, not a venue; Yahoo-sourced rows now land under their REAL
      venues — DXY→ICE, KRW/USD→FX — tagged `source=yahoo`). Confirmed via
      `unified-api-contracts/unified_api_contracts/registry/expected_coverage.py:140,201`, `venue_adapter_keys.py:139`,
      `market_data_categories.py:521,850` (all cite the same 2026-07-15 removal; `market_data_categories.py:858-863`'s
      `TRADFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES` explicitly documents the pre-removal manifest rows as "genuinely
      dead, not a registry gap" via a bounded manifest spot-check at day=2025-01-02). No `venue=YAHOO_FINANCE` row can
      reach the market-tick-view `is_expected()` check anymore — nothing to add. 2. **KALSHI ohlcv_1m**: confirmed
      genuinely NOT provided — `KALSHI` is already correctly scoped to `["trades", "book_snapshot_5"]` in
      `expected_coverage.py:503` (`_PREDICTION`), and
      `market_tick_data_service/market_interface/adapters/prediction/kalshi_adapter.py` has NO ohlcv fetch path at all
      (grep for `ohlcv`/candle methods: zero hits — only trades/batch-trades methods exist). Kalshi is a CLOB prediction
      market; raw OHLCV bars are not a data shape it exposes (trades + order-book snapshots are the real granularity) —
      `out_of_scope=True` for `(KALSHI, ohlcv_1m)` correctly signals "this source doesn't provide this data_type",
      exactly the doc's own hypothesis. No registry entry to add. No repo touched — this was a verification-only todo
      with a correct-by-design outcome on both venues.
- [x] ✅ [CODE] P2. Root-fix the per-service coverage BucketNamingError for
      features-calendar/ml-service/features-cross-instrument — **ALREADY ROOT-FIXED, verified live against current
      deployment-api code (2026-08-14), no new change needed.** All 3 sub-cases from the source doc's P3 follow-up
      confirmed resolved: (1) **features-cross-instrument-service**: `_resolve_defi_main_bucket` in
      `deployment_api/services/data_status/defi.py:265-276` resolves per-AG kinds WITH `asset_group` (not kind-only) on
      the prediction branch — landed `deployment-api@c1aab6e` (2026-06-17), still present at current HEAD. (2)
      **features-calendar-service / ml-service (SHARED pseudo-key)**: `_resolve_defi_main_bucket` returns `None` for
      `ag == "shared"` (`defi.py:257-264`) — an intentional honest-skip, never calls
      `resolve_bucket_name(asset_group='shared')`, so `BucketNamingError` cannot raise — landed `deployment-api@b014ae9`
      (2026-06-17), still present. Real cross-asset SHARED coverage (vs. honest-empty) is a distinct, larger feature
      deliberately deferred by design (not a bug) — its tracking plan
      `instruments_mtds_subset_consistency_remediation_2026_06_17.md` is `status: complete`/archived and was itself
      3-way split (`instruments_store_cf_canonicalization_single_walk_2026_07_24.md`,
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`,
      `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`) — out of THIS todo's bounded scope (root-fixing
      the error, not building the SHARED-coverage feature). (3) A separate resolver path
      (`deployment_api/services/data_status_drilldown.py::build_bucket_name`) also already carries a regression test —
      `TestBuildBucketName.test_every_service_to_kind_entry_resolves_a_real_bucket` (parametrized over every
      `SERVICE_TO_KIND` entry incl. `ml-service`/`features-calendar`, `tests/unit/test_data_status_drilldown.py:1020`) —
      guarding the sibling `data_status_rollup_ml_service_full_blob_missing_2026_07_26` bucket-alias bug class. No repo
      touched — this was a verification-only todo; the root-fix commits predate this batch plan. Source:
      `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md`
- [ ] [DOC] P3. Add a one-line cross-file conflict-check note to
      ui_satellite_ao_dispatch_batch3_finalize_2026_08_09.md's todo 1, naming
      ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md's still-open todo 4 as a same-file
      (artifact_pipeline_observability_2026_07_17.md) dispatch-collision risk. Source:
      `plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md`
- [x] ✅ [CODE] P2. Port the manual-trigger action into the new /ops/artifacts page; remove CloudBuildsTab from the
      per-service tab bar + DeployConsole; delete CloudBuildsTab.tsx (Phase 4) — deployment-ui@9d5ad0d105. Added a
      "Trigger build" popover to the Pipeline view's toolbar (service/branch picker → `triggerCloudBuild`, lazy-loads
      `getCloudBuildTriggers` on open, refreshes the builds table on success); removed the "Builds" tab from HomeShell's
      per-service tab bar and DeployConsole's "Build history" view; deleted `CloudBuildsTab.tsx` (no shim). Found +
      fixed in the same change: the mock API router only matched the unprefixed `/cloud-builds/trigger` POST path, so
      every real `triggerCloudBuild()` call 404'd against the mock — a pre-existing gap CloudBuildsTab shared but was
      never pw:L2-covered enough to catch. **pw:L2 ✓** (full
      `--project=chromium tests/smoke/artifact-pipeline.spec.ts tests/smoke/cockpit.spec.ts` re-run, 53/53 passed) |
      regression: `tests/smoke/artifact-pipeline.spec.ts` (new case: "Pipeline: the Trigger build popover fires a manual
      build and refreshes the table (Phase 4 port)") + `src/pages/ArtifactPipeline.test.tsx` (new Vitest case asserting
      lazy-fetch, submit, and builds-table refresh). Full deployment-ui gate green (102 Vitest tests, build, typecheck,
      lint). Not in this todo's scope (batch4's title doesn't cite it): "Fold RepoCi ImageCell fields into the new
      columns" — that's a distinct sentence trailing the same source-doc checkbox, left for the source doc's own
      reconciliation. Source: `plans/active/artifact_pipeline_observability_2026_07_17.md`
- [ ] [BACKEND] P2. Retire the superseded narrow deployment-api build/artifact routes once the new artifact_pipeline
      service covers them; delete dead code (Phase 4) — retagged `[CODE]` → `[BACKEND]` 2026-08-14 (ui_developer slot-14
      craft-mismatch catch): the work is Python-only
      (`deployment-api/routes/{cloud_builds,_cloud_builds_*,     _code_builds_aws,builds_history}.py` + their `main.py`
      registrations + tests) — no TS/React surface, out of ui_developer's craft (`agents/ui_developer.md` does_not:
      Python service code). Source: `plans/active/artifact_pipeline_observability_2026_07_17.md`
- [ ] [BACKEND] P2. Build→deploy latency join: 'built but never deployed' + build-to-first-revision latency (Phase 6
      stretch) — retagged `[CODE]` → `[BACKEND]` 2026-08-14 (ui_developer slot-7 craft-mismatch catch, same class as the
      routes-retirement todo above): the work is a new `_condition()` derivation in
      `deployment-api/deployment_api/services/artifact_pipeline/service.py` (join `BuildFact` ↔ `DeployFact` by
      digest/sha, compute build-finished→first-deploy latency + flag builds with no matching deploy) — the Health tab's
      row rendering (`deployment-ui/src/pages/ArtifactPipeline.tsx`) is already fully generic (`data.conditions.map`, no
      per-condition-type UI), so this todo has zero TS/React surface, out of ui_developer's craft
      (`agents/ui_developer.md` does_not: Python service code). Source:
      `plans/active/artifact_pipeline_observability_2026_07_17.md`
- [ ] [BACKEND] P2. Add a deploy-churn/crash-loop health condition (e.g. a service redeployed ~14x in hours, ~40%
      config-only) (Phase 6 stretch) — retagged `[CODE]` → `[BACKEND]` 2026-08-14 (same craft-mismatch catch as the todo
      above): also a pure `_condition()` derivation over already-fetched `DeployFact`s in
      `deployment-api/deployment_api/services/artifact_pipeline/service.py`, rendered by the same generic Health table —
      no TS/React surface. Source: `plans/active/artifact_pipeline_observability_2026_07_17.md`
- [x] ✅ [CODE] P2. Resolve the ACTIVE_INDEX.md dangling normative-ref: edit
      cursor-configs/skills/plan-reconcile/SKILL.md (lines 5,59,425) + agents/plan_reconciler.md (line 114) to drop the
      stale name and cite only INDEX.md, or regenerate ACTIVE_INDEX.md if a distinct artifact was genuinely intended —
      `plans/ACTIVE_INDEX.md` DOES exist (not dangling) but self-declares STALE/superseded-by-`plans/active/INDEX.md`
      since 2026-07-14, so "genuinely distinct artifact" doesn't apply — dropped the stale name, both files now cite
      only `INDEX.md` as a normative ref: unified-trading-pm@`<SHA>`. Source:
      `plans/active/issues/plan_reconciler_findings_2026_08_07.md`
- [ ] [CODE] P2. Expand the ui-tranche doc discovery/inventory logic (used by /plan-reconcile ui and /ag-closeout-audit
      ui) to include multiline-frontmatter `asset_group:` docs missed by same-line grep (named examples:
      data_status_tab_and_downloads_remediation_2026_06_16.md, deployment_registry_firestore_migration_2026_07_14.md).
      Source: `plans/active/issues/plan_reconciler_findings_ui_2026_08_11.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
