---
doc_type: plan
title: UTL/UAC reuse consolidation — Phase 7 LOW + lint tail
summary:
  Close the remaining LOW-severity findings and lint ratchet tail — strategy-service noqa cleanup, execution-service
  cross-service import fixes, and the ~70-file scripts/ lint ratchet — after Phases 1-6 are green.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service, execution-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [utl, uac, consolidation, refactor, lint, ratchet, split]
related: [plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
locked_by: live-defi-rollout
locked_since: "2026-07-13"
supersedes:
superseded_by:
depends_on:
  [
    utl_reuse_phase1_strategy_risk_hwm_2026_07_13,
    utl_reuse_phase2_api_auth_dedup_2026_07_13,
    utl_reuse_phase3_ml_model_registry_2026_07_13,
    utl_reuse_phase4_features_builder_registry_2026_07_13,
    utl_reuse_phase5_deployment_api_cloud_sdk_2026_07_13,
    utl_reuse_phase6_venue_health_retry_2026_07_13,
  ]
gate_on_depends: true
source: [split from utl_uac_reuse_consolidation_remediation_2026_06_10 tracker, operator-approved 2026-07-13]
assigned_role: backend-engineer
drift_direction: advance-code
---

# UTL/UAC reuse consolidation — Phase 7 LOW + lint tail

> **Split provenance (2026-07-13):** Phase 7 of
> [`utl_uac_reuse_consolidation_remediation_2026_06_10.md`](utl_uac_reuse_consolidation_remediation_2026_06_10.md)
> (findings #14–#19). alerting-service, agent-orchestrator (all 6 read-migration waves), unified-trading-api, and
> greeks-service already shipped — reproduced below as done. **Machine-held** until Phases 1–6 all reach `done`
> (`depends_on` + `gate_on_depends: true`), matching the tracker's original DAG ("Phases 1-6 GREEN → Phase 7").

## Todos

- [x] ✅ [AGENT] P2. **alerting-service** — DONE `alerting-service@39181c7` (348 tests ✓, QG 0). Replaced
      `Literal["WARNING","CRITICAL"]` in `rules/connectivity_rules.py` + `rules/reconciliation_rules.py` with UAC
      `AlertSeverity` (`.WARN`/`.CRITICAL`); also fixed a dropped `"delivered": False` found in passing.
- [x] ✅ [AGENT] P2. **agent-orchestrator** — CORE + P2 read-migration (ALL 6 waves) SHIPPED 2026-06-22, 858 tests green
      on HEAD. Full detail in the tracker's Progress Log (`unified_cloud_config` foundation, ~93+ env reads migrated to
      typed `OrchestratorConfig`, 14 sanctioned residuals). No remaining action.
- [x] ✅ [AGENT] P3. **unified-trading-api** — DONE `unified-trading-api@e3fbd8d` (QG 0). `routes/chat.py`
      `ANTHROPIC_API_KEY` now via `UnifiedCloudConfig().get_secret("anthropic-api-key")` (name confirmed from
      `credentials-registry.yaml`); the `# config-bootstrap` os.environ reads left as sanctioned.
- [x] ✅ [AGENT] P3. **greeks-service** — DONE `greeks-service@b119b5b` (QG 0). Deleted `greeks_service/events.py`
      re-export stub; the single importer now imports `log_event` from UTL directly.
- [x] ✅ [AGENT] P3. **strategy-service**: noqa-with-reason (or `UnifiedCloudConfig`) the un-annotated `os.environ.get`
      in `recovery_event_helper.py:41,90` and `pnl/engine/mock_data_provider.py:38` (mirror the existing
      `position/engine/mock_data_provider.py` noqa pattern). — VERIFIED STALE, no code change needed. (1)
      `recovery_event_helper.py` has zero `os.getenv`/`os.environ` calls today — already cleared by an earlier commit
      `6aff0c48` ("clear os.getenv/imports-in-fn/... classes"), which predates this plan's `created: 2026-07-13`; the
      file is 98 lines with no match at lines 41/90 or anywhere else. (2) `pnl/engine/mock_data_provider.py:38`'s
      `os.environ.get("WORKSPACE_ROOT", "")` IS already covered — not by an inline noqa like
      `position/engine/mock_data_provider.py`, but by `scripts/quality-gates.sh`'s
      `OS_ENV_EXCLUDE_GLOBS=(--glob "!**/engine/mock_data_provider.py")`, which glob-matches ANY
      `engine/mock_data_provider.py` path (not just `position/`'s), excluding it from the QG os-environ scan entirely —
      a more robust fix than a per-line comment (survives file moves/renames). Confirmed by running the exact QG grep
      logic locally: 0 hits. Adding a redundant inline noqa would not change QG behaviour and risks drifting from the
      glob exclude's own "one exclusion, covers the whole family" intent.
- [x] ✅ [CODE] P2. **execution-service cross-service imports surfaced by the 2026-06-11 imports-in-fn sweep (codex
      ratchet plan)** — DONE. (1) `leg_snapshot_builder` (pure Decimal/UAC-typed math, no service/IO deps) moved to
      `unified_trading_library.risk.leg_snapshot_builder`, mirroring the `risk/net_delta.py` (F45) precedent — single
      SSOT for strategy-service + execution-service, no service↔service import: `unified-trading-library@ff387620` (new
      module + `__init__` export + moved test), `strategy-service@59297fa0` (deleted the old module, updated the
      `LegControllerAdapter` docstring), `execution-service@cd65e2cd` (top-level
      `unified_trading_library.build_leg_snapshots` import replaces the lazy cross-service import),
      `system-integration-tests@a44f224` (e2e test import updated). (2) `mtds_book_provider.py`'s
      `market_tick_data_service.reader.CanonicalParquetReader` import: the reader class is 641 L of MTDS-domain-specific
      logic (asset_group/hive-key/DeFi-chain-axis resolution) — promoting it or flipping to a UAC-contract+GCS read was
      judged too large/risky for this unit, so instead SANCTIONED as a tracked exception (mirroring the existing
      `target_universe.catalog` precedent): `unified-api-contracts@0bd81fc2` (added `market_tick_data_service` to
      execution-service's `forbidden_imports` + a `forbidden_exceptions` entry for the specific site) +
      `unified-trading-pm` deprecation-ledger.yaml entry (id: `execution_service_mtds_reader_dep`) tracking the real
      promotion as follow-up work. All 4 repos' `quality-gates.sh` confirmed full-green pre-ship; 3 pre-existing
      (unrelated) repo-reds hit along the way were each verified pre-existing + issue-doc'd + repo-blocker'd, then
      resolved upstream or by this agent (execution-service codex-violations ceiling breach, UAC's incomplete
      deployment-service registry migration, SIT's fleet-wide pip-audit CVEs) — see
      `plans/active/issues/execution_service_codex_compliance_red_2026_07_13.md`,
      `…/uac_cross_repo_invariant_incomplete_deployment_service_migration_2026_07_13.md`,
      `…/system_integration_tests_pip_audit_red_2026_07_13.md`. Repos: unified-trading-library, strategy-service,
      execution-service, unified-api-contracts, system-integration-tests.
- [ ] [AGENT] P3. **lint ratchet tail (opportunistic, not blocking)**: in MTDS/IS/execution/deployment one-off
      `scripts/` (~70 files), convert `from google.cloud import storage` → `get_storage_client()`, `gs://` →
      `resolve_bucket_name`, per-object `gsutil`/`gcloud` subprocess → UTL `gcs_copy/delete/describe_object`, and fix
      the banned env name `GOOGLE_CLOUD_PROJECT` → `GCP_PROJECT_ID` (`cleanup_kraken_spot_empty_confirmed.py:96`,
      `cleanup_may4_bait_sentinels.py:117`, MTDS `cleanup_*`). These are QG-baselined; counts only go down.
- [ ] [VERIFY] P2. `quality-gates.sh` green per touched repo; ratchet baselines decrease (never increase); quickmerge.

## Success criteria

UAC `AlertSeverity` used; orchestrator on `UnifiedCloudConfig`+events; stubs/lint cleared; ratchet baselines down.

## Notes for the worker

- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE).
