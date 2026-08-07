---
doc_type: issue
title: >-
  perp_daily_ctx/perp_funding manifest-invisibility — derivative_ticker migration DECLINED (live paper-trading reader
  risk); safe incremental fix identified instead
summary: >-
  Investigated distinct_values_noncanonical_audit_2026_07_20.md's perp_daily_ctx/perp_mark_price todo (migrate the MTDS
  HL backfill script + features-service CeFi corpus writer onto the derivative_ticker schema). Found the proposed target
  directly conflicts with the CURRENT production read shape — CanonicalPerpFundingProvider (instantiated by the live
  paper-trading CLI paper_run_handler.py:931-932) reads perp_funding + perp_daily_ctx TODAY, serving real,
  already-migrated historical HYPERLIQUID/GMX/CeFi funding+mark-price data (the 2026-07-13
  dedicated-bucket-to-shared-bucket migration copied years of real production rows into this exact shape). Migrating
  onto derivative_ticker would require rewriting the live reader + a real backfill/dual-read transition, and would
  pre-empt an already-gated, NOT-yet-approved separate design decision (see Established facts). Declined the risky
  migration per this task's own explicit safety override; documented a safe incremental alternative instead (register
  perp_daily_ctx as its own canonical data_type + backfill manifest rows for the already-migrated historical shard
  tuples, WITHOUT touching the reader or writer schema) — flagged as itself needing operator awareness before autonomous
  execution, mirroring this exact plan's own established "UAC canonical-set additions are not safe-code" precedent
  (RESULT 4, venue-axis case).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, features-service, strategy-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    defi,
    perp-funding,
    perp-daily-ctx,
    derivative-ticker,
    manifest,
    honest-coverage,
    canonicalisation,
    live-strategy-reader,
    data-correctness,
  ]
related:
  [
    plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    plans/archive/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md,
    /plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    plans/active/issues/downstream_funding_staking_canonical_reader_audit_2026_07_21.md,
    plans/archive/issues/mtds_plan_reconciliation_2026_06_29.md,
  ]
created: "2026-07-22"
author: unknown
last_updated: "2026-07-22"
parent_epic: manifest_master
priority: P1
source: >-
  distinct_values_noncanonical_audit_2026_07_20.md's perp_daily_ctx/perp_mark_price todo (line ~330), dispatched to a
  sub-agent under /autonomous with an explicit override to stop short of forcing the migration if the live-reader risk
  proved real
assigned_vm: NA
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py,
    strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py,
    /plans/archive/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md,
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /plans/active/issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md,
  ]
---

# perp_daily_ctx/perp_funding manifest-invisibility — derivative_ticker migration DECLINED, safe alternative identified

## Verdict

**Did NOT execute the migration the source todo asked for.** Investigation (below) shows the requested "migrate both
writers onto `derivative_ticker`" fix would touch a **live, currently-consumed strategy read path** in a way that cannot
be verified safe within this session's scope, and would pre-empt a separate, already-gated, not-yet-approved design
decision. Per this task's explicit safety override, stopping here with a full writeup + a concrete, safe, incremental
alternative rather than forcing the migration. No code was changed in market-tick-data-service, features-service, or
strategy-service.

## What the source todo asked for (paraphrased)

`distinct_values_noncanonical_audit_2026_07_20.md` (~line 330) flagged `perp_daily_ctx`/`perp_mark_price` as
"structurally invisible" to the honest-coverage system — written via raw `gcsfs` calls with zero manifest writes, by:

1. `market-tick-data-service/scripts/backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py` — a campaign-scoped
   Hyperliquid mark-price backfill.
2. `features-service/features_service/cefi/calculators/perp_funding_corpus.py` — a CeFi perp-funding corpus writer.

Proposed fix: migrate both onto the `derivative_ticker` data_type/schema (`DEFI_PERPETUAL_DERIVATIVE_TICKER`,
`unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py:766-782` — one row per instrument/day with
`funding_rate`/`open_interest`/`mark_price`/`index_price` as embedded, nullable fields) and retire the raw-gcsfs path.

## Established facts (verified this session, file:line evidence)

1. **`perp_funding` is ALREADY a registered canonical data_type with a full SchemaContract** —
   `unified-api-contracts/.../registry/market_data_categories.py:165` (`DATA_TYPES_BY_ASSET_GROUP["defi"]`) +
   `unified_api_contracts/internal/schemas/contracts.py:745-758` (`DEFI_PERPETUAL_PERP_FUNDING`). The source todo's
   claim "neither is a canonical data_type" is only half right. **`perp_daily_ctx` is the genuine gap** — it appears
   nowhere in `DATA_TYPES_BY_ASSET_GROUP` or any `SchemaContract`.

