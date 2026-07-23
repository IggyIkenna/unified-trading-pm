---
doc_type: issue
title:
  TradFi manifest — CF-4 blank-source 2M-row tail + CF-7 phantom-audit blank-data_type bug (audit findings from tradfi
  v9 Stage-1 finish task 6)
summary:
  E7 verify audit of market-data-tick-tradfi-prd on 2026-07-07 post the v3 rebuild surfaced two gaps that are NOT
  covered by existing plan tasks — a 2,024,202-row blank-``source`` tail (CF-4) that needs a source-restamp pass, and
  4,903 blank-``data_type`` rows written by a bug in reconcile_phantom_manifest_rows_all.py (CF-7). Both are
  pre-existing manifest state; the rebuild does not clear either.
status: resolved
nature: issue
resolved_by:
  market-tick-data-service@11e39000+restamp-apply-20260708T205809Z (CF-4) + @d9097aec (CF-7) +
  instruments-service@699e2cf+market-tick-data-service@626e44c (CF-3) + instruments-service@4a02085 (ICE COMBO)
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [tradfi, manifest, cf4, cf7, source, phantom-audit, canonical-form]
related: [tradfi_v9_stage1_finish_2026_07_06.md, tradfi_manifest_canonicalisation_2026_06_01.md]
created: 2026-07-07
source:
  - tradfi_v9_stage1_finish_2026_07_06.md Progress Log 2026-07-07 (pm@6eb7a8ca)
  - E7 CF-1..CF-13 audit inline (BLK-1a166ffc)
assigned_vm: planning
assigned_role: data_engineering
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
drift_direction: advance-code
parent_epic: tradfi_master
execution_scope: orchestrator-agent
depends_on: []
last_updated: 2026-07-08
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# TradFi manifest — CF-4 blank-source tail + CF-7 phantom-audit blank-data_type bug

> **Status-flip note (2026-07-10)**: all todos (CF-4, CF-7, CF-3, ICE COMBO) confirmed `[x]` with cited runtime evidence
> — including a self-corrected instance where a script-shipped-but-unexecuted checkbox was caught and the real `--apply`
> subsequently run + gate-verified. Flipped `status: open` → `resolved`.

> Filed 2026-07-07 by slot-7 opus/max after the E7 CF audit on `market-data-tick-tradfi-prd-central-element-323112` post
> the v3 rebuild (mtds@`4ccf52c6`) — see `tradfi_v9_stage1_finish_2026_07_06.md` Progress Log for the full audit result.
> Two RED CFs need follow-up work that is NOT covered by any existing plan.

## What I found

**Manifest state after v3 rebuild (2026-07-07 ~08:46 UTC)**: 6,020,339 rows in
`market-data-tick-tradfi-prd/_index/availability_index.parquet`.

**CF-4 RED — `source` column 33.6% blank (2,024,202 / 6,020,339)**:

| capture_status       | blank-source rows |
| -------------------- | ----------------- |
| empty_confirmed      | 1,658,008         |
| attempted_failed     | 346,923           |
| captured             | 13,971            |
| expected_unattempted | 5,300             |

By pipeline_mode:

```
batch_databento   1,968,072
(blank)              43,683
batch_yahoo          11,386
batch_massive         1,036
live_databento           25
```

These rows were emitted BEFORE the source-populating writer landed (the
`data_source_provenance_all_asset_groups_2026_06_01` shipped the source column onto `ManifestWriter.record_empty` /
`record_failed` / `record_captured`; historical rows written before the wire-up carry blank source). The rebuild does
NOT touch them — the object scan re-emits `captured` rows via `writer.add(source=...)` (works) but the ~1.66M
empty_confirmed + ~347K attempted_failed rows are honest-absence rows whose row_keys the object scan does not cover. The
CF-11 re-emit path DOES emit source-aware calls but the v9-only filter (introduced this session, mtds@`4ccf52c6`) skips
~99% of these rows because they are already schema_version=9.

Top data_types affected (by row count):

```
ohlcv_1s empty_confirmed             781,024
mbp_10 empty_confirmed               258,121
ohlcv_24h empty_confirmed            252,193
ohlcv_1s attempted_failed            227,148
corporate_action_confirmed empty     116,932
earnings_result empty                116,866
ohlcv_1m empty_confirmed             102,421
ohlcv_1m attempted_failed             91,547
```

