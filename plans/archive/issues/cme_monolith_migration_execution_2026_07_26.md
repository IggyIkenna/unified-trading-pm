---
doc_type: issue
title: "CME monolith trades migration tool built + shipped — execution against real objects still pending"
summary: >-
  `market_tick_data_service/scripts/migrate_cme_monolith_trades_2026_07_26.py` migrated all 30 real
  `day=*/venue=CME/ticks.parquet` monolith objects to canonical per-contract/chain form via the SAME production write
  path live adapters use (`write_tradfi_shard`), additively registered 23,589 new manifest rows, and had the result
  independently verified (all 30 days present, row-count math reconciled exactly, 4 objects spot-checked byte-exact).
  `--delete-source` DRY-RUN confirms all 30 source objects as delete-safe (manifest-verified `captured` per day); the
  actual `--apply` delete of the only-copy monolith source objects is a deliberate human-reviewed decision, not run
  here.
status: resolved
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
resolved_by: "slot 3, /autonomous run, 2026-07-27"
drift_direction: advance-code
---

> **🟢 RESOLVED 2026-07-27** — all 30 real days migrated + independently reconciled (24,588 captured rows exact match),
> `--delete-source` dry-run confirms all 30/30 delete-safe. The one remaining decision (the `--delete-source --apply`
> irreversible delete) is a standing human-sign-off judgment call by this doc's own policy, not an open todo — this
> doc's full stated scope is complete.

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
- [x] ✅ [SCRIPT] P2. Full `--all-days` apply against all 30 known days —
      `canonical-migration-tradfi-cme-monolith-     20260727-011420`, completed clean (`exit_code=0`, VM self-deleted).
      `MIGRATE DONE totals={dropped_continuous_or_     unrecoverable: 302351, kept_future: 65239402, kept_option: 1097109, kept_combo: 15542780, dropped_instrument_id_     construction_failed: 6150}`;
      `MANIFEST: {existing_rows: 5827108, new_rows: 23589, merged_rows: 5850697}`.