2. **`CanonicalPerpFundingProvider` is the live production reader, and it reads `perp_funding` + `perp_daily_ctx`
   TODAY** — `strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py:65-66`
   (`_FUNDING_DATA_TYPE = "perp_funding"`, `_DAILY_CTX_DATA_TYPE = "perp_daily_ctx"`), reading from
   `resolve_bucket_name(kind="tick-data", asset_group="defi")` (the shared, canonical bucket — not a side channel).
   **Real production caller confirmed**: `strategy-service/strategy_service/cli/handlers/paper_run_handler.py:931-932`
   instantiates `CanonicalPerpFundingProvider()` and calls `funding_window(...)` directly in the paper-trading run path
   (also `paper_universe_metrics.py`). This is the CARRY_BASIS_PERP / CARRY_FUNDING_DISPERSION archetype's real data
   feed, not a dead or diagnostic-only path.

3. **The current `perp_funding`/`perp_daily_ctx` rows in the shared bucket are REAL, migrated PRODUCTION history, not
   placeholder/test data.**
   `market-tick-data-service/market_tick_data_service/scripts/ migrate_lst_perp_shared_bucket_gap_2026_07_13.py`
   (referenced from `/plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md`) copied years of real
   HYPERLIQUID/GMX/CeFi funding + mark-price history from the now-deleted dedicated `perp-funding-{project}` bucket into
   the shared bucket at the IDENTICAL `perp_funding`/`perp_daily_ctx` path shape (same key, `gcs_copy_object`, no
   transform). Verified counts from that plan's Progress Log: HL `perp_daily_ctx` 1,109 objects + a later 6,941-object
   residual-gap closure (HL funding 177d, the whole HL `perp_mark_price` data_type 316d, GMX 2021-2023 funding history,
   7 CeFi Tardis venues' captures, etc). Post-migration live verification: `funding_for_day(2026-05-18)` → 697 real
   observations across 7 CeFi venues + HL + GMX, all with real `mark_price` populated from `perp_daily_ctx`.

4. **The MTDS HL mark-price backfill script targets a bucket that is CONFIRMED DELETED.** Live-checked this session:
   `gcloud storage buckets describe gs://perp-funding-central-element-323112` → **404 not found.** The script's
   `PF_BUCKET = f"perp-funding-{PROJECT}"` (line 42) can no longer be written to — any `--apply` run today would error
   outright, not silently succeed. This is corroborated by
   `plans/active/issues/downstream_funding_staking_canonical_reader_audit_2026_07_21.md` ("3 funding diagnostic scripts
   on the deleted `perp-funding-{pid}` bucket ... deleted 2026-07-10") and by
   `defi_dedicated_bucket_shared_migration_2026_07_13.md`'s P3 housekeeping todo (open when this was written; closed
   2026-07-31 per na-eligibility-audit — doc now archived at
   `/plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md`), which explicitly names
   `backfill_hl_*_2026_06_17.py` as hardcoding a dead bucket name tied to an already-completed migration — **this
   script's disposition was tracked in that OTHER plan.** Not touched here to avoid collision with whoever owns that
   plan's cleanup pass. Its own lifecycle marker
   (`# Delete-when: after HyperLiquid mark-price backfill prod-run verified + GCS orphan sweep = 0`) appears already
   satisfied — the backfill's real historical output is the exact data the 2026-07-13 migration copied forward, and the
   source bucket is confirmed gone.

5. **The features-service CeFi corpus writer (`perp_funding_corpus.py`) targets the CORRECT current-schema location but
   has never run in production.** Its own docstring (lines 21-26) states it writes to the shared bucket at
   `perp_funding`/`perp_daily_ctx` (matching what the reader expects), and "has never actually run in production
   (confirmed via a direct real-data check 2026-07-13 — zero `asset_group=cefi`/`pipeline_mode=batch_tardis` objects
   exist in either bucket across 2021-2026)". No historical CeFi data is at stake for this one specifically — but
   migrating ONLY this writer's schema to `derivative_ticker` without also updating the reader would make its future
   output permanently unreadable by `CanonicalPerpFundingProvider` (defeating the writer's whole purpose — unblocking
   CARRY_BASIS_PERP non-HL venues + CARRY_FUNDING_DISPERSION), since the reader would still be looking for
   `perp_funding`/`perp_daily_ctx`.

6. **The 2026-07-15 operator ruling on `derivative_ticker` is about the MTDS CAPTURE layer, and explicitly does NOT yet
   authorize retiring `perp_funding`/`perp_daily_ctx` as the read/strategy-facing shape.**
   `plans/archive/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md` established
   `derivative_ticker` as the canonical RAW-funding capture home for ALL perp venues going forward (MTDS wiring, GMX
   dual-write, etc) — this is a genuinely-shipped, separate change. But that SAME doc carries an explicitly gated,
   still-open `[DESIGN] P1` todo: _"Decide: demote `perp_funding` from a captured raw type to a DERIVED interval view...
   Scope of the decision (do NOT execute before the parity evidence exists)..."_ — unchecked (`[ ]`), and its own stated
   scope is `perp_funding` only; it never even mentions `perp_daily_ctx`/mark-price. Executing the source todo's
   requested migration (retire `perp_funding`/`perp_daily_ctx` on the STRATEGY READ side in favor of
   `derivative_ticker`) would pre-empt this still-undecided, explicitly-gated design question — for a shape (mark price)
   that design todo doesn't even cover yet.

## Why the requested migration is declined (risk assessment)

Doing what the source todo asked — rewrite both writers to emit `derivative_ticker` rows and retire the raw-gcsfs path —
necessarily also requires rewriting `CanonicalPerpFundingProvider` (it has no other way to see the new shape), which is
read by the live paper-trading CLI today. That, in turn, requires one of:

- **Backfilling** years of already-migrated real HL/GMX/CeFi `perp_funding`+`perp_daily_ctx` history into the new
  `derivative_ticker` row shape (a real, large, non-trivial data transform on live-strategy-facing history — no small
  "add a manifest call" change), or
- **Dual-reading** both shapes in the provider during a transition window (real added complexity + a real
  determinism/testing burden — `paper(W) == batch-rerun(W)` epsilon=0 must hold per
  `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`, and this session cannot fully verify that
  invariant survives a live-schema change to a strategy-reading class without a dedicated backtest re-run), plus
- Pre-empting the separately-gated `[DESIGN] P1` decision above, which the operator has not yet ruled on.

This is exactly the class of risk the task's own explicit safety override anticipated ("the reader would need
simultaneous changes you're not confident are safe... STOP and write a thorough investigation"). Declining to force it.

## Safe, incremental alternative (proposed, NOT executed)

The actual complaint driving the source todo is **manifest-invisibility**, not the schema shape itself — "this cluster
will keep costing real coverage/completeness accuracy without ever tripping the distinct-values panel, since the panel
only ever sees what's in the manifest." That can be fixed WITHOUT touching the live reader or either writer's row shape:

1. Register `perp_daily_ctx` as its own canonical data_type in `DATA_TYPES_BY_ASSET_GROUP["defi"]` + add a
   `SchemaContract` mirroring `DEFI_PERPETUAL_PERP_FUNDING`'s shape (mark_price + day_ntl_vlm + open_interest columns,
   `instrument_id`/`venue`/`chain`/`ts_event`) — `perp_funding` already has one; `perp_daily_ctx` needs its own, not a
   fold into `derivative_ticker`.