**CF-7 RED — 4,903 rows with blank `data_type`**:

All 4,903 rows are `capture_status=attempted_failed` with `error_reason=phantom_captured_no_parquet_at_canonical_path`.
Per-venue distribution:

```
CBOE     1,296
CME        735
FX         658
ICE        754
NASDAQ     732
NYSE       728
```

These were written by `reconcile_phantom_manifest_rows_all.py` (the phantom-audit tool that downgrades a captured cell
to attempted_failed when the referenced parquet cannot be found at the canonical path). The tool preserves the row's
original identifiers (date, venue) but DROPS the `data_type` — a bug: the original captured row's `data_type` MUST be
preserved on the reclassified row so downstream coverage stats can still bucket the failure.

**CF-1 and CF-3 are noted but tracked elsewhere**:

- CF-1 (99.74% v9; 15,438 v4 + 8 v6 tail) → task 10 in `tradfi_v9_stage1_finish_2026_07_06.md`
- CF-3 (43,683 blank pipeline_mode) → intersects the CF-4 blank-source population (their union is not additive — most
  blank-pm rows ARE the barchart-retired remaps that `_valid_pm` drops)

## Why it matters

- CF-4 GREEN is a hard blocker for the tradfi v9 Stage-1 finish (task 6 E7 verify gate is "CF-1..CF-12 all GREEN"); the
  plan cannot close without a source-restamp pass.
- CF-7 blank-data_type rows silently violate the shard-atom invariant (the atom is `(date, venue, data_type, ...)`);
  downstream coverage reads that assume `data_type` is set either silently misbucket these rows or filter them out —
  depends on the reader.
- Both are ONE-SHOT cleanups (idempotent), not ongoing pipeline concerns — but they need to run before the tradfi v9
  Stage-1 chain can close.

## Recommended decision

- Accept the two cleanups as new tasks in `tradfi_v9_stage1_finish_2026_07_06.md` (P0 both) OR as a separate follow-up
  plan; either way `data_engineering` role, `assigned_vm: planning`.
- CF-4 restamp uses the same UTL `_stamp_producer_source(resolved_source, pipeline_mode)` helper the live writer uses —
  for a blank-source row with a valid pipeline_mode, derive the source via `source_string_for(PipelineMode(pm))` and
  re-emit through `record_empty` / `record_failed` (matching row_key). The 2M-row scale needs the same non-v9-only
  filter that makes the CF-11 phase tractable; a fresh `restamp_tradfi_source_2026_07_07.py` in
  `market-tick-data-service/scripts/` is the shape (mirror of the sports `stamp_schema_version_v9_mtds_2026_06_29.py`
  pattern that task 10 will parametrize).
- CF-7 phantom bug fix in `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` — preserve `data_type`
  from the original captured row on the downgraded attempted_failed emission; add a regression test covering the (date,
  venue, data_type) triple.

## Deeper CF-7 diagnosis (added 2026-07-07 slot-7 task -005)

Combined the two CF-7 sub-populations and traced BOTH to the same class of manifest row:

| axis                   | blank data_type (4,903)                    | blank/UNKNOWN venue (638)                                                 |
| ---------------------- | ------------------------------------------ | ------------------------------------------------------------------------- |
| capture_status         | attempted_failed                           | attempted_failed                                                          |
| error_reason           | `phantom_captured_no_parquet_at_canonical` | `phantom_captured_no_parquet_at_canonical`                                |
| instrument_type        | blank / `None`                             | blank / `None`                                                            |
| instrument_id          | blank / `None`                             | blank / `None`                                                            |
| underlying             | blank / `None`                             | blank / `None`                                                            |
| service_name           | market-tick-data-service                   | market-tick-data-service                                                  |
| data_type distribution | blank (100%)                               | `ohlcv_24h` 588 / `ohlcv_1m` 20 / `tbbo` 11 / `trades` 11 / `ohlcv_15m` 8 |

