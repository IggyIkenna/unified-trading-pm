---
doc_type: plan
title: UTL/UAC reuse consolidation — Phase 2 API auth dedup (alerting-service + unified-trading-api)
summary:
  Migrate alerting-service (prod-live X-API-Key path) and unified-trading-api middleware auth onto UTL create_api_auth's
  new legacy X-API-Key branch; UTL extension + client-reporting-api already shipped.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, unified-trading-api]
scope: [engineer, admin]
tags: [utl, uac, consolidation, refactor, auth, split]
related: [plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
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

# UTL/UAC reuse consolidation — Phase 2 API auth dedup

> **Split provenance (2026-07-13):** Phase 2 of
> [`utl_uac_reuse_consolidation_remediation_2026_06_10.md`](utl_uac_reuse_consolidation_remediation_2026_06_10.md)
> (findings #2, #3, #7b). The UTL `create_api_auth` legacy X-API-Key extension and client-reporting-api's dead-code
> deletion already shipped (`unified-trading-library@20c8ae8d`, `client-reporting-api@9cd77cc`) — reproduced below as
> done. Independent of Phase 0/1 — no gate.

> **⚠️ ACCURACY CORRECTION (already applied 2026-06-10):** UTL `create_api_auth` authenticates via Bearer JWT +
> X-Service-Token (S2S) + DISABLE_AUTH by default — it did NOT read `X-API-Key` until the shipped extension below added
> a 4th legacy path validating against `UnifiedCloudConfig.api_key`. alerting-service `verify_api_key` and
> unified-trading-api `middleware/auth.py` authenticate via `X-API-Key`, so this migration is now unblocked.

## Todos

- [x] ✅ [AGENT] P0. **UTL extension FIRST** — DONE `unified-trading-library@20c8ae8d` (6081 tests ✓, 4 new auth tests,
      QG 0). Added the `X-API-Key` (legacy) branch to `create_api_auth` (validates against
      `UnifiedCloudConfig().api_key`, returns `AuthContext(is_api_key=True, is_internal=True, role="admin")`, 401 on
      mismatch; ordered after S2S, before Bearer JWT; existing paths byte-preserved). **Unblocks alerting-service +
      unified-trading-api auth migration.**
- [x] ✅ [AGENT] P0. **alerting-service** — DONE `alerting-service@f59dc67` (QG green, sentinel-verified). Deleted
      `alerting_service/auth.py` (`verify_api_key` + DISABLE_AUTH guard); `api/main.py` now depends on UTL
      `create_api_auth("alerting-service")` (`_api_auth`); `_env` reads `UnifiedCloudConfig().environment` directly.
      Updated 5 test files' dependency overrides from `verify_api_key` to `_api_auth` (returning a fabricated
      `AuthContext(is_api_key=True, is_internal=True, role="admin")`); deleted the now-dead `TestVerifyApiKey` class
      from `test_health_and_auth.py` (X-API-Key path coverage lives in UTL's own 4 new auth tests). `X-API-Key`
      production callers still authenticate via the same `UnifiedCloudConfig().api_key` check, now inside UTL.
- [x] ✅ [AGENT] P0. **client-reporting-api** — DONE `client-reporting-api@9cd77cc` (579 tests ✓, coverage 71.2%, QG 0).
      Deleted dead `auth.py` + `_google_auth_sync.py` (+ their tests); repointed the 2 live importers (`main.py`,
      `api/main.py`) to `config.get_config()`; cleared the `DISABLE_AUTH` toggle from 16 test fixtures (live path
      already on UTL `create_api_auth`). Direct `google.oauth2`/`google.auth` SDK import removed with the files.
- [ ] [AGENT] P1. **unified-trading-api** (UTL extension is shipped — unblocked): migrate `middleware/auth.py` X-API-Key
      validation core to UTL `create_api_auth(...)`'s new legacy path; preserve the gateway-specific mock/app_state
      wiring (the only local-specific bit).
- [ ] [VERIFY] P0. Auth smoke per repo (200 with valid **X-API-Key**, 200 with Bearer JWT / X-Service-Token, 401
      without, DISABLE_AUTH refused in prod mode); `quality-gates.sh` green; quickmerge each.

## Success criteria

3 repos depend on `create_api_auth`; hand-rolled `auth.py` deleted; no direct `google.oauth2`.

## Notes for the worker

- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE).
- alerting-service's `X-API-Key` path is **wired in production** — verify before/after, don't ship blind.
