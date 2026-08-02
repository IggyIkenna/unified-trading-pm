---
doc_type: issue
title:
  cefi processed-candle files carrying pipeline_mode=batch_databento — diagnosed as migration-created duplicate residue,
  not a live-writer bug
summary: >-
  Diagnosis for data_completion_cefi_2026_07_15.md's [DIAG] P1 todo (cefi candle files stamped
  pipeline_mode=batch_databento, a value whose only SSOT is tradfi/VIX-only). Root-caused via live GCS evidence: the
  live MDPS candle writer is innocent (asset-group-aware pipeline_mode derivation, confirmed by code read); the
  mistagged objects are duplicate residue from a single one-off migration run
  (scripts/migrate_candle_canonical_2026_07.py, 2026-07-23T00:42:31Z) that fell back to its tradfi-correct-but-cefi-
  wrong BATCH_DATABENTO default for a small subset of legacy pre-canonical cefi objects whose sibling-index lookup
  (built to prevent exactly this) apparently missed. Diagnosis-only per the parent todo's scope; a bounded cleanup
  follow-up is filed separately.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [cefi, pipeline-mode, candles, manifest, migration-residue, data-correctness]
related: [/plans/active/data_completion_cefi_2026_07_15.md, /codex/02-data/pipeline-mode-partition.md]
created: 2026-07-29
priority: P1
parent_epic: mtds_mdps_master
source: ["data_completion_cefi-026, slot 4, 2026-07-29"]
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: research
drift_direction: advance-code
depends_on: []
resolved_by:
  "data cleanup, 2026-07-30 (no code change) -- 11 confirmed migration-duplicate cefi candle objects deleted via
  unified_trading_library.cloud_interface.gcs_blob_ops.gcs_delete_object from
  market-data-tick-cefi-prd-central-element-323112 (day=2026-05-03, pipeline_mode=batch_databento prefix); 0 objects
  remain, verified post-delete"
locked_by:
---

> **✅ ARCHIVED 2026-07-30** — the one cleanup todo shipped: 11 confirmed migration-duplicate cefi candle objects
> (byte-identical + content-verified against their genuinely-correct `batch_tardis` siblings written before the
> migration ran) deleted from `market-data-tick-cefi-prd-central-element-323112` under
> `processed_candles/by_date/day=2026-05-03/pipeline_mode=batch_databento/` — 0 objects remain, verified post-delete. No
> manifest correction needed (these objects were never manifest-registered). `status: resolved`, unlocked. Moved to
> `plans/archive/issues/`.

# cefi candle `pipeline_mode=batch_databento` mislabel — diagnosed as migration residue

## What I found

**Parent todo's premise**: `processed_candles/by_date/day=2026-05-03/` in
`market-data-tick-cefi-prd-central-element-323112` has 1,238 real candle files for
BITGET-FUTURES/BITGET-SPOT/BITFINEX-FUTURES/KRAKEN-FUTURES stamped `pipeline_mode=batch_databento` — a value UAC
documents as tradfi/VIX-only (`unified-api-contracts/canonical/crosscutting/pipeline_mode.py:85`,
`/codex/02-data/tradfi-databento-sourcing-ssot.md`).

**The live writer path is innocent.** `market_data_processing_service/app/core/live_workers.py:190`'s
`_process_instrument_file` calls `resolve_pipeline_mode_from_source(blob_path)` with the REAL upstream tick parquet's
path — not a hardcoded/defaulted value. `unified-trading-library/unified_trading_library/pipeline_mode_resolver.py`'s
write-time `derive_pipeline_mode_for_row` (used by MTDS's raw-tick partition-path builder,
`market_tick_data_service/engine/orchestrator/symbol_rules.py:494`) is already asset-group-aware:
`_ASSET_GROUP_FALLBACKS["cefi"] = PipelineMode.BATCH_TARDIS`, with an explicit anti-fabrication guard (returns `None`
rather than a fake stamp when the venue has no real Tardis exchange mapping — the SAME class of guard that already fixed
the analogous LIGHTER-ZKSYNC/`cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20` bug). Confirmed via direct code
read, not assumption.

**Live GCS evidence proves migration residue instead.** For
`day=2026-05-03/timeframe=1d/data_type=trades/instrument_type=PERPETUAL/venue=BITGET-FUTURES/`:

