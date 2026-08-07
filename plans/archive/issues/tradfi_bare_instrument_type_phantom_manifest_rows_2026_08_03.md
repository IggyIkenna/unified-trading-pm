---
doc_type: issue
title:
  TradFi bare instrument_type (UD/OPTION/FUTURE/COMBO) phantom manifest rows — one write batch, no backing GCS objects,
  explains the mtds_available_at_cross_asset_backfill "genuine ~16% gap"
summary: >-
  Investigating the still-open tradfi lane of mtds_available_at_cross_asset_backfill_2026_07_13.md's Apply todo
  (pre-2023-04 ohlcv_1s/ohlcv_1m available_at fill), found the remaining unfilled population is dominated by phantom
  manifest rows — instrument_type in {UD, OPTION, FUTURE, COMBO} (bare, no instrument_id, no underlying), all written in
  a single ~9-second batch (2026-07-27T16:46:31-40Z), with NO corresponding real GCS object (directly confirmed for
  UD/OPTION/FUTURE via gcs_describe/list at sampled dates+venue). UD alone was already known + quarantined
  (unified-api-contracts market_data_categories.py TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE, root cause not
  confirmed); this extends that finding to OPTION/FUTURE/COMBO (same batch, same signature) and also found that
  frozenset is NOT actually wired into deployment-api's _ACCEPTED_EXCEPTIONS despite its own comment claiming it is.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, deployment-api]
scope: [engineer, admin]
tags: [tradfi, manifest, phantom-rows, data-correctness, available_at, instrument_type, delete-safety]
related:
  [
    /plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-03
author: unknown
last_updated: 2026-08-03
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by: market-data-processing-service@b039ec2f (writer guard) + market-tick-data-service (full purge, 2026-08-05)
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Found while working mtds_available_at_cross_asset_backfill_2026_07_13.md's tradfi Apply todo (task
  mtds_available_at_cross_asset_backfill-008), 2026-08-03, slot 14."
context_scope:
  [
    /plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    deployment-api/deployment_api/routes/data_status/_distinct_values.py,
    market-data-processing-service/market_data_processing_service/app/core/canonical_writer.py,
  ]
---

# TradFi bare instrument_type phantom manifest rows (UD/OPTION/FUTURE/COMBO)

## What I found

Re-ran the tradfi `available_at` fill-rate check for pre-2023-04-10 `ohlcv_1s`/`ohlcv_1m` captured rows against the
live-freshly-consolidated manifest
(`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`, consolidated
2026-08-03T00:34:07Z). Raw fill rate: 88.6%. Folded by `UPPER(instrument_type)` (the known C2a casing-migration-pending
workaround this doc's parent plan already established): 91.9% (8,377/9,117 distinct
`(date, venue, data_type, UPPER(instrument_type))` cells covered).

**Broke down the 740 still-unfilled folded keys** — dominated by 4 `instrument_type` values, NOT `ohlcv_1s`/`ohlcv_1m`
data proper:

```
UD              372 folded keys (2,232 raw rows)
OPTION          205 folded keys (1,230 raw rows)
COMBO            73 folded keys (raw rows include real underlying-bundle rows AND phantom rows — see below)
FUTURE           59 folded keys (raw rows include real per-instrument/bundle rows AND phantom rows)
OPTIONS_CHAIN    31 folded keys (real, recently-written, see § "Not phantom" below)
```

**All 4 of UD/OPTION/FUTURE/COMBO's fully-unfilled rows share one exact signature**: `instrument_id IS NULL`,
`underlying IS NULL`, `written_at` in the identical 9-second window **2026-07-27T16:46:31.986Z ..
2026-07-27T16:46:40.441Z** — clearly one batch job/writer run, not organic capture traffic (8,556 such rows total in
just this pre-2023-04/ohlcv_1s+1m slice; the true corpus-wide count is unknown — not checked, see § Recommended next
steps).

**Confirmed via direct GCS checks these are phantom (no backing object), not just unfilled**:

