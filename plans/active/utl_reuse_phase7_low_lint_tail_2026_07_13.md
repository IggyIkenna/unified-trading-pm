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
- [ ] [AGENT] P3. **strategy-service**: noqa-with-reason (or `UnifiedCloudConfig`) the un-annotated `os.environ.get` in
      `recovery_event_helper.py:41,90` and `pnl/engine/mock_data_provider.py:38` (mirror the existing
      `position/engine/mock_data_provider.py` noqa pattern).
- [ ] [CODE] P2. **execution-service cross-service imports surfaced by the 2026-06-11 imports-in-fn sweep (codex ratchet
      plan)** — two UNSANCTIONED sites were hiding behind lazy in-function imports (now carrying tracked
      `# noqa: imports-inside-functions` markers): (1) `execution_service/algo_library/leg_controller_runner.py:222`
      imports `strategy_service.position.core.leg_snapshot_builder` — `strategy_service.position` is in the UAC
      `service_contract_map` **forbidden_imports** for execution-service and NOT in forbidden_exceptions (unlike the
      sanctioned target_universe.catalog site); move `leg_snapshot_builder` to UTL/UAC or add a justified
      forbidden_exception + deprecation-ledger entry. (2) `execution_service/algo_library/mtds_book_provider.py:93`
      imports `market_tick_data_service.reader.CanonicalParquetReader` AND execution-service pyproject declares
      `../market-tick-data-service` as a path dep (pyproject ~L124) — same no-service↔service violation class the
      MDPS/deployment-api removals fixed 2026-06-11; needs the reader surface promoted to a shared lib (UTL) or the
      manifest-read path flipped to the UAC contract + GCS. Repos: execution-service + strategy-service +
      market-tick-data-service + unified-api-contracts.
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
