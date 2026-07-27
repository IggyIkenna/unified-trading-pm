---
doc_type: issue
title: "CME monolith trades migration tool built + shipped — execution against real objects still pending"
summary: >-
  `market_tick_data_service/scripts/migrate_cme_monolith_trades_2026_07_26.py` (mtds@02284f8e) is designed, built,
  unit-tested, and quality-gates green — it migrates the 30 real `day=*/venue=CME/ticks.parquet` monolith objects
  (Databento MBP-0/trades, all CME symbols mixed per day, no Hive partitioning) to canonical per-contract/chain form via
  the SAME production write path live adapters use (`write_tradfi_shard`), then additively registers manifest rows. This
  doc tracks what's NOT yet done: actually running the tool against the 30 real objects, verifying the writes, and
  (separately, gated) running its `--delete-source` phase.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer]
tags: [tradfi, cme, migration, only-copy, manifest]
related: [/plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md]
created: 2026-07-26
priority: P2
parent_epic: mtds_mdps_master
source: "slot 3, interactive session, 2026-07-26, /autonomous dispatch on the CME monolith P2 todo"
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
---

# CME monolith migration — tool shipped, execution pending

## What's done

- Tool designed + built: reuses `classify_databento_symbol` (real production classifier — combo/option/future/
  continuous detection, expiry derivation) and `write_tradfi_shard` (real production canonical write path) rather than
  reimplementing canonicalisation logic. Combo rows with an unrecoverable underlying are dropped (honest absence),
  mirroring `databento_enrichment.py::_classify_row` exactly.
- Manifest safety mirrors the proven `canonicalize_cme_options_chain_legacy_flat_2026_07_14.py` precedent: additive
  CAS-write, pre-write snapshot backup, consolidator-cron pause/resume (best-effort), dedup-for-idempotency.
- Verify-before-manifest-row: every real write is re-downloaded and row-count-checked before a manifest row is even
  constructed for it.
- `--delete-source` is a SEPARATE CLI phase (never bundled with migrate) that refuses to delete any source object unless
  the live manifest already shows a `captured` row for that day — re-verified live, not from a stale ledger.