2. Add real `ManifestWriter`/`record_captured` calls to both ad-hoc writers, keeping their CURRENT
   `perp_funding`/`perp_daily_ctx` data_types exactly as-is (zero change to what the reader sees or reads).
3. Backfill manifest rows for the already-migrated historical `(venue, data_type, day)` shard tuples sitting in the
   shared bucket today (mirrors the precedent already executed for the dex_pools/lending_indices fold —
   `/plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md`, `status: resolved` 2026-07-22, path
   corrected 2026-07-26 by `/plan-reconcile defi` — a manifest-registration-only pass, zero GCS object mutation).

**This proposal is NOT executed here either**, for one reason worth flagging explicitly: step 1 (adding a new canonical
`data_type` to `DATA_TYPES_BY_ASSET_GROUP`) is the same class of change this exact parent plan
(`distinct_values_noncanonical_audit_2026_07_20.md`, RESULT 4) already established is **"NOT safe-code"** for the venues
axis — a canonical-set addition can expand what the standing expected-universe enumerator treats as
`expected_unattempted` across the historical calendar, which can visibly DROP measured `completeness_pct` fleet-wide
(the same "rule-11 blast radius" already flagged there for venues). The same mechanism plausibly applies to a new
data_type addition. This needs a quick, cheap check (does adding a data_type to this dict, for an
already-perpetual-scoped instrument_type, actually mint new `expected_unattempted` rows across the full historical
window, or is the perpetual/defi denominator already bounded by venue×instrument_type independent of this specific
list?) before executing autonomously — flagging for operator awareness rather than guessing.