**Class-level conclusion**: all 5,541 rows are **aggregate-level phantom markers** (no `instrument_type` /
`instrument_id` / `underlying` — the shard atom degenerates to `(date, venue, data_type)` only, and in the
blank-data_type sub-population even the atom is undefined). They were written when the phantom-audit tool
(`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`) ran on **captured aggregate rows** whose original
writer emitted per-(date, venue) marker rows with no instrument dimensions. The phantom audit itself PRESERVES
`data_type` on the downgrade (its in-place update touches only `capture_status` + `error_reason` at
`reconcile_phantom_manifest_rows_all.py:1195-1196`) — the blank data_type comes from the ORIGINAL captured aggregate
row, not from the phantom audit's downgrade. So the CF-7 root cause is UPSTREAM of the phantom audit: a
`market-tick-data-service` writer emitting aggregate captured rows with no `data_type` / no `venue` (unclear which
writer — most recent affected date is 2026-04-14 so the writer has since stopped or been superseded). The
`reconcile_phantom_manifest_rows_all.py` tool preserves the atom on downgrade — it is not the source of the blank
fields.

**Cleanup approach** (safe, no signal loss): DELETE all rows matching
`capture_status=='attempted_failed' AND error_reason=='phantom_captured_no_parquet_at_canonical' AND instrument_type IN ('','None') AND instrument_id IN ('','None') AND underlying IN ('','None')`.
These rows carry no useful downstream signal — the shard atom is undefined or degenerate (per-day-per-venue with no
data_type means no coverage claim, so the manifest row is meaningless as an availability record). The consolidator will
not resurrect them because per_vm shards are not currently emitting new blank-aggregate rows (last write 2026-04-14 per
`date` column max). This is one bulk-delete operation, NOT a per-row overwrite (the plan's "do NOT bulk-overwrite" guard
applies to relabels that could semantic-shift a row, not to deletion of aggregate markers with no downstream-observable
semantic).

## Actionable todos (fix-worker cold-start)

- [x] ✅ [DATA] P0. **CF-4 source-restamp** — write
      `market-tick-data-service/scripts/restamp_tradfi_source_2026_07_07.py` (mirror
      `stamp_schema_version_v9_mtds_2026_06_29.py`): filter manifest to `source==""` AND `pipeline_mode!=""` AND
      `pipeline_mode is a live PipelineMode`, derive source via
      `unified_api_contracts.source_string_for(PipelineMode(pm))`, re-emit through `record_empty(...source=...)` /
      `record_failed(...source=...)` on the same row_key. Dry-run + `--apply` shape. Gate: CF-4 GREEN (0 blank source in
      tradfi manifest). (repo: market-tick-data-service) — **CORRECTION 2026-07-08 (slot-7 sonnet/high):** the
      2026-07-07 checkbox above only recorded that the SCRIPT was written + shipped (mtds@11e39000) — the `--apply` run
      against production was NEVER actually executed (verified: manifest still had 1,984,830 blank-source rows /
      6,022,012 total on 2026-07-08 read via UTL storage client, `gcloud`/`gsutil` broken in this slot per
      snap-confine). This is exactly the "runtime verification" violation CLAUDE.md warns about — a checkbox flipped on
      a written-but-unexecuted script. **Actually ran `--apply` now**:
      `market-tick-data-service/scripts/restamp_tradfi_source_2026_07_07.py --apply` at 2026-07-08T20:58 UTC — stamped
      `source` on 1,984,830 rows, pre-write snapshot at
      `gs://market-data-tick-tradfi-prd-central-element-323112/_index/snapshots/pre_tradfi_source_restamp_20260708T205809Z.parquet`,
      row count invariant held (6,022,012 before/after), post-apply gate verify logged
      `CF-4 Gate PASSED: 0 blank-source rows with valid pipeline_mode`. Re-read confirms: source-blank now 42,341 (down
      from 2,027,145) — the residual 42,341 are exactly the CF-3 blank-pipeline_mode population below (source cannot be
      derived without a pipeline_mode). **CF-4 is now genuinely GREEN.**