- `instrument_type=UD` was already documented as unresolved residue (see § "Prior art" below) — this session reconfirms
  it, no new check needed.
- `instrument_type=future` / `instrument_type=option` (bare, lowercase per the real hive-path convention): checked
  `gs://market-data-tick-tradfi-prd-central-element-323112/raw_tick_data/by_date/day=2020-03-31/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/`
  — only `instrument_type=combo/`, `instrument_type=futures_chain/`, `instrument_type=options_chain/` exist. **No bare
  `instrument_type=future/` or `instrument_type=option/` prefix exists at all.** Same result at 2 more sampled dates
  (structure confirmed identical for the whole 2019-2023 range these phantom rows span).
- `instrument_type=combo` (bare, blank underlying) rows: sampled `date=2020-01-05/CME/ohlcv_1m` — every raw row for that
  folded key has `underlying=None`, matching the phantom signature (a REAL combo row for the same day, e.g.
  `underlying=WTI-BZ`, DOES exist with a real backing object and IS filled — real and phantom combo rows coexist under
  the same `instrument_type=combo` label, distinguished by whether `underlying` is populated).

**Excluding all rows matching the phantom signature (written_at in that 9s window AND `instrument_id`+`underlying` both
null) from the population and re-folding**: real folded keys drop from 9,117 to 8,408; **real fill rate rises to 99.63%
(8,377/8,408)**. The only remaining unfilled real folded keys are all `instrument_type=OPTIONS_CHAIN` (31 keys) — see
next section.

## Not phantom: OPTIONS_CHAIN's 31 remaining unfilled keys

Spot-checked one (`date=2020-07-27, CME, ohlcv_1m, underlying=SP500, quote=USD, margin=linear`): the manifest row's
`written_at` is `2026-08-02T23:22:43Z` and the real GCS object
(`.../instrument_type=options_chain/data_type=ohlcv_1m/underlying=SP500/quote=USD/margin=linear/ticks.parquet`) has
`time_created=2026-08-02T23:22:42Z` — essentially the same instant. This looks like a genuinely real, very recently
(possibly still actively) written shard, not a stale gap — plausibly a live/in-progress options_chain backfill still
landing objects marginally ahead of the manifest read. Not investigated further (out of scope for this finding; tiny
population, 31/8,408 = 0.4%).

## Prior art (why this isn't a fresh discovery, just an extension of one)

`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:806-819` already documents
`instrument_type=UD` as `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE` — "3,607 captured rows, venue=CME, spanning
2021-2026 in disjoint yearly chunks. Investigated twice: no writer found stamping bare instrument_type='UD' ... GCS
checked at 3 dates found no instrument_type=UD/ or instrument_type=ud/ path. Quarantined per the operator's standing
classify-or-quarantine precedent (UNKNOWN, 2026-07-18) — root cause NOT fully confirmed." This session's finding:
**OPTION/FUTURE/COMBO-bare share the exact same signature (same 9-second write batch, same blank id+underlying shape,
same GCS non-existence) and should very likely be added to the same quarantine class** — this is one root cause across 4
instrument_type labels, not 4 separate issues.

**Also found while checking how the UD residue set is consumed**: its own comment claims "consumed by
`_ACCEPTED_EXCEPTIONS[("instrument_types", "tradfi")]`" but
`deployment-api/deployment_api/routes/data_status/ _distinct_values.py:200-206`'s actual `_ACCEPTED_EXCEPTIONS` dict
maps `("instrument_types", "tradfi")` to `CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES`
(`{"options_chain", "futures_chain"}` only) — `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE` is defined + exported
but never actually wired in. The census/data-status surface is therefore NOT currently silencing UD as its own comment
claims.

## Why it matters