## What was deliberately NOT touched (collision avoidance)

- `market-tick-data-service/scripts/backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py` — disposition was tracked
  as a P3 todo in `defi_dedicated_bucket_shared_migration_2026_07_13.md` (housekeeping cluster, item 3; closed
  2026-07-31, doc now archived at `/plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md`). Not
  deleted or edited here.
- `market-tick-data-service/market_tick_data_service/scripts/migrate_lst_perp_shared_bucket_gap_2026_07_13.py` — same
  plan's P3 item 1 (its own `Delete-when` condition was already satisfied and the file deleted — see the archived doc).
  Not deleted here.
- `strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py` — the live reader. Not touched.
- `features-service/features_service/cefi/calculators/perp_funding_corpus.py` — the unrun CeFi writer. Not touched (its
  current schema is already correct for what the reader expects; only the manifest-writing gap is real).

## Todos (for whoever picks this up next — NOT dispatched automatically)

- [x] ✅ [VERIFY] P2. **DONE 2026-07-28 (slot-6, data_engineering).** Confirmed whether adding a data_type to
      `DATA_TYPES_BY_ASSET_GROUP["defi"]` (for an already-registered venue×instrument_type combination) actually changes
      `expected_unattempted` materialisation / `completeness_pct`, or whether that denominator is scoped independently.
      See Progress Log entry above: NOT inert in general (the axis is a direct enumerator input, unlike the venue axis)
      but IS inert specifically for HYPERLIQUID/CeFi combos, since they enumerate under
      `DATA_TYPES_BY_ASSET_GROUP["cefi"]`, a separate dict key.
