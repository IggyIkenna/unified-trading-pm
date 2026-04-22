---
title: "instruments-service write-gate — fail loud on batch-date vs row-timestamp misalignment (catch §5 data-crimes at source)"
priority: P1
status: active
owner: agent
created: 2026-04-22
locked_by: live-defi-rollout
locked_since: 2026-04-22
type: code
epic: none
completion_gates:
  code: C5
  deployment: none
  business: none
repo_gates:
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
depends_on: []
isProject: false
---

## Context

On 2026-04-22 we killed VM `tm-backfill-20260421-231758` after 18 hours of wasted compute because:

1. The orchestrator's Transfermarkt short-circuit passed `season=None`, defaulting to `datetime.now(UTC).year`
   (= 2026) for every historical batch date.
2. The Transfermarkt adapter stamped `valuation_date = datetime.now(UTC).strftime(...)` when the API omitted
   the field — today's wall-clock on every historical-backfill row.

Both are direct §5 data-crimes per codex `02-data/sports-scheduling-and-sharding.md` ("never write today's
value onto a 2018 fixture"). Both landed on HEAD and ran for 18h on a VM before being caught **by visual
inspection of logs**, not by any automated guardrail. Fixes in FSS commit `cdded95`.

**The architectural gap**: UTL has three layers of point-in-time validation
(`validate_timestamp_date_alignment`, `PointInTimeEnforcer`, `validate_pit_safety`), but **instruments-service
bypasses all of them**. Grep confirmed zero use in `instruments-service/instruments_service/engine/orchestrator.py`.
Only `features-sports-service` write-gate uses them. So the raw-data layer has no fail-loud at write time
for batch-date vs row-timestamp misalignment — the very invariant §5 cares about.

This plan closes that gap: every raw-data sink write in instruments-service goes through a UTL write-gate
that asserts `row.timestamp_like_column` aligns with the batch `date` partition before the parquet lands on
GCS. When misaligned, emit `DATA_ALIGNMENT_VIOLATION`, fail the write, and (configurable) either abort the
shard or record_failed in the manifest.

## Blast radius

| Repo                      | Scope                                                                                                 |
| ------------------------- | ----------------------------------------------------------------------------------------------------- |
| unified-trading-library   | Extend existing `validate_timestamp_date_alignment` to cover the `as_of_date` / `valuation_date` /
                              `data_available_at` column families used by raw-data adapters (not just feature writes). |
| instruments-service       | Every `sink.write(...)` in `orchestrator.py` gates through the new write-gate call. ~30 call sites.  |
| unified-trading-pm        | Codex `06-coding-standards/validation-patterns.md` adds the write-gate rule.                          |

## PRE-AUDIT-FINDINGS (2026-04-22 — agent)

### Existing UTL validators + their current callers

- [`unified_trading_library/point_in_time.py`](../../unified-trading-library/unified_trading_library/point_in_time.py):
  `PointInTimeEnforcer`, `enforce_point_in_time`, `validate_pit_safety`. Filter-based; suits feature writes.
- [`unified_trading_library/feature_service_base/write_gate.py`](../../unified-trading-library/unified_trading_library/feature_service_base/write_gate.py)
  L322: calls `validate_timestamp_date_alignment` — but only via `FeatureWriteGate` in feature services.
- **Zero callers in instruments-service** (grep confirmed 2026-04-22).

### Raw-data adapters already emit batch-date-aligned timestamps (sometimes)

Most sports adapters write parquets with a `data_available_at` column — but it's typically stamped with
`datetime.now(UTC)` at write time, not derived from the batch date. Going forward, the rule should be:

> For every raw-data parquet written at `by_date/day={D}/entity={E}/...`, every row-level date / timestamp
> column (valuation_date, as_of_date, data_available_at, kickoff_utc, event_time, etc.) MUST satisfy
> `row.timestamp.date() <= D` (no-lookahead). Writes that violate this fail at the gate.

### Two deployable shapes

1. **Strict mode (default)**: misalignment raises `TimestampAlignmentError` → caller's per-shard try/except
   catches it and records `attempted_failed` in the manifest. No parquet written. Forces adapter fix.
2. **Warn mode**: log + emit `DATA_ALIGNMENT_VIOLATION` event + proceed with write. Useful during
   migration when some adapters aren't yet compliant.

Rollout: warn-mode first to measure violation volume; strict-mode once all adapters are clean.

## Pre-audit manifest

| File / thing to find                                                                                         | Purpose                                                                    | Expected outcome                                                                                          |
| ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `unified_trading_library/feature_service_base/write_gate.py`                                                 | Reference impl of `FeatureWriteGate` for feature writes.                   | Mirror shape for instruments write-gate.                                                                  |
| `unified_trading_library/canonical/domain/timestamp_alignment.py` (if exists, else new)                      | Where `validate_timestamp_date_alignment` lives.                           | Extend to accept `column_candidates=["valuation_date", "as_of_date", ...]` list + batch date.              |
| `instruments-service/instruments_service/engine/orchestrator.py` `sink.write(...)` call sites                | Count + classify writes: per-date raw adapter writes vs summary/index writes. | ~30 call sites expected. Each gets a `validate_and_write(df, partition, batch_date)` wrapper.             |
| UTL `events` registry                                                                                        | Add `DATA_ALIGNMENT_VIOLATION` event def.                                  | Payload: `{venue, entity, date, column, offending_value, row_count}`.                                     |
| Codex `06-coding-standards/validation-patterns.md`                                                           | Document the rule.                                                         | Add a §Timestamp-Alignment-Gate subsection.                                                               |

## Success criteria

- UTL: `InstrumentsWriteGate.validate_and_write(df, partition, batch_date)` helper ships. Unit-tested with
  positive (compliant) + negative (wall-clock row on historical batch) cases.
- instruments-service: every `sink.write(...)` in `orchestrator.py` goes through the gate. Warn-mode
  enabled in prod; count of `DATA_ALIGNMENT_VIOLATION` events over 1 week baselines the cleanup scope.
- Codex: §Timestamp-Alignment-Gate subsection added, cross-referenced from §5 lookahead-bias rules.
- Regression test: a simulated adapter return with `datetime.now(UTC)` stamped row on a 2023-03-16 batch
  emits `DATA_ALIGNMENT_VIOLATION`, blocks the write (strict mode), and `record_failed`s the shard.

## Phases

### Phase 0: Audit sink.write call sites + existing UTL validator [SEQUENTIAL]

- [ ] [AGENT] P0. Grep `instruments_service/engine/orchestrator.py` for `sink.write(`. Classify each:
      - A: per-date raw-data write (gate applies)
      - B: summary / index / aggregate write (gate may not apply)
      Document counts in PRE-AUDIT-FINDINGS.

- [ ] [AGENT] P0. Read `validate_timestamp_date_alignment` impl in UTL. Document the
      batch-date-vs-column-value signature. If it's feature-specific (column name hardcoded), extend to
      accept a `column_candidates` list.

- [ ] [AGENT] P0. Grep `datetime.now(UTC)` in all instruments-service adapters — produce a report of other
      wall-clock-stamp sites that may have the same bug as Transfermarkt's `valuation_date`. Embed in
      PRE-AUDIT-FINDINGS.

### Phase 1: UTL InstrumentsWriteGate [SEQUENTIAL, depends on Phase 0]

- [ ] [AGENT] P0. Add `unified_trading_library/instruments_write_gate.py` exporting
      `InstrumentsWriteGate.validate_and_write(df, partition, batch_date, mode='strict'|'warn')`.
      Checks: for each column in a configurable list of "as-of" candidates (`as_of_date, valuation_date,
      data_available_at, kickoff_utc, event_time, computed_at`), assert all non-NULL values satisfy
      `value.date() <= batch_date`.

- [ ] [AGENT] P0. Add `DATA_ALIGNMENT_VIOLATION` event to UTL events registry if not present.

- [ ] [AGENT] P0. Unit tests:
      - Compliant DataFrame (all `valuation_date <= batch_date`) → write proceeds, no event.
      - Non-compliant row (`valuation_date > batch_date`) in strict mode → raises `TimestampAlignmentError`.
      - Non-compliant row in warn mode → event emitted, write proceeds.
      - NULL values pass (nothing to check).
      - Multi-column mix (some compliant, some not) → all violations reported.

### Phase 2: Wire instruments-service [SEQUENTIAL after Phase 1]

- [ ] [AGENT] P0. Replace each `sink.write(...)` in `orchestrator.py` (category A from Phase 0) with
      `gate.validate_and_write(...)`. Default to warn-mode until all adapters clean.

- [ ] [AGENT] P0. For each per-shard try/except in the orchestrator, extend the except clause to catch
      `TimestampAlignmentError` and `manifest.record_failed(...)` the shard with `error="ALIGNMENT_VIOLATION"`.

- [ ] [AGENT] P0. Unit tests: simulated adapter output with wall-clock-now on historical batch →
      manifest records `attempted_failed` + event emitted + no parquet written (strict mode).

### Phase 3: Measurement + codex [SEQUENTIAL]

- [ ] [AGENT] P1. Enable warn-mode in prod for 1 week. Query events.jsonl for count of
      `DATA_ALIGNMENT_VIOLATION` events per venue + per column. Document in plan.

- [ ] [AGENT] P1. Fix any non-compliant adapters surfaced (expected candidates beyond Transfermarkt:
      api_football injuries, footystats matches, understat_xg — whichever wall-clock-stamp the Phase 0
      audit catches).

- [ ] [AGENT] P1. Flip default to strict-mode. Update codex.

- [ ] [AGENT] P1. Update
      [`codex/06-coding-standards/validation-patterns.md`](../../unified-trading-pm/codex/06-coding-standards/validation-patterns.md)
      with the new §Timestamp-Alignment-Gate subsection. Cross-ref from codex
      `02-data/sports-scheduling-and-sharding.md` §5.

### Phase 4: QG + quickmerge [SEQUENTIAL]

- [ ] [AGENT] P0. `bash unified-trading-library/scripts/quality-gates.sh` green.
- [ ] [AGENT] P0. `bash instruments-service/scripts/quality-gates.sh` green.
- [ ] [AGENT] P0. Commit + push in dep order: UTL → instruments-service → PM.
- [ ] [HUMAN] P0. Approve unlock once strict-mode has run in prod for ≥ 3 days with zero alignment
      violations.

## Dependency graph

```
Phase 0 (audit sink.write + validator + wall-clock grep) [SEQUENTIAL]
      │
      └─► Phase 1 (UTL InstrumentsWriteGate)            [SEQUENTIAL]
             │
             └─► Phase 2 (Wire instruments-service)    [SEQUENTIAL]
                    │
                    ├─► Phase 3 (Measure + clean up + strict-mode + codex)
                    │
                    └─► Phase 4 (QG + quickmerge + HUMAN unlock)
```

## SSOT cross-refs

- Lookahead-bias rule: codex `02-data/sports-scheduling-and-sharding.md` §5.
- Existing FSS write-gate: `unified-trading-library/unified_trading_library/feature_service_base/write_gate.py`
  + `feature_service_base/`.
- Point-in-time enforcement: `unified_trading_library/point_in_time.py`.
- Observed violation commits (both fixed): instruments-service `cdded95` (TM season-derivation +
  valuation_date None-pass-through).

## Out of scope

- MTDS + features-* services — they already use `FeatureWriteGate` through feature_service_base. No new
  work.
- External-venue adapters (CeFi / DeFi / TradFi market data) — they have their own validation patterns
  (candle-time alignment is already checked in MTDS). This plan is scoped to sports reference-data
  adapters in instruments-service.
- Cross-repo enforcement of the rule via SIT / pre-commit hook — Phase 3 leaves this as a follow-up if
  warn-mode reveals systemic non-compliance.
