---
doc_type: issue
title:
  ManifestWriter.record_captured() / record_captured_from_counts() validate available_at but never persist it — every
  CAPTURED manifest row system-wide has always defaulted to ""
summary: >
  While root-causing the sports CF-8 available_at backfill regression
  (sports_cf8_available_at_backfill_regression_2026_07_13.md), found a second, separate, and much broader bug in the
  SAME area: ManifestWriter.record_captured() validates that its df carries a populated available_at column
  (assert_available_at_present), and record_captured_from_counts() validates its available_at_envelope, but NEITHER
  method ever passes that value into the AvailabilityRecord it constructs. Fixed both (unified-trading-library@9c9cdc50)
  with unit-test coverage, but this defect predates the fix by an unknown amount of time and affects every asset_group
  that calls record_captured() (confirmed non-test call sites: 18 in instruments-service, 43 in
  market-tick-data-service, 3 in market-data-processing-service, 4 in execution-service, 5 in strategy-service) — the
  CF-8-style audit only ever ran against sports; other asset_groups' manifest available_at fill rate has never been
  checked and may be systemically low for the same reason.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [data]
repos:
  [
    unified-trading-library,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    execution-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: [data-correctness, available-at, manifest-writer, cross-cutting, record-captured, lookahead-bias]
related:
  [
    plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    plans/active/sports_manifest_canonicalisation_2026_06_01.md,
    codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-13
parent_epic: manifest_master
priority: P1
source:
  sports_manifest_canonicalisation-004 dispatch, slot 3, 2026-07-13 (found while root-causing a different, sports-scoped
  todo)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
locked_by:
resolved_by:
---

# record_captured() / record_captured_from_counts() never persisted available_at onto the manifest index

## What happened

Dispatched to `sports_manifest_canonicalisation-004` ("CF-8 `available_at` live backfill pass"). The plan's own text
(and `sports_cf8_available_at_backfill_regression_2026_07_13.md`) explicitly forbade re-running that live backfill until
its P0 root-cause todo was resolved, so instead of re-attempting the destructive operation I worked that P0 todo: a
synthetic (non-production) repro of `ManifestWriter._records_to_dataframe()`.

While doing so, another agent (slot 11) independently found and fixed the SAME root cause concurrently
(`unified-trading-library@f5f15e3a`): the serializer never included `available_at` in its per-row dict, so every
`write()` silently dropped the column regardless of what the in-memory record carried. That fix is correct and
sufficient for the `record_empty`/`record_failed`/`add()` write paths (all three DO correctly thread `available_at` onto
the in-memory `AvailabilityRecord` — confirmed by reading `_writer_record.py` / `_writer_ingest.py`).

**But `record_captured()` and `record_captured_from_counts()` — the OTHER two write paths, and the ones actual
production adapters use for real captured data — never threaded `available_at` onto the in-memory record AT ALL**,
independent of the serializer bug:

- `record_captured(df=..., ...)` (`unified_trading_library/manifest_writer/_writer_captured.py`) calls
  `assert_available_at_present(df)` — a **validation-only** gate confirming the caller's data `df` has a populated
  `available_at` column — then constructs the `AvailabilityRecord` for the MANIFEST INDEX row without ever reading that
  column's value. The manifest row's `available_at` field is simply omitted from the constructor call, so it silently
  defaults to `""`.
- `record_captured_from_counts(available_at_envelope=..., ...)` accepts a mandatory, validated (presence + tz-awareness)
  `available_at_envelope` parameter, uses it for `attempted_at=envelope_ts.isoformat()`... but never for
  `available_at=`. Same omission.

This is a genuinely different bug from the serializer issue: even with `f5f15e3a` alone, every row written via
`record_captured()`/`record_captured_from_counts()` would STILL have `available_at=""` on the manifest index, because
the value never reaches the `AvailabilityRecord` constructor in the first place. The serializer fix only guarantees that
whatever value the record carries survives to the parquet — it does nothing for a record that never had the value
stamped on it.

## Why this was missed for so long

The masking pattern is identical to the one `test_manifest_writer_serialized_columns.py`'s own docstring describes for
the pre-2026-06-16 v6-v9 column drop: `test_manifest_writer_live_mode_available_at.py` (the existing "A.8" contract test
for `record_captured` + `available_at`) asserts ONLY that no `LookaheadBiasError` is raised and that shard-shape fields
(`capture_status`, `data_type`, `venue`, `instrument_count`) are correct — it never asserts
`writer._records[-1].available_at` or the serialized DataFrame's value. The presence-gate
(`assert_available_at_present`) passing was mistaken for "available_at is stamped," when it only ever validated the
INPUT, not the OUTPUT.

## Blast radius (NOT yet audited — this issue doc's main ask)

Confirmed non-test call sites of `record_captured(` (a floor, not a full audit — services not checked, e.g.
alerting-service, deployment-api, fund-administration-service, greeks-service, trading-agent-service, ml-service,
features-service families, unified-trading-system-ui backend, are not yet grepped):

| repo                           | non-test `record_captured(` call sites |
| ------------------------------ | -------------------------------------- |
| market-tick-data-service       | 43                                     |
| instruments-service            | 18                                     |
| strategy-service               | 5                                      |
| execution-service              | 4                                      |
| market-data-processing-service | 3                                      |

Every asset_group these services write (tradfi, cefi, defi, sports, and whatever strategy/execution stamp) has, until
`unified-trading-library@9c9cdc50`, had `available_at=""` on every `record_captured`-written manifest row — the CF-8
sports investigation only ever measured sports (IS 62.9%, MDPS ~0%) because that is the ONLY asset_group with a
dedicated audit script (`cf_manifest_audit_2026_06_01.py`). Whether tradfi/cefi/defi manifest `available_at` fill rates
are similarly degraded is UNKNOWN — no equivalent audit exists for them.

## Fix applied

`unified-trading-library@9c9cdc50` (built on top of `f5f15e3a`):

- `record_captured()`: after the existing `assert_available_at_present(df)` gate passes, derive
  `_available_at_value = str(df["available_at"].max())` (empty df / missing column → `""`) and pass
  `available_at=_available_at_value` into the `AvailabilityRecord` constructor.
- `record_captured_from_counts()`: pass the already-validated `available_at_envelope` through as
  `available_at=envelope_ts.isoformat()`.
- Extended `test_manifest_writer_serialized_columns.py` with value-level assertions
  (`row["available_at"] == writer._records[-1].available_at`) on both `record_captured` tests, so a future regression in
  either method fails loudly rather than only checking column presence.

Full `quality-gates.sh` green (281s). Unit-tested only — **NOT verified against production data** (no production write
was made or attempted by this touch).

## Recommended next steps (not mine to decide unilaterally — routing to operator/manifest_master owner)

1. **Audit the true blast radius** — for each asset_group/service in the table above (and the ones not yet grepped),
   sample the current manifest index's `available_at` fill rate for `capture_status=captured` rows. This tells us
   whether this was a sports-only-severity issue or whether tradfi/cefi/defi CF-8-equivalents are ALSO silently RED.
2. **Decide whether a backfill is warranted for non-sports asset_groups** — if fill rates are low elsewhere too, this
   becomes a much larger cross-asset-group backfill program, not a sports-scoped one. Should probably become its own
   plan under `manifest_master` rather than living in this issue doc.
3. **New captures are now correct** (as of `9c9cdc50`) — no further action needed for rows written after this fix lands
   on `live-defi-rollout`/promotes; this issue is only about the historical backlog.
4. This does NOT block or change `sports_cf8_available_at_backfill_regression_2026_07_13.md`'s own P1 todo (re-attempt
   the sports-scoped full-corpus backfill) — that fix (`f5f15e3a`) is independently sufficient for the `record_empty`/
   `record_failed`/`add()` paths the sports rebuild script uses. This issue doc's fix (`9c9cdc50`) is orthogonal —
   relevant to `record_captured`-based captures, not the rebuild-walk path.

## Todos

- [ ] [DATA] P1. Audit current manifest `available_at` fill rate for `capture_status=captured` rows, per asset_group,
      for every service in the blast-radius table above (plus the not-yet-grepped services named in that section) —
      determine whether this is sports-severity or worse elsewhere. (repo: unified-trading-library, all services above)
- [ ] [DATA] P2. Based on the audit's findings, scope a backfill plan for any non-sports asset_group found to have a
      degraded `available_at` fill rate — route through `manifest_master` epic, NOT this issue doc, once scoped. (repo:
      TBD per audit)