- [x] ✅ [CODE] P2. (Gated on the verify above.) **DONE 2026-08-04 — closed by citation, landed via
      `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s todo -010** (per this item's own note below: "close this
      checkbox by citation once batch6's todo lands"). Register `perp_daily_ctx` under
      `DATA_TYPES_BY_ASSET_GROUP["defi"]` ONLY (confirmed inert for HYPERLIQUID/CeFi combos, no operator sign-off needed
      for THIS specific registration — see Progress Log) as its own canonical data_type + SchemaContract (mirror
      `DEFI_PERPETUAL_PERP_FUNDING`); add manifest writes to both ad-hoc writers, unchanged schema; backfill manifest
      rows for the existing historical shard tuples. Repos: unified-api-contracts, market-tick-data-service,
      features-service, unified-trading-pm (manifest backfill script). **na-eligibility-audit 2026-08-01:
      KEEP-NA-STALE-DUPLICATE — already extracted verbatim into
      `defi_satellite_ao_dispatch_batch6_2026_07_30.md:363-371` (status: active, `assigned_vm: planning`, cites this doc
      as source). Not reclassified — track completion there; close this checkbox by citation once batch6's todo lands.**
      Evidence: `unified-api-contracts@17b1cf21`, `features-service@c678f0fd`,
      `unified-trading-pm/scripts/migration/register_perp_daily_ctx_manifest_backfill_2026_08_04.py` (1,158 manifest
      rows registered against prod, verified via direct per-VM-shard read). Full detail in batch6's Progress Log entry
      for this todo. The MTDS HL mark-price backfill script's writer-half was confirmed moot (dead target bucket, per
      fact #4 above) rather than forced — matches this doc's own established finding, not a new decision.
- [x] ✅ [CODE] P2. **DONE 2026-08-04 (sub-agent, data_engineering).** This doc's source todo named BOTH
      `perp_daily_ctx` AND `perp_mark_price` — the checkbox above only closed the `perp_daily_ctx` half.
      `perp_mark_price` is a DISTINCT, separately-tagged data_type (confirmed via direct GCS content read, not name
      inference — its rows carry only `mark_price`, no `day_ntl_vlm`/`open_interest`, unlike `perp_daily_ctx`), so it
      needed its own registration + backfill, not a citation of the above. Registered `perp_mark_price` under
      `DATA_TYPES_BY_ASSET_GROUP["defi"]` + new `DEFI_PERPETUAL_PERP_MARK_PRICE` SchemaContract (mirrors this doc's
      established inertness argument — HYPERLIQUID/CeFi combos enumerate under the separate `"cefi"` key, so this
      registration is a no-op for their `expected_unattempted` denominator, same as `perp_daily_ctx`'s). Confirmed this
      data_type is fully DEAD (no writer AND no reader) — a stronger case than `perp_daily_ctx`'s: the MTDS HL
      mark-price backfill script's target bucket is confirmed deleted (fact #4 above) AND its current code no longer
      even produces this data_type (its `_DT` constant was renamed to `perp_daily_ctx` at some point after the
      historical `perp_mark_price` rows were written — the script's own OUTPUT docstring is stale); no strategy-service
      reader references it either (direct grep of `canonical_perp_funding_provider.py` +
      `canonical_dex_pool_provider.py`, zero hits). Registered anyway per the honest-coverage rule established elsewhere
      in this doc — real historical rows should not stay manifest-invisible just because both writer and reader are
      dead. Backfilled manifest rows for the real historical objects: 316 (day, venue) shards, HYPERLIQUID, 22,690
      objects, 2023-05-20..2025-06-01 — NON-contiguous (315 contiguous days + one isolated day 2025-06-01, 199 objects,
      both segments sharing the same `available_at` timestamp cluster, i.e. one historical migration batch, not ongoing
      production). Evidence: `unified-api-contracts@<pending-quickmerge-sha>`,
      `unified-trading-pm/scripts/migration/register_perp_mark_price_manifest_backfill_2026_08_04.py` (316 manifest rows
      registered against prod, verified via direct per-VM-shard read — all `capture_status=captured`, `row_count` sum
      22,690, matching discovery exactly).
- [ ] [OPERATOR-DECISION] P3. Whether/when to execute the ALREADY-GATED `[DESIGN] P1` todo in
      `defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md` (demote `perp_funding` to a derived
      view) — and, if so, whether `perp_daily_ctx`/mark-price should be folded into that same decision. This issue doc
      does not resolve that question; it only establishes that the source todo's migration should not be forced ahead of
      it.

## Not fixed here, why

This is a stop-and-document outcome per this task's explicit safety override, not a completed migration. See "Verdict"
above.

## Progress Log

- **2026-08-04 (sub-agent, data_engineering — perp_mark_price sibling gap)**: Closed the second `[CODE] P2` todo above.
  This doc's source todo (see "What the source todo asked for") named both `perp_daily_ctx` and `perp_mark_price`; the
  earlier 2026-08-04 entry below only closed the `perp_daily_ctx` half (via batch6's todo -010). Re-verified from
  scratch rather than trusting the name similarity: `perp_mark_price` is a genuinely DISTINCT data_type — a direct GCS
  content read of the real historical objects (not the writer script's docstring, which is stale) showed rows carrying
  only `mark_price`, no `day_ntl_vlm`/`open_interest`. Confirmed via a full bounded day-by-day prefix scan
  (2023-05-20..2026-08-04, 1,173 days, one exact-prefix GCS list call per day — same single-walk-discipline method as
  the `perp_daily_ctx` backfill) that the real corpus is 316 (day, venue) shards / 22,690 objects, HYPERLIQUID only,
  spanning 2023-05-20..2025-06-01 but NON-contiguous (315 contiguous days 2023-05-20..2024-03-29 + one isolated day
  2025-06-01 with 199 objects — an initial binary-search + spot-check pass suggested exactly this shape, but the full
  scan was run anyway rather than trusting an assumption, per the workspace's data-correctness-is-the-heartbeat rule;
  both segments share the same `available_at` timestamp cluster, confirming one single historical migration/backfill
  batch wrote all of it, not ongoing production). This matches the "HL `perp_mark_price` (316 objs)" figure this plan's
  own archived source (`/plans/archive/2026_07/defi_dedicated_bucket_shared_migration_2026_07_13.md` Progress Log
  2026-07-13 entry (c)) already recorded — that "316" turns out to mean 316 DAYS/shards (not raw objects), the same
  mislabeling this doc's earlier entry already found and corrected for `perp_daily_ctx`'s "1,109" figure. **Reader
  check**: confirmed via direct grep of
  `strategy-service/strategy_service/engine/core/canonical_perp_funding_provider.py` and
  `canonical_dex_pool_provider.py` (the only two "Canonical*Provider" DeFi readers) that NEITHER references
  `perp_mark_price` — zero hits workspace-wide outside the dead writer script and one test fixture
  (`market-tick-data-service/tests/unit/scripts/test_migrate_defi_batch_to_per_instrument.py`). So unlike
  `perp_daily_ctx` (which has a live reader), `perp_mark_price` has NEITHER a live writer NOR a live reader — pure
  historical residue. Registered anyway per this doc's own established honest-coverage precedent (real captured rows
  should not be structurally invisible to the manifest just because nothing currently reads or writes them).
  **Shipped**: `unified-api-contracts` (`DATA_TYPES_BY_ASSET_GROUP["defi"]` + new `DEFI_PERPETUAL_PERP_MARK_PRICE`
  SchemaContract, mirrors `DEFI_PERPETUAL_PERP_FUNDING`'s 4 common columns + `mark_price` only;
  `NEEDS_CANDLE_PROCESSING["perp_mark_price"]=False`) via quickmerge. **Backfill**: new
  `unified-trading-pm/scripts/migration/register_perp_mark_price_manifest_backfill_2026_08_04.py` (mirrors
  `register_perp_daily_ctx_manifest_backfill_2026_08_04.py`'s structure, adapted for the non-contiguous shape — scans
  the full candidate window day-by-day instead of assuming contiguity) — dry-run then `--apply` both run against prod
  (`market-data-tick-defi-prd-central-element-323112`, `MANIFEST_PER_VM_SHARDS=true`): registered 316 manifest rows
  covering 22,690 real objects, 0 failures. Verified via a direct per-VM-shard read
  (`_index/per_vm/local-82973-c93a.parquet`): all 316 rows `capture_status=captured`, `row_count` sum 22,690 — matches
  discovery exactly.

- **2026-08-04 (data_engineering, executing `defi_satellite_ao_dispatch_batch6_2026_07_30.md` todo -010)**: Shipped the
  [CODE] P2 safe-alternative in full.
  1. **UAC registration** (`unified-api-contracts@17b1cf21`): `perp_daily_ctx` added to
     `DATA_TYPES_BY_ASSET_GROUP["defi"]`; new `DEFI_PERPETUAL_PERP_DAILY_CTX` SchemaContract (mirrors
     `DEFI_PERPETUAL_PERP_FUNDING`'s 4 common columns + `mark_price`/`day_ntl_vlm`/`open_interest`, the latter two
     nullable since the CeFi writer never populates them); `NEEDS_CANDLE_PROCESSING["perp_daily_ctx"]=False` (a
     pre-existing test parametrized over every `DATA_TYPES_BY_ASSET_GROUP["defi"]` entry required this).
  2. **Writer fix** (`features-service@c678f0fd`): real `ManifestWriter.add()` call added to `perp_funding_corpus.py`'s
     `perp_daily_ctx` write path — best-effort (a manifest-write failure never blocks the real parquet write, which has
     already succeeded by the time it runs), zero row-schema change. 2 new unit tests.
  3. **MTDS HL mark-price backfill script**
     (`market-tick-data-service/scripts/ backfill_hl_mark_price_from_s3_asset_ctxs_2026_06_17.py`): confirmed still
     present in the repo, but deliberately NOT touched — re-verified this session that its target bucket
     (`perp-funding-{project}`) is still gone (this doc's own fact #4), so its writer-half of the todo is moot, not
     skipped.
  4. **Historical backfill**
     (`unified-trading-pm/scripts/migration/ register_perp_daily_ctx_manifest_backfill_2026_08_04.py`, committed for
     audit trail): bounded, exact-prefix GCS discovery (never a whole-day/whole-corpus listing — a naive `day={D}/`
     prefix returns 5,000-26,000 objects across every asset_group/venue/data_type for that day, so this script lists the
     FULLY-QUALIFIED per-(day,venue) prefix instead, O(1) per call). Found the HYPERLIQUID `perp_daily_ctx` corpus spans
     EXACTLY 2023-05-20..2026-06-01 with zero gap days (1,109 calendar days — an EXACT match to this doc's own "1,109
     objects" figure once you realize that figure was counting shard-days, not the underlying ~22-to-230-per-day
     per-coin files this session found via direct content reads: the real object population is 169,412 HL files, one row
     each, plus a `_migrated_hyperliquid_*` consolidation-marker file per day that duplicates that same day's rows and
     was excluded from counting/registration to avoid double-counting). The 7 CeFi Tardis venues' 2026-05-16..22 window
     added another 49 `(day, venue)` rows (7 venues × 7 days), matching the "98 objs" residual-gap figure once split
     evenly between `perp_funding` and `perp_daily_ctx`. **Dry-run then `--apply` both run against prod**
     (`market-data-tick-defi-prd-central-element-323112`) — registered 1,158 `(day, venue)` manifest rows covering
     169,461 real objects, 0 failures. Verified via a direct per-VM-shard read
     (`_index/per_vm/local-64151-459f.parquet`): all 1,158 rows `capture_status=captured` with correct `row_count`s (21
     for the earliest day, 230 for the latest — matches the real per-day coin counts). Ran the manifest consolidator
     afterward — it hit a transient network `IncompleteRead` downloading the ~1.7GB canonical index and fell back to a
     shards-only computation it did NOT persist back to canonical (confirmed via blob metadata: the canonical index's
     `last_modified` timestamp predates this consolidator run, size unchanged — no data loss, no partial-write risk).
     The per-VM-shard reader fallback already surfaces the captured rows to any caller regardless of consolidator
     completion, per the established `defi_fold_manifest_registration_pending_2026_07_21.md` precedent, so this doesn't
     block closing out; a future consolidator run (standing cron or a follow-up session) will complete the merge
     normally. **Separate, real finding surfaced while verifying (out of this todo's scope, flagging per the
     data-correctness heartbeat rule)**: the HYPERLIQUID `perp_daily_ctx` corpus stops abruptly after 2026-06-01 — no
     objects exist for any day on/after 2026-06-02, and neither the retired backfill script (dead bucket) nor the live
     `perp_funding_handler.py` (confirmed, via direct grep, to never write `perp_daily_ctx` at all — only
     `perp_funding`) currently produces it. `CanonicalPerpFundingProvider` will silently return `mark_price=None` for HL
     going forward from that date (honest-absence by design, not a crash, but a real forward coverage gap for the
     funding-driven archetypes' mark price). Filed as its own tracked follow-up:
     `issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md` (out of this todo's own scope, so not
     resolved here).
- **na-eligibility-audit 2026-08-01**: KEEP-NA-STALE-DUPLICATE — re-verified: the [CODE] P2 half's AO-readiness (flagged
  2026-07-30) has since been realized via `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s verbatim extraction (same
  date, 2026-07-30) — see inline note above. Not reclassified (already dispatched elsewhere). The [OPERATOR-DECISION] P3
  item remains genuinely open/unresolved. Doc not archive-eligible until both resolve.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - carries an explicit [OPERATOR-DECISION] P3 todo; the [CODE] P2
  half is AO-ready but the doc cannot flip as a unit
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (6 entries, unchanged) — all six still resolve and remain the
  minimal set covering the open [CODE] P2 (tracked in batch6) and [OPERATOR-DECISION] P3 (derivative_ticker demote todo)
  items.

