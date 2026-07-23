---
doc_type: codex-ssot
title: Audit Logging
summary: >-
  SSOT for security + trade/strategy audit logging: mandatory `AUTH_FAILURE`/`SECRET_ACCESSED`/`CONFIG_CHANGED` events,
  execution audit (7-year cold retention) + strategy audit (3-year) GCS paths + required fields, and append-only
  bucket-level immutability rules.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, execution-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [audit, execution, compliance, observability, data-status]
related:
  [
    /codex/07-security/compliance.md,
    /codex/07-security/secrets-management.md,
    /codex/03-observability/lifecycle-events.md,
  ]
created: 2026-03-27
authoritative_for:
  [security audit events (AUTH_FAILURE/SECRET_ACCESSED/CONFIG_CHANGED), trade and strategy audit retention]
referenced_by:
  [
    /codex/03-observability/lifecycle-events.md,
    /codex/06-coding-standards/correlation-id.md,
    /codex/07-security/compliance.md,
    /codex/07-security/transport-security.md,
  ]
owner:
last_reviewed:
code_refs:
execution:
  {
    owner: execution-service maintainer (audit-log path) + governance (retention-lock provisioning),
    cadence: continuous (live emission per trade/order action; one-shot retention-lock setup pre-cutover),
    verifier:
      "GCS object-listing under `audit/{client_id_or_order_id}/{YYYY/MM/DD}/` matches `EXECUTION_AUDIT.required_fields`
      schema; retention-lock policy attached via `gsutil retention set`.",
    last_executed: NEVER (retention-lock provisioning P0 PRE_CUTOVER gap per slot 8 audit PB-2 / PB-8),
  }
---

# Audit Logging

## TL;DR

Three mandatory security audit events must be emitted via `log_event()` wherever the triggering action occurs:
`AUTH_FAILURE`, `SECRET_ACCESSED`, and `CONFIG_CHANGED`. Trade execution and strategy audit records are persisted to GCS
and subject to a minimum 7-year retention period for regulatory compliance (FCA/MiFID II).

**Machine-readable SSOT:**

- Event schemas: `unified-api-contracts/unified_api_contracts/internal/events.py` — `AuthFailureDetails`,
  `SecretAccessedDetails`, `ConfigChangedDetails`
- Audit retention and required fields: `unified-api-contracts/unified_api_contracts/internal/schemas/audit.py` —
  `EXECUTION_AUDIT`, `STRATEGY_AUDIT`

---

## Mandatory Security Audit Events

### AUTH_FAILURE

Emit whenever an authentication attempt fails (API key rejected, OAuth token invalid, JWT expired, mTLS handshake
failure, etc.).

> **Do not confuse with `LOGIN_FAILURE`:** `AUTH_FAILURE` is a **server-side** security audit event emitted by API
> services when an API key, JWT, or mTLS credential is rejected. `LOGIN_FAILURE` is a **UI-side** observability event
> emitted by `unified-trading-ui-auth` when an OAuth PKCE flow fails in the browser (OAuth error callback or token
> validation failure). Both coexist in `STANDARD_LIFECYCLE_EVENTS`. See
> `03-observability/lifecycle-events.md §UI Auth Events`.

**Required fields:**

| Field            | Type  | Description                                               |
| ---------------- | ----- | --------------------------------------------------------- |
| `auth_type`      | `str` | One of: `api_key`, `oauth`, `jwt`, `mtls`                 |
| `username`       | `str` | Identity that attempted authentication (or `"anonymous"`) |
| `failure_reason` | `str` | Human-readable reason for failure                         |
| `ip_address`     | `str` | Source IP address of the request (if available)           |
| `endpoint`       | `str` | The endpoint or resource that was accessed                |
| `attempt_count`  | `int` | Cumulative failed attempts from this identity (if known)  |

```python
log_event("AUTH_FAILURE", metadata={
    "correlation_id": request_id,
    "auth_type": "api_key",
    "username": username,
    "failure_reason": "key_not_found",
    "ip_address": client_ip,
    "endpoint": "/orders",
    "attempt_count": 3,
})
```

