---
scope: [engineer]
---

# T+1 audit discrepancy — runbook

## When this fires

The T+1 audit for instruments-live re-runs the prior day's (asset_group, entity-type) refresh from the historical-batch
source and compares against what the live-mode trigger wrote. When the comparison exceeds tolerance, alerting-service
emits `INSTRUMENTS_LIVE_T1_AUDIT_DISCREPANCY` and pages on-call.

## The 60-second triage

1. Open deployment-UI → events tab → filter by `INSTRUMENTS_LIVE_T1_AUDIT_DISCREPANCY` for the alert's `correlation_id`.
2. The event's `metadata.details` carries
   `{asset_group, entity_type, day, live_row_count, batch_row_count, discrepancy_type, sample_diffs: [...]}`.
3. Pick the `discrepancy_type` and follow the matching section below.

## Discrepancy classes

### Class A — `MISSING_ROWS_LIVE`

**Symptom**: live wrote N rows, batch returned N+M rows. Live missed M entities.

**Likely causes**:

- Live source (e.g. CCXT) returned a subset of what the historical source (e.g. Tardis archive) covers.
- Trigger fired but completed before pagination finished (look for `STOPPED` event mid-fetch).
- Pre-flight chain didn't fail-loud but should have (an upstream was stale).

**Action**:

1. Re-run the live trigger for the affected day with `--operation refresh` to pick up missed rows.
2. Verify the manifest now reflects the full row count (drilldown in deployment-UI to the affected
   `(asset_group, entity-type, day)`).
3. If the gap recurs ≥ 3 days running, raise a finding in the source-coverage codex doc for that asset_group.

### Class B — `EXTRA_ROWS_LIVE`

**Symptom**: live wrote N+M rows, batch returned N rows. Live wrote rows that the batch source rejects.

**Likely causes**:

- Live source returned soft-deleted / pre-listed entities that the historical source filters out.
- Adapter's filtering rules drift between live and batch paths (live=batch invariant violated).

**Action**:

1. Inspect the per-row diff in the event payload's `sample_diffs`.
2. If the rows are legitimate (live caught a real entity earlier than batch's settle window), file an issue doc for
   source coverage clarification.
3. If the rows are spurious (adapter bug), block the live trigger via DART kill-switch, raise a code fix, and
   re-validate before re-enabling.

### Class C — `FIELD_VALUE_DRIFT`

**Symptom**: row count matches; per-row field values diverge beyond tolerance (e.g. instrument_type, expiry,
canonical_question_group differ).

**Likely causes**:

- Live source returns a different field representation than batch (e.g. `expiry: 2026-12-26T16:00:00Z` vs
  `expiry: 2026-12-26T21:00:00Z` — UTC vs ET).
- Adapter normalization step diverges between live and batch paths.

**Action**:

1. Pick the diverging field; consult the canonical UAC schema for the entity-type.
2. If the canonical schema agrees with batch (live is wrong), fix the live adapter's normalization path; do NOT "fix"
   batch.
3. If the canonical schema is ambiguous, raise the canonicalization issue as a finding and freeze the disagreeing field
   in both paths until clarified.

### Class D — `AVAILABLE_AT_DRIFT`

**Symptom**: row count + values match; `available_at` column drifts.

**Likely causes**:

- Live stamped `available_at = now()`; batch stamped historical-source's emission time.

**Action**:

- This is **expected** for instruments — `available_at` for instrument refreshes is "when the live pipeline would have
  actually had this row," which differs by definition between live (`now()`) and batch (historical emission). The audit
  should NOT alert on this class for instruments unless the drift exceeds expected bounds (e.g. days, not hours). If
  alerting fires for normal hours-scale drift, tune the threshold in the rule config.
- For market-data audits (separate from instruments), the same row should have the same `available_at` in both paths; if
  it doesn't, treat as Class C.

## When to NOT remediate

- **Last-day-of-source-coverage**: if the day in question is the live source's coverage start (e.g. BITGET 2024-11-08),
  live correctly has fewer rows; batch shouldn't either. Verify against
  [`../../02-data/mtds-data-source-coverage-matrix.md`](../../02-data/mtds-data-source-coverage-matrix.md) before
  re-running.
- **Honest gap window**: per the VIX 15m source layering rule (Barchart 2020-01-02 → 2025-11-12, Yahoo rolling 60d,
  honest gap 2025-11-13 → today − 60d), the audit should already filter the gap; if it doesn't, fix the audit filter.

## Cross-references

- Architecture:
  [`../../04-architecture/instruments-live-architecture.md`](../../04-architecture/instruments-live-architecture.md)
- Pre-flight chain:
  [`../../04-architecture/instruments-preflight-chain.md`](../../04-architecture/instruments-preflight-chain.md)
- Alert taxonomy entry: [`../alerting/alert-code-taxonomy.md`](../alerting/alert-code-taxonomy.md)
- Source coverage SSOT (per asset_group): the per-asset_group coverage matrices under `codex/02-data/`
- Live deployment monitoring (event source):
  [`../../05-infrastructure/live-deployment-monitoring.md`](../../05-infrastructure/live-deployment-monitoring.md)