### 2026-07-28 — data_engineering (slot-6): data_type-axis denominator trace

Answers this doc's own P2 verify todo + `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s mirrored todo.

**Question**: does adding a data_type to `DATA_TYPES_BY_ASSET_GROUP["defi"]` (for an already-registered HYPERLIQUID/CeFi
venue×instrument_type combination) change `expected_unattempted` materialisation / `completeness_pct`, or is that
denominator scoped independently — mirroring RESULT 4's venue-axis finding in
`distinct_values_noncanonical_audit_2026_07_20.md`?

**Verdict — for the specific HYPERLIQUID/CeFi combos named in the source todo: NO, it does not change anything.** But
the axis is NOT scoped independently in general — the mechanism is real and would fire for genuine defi-asset-group
protocols. Read-only code trace, no code/schema/manifest changes made.

**Mechanism (unlike the venue axis, which routes indirectly through the catalogue, the data_type axis is consumed
DIRECTLY by the enumerator):**

- `instruments-service/scripts/enumerate_expected_universe.py:4145` —
  `data_types_list = [str(dt) for dt in DATA_TYPES_BY_ASSET_GROUP.get(asset_group, [])]` (the
  `"defi"`/`"cefi"`/`"prediction"` fallback branch), fed into `enumerate_v2(...)` (:4160) →
  `_row_data_types(asset_group, instr, data_types)` (defi path at :1482).
