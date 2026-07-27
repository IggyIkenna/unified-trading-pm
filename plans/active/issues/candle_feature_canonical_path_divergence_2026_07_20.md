---
doc_type: issue
title:
  MDPS candle + features object paths diverge from their declared canonical templates — path≠declared-template,
  path≠manifest on data_type, non-canonical TradFi leaf ids, an empty-stem object, and a volatility writer that bypasses
  its own path SSOT
summary: >-
  Ground-truthed against real prod objects while building /data-pipeline-check-mdps + /data-pipeline-check-features.
  MDPS candle OBJECT paths do not match the template the writer's own SSOT declares — they omit the instrument_type=
  segment entirely and carry the SOURCE data_type (data_type=derivative_ticker) while the MANIFEST row for the same
  shard carries the AGGREGATED mdps_data_type_key (deriv_ohlcv_15m) and the normalised timeframe. So the documented
  path==manifest invariant does not hold on the data_type axis. Separately, TradFi candle leaves are non-canonical
  migration artifacts (E1AF0_C3200_migrated_20260418T131054Z.parquet) where CeFi leaves are correctly canonical
  (DERIBIT:PERPETUAL:BTC-PERPETUAL.parquet), and at least one object has a ZERO-LENGTH instrument stem
  (venue=CME/.parquet) which is a genuine data defect. On the features side the volatility writer bypasses its own
  declared path SSOT (get_data_sink built with no prefix=, so UTL emits day={D}/feature_group=/timeframe=/{u}.parquet at
  the BUCKET ROOT instead of under volatility/by_date/), and the UTL paths registry's delta_one entry is stale versus
  the real writer. None of this is silently accepted by the new skills — the canonical leg reports each divergence as
  content_check=non_canonical and collects them into a migration worklist — but the underlying writers need an operator
  ruling on which shape is canonical before a full-history backfill bakes the current shape into ~386
  serial-compute-days of new candles.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [market-data-processing-service, features-service, unified-trading-library, unified-api-contracts]
scope: [engineer, admin]
tags: [data-correctness, canonical, gcs-paths, manifest, candles, features, migration, mdps, volatility]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/archive/issues/candle_feature_canonical_path_divergence_history_part1_2026_07_25.md,
    /plans/archive/issues/candle_feature_canonical_path_divergence_history_part2_2026_07_25.md,
  ]
created: 2026-07-20
last_updated: 2026-07-25
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: data
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  measured 2026-07-20 by direct `gsutil ls` against market-data-tick-{cefi,tradfi,sports}-prd-central-element-323112
  while building the two data-pipeline-check skills; writer-side claims re-read from the actual writer code.
---

# Candle + feature object paths diverge from their declared canonical templates

> **Why this matters NOW**: derived candles are effectively greenfield (cefi 6 manifest rows, tradfi 139, prediction 168
> as of 2026-07-20) and a full-history candle backfill is ~386 serial-compute-days of work. Whatever shape the writer
> emits will be baked into the entire corpus. **Rule on the canonical shape BEFORE the big backfill runs**, not after.

## Measured evidence (real prod objects, not inferred)

```
# cefi — data_type is the SOURCE type; NO instrument_type= segment; leaf id IS canonical
gs://market-data-tick-cefi-prd-central-element-323112/processed_candles/by_date/day=2019-03-30/
  pipeline_mode=batch_tardis/timeframe=15m/data_type=derivative_ticker/venue=DERIBIT/
  DERIBIT:PERPETUAL:BTC-PERPETUAL.parquet

# tradfi — NO instrument_type=; leaf id is a MIGRATION ARTIFACT, not VENUE:TYPE:SYMBOL
gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2020-01-01/
  pipeline_mode=batch_databento/timeframe=15m/data_type=ohlcv_15m/venue=CME/
  E1AF0_C3200_migrated_20260418T131054Z.parquet

# tradfi — ZERO-LENGTH instrument stem (a genuine defect)
  .../timeframe=15m/data_type=ohlcv_15m/venue=CME/.parquet

# sports — a legitimately DIFFERENT root and shape (processed/, league_id=, bucketed.parquet); no processed_candles/ at all
gs://market-data-tick-sports-prd-central-element-323112/processed/by_date/day=.../data_type=.../
  league_id=.../timeframe=T-10m/bucketed.parquet
```

## Findings