### SECRET_ACCESSED

Emit whenever a secret is retrieved from Secret Manager via `get_secret_client()`. This event is typically emitted by
the secret client wrapper, not by application code directly.

**Required fields:**

| Field             | Type   | Description                                                   |
| ----------------- | ------ | ------------------------------------------------------------- |
| `secret_name`     | `str`  | Name of the secret in Secret Manager                          |
| `caller_identity` | `str`  | Service account or identity that accessed the secret          |
| `success`         | `bool` | Whether the access succeeded                                  |
| `operation`       | `str`  | One of: `access`, `create`, `delete`, `rotate`                |
| `version`         | `str`  | Secret version accessed (e.g. `"latest"` or a version number) |

```python
log_event("SECRET_ACCESSED", metadata={
    "correlation_id": run_id,
    "secret_name": "tardis-api-key",
    "caller_identity": "instruments-service@project.iam.gserviceaccount.com",
    "success": True,
    "operation": "access",
    "version": "latest",
})
```

### CONFIG_CHANGED

Emit whenever a configuration file is created, updated, or deleted — typically in deployment or runtime reconfiguration
flows.

**Required fields:**

| Field            | Type   | Description                                                   |
| ---------------- | ------ | ------------------------------------------------------------- |
| `config_file`    | `str`  | Workspace-relative path to the config file that changed       |
| `changed_by`     | `str`  | Identity (service account or username) that made the change   |
| `authorized`     | `bool` | Whether the change was authorized per IAM / approval workflow |
| `change_type`    | `str`  | One of: `update`, `create`, `delete`                          |
| `git_commit_sha` | `str`  | Git commit SHA if the change was applied via a code push      |
| `fields_changed` | `list` | List of field names that changed (redact values, not names)   |

```python
log_event("CONFIG_CHANGED", metadata={
    "correlation_id": deploy_id,
    "config_file": "deployment-service/configs/runtime-topology.yaml",
    "changed_by": "deploy-sa@project.iam.gserviceaccount.com",
    "authorized": True,
    "change_type": "update",
    "git_commit_sha": "a1b2c3d4",
    "fields_changed": ["max_workers", "venues"],
})
```

---

## Trade Execution Audit

Execution events (`ORDER_CREATED`, `ORDER_UPDATED`, `ORDER_CANCELLED`, `ORDER_FILLED`, `ORDER_REJECTED`) must be
persisted as immutable audit records.

**Canonical schema:** `EXECUTION_AUDIT` in `unified-api-contracts/unified_api_contracts/internal/schemas/audit.py`

**Required fields on every execution audit record:**

| Field                | Description                       |
| -------------------- | --------------------------------- |
| `client_order_id`    | Client-assigned order identifier  |
| `exchange_timestamp` | Timestamp from the exchange (UTC) |
| `venue_response_id`  | Exchange-assigned order/fill ID   |
| `fill_price`         | Execution price (for fills)       |
| `fill_quantity`      | Quantity filled                   |

**GCS storage path:** `audit/{client_order_id}/{YYYY/MM/DD}/{iso-timestamp}-{event_type}.json` (per-event file; lineage
axis is per-order — see Data Retention Summary for PB-3 threading note)

**Retention:** minimum **7 years** (cold storage), per `AuditRetention(cold_years=7)` in `EXECUTION_AUDIT`.

---

## Strategy Audit

> **STATUS 2026-05-12 (per slot 8 audit PB-4)**: schema declared in UAC; runtime emission today is `log_event(...)` into
> the events JSONL bucket (`gs://{pid}-events/events/...`) ONLY — there is **no `persist_audit_log`-equivalent for
> strategy events**, and `signal_publisher.py:188` hardcodes `"client": "system"` so the per-client lineage axis below
> is design-intent, not present-tense. Strategy-audit GCS writer wiring is a PRE*CUTOVER follow-up per the slot 8 audit
> doc; until shipped, treat the `audit/{client_id}/...` path as the \_target* shape, not the _current_ path.

