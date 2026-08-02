---
doc_type: issue
title: >-
  ManifestWriter(...) per_vm_shards audit across market-tick-data-service/instruments-service/market-data-processing-service
  scripts/ — 13 unsafe sites found + fixed, 3 deliberately left alone
summary: >-
  defi_satellite_ao_dispatch_batch7_2026_08_01.md's todo asked to sweep every direct `ManifestWriter(...)` construction
  in the 3 repos' `scripts/` trees for the same missing-`per_vm_shards=True` bug that caused two fleet-wide OOM
  outages on 2026-07-30/31 (`mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md`). Inventoried 47 real
  construction sites (13 MTDS, 29 instruments-service, 5 MDPS — one grep hit in each of MTDS/instruments-service was a
  docstring reference, not a real call). 13 were unsafe (no `per_vm_shards=True` and no `MANIFEST_PER_VM_SHARDS` env
  guard) — all 13 fixed by adding `per_vm_shards=True` explicitly. 1 additional site was SAFE-but-fragile (relied
  solely on an ambient env var with no explicit kwarg) — hardened defensively. 3 sites use `per_vm_shards=False`
  DELIBERATELY (a synchronous CAS remove+add+verify swap design that requires the ADD to land in the SAME consolidated
  index a raw `client.download_bytes()` re-read checks — `per_vm_shards=True` would silently break their own
  correctness verification) — confirmed correct, left unchanged. The remaining 30 sites were already safe (explicit
  `per_vm_shards=True` or an env-var hard-gate before `--apply-flips`).
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, instruments-service, market-data-processing-service]
scope: [engineer]
tags: [manifest-writer, per-vm-shards, memory-safety, audit, defi, sports, prediction]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch7_2026_08_01.md,
    /plans/active/issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: "2026-08-02"
parent_epic: defi_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [defi_satellite_ao_dispatch_batch7_2026_08_01-004]
resolved_by: slot-7
locked_by:
---

# ManifestWriter per_vm_shards audit — market-tick-data-service / instruments-service / market-data-processing-service

## What I found

Grepped `ManifestWriter(`/`_ManifestWriter(` construction sites under each repo's `scripts/` tree (including
subdirectories), read each multi-line call plus enough surrounding context to trace the target bucket/asset_group and
any pre/post-write verification pattern, and classified each as SAFE, UNSAFE, or DELIBERATE-FALSE.

### Fixed (13 sites — added `per_vm_shards=True`)

| repo | file:line | target bucket | why it was unsafe |
| --- | --- | --- | --- |
| market-tick-data-service | `scripts/rebuild_mtds_manifest.py:183` | cefi/defi/sports (per `--asset-group`) | no kwarg, no env guard, `Lifecycle: permanent` — highest-priority MTDS fix |
| instruments-service | `scripts/backfill_sports_per_entity_manifest.py:738` | sports (~2.6M rows) | no kwarg, no env guard |
| instruments-service | `scripts/close_fixtures_split_expected_unattempted_cells_2026_07_25.py:144` | sports | no kwarg, no env guard |
| instruments-service | `scripts/close_stale_enrichment_expected_unattempted_cells_2026_07_19.py:121` | sports | no kwarg, no env guard |
| instruments-service | `scripts/full_polymarket_dump.py:228` | prediction (~2.67M rows) | no kwarg, no env guard |
| instruments-service | `scripts/patch_prediction_shards.py:75` | prediction | no kwarg, no env guard |
| instruments-service | `scripts/rescan_prediction_v4.py:115` | prediction | no kwarg, no env guard, `Lifecycle: permanent` |
| market-data-processing-service | `scripts/reprocess_sports_odds.py:1075` | sports (canonical `instruments-store-sports-*`) | no kwarg, no env guard, `Lifecycle: permanent` |
| market-data-processing-service | `scripts/migrate_candle_canonical_2026_07.py:918` | per-`--asset-group` MDPS candle bucket | no kwarg; constructed **PER MIGRATED OBJECT inside a 64-thread pool** — the highest-severity site found (see below) |
| market-data-processing-service | `scripts/close_odds_horizon_bucket_expected_unattempted_cells_2026_07_25.py:154` | sports | no kwarg, no env guard (already ran once in prod 2026-07-25, kept anyway per its own not-yet-deleted `Lifecycle` marker) |

Plus 1 defense-in-depth hardening (already SAFE via an ambient-env hard-gate, but fragile to a future edit removing
that guard):

| repo | file:line | note |
| --- | --- | --- |
| market-tick-data-service | `scripts/mtds_reconcile_partial_bundles.py:488` | `--apply-flips` already hard-exits unless `MANIFEST_PER_VM_SHARDS` is set — added the explicit kwarg too so a future edit weakening that guard can't silently reopen the hole |

