---
doc_type: plan
title: UI & API Event Telemetry — Auth Events + Request Audit Trail
summary:
status: DONE
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api, deployment-api, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: 2026-03-10
id: ui_api_event_telemetry_2026_03_10
priority: P1
completed: 2026-03-10
owner: agent
---

## Context

Two telemetry gaps identified in 2026-03-10 re-audit:

- All 7 UI repos emit zero observability events — login, logout, and session expiry are completely dark in the GCS event
  sink.
- APIs log AUTH_FAILURE at the auth layer but have no per-request ingress/egress audit trail (method, path, status_code,
  latency_ms) for security audit and SLA reporting.

This plan closes both gaps using existing UEI + UTL infrastructure — no new services.

## Architecture

```
Browser
  └─ unified-trading-ui-auth AuthContext.tsx
        ├─ emitAuthEvent("LOGIN_INITIATED")  ──POST /events──► API relay endpoint
        ├─ emitAuthEvent("LOGIN_SUCCESS")                       │
        ├─ emitAuthEvent("LOGIN_FAILURE")                       │ make_events_relay_router()
        ├─ emitAuthEvent("LOGOUT")                              │ (UTL)
        └─ emitAuthEvent("SESSION_EXPIRED")                     │
                                                                ▼
FastAPI App (any API repo)                                  log_event() → GCS/UEI sink
  └─ RequestAuditMiddleware (UTL)
        ├─ API_REQUEST_RECEIVED  (on ingress; skips /health /readiness /metrics)
        └─ API_RESPONSE_SENT     (on egress; includes status_code + latency_ms)
```

## Scope

| Repo                       | Change                                                               | Commit  |
| -------------------------- | -------------------------------------------------------------------- | ------- |
| `unified-events-interface` | +7 event names; v0.2.23 → v0.2.26                                    | 85bbe29 |
| `unified-trading-library`  | +`RequestAuditMiddleware` + `make_events_relay_router()`             | 66513b4 |
| `unified-trading-ui-auth`  | +`authEvents.ts`; AuthContext wiring (5 call-sites); v0.2.0 → v0.2.1 | 8bae8f7 |
| `market-data-api`          | +`RequestAuditMiddleware`                                            | d86528e |
| `execution-results-api`    | +`RequestAuditMiddleware`                                            | 954a36a |
| `client-reporting-api`     | +`RequestAuditMiddleware`                                            | d78d1c5 |
| `deployment-api`           | +`RequestAuditMiddleware` + relay router                             | 19f3fdb |
| `ml-inference-api`         | +`RequestAuditMiddleware`                                            | b1eff31 |
| `ml-training-api`          | +`RequestAuditMiddleware` + relay router                             | b707be1 |
| `trading-analytics-api`    | +`RequestAuditMiddleware` + relay router                             | 9435279 |

## New Event Names (STANDARD_LIFECYCLE_EVENTS additions)

| Event                  | Layer | Severity     | Notes                                                                                |
| ---------------------- | ----- | ------------ | ------------------------------------------------------------------------------------ |
| `LOGIN_INITIATED`      | UI    | INFO         | OAuth redirect started                                                               |
| `LOGIN_SUCCESS`        | UI    | INFO         | Token stored, user authenticated                                                     |
| `LOGIN_FAILURE`        | UI    | WARNING      | OAuth error / token validation failed; distinct from AUTH_FAILURE (API key failures) |
| `LOGOUT`               | UI    | INFO         | User-initiated logout                                                                |
| `SESSION_EXPIRED`      | UI    | WARNING      | Token TTL exceeded; detected via sessionStorage sentinel                             |
| `API_REQUEST_RECEIVED` | API   | INFO         | Request ingress audit (method, path, correlation_id)                                 |
| `API_RESPONSE_SENT`    | API   | INFO/WARNING | Response egress audit (status_code, latency_ms); WARNING if status >= 400            |

## Tasks

### T1 — UEI ✅