- Inside `_row_data_types` (:649-698):
  `valid = valid_data_types_for_venue_instrument_type(asset_group, instr.venue, instr.instrument_type)` (:681);
  `known_ag_dts = frozenset(DATA_TYPES_BY_ASSET_GROUP.get(asset_group.lower(), []))` (:696);
  `row_dts = [dt for dt in data_types if dt in valid or dt not in known_ag_dts]` (:698). So once a data_type is
  registered (→ "known"), it survives the filter only if `valid` includes it.
- For `asset_group == "defi"`, `valid` comes from `valid_data_types_for_venue_instrument_type`
  (`unified_api_contracts/registry/market_data_categories.py:1443-1517`), which narrows to the specific protocol's
  `PROTOCOL_CAPABILITIES[protocol].data_types` (:1487-1503), keyed off `venue.split("-", 1)[0]` — a registry entirely
  independent of `DATA_TYPES_BY_ASSET_GROUP`.
- **Conclusion on the general mechanism**: registering a new data_type in `DATA_TYPES_BY_ASSET_GROUP["defi"]` DOES
  expand the denominator / move `completeness_pct` for any real defi-asset-group protocol×instrument_type pair whose
  `PROTOCOL_CAPABILITIES` entry also lists that data_type — this axis is NOT independently scoped the way the venue axis
  effectively is; it is a direct enumerator input gated only by the protocol-capability allowlist.