Strategy decision events (`STRATEGY_INSTRUCTION`, `SIGNAL_GENERATED`) **must** be persisted (design intent — writer
PRE_CUTOVER pending per PB-4); they are emitted on the events stream today via `log_event(...)` and consumed by
analytics from there.

**Canonical schema:** `STRATEGY_AUDIT` in `unified-api-contracts/unified_api_contracts/internal/schemas/audit.py`

**Required fields:**

| Field               | Description                                          |
| ------------------- | ---------------------------------------------------- |
| `strategy_id`       | Identifier for the strategy that generated the event |
| `client`            | Client for whom the strategy is running              |
| `signal_source`     | Model or rule that produced the signal               |
| `position_snapshot` | Serialised position state at decision time           |

**GCS storage path:** `audit/{client_id}/{YYYY/MM/DD}/{iso-timestamp}-strategy.json` (per-event file, 4-level date
split). Strategy-audit lineage IS per-client (strategy_id resolves to a single client).

**Retention:** minimum **3 years** (cold storage).

---

## Data Retention Summary

| Audit Domain | Hot (days) | Warm (days) | Cold (years) | Path template                                                            | Lineage axis                                                                                                                                                                                                         |
| ------------ | ---------- | ----------- | ------------ | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Execution    | 90         | 365         | 7            | `audit/{client_order_id}/{YYYY/MM/DD}/{iso-timestamp}-{event_type}.json` | **per-order** (3 of 5 event types thread `client_order_id` / `order_id` / `operation_id` into the path slot; code-fix to thread real `client_id` = PRE_CUTOVER follow-up in execution-service per slot 8 audit PB-3) |
| Strategy     | 90         | 365         | 3            | `audit/{client_id}/{YYYY/MM/DD}/{iso-timestamp}-strategy.json`           | per-client                                                                                                                                                                                                           |
| Risk         | 90         | 365         | 3            | `audit/{client_id}/{YYYY/MM/DD}/{iso-timestamp}-risk.json`               | per-client                                                                                                                                                                                                           |

Retention tiers are defined as `AuditRetention` models in
`unified-api-contracts/unified_api_contracts/internal/schemas/audit.py`. Note: `gcs_path_template` on `AuditRetention`
is **declared-but-unused** at runtime (per slot 8 audit PB-1) — execution-service `audit_log.py:60` hardcodes the
4-level date split shape; align template with code OR wire template into runtime as PRE_CUTOVER follow-up.

---

## Immutability Rules

- Audit records are **append-only at the bucket level** — every event lands as a NEW per-event-filename object (PUT, NOT
  append-to-existing-file). The per-event filename (ISO timestamp + event_type suffix) prevents overwrite by
  construction.
- GCS Object Versioning + Retention Lock on the audit bucket enforce immutability at the storage layer (**PRE_CUTOVER
  follow-up routed to slot 4** per `api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 3.C — audit bucket
  Retention-Lock configuration).
- `log_event()` writes are non-destructive: write-once per per-event filename; no in-place modification of existing
  objects.

---

## Anti-Patterns

```python
# NEVER: emit AUTH_FAILURE without all required fields
log_event("AUTH_FAILURE")  # missing auth_type, username, failure_reason

# NEVER: skip logging on auth failure to avoid noise
except AuthError:
    pass  # silent swallow — violates audit requirement

# NEVER: modify or delete an existing audit record
storage_client.delete("audit/client-alpha/2026-03-01/ORDER_FILLED/records.jsonl")
```

---

## Related

- Machine-readable event schemas: `unified-api-contracts/unified_api_contracts/internal/events.py`
- Machine-readable audit schemas: `unified-api-contracts/unified_api_contracts/internal/schemas/audit.py`
- Lifecycle events (non-security): `03-observability/lifecycle-events.md`
- Secrets access pattern: `07-security/secrets-management.md`
- Cursor rule: `.cursor/rules/core/event-logging.mdc`
- Observability compliance: `.cursor/rules/misc/observability-compliance.mdc`