**`migrate_candle_canonical_2026_07.py:918` deserves its own callout.** Unlike every other fix here (a single
construction per script run), this one constructs a BRAND NEW `ManifestWriter` **per migrated GCS object**, inside a
`ThreadPoolExecutor(max_workers=args.workers)` (`--workers` defaults to 64) fan-out over potentially millions of
objects. Before this fix, every single one of those calls would have taken the legacy full-index read-merge-write path
on EVERY object if `MANIFEST_PER_VM_SHARDS` wasn't set in-process — not a one-time 14GB spike but potentially millions
of repeated multi-GB reads at 64-way concurrency. The file's own `_flush_manifest_with_backoff` docstring
(`market_data_processing_service/app/core/canonical_writer_manifest.py:66-78`) already states "Per-VM sharding reduced
but did not eliminate the contention" — confirming the design always assumed per-VM shards were on; the construction
site had simply never been updated to say so explicitly, relying entirely on the VM launcher's ambient
`MANIFEST_PER_VM_SHARDS` export (`deployment-service/scripts/vm/setup-data-pipeline-vm.sh`). A direct/local invocation
bypassing that launcher was fully exposed.

### Verified SAFE — no change needed (30 sites)

- **Explicit `per_vm_shards=True` already present** (verified by reading the actual multi-line call, not just the grep
  match): `gate3_solana_manifest_reconcile.py`, `reconcile_lighter_derivative_ticker_manifest_2026_07_30.py`,
  `restamp_lighter_ohlcv_batch_tardis_to_lighter_api_2026_07_18.py`, `migrate_legacy_gas_fees_venue_2026_07_30.py`
  (the original incident's own fix — confirmed still correct), `relabel_solana_dex_pools_fake_history.py`,
  `relabel_kamino_solend_lending_fabrication_2026_07_29.py`, `sports_captured_available_at_targeted_backfill_2026_07_14.py`,
  `one_offs/gmx_pipeline_mode_migration_2026_07_21.py` (MTDS); `aggregate_legacy_es_opt_trades.py`,
  `aggregate_processed_options_to_chain_bundle.py`, `backfill_orphan_class_e.py`, `backfill_orphan_class_e_sports.py`,
  `backfill_per_league_record_empty.py`, `backfill_teams_61_leagues_2026_07_13.py`,
  `dereg_rekey_la_liga_2_2026_07_13.py`, `fill_missing_player_stats.py`,
  `fold_china_russia_league_raw_id_folders_2026_07_24.py`,
  `fold_china_russia_league_raw_id_folders_fixtures_siblings_2026_07_24.py` (instruments-service);
  `backfill_candle_manifest.py` (MDPS).
- **`os.environ["MANIFEST_PER_VM_SHARDS"] = "true"` set unconditionally at module level before construction**
  (instruments-service, 14 sites — mostly the `backfill/api_football_*` + `fixtures_*`/`osc_repair`/`gw_false_empty`
  family): `reconcile_sports_lost_per_vm_shard_2026_07_13.py`, `recover_fixtures_from_truthset.py`,
  `osc_repair_captured_over_empty_2026_07_13.py`, `fixtures_trickle_resolution_2026_07_13.py`,
  `fixtures_eu_truthset_flip_2026_07_13.py`, `recency_masked_adjudication_2026_07_13.py`,
  `gw_false_empty_repair_2026_07_14.py`, `backfill/api_football_teams_no_roster_leagues_reconcile_2026_07_14.py`,
  `backfill/sports_blank_league_orphan_reconcile_2026_07_14.py`,
  `backfill/api_football_blank_league_orphan_reconcile_2026_07_15.py`,
  `backfill/api_football_attempted_failed_residual_closer_2026_07_13.py`,
  `backfill/api_football_blank_dt_venue_orphan_reconcile_2026_07_15.py`,
  `backfill/api_football_cf11_manifest_reconcile_2026_07_15.py`.
- **`reconcile_1440_nan_placeholders.py`** (MDPS): hard `os.environ.get("MANIFEST_PER_VM_SHARDS")` gate before
  `--apply-flips` — same pattern as `mtds_reconcile_partial_bundles.py`, but not hardened with an explicit kwarg in this
  pass (lower urgency; flagging here in case a future pass wants the same defense-in-depth treatment).

### Deliberately LEFT UNCHANGED — `per_vm_shards=False` is correct, not a bug (3 sites)

`market-tick-data-service`'s three dated "manifest swap" one-offs —
`scripts/sports/k1k2_casing_revert_2026_07_27/manifest_swap_casing_revert_2026_07_27.py:502`,
`scripts/sports/league_id_relocation/manifest_swap_2026_07_22.py:556`,
`scripts/sports/exchange_fixed_odds_fork/manifest_reconcile_2026_07_27.py:340` — all explicitly pass
`per_vm_shards=False`. Traced the full flow before touching any of them: each does `cas_remove_stale()` (a
generation-matched read-filter-write loop directly against the consolidated index via `client.download_bytes_with_
generation`/`conditional_upload_bytes` — bypassing `ManifestWriter` entirely), THEN constructs a `ManifestWriter(...,
per_vm_shards=False)` to `record_captured`/`add` the replacement rows, THEN calls `writer.write()`/`writer.flush()`,
THEN immediately re-reads the consolidated index via a RAW `client.download_bytes(bucket, INDEX_BLOB)` (its own
`_index_read()` helper, NOT the library's `read_availability_index()`) to `verify_swap()` that the ADD rows are
already present.

**This raw-read verify is the deciding factor.** `unified_trading_library.manifest_writer.read_availability_index()`
always transparently merges per-VM shards on top of the consolidated blob regardless of the writer's setting
(`_read_index.py:585-599`: "Single SSOT: reader is flag-agnostic... reader now always merges per-VM" — this was a
2026-04-29 fix for exactly the opposite failure mode, a reader/writer SSOT split). But these 3 scripts' own `_index_
read()` is a raw, un-merged read — if the ADD had gone to a per-VM shard (`per_vm_shards=True`), the immediate
post-write `verify_swap()` call would see the OLD (pre-ADD) consolidated content and fail every single time, even
though the write genuinely succeeded. `per_vm_shards=False` is therefore load-bearing for this design's own
correctness check, not an oversight — flipping it would have been a real regression I almost introduced before tracing
the verify path. Confirmed instruments-service's 6 fixed sites do NOT have this raw-read pattern (they verify via the
library's own `read_availability_index()`, which is merge-aware) before applying their fixes.

## Why it matters

Per `mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md`, the legacy (non-per-VM-shard) `ManifestWriter`
flush path reads the ENTIRE consolidated index into memory on every `.close()`/`.flush()` — ~14.86 GiB for the 27M-row
defi bucket, and proportionally large (low-single-digit GB) for the ~2.6-2.7M-row sports/prediction buckets these 13
fixes target. This has already caused two confirmed fleet-wide orchestrator outages. `migrate_candle_canonical_2026_07.py`
was the most severe latent instance found — a per-object construction under 64-way concurrency, meaning an unset env
var wouldn't have caused one OOM spike but potentially thousands of repeated multi-GB reads across a single migration
run.

## Todos

- [x] [DATA] P2. Fix all 13 confirmed-unsafe `ManifestWriter(...)` construction sites (add `per_vm_shards=True`) across
      market-tick-data-service (2 files), instruments-service (6 files), market-data-processing-service (3 files, incl.
      the highest-severity per-object/64-thread site). — DONE 2026-08-02, this doc's own audit.
- [x] [DATA] P3. Harden `mtds_reconcile_partial_bundles.py`'s already-safe ambient-env-gated construction with an
      explicit `per_vm_shards=True` kwarg (defense-in-depth against a future guard-weakening edit). — DONE 2026-08-02.
- [ ] [DATA] P3. Apply the same defense-in-depth hardening to `market-data-processing-service/scripts/reconcile_1440_
      nan_placeholders.py:422` (currently SAFE via a hard env-gate before `--apply-flips`, same fragility class as
      `mtds_reconcile_partial_bundles.py` was before this pass) — not done in this pass to keep scope to the confirmed-
      unsafe set; low urgency since it's already safe as written. (repo: market-data-processing-service)
- [ ] [DATA] P3. Confirm (via GCS heartbeat/last-run evidence, not guesswork) whether the 3 deliberately-unchanged MTDS
      sports "manifest swap" one-offs (`k1k2_casing_revert_2026_07_27`, `league_id_relocation/manifest_swap_2026_07_22`,
      `exchange_fixed_odds_fork/manifest_reconcile_2026_07_27`) have already run to completion in prod — each carries a
      "DELETE after applied" lifecycle marker but the files are still present. If confirmed applied, delete them (the
      `per_vm_shards=False` design is correct either way; this is purely a repo-hygiene follow-up, not a safety fix).
      (repo: market-tick-data-service)

## Codex SSOTs

`/codex/02-data/availability-manifest-and-data-status.md` (manifest schema + per-VM-shard architecture);
`/codex/06-coding-standards/script-homes.md` (one-off script lifecycle markers).