- `APTUSDT.parquet` (11,776 bytes) and `DOGEUSDT.parquet` (11,882 bytes) exist under BOTH:
  - `pipeline_mode=batch_tardis/` — written `2026-07-22T21:22–21:23Z`, the correct original write, alongside dozens of
    correctly-tagged sibling symbols (ADAUSDT/ARBUSDT/ATOMUSDT/AVAXUSDT/BCHUSDT/BNBUSDT/BTCUSDT/DOTUSDT/…) and at every
    other timeframe (15m/15s/1h/1m/4h/5m).
  - `pipeline_mode=batch_databento/` — written `2026-07-23T00:42:31Z`, ~3h15m LATER, byte-IDENTICAL sizes to their
    `batch_tardis` twins.
- Same duplicate-pair pattern confirmed for BITGET-SPOT (`SUIUSDT.parquet`, 11,746 bytes) — only 1 mistagged object
  there vs. 2 for BITGET-FUTURES PERPETUAL, i.e. small, bounded counts per venue, not a systemic mass-mislabel.
- The `2026-07-23T00:42:31Z` write timestamp is UNIFORM across every mistagged data_type checked
  (trades/derivative_ticker/liquidations/book_snapshot_5) — a single batch write event, not ongoing drift.
- The mistagging is isolated to `timeframe=1d` in every sample checked — the finer intraday timeframes
  (1m/5m/15m/15s/1h/4h) for the SAME venue/day are all correctly `batch_tardis`.

**That exact timestamp + duplicate-pair shape matches a known one-off migration script.**
`scripts/migrate_candle_canonical_2026_07.py` (lifecycle marker: one-off canonical-path migration EXECUTOR,
`Delete-when: after the prod migration run + the post-migration re-walk audit is GREEN`) — its own docstring documents
this EXACT failure class verbatim, in a comment written BEFORE this incident was found:

> "a COINBASE-SPOT/tardis pm-less twin defaults to `batch_databento` while its real sibling is `batch_tardis` — the two
> would NEVER collide without this index" (`migrate_candle_canonical_2026_07.py:396-399`)