- Real worklist: the 30 real days were directly enumerated 2026-07-26 (server-side `match_glob`, 339s off-region —
  confirms this exact shape's already-documented cross-region listing latency) and hardcoded as the tool's static
  worklist (single-walk discipline; this is dead legacy data, no longer written to). One malformed partition value
  observed (`day=2026-03-20T00:00:00+00:00` instead of a plain date) is handled explicitly.
- Shipped: `mtds@02284f8e` — `market_tick_data_service/scripts/migrate_cme_monolith_trades_2026_07_26.py` +
  `tests/unit/scripts/test_migrate_cme_monolith_trades_2026_07_26.py`. Full `quality-gates.sh` green (7056+ tests
  passed, lint clean, no new basedpyright/codex-compliance violations).

## What's NOT done (this doc's actual scope)

- [x] ✅ [SCRIPT] P2. Add a `tradfi-cme-monolith` (+ `tradfi-cme-monolith-delete`) launcher category to
      `launch-canonical-migration-vm.sh` — `deployment-service@58ebabc`. Canary-day support via `CME_DAY`,
      dry-by-default, `--apply --stamp` embedded on `full`.
- [x] ✅ [SCRIPT] P2. Canary day (2026-02-06, largest real day — 1257 groups, all 4 instrument-type shapes) run to
      completion: dry-run clean, then real apply — 999 manifest rows registered, spot-checked object content (ES
      futures_chain: 594,274 rows verified byte-exact against the manifest's `row_count`). See Progress Log below for
      the 3 real bugs this surfaced and fixed.
- [ ] [SCRIPT] P2. Full `--all-days` apply against all 30 known days — IN PROGRESS (see Progress Log), self-monitored
      under `/autonomous`.
- [ ] [SCRIPT] P2. Verify the real write across ALL 30 days: re-check the live manifest shows new `captured` rows for
      `venue=CME, data_type=trades` across every known day, and spot-check a few more written canonical objects.
- [ ] [SCRIPT] P2. Run `--delete-source` in DRY-RUN first (default) and report the candidate list — this is an only-copy
      corpus (2026-07-21 reconciliation report). Per operator ruling 2026-07-27 (delete-safety codex §3, `[SCRIPT]` tag
      now valid for an exhaustively-passing 5-part proof), the actual `--apply` delete MAY be `[SCRIPT]`-eligible once
      the dry-run's proof is complete — but is explicitly NOT authorized in this `/autonomous` run; leave it as a
      reported recommendation only, human-reviewed before anyone applies it.

## Progress Log

**2026-07-27, `/autonomous` run, slot-3** — canary day (2026-02-06) surfaced 3 real bugs, all found via dry-run/apply
against REAL production data (not caught by the unit tests, which use synthetic symbols), all fixed + shipped +
re-verified against the live manifest before moving on:

1. **Crash: malformed COMBO symbol embeds `:`** — a CME/ICE continuous-contract-prefix combo (e.g. `CL:C1 RB-CL H6`,
   `NG:HH J6-V6`, `RB:BF H6-M6-U6`) has a REAL, recognised underlying (so it's not dropped as opaque-CBOE), but the raw
   wire symbol itself carries `:`, which collides with `build_instrument_id`'s own `VENUE:TYPE:SYMBOL` delimiter and
   raised `ValueError` uncaught → crashed the whole day. Production's live adapter
   (`databento_enrichment.py::_classify_row`) already wraps this exact call in `try/except ValueError` and drops the row
   (honest absence) — `write_day_plan` didn't have that guard. Fixed: wrapped `finalise_tradfi_rows_and_path`/
   `write_tradfi_shard` in the same try/except, counts as `dropped_instrument_id_construction_failed`. Shipped
   `mtds@190e839d`.
2. **Stats-aggregation ordering bug** — `run_migrate`'s per-day stats roll-up ran BEFORE `write_day_plan` (which is
   where bug #1's new counter increments), so `dropped_instrument_id_construction_failed` never reached the final
   `MIGRATE DONE totals=` summary even though the per-group WARNING lines showed it happening (258 groups / ~20,220 rows
   for 2026-02-06 alone). Fixed: moved the log+aggregate to run AFTER `write_day_plan`. Shipped `mtds@1e98d69d`.
3. **Manifest dtype mismatch (found mid-APPLY, AFTER all 999 data shards had already written+verified successfully —
   idempotent, safe to re-run)** — `_align_new_rows_dtypes` only coerced new rows TOWARD string when the existing column
   was all-string; it never handled the reverse. Confirmed live against the real 5.8M-row manifest:
   `available`/`expected` are real `bool` (this script stamped `"true"`/`"false"` strings), `row_count`/`schema_version`
   are real `float64`/`int64` (this script stamped string literals) — pyarrow's `to_parquet` then fails to homogenise
   the merged column. Fixed with a bool-branch + a generic numeric-coercion branch (bool checked first since `bool` is a
   Python `int` subclass); verified by simulating the exact merge against the real live manifest before shipping.
   Shipped `mtds@4610eefa`.

Canary re-run after all 3 fixes: clean dry-run (totals include `dropped_instrument_id_construction_failed=258`), clean
apply (`MANIFEST: {'existing_rows': 5825023, 'new_rows': 999, 'merged_rows': 5826022}` — 999 = 1257 groups − 258
dropped, exact match), manifest independently re-read and confirmed (999 rows, `instrument_type` breakdown: 955 combo /
34 futures_chain / 9 future / 1 options_chain, correct dtypes), ES futures_chain object spot-checked (594,274 rows,
exact match to the manifest + the VERIFIED log line, 4 distinct instrument_ids for 4 expiries).

Full `--all-days` apply launched: `canonical-migration-tradfi-cme-monolith-20260727-011420` (mtds tarball pinned exactly
at `4610eefa6b5f`, confirmed via the launcher's tarball-freshness check). 6/30 days done cleanly as of this log entry
(2024-07-15, 2026-02-06 idempotent re-verify, 2026-02-08 through 2026-02-11), no new crash class, ~3-4 min/day.
Self-monitoring under `/autonomous` — next update when the run completes or a new failure needs diagnosis.

## Why split into its own doc

The parent plan (`tradfi_manifest_content_recovery_completion_2026_07_24.md`) is at its 1000-line hard cap; this sibling
doc carries the remaining execution scope per the standard "outside-plan → issue doc" convention rather than cramming
further into an already-full file.

## Codex SSOTs

`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (only-copy delete discipline),
`/codex/05-infrastructure/vm-launcher-runbook.md` (heavy-I/O-on-a-VM rule).
