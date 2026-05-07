---
title: Expected-Absence Backfill Runbook
status: planned
created: 2026-05-07
authoritative_for: Per-asset-group runbook for back-filling `record_expected_empty(reason=...)` rows over legacy null-reason manifest entries. Complements the on-the-fly UTL `classify_legacy_empty_row()` helper by establishing a one-time batch backfill that stamps a real reason on every legacy `empty_confirmed AND error_reason IS NULL` row.
referenced_by:
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md
related:
  - codex/02-data/honest-absence-downstream-handling.md
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/manifest-migration-coordination.md
---

# Expected-Absence Backfill Runbook

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from active plans. Body to be filled in
> as the per-asset-group reconcilers ship under writegate Phase 3.D.

## Purpose

The reader-side UTL helper [`classify_legacy_empty_row()`](https://github.com/IggyIkenna/unified-trading-library)
classifies legacy null-reason rows on-the-fly so deployment-api never returns an unclassified `empty_confirmed`. But
that's a runtime fallback — the canonical fix is to materialise a real `error_reason` on disk. This doc is the runbook
for executing that one-time backfill across all 5 asset_groups.

## Scope

- Per-asset-group reconcile scripts: `instruments-service/scripts/reconcile_expected_absence_reasons.py` (already
  shipped) covers the on-disk manifest pass.
- Operator-driven invocation: scan-only first; `--apply-flips` requires per-VM shard isolation envvars.
- Per-asset-group classifier dispatch — TradFi calendar, Sports source-coverage + known gaps, DeFi chain genesis,
  CeFi/Prediction default `SOURCE_RETURNED_ZERO`.
- Excluded: rows with non-null reason already (no-op); rows with `capture_status != empty_confirmed` (different fix).

## Outline (planned sections)

1. **Pre-run validation** — manifest snapshot taken; per-VM shard isolation envvars set; `--dry-run` produces a sane
   distribution of reasons.
2. **Per-asset-group invocation order** — TradFi first (most rows, simplest classifier), then Sports, DeFi, CeFi,
   Prediction. Allows rolling rollback if early asset_group reveals a classifier bug.
3. **Concurrency posture** — single VM per asset_group with `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME` set; consolidator
   merges into canonical within ~5min.
4. **Operator monitoring** — RECONCILER_* events emitted to event stream; CSV audit written to GCS audit bucket.
5. **Verification** — post-run, query `_index/availability_index.parquet` for `capture_status=empty_confirmed AND
   error_reason IS NULL` count; expect 0 (or only rows added since reconciler started).
6. **Rollback** — manifest snapshot pre-run; restore via GCS object versioning if reason-distribution is unexpectedly
   skewed (e.g. classifier mis-attributing too many rows to `SOURCE_RETURNED_ZERO`).
7. **Re-run cadence** — quarterly thereafter; new gaps without reasons should not appear once Tier 2 orchestrator
   pre-skips emit `record_expected_empty()` directly.

## Cross-references

- **Plan(s) implementing this:** [`writegate_honest_coverage_endtoend`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.plan.md) Phase 3.D.
- **Related codex SSOTs:** [`honest-absence-downstream-handling`](./honest-absence-downstream-handling.md), [`availability-manifest-and-data-status`](./availability-manifest-and-data-status.md), [`manifest-migration-coordination`](./manifest-migration-coordination.md).
- **Code:** `instruments-service/scripts/reconcile_expected_absence_reasons.py` (shipped Tier 3D.1), `unified-trading-library/legacy_reason_classifier.py` (shipped Tier 3D.2).

## Open questions

- For TradFi: do we backfill venue trading-calendar holidays globally, or limit to the venues we actively trade?
- For Sports: are `KNOWN_COVERAGE_GAPS` ranges complete enough to drive classification, or should we also stamp
  `EXPECTED_PAUSED_LEAGUE` on inferred gaps via empty-stretch detection?
- Does the reconciler need to handle `attempted_failed` rows where the original error was actually expected-absence in
  disguise? (probably no — leave alone; that's a separate audit)