`mtds_available_at_cross_asset_backfill_2026_07_13.md`'s tradfi "Apply" todo has been re-run and re-diagnosed across at
least 4 sessions (2026-07-14, 2026-08-02 x3) chasing a "genuine ~16% gap" that turned out to be >95% phantom manifest
bookkeeping the rebuild script structurally cannot fill (no real GCS object exists to read a `time_created` from) — the
same "aggregate metric dominated by out-of-scope rows" trap this same plan's prediction lane hit and resolved in its own
session #21 (`mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md`). Flipping the plan's Apply todo now
against the corrected 99.63% real-data metric, citing this issue doc.

Separately, these are `capture_status=captured` manifest rows with **no real backing data** — the same defect class as
the already-resolved "4,991 phantom captured FIXTURE_EVENTS manifest rows" (sports) — a genuine, if small (8,556 rows in
this one slice), manifest-correctness problem independent of the `available_at` question.

## Corpus-wide scope (2026-08-03, slot 2)

Ran a bounded, column-pruned + predicate-pushdown read of the live-consolidated `_index/availability_index.parquet`
(single object, not a new GCS walk) filtered to the exact phantom signature (`written_at` in
`2026-07-27T16:46:31Z..2026-07-27T16:46:41Z` AND `instrument_id IS NULL` AND `underlying IS NULL`). Shipped as
`market-tick-data-service/scripts/audit_tradfi_phantom_batch_corpus_wide_scope_2026_08_03.py@125ec228`.

**Corpus-wide total: 12,582 rows** — larger than the 8,556 this doc originally found, because the same batch also
touched `trades` and `ohlcv_15m` (not just `ohlcv_1s`/`ohlcv_1m`) and 728 rows post-2023-04-10 (the doc's original slice
was pre-2023-04-10 only). Sanity-check against the doc's own number: re-applying the exact original slice filter
(pre-2023-04-10, `data_type in {ohlcv_1s, ohlcv_1m}`) to this same read returns 8,550 rows — within 6 of the documented
8,556 (immaterial, consistent with the same batch/signature).

By `instrument_type` (case-folded, C2a convention):

```
FUTURE      4560
COMBO       4190   (stored lowercase "combo" — same C2a casing-migration-pending note as elsewhere)
UD          2354
OPTION      1346
EQUITY       122   <- NOT previously documented as part of this signature
ETF            6   <- NOT previously documented as part of this signature
INDEX          4   <- NOT previously documented as part of this signature
```

**New finding beyond the original scope**: `EQUITY`/`ETF`/`INDEX` (132 rows total) share the exact same phantom
signature (same 9-second write batch, same null instrument_id+underlying) but were NOT in this doc's original
UD/OPTION/FUTURE/COMBO list — the original investigation's pre-2023-04 ohlcv_1s/1m slice happened not to surface them.
Todo 3 below (extending `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE`) should add these 3 alongside
OPTION/FUTURE/COMBO, not just the original 3.

By `data_type`: `ohlcv_1m` 9,054 · `trades` 3,514 · `ohlcv_15m` 14. By venue: `CME` 12,083 · `ICE` 341 · `NASDAQ` 68 ·
`NYSE` 60 · `CBOE` 30. Date range 2020-01-01..2024-01-16 (613 distinct dates). `capture_status`=`captured` and
`pipeline_mode`=`batch_databento` for all 12,582 rows (100%) — consistent with one writer/batch job, not organic
per-venue capture. `written_at` has 12,582 distinct values inside the 9-second window (one row per timestamp, consistent
with a tight per-row write loop, not a bulk single-timestamp write).