**Why the HYPERLIQUID/CeFi combos specifically are unaffected**: `HYPERLIQUID` is registered in
`VENUES_BY_ASSET_GROUP["cefi"]` (`market_data_categories.py:360`, "On-chain CLOBs reclassified from DEFI" section), NOT
in `VENUES_BY_ASSET_GROUP["defi"]`. Its catalogue rows are therefore enumerated via the **CEFI** pass
(`_row_data_types("cefi", instr, data_types)` at `enumerate_expected_universe.py:1157`), whose candidate `data_types`
list is sourced from `DATA_TYPES_BY_ASSET_GROUP["cefi"]` — a completely separate dict key from `["defi"]`. Different
asset_group ⇒ different `data_types_list` ⇒ different `known_ag_dts` ⇒ different `valid` branch. So editing
`DATA_TYPES_BY_ASSET_GROUP["defi"]` alone touches zero HYPERLIQUID/CeFi shard tuples — it mints no new
`expected_unattempted` rows and moves no completeness_pct for them, full stop. (Note: a
`PROTOCOL_CAPABILITIES["hyperliquid"]` entry does exist, `capability_declarations/_defi.py:715-721`,
`data_types=["perp_funding", "oracle_prices"]` — but it is unreachable for enumeration purposes since HYPERLIQUID is
never iterated under the `"defi"` asset_group.)

**Implication for this doc's own gated P2 todo (below, "register `perp_daily_ctx` as its own canonical data_type")**:
the safe-alternative's step 1 is genuinely inert / operator-sign-off-free **only if `perp_daily_ctx` is registered
solely under `DATA_TYPES_BY_ASSET_GROUP["defi"]`** (as the todo literally asks) — because none of the affected
combinations (HYPERLIQUID, CeFi venues) enumerate under that key. It would NOT be inert if the registration instead
targeted `DATA_TYPES_BY_ASSET_GROUP["cefi"]` (the dict HYPERLIQUID/CeFi venues actually enumerate under) — that edit
would expand the cefi denominator for any cefi venue×instrument_type whose `valid_data_types_for_venue_instrument_type`
branch (cefi's own gating, not traced further here — out of this todo's scope) admits `perp_daily_ctx`, and would need
the same operator-gating precedent as RESULT 4's venue-axis finding.

Full trace performed by a dispatched read-only Explore sub-agent (Sonnet); no files edited in
instruments-service/unified-api-contracts/market-tick-data-service/features-service/strategy-service.

- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid — the only remaining open item
  is the `[OPERATOR-DECISION] P3` todo, gated on a still-open, separately-owned `[DESIGN] P1` decision in another doc;
  `[VERIFY]` and `[CODE]` are both already closed by citation. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — both `[CODE] P2` halves (perp_daily_ctx +
  perp_mark_price) are now DONE, so swapped the now-historical `defi_satellite_ao_dispatch_batch6_2026_07_30.md` pointer
  for `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md` — a sibling open issue on the same live reader
  (`CanonicalPerpFundingProvider`) discovered during this doc's own backfill work, more relevant to a future worker than
  the completed dispatch batch.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — sole open item remains an [OPERATOR-DECISION] on a
  linked canonicalisation design question; the other 3 items already closed with evidence.
