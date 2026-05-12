---
title: "expected_unattempted not propagated through instruments→MTDS→MDPS→features→ML chain"
created: 2026-05-12
author: ikenna
source:
  - operator direction 2026-05-12 (pre-flight dependency chain audit)
  - explore agent audit: MTDS/MDPS/features/UTL
locked_by: live-defi-rollout
locked_since: 2026-05-12
severity: P1
suggested_owner: ikenna
---

## What I found

The manifest dependency chain (instruments-service → MTDS → MDPS → features → ML) does NOT correctly propagate
`expected_unattempted` status when a service skips a shard because its upstream is absent or because a scope/MVP config
excludes the instrument.

UTL's `record_expected_unattempted()` exists
([manifest_writer.py:1595](../../unified-trading-library/unified_trading_library/manifest_writer.py#L1595)) but is NOT
called by any service in the chain when skipping.

### Per-service gap detail

**MTDS** — does not read instruments-service manifest at all.

- No pre-flight that checks whether an instrument exists in instruments-service before attempting fetch.
- When MTDS tries a fetch for an instrument that instruments-service says is `empty_confirmed` or
  `expected_unattempted`, MTDS writes `attempted_failed` in its own manifest.
- Result: false-positive phantom rows in MTDS manifest for instruments that legitimately don't exist.
- File: `market-tick-data-service/market_tick_data_service/cli/handlers/tick_data_handler.py:54` — uses
  `check_shard_freshness` on its own manifest but never reads instruments-service manifest.

**MDPS** — reads MTDS manifest via `DependencyChecker`
([orchestration_service.py:127](../../market-data-processing-service/market_data_processing_service/app/core/orchestration_service.py#L127)).

- When upstream MTDS shard is absent/empty, MDPS returns empty results (line 136) but does NOT call
  `record_expected_unattempted()` in its own manifest.
- Result: MDPS manifest has NO row for shards skipped due to absent MTDS data. Reconciliation sees a gap with no status,
  which is ambiguous.

**Features** — filters by `subscription_list` config per module.

- Each feature module (delta_one, calendar, onchain, volatility, etc.) has its own `subscription_list`.
- When an instrument is not in the subscription list, the module skips it without calling
  `record_expected_unattempted()`.
- Result: instruments outside MVP scope have no manifest row for features — reconciliation can't distinguish "not
  computed because not in MVP" from "failed to compute" from "never attempted".

**ML** — unknown scope; same pattern assumed.

### Reconciliation script behavior

`reconcile_phantom_manifest_rows_all.py` at line 558 only audits rows where `capture_status == 'captured'`. It does NOT
flag `expected_unattempted` rows as phantoms (correct behavior). BUT: because services write `attempted_failed` instead
of `expected_unattempted`, phantom counts are inflated with false positives that don't represent real data gaps.

## Why it matters

1. **False-positive phantom counts**: MTDS `attempted_failed` rows for instruments that instruments-service says
   `empty_confirmed` inflate the phantom count. Target "0 phantoms" is unreachable without this fix because MTDS will
   keep re-creating these rows on next run.

2. **Missing data is invisible**: MDPS and features write NO manifest row for skipped shards → the deployment-api
   data-status panel shows nothing (not `empty_confirmed`, not `expected_unattempted`) for those shards → operator has
   no visibility into why data is missing.

3. **Pre-flight gates don't propagate**: Each service runs its own pre-flight but doesn't learn from upstream's
   honest-absence declarations. A chain of `empty_confirmed` at instruments-service should cascade as
   `expected_unattempted` through MTDS → MDPS → features without any service actually trying to fetch or compute.

4. **Config-driven scope (MVP lists) is invisible to manifest**: Features subscription lists exist in config but aren't
   surfaced in the manifest — so there's no way to audit "which coins are in the features MVP scope" from manifest data.

## Recommended decision

**Phase 1 (P0 — needed before reconciliation `--apply-flips` runs)**:

Add instruments-service manifest read to MTDS orchestrator pre-flight. For each shard MTDS is about to attempt, check
instruments-service manifest for that `(asset_group, instrument_id, date)`:

- If instruments-service says `empty_confirmed` or `expected_unattempted` → MTDS calls
  `record_expected_unattempted(reason=EXPECTED_UPSTREAM_EMPTY)` and skips fetch.
- Pattern: same `check_shard_freshness` framework already in UTL, extended with upstream-bucket read.

**Phase 2 (P1)**:

Add `record_expected_unattempted()` call in MDPS `DependencyChecker` when skipping due to absent MTDS data. Already has
the right pre-flight; just needs to record rather than silently return empty.

**Phase 3 (P1)**:

Add `record_expected_unattempted()` in features batch handlers for instruments not in `subscription_list`. Centralize
the MVP scope as a UAC or UTL constant so it's visible outside the per-module config.

**Phase 4 (P2 — nice to have)**:

ML scope list → same pattern as features.

## Successor plan

This issue should be folded into `writegate_honest_coverage_endtoend_2026_05_06.md` as a new slice (Phase 7:
upstream-propagation chain). Alternatively, spawn a new plan `expected_unattempted_propagation_chain_2026_05_12.md` if
writegate is near close-out.

**Do NOT run `--apply-flips` on MTDS manifest before Phase 1 is shipped** — you will flip legitimate `attempted_failed`
rows (instruments that never existed) to `empty_confirmed`, masking the fact that MTDS is attempting fetches it
shouldn't be doing at all.
