---
doc_type: issue
title: cefi instruments-store-cefi-prd — 6.87% blank data_type residual (post v8→v9 walk)
summary: >-
  Live cf_manifest_audit re-run against instruments-store-cefi-prd found the parent v8→v9 single-walk todo's named
  criteria (CF-1/3/4/8, capture_status null%) fully GREEN, but a distinct blank-data_type residual (6.87% of rows) is
  not yet resolved -- filed as its own bounded follow-up.
status: open
nature: guideline
asset_group: [cefi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [cefi, instruments-store, manifest, data-type, data-correctness]
related: [/plans/active/data_completion_cefi_2026_07_15.md]
created: 2026-07-29
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on:
assigned_role: data_engineering
source: [data_completion_cefi_2026_07_15.md, cf_manifest_audit live re-run 2026-07-29]
drift_direction: advance-code
context_scope:
  [
    /plans/active/data_completion_cefi_2026_07_15.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    unified-trading-library/unified_trading_library/manifest_writer_normalising.py,
    /plans/active/issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md,
    /plans/archive/issues/manifest_reprocessing_generic_utility_2026_07_07.md,
    unified-trading-library/unified_trading_library/manifest_writer/_rows.py,
  ]
---

## What I found

Re-ran `unified_trading_library.cf_manifest_audit.audit()` live (read-only, `mode="changed"`, no `--apply`) against
`instruments-store-cefi-prd-central-element-323112` (84,542 rows) as part of closing
`data_completion_cefi_2026_07_15.md`'s "cefi `instruments-store` `_index` v8→v9 single-walk" todo. The core v8→v9
migration criteria named by that todo are now fully GREEN: CF-1 schema_version=100% v9, CF-3 pipeline_mode
populated=100%, CF-4 source blank=0%, CF-8 available_at non-null=100%, `capture_status` null=0% (was ~40% at the
2026-06-07 baseline).

One named residual from that same original diagnosis is NOT fully resolved: **blank `data_type` = 6.87% (5,807/84,542
rows)**, down from "blank on every row" (100%) at the 2026-06-07 baseline but not zero. Breakdown by `capture_status`:

- `empty_confirmed`: 4,935
- `expected_unattempted`: 856
- `attempted_failed`: 15
- `captured`: **1** ← the one row that looks like a genuine gap (a captured cell should always carry a typed
  `data_type`)

All 5,807 blank rows have `service_name=instruments-service`. By venue: POLYMARKET-PERP 1,435 / KALSHI-PERP 1,428 /
COINBASE-CDE 1,420 / LIGHTER-ZKSYNC 976 / PACIFICA-SOLANA 489 / BINANCE-DELIVERY 32 / DERIBIT-COMBO 7 / a handful of
others. The non-blank rows (78,735) all carry `data_type=instruments` (the IS reference index is venue×date-keyed, not
literally data_type-keyed, per the original 2026-06-07 diagnosis — this file's `data_type` column is a bolt-on typing
rather than a native key column).

## Why it matters

Per the data-pipeline-correctness HARD RULE, a manifest cell in a non-empty `capture_status` state should carry
complete, typed columns — a blank `data_type` on 6.87% of rows is a residual gap in the "canonical form should still
type it" recommendation from the original diagnosis, even though it doesn't block the v8→v9 schema/column migration
itself (which is what the parent todo's CF-1/3/4/8 named criteria actually gate). The 1 blank-`data_type` row with
`capture_status=captured` is the highest-priority sub-case — a captured cell with no data_type is a genuine typing gap,
not a structural non-issue.

## Live diagnosis (2026-07-30, read-only re-download of `_index/availability_index.parquet`, 84,542 rows — matches doc)

**Todo 1 (the 1 `captured`+blank row) — fully identified.**
`date=2023-12-16, venue=BITFINEX-SPOT, capture_status=captured, row_count=284, available=True, expected=True, written_at=2026-07-06T15:00:10.079766Z`.
`instrument_id` is `None` on this row too — expected, per this doc's own note that the IS reference index is
venue×date-keyed, not instrument-keyed. Cross-checked against every OTHER `BITFINEX-SPOT` `captured` row (2,399 total):
2,398/2,399 carry `data_type=instruments` — this is the sole exception for that venue, and (checked globally across all
84,542 rows) the sole `captured`+blank row in the **entire** index (56,117/56,118 captured rows are correctly typed).
The write batch is isolated: only 5 rows in the index share a `written_at` within ±2 minutes of this row, covering
`date=2023-12-16` across BITFINEX-SPOT/PACIFICA-SOLANA/LIGHTER-ZKSYNC/KALSHI-PERP/POLYMARKET-PERP — the other 4 are
`empty_confirmed` (correctly blank). So a small backfill run re-captured this one historical date across several venues;
every sibling in that same batch behaved correctly, but the one row that WAS captured didn't get `data_type=` set — an
isolated writer-call gap in that specific run, not a systemic pattern (its `written_at` is a full month later than the
main 2026-06-26 backfill that populated the other 2,398 BITFINEX-SPOT rows, so it's a distinct code path/run, not
reproducible-on-every-write).

**Why this is NOT a trivial single-cell patch (re-scoping, not closing)**: `data_type` is a member of
`unified_trading_library.manifest_writer._rows._ROW_KEY_COLUMNS` — the manifest's ROW IDENTITY key, not a payload field.
A row keyed `(date=2023-12-16, venue=BITFINEX-SPOT, data_type="", ...)` and a row keyed
`(..., data_type= "instruments", ...)` are different logical shards to the manifest's own addressing scheme.
"Backfilling" this value is therefore not a value UPDATE — it requires writing a NEW correctly-keyed row via
`NormalisingManifestWriter. record_captured(...)` (the safe, generation-matched, concurrent-write-aware path — confirmed
via `ManifestWriterIoMixin`'s `PreconditionFailed`-retry + write-buffer design) and then reconciling the now-orphaned
blank-`data_type`-keyed row (delete? supersede? — depends on whether the manifest consolidator already treats a
same-date/venue blank-key row as legacy-superseded once a typed sibling exists, which was not verified this session).
That reconciliation step needs a maintainer who understands the consolidator's merge semantics for this case — left as
the properly-scoped remaining action below, not attempted here (this session's investigation was read-only against a
downloaded index copy; no prod manifest writes were made).

> **✅ OWNERSHIP RESOLVED 2026-07-31 (corpus-wide ownership-conflict sweep).** Three docs looked like they were fighting
> over "the cefi blank-`data_type` population". They are not — the split is by **bucket**, and it is clean: **THIS doc
> owns `instruments-store-cefi-prd-central-element-323112`** (the IS instruments manifest) and nothing else.
> `/plans/active/issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md` owns the entirely separate
> `market-data-tick-cefi-prd-central-element-323112` MTDS tick manifest (9,750 rows: 9,743 backfill + 7 bare-`OKX`
> reclassify) — **do not touch that population from here**, and do not treat its numbers as describing these rows.
> `/plans/archive/issues/manifest_reprocessing_generic_utility_2026_07_07.md` is **not a competing owner** — it is the
> shared tooling (resolved + archived, 4/4 done), which shipped the instruments-service `--operation reprocess-shards`
> CLI. Prefer that over a fresh one-off script if the `record_captured` path below turns out not to be enough.

- [ ] [DATA] P3. Execute the correction for the single known row
      (`date=2023-12-16, venue=BITFINEX-SPOT,     capture_status=captured, row_count=284`, target
      `data_type=instruments` — matching all 2,398 sibling BITFINEX-SPOT captured rows): write a correctly-keyed row via
      `NormalisingManifestWriter.record_captured(...)` (NOT a raw parquet overwrite — `data_type` is a row-key column,
      per `_ROW_KEY_COLUMNS`) and confirm the pre-existing blank-`data_type` row for the same `(date, venue)` is
      reconciled (superseded/removed) by the manifest consolidator rather than left as an orphaned duplicate shard.
      Re-run `cf_manifest_audit.audit()` after to confirm 0 `captured`+blank rows remain. (repo: instruments-service /
      unified-trading-library)

**Todo 2 (the 5,806 non-captured blank rows) — RESOLVED, exemption confirmed with full evidence (not venue-specific).**
Global cross-tab of `capture_status` × blank-`data_type` across the whole 84,542-row index:

| capture_status       |  typed | blank |
| -------------------- | -----: | ----: |
| captured             | 56,117 |     1 | ← the lone Todo-1 anomaly |
| empty_confirmed      | 22,517 | 4,935 |
| expected_unattempted |     31 |   856 |
| attempted_failed     |     70 |    15 |

`data_type` is populated by the writer ONLY as a byproduct of a genuine capture — non-captured rows are typed only
opportunistically (22,618 of them ARE typed, which is a completeness bonus, not evidence of a requirement) — and the
5,806 blank-non-captured rows are overwhelmingly explained by a typed `error_reason`, not a missing-type bug:
`EXPECTED_PRE_VENUE_LAUNCH` 4,883 (84%, confirmed for LIGHTER-ZKSYNC + PACIFICA-SOLANA: 484 rows each, `date` range
2022-08-23..2023-12-19, written 2026-07-14T11:24-11:38Z by a DISTINCT later batch from the main 2026-06-26 backfill — a
deliberate "this venue didn't exist yet on this historical date" placeholder, nothing to type by construction),
`expected_unattempted` (blank `error_reason`, 857 — never attempted, nothing was ever typed), `SOURCE_RETURNED_ZERO`
(52) and `UNCLASSIFIED_ADAPTER_ERROR` (15) — real attempts that found/produced nothing, also correctly untyped. This
pattern holds identically across **26 CEFI venues** (not just the 5 named in the original diagnosis) — POLYMARKET-PERP/
KALSHI-PERP/COINBASE-CDE were flagged because 100%/99.4%/98.7% of their rows happen to be non-captured (young/thin
venues), not because of venue-specific writer behavior; LIGHTER-ZKSYNC/PACIFICA-SOLANA's `captured` rows are 100% typed
(728/728, 411/411) — identical to every other venue. **Verdict: no per-venue exemption needed because there is no
per-venue gap — `data_type` blank-on-non-captured is the correct, universal, cross-cutting manifest behavior; the
`error_reason` column is the "why" signal for non-captured cells, `data_type` is reserved for what was actually typed.**
No code change, no waiver doc needed — this todo is closed by evidence.

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (4 entries).
