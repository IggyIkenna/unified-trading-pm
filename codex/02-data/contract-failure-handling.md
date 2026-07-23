---
doc_type: codex-ssot
title: Contract Failure Handling
summary:
  Adapter failure routing — pre-normalisation _safe_parse Pydantic failures go to the DLQ (DeadLetterRecord → GCS +
  Pub/Sub DEAD_LETTER_VALIDATION, 0 retries) while mid-normalisation transient/data-quality errors use record_failed() /
  record_empty() per the 4-state capture_status contract.
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
last_reviewed: 2026-05-17
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
  → _safe_parse() (unified-api-contracts Pydantic validation)
  → ValidationError → EnhancedError(category=VALIDATION_ERROR, recovery_strategy=DEAD_LETTER)
  → DeadLetterRecord written to GCS + published to Pub/Sub topic DEAD_LETTER_VALIDATION
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

| Field              | Type          | Purpose                            |
| ------------------ | ------------- | ---------------------------------- |
| `service`          | str           | Originating service                |
| `venue`            | str           | Venue identifier                   |
| `timestamp`        | datetime      | UTC timestamp                      |
| `raw_payload`      | str           | JSON string of failed raw response |
| `schema_attempted` | str           | e.g. "BinanceLiquidationMessage"   |
| `error`            | EnhancedError | Full error with correlation_id     |
| `correlation_id`   | str           | Cross-service trace                |
| `retry_count`      | int           | 0 for validation failures          |
| `dlq_topic`        | str           | "DEAD_LETTER_VALIDATION"           |

---

## Storage and Publishing

- **GCS bucket**: DeadLetterRecord written to configured DLQ bucket (partitioned by date/venue)
- **Pub/Sub**: Published to topic `DEAD_LETTER_VALIDATION`

---

## Monitoring

- **DLQ depth per venue**: Monitored in live-health-monitor-ui ContractHealth dashboard
- **Alert threshold**: Depth > 100 per venue per hour

---

## Retry Policy

- **0 auto-retries** for validation failures — data is invalid, not transient
- Retrying invalid data does not fix it; alert and investigate
