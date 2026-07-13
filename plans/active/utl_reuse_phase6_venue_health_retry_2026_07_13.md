---
doc_type: plan
title: UTL/UAC reuse consolidation — Phase 6 venue-error, health router, retry helper
summary:
  Fold execution-service's second hand-rolled /health onto UTL make_health_router, and consolidate the MTDS + IS
  base-adapter retries onto the new UTL retry helper; venue-error classification already shipped.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [utl, uac, consolidation, refactor, venue-error, health, retry, split]
related: [plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
locked_by: live-defi-rollout
locked_since: "2026-07-13"
supersedes:
superseded_by:
depends_on:
source: [split from utl_uac_reuse_consolidation_remediation_2026_06_10 tracker, operator-approved 2026-07-13]
assigned_role: backend-engineer
drift_direction: advance-code
---

# UTL/UAC reuse consolidation — Phase 6 venue-error, health router, retry helper

> **Split provenance (2026-07-13):** Phase 6 of
> [`utl_uac_reuse_consolidation_remediation_2026_06_10.md`](utl_uac_reuse_consolidation_remediation_2026_06_10.md)
> (findings #8, #10, #11). instruments-service's venue-error classification and the UTL retry-helper addition already
> shipped — reproduced below as done. Independent of every other split plan — no gate.

## Todos

- [x] ✅ [AGENT] P1. **instruments-service** — DONE `instruments-service@66165f2e` (23 tests ✓, QG 0; direct-push
      carve-out — UTL was transiently dirty). Deleted local `VenueError`; all 8 construction sites now build UAC
      `VenueErrorClassification` (`retry_safe`/`reconnect`/`action: ErrorAction`); `VenueFetchResult` wrapper kept.
- [ ] [AGENT] P2. **execution-service**: fold the second hand-rolled `/health`+`/ready`+`/readiness` in `api/app.py:209`
      onto UTL `make_health_router(...)` with a `data_freshness` callback (QG STEP 5.62), so the service has ONE health
      surface (the canonical `api/main.py` already uses it).
- [x] ✅ (UTL helper half) **Add a UTL retry helper** — DONE `unified-trading-library@20c8ae8d`: `retry` (decorator) +
      `with_retry` (callable), stdlib-only, exp backoff + jitter, 429/5xx-aware, exported from
      `unified_trading_library.utils.retry` / `.utils` / top-level. 9 new tests.
- [ ] [AGENT] P2. **Consume the UTL retry helper** (REMAINING): consolidate the two hand-rolled base-adapter retries —
      MTDS `market_interface/base_adapter.py:29-100` + instruments-service `reference_data/base_adapter.py:39-160` —
      onto `unified_trading_library.utils.retry`/`with_retry`. Preserve each adapter's classify-on-give-up behaviour.
- [ ] [VERIFY] P1. Adapter retry behaviour unchanged (mock 429 → N retries → classify); health endpoints respond;
      `quality-gates.sh` green; quickmerge.

## Success criteria

`classify_venue_error` single-sources IS venue errors; execution has ONE health surface; one UTL retry helper, two
adapters consolidated.

## Notes for the worker

- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE).
