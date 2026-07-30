---
doc_type: codex-ssot
title: Contract Failure Handling
summary:
  Adapter failure routing — pre-normalisation _safe_parse Pydantic failures go to the DLQ (DeadLetterRecord → GCS +
  EventType.DEAD_LETTERED on the event spine, 0 retries) while mid-normalisation transient/data-quality errors use
  record_failed() / record_empty() per the 4-state capture_status contract.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: [uac, data-pipeline, validation, manifest, capture-status]
related: [/codex/02-data/honest-absence-downstream-handling.md, /codex/02-data/availability-manifest-and-data-status.md]
created: 2026-03-27
authoritative_for: [adapter contract-failure DLQ routing (pre-normalisation validation failures)]
referenced_by:
owner:
last_reviewed: 2026-08-14
code_refs:
last_updated: 2026-05-12
---

# Contract Failure Handling

> **Routing rule between DLQ + manifest `record_failed()` paths** (codex audit D-19 2026-05-12):
>
> | Failure stage                                                                                           | Adapter action                                                                                                            |
> | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
> | **Pre-normalisation** — raw API response fails `_safe_parse()` Pydantic validation                      | DLQ (this doc). Schema mismatch — data shape is wrong before any row exists.                                              |
> | **Mid-normalisation** — known transient error (rate-limit, 5xx, timeout)                                | `record_failed(error=, attempted_at=)` per the 4-state `capture_status` contract. Retryable.                              |
> | **Mid-normalisation** — `MalformedTickFieldError` / `UpstreamTimestampBiasError` (per-row data quality) | `record_failed(error=...)` per writegate Phase 2.A Category B/C; the row exists but is unusable.                          |
> | **Source returned legitimately empty window**                                                           | `record_empty(reason=<typed>)` per the closed `EmptyConfirmedReason` set — NOT DLQ.                                       |
> | **Reader/schema-drift bug — manifest says captured but parquet row missing**                            | STOP + `DependencyError(fail_fast=True)`. Never silent placeholder. (SSOT in `availability-manifest-and-data-status.md`.) |
>
> DLQ owns the **shape-mismatched-before-row-existed** class; `record_failed()` + `record_empty()` own everything from
> mid-normalisation onward — the row key exists, the question is what happened TO that row. Cross-references:
> [`honest-absence-downstream-handling.md`](./honest-absence-downstream-handling.md) (consumer-side rules),
> [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md) § "Four-category empty-output
> decision" (writegate Phase 2.A taxonomy).

## Dead-Letter Queue Strategy

All adapters must validate raw API responses before normalisation. Validation failures are routed to a dead-letter queue
— never silently pass-through. (DLQ is the **pre-row** failure path per the routing rule above.)

---

## Flow

```
RAW API RESPONSE
  → _safe_parse() (market_tick_data_service.market_interface.base_adapter, UAC Pydantic validation)
  → ValidationError → EnhancedError(category=VALIDATION_ERROR, recovery_strategy=DEAD_LETTER)
  → DeadLetterRecord written to GCS + EventType.DEAD_LETTERED published on the event spine
```

---

## \_safe_parse() Contract

All adapters call `_safe_parse()` before normalisation. Validation failures are never caught and retried — they are
routed to DLQ.

---

## EnhancedError for Validation Failures

```python
EnhancedError(
    category=VALIDATION_ERROR,
    recovery_strategy=DEAD_LETTER,
    correlation_id=...,
    ...
)
```

---

## DeadLetterRecord Fields

SSOT: `unified_api_contracts/internal/schemas/errors.py` § `DeadLetterRecord` — read the model, not this table, when
writing code. Reproduced here for orientation:

| Field                                  | Type                    | Purpose                                              |
| -------------------------------------- | ----------------------- | ---------------------------------------------------- |
| `record_id`                            | str                     | DLQ record identity                                  |
| `original_event`                       | str                     | Event name that failed                               |
| `original_payload`                     | str \| None             | JSON string of the failed raw response               |
| `error_category`                       | `ErrorCategory`         | `VALIDATION_ERROR` for pre-normalisation shape fails |
| `error_message`                        | str                     | Human-readable failure detail                        |
| `retry_count` / `max_retries`          | int                     | Retry accounting (0 attempts for validation fails)   |
| `first_failure_at` / `last_failure_at` | datetime                | UTC failure window                                   |
| `source_service`                       | str                     | Originating service                                  |
| `dead_lettered_at`                     | datetime                | UTC dead-letter timestamp                            |
| `correlation_id` / `trace_id`          | str \| None             | Cross-service trace                                  |
| `venue`                                | str \| None             | Venue identifier                                     |
| `recovery_strategy`                    | `ErrorRecoveryStrategy` | Defaults to `DEAD_LETTER`                            |
| `metadata`                             | dict[str, str]          | Free-form context                                    |
| `schema_version`                       | str                     | Contract version                                     |

---

## Storage and Publishing

- **GCS bucket**: DeadLetterRecord written to the configured DLQ bucket (partitioned by date/venue), resolved via
  `resolve_bucket_name(...)` — never an inline `gs://`.
- **Event spine**: `EventType.DEAD_LETTERED` (`unified_api_contracts/internal/events.py`) published via the UTL
  `EventTransport` facade. There is no dedicated `DEAD_LETTER_VALIDATION` topic constant.

---

## Monitoring

- **DLQ depth per venue**: surfaced in the consolidated portal `unified-trading-system-ui` (the split
  `live-health-monitor-ui` was folded into it on 2026-05-08 — see `/codex/DEPRECATED_UIS_NOTICE.md`).
- **Alert threshold**: Depth > 100 per venue per hour

---

## Retry Policy

- **0 auto-retries** for validation failures — data is invalid, not transient
- Retrying invalid data does not fix it; alert and investigate