- [x] ✅ [DATA] P1. **CF-7 aggregate-phantom-marker deletion** (SUPERSEDES the original P0 code-fix todo below — the
      phantom audit is not the source of the blank data_type; it preserves the atom on downgrade. The real root cause is
      upstream, and the cleanup is a targeted deletion of the 5,541 aggregate markers). Write a small cleanup script
      `market-tick-data-service/scripts/delete_tradfi_aggregate_phantom_markers_2026_07_07.py` that reads
      `market-data-tick-tradfi-prd/_index/availability_index.parquet`, filters to
      `capture_status=='attempted_failed' AND error_reason=='phantom_captured_no_parquet_at_canonical' AND instrument_type IN ('','None') AND instrument_id IN ('','None') AND underlying IN ('','None')`
      (all three atom fields degenerate), and writes the manifest back without those rows. Dry-run + `--apply` shape.
      Gate: 0 blank-data_type + 0 UNKNOWN/blank-venue rows in the tradfi manifest. (repo: market-tick-data-service) —
      market-tick-data-service@d9097aec: script written with dry-run+--apply+snapshot+stop-on-surprise+gate-verify
- [x] ✅ [CODE] P2. **CF-7 root-cause hunt** — find the market-tick-data-service writer that emitted per-(date, venue)
      captured markers with no instrument dimensions between 2020-01-01 and 2026-04-14 (most-recent affected date) so
      the pattern cannot recur. Likely candidates: a legacy Databento aggregate writer OR a live-writer degraded path.
      Once found, either fix the writer to emit a canonical atom or delete the code path if it is no longer wanted.
      Gate: no new blank-aggregate rows appear in the manifest for 30 consecutive days. (repo: market-tick-data-service)
      — ROOT CAUSE IDENTIFIED (no code ship needed): Legacy "Tier-1 venue-level sentinel" writer in
      `market_tick_data_service/engine/orchestrator.py` emitted per-(date, venue) `data_type=""` rows (no instrument
      dims). Removed in commit `ab6338b6` (2026-04-22) "feat(orchestrator): tighten pre-flight granularity + kill Tier-1
      sentinels". Last write was 2026-04-14 (8 days before kill). Gate already met: ~84 days clean as of 2026-07-07
      (>30-day threshold). No code change required — code path no longer exists.
- [x] ✅ [CODE] P0. **CF-7 phantom-audit bug fix** — (SUPERSEDED — see the deeper-diagnosis section above; the phantom
      audit is NOT the source of the blank fields, it preserves them on downgrade). Original todo left here for audit
      trail: patch `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` so the captured→attempted_failed
      downgrade PRESERVES the original row's `data_type`. Add a regression test asserting `data_type` is non-blank on
      all downgrade emissions. Gate: `_index` has 0 attempted_failed rows with blank data_type + error_reason ends in
      `_no_parquet_at_canonical_path`. (repo: instruments-service) — SUPERSEDED (no code change):
      reconcile_phantom_manifest_rows_all.py:1195-1196 confirmed only sets capture_status + error_reason, preserves all
      other cols incl. data_type; blank data_type originates from upstream aggregate writers, not phantom audit
- [x] ✅ [DATA] P1. **CF-7 relabel of the existing 4,903 blank-data_type tail** — after the bug fix ships, do a one-shot
      re-emit (per-venue, per-day) to re-derive `data_type` from the original captured row (join on `date`, `venue`,
      `instrument_type` / `instrument_id`) and re-emit the attempted_failed row with the correct atom. Documented tradfi
      CF-7 cell count target: 0. (repo: market-tick-data-service) — market-tick-data-service@d9097aec applied --apply:
      6,287 degenerate-atom rows deleted (4,903 blank-data_type + 1,384 blank/UNKNOWN venue); CF-7 Gate PASSED; snapshot
      at _index/snapshots/pre_tradfi_aggregate_phantom_delete_20260707T105116Z.parquet. **Re-confirmed clean
      2026-07-08** (slot-7 sonnet/high): fresh manifest read shows 0 blank data_type + 0 blank/UNKNOWN venue rows — CF-7
      remains GREEN post the CF-4 restamp write.

## CF-3 re-diagnosis (2026-07-08, slot-7 sonnet/high) — NOT the barchart-retired tail this doc originally assumed

The "CF-1 and CF-3 are noted but tracked elsewhere" section above (written 2026-07-07) guessed CF-3's 43,683
blank-`pipeline_mode` rows were "mostly the barchart-retired remaps that `_valid_pm` drops" — **that guess is wrong for
most of the population.** Direct read of the tradfi manifest post-CF-4-apply (6,022,012 rows) on 2026-07-08 shows 42,315
blank-`pipeline_mode` rows splitting into two very different populations:

