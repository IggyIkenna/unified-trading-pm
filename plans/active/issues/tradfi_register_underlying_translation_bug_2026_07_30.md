---
doc_type: issue
title:
  "register_tradfi_recovery_quarantine_manifest_2026_07_30.py's apply_register wrote the raw candidate root as the
  manifest underlying instead of the translated value baked into the physical GCS path — 98 of 248 first-prod-run rows
  mismatched (caught pre-consolidation, hand-patched + verified, root cause fixed)"
summary:
  "Executing tradfi_recovery_quarantine_registration_gap_2026_07_27.md item 2 (run the register script's dry-run then
  --apply against prod), the --apply pass wrote 248 canonical manifest rows into a per-VM shard, but 98 of them (40%)
  carried a manifest `underlying` value that did not match the `underlying=` segment of the row's own
  physically-confirmed GCS path — because chain instrument_types (futures_chain/options_chain) translate a candidate
  root through `_exchange_to_product_root` (e.g. MES->MICRO-SP500, EW1-4->SP500, RB->GASOLINE) when building the target
  path, but `apply_register` wrote the untranslated `cand.root` into the manifest instead of the translated value.
  Caught before the every-minute manifest-consolidator cron merged the per-VM shard into the main availability_index
  (main index mtime 12:00:59 UTC, shard write 12:06:04 UTC, caught+patched by 12:10 UTC) — hand-patched the
  still-unconsolidated shard in place via a generation-CAS read-modify-write, verified 0 remaining mismatches across all
  186 affected cells / 248 rows, then fixed the root cause in the script (added an `actual_underlying` field to
  `RegisterCandidate`, populated from the same translation already computed for the existing-key dedup, and used it in
  both `apply_register` write branches) plus added regression tests + a diagnostic `underlying` column to the dry-run
  mapping TSV."
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tradfi, manifest, data-correctness, register-script, incident]
related:
  [
    /plans/active/issues/tradfi_recovery_quarantine_registration_gap_2026_07_27.md,
    /plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md,
  ]
created: 2026-07-30
priority: P1
parent_epic: tradfi_master
source: "tradfi_recovery_quarantine_registration_gap-003 (backlog task), 2026-07-30"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by: ""
locked_by: ""
---

# TradFi register-script incident: untranslated root written as manifest underlying

## What I found

Running `tradfi_recovery_quarantine_registration_gap_2026_07_27.md` item 2 — the dry-run then `--apply` pass of
`register_tradfi_recovery_quarantine_manifest_2026_07_30.py` against prod GCS
(`market-data-tick-tradfi-prd-central-element-323112`) — the dry-run confirmed 248 candidates present on GCS (within the
~428 upper bound), and `--apply` wrote 248 canonical rows into a per-VM manifest shard
(`_index/per_vm/local-2108856-43a6.parquet`, `per_vm_shards=True`).