1. **`instrument_type=` is absent from every MDPS candle object path** (cefi + tradfi), while the declared template (UTL
   `PATH_REGISTRY["processed_candles"].path_template`, and `config.get_processed_path`'s documented shape) includes it.
   Consistent across the corpus → this is the writer's de-facto shape, not sporadic corruption.
2. **path ≠ manifest on `data_type`.** The OBJECT carries the SOURCE `data_type` (`derivative_ticker`); the MANIFEST row
   for the same shard carries the AGGREGATED `mdps_data_type_key(src, tf)` (`deriv_ohlcv_15m`) plus the normalised
   timeframe (`24h`→`1d`). `market-data-processing-service/docs/GCS_PATHS.md:42` documents the `data_type={source}`
   object form, so the two SSOTs themselves disagree. **This is the ruling that's needed** (see Decision below).
3. **TradFi candle leaf ids are non-canonical** (`E1AF0_C3200_migrated_20260418T131054Z.parquet`) where CeFi's are
   correctly canonical (`DERIBIT:PERPETUAL:BTC-PERPETUAL.parquet`). TradFi candles appear to carry a one-off migration
   naming that never got canonicalised.
4. **At least one zero-length-stem object exists** (`venue=CME/.parquet`). A parquet with no instrument id cannot be
   attributed to a shard — a real defect, not a naming nit. Needs a corpus-wide count + purge/repair.
5. **`volatility` writer bypasses its own declared path SSOT.** `VolatilityFeatureWriter._upload_parquet` builds
   `get_data_sink(bucket=…, routing_key=…)` with **no `prefix=`**, so UTL's `_build_partition_path` emits
   `day={D}/feature_group={g}/timeframe={tf}/{underlying}.parquet` at the **bucket root** — missing the
   `volatility/by_date/` prefix that BOTH `volatility/io/writer.py::build_path` AND the UTL paths-registry `DataSetSpec`
   declare.
6. **UTL paths-registry `delta_one` entry is stale**: it declares
   `delta_one/by_date/day={date}/feature_group=/timeframe=/` (with `by_date/`, no version) while the real writer emits
   `delta_one/day={D}/feature_group={fg}/feature_group_version={N}/timeframe={tf}/{id}.parquet`.

## MEASURED 2026-07-20 (bounded day-prefix listings — NOT a corpus walk)

### (i) Zero-length instrument stems are ONGOING, not historical

| corpus                  | candle objects | empty-stem `/.parquet` | share |
| ----------------------- | -------------- | ---------------------- | ----- |
| cefi `day=2019-05-08`   | 56             | **14**                 | 25%   |
| cefi `day=2020-01-01`   | 3,318          | 0                      | 0%    |
| tradfi `day=2020-01-01` | 8,546          | 50                     | 0.6%  |
| cefi `day=2026-04-14`   | 20,734         | 168                    | 0.8%  |

Mechanism (read from `output_path_helpers.py::candle_output_filename`): a bundle written under an `underlying=`
partition for a data_type that is NOT in `CEFI_CHAIN_INSTRUMENT_TYPES` (e.g. DERIBIT `data_type=trades` grouped by
underlying) takes the `f"{instrument_id}.parquet"` branch, but a bundle has no single `instrument_id` → the stem is
EMPTY. Measured example:
`processed_candles/by_date/day=2019-05-08/pipeline_mode=batch_tardis/timeframe=15m/data_type=trades/venue=DERIBIT/underlying=BTC/.parquet`

**This is the chain-bundle rule leaking**: the operator's contract is "one bundled file per (date, root)" =
`ticks.parquet`. These objects are bundles that never got the bundled NAME because the data_type gate is keyed on
`{options_chain, futures_chain}` only, while the WRITER bundles by `underlying=` for more data_types than that. Fix
direction: make the bundled-name decision follow "is this write bundled by `underlying=`?", not "is the data_type in the
chain set". Objects with an empty stem cannot be attributed to an instrument and should be repaired or purged.

### (ii) BIG: candle objects exist WITHOUT manifest rows (object↔manifest disconnect)

cefi `day=2026-04-14` holds **20,734 candle objects**, yet the whole cefi availability index carries only **6** rows
with `service_name=="market-data-processing-service"` (measured via slim read, §B3 of the parent plan). A ~3,400×
disconnect on a single day. Consequences, all real:

- **skip-if-fresh is driven by the manifest** (`check_shard_freshness`) → it sees "not fresh" and RE-DERIVES candles
  that already exist, wasting the exact compute the ~386-serial-day backfill is trying to budget.
- **honest coverage / data-status** report candles as absent while 20k+ objects sit on disk — the "invisible by
  declaration" pattern the honest-coverage codex warns about, inverted.
- **features input-coverage** (and the new `/data-pipeline-check-features` `--require-captured`) will report
  `no_captured_input_for_window` for candle-dependent families even though the candles exist.

This is the INVERSE of `PHANTOM_CAPTURED_NO_OBJECT` (manifest row, no object): here it is object, no manifest row.
Root-cause it before the full-history backfill — either MDPS is not calling `record_captured` on these paths, or the
rows are stranded in un-consolidated per-VM shards.

### (iii) ADDENDUM 2026-07-20 — TWO structural candle shapes coexist on the SAME day + NO machine oracle governs candle paths

Two facts verified today by bounded `gsutil ls` + running the UAC oracle directly (not inferred):

**(iii-a) The writer emits BOTH a `pipeline_mode=`-partitioned shape AND a `pipeline_mode`-LESS shape into the same
bucket on the same day.** Under `market-data-tick-cefi-prd-…/processed_candles/by_date/day=2026-05-23/` BOTH of these
exist side by side:

```
# canonical-ish (has pipeline_mode):
  .../day=2026-05-23/pipeline_mode=batch_tardis/timeframe=15m/data_type=…/venue=…/…parquet
# ORPHAN (no pipeline_mode segment at all — timeframe= sits directly under day=):
  .../day=2026-05-23/timeframe=15m/data_type=ohlcv_15m/venue=COINBASE-SPOT/COINBASE-SPOT:spot_pair:BTC-USDT.parquet
```

This is a DISTINCT orphan class from Finding 1 (missing `instrument_type=`): here the `pipeline_mode=` partition segment
— required by `/codex/02-data/pipeline-mode-partition.md` and inserted by the driver's canonical model — is present on
some candle objects and absent on others **in the same bucket, for the same day**. A `pipeline_mode`-blind reader (glob
`day=*/timeframe=*/…`) and a `pipeline_mode`-aware reader (glob `day=*/pipeline_mode=*/timeframe=*/…`) therefore see
DIFFERENT, non-overlapping subsets of the same candle corpus — a silent split-brain over the candle estate. The leaf id
itself (`COINBASE-SPOT:spot_pair:BTC-USDT.parquet`) IS canonical (VENUE:TYPE:SYMBOL), so this is purely a STRUCTURAL
(partition-layout) orphan, not an id-form one.

**(iii-b) ROOT CAUSE of why candle divergence goes unchecked: the UAC canonical oracle does not cover the
`processed_candles/` namespace at all.** `unified_api_contracts.canonical.partition_paths.canonical_path_violations()`
hardcodes `RAW_TICK_DATA_PREFIX = "raw_tick_data/by_date/"` (`partition_paths.py:67`) and returns a `structural`
violation (`"path does not start with the canonical prefix 'raw_tick_data/by_date/'"`) for **every**
`processed_candles/` path — the canonical shape AND the orphan shape are BOTH flagged identically, so the oracle cannot
distinguish them. Verified by running `canonical_path_violations()` + `_classified()` on the two real objects above
(both `require_pipeline_mode` values): identical `structural` verdict for canonical and orphan alike.

Consequence: there is **no machine authority for derived-candle canonical shape** — only the PATH_REGISTRY template
(which itself lacks `pipeline_mode` and includes `instrument_type`, i.e. matches NEITHER shape on disk) plus the prose
pipeline-mode-partition rule. That is exactly why divergent shapes coexist unchecked, and why
`/data-pipeline-check-mdps`'s canonical leg has to re-implement the check (a JUSTIFIED exception to "never re-implement
the oracle" — the oracle simply doesn't cover this namespace). **The durable fix is to EXTEND the oracle to the
`processed_candles/` (and features) namespace** so the ratified candle shape (post A/B/C ruling) becomes
machine-checkable and the skill can call the oracle instead of a bespoke rule.

## ⚠️→✅ CORRECTED RULING 2026-07-21 (evening) — the codex SSOT contradicted the original Option-A framing; operator RE-DECIDED with full info

**Critical correction (workflow wq44d6bto, ground-truthed):** my original A/B/C framing treated the UTL registry
template (`registry.py:28`, which carries `instrument_type=`) as the SSOT. But the AUTHORITATIVE codex layout
`/codex/02-data/per-asset-group-bucket-layouts.md:166` defines cefi/tradfi/defi candles as
`processed_candles/by_date/day={date}/timeframe={tf}/data_type={dt}/venue={v}/{id}.parquet` — **NO `instrument_type=`
segment** (only PREDICTION shards by instrument_type). The current objects ALREADY match the codex. So the original
"Option A = fulfill the declared template" was WRONG — adding `instrument_type=` CONTRADICTS the codex + is a NEW
canonical definition, not a divergence fix. ALSO verified: the candle-path migration is a GENUINE GAP (NOT duplicative)
— every running `canonical-migration-*` VM is `raw_tick_data/`-scoped (column patching), no plan/VM/todo migrates candle
PATHS; and the aggregated key `deriv_ohlcv` appears NOWHERE in codex/plans.

**Operator RE-DECISION 2026-07-21 (with the corrected info):**

1. **`instrument_type=` → AMEND THE CODEX + ADD IT (full migration).** Deliberate new-canonical: candles get an
   `instrument_type=` segment for cefi/tradfi/defi too (consistency with raw_tick + prediction, instrument_type
   sharding). Requires amending `per-asset-group-bucket-layouts.md:166` FIRST, then the object migration.
2. **`data_type` axis → KEEP SOURCE on the path, ALIGN THE MANIFEST to match (source).** The object path keeps the
   SOURCE `data_type` (derivative_ticker/trades/dex_pool_swaps) — **NO data_type object rewrite** (drops the aggregated
   `deriv_ohlcv` idea, which isn't a codex concept anyway). Instead the MANIFEST writer records the SOURCE key so
   path==manifest (code-only). Existing aggregated manifest rows re-recorded as source during the migration's manifest
   pass.

**REVISED canonical candle shape (LOCKED):**
`processed_candles/by_date/day={date}/pipeline_mode={pm}/timeframe={tf}/data_type={SOURCE}/instrument_type={it}/venue={v}/{canonical_id}.parquet`
(the migration ADDS `instrument_type=` + normalises pipeline_mode/tf + fixes defects; it does NOT rewrite data_type.)

**FOLD INTO the master consolidated plan** (`master_data_canonicalisation_migration_catalogue_2026_06_07.md`) as a new
candle-path phase — NOT a parallel effort (per the check's recommendation). Coordinate with the running raw_tick cefi
fleet: DISJOINT prefix (processed_candles/ vs raw_tick_data/) so no object collision, but manifest-shard contention +
the pre-migration-drain rule mean the candle cutover is scheduled AROUND the raw-tick fleet's completion, not
mid-flight.

**The genuine DEFECTS are fixed under EITHER path** (empty stems, split-brain pipeline_mode-less dups, TradFi artifact
ids, volatility bucket-root — P2 done). The UTL foundation built earlier (template + `build_canonical_candle_path` +
`candle_read_prefixes`) is CORRECT for the revised shape (keeps instrument_type=, adds pipeline_mode=, data_type generic
= source) — held uncommitted, lands atomically with the MDPS writer.

**OPERATOR PRINCIPLE 2026-07-21 — coordinated all-surface upgrade + BACKWARD migration (no split canonicals):** the
`instrument_type=`-add + `data_type` source-alignment must be upgraded across ALL canonical-definition surfaces TOGETHER
in the coordinated landing — (1) **codex** (`per-asset-group-bucket-layouts.md:166` candle layout + any sibling candle
SSOT + the UTL registry template), (2) **docs/plans** (this issue + fold into the master consolidated catalogue), (3)
**manifest** (writer records SOURCE data_type going forward AND existing aggregated rows RE-RECORDED to source — a
backward manifest migration, not just forward), (4) **code** (writer + all readers), (5) **data** (existing ~10-20M
objects MIGRATED BACKWARD to add `instrument_type=`, not merely new objects born canonical). "Not just going forward,
always migrated backwards": every surface is reconciled for the WHOLE historical corpus, so no split-canonical state
lingers on old data, old manifest rows, or stale docs. This is the acceptance bar for closing the migration.

---

## (SUPERSEDED by the corrected ruling above) OPTION A first framing — kept for history

The operator chose **A** and explicitly directed: **"migrate data gcs paths and manifest"** — i.e. do the full breaking
migration, not just the writer. Scope now:

1. **Writer** emits the declared template:
   `…/timeframe={tf}/data_type={mdps_data_type_key}/instrument_type={it}/venue={v}/{canonical_id}.parquet` (add
   `instrument_type=`, use the AGGREGATED data_type so path==manifest, plus the `pipeline_mode=` segment).
2. **Readers** (blast radius — every candle path-globber: features `delta_one`/`volatility` loaders, ml, anything)
   update in lockstep or they silently miss the migrated corpus.
3. **Existing GCS objects** migrate old→new canonical paths (copy→verify→delete; prod deletes operator-authorised here).
4. **Manifest** populated/reconciled for the (migrated) candle shards (subsumes item-4 / todo 7 — path-independent
   keys).
5. **Genuine defects** fixed along the way: TradFi leaf ids, empty stems, split-brain `pipeline_mode`, volatility
   prefix.

Blast radius is being scoped by workflow BEFORE any code/data change (a missed reader = a silent corpus gap). Tracked in
the plan Progress Log. **Todo 1 RULED → A.** Todos 2-10 fold into the migration phases below.

### Phase-0 operator decisions RULED 2026-07-21 (workflow wvyttno6s scoped the migration as an 8-phase epic, ~10-20M objects)

1. **`pipeline_mode=` placement → ADD TO THE REGISTRY TEMPLATE (single SSOT).** Add `pipeline_mode=` to
   `unified-trading-library/…/config_interface/paths/registry.py:28` `processed_candles` `path_template` +
   `partition_keys`, so `build_path()` alone yields the correct shape and readers routed through it cannot silently
   drift. (Was: post-hoc string-insert in `config.py:144-145`.) Every reader + the oracle extension builds THIS shape.
2. **continuous_future slice → IN SCOPE (treat as canonical, don't break it).** It already carries
   `instrument_type=continuous_future` + aggregated `ohlcv_1m`; writer (`build_continuous_engine`) + reader
   (`delta_one/engine/orchestrator.py:606-609`) move in lockstep with the rest; the migration executor verifies/no-ops
   it (already canonical). Do NOT accidentally corrupt the CME roll path.
3. **Migration scope → FULL, ALL 4 AGs, ONE CAMPAIGN.** Writer+readers change for all AGs; DATA migration sequenced
   `defi → prediction → cefi → tradfi` (tradfi LAST — ~10^7, ~99% id-canonicalisation, quarantine unresolvable ids).
   Precise per-AG counts from a sanctioned Tier-2 spot-VM census before sizing the migration VMs.
4. **PURGE the old/bad forms too (operator 2026-07-21 "full migration and purging of old bad data forms").** The
   migration is copy→verify(crc32c)→**delete** — the delete IS the purge of the old-shape objects once the canonical
   copy is proven. ALSO purge the genuinely-bad objects: (a) zero-length-stem `venue=*/.parquet` (unattributable —
   delete/repair to `ticks.parquet`), (b) DEDUP the ~2x split-brain copies (same shard under `pipeline_mode=` AND naked
   `timeframe=`) to the single canonical copy, (c) UNRESOLVABLE TradFi artifact ids (`E1AF0_*_migrated_*` that
   `_renormalize_legacy_instrument_ids` cannot resolve) → QUARANTINE (never fake-canonicalise), operator-review before
   any quarantine-delete. All prod deletes are gated: canonical copy crc32c-verified present FIRST, dry-run + reconcile
   orphan gate + bucket snapshot BEFORE `--apply` (delete-safety + pre-migration-drain hard rules).

## Decision (ruled A — historical options kept for context) — which shape is canonical?

**(A) [RULED ✅] The declared template is canonical → migrate the writers.** Add `instrument_type=` to the candle object
path, use the aggregated `mdps_data_type_key` on the object path so path==manifest genuinely holds, canonicalise TradFi
leaf ids, and give volatility its declared prefix. Do it **before** the full-history backfill so the corpus is born
canonical; the existing corpus is small enough (cefi 6 rows) that migrating it is cheap. **Cost: a breaking
object-layout change — every reader that path-globs candles (features `delta_one`/`volatility` data loaders) must be
updated in the same change (blast-radius rule).**

**(B) The emitted shape is canonical → fix the declarations.** Update `PATH_REGISTRY`/`GCS_PATHS.md`/the volatility
`build_path` + registry to match what the writers actually emit, and drop the path==manifest claim on `data_type`.
Cheapest, no data migration, but it ratifies path≠manifest.

**(C) Split the difference**: ratify the emitted candle shape (B) but still fix the _genuine defects_ — TradFi
non-canonical leaf ids, the empty-stem objects, and the volatility bucket-root bypass.

Findings 3 and 4 are **defects under every option** and should be fixed regardless.

## Todos

- [x] 1. ✅ [DATA] P1. **Operator ruling on A/B/C** for the candle object-path shape — RULED 2026-07-21 (see "CORRECTED
      RULING" above): ADD `instrument_type=` (amend codex + full migration) + KEEP SOURCE `data_type` on the path, align
      the manifest to match. LOCKED shape documented; codex `per-asset-group-bucket-layouts.md:166` amended
      (`mdps@752eaff`).
- [x] 2. [DATA] P1. **[already covered by plans/active/candle_canonical_path_migration_execution_2026_07_24.md, see that
      doc for execution]** Corpus-wide count of **zero-length-stem** candle objects (`…/venue=*/.parquet`); purge or
      repair. These cannot be attributed to a shard. **P0 census counted them exactly 2026-07-22**: cefi
      `EMPTY_STEM_WITH_UNDERLYING`=2,576 + `EMPTY_STEM_WITHOUT_UNDERLYING`=2,198; tradfi
      `EMPTY_STEM_WITH_UNDERLYING`=428,792 (!) + `EMPTY_STEM_WITHOUT_UNDERLYING`=6,780; defi/prediction had none of this
      class. Repair itself is still **pending P7 `--apply`** (content-repair gated).
- [x] 3. [DATA] P1. **[already covered by plans/active/candle_canonical_path_migration_execution_2026_07_24.md, see that
      doc for execution]** Canonicalise **TradFi candle leaf ids** (`E1AF0_C3200_migrated_*` → `VENUE:TYPE:SYMBOL`) or
      rule the migration naming acceptable. **P0 census counted them exactly 2026-07-22**:
      `NEEDS_CONTENT_TRADFI_ID`=6,487,045 — **84.8% of the entire 7.65M-object TradFi corpus** needs content-read
      leaf-id repair, by far the dominant disposition class and the reason tradfi is sequenced LAST/hardest. **UPDATE
      2026-07-23 (post-P7/P8)**: `--apply` ran; the vast majority of this class did NOT auto-resolve and was routed to
      `CONTENT_REPAIR_UNRESOLVED_QUARANTINED` instead — P8's fresh independent enumeration + a targeted `_quarantine/`
      sanity check (712 day-prefixes, one sampled day hit a 5,000-object listing cap) confirms **~7.1M TradFi candle
      objects (93% of the original corpus)** are sitting in `_quarantine/`, safe/un-deleted but NOT canonically
      available to downstream readers. This is now the single largest open item in this doc by object count — needs
      either a real leaf-id resolution pass (read `E1AF0_*` parquet content, derive the true canonical id) or an
      explicit operator ruling to accept the loss and re-scope todo 3 to "won't fix." Not attempted in P8 (P8 was
      verification-only, no content reads/writes).
- [x] 4. ✅ [SCRIPT] P1. **volatility writer**: pass the declared `prefix=` to `get_data_sink` so output lands under
      `volatility/by_date/` per its own SSOT. Fixed + shipped `features-service@99d5554e`.
- [x] 5. ✅ [SCRIPT] P2. Reconcile the **UTL paths-registry `delta_one` entry** with the real writer — readers now
      dual-read via `candle_read_prefixes` (canonical + legacy, both pre/post-migration) rather than relying on a single
      hand-rolled template. Shipped `unified-trading-library` (staging-first landing) + `features-service@99d5554e`.
- [x] 6. ✅ [SCRIPT] P2. Re-point `/data-pipeline-check-mdps` + `/data-pipeline-check-features` canonical legs at the
      LOCKED template. Shipped `mdps@25ce29c37` + `features@d58b7760`, proven on real `-test-` infra — see Progress Log
      2026-07-22 entry below.
- [x] 17. ✅ [DATA] P2. **`pipeline_mode=batch_hyperliquid_rest`** — investigated + fixed. Confirmed a
      **duplicate/legacy alias, NOT a genuine new mode**: `batch_hyperliquid_rest` is the pre-R4 (2026-06-07,
      `/codex/02-data/pipeline-mode-partition.md`) glued-transport antipattern; a prior migration
      (`migrate_hyperliquid_rest_pipeline_mode_2026_06_17.py`) already renamed 19,361 `raw_tick_data/` objects to
      `batch_hyperliquid` but was scoped to `raw_tick_data/by_date` only, never `processed_candles/`, stranding 31,640
      real CEFI HYPERLIQUID candle objects (day=2023-11-01..2026-04-14) with the stale literal.
      `resolve_pipeline_mode_from_source` now maps the legacy literal to `PipelineMode.BATCH_HYPERLIQUID` via an
      explicit alias table (every OTHER unrecognized value still warns/defaults as before) — deliberately NOT a UAC enum
      addition (would resurrect the retired antipattern) and NOT a separate standalone GCS rename migration
      (unnecessary: P7 `--apply` already re-classifies + migrates these 31,640 objects normally, so fixing the resolver
      alone is sufficient). `mdps@6b9ee49`.
- [x] 18. ✅ [DATA] P3. **CEFI `QUARANTINE_CORRUPT` = 130,906 objects** — sampled + fixed, confirmed **systematic, not
      random**. 97.9% (128,218) share one reason: bare wire-exchange leaf ids (e.g. `BTCUSDT`) that
      `_renormalize_wire_cefi` already exists to resolve but was never wired in for CEFI (see todo 14, now also
      resolved) — new `NEEDS_CONTENT_CEFI_WIRE_ID` disposition routes them through content-repair instead. 2.1% (2,688)
      are a SEPARATE, newly-found class: 100% venue=KRAKEN-SPOT trades, whose pair symbol embeds a literal `/` (e.g.
      `ADA/USD`), spilling the canonical colon-delimited leaf id across an extra Hive segment and breaking the path
      parser before classification even ran — `_parse_candle_rel` now narrowly rejoins this one confirmed shape (a
      genuinely corrupt trailing segment still quarantines exactly as before). Both proven via regression tests using
      the exact ground-truthed real object shapes from the census. `mdps@6b9ee49`. **Not yet re-verified against a fresh
      live census** (P7's own `--apply` re-derives classification fresh per object rather than trusting the stale
      dry-run plan, so this isn't blocking, but the true residual QUARANTINE_CORRUPT count post-fix is unmeasured until
      P7 actually runs — don't assume it drops to exactly 130,906-128,218-2,688).

## How the new skills currently handle this (no silent acceptance)

`/data-pipeline-check-mdps` and `/data-pipeline-check-features` verify the **force/skip** legs against the writer's REAL
measured shape (so the pipeline mechanism is provable and every shard gets tested), and report each divergence from the
DECLARED template as a **separate** `content_check=non_canonical` verdict collected into a greppable
`## Migration worklist (canonical-shape gaps)` section. Three failure modes on one cell never collapse into one bit.
`rg 'non_canonical|content_check' <report>` yields the worklist.

> **⚠️ CORRECTION 2026-07-27 (slot-12) — this todo's own measurement methodology is the SAME "wrong vocabulary" mistake
> already root-caused for cefi in `plans/archive/issues/mdps_cefi_candle_manifest_never_emitted_2026_07_26.md`.** That
> doc found the cefi "0 rows, ever" verdict was produced by querying the aggregated `ohlcv_*` family instead of MDPS's
> actual `data_type=<SOURCE data_type>` + real `timeframe` axis (a deliberate, operator-ruled design). This todo's
> 2026-07-23 cross-AG table below (`cefi 6`, `defi 0`, `tradfi 73`, `prediction 168`) was almost certainly measured the
> same wrong way — re-verified DEFI directly this session (`read_availability_index` with
> `service_name= market-data-processing-service`, column-projected, no vocabulary filter): **7,913 real candle-manifest
> rows exist today** (`data_type=dex_pool_swaps`, real timeframes `15s/1m/5m/15m/1h/4h/1d`, ~1,129-1,133 each), not 0.
> So this todo's headline claim ("candle manifest was never systematically populated") is likely STALE for the
> going-forward emission path — genuine remaining gap, if any, is far smaller than the 20,734-vs-6 framing suggests and
> is probably now the SAME narrower class as `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` (PAST
> OOM-era orphans only), not a total non-population defect. **Not fully re-verified for cefi/tradfi/prediction this
> session** — do not close this todo on the DEFI spot-check alone; re-measure each AG with the correct vocabulary before
> flipping.

- [ ] 7. [DATA] P0. **Root-cause the object↔manifest disconnect** (20,734 cefi candle objects on 2026-04-14 vs 6 MDPS
      manifest rows corpus-wide). Either `record_captured` is not firing on the candle write path or per-VM shards never
      consolidated. Blocks trustworthy skip-if-fresh, honest coverage, and features input-gating. **MEASURED +
      CHARACTERIZED 2026-07-20** (direct pyarrow read of the consolidated
      `market-data-tick-cefi-prd-…/_index/availability_index.parquet`, 166 MB / **10,363,628 rows**): by `service_name`
      → `market-tick-data-service` 6.78M, `instruments-service` 3.47M, `None` 114,749,
      **`market-data-processing-service` = 6**. The 6 candle rows are all `date=2026-04-14`, all written
      `2026-04-16T15:25Z`, and **DEGENERATE**: `venue` is **empty**, `row_count` is **NaN**, exactly one row per SOURCE
      data_type (book_snapshot_5, derivative_ticker, futures_chain, liquidations, options_chain, trades). So this is not
      "some rows missing" — the candle manifest was **never systematically populated**; the 6 rows are a single one-off
      degenerate write (venue-less, un-joinable to any instrument), while the real corpus is 20,734 objects across
      multiple `pipeline_mode`s on that one day. Refined root-cause: the candle write path is not calling
      `record_captured` per (instrument×data_type×day) shard at all (NOT a consolidation-lag problem — the per-VM shards
      under `_index/per_vm/` that DO exist are `market-tick-data-service` raw-tick backfill shards, e.g. `cefi-aster-*`,
      not candle shards). **Consequence for the backfill ETA**: prod skip-if-fresh reads this manifest, so it will
      re-derive EVERY existing candle object (the skip optimization is moot in prod until candle-manifest population is
      fixed). NOTE for future agents — a naive `read_availability_index()` call can return 0 rows on a COLD first
      invocation (transient cache/download artifact); a clean re-run returns the full 10.36M (+~3,940 from the per-VM
      merge). The reader is NOT broken — do not chase a phantom reader bug; the real defect is candle-manifest
      under-population. **CROSS-AG CONFIRMATION 2026-07-23** (prompted by an operator question during P8 close-out: did
      the migration also clean up stale manifest entries? Checked directly — first confirmed the migration script itself
      contains ZERO manifest-writing code, only its own internal tracking TSV, so it could not have touched manifest
      state either way; then downloaded + queried all 4 buckets' `_index/availability_index.parquet` locally, filtering
      `service_name=="market-data-processing-service"`): **defi 0** rows (of 23,471,601 total) despite 1,123,415 live
      candle objects; **cefi 6** rows (of 10,581,647) — identical to the 2026-07-20 measurement above, unchanged by the
      migration, still the same degenerate `date=2026-04-14` one-off; **tradfi 73** rows (of 5,881,228), all with
      `instrument_type=''` (empty — pre-dates the migration's manifest re-key), despite 534,679 live candle objects;
      **prediction 168** rows (of 758,961), all `instrument_type='PREDICTION_MARKET'`/`captured`, despite 583,228 live
      candle objects. **Confirms this is a genuine, pre-existing, cross-AG gap** (not cefi-specific), and confirms the
      P6-P8 path migration neither created nor fixed it — there was nothing migration-adjacent to clean up because the
      manifest was never tracking the candle namespace to begin with. Skip- if-fresh is moot for candles fleet-wide, not
      just cefi, until this is fixed.
- [x] 8. ✅ [DATA] P1. **Fix the bundled-name rule** (going-forward writer): `candle_leaf_filename` now decides the leaf
      by "is this write bundled by `underlying=`?" (→ `ticks.parquet`) rather than the data_type-in-set check. Shipped
      `mdps@752eaff`. **Repair/purge of EXISTING empty-stem objects is still pending P5/P7** (backward migration).
- [ ] 9. [DATA] P1. **Split-brain candle layout** (addendum iii-a): the same cefi day (2026-05-23) holds BOTH
      `pipeline_mode=…/timeframe=…` and `pipeline_mode`-less `timeframe=…` candle objects. Quantify the corpus-wide
      split (how many days / objects lack the `pipeline_mode=` segment) and fold it into the A/B/C migration — a
      `pipeline_mode`-blind vs `pipeline_mode`-aware reader see disjoint subsets. Part of the same operator ruling (todo
      1), not an independent decision. **Pending P5 executor (dedup phase).**
- [x] 10. ✅ [SCRIPT] P1. Oracle extended for the candle namespace (`processed_candles/` — the features namespace
      remains out of scope, not attempted): `PROCESSED_CANDLES_PREFIX` + `_candle_path_violations()` +
      `require_candle_migration_complete=` on `canonical_path_violations`/`is_canonical`, validating the CORRECTED
      LOCKED shape (source `data_type`, `instrument_type=`/`pipeline_mode=` added, both suppressed by default during the
      migration window per taxonomy AE-6). `/data-pipeline-reconciliation`'s candle leg (§3h) re-pointed at the oracle.
      `unified-api-contracts@6329fc04`.

- [x] 11. ✅ [SCRIPT] P2. **`<ag>-candle-apply` category added** to `launch-canonical-migration-vm.sh` — shipped
      `deployment-service@3af1a67`. The real `--apply --quarantine --content-repair` (full mode) / `--dry-run` (dry
      mode) pass, distinct from the `-candle-census` category (always dry-run, no reachable apply). Adversarial
      self-testing (no subagent available — weekly agent-dispatch limit hit) caught 3 real bugs before any VM touched
      production: `DRY_RUN=true` never actually gated `gcloud compute instances create` for ANY category (fixed at the
      shared level — a real VM was silently created during a "preview", harmless only because that specific preview also
      happened to pass dry mode); the shard-suffixed vm_name overflowed GCE's 63-char limit for the longer category
      names; fixing that introduced an unbound-variable crash under `set -u` for non-sharded launches. 9 new regression
      tests. Full details in the history doc, part 2
      (`/plans/archive/issues/candle_feature_canonical_path_divergence_history_part2_2026_07_25.md`, "P7 launcher: new
      `<ag>-candle-apply` category" entry).
- [x] 12. ✅ [SCRIPT] P2. **SPOT-preemption resume checkpoint for `--apply`** — shipped `mdps@efa559a`. Per-shard
      checkpoint (`vm-logs/{vm}/MIGRATION_PROGRESS-shard{N}.json`, distinct from the day-frontier `PROGRESS.json`
      contract this migration has no date axis for): frontier advances ONLY over a contiguous prefix of checkpoint-SAFE
      outcomes (never `ERROR:*`/KEPT_SRC — a straggler PINS the frontier and is retried, never silently skipped);
      `enumeration_signature` is a full-content blake2b hash (not local mtime, which changes on every real VM restage
      after preemption); draining switched to completion-order (`as_completed`) so the cadence bound holds under a
      stalled object. Built + independently adversarially reviewed (3 lenses) via a workflow; caught 1 CRITICAL + 3
      HIGH/MEDIUM findings, all fixed with regression tests — full details in the history doc, part 1
      (`/plans/archive/issues/candle_feature_canonical_path_divergence_history_part1_2026_07_25.md`, "Todo 12 (resume
      checkpoint)" entry). **`deployment-service@0ed7cf5`** companion fix: `launch-canonical-migration-vm.sh` now pins
      `VM_NAME` + persists launch params on relaunch (the review's own 4th finding — without it the checkpoint could
      never be found after a real SPOT preemption of the actual launcher family).
- [ ] 13. [DATA] P3. `ProvisionalTargetIndex` keys lack a bucket component, so the split-brain COUNT (not the actual
      migration safety) can be inflated by cross-asset-group path coincidences — cosmetic, fix before trusting the
      corpus-wide "quantify the split" number (todo 9) precisely.
- [x] 14. ✅ [DATA] P3. **Resolved as a side effect of todo 18** — non-colon CeFi "bare wire" leaf stems now DO route
      through `_renormalize_wire_cefi` content-repair (new `NEEDS_CONTENT_CEFI_WIRE_ID` disposition) instead of
      QUARANTINE_CORRUPT. Confirmed: the TRADFI-only scope boundary was NOT intentional — `_renormalize_wire_cefi`
      already existed, was already imported into the script, and was simply never wired into the CEFI branch.
      `mdps@6b9ee49`.
- [ ] 15. [DOC] P3. `unified-trading-library`'s `build_canonical_candle_path()` docstring example still shows the
      SUPERSEDED "aggregated data_type" semantics (`data_type='deriv_ohlcv_15m'`) — not a functional bug (the function
      is value-agnostic), but could mislead a future maintainer into "fixing" the correct SOURCE-keyed callers. Update
      the docstring example to match the 2026-07-21 correction.
- [ ] 16. [SCRIPT] P3. Investigate why `CEFI:DERIBIT:trades:24h`'s force-leg MEASURED classification shows
      `off_template=29` (timeframe mismatch against the raw `"24h"` token) while the canonical leg still passes it —
      confirm whether the object path already writes `timeframe=1d` (making §3A's "RAW token" docstring stale the same
      way the data_type one was) or whether this is a genuine separate defect. Non-blocking; found during the todo-6
      real-infra verification 2026-07-22, `data_pipeline_e2e_check_mdps_2026_06_27.md`.
- [ ] 19. [SCRIPT] P2. **Fix `_copy_verify_delete()`'s retry-idempotency gap**
      (`migrate_candle_canonical_2026_07.py:794-831`) — a destination that exists but FAILS verification
      (`SIZE_MISMATCH_KEPT_SRC`/`CRC32C_MISMATCH_KEPT_SRC`) is never re-copied on a subsequent run (the copy is gated on
      `dmeta is None`), so this straggler class cannot converge no matter how many times the shard is re-run — proven
      via reproduction on CEFI's P7c apply (7/10 shards hit near-identical mismatch counts across two independent runs,
      2026-07-23). Fix: treat a verification-FAILED existing destination the same as an absent one (overwrite +
      re-verify), with tests proving it against a synthetic bad-destination fixture before trusting it on prod. Then run
      ONE surgical mop-up pass against CEFI's (and TRADFI's, if it hits the same class) residual objects. Source data
      was never at risk (`KEPT_SRC` never deletes source) — this is a script gap, not a data-safety incident. Full
      root-cause writeup in the history doc, part 2, "P7c: CEFI retry — another 3-shard SPOT preemption burst;
      ROOT-CAUSED..." entry
      (`/plans/archive/issues/candle_feature_canonical_path_divergence_history_part2_2026_07_25.md`).

## Progress Log

> **Full chronological narrative extracted 2026-07-25** to two companion docs (split because the combined narrative
> itself exceeded the 1000-line cap):
> `/plans/archive/issues/candle_feature_canonical_path_divergence_history_part1_2026_07_25.md` (2026-07-21 writer/reader
> lockstep + `-test-` gate proof + P0 census + P5 executor build + prep-risk items) and `_part2_2026_07_25.md`
> (2026-07-22/23 P6 drain → P7 per-AG SPOT `--apply` for DEFI/PREDICTION/CEFI/TRADFI → P8 cross-AG verify/reconcile).
> This section is a condensed summary of that history; read the two history docs for the full VM-by-VM / shard-by-shard
> operational detail.

**2026-07-21 — coordinated writer+reader lockstep landed.** UTL (`build_canonical_candle_path`/`candle_read_prefixes`

- `pipeline_mode=` registry template), MDPS (`mdps@752eaff` writer single-derivation + manifest SOURCE-key + empty-stem
  bundled-write fix + a bonus broken-bucket-resolution fix), features-service (`features@99d5554e` delta_one/volatility
  dual-read + the volatility prefix fix, todo 4), and unified-trading-api (`uta@8377c98` chart reader dual-read) all
  shipped, QG-green. Same day, the `-test-` gate ran (`/data-pipeline-check-mdps` force+skip+canonical): first attempt
  failed on a real regression (a `source=` manifest-write guard mismatch, fixed `mdps@2d720b4`), then PASSED — a real
  GCS object was ground-truthed carrying the exact LOCKED shape, path==manifest confirmed.

**2026-07-22 — todo 6 shipped** (the check scripts' own comparators were asserting the pre-migration shape — 2 more real
bugs found across MDPS + features-service, fixed `mdps@25ce29c37`/`features@d58b7760`, proven on real `-test-` infra).
**P0 census completed** across all 4 asset_groups via 4 parallel SPOT VMs (real GCS enumeration, not inferred): **~10.9M
candle objects total, `ORPHAN=0` on every AG** — full disposition table (MIGRATE / SPLIT_BRAIN_DUPLICATE /
QUARANTINE_CORRUPT / EMPTY_STEM / NEEDS_CONTENT_TRADFI_ID / CANONICAL_NOOP) is in the history doc. Prep-risk items
(todos 12, 14, 17, 18) shipped the same day, all adversarially reviewed. **P5 migration executor shipped**
(`mdps@6ce1a25`, 951 lines + 23 tests) — a 3-lens adversarial review caught a CRITICAL pre-prod bug (split-brain dedup
indices built per-shard, would have silently corrupted provenance metadata at scale) before any real object was touched.
**P6 drain + P7 apply started**: DEFI's 200-object `--apply` canary succeeded and was hard-verified on real GCS.

**2026-07-22/23 — P7 full per-AG `--apply` sequence, all 4 asset groups.** DEFI (1,131,814 objects, 1 straggler retry, 0
outstanding), PREDICTION (1,165,459 objects, clean first pass, 0 outstanding), CEFI (940,606 objects; survived 2
SPOT-preemption bursts; **149-object (0.0158%) permanent residual** — root-caused to a genuine retry-idempotency gap in
`_copy_verify_delete()`, now tracked as **todo 19**; source data never at risk), TRADFI (7,646,831 objects; survived 3
severe SPOT-preemption storms — 18/20 then 36/50 shards preempted in one zone-contention event — recovered on-demand
each time; **0 outstanding**, fully converged). Full VM names, shard tables, and preemption-recovery mechanics are in
the history doc.

**2026-07-23 — P8 cross-AG verify/reconcile: all 4 AGs independently confirmed CLEAN.** 4 parallel agents each ran a
fresh GCS enumeration + the migration script's own `--dry-run` classifier (not trusting `--apply`'s self-report).
`ORPHAN=0` and `sum(dispositions)==total` held on every AG. The one material finding: **TRADFI's gap between
P7-processed (7,646,831) and P8-live (534,679) is 7,112,152 objects (93.0%)** — independently verified (not just
inferred) to be sitting safely in `_quarantine/` pending leaf-id resolution. This is **todo 3** (already tracked, not a
new defect), now precisely quantified for the first time as a headline number rather than the P0 census's pre-execution
"84.8% needs content-read repair" estimate.

**Verdict (2026-07-23, closing the P6→P7→P8 phase): the canonical-PATH migration+purge is COMPLETE and independently
verified clean across all 4 asset groups** — 0 orphans, 0 malformed objects, every residual fully accounted for (CEFI's
149 = todo 19, TRADFI's ~7.1M = todo 3). **This issue doc stays `status: open`** — todos 2, 3, 7, 9, 13, 15, 16, 19
remain genuinely open content-level work, distinct from the path-migration infra lift this phase completed.