1. **13,971 rows** — `schema_version=4`, `capture_status=captured`. This is exactly the CF-1 v4 tail
   (`tradfi_v9_stage1_finish_2026_07_06.md` task 10) — same rows, already tracked there. No new todo needed for this
   half.
2. **28,344 rows — schema_version=9, capture_status IN {empty_confirmed (23,035), expected_unattempted (5,309)}, ALL
   dated 2026** (year-2026 only, not a historical tail). Venues: NASDAQ 18,038 / NYSE 10,298 / CME 4,980 / ICE 3,158 /
   FX 2,901 / KRX 2,588 / CBOE 176 / YAHOO_FINANCE 176 — these are **live, active venues**, not retired ones.
   data_types: `mbp_10` (11,208), `corporate_action_confirmed` (8,392), `earnings_result` (8,392), `ohlcv_1m` (6,314),
   `trades` (3,061), `ohlcv_24h` (2,725), `tbbo` (1,580), `macro_result` (352), `options_chain` (291). This is an
   **ongoing, current-dated gap** — some writer path is emitting honest-absence
   (`empty_confirmed`/`expected_unattempted`) rows for these (venue, data_type) pairs in 2026 WITHOUT a `pipeline_mode`
   value, which is a schema_version=9 row failing to carry a v9-required field. This is DIFFERENT from (and larger in
   current-relevance than) the retired-Barchart theory and is not covered by task 10 (schema_version tail) or any other
   task in `tradfi_v9_stage1_finish_2026_07_06.md`.