- [x] Add 7 event names to `STANDARD_LIFECYCLE_EVENTS` in `schemas.py`
- [x] Bump version 0.2.23 → 0.2.26 (auto-bump hook ran twice due to ruff reformat)
- [x] Commit: `feat: add UI auth + API audit event types (v0.2.26)` (85bbe29)

### T2 — UTL ✅

- [x] Create `unified_trading_library/core/audit_middleware.py` with `RequestAuditMiddleware`
- [x] Create `unified_trading_library/core/events_relay.py` with `make_events_relay_router()`
- [x] Export both from `unified_trading_library/core/__init__.py`
- [x] basedpyright: 0 errors on new files
- [x] Commit: `feat: add RequestAuditMiddleware and make_events_relay_router()` (66513b4)

### T3 — unified-trading-ui-auth ✅

- [x] Create `src/authEvents.ts` with `emitAuthEvent()` + `SESSION_SENTINEL_KEY` + `AuthEventName`
- [x] Extend `AuthProviderConfig` in `types.ts` with `eventEndpoint?` + `serviceName?`
- [x] Wire `emitAuthEvent()` into `AuthContext.tsx` at 5 call-sites (login, success, failure, logout, expired)
- [x] SESSION_EXPIRED detection via sessionStorage sentinel (set on success, cleared on logout)
- [x] Export from `index.ts`
- [x] Bump to v0.2.1 + `npm run build` passes
- [x] Commit: `feat: auth event emission via emitAuthEvent() (v0.2.1)` (8bae8f7)

### T4 — API repos (7 repos) ✅

- [x] market-data-api: `RequestAuditMiddleware` (d86528e)
- [x] execution-results-api: `RequestAuditMiddleware` (954a36a)
- [x] client-reporting-api: `RequestAuditMiddleware` (d78d1c5)
- [x] deployment-api: `RequestAuditMiddleware` + relay router (19f3fdb)
- [x] ml-inference-api: `RequestAuditMiddleware` (b1eff31)
- [x] ml-training-api: `RequestAuditMiddleware` + relay router (b707be1)
- [x] trading-analytics-api: `RequestAuditMiddleware` + relay router (9435279)

### T5 — Codex + Registration ✅

- [x] Write cursor plan to `plans/active/ui_api_event_telemetry_2026_03_10.md`
- [x] Add entry #35 to `plans/active/INDEX.md`
- [x] Update `unified-trading-/codex/03-observability/lifecycle-events.md`

## Verification

```bash
# UEI — new event names present
python -c "from unified_events_interface.schemas import STANDARD_LIFECYCLE_EVENTS; \
  assert all(e in STANDARD_LIFECYCLE_EVENTS for e in ['LOGIN_SUCCESS','API_REQUEST_RECEIVED']); \
  print('UEI OK')"

# UTL — middleware importable
python -c "from unified_trading_library.core import RequestAuditMiddleware, make_events_relay_router; print('UTL OK')"

# UI auth — build passes
cd unified-trading-ui-auth && npm run build

# Integration — POST /events relay returns 204
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/events \
  -H "Content-Type: application/json" \
  -d '{"event_name":"LOGIN_SUCCESS","severity":"INFO","details":{"provider":"google"}}'
# Expect: 204
```

## Notes

- `LOGIN_FAILURE` (UI OAuth error) is semantically distinct from `AUTH_FAILURE` (API key validation failure). Both
  remain in `STANDARD_LIFECYCLE_EVENTS`.
- `emitAuthEvent()` is fire-and-forget — network errors are silently swallowed. Telemetry MUST NOT break auth flows.
- SESSION_EXPIRED uses a sessionStorage sentinel (`_uts_auth_session`) set on LOGIN_SUCCESS and cleared on LOGOUT. If
  the sentinel exists on mount but no token is found, SESSION_EXPIRED is emitted.
- `RequestAuditMiddleware` skip-list: /health, /readiness, /metrics, /docs, /openapi.json, /favicon.ico, /redoc — these
  generate high-frequency infra traffic.