**Additional correctness concern surfaced (not previously flagged)**: these 12,582 phantom rows collectively carry
`row_count` = **2,762,371,174** (sum of the manifest rows' own `row_count` field) — i.e. the manifest's bookkeeping
falsely claims ~2.76 billion rows of tick data captured with zero backing GCS objects. This inflates any row-count-based
coverage/completeness metric that trusts the manifest's `row_count` column without cross-checking against real GCS
objects. Flagging for whoever picks up todo 3/4 — worth a quick check whether any dashboard/report sums `row_count`
directly.

## Root-cause diagnosis (2026-08-03, slot 8)

**Different angle from the twice-failed UD-only search**: instead of searching by `instrument_type`/GCS path (the
approach that failed twice for UD alone — see § "Prior art"), correlated the exact `written_at` timestamp cluster
(`2026-07-27T16:46:31.986Z..2026-07-27T16:46:40.441Z`) against Cloud Logging, GCS backup-snapshot naming, and finally
the manifest's own `service_name`/`job_id`/`source` provenance columns
(`unified_trading_library/manifest_writer/ _writer_io.py` confirms `service_name` is a real, populated column — the same
column the related `tradfi_casing_100pct_redrift_2026_07_27.md` issue used to positively identify 3 other tradfi writer
bypasses via a "per-`service_name` provenance read" of this same manifest object).

**Ruled OUT (with evidence, so a future session doesn't re-tread these)**:

- `migrate_tradfi_manifest_itype_semantic_relabel_2026_07_27.py` (same-day script, computes/restamps `instrument_type`)
  — **code-proof ruled out**: `canonicalize_raw_tradfi_id()` returns `status="NULL_OR_EMPTY"` for any blank/None `raw`
  id (`unified_api_contracts/internal/reference/tradfi_id_canonicalizer.py:296-302`), and the relabel script only
  mutates rows where the classifier returns a `_RELABEL_STATUSES` status (`OK`/`ALREADY_CANONICAL`/`QUARANTINE_COMBO`) —
  `NULL_OR_EMPTY` is never in that set, so a row with `instrument_id IS NULL` can never be touched by this script. It
  also stamps ONE shared `now_iso` per run onto every changed row, not a per-row distinct timestamp — doesn't match our
  12,582+ DISTINCT `written_at` values either.
- The scheduled `uts-prod-market-tick-data-service-tradfi-databento-t1-recon` Cloud Run job — its only 2026-07-27
  execution was at `00:37:38Z` (its normal `35 0 * * *` schedule), nowhere near 16:46.
- `rewrite_tradfi_chain_bundle_content_id_2026_07-25.py --apply` (the chain-bundle content migration launched
  2026-07-27) — ran `04:17:04Z`→gate-closed `06:13:25Z`, hours before 16:46.
- `correct_tradfi_recovery_quarantine_manifest_2026_07_27.py` — only flips `capture_status` on already-existing
  combo/futures_chain/options_chain rows (never creates rows, never touches `instrument_id`/`underlying`); its own
  `_index/backups/availability_index.pre_recovery_quarantine_correction_20260727T210054Z.parquet` snapshot is
  timestamped 21:00:54Z, ~4h after the batch.
- `rebuild_tradfi_manifest.py` at current HEAD — traced every `parse_tradfi_path()` branch; none produces a row with
  BOTH `instrument_id` AND `underlying` blank for a non-bundle-grain type (only `futures_chain`/`options_chain` legally
  get blank `instrument_id`, and those always carry a non-blank `underlying`).
- No `_index/backups/*` or `_index/snapshots/*` object exists anywhere near `2026-07-27T16:4[5-7]` — rules out every
  known whole-index CAS-migration script (they all snapshot-before-write by convention), meaning the writer used the
  ordinary per-shard `ManifestWriter.record_captured()` path, not a one-off migration script.

**CONFIRMED — writer service** (bounded, column-pruned, single-object live read of `_index/availability_index.parquet`,
filtered to the exact phantom signature — 13,923 matching rows as of this live read, vs. 12,582 in the original
2026-08-03 corpus-wide scope; the corpus has grown since, same signature):

```
service_name: market-data-processing-service   (13,923/13,923 — 100%)
source:       databento                        (13,923/13,923 — 100%)
job_id:       "" (blank, all rows)
capture_status: captured                        (13,923/13,923 — 100%)
```

This directly contradicts the assumption implicit in this doc's own original todo wording ("check
market-tick-data-service run.log") — **the writer is market-data-processing-service (MDPS), not MTDS.** MDPS is also
independently confirmed (via the sibling `tradfi_casing_100pct_redrift_2026_07_27.md` issue, same-day, same corpus) as a
tradfi manifest writer with a DIFFERENT casing defect (`build_continuous_engine.py` stamping lowercase
`continuous_future`) — this is a second, distinct MDPS tradfi-writer defect, not the same one.

**CONFIRMED — code mechanism**
(`market-data-processing-service/market_data_processing_service/app/core/ canonical_writer.py::write_candle_parquet`,
lines ~372-390):

```python
row_key: dict[str, object] = {
    ...
    "underlying": (underlying or "").upper(),   # falsy underlying -> ""
}
# Shard-atom discipline (hard_schema_enforcement Phase 4): include
# `instrument_id` in the row_key ONLY for per-instrument shards. An
# AGGREGATED venue/underlying-level candle ... is NOT a per-instrument
# shard -- it arrives with an empty `instrument_id`. ... OMITTING the key
# is the contract for a non-per-instrument shard.
if instrument_id:
    row_key["instrument_id"] = instrument_id
```

This is the ONLY code path found anywhere in the corpus that can emit a `record_captured` manifest row with BOTH
`instrument_id` and `underlying` simultaneously blank for a non-permanently-bundle-grain `instrument_type` — it happens
whenever a caller invokes this "aggregated" (non-per-instrument) write shape with `instrument_id=""` AND
`underlying=""`/`None` at the same time, which by the code's own comment is meant for a genuine venue/underlying-level
rollup (e.g. tradfi 15m/24h stitched from 1m), but our phantom population is dominated by `data_type=ohlcv_1m`
(9,912/13,923) and `trades` (3,997) — the BASE data_types, not an aggregated 15m/24h rollup — and spans
`instrument_type` values (`UD`, `EQUITY`, `ETF`, `INDEX`) that have no legitimate "chain/underlying aggregation" concept
at all. This strongly suggests the UPSTREAM caller is feeding a bad/unfiltered `instrument_type` (most likely sourced
from the manifest's OWN already-corrupted distinct-value vocabulary, e.g. re-ingesting the `UD` residue) into this
aggregated-write path rather than a genuine per-instrument or genuine-rollup shard.

**NOT fully traced — the exact upstream caller/trigger.** `write_candle_parquet` is invoked from
`candle_write_mixin.py::_upload_candles_to_gcs` and `io/writer.py`; the actual per-cell dispatch loop that decided to
call it with `instrument_type=UD/EQUITY/ETF/INDEX/OPTION/FUTURE/combo` + blank id + blank underlying, specifically at
`2026-07-27T16:46:31-40Z`, was not traced further (would need either MDPS's own execution/stdout logs from that run —
not captured in the Cloud Run audit trail checked here, which only records job start/stop, not stdout — or a deeper
static trace of every `batch_workers.py`/orchestrator call site that supplies `instrument_id`/`underlying` to the
candle-write path). Flagging as the honest boundary of this session's investigation rather than guessing further.

**Recommendation for todo 3**: given the writer/mechanism are now confirmed (not "root cause remains elusive" in the
weakest sense — we know WHICH service and WHICH code site, just not the precise per-cell trigger), todo 3's quarantine
extension (adding OPTION/FUTURE/COMBO/EQUITY/ETF/INDEX to `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE`) can
proceed on its own merits — these rows have zero backing GCS data regardless of exactly which upstream call triggered
the write. A SEPARATE, smaller follow-up (not this todo's scope) would be pinning the exact MDPS caller so the write
path can be hardened to refuse `instrument_type` values with no underlying/chain concept.

## Recommended next steps

- [x] [DATA] P2. Determine the FULL corpus-wide scope of this phantom signature (written_at in
      `2026-07-27T16:46:31Z..2026-07-27T16:46:41Z` AND `instrument_id IS NULL` AND `underlying IS NULL`) — this session
      only checked the pre-2023-04 `ohlcv_1s`/`ohlcv_1m` slice (8,556 rows); the same 9-second batch likely touched
      other data_types/date ranges too. Read the manifest with this filter directly (bounded read, already have the
      parquet locally cached from this session if still fresh) — do not re-derive via a new GCS walk. (repo:
      market-tick-data-service) — ✅ 2026-08-03, slot 2: 12,582 rows corpus-wide (see § "Corpus-wide scope" above) —
      market-tick-data-service@125ec228
- [x] ✅ [SCRIPT] P2. **ROOT-CAUSED 2026-08-03 (slot 8) — writer SERVICE + code MECHANISM confirmed; exact upstream
      trigger not fully traced, see caveat below.** market-tick-data-service@(no code change — see § "Root-cause
      diagnosis" below).
- [x] ⚠️ [DATA] P2. Once root-caused (or if root-cause remains elusive after the above), extend
      `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`'s
      `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE` frozenset to add `"OPTION"`, `"FUTURE"`, `"COMBO"`,
      `"EQUITY"`, `"ETF"`, `"INDEX"` alongside the existing `"UD"` (all 6 confirmed same evidenced phantom signature —
      the 3 added beyond the doc's original OPTION/FUTURE/COMBO list came out of the corpus-wide scope pass above) — OR,
      if by then the operator has ruled these should be deleted (delete-safety protocol, since they carry zero real data
      and a false `capture_status=captured` claim) rather than quarantined, do that instead. Do not delete manifest rows
      without a fresh delete-safety 5-part-proof pass regardless of how confident this doc's evidence looks. (repo:
      unified-api-contracts) — ✅ 2026-08-03, slot 9: `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE` extended to
      all 6 values (quarantine, not delete) — unified-api-contracts@d1495b35. **⚠️ REVERTED 2026-08-04 (operator live
      regression report — deployment-ui's distinct-values panel stopped showing `FUTURE`/`OPTION` for tradfi at all)**:
      `_ACCEPTED_EXCEPTIONS` filters by raw VALUE across the whole axis, not per-row — quarantining the string
      `"OPTION"` hid EVERY row with `instrument_type=OPTION` from the panel, including the millions of legitimate
      captured rows, not just the 13,923 phantom ones. Unlike `UD` (whose entire population IS the residue), these 6 are
      real, heavily-populated `InstrumentType` enum members — quarantining the value was the wrong tool for a row-level
      defect. Reverted to `{"UD"}` only via `unified-api-contracts@86a35fdb`. The 13,923 phantom rows themselves are
      UNCHANGED by this revert (still `capture_status=captured` with zero backing GCS object) — see new todo below for
      the row-level fix this should have been from the start.
- [x] ✅ [CODE] P3. **Already fixed — citation flip only (verified 2026-08-04).**
      `_ACCEPTED_EXCEPTIONS[("instrument_types",     "tradfi")]` in
      `deployment-api/deployment_api/routes/data_status/_distinct_values.py` (lines 225-227) already ORs in
      `TRADFI_INSTRUMENT_TYPE_ACCEPTED_UNRESOLVED_RESIDUE` alongside
      `CHAIN_BUNDLE_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES` — landed by `deployment-api@7988451` ("fix(data-status):
      land 6 accepted-exception entries for sports/tradfi distinct-values census (recovered 2026-07-30 WIP)",
      2026-08-03), independently of this doc. Verified live on `origin/live-defi-rollout`, working tree clean. No code
      change needed — this todo's own diagnosis (the wiring gap) was already closed by unrelated work before this
      session found it. (repo: deployment-api)
- [x] ✅ [DATA] P2. **NEW 2026-08-04, FULLY CLOSED 2026-08-05.** Fix the phantom rows (venue∈{CME,ICE,NASDAQ,NYSE,CBOE},
      instrument_type∈{UD,OPTION,FUTURE,COMBO,EQUITY,ETF,INDEX}, `instrument_id IS NULL AND underlying IS NULL`,
      `capture_status=captured`) at the ROW level — a delete-safety-gated manifest CAS write scoped to this exact
      signature, not an axis-value quarantine (which the doc above's REVERTED entry shows breaks the distinct-values
      panel for the axis's legitimate population). **Two purges were needed, not one**: (1)
      `market-tick-data-service@6c797a14` (2026-08-04) purged 9,440 rows scoped to the ORIGINAL doc's `written_at`
      window (`2026-07-27T16:46:31Z..41Z`) — but a fresh live re-read 2026-08-05 found the SAME signature had
      **recurred** (16,992 rows, a NEW dominant batch of 6,528 COMBO rows written `2026-08-04T08:51:36Z` — 21 hours
      AFTER that purge ran), proving the writer bug itself was never fixed, only its symptom cleaned up once. (2)
      Root-caused + FIXED the writer: `market-data-processing-service@b039ec2f` adds a guard in `write_candle_parquet`
      that REFUSES (raises + records `attempted_failed`, per-shard-isolated) an aggregated blank-id+blank-underlying
      write for these 7 non-aggregable instrument_types, converting future occurrences into a traceable failure instead
      of a silent phantom `capture_status=captured` row. Regression test added
      (`test_write_candle_parquet_refuses_phantom_aggregated_write_for_non_aggregable_type`); confirmed the existing
      legitimate-aggregate test (`underlying="MES"`, a real venue rollup) is unaffected. (3) Re-purged the full,
      unscoped population: `market-tick-data-service` (2026-08-05) — 16,992 rows removed (COMBO 6,528 / EQUITY 4,528 /
      FUTURE 4,041 / UD 1,099 / OPTION 652 / INDEX 96 / ETF 48; falsely claimed 2,243,619,013 rows of `row_count`),
      snapshot at `_index/backups/availability_index.pre_phantom_instrument_type_full_purge_20260805T164008Z.parquet`, 2
      CAS attempts (1 safely rejected by concurrent writer activity, 2nd succeeded), fresh post-purge re-read confirms 0
      phantom rows remain. Soft-delete retention 604800s confirmed fresh both purges. (repo: market-tick-data-service,
      market-data-processing-service)

## Progress Log

- **2026-08-03** — Filed while working `mtds_available_at_cross_asset_backfill_2026_07_13.md` task
  `mtds_available_at_cross_asset_backfill-008` (data_engineering, slot 14). Full evidence above.
- **context-scout 2026-08-03**: populated context_scope (5 entries).
- **2026-08-03 (slot 2, data_engineering)**: closed todo 1 — corpus-wide scope determined via bounded single-object
  read, 12,582 phantom rows total (vs. 8,556 in the original slice), found 3 new instrument_type labels
  (EQUITY/ETF/INDEX) and a ~2.76B row_count over-claim. Full breakdown in § "Corpus-wide scope" above. Shipped
  `market-tick-data-service/scripts/audit_tradfi_phantom_batch_corpus_wide_scope_2026_08_03.py@125ec228`. Updated todos
  2-3's wording to reflect the wider scope. Todos 2-4 remain open for a future session.
- **2026-08-03 (slot 8, data_engineering)**: closed todo 2 — root-caused the writer SERVICE
  (`market-data-processing-service`) + code MECHANISM (`canonical_writer.py::write_candle_parquet`'s row_key
  construction) via a live `service_name`/`job_id`/`source` provenance read of the manifest, a genuinely different angle
  from the twice-failed instrument_type/GCS-path search. Full diagnosis in § "Root-cause diagnosis" above, including 5
  ruled-out candidates with evidence. **Side finding, not this todo's scope, flagging for awareness**: the
  `market-tick-data-service@125ec228` SHA cited for todo 1's audit script does not exist in the repo's git history
  (`git log --all`/`git cat-file -t` both fail to resolve it, across all slot-8 sibling repos) and the script file
  itself is absent from the working tree — possibly an instance of the known
  `quickmerge_agent_regate_resets_branch_ loses_local_commit_2026_07_31.md` class (a "Landed" claim that didn't actually
  land), or the script was deleted post-run per its one-off lifecycle without the commit having reached
  `live-defi-rollout`. Not investigated further — the audit's OWN findings (12,582 rows, the
  instrument_type/data_type/venue breakdown) are independently reproducible and were not relied upon blindly by this
  session's own live re-query (13,923 rows, larger population, consistent signature).
- **2026-08-03 (slot 4, data_engineering)**: picked up todo 3 (`tradfi_bare_instrument_type_phantom_manifest_rows-003`)
  and found the code change already shipped by slot 9 (`unified-api-contracts@d1495b35`,
  `fix(tradfi): extend residue quarantine for confirmed phantom instrument_type batch`, already on origin — verified
  frozenset in current HEAD carries all 6 values with the dated comment citing this doc) — flipping the checkbox to
  reflect reality. Todo 4 (deployment-api wiring gap) remains open.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — added the confirmed root-cause write site
  (`canonical_writer.py::write_candle_parquet`) found by the slot-8 root-cause pass above.
- **2026-08-04 (interactive session)**: closed the final open todo (4, deployment-api wiring gap) — found already fixed
  by unrelated work (`deployment-api@7988451`, 2026-08-03) that landed 6 accepted-exception entries including this
  frozenset. All 4 todos now done — flipped `status: resolved`.
- **2026-08-04 (interactive session, same day, later — operator live regression report)**: **REOPENED.** Operator
  observed deployment-ui's tradfi distinct-values panel showing only 3 instrument_types (`BOND`, `SPOT_PAIR`, `UNKNOWN`)
  — `FUTURE`/`OPTION`/`COMBO`/`EQUITY`/`ETF`/`INDEX` had vanished entirely. Root-caused to todo 3's own fix:
  `_ACCEPTED_EXCEPTIONS` filters by raw axis VALUE, not per-row, so quarantining `"OPTION"` etc. to silence 13,923
  phantom rows also hid every one of the millions of LEGITIMATE `OPTION` rows from the panel. Reverted the frozenset to
  `{"UD"}` only (`unified-api-contracts@86a35fdb`) — `UD` is the one value with genuinely zero legitimate population, so
  it's the only one safe to blanket-hide this way. The underlying 13,923 phantom rows are untouched by this revert
  (still real data-correctness defects, `capture_status=captured` with no backing GCS object) — added a new todo above
  for the proper row-level fix. `status` back to `open` pending that todo. Verified the live `coverage.json` rollup
  itself was never the problem (already had the full BOND/COMBO/EQUITY/ETF/FUTURE/INDEX/OPTION/SPOT_PAIR/UD population
  correctly) — this was purely a deployment-api read-time filtering bug, so no honest-coverage VM re-trigger is needed;
  the fix takes effect once deployment-api's own Docker image rebuilds against the new UAC version and redeploys (same
  publish→redeploy pipeline as the day's earlier tradfi fixes — see
  `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` for the CI-congestion context that also gates this).
- **2026-08-05 (interactive session, next day)**: live re-check of the phantom-row population (unscoped by `written_at`,
  unlike the prior day's window-scoped purge) found it had REGROWN — 16,992 rows, not the expected 0, with a fresh
  dominant batch (6,528 COMBO rows) written 21 hours AFTER the prior purge. This proved the writer bug was never
  actually fixed, only its symptom cleaned up once — a genuinely different, more serious finding than "one historical
  batch to clean up." Root-caused + fixed the writer itself (`market-data-processing-service@b039ec2f`, guard in
  `write_candle_parquet` refusing the phantom write shape outright) and re-purged the full current population (16,992
  rows, `market-tick-data-service`, verified 0 remain). `status: resolved` — this time backed by a code fix that
  prevents recurrence, not just another cleanup pass. Deployment-api's own display fix (separate finding above) still
  needs its live traffic promoted to a newer revision — flagged separately, not blocking this todo's closure.