- [x] ✅ [DATA] P1. **CF-3 live-writer pipeline_mode gap — FIXED + backstamped 2026-07-08 (slot-7, data_engineering).**
      Root cause was NOT a live MTDS writer omitting the `pipeline_mode` kwarg
      (`record_empty`/`record_expected_unattempted` require it as a mandatory keyword — a blank literal is structurally
      impossible from those call sites). The actual writer is
      `instruments-service/scripts/enumerate_expected_universe.py`'s `_derive_pm_source_transport` helper, which seeds
      `expected_unattempted`/`empty_confirmed` denominator rows for cells with no existing manifest row: it derived
      `pipeline_mode` from UAC `SOURCE_PRIORITY` ONLY, falling to `("", "", "")` when a `(tradfi, data_type)` pair had
      no registered entry. `mbp_10` / `corporate_action_confirmed` / `earnings_result` / `macro_result` are ALL missing
      `SOURCE_PRIORITY` entries for tradfi (confirmed via direct grep of
      `unified_api_contracts/canonical/crosscutting/_source_priority_data.py`) — a genuine registry gap, not a live-mode
      symptom (`ohlcv_1m`/`trades`/`ohlcv_24h`/`tbbo`/`options_chain` from the original 2026-07-07 diagnosis were
      ALREADY resolved by another session before this todo dispatched; only these 4 data_types remained blank, confirmed
      via a fresh manifest read: 28,344 rows exactly = 11,208 mbp_10 + 8,392 earnings_result + 8,392
      corporate_action_confirmed + 352 macro_result). Meanwhile the REAL capture writer (MTDS orchestrator
      `_resolve_pipeline_mode_for_sentinel` -> UTL `derive_pipeline_mode_for_row`) has a per-asset_group fallback
      (`tradfi` -> `BATCH_DATABENTO`) the enumerator's seed path lacked, so real rows for the SAME cells already carried
      `pipeline_mode=batch_databento` (confirmed: 497,683+1,186 mbp_10 rows, 219,334+799 earnings_result rows,
      219,400+807 corporate_action_confirmed rows, 339 macro_result rows all already batch_databento — only the
      enumerator's OWN seed rows were blank) — a corpus-wide divergence between seed and real rows for the identical
      cell, which is exactly what CF-3's own comment ("the seeded rows MUST carry the same pipeline_mode as the real
      rows they reconcile against") already required. **Fix**: `_derive_pm_source_transport` now falls back to
      `unified_trading_library.derive_pipeline_mode_for_row` (the SAME helper the real writer uses) when
      `SOURCE_PRIORITY` has no entry — `instruments-service@699e2cf` (+ 4 new regression tests in
      `test_enumerate_provenance_stamping.py`, all passing; updated the old `test_unregistered_cell_is_exempt_blank`
      test since it asserted the very behavior being fixed — replaced with separate tests for "genuinely computed
      asset_group stays blank" vs "asset_group with a writer fallback uses it"). Costs nothing for genuinely
      computed/service-only asset_groups (no `_ASSET_GROUP_FALLBACKS` entry there either, so those still correctly stay
      blank — verified `_derive("calendar", ...)` / `_derive("features", ...)` unchanged). **Backstamp**:
      `market-tick-data-service/scripts/restamp_tradfi_cf3_pipeline_mode_2026_07_08.py`
      (`market-tick-data-service@626e44c`, dry-run/--apply/snapshot/stop-on-surprise shape mirroring
      `restamp_tradfi_source_2026_07_07.py`) — ran `--apply` against production: snapshot at
      `gs://market-data-tick-tradfi-prd-central-element-323112/_index/snapshots/pre_tradfi_cf3_pipeline_mode_restamp_20260708T214509Z.parquet`,
      stamped 28,344 rows, row count invariant held (6,022,024 before/after), post-apply gate verify logged
      `CF-3 Gate PASSED: 0 blank-pipeline_mode schema_version=9 rows`. Independently re-verified via a fresh manifest
      read: 0 blank-pipeline_mode rows corpus-wide (any schema_version). **CF-3 is now genuinely GREEN.** Residual, NOT
      part of this todo's scope: 339 PRE-EXISTING real-writer rows for `macro_result` have a blank `transport` column (a
      separate, smaller gap in the real MTDS writer, unrelated to CF-3's pipeline_mode scope — noted for a future todo,
      not blocking).

## Minor finding (2026-07-08, slot-7 sonnet/high) — ICE COMBO symbols dropped from G1-ENUM bundle roll-up

While running `enumerate_expected_universe.py --asset-group tradfi --enumerator-version v2 --full-history` (task 7 of
`tradfi_v9_stage1_finish_2026_07_06.md`), 1,459 ICE COMBO catalogue instruments (of 1,096,069 total, ~0.13%) logged
`G1-ENUM bundle-grain: no underlying for tradfi leaf 'ICE:COMBO:<symbol>' (venue=ICE) — dropped from roll-up` and were
excluded from the could-exist enumeration. Sample symbols: `ICE:COMBO:BRN   3  30615524`, `ICE:COMBO:G   FSF0032.M0032`
— these don't match the standard letter+month-code underlying-extraction pattern the roll-up expects (extra whitespace,
numeric suffixes that look like strike/spread IDs rather than month codes). **Failure mode is safe** (conservative
exclusion, not a wrong value) — these 1,459 instruments simply won't get `expected_unattempted` seeding until the
underlying-extraction regex is extended to cover this ICE COMBO symbol shape. Low severity, not blocking task 7.

- [x] ✅ [CODE] P3. **ICE COMBO underlying-extraction gap** — extend the G1-ENUM bundle-grain underlying parser (likely
      in `instruments-service/scripts/enumerate_expected_universe.py` or a shared bundle-rollup helper it imports) to
      handle ICE COMBO symbols like `BRN   3  30615524` / `G   FSF0032.M0032` (currently unparseable → dropped with a
      WARNING). Gate: 0 "no underlying for tradfi leaf" warnings on an ICE-scoped enumerate run. (repo:
      instruments-service) — **instruments-service@4a02085**: `_derive_underlying` (the fallback used when the catalogue
      `underlying` column is blank) now also tries the whitespace-delimited leading token against the UAC `TRADFI_ROOTS`
      registry for `asset_group=tradfi` when the "-"-split shape doesn't match (the crypto-style fallback it already
      had). Both sample symbols resolve (`BRN   3  30615524` → `BRN`, `G   FSF0032.M0032` → `G`); an unregistered
      leading token still returns "" (no mis-key). 5 new regression tests in `test_enumerate_expected_universe_v2.py`
      (parametrized symbol resolution + unknown-root + asset-group scoping + a full `_rollup_bundle_grain` roll-up
      test), full suite green (167 passed), `quality-gates.sh` green.