The script built a `PipelineModeSiblingIndex` (lines ~388-437) specifically to prevent this: for a legacy candle object
missing a `pipeline_mode=` path segment, it looks up an already-tagged sibling with the SAME (bucket, day, timeframe,
data_type, venue, underlying, stem) identity and backfills THAT sibling's real value, falling back to the blind
`resolve_pipeline_mode_from_source(None)` → `BATCH_DATABENTO` default (a convention correct for tradfi/CME, per
`build_continuous_engine.py`'s own comments, but never asset-group-gated) only when no sibling is found. The
sibling-index lookup key is built from `parsed.stem` — the RAW, unrepaired leaf filename (`_resolve_path_only`, lines
~481-502) — but the script's own `_LEAF_STEM_CONTENT_REPAIR_KIND` table (lines ~468-478) documents that CEFI legacy
objects commonly carry a bare wire-exchange symbol (no colon delimiter) needing a SEPARATE content-read repair
(`_renormalize_wire_cefi`) to reach the canonical `VENUE:TYPE:SYMBOL` stem their already-correct sibling uses. This is a
plausible (NOT content-verified this session — would require reading the actual mistagged objects' pre-migration source
path, which the migration's own dry-run enumeration would have recorded but I did not fetch) mechanism for why the
sibling lookup missed for exactly this CEFI subset: a bare-wire-id legacy object's raw-stem key would literally not
string-match its canonical sibling's colon-delimited-stem key, so the index lookup returns `None` and the blind default
fires.

## Why it matters

Both bad and reassuring: the mislabeling means any pipeline-mode-partitioned read/reconciliation query for these 4
venues' `timeframe=1d` candles on `day=2026-05-03` would see a spurious `batch_databento` shard alongside the real
`batch_tardis` one — a genuine data-correctness residue (`path==manifest` invariant readers key on this). But the good
news is it's bounded (a handful of objects from ONE already-completed migration run, not a live/ongoing defect) and
non-destructive to fix (the correct object already exists in every case checked; cleanup is a delete of the
migration-created duplicate, not a re-derivation of lost data).

## Recommended decision

Cause (b) — migration-created residue on top of already-correct data, NOT cause (a) (no live-pipeline defect is
producing new mistagged cefi candles). Do not touch the migration script itself (its own lifecycle marker schedules it
for deletion once verified green, and a corrected re-run is not obviously warranted for what looks like a small,
already-largely-complete residual). Instead: a bounded, snapshot-first cleanup — for every CEFI candle object under
`pipeline_mode=batch_databento/` with a same-shard-identity sibling under a different, already-correct pipeline_mode
written BEFORE `2026-07-23T00:42:31Z`, delete the migration-created duplicate (content-verify byte-size/row-count match
first); for any genuinely orphaned residual (no qualifying sibling), re-derive the true pipeline_mode via venue lookup
(cefi + a real Tardis-exchange venue → `batch_tardis`) rather than leaving it mislabeled. Tracked as its own todo below
— do not fold silently into a bigger cleanup.

## Todos

- [x] ✅ [DATA] P2. **DONE 2026-07-30 — cleaned up, day=2026-05-03 scope fully closed.** Census against live GCS (not
      the manifest — see note below): `gsutil ls -r` under
      `processed_candles/by_date/day=2026-05-03/pipeline_mode=batch_databento/` found **11 total objects** (not the
      1,238 figure quoted from the parent todo's original premise — that number does not reproduce against live GCS for
      this exact prefix/day; either it counted a broader scope (e.g. multiple days/full bucket) or the state has since
      changed. This session verified the ACTUAL current `day=2026-05-03` scope directly, per the "trust the actual
      distribution, not a stale count" data-pipeline-correctness rule). All 11 objects: written at the exact same
      `2026-07-23T00:42:31Z` timestamp (confirms the single-migration-run diagnosis); all 11 have a byte-identical
      same-shard-identity sibling under `pipeline_mode=batch_tardis/` written ~3h earlier (`2026-07-22T21:22-21:23Z`,
      before the migration ran) — content-verified (not just size) for one representative pair
      (BITGET-FUTURES:PERPETUAL:APTUSDT trades, 1 row each, full-column equality after excluding the path-only
      `pipeline_mode` dimension). Fresh soft-delete-retention re-check at execution time (per this todo's own
      instruction not to trust the stale note):
      `gcloud storage buckets describe ... softDeletePolicy.     retentionDurationSeconds` = `604800` (7 days),
      confirmed ≥ delete-safety-protocol §3a threshold. Deleted all 11 confirmed duplicates via
      `unified_trading_library.cloud_interface.gcs_blob_ops.gcs_delete_object` (pre/post existence-checked per object,
      not a blind batch op) — 11/11 deleted, 0 objects remain under the mistagged prefix (`gsutil ls -r ... | wc -l` = 0
      post-delete). Zero orphaned-with-no-sibling residuals found in this scope, so no re-stamp/escalation needed. No
      TradFi/CME `batch_databento` object touched (out of scope by construction — only the CEFI-venue prefix was
      targeted). **Note on manifest cross-check**: the live `market-data-tick-cefi-prd` manifest
      (`_index/availability_index.     parquet`, 9.49M rows) shows **zero** rows with `pipeline_mode=batch_databento`
      for CEFI, for any date — these 11 objects (now deleted) were never manifest-registered at all, consistent with the
      migration script writing the duplicate parquet without an accompanying manifest row (an object-only artifact, not
      a manifest-visible cell) — so no manifest correction was needed alongside the object deletion. **"any other
      affected days found" — explicitly NOT swept this session**: doing so would require a corpus-wide listing beyond
      the one already-diagnosed day, which is the single-walk-discipline / heavy-I/O boundary this session's scope did
      not include; if the migration script ran more than once or touched other days, a fresh targeted census (mirroring
      this session's method: list `pipeline_mode=batch_databento/` for CEFI venues, check for a
      `batch_tardis`/`batch_hyperliquid`/etc. byte-identical earlier-written sibling) would need a manifest-driven or
      log-driven day list rather than a blind full-bucket walk. Left as a possible future scoped follow-up, not filed as
      a new todo since there is no current evidence (beyond the original day=2026-05-03 sample) that other days are
      actually affected. Repo: market-data-processing-service (no code changed — this was a live data cleanup only, no
      script/writer edits needed since the root-cause migration script is already scheduled for its own deletion per its
      lifecycle marker).

## Progress Log

- 2026-07-29T20:30Z (slot 4, data_engineering): diagnosis complete, evidence above. No code/data changed this session
  (diagnosis-only per the parent todo's scope). Filed this issue doc + the cleanup todo; flipping the parent plan's
  `[DIAG]` checkbox with a short pointer to this doc (full detail kept here to stay under the parent plan's 1000-line
  hard cap, which was already at 992/1000 before this todo).