Spot-checking the mapping TSV against the actual GCS paths surfaced a mismatch: for `instrument_type=futures_chain`
candidates, `_canonical_chain_path` (the SAME builder `_recovery_target_for` calls) translates the candidate root
through `_exchange_to_product_root` before building the path (e.g. root `MES` -> path segment `underlying=MICRO-SP500`;
`EW1`/`EW2`/`EW3`/`EW4` -> `SP500`; `RB`->`GASOLINE`; `ZM`->`SOYMEAL`; `6A`->`AUD`; etc. — 20+ distinct alias pairs
observed in this run's 248 rows). `apply_register`, however, wrote `underlying=cand.root` (the untranslated root)
directly into both write branches (`record_captured_from_counts`'s `row_key`/`expected_root_clusters`/
`observed_clusters`, and `writer.add`'s `underlying=` kwarg) instead of the translated value. A quantitative check
across all 248 written rows found 98 (39.5%) where `root != actual_underlying_in_path` — i.e. 98 manifest rows whose
`underlying` field did not match the `underlying=` segment of their own physically-confirmed GCS object path.
`instrument_type=combo` rows were unaffected (combo paths pass the root through verbatim, so root and actual-underlying
are always equal there).

Timeline: `--apply` ran 12:05:27-12:06:04 UTC. The manifest-consolidator SSOT documents a per-minute (`*/1 * * * * UTC`)
cron that merges every `_index/per_vm/*.parquet` shard idempotently and prunes nothing. The main
`availability_index.parquet`'s `updateTime` was 12:00:59 UTC (before the write) and had not advanced by 12:10 UTC when
checked — the shard had not yet been consolidated, giving a window to correct it in place rather than needing a post-hoc
manifest correction pass against the merged main index.

## Why it matters

A manifest row whose `underlying` doesn't match its physical bundle's own path is silently wrong twice over: (1) it does
NOT close the real registration gap for the CORRECT canonical key (e.g. a query for `underlying=MICRO-SP500` would still
see `todo`/missing, since the row was filed under `MES` instead), and (2) it plants an extra row under a key (`MES`)
that doesn't correspond to how any other tooling in this corpus writes/reads `underlying=` for chain instrument_types
(verified: existing manifest rows for the same population consistently use the translated human-readable name, never the
raw exchange code, for chain types). Left uncorrected, this would have both re-opened the exact gap this whole
recovery/register effort exists to close AND introduced ~98 confusing extra rows into the live tradfi availability_index
— a data-correctness regression, not a cosmetic one.

## Remediation (complete)

1. **Caught pre-consolidation**: confirmed via `updateTime` comparison that the bad shard had not yet merged into the
   main index.
2. **Hand-patched in place**: downloaded the per-VM shard with its generation, corrected the 98 mismatched rows'
   `underlying` field (using the same target-path parse the enumeration step already computes), and wrote it back via
   `conditional_upload_bytes(if_generation_match=<original generation>)` — an atomic CAS write, so no concurrent writer
   to this shard could have been silently clobbered. Verified: re-downloaded, grouped all 248 rows by
   `(date, venue, instrument_type, data_type)`, and confirmed the SET of `underlying` values per cell now exactly equals
   the SET of translated values independently derived from each confirmed candidate's own `target_uri` — 0 mismatches
   across all 186 affected cells.
3. **Root cause fixed** in `register_tradfi_recovery_quarantine_manifest_2026_07_30.py` (market-tick-data-service):
   added `actual_underlying: str` to the `RegisterCandidate` dataclass, populated from the same
   `_kv(target_rel)`-derived translation `enumerate_register_candidates` already computes for the existing-key dedup
   (previously computed and then discarded), and used `cand.actual_underlying` (not `cand.root`) in both
   `apply_register` write branches. Also added an `underlying` column to the dry-run mapping TSV so a future spot-check
   can catch this class of bug without needing to hand-parse `target_uri`.
4. **Regression tests added**: `test_enumerate_register_candidates_captures_translated_underlying_when_not_deduped`,
   `test_apply_register_writes_translated_underlying_not_raw_root`,
   `test_apply_register_bundled_data_type_writes_translated_underlying`,
   `test_apply_register_skips_unresolvable_pipeline_mode` (19 total unit tests green, full `quality-gates.sh` run in
   progress at issue-filing time).

## Recommended decision

- [x] ✅ [SCRIPT] P2. After the next manifest-consolidator run for the tradfi bucket, verify the corrected 248 rows
      (from `_index/per_vm/local-2108856-43a6.parquet`) merged correctly into `_index/availability_index.parquet` with
      no duplicate keys and no dropped rows — spot-check the same sample cells this issue doc verified (e.g.
      `date=2020-06-29, venue=CME,     instrument_type=futures_chain, data_type=ohlcv_1m` should read
      `underlying=MICRO-SP500`). Repo: market-tick-data-service. **Done when**: a fresh read of the main
      `availability_index.parquet` confirms the sample cells carry the correct translated `underlying` and the total
      registered-row count for this population is unchanged at 248 (no dupes, no drops). — **Verified 2026-07-30**: the
      per-VM shard `_index/per_vm/local-2108856-43a6.parquet` is gone (consolidated); main index `updateTime`
      2026-07-30T12:33:22Z (well after the 12:05:27-12:06:04Z write window). Read-only check against
      `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`: the sample cell
      (`date=2020-06-29, venue=CME, instrument_type=futures_chain, data_type=ohlcv_1m`) reads `underlying=MICRO-SP500`,
      `capture_status=captured`. Isolating the register-run population (rows with `written_at` in the
      `[12:05:00Z, 12:07:00Z]` write window, `service_name=market-tick-data-service`, chain/combo instrument_types):
      exactly 248 rows, 0 duplicate `(date, venue, data_type, instrument_type, underlying)` keys, 0 rows with
      `capture_status != captured` — no dupes, no drops.