- [x] ✅ [SCRIPT] P2. Verify the real write across ALL 30 days — independently re-read the live manifest (not just
      trusted the tool's own log): all 30 known days present, zero missing; row-count math reconciled EXACTLY (30,738
      total groups − 6,150 dropped = 24,588 captured rows total = 999 already-captured from the canary + 23,589 newly
      added this run, matching the tool's own reported `new_rows`). `2026-03-20` confirmed registered under its clean
      calendar date (not the malformed `T00:00:00+00:00` partition value), proving `SourceObject.day` truncation worked.
      3 additional objects spot-checked byte-exact against manifest `row_count` (on top of the canary's ES futures_chain
      check): `2026-03-20` ES futures_chain 591,679 rows, `2026-03-09` RTY futures_chain 247,864 rows, `2024-07-15` ES
      options_chain 3,242 rows — all exact matches, correctly-shaped canonical `instrument_id`s.
- [x] ✅ [SCRIPT] P2. Run `--delete-source` in DRY-RUN —
      `canonical-migration-tradfi-cme-monolith-delete-20260727-     032611`, clean (`exit_code=0`).
      `=== DELETE-SOURCE DRY-RUN stats={'would_delete': 30} ===` — all 30/30 source monolith objects confirmed "day=X
      confirmed migrated" by the tool's own live-manifest re-verification gate (per source object, independent of the
      migrate run's own bookkeeping). Full candidate list in the Progress Log below. **The actual `--apply` delete is
      explicitly NOT run in this `/autonomous` run** — left as a human-reviewed recommendation per this doc's own stated
      policy (only-copy corpus, 2026-07-21 reconciliation report).

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
at `4610eefa6b5f`, confirmed via the launcher's tarball-freshness check). Ran to completion in ~2h with NO new crash
class across all 30 real days (the 3 fixes above were the only bug classes hit, and they recurred consistently — never a
4th new failure mode) — confirms all 3 were genuinely structural (shape-class, not day-specific), matching the
prediction made before launching the full run. Final:
`MIGRATE DONE totals={'dropped_continuous_or_unrecoverable': 302351, 'kept_future': 65239402, 'kept_option': 1097109, 'kept_combo': 15542780, 'dropped_instrument_id_construction_failed': 6150}`,
`SUMMARY (APPLIED)`, `MANIFEST: {'existing_rows': 5827108, 'new_rows': 23589, 'merged_rows': 5850697}`. VM self-deleted
cleanly (`exit_code=0`).

**Independent verification (not just trusting the tool's own log)**: read `_index/availability_index.parquet` directly,
filtered to `venue=CME, data_type=trades, pipeline_mode=batch_databento, source=databento, capture_status=captured`,
restricted to the 30 known days — all 30 present, 0 missing, 24,588 total captured rows. Reconciliation: summed
`groups=`/`dropped_instrument_id_construction_failed=` across all 30 real per-day log lines directly (not estimated) =
30,738 groups total, 6,150 dropped → 24,588 expected-captured, EXACT match to the independently-measured manifest count;
and 24,588 − 999 (already captured from the canary run, confirmed via the log's own
`Skipping 999 already-captured row(s) (idempotent re-run)` line for 2026-02-06) = 23,589, EXACT match to the tool's own
reported `new_rows`. `2026-03-20` confirmed present under the clean calendar date. 3 objects spot-checked byte-exact
(see checkbox above).

**`--delete-source` DRY-RUN full candidate list** (`canonical-migration-tradfi-cme-monolith-delete-20260727-032611`,
`exit_code=0`, `would_delete: 30`) — every one of the 30 real source objects, each independently re-confirmed "day=X
confirmed migrated" against the LIVE manifest by the tool's own gate (not the migrate run's bookkeeping):
`day=2024-07-15`, `2026-02-06`, `2026-02-08`, `2026-02-09`, `2026-02-10`, `2026-02-11`, `2026-02-12`, `2026-02-13`,
`2026-02-15`, `2026-02-16`, `2026-02-17`, `2026-02-18`, `2026-02-19`, `2026-02-20`, `2026-02-22`, `2026-02-23`,
`2026-02-24`, `2026-02-25`, `2026-02-26`, `2026-02-27`, `2026-03-02`, `2026-03-03`, `2026-03-04`, `2026-03-05`,
`2026-03-06`, `2026-03-08`, `2026-03-09`, `2026-03-10`, `2026-03-11`, `2026-03-20` (source path
`raw_tick_data/by_date/day=2026-03-20T00:00:00+00:00/venue=CME/ticks.parquet` — the malformed source path itself, as
expected; only the MANIFEST/canonical-output side uses the clean date). **Recommendation for whoever makes the delete
call**: the proof is exhaustive (all 30/30, migrate-verified + independently re-verified twice over) and this is
additive-registration-then-delete-source (never destructive-in-place), so the delete is low-risk — but it is still a
real, irreversible deletion of an only-copy corpus's LAST remaining source form, so per this doc's standing policy it is
left for human sign-off (`--apply` flag), not auto-run here.

## Autonomous-run final report (rule 9)

Ran under `/autonomous` end-to-end from the canary re-launch through this final verification, no operator input needed.
**Forced-tradeoff decisions made under rule 1**: none required — no genuine physical impossibility was hit; every
obstacle (3 real bugs) had a clean, root-cause fix. **Genuine impossibilities**: none. **Verified end-state**: migrate
done (30/30 days, independently reconciled), verify done (manifest + object spot-checks), delete-source dry-run done
(30/30 candidates confirmed) — this doc's full stated scope is complete. **What's left for the operator**: exactly one
judgment call, by design — whether/when to run the actual `--delete-source --apply` against the only-copy monolith
source objects (never auto-applied per this doc's standing policy, regardless of how clean the proof is). Nothing else
requires operator attention on this task.

## Why split into its own doc

The parent plan (`tradfi_manifest_content_recovery_completion_2026_07_24.md`) is at its 1000-line hard cap; this sibling
doc carries the remaining execution scope per the standard "outside-plan → issue doc" convention rather than cramming
further into an already-full file.

## Codex SSOTs

`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (only-copy delete discipline),
`/codex/05-infrastructure/vm-launcher-runbook.md` (heavy-I/O-on-a-VM rule).
