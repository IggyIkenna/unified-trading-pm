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
  [../data_pipeline_check_mdps_features_2026_07_20.md, ../../codex/02-data/availability-manifest-and-data-status.md]
created: 2026-07-20
last_updated: 2026-07-20
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
— required by `codex/02-data/pipeline-mode-partition.md` and inserted by the driver's canonical model — is present on
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
`codex/02-data/per-asset-group-bucket-layouts.md:166` defines cefi/tradfi/defi candles as
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
- [ ] 2. [DATA] P1. Corpus-wide count of **zero-length-stem** candle objects (`…/venue=*/.parquet`); purge or repair.
      These cannot be attributed to a shard. **P0 census counted them exactly 2026-07-22**: cefi
      `EMPTY_STEM_WITH_UNDERLYING`=2,576 + `EMPTY_STEM_WITHOUT_UNDERLYING`=2,198; tradfi
      `EMPTY_STEM_WITH_UNDERLYING`=428,792 (!) + `EMPTY_STEM_WITHOUT_UNDERLYING`=6,780; defi/prediction had none of this
      class. Repair itself is still **pending P7 `--apply`** (content-repair gated).
- [ ] 3. [DATA] P1. Canonicalise **TradFi candle leaf ids** (`E1AF0_C3200_migrated_*` → `VENUE:TYPE:SYMBOL`) or rule the
      migration naming acceptable. **P0 census counted them exactly 2026-07-22**: `NEEDS_CONTENT_TRADFI_ID`=6,487,045 —
      **84.8% of the entire 7.65M-object TradFi corpus** needs content-read leaf-id repair, by far the dominant
      disposition class and the reason tradfi is sequenced LAST/hardest. Repair itself is still **pending P7 `--apply`**
      (content-repair gated).
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
      `codex/02-data/pipeline-mode-partition.md`) glued-transport antipattern; a prior migration
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
      under-population.
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

## Progress Log

### 2026-07-21 — coordinated code foundation LANDED (P1 writer + P3 readers), QG-green all 4 repos

The coordinated, held-uncommitted foundation described in the "OPERATOR PRINCIPLE" section above landed dep-ordered.
Every repo was QG-green (fresh sentinel against current HEAD — this host has heavy concurrent agent QG activity, so the
sentinel needed a re-run per repo each time HEAD advanced underneath it) before shipping.

- **`unified-trading-library`** — `build_canonical_candle_path` / `candle_read_prefixes` + `pipeline_mode=` in the
  `processed_candles` registry template. Landed via `quickmerge --agent` (staging-first routing for this repo).
- **`market-data-processing-service@752eaff`** — writer single-derivation (`build_canonical_candle_object_path` /
  `derive_candle_object_path`: adds `instrument_type=` + SOURCE `data_type` + `pipeline_mode=`); manifest records the
  SOURCE key; empty-stem bundled-write fix (todo 8); codex `per-asset-group-bucket-layouts.md:166` amended to the LOCKED
  shape. **Also closed the ONE gap the prior session flagged** (`build_continuous_engine.py`'s per-contract candle
  reader): now dual-probes canonical (`pipeline_mode=batch_databento` default + `instrument_type=FUTURE`) + legacy
  prefixes via `candle_read_prefixes`; the stitched continuous-future OUTPUT is now built through the same
  single-derivation UTL seam (it was missing `pipeline_mode=` entirely). **Bonus find while in that file**:
  `_resolve_tradfi_bucket()` called `resolve_bucket_name(kind="market-data-tick-tradfi")` — not a registered kind — so
  `run_build_continuous` raised on every invocation; the continuous-futures pipeline had never successfully run. Fixed
  to use the same `get_service_config().get_output_bucket_for_asset_group()` seam every other MDPS writer uses (also
  makes it `-test-`-routable, matching the writer's existing test-isolation contract). Shipped via the closed dirty-deps
  carve-out (UAC had live uncommitted venue-registry + quarantine WIP, mtime <120s, blocking quickmerge's pre-flight).
- **`features-service@99d5554e`** — `delta_one` + `volatility` readers dual-read via `candle_read_prefixes` (todo 5);
  `dependency_checker` drops `delimiter="/"` to walk the candle subtree; `continuous_future` slice confirmed intact. P2
  volatility sink-prefix fix (todo 4) landed in the same commit. Shipped via the same dirty-deps carve-out
  (`calendar_orchestrator.py`, a separate peer's live WIP in the same repo, was deliberately excluded from staging).
- **`unified-trading-api@8377c98`** — `batch_candles` chart/UI reader dual-reads via the same `candle_read_prefixes`
  SSOT. Shipped via the dirty-deps carve-out.
- **`deployment-service`** — coverage probe confirmed transparent to the `instrument_type=` insert (no code change
  needed, per the earlier scoping). While QG-ing this batch, found + attempted to fix an UNRELATED pre-existing parity
  gap (`configs/cloud-providers.yaml` missing the `alerting-service` bucket kind UAC's packaged copy already had —
  `test_sibling_copy_matches_packaged_uac_copy[deployment-service]` was failing on it) — a concurrent agent fixed the
  identical gap upstream in the interim, so this repo needed no commit from this session (verified via a clean
  `git diff HEAD` after reconciling the pull).

**Verification note (this host):** `bash scripts/quality-gates.sh --no-fix`'s SHA sentinel is invalidated the moment
`origin/live-defi-rollout` advances underneath it (the per-slot cron fast-forward-pulls every ~5 min, and this session
observed multiple OTHER concurrent `quality-gates.sh` processes for other repos/slots on the same host) — every
`quickmerge`/carve-out commit in this batch needed a **fresh** `quality-gates.sh --no-fix` run immediately before
staging, not the run from a few minutes earlier. Budget for this when landing a multi-repo batch on a busy host.

**NEXT (per the RESUME ORDER in `data_pipeline_check_mdps_features_2026_07_20.md`):** rebuild tarballs
(`refresh_code_tarballs.sh`) → verify the canonical shape on `-test-` via `/data-pipeline-check-mdps` (force+skip+
canonical, both axes) — THE GATE before any prod-data executor → then build the P5 migration+purge executor (todos 2/3/9
— census, tradfi-id quarantine, split-brain dedup) → P0 census + P6 drain/snapshot + P7 per-AG SPOT backward apply + P8
verify/reconcile.

### 2026-07-21 — ✅ THE GATE PASSED: writer proven emitting the LOCKED canonical shape on a real -test- VM (2 real bugs found + fixed along the way)

Ran `/data-pipeline-check-mdps` (force+skip+canonical) against CEFI:DERIBIT:trades on the rebuilt tarball
(`mdps@752eaff`). **First attempt failed with a real regression** (not the expected canonical-leg staleness): every
force-leg write errored `Multi-source manifest write missing required source= kwarg` (VM exit 1, 0 objects). Root cause
— `_resolve_candle_source_from_pipeline_mode`'s `has_source_priority`/`get_source_priority` lookup was keyed on the
AGGREGATED `mdps_data_type_key` (a computed key almost never registered in `SOURCE_PRIORITY`), but `record_captured`'s
own multi-source guard now evaluates `row_key["data_type"]` — the SOURCE type — since the coordinated manifest change.
cefi/trades has 6 registered `SOURCE_PRIORITY` sources (tardis first), so the writer's own guard rejected the write its
own source-resolver had just silently returned `None` for. **Fixed + shipped `mdps@2d720b4`** (dirty-deps carve-out):
re-keyed the lookup on `source_data_type`; moved the resolver to the shared `canonical_writer_shaping.py` and wired the
SAME fix into the streaming write path, which had NEVER passed `source=` at all (a pre-existing, independent gap the
SOURCE-key change made much more likely to bite). Verified directly:
`resolve_candle_source_from_pipeline_mode(CEFI, "trades", BATCH_TARDIS)` now returns `"tardis"` (was `None`).

**Re-ran on the re-rebuilt tarball — THE GATE PASSED.** 29/60 instrument×timeframe cells succeeded (217,679 candles
written); ground-truthed an actual object directly on GCS:

```
gs://market-data-tick-cefi-test-central-element-323112/processed_candles/by_date/day=2026-06-27/
  pipeline_mode=batch_tardis/timeframe=15m/data_type=trades/instrument_type=PERPETUAL/venue=DERIBIT/
  DERIBIT:PERPETUAL:BTC-USD@INV.parquet
```

— exactly the LOCKED shape (`instrument_type=` present, SOURCE `data_type=trades`, `pipeline_mode=` present). Read the
per-VM manifest shard directly via pyarrow for the same shard:
`data_type=trades, instrument_type=PERPETUAL, pipeline_mode=batch_tardis, capture_status=captured, row_count=96, source=tardis`
— **path==manifest holds exactly**, and `source=` resolved correctly (proves the fix). The remaining 31/60 failures are
a SEPARATE, PRE-EXISTING gap (`cefi/trades/FUTURE: ALL FAILED (31/31)` — CEFI has no registered candle SchemaContract
for standalone `instrument_type =future`, unrelated to path/manifest shape) — filed
`issues/cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md`, not blocking this gate. The `canonical`
leg still correctly reports `content_check=non_canonical` (todo 6, re-point the skill's declared-template comparator,
still pending — expected, not a failure of the writer).

**Gate verdict: the writer + manifest are proven correct on real infra. Proceeding to the P5 executor.**

### 2026-07-21 — P5 executor build dispatched (workflow); raw-tick fleet CHECKED — P6/P7 must wait for it

Dispatched a workflow (build agent + 3 parallel adversarial-review lenses — data-loss safety, dedup/shape correctness,
operational safety — + a conditional fix pass) to write
`market-data-processing-service/scripts/ migrate_candle_canonical_2026_07.py`, cloning
`market-tick-data-service/.../migrate_tradfi_canonical_2026_07.py`'s proven safety structure (dry-run default,
mapping-manifest + 0-orphan reconcile before any write, copy→verify→delete with the target==source no-delete guard,
per-object try/except isolation, sharding) while explicitly NOT cloning its `source→aggregated data_type` transform —
the candle migration's `data_type` axis is UNCHANGED (already SOURCE on existing objects, per the -test- gate proof
above); only `instrument_type=`/`pipeline_mode=` are added + the 3 genuine defects (empty-stem, TradFi leaf-id,
split-brain) repaired. Not yet reviewed/shipped — awaiting the workflow.

**Checked the running raw-tick fleet before considering P6/P7 timing**:
`gcloud compute instances list --filter="name~'canonical-migration-cefi'"` → **11 RUNNING / 7 TERMINATED (18 total)**,
so the fleet is well underway but NOT complete. Per the coordination note already in the master catalogue row (sequence
P7 AROUND the raw-tick fleet's completion, disjoint prefix but shared manifest-shard write contention): **P0 census / P6
drain / P7 apply are correctly BLOCKED-pending on this external fleet finishing, not something to force through now.**
This is a "cannot be done yet" deferral (elapsed time / external event), not a gap — re-check fleet status before
starting P6.

### 2026-07-21 — ✅ P5 executor SHIPPED (`mdps@6ce1a25`) — the adversarial workflow caught a real critical bug before it ever touched prod

`market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py` (951 lines) + a 23-test unit suite, cloning
`migrate_tradfi_canonical_2026_07.py`'s proven safety structure (dry-run default, mapping-manifest + 0-orphan reconcile
before any write, copy→verify→delete with the target==source no-delete guard, per-object try/except isolation, sharding)
while deliberately NOT reusing its `data_type` transform (candles keep SOURCE `data_type` unchanged — see the LOCKED
shape above). 8 disposition classes + the ORPHAN loud-failure bucket; genuine defects (empty-stem, TradFi leaf-id,
split-brain dedup) repaired in the same pass per todos 2/3/9.

**Built + reviewed via a workflow (build agent + 3 parallel adversarial lenses — data-loss safety, dedup/shape
correctness, operational safety — + a conditional fix pass), and it earned its keep**: all 3 lenses INDEPENDENTLY
converged on the same **CRITICAL** finding — `PipelineModeSiblingIndex`/`ProvisionalTargetIndex` (the split-brain dedup
indices) were built PER-SHARD using the same `--shard-of`/`--shard-index` filter as the classify/apply pass, but
`_stable_shard()` hashes each object's raw enumeration LINE TEXT, and a split-brain pair's two lines differ (one carries
an extra `pipeline_mode=X/` segment) — so under the script's own documented `--shard-of N` prod usage, a split-brain
pair lands in DIFFERENT shards with overwhelming probability. The sibling backfill would silently never fire, the
pm-less twin would fall back to the blind `BATCH_DATABENTO` default, and BOTH objects would migrate to DISTINCT,
one-mislabeled canonical paths — permanently duplicating the shard with corrupted provenance metadata, with the
reconcile's 0-orphan check never catching it (both twins individually resolve to a valid disposition). This is exactly
the class of silent-corruption-at-scale bug the adversarial-review step exists to catch before a real `--apply` run.

**Fixed in the same pass**: `build_pipeline_mode_sibling_index()` / `build_target_index()` no longer accept shard
parameters at all (the footgun removed at the signature level, not just one call site) — they always scan the full
unsharded enumeration; only the classify/apply passes stay sharded. 4 new regression tests added, including one that
hand-reconstructs the OLD buggy call pattern and asserts it DOES reproduce the bug (documents exactly what the fix
prevents). I additionally fixed 2 issues surfaced but not auto-fixed (medium/low severity, so outside the workflow's
auto-fix threshold): the crc32c verification was OPPORTUNISTIC (`if smeta.crc32c and dmeta.crc32c and ...`) rather than
REQUIRED, so a missing crc32c on either side would silently downgrade to a weaker size-only match — tightened to require
crc32c on both sides, never falling through to size-only; and a genuine `str | None` type-safety gap in the
content-repair path (now explicitly narrowed, never assumed). basedpyright: 0 errors. QG: ALL PASSED.

**Remaining findings NOT fixed (medium/low, tracked as follow-up, not blocking)**:

- [x] 11. ✅ [SCRIPT] P2. **`<ag>-candle-apply` category added** to `launch-canonical-migration-vm.sh` — shipped
      `deployment-service@3af1a67`. The real `--apply --quarantine --content-repair` (full mode) / `--dry-run` (dry
      mode) pass, distinct from the `-candle-census` category (always dry-run, no reachable apply). Adversarial
      self-testing (no subagent available — weekly agent-dispatch limit hit) caught 3 real bugs before any VM touched
      production: `DRY_RUN=true` never actually gated `gcloud compute instances create` for ANY category (fixed at the
      shared level — a real VM was silently created during a "preview", harmless only because that specific preview also
      happened to pass dry mode); the shard-suffixed vm_name overflowed GCE's 63-char limit for the longer category
      names; fixing that introduced an unbound-variable crash under `set -u` for non-sharded launches. 9 new regression
      tests. Details in the Progress Log below.
- [x] 12. ✅ [SCRIPT] P2. **SPOT-preemption resume checkpoint for `--apply`** — shipped `mdps@efa559a`. Per-shard
      checkpoint (`vm-logs/{vm}/MIGRATION_PROGRESS-shard{N}.json`, distinct from the day-frontier `PROGRESS.json`
      contract this migration has no date axis for): frontier advances ONLY over a contiguous prefix of checkpoint-SAFE
      outcomes (never `ERROR:*`/KEPT_SRC — a straggler PINS the frontier and is retried, never silently skipped);
      `enumeration_signature` is a full-content blake2b hash (not local mtime, which changes on every real VM restage
      after preemption); draining switched to completion-order (`as_completed`) so the cadence bound holds under a
      stalled object. Built + independently adversarially reviewed (3 lenses) via a workflow; caught 1 CRITICAL + 3
      HIGH/MEDIUM findings, all fixed with regression tests — see Progress Log below. **`deployment-service@0ed7cf5`**
      companion fix: `launch-canonical-migration-vm.sh` now pins `VM_NAME` + persists launch params on relaunch (the
      review's own 4th finding — without it the checkpoint could never be found after a real SPOT preemption of the
      actual launcher family).
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

**NEXT: P0 census** (Tier-2 spot VM, per the workspace's own census-and-compute-tiers rule — a full ~10-20M-object
enumeration + classification run must happen on sanctioned infra, never in-session) — **blocked on the raw-tick fleet
finishing** (checked above, 11/18 still running).

### 2026-07-22 — ✅ Todo 6 SHIPPED: the check scripts' OWN comparators were still asserting the pre-migration/superseded shape (2 real bugs beyond the known one, proven fixed on real `-test-` infra)

Re-checked the raw-tick fleet before picking up todo 6: down to **1/8 CEFI VMs RUNNING** (`wp21`, actively writing —
confirmed via serial-port gsutil activity every ~60s, not stalled); AWS side fully drained. Not yet fully drained, so P0
census stays blocked; picked up todo 6 as the highest-value unblocked item per the prior session's own recommendation.

**Traced the comparator code** (`market-data-processing-service/scripts/pipeline_e2e_check.py`) rather than assuming the
fix was purely doc-cosmetic, and found it was NOT — offline-probed the exact ground-truthed `-test-` object path from
the 2026-07-21 gate (`.../timeframe=15m/data_type=trades/instrument_type=PERPETUAL/venue=DERIBIT/…parquet`) directly
against `_measured_violations`/`_declared_violations` and confirmed **two real, currently-live bugs**, not one:

1. **Force leg (§3A MEASURED template) would have FALSE-FAILED every genuinely-migrated write.**
   `_MEASURED_CANDLE_SEGMENT_ORDER` didn't include `instrument_type` at all, so `_measured_violations` reported
   `unexpected_segments=instrument_type` on the exact object the writer now correctly produces — the object would land
   in `off_template`, never `matched`, meaning `write_verified=False` and the force leg's own pass predicate would fail
   on real, correct data. (§3A's docstring said "there is NO instrument_type= segment anywhere" — true on 2026-07-20
   when it was measured, stale since `mdps@752eaff`/`2d720b4` landed the writer fix.)
2. **Canonical leg (§3B DECLARED template) — the known one — plus its manifest lookups were ALSO broken.**
   `_declared_violations` compared `data_type` against the AGGREGATED `mdps_data_type_key()` instead of the shard's
   SOURCE data_type, so it reported `data_type=trades!=ohlcv_15m` on the exact LOCKED-shape object (a false
   `non_canonical`). `_manifest_match` and `_canonical_leg_ids` had the SAME bug on the manifest-row filter — since the
   manifest `data_type` column is now overridden to SOURCE right before `record_captured` (operator ruling 2026-07-21),
   filtering on the aggregated key silently matched **zero rows**, making the id-canonicality check vacuous rather than
   a real assertion.

**Fixed both, offline-verified the fix** (same ground-truthed object + a synthetic legacy/pre-migration sibling without
`instrument_type=`): the LOCKED object now passes `_measured_violations`/`_declared_violations` with zero violations;
the legacy object still passes `_measured_violations` (force leg stays green on either shape, by design) but
`_declared_violations` correctly reports exactly `missing_segment=instrument_type` — the P7 migration-worklist signal,
and nothing else (no more false `data_type` mismatch riding along). Added 6 regression tests (MDPS) covering both the
LOCKED-pass and legacy-still-flagged cases.

**Found the same root-cause bug a third time, in a third file, while checking `/data-pipeline-check-features`** (todo 6
named it too): `features-service/scripts/pipeline_e2e_check.py`'s `_is_canonical_input_row` required a candle INPUT
row's `data_type` to start with an aggregated prefix (`ohlcv_`/`book5_`/`deriv_`) to count as canonical — same
superseded assumption, would have flagged every genuinely-canonical candle input row (feeding
delta_one/multi_timeframe/cross_instrument) non-canonical. Dropped the `data_type` axis from that check entirely (the
manifest `data_type` is now SOURCE, permanently, not a migration-transient signal); `timeframe` presence + normalisation
remains the real signal. 3 new regression tests.

**Shipped**: `mdps@25ce29c37` via quickmerge (QG green, 67s, incl. a driver smoke re-import); `features@d58b7760` via
the closed **dirty-deps carve-out** (`unified-api-contracts` had live peer WIP, mtime <120s — protected, not touched; QG
green, 237s fresh sentinel immediately pre-commit). Also updated
`cursor-configs/skills/data-pipeline-check-mdps/SKILL.md`'s documented canonical contract to match (still needs its own
commit — see below).

**Proven on real `-test-` infra, not just offline** — ran `/data-pipeline-check-mdps` force+canonical for
`CEFI:DERIBIT:trades` day=2026-06-27 (same shard as the 2026-07-21 gate):
`plans/audit/results/data_pipeline_e2e_check_mdps_2026_06_27.md`. The force leg's own VM run itself hit a **known,
separately-tracked, unrelated** gap (`cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md` —
`cefi/trades/FUTURE: ALL FAILED (31/31)` in that shard's sub-dimension breakdown, dragging the overall VM exit code
to 1) — but the VM's own `run.log` shows it genuinely wrote **29/60 succeeded, 217,679 candles** (matching the
2026-07-21 gate's numbers exactly) before that unrelated failure. Critically, the **canonical leg does not depend on the
VM's exit code** (only needs a VM name to scan real `-test-` objects + the per-VM manifest shard), so it directly
exercised the fixed code on real data regardless:

- **7/7 canonical-leg cells PASSED** (`content_check=canonical`), migration worklist **EMPTY** — before the fix, every
  one of these would have shown `data_type=trades!=ohlcv_15m`.
- **6/7 cells' internal `_scan_cell` classification showed `on_measured_template=29, off_template=0`** — i.e.
  `_measured_violations` (the SAME function the force leg's pass predicate uses) found ZERO violations on 29 real,
  `instrument_type`-bearing objects — direct real-infra proof the force-leg fix (item 1 above) is correct too, not just
  offline-probed.
- **29/29 instrument ids checked, 29/29 canonical**, read via `checked per_vm_shard` — direct proof
  `_canonical_leg_ids`'s manifest-frame mask now correctly finds real rows filtered on SOURCE `data_type` (was silently
  vacuous before the fix).

**One minor observed nuance, NOT caused by this fix, not blocking, tracked as todo 16 below**: the `24h` timeframe cell
alone showed `on_measured_template=0, off_template=29` (all 29 objects landed off-template in the MEASURED
classification) while the canonical leg still correctly passed it. Not touched by today's data_type/instrument_type fix
— orthogonal to it — plausibly the object path already normalises `24h`→`1d` (contradicting §3A's own "timeframe is the
RAW token" documentation, which may itself now be stale the same way the data_type docs were). Didn't chase it further
this session; doesn't affect correctness (canonical leg's own `tf_canon` comparison already absorbs it).

- [ ] 16. [SCRIPT] P3. Investigate why `CEFI:DERIBIT:trades:24h`'s force-leg MEASURED classification shows
      `off_template=29` (timeframe mismatch against the raw `"24h"` token) while the canonical leg still passes it —
      confirm whether the object path already writes `timeframe=1d` (making §3A's "RAW token" docstring stale the same
      way the data_type one was) or whether this is a genuine separate defect. Non-blocking; found during the todo-6
      real-infra verification 2026-07-22, `data_pipeline_e2e_check_mdps_2026_06_27.md`.

### 2026-07-22 — ✅ P0 census COMPLETE, all 4 asset_groups, real GCS enumeration — ~10.9M total objects, ORPHAN=0 everywhere

Operator explicitly approved starting the **read-only** P0 census in parallel with the still-running raw-tick fleet
("start the read-only P0 census now in parallel, and hold P6/P7/P8 until wp21 finishes") — census is enumeration +
classification only (no writes/deletes to any AG data bucket), genuinely disjoint from the fleet's write path.

**Launcher wiring** (todo, new): `migrate_candle_canonical_2026_07.py` had no VM-launcher dispatch branch (todo 11's
gap). Built 4 new categories (`{cefi,defi,tradfi,prediction}-candle-census`) in
`deployment-service/scripts/vm/launch-canonical-migration-vm.sh` via a workflow (build agent + 3 parallel adversarial
lenses: no-mutation-safety / service-staging-correctness / bucket-scope-and-registry). The adversarial pass caught 2
real bugs before any VM ever launched: a **CRITICAL** wrong-bucket-name bug (`prediction-candle-census` targeted the
nonexistent `market-data-tick-prediction-*` bucket — real abbreviation is `pred` — would have silently produced zero
census output on every invocation), and a **HIGH** shell-injection path via the unquoted `WORKERS`/`TRADFI_TICK_BUCKET`
env vars in the VM-side `bash -c` execution (**pre-existing in this launcher file, affects every category, not just the
new ones** — closed globally with a positive-integer / bucket-name-shape validation gate). Verified via `bash -n` + a
`DRY_RUN=true` preview of the actual generated command string for both a normal and the previously-broken category.
Shipped `deployment-service@865d0f9`, QG green (97s).

**Launched all 4 as parallel SPOT VMs** (`cefi-candle-census`/`defi-candle-census`/`tradfi-candle-census`/
`prediction-candle-census`, each `--dry-run`-only against `gs://<AG tick bucket>/processed_candles/**`, `2020-01-01`/
`2026-07-22` cosmetic labels). Rebuilt VM-deployment code tarballs first (`refresh_code_tarballs.sh`) since the MDPS
tarball predated today's launcher work — confirmed via `git merge-base --is-ancestor` that the pre-refresh "stale"
tarball SHA already contained everything the census script needs (`6ce1a25`/`752eaff`/`2d720b4`), so the already-running
`defi` VM (launched before the refresh) was left alone rather than killed/relaunched. All 4 VMs completed in 4-25
minutes (`VM_SHUTDOWN_ON_COMPLETION=true`, self-deleted after finishing — **do not expect to find them in
`gcloud compute instances list`**, their evidence lives in GCS logs/staged output only), `exit_code=0` on every one.

**Full results** (source: each VM's `run.log` at
`gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-{cat}-candle-census-<ts>/run.log`; mapping
TSV + reconcile report staged to
`gs://deployment-scripts-central-element-323112/canonical-migration-candle-census/<ts>/canonical-migration-{cat}-candle-census-<ts>/mappings/`):

| Asset group    |  Total objects |   MIGRATE |   SPLIT_BRAIN_DUPLICATE | QUARANTINE_CORRUPT | EMPTY_STEM (with/without underlying) | NEEDS_CONTENT_INSTRUMENT_TYPE | NEEDS_CONTENT_TRADFI_ID | CANONICAL_NOOP | ORPHAN |
| -------------- | -------------: | --------: | ----------------------: | -----------------: | -----------------------------------: | ----------------------------: | ----------------------: | -------------: | -----: |
| **defi**       |      1,124,849 | 1,123,407 | 0 (folded into MIGRATE) |              1,442 |                                0 / 0 |                             0 |                       0 |              0 |  **0** |
| **prediction** |      1,165,459 |         1 |               1,165,458 |                  0 |                                0 / 0 |                             0 |                       0 |              0 |  **0** |
| **cefi**       |        940,606 |        10 |                 804,670 |            130,906 |                        2,576 / 2,198 |                           238 |                       0 |              8 |  **0** |
| **tradfi**     |      7,646,831 |         0 |                 724,214 |                  0 |                      428,792 / 6,780 |                             0 |               6,487,045 |              0 |  **0** |
| **TOTAL**      | **10,877,745** |         — |                       — |                  — |                                    — |                             — |                       — |              — |  **0** |

(`defi`'s disposition histogram reported `MIGRATE`/no separate split-brain line — its split-brain count folds into the
1,123,407 MIGRATE figure per the script's own histogram, unlike the other 3 AGs which break it out; the executor's own
"MIGRATE (incl. split-brain)" summary line confirms this convention.)

**Reading the numbers** — every AG's `ORPHAN count = 0 (PASS — total map)`, the executor's own hard safety invariant
(every enumerated object gets exactly one disposition or the run aborts loudly): this is the single most important line
in each report, and it held cleanly across ~10.9M real objects. Beyond that:

- **prediction is ~100% split-brain** (1,165,458/1,165,459) — virtually the entire prediction candle corpus exists as
  duplicate pipeline_mode-partitioned + pipeline_mode-less pairs. Dedup is effectively the WHOLE prediction migration.
- **tradfi is dominated by content-repair** (6,487,045/7,646,831 = 84.8% `NEEDS_CONTENT_TRADFI_ID`) — confirms the
  LOCKED plan's own sequencing rationale ("tradfi LAST — ~99% id-canonicalisation"); P7 for tradfi will spend the vast
  majority of its time doing parquet content reads + `_renormalize_legacy_instrument_ids`, not path-only rewrites.
- **cefi's 13.9% QUARANTINE_CORRUPT rate is anomalously high** vs defi's 0.13% — filed as new todo 18, worth sampling
  before quarantining 130,906 objects at scale in case it's a fixable systematic bug rather than true garbage.
- **A genuinely new finding, not previously known**: cefi's `run.log` surfaced live WARNINGs for an **unregistered
  `pipeline_mode=batch_hyperliquid_rest`** value, silently defaulting to `BATCH_DATABENTO` in `canonical_writer.py` —
  filed as new todo 17, should be resolved before P7 backfills those objects' siblings with the wrong mode.
- **defi and cefi both show `CANONICAL_NOOP` near-zero (0 and 8)** — confirms the corpus really is "born non-canonical"
  as the original issue framed it; essentially nothing was already on the LOCKED shape before this migration.

**Raw-tick fleet ALSO fully drained during this work** (checked 2026-07-22, after the census): `wp21` (the last VM, 1/8
running as of the previous check) is gone entirely from `gcloud compute instances list` — self-deleted after completion,
same as the census VMs. **This means the fleet-drain condition that was blocking P6/P7/P8 is now satisfied** — but per
the operator's explicit instruction this session ("hold P6/P7/P8 until wp21 finishes"), P6 (drain/snapshot) and P7 (the
actual destructive backward-migration `--apply`) are NOT started without a fresh operator go-ahead, since P7 is
genuinely destructive (copy→verify→**delete** across ~10.9M objects) and deserves its own explicit authorization
checkpoint even though the technical blocker has lifted.

### 2026-07-22 — ✅ Prep work COMPLETE: todos 12/14/17/18 all shipped — operator authorized P6→P7→P8 pending this prep

Operator gave explicit go-ahead this session for the full P6→P7→P8 sequence, conditioned on resolving the prep risk
items first ("resolve prep risks first, then P6→P7→P8"). All three (four, counting todo 14 as a free side effect of
todo 18) are now shipped, real-infra-test-proven where applicable, and QG-green.

**Todo 12 (resume checkpoint)** — built via a workflow (build agent + 3 parallel adversarial lenses: data-loss safety,
resume correctness, operational safety) before touching production. The review caught real, concrete bugs, not style
nits: (1) HIGH/CRITICAL (found independently by 2 lenses) — the checkpoint frontier advanced past `ERROR:*`/KEPT_SRC
outcomes exactly like a real success, so a transient GCS failure or crc32c mismatch would be checkpointed as "done" and
silently, permanently skipped on every future resumed/re-run invocation — a genuine regression versus the pre-diff
behavior (a plain re-run always retried a straggler from line 0). (2) HIGH — `enumeration_signature` fingerprinted the
local enum file via `(size, mtime_ns)`; a real SPOT preemption relaunches on a FRESH VM that re-stages the same file
with a NEW mtime, so the signature would mismatch and the shard would replay from line 0 on every single preemption —
the checkpoint would work in every synthetic test but never actually help in the one scenario it exists for. (3) MEDIUM
— `ThreadPoolExecutor.map()`'s submission-order result consumption meant the checkpoint's advertised "~500 objects at
risk" cadence bound didn't actually hold under a stalled object. (4) HIGH (operational-safety lens, cross-repo) — the
checkpoint is keyed by `VM_NAME`, but the actual production launcher
(`deployment-service/scripts/vm/launch-canonical-migration-vm.sh`) regenerates a fresh `RUN_TS`-derived name on every
invocation and never calls `lc_write_launch_params`, so a real preemption relaunch (automatic OR manual) could never
find the checkpoint the preempted VM wrote — the whole mechanism would be dead weight for the one launcher family that
matters. All 4 fixed with regression tests (mirroring `launch-mdps-backfill-vm.sh`'s proven `VM_NAME_OVERRIDE` +
launch-param-persistence pattern for finding 4). Shipped `mdps@efa559a` + `deployment-service@0ed7cf5` (both via the
closed dirty-deps carve-out — `unified-api-contracts` had live peer WIP both times), fresh QG green on both repos.

**Todos 14/17/18 (classifier fixes)** — the follow-on workflow to BUILD these fixes hit the account's weekly
agent-dispatch limit (all 3 subagents errored immediately, zero work done, `resets Jul 24 8pm London`) after the
read-only investigation phase had already completed successfully with strong, evidenced findings. Rather than wait ~2
days, did the implementation directly (no subagents) using the same investigation evidence:

- **Todo 17**: confirmed `batch_hyperliquid_rest` is a duplicate/legacy alias of `batch_hyperliquid`, NOT a genuine new
  pipeline_mode (would have resurrected the R4-retired glued-transport antipattern if registered in UAC). Root cause: a
  prior migration (`migrate_hyperliquid_rest_pipeline_mode_2026_06_17.py`) fixed `raw_tick_data/` but was never scoped
  to `processed_candles/`, stranding 31,640 real CEFI HYPERLIQUID candle objects. Fixed
  `resolve_pipeline_mode_from_source` with an explicit legacy-alias table — sufficient on its own (no separate GCS
  rename migration needed) since P7 `--apply` will re-classify + migrate these objects normally anyway.
- **Todos 14 + 18**: confirmed the CEFI `QUARANTINE_CORRUPT` over-classification (128,218 of 130,906, 97.9%) was a
  simple wiring gap — `_renormalize_wire_cefi` already existed, was already imported, was simply never called for CEFI's
  classify branch (only TRADFI was wired). New `NEEDS_CONTENT_CEFI_WIRE_ID` disposition closes it. Separately found +
  fixed a genuinely NEW class (2,688 KRAKEN-SPOT objects, not previously tracked): a literal `/` embedded in the pair
  symbol (e.g. `ADA/USD`) broke Hive-path parsing outright — `_parse_candle_rel` now narrowly rejoins this one confirmed
  shape.
- Both real-object shapes were ground-truthed directly against the P0 census's staged CEFI mapping TSV
  (`gs:// deployment-scripts-central-element-323112/canonical-migration-candle-census/20260722-031920/.../candle_census_ mapping.tsv`)
  before writing any code, and proven via regression tests using those exact shapes. Hit + fixed one self-inflicted lint
  failure along the way (`_resolve_path_only` cyclomatic complexity 16>15 from the added CEFI branch — resolved by
  factoring the TRADFI/CEFI dispatch into a small `_LEAF_STEM_CONTENT_REPAIR_KIND` mapping). Shipped together as
  `mdps@6b9ee49` (dirty-deps carve-out again), fresh QG **fully green** (a concurrent peer fixed the pre-existing
  unrelated `seed_mock_data.py` baseline overage mid-session, so unlike the todo-12 ship this one hit zero pre-existing
  noise).

**Also recovered dangling evidence**: this issue doc's own todo-6 Progress Log entry (2026-07-22, earlier this session)
cited `plans/audit/results/data_pipeline_e2e_check_mdps_2026_06_27.md` as evidence, but that file was never actually
committed — found uncommitted in the working tree during this session's routine `git pull` (autostash-pop surfaced it).
Committed alongside this doc update so the citation isn't dangling for a fresh clone.

**Residual, explicitly non-blocking**: the true post-fix CEFI QUARANTINE_CORRUPT count is unmeasured (a fresh dry-run
census re-run would confirm it quantitatively, but P7's own `--apply` re-derives classification fresh per object rather
than trusting a stale plan, so this doesn't gate starting P7 — just don't assume the residual count is exactly
`130,906 - 128,218 - 2,688`).

### 2026-07-22 — ✅ P6 DONE, P7 STARTED: operator authorized full P6→P7→P8, `/autonomous` invoked, DEFI real `--apply` canary SUCCEEDED (200/200 MIGRATED, hard-verified on real GCS)

**Governing authorization** (do not re-ask, per `/autonomous`'s rule 2 — decide and document): operator's exact
instruction this session — _"do this stop all VMs both clouds → snapshot → sequenced SPOT --apply migration+purge across
~10.9M objects, defi→prediction→cefi→tradfi → verify/reconcile"_ — followed immediately by `/autonomous` (apply
`cursor-configs/AUTONOMOUS_AGENT_RULES.md` + drive to completion on a loop, full authority for the infra ops this plan
labels operator, never stop at the first natural break). This is the standing authorization for everything below and
everything still to come (P7 for prediction/cefi/tradfi, P8) — a fresh session should NOT re-request confirmation for
continuing this exact sequence.

**P6 drain — scope decision (documented per rule 2, not asked)**: "stop ALL VMs both clouds" was interpreted as scoped
to VMs that write to/read the 4 target asset_groups' data (defi/prediction/cefi/tradfi), not the entire compute fleet —
stopping e.g. `footystats-fwd-*` (sports, disjoint `processed/` root) or `vm-zombie-watchdog-*` (fleet health
monitoring) would be over-broad and outside this migration's actual write-contention concern. AWS side: confirmed via
`aws ec2 describe-instances` — only `agent-orchestrator-vm-1` and `agent-orch-human-planning-vm` running, both
orchestrator infra, zero data-pipeline VMs — AWS was already clear. GCP side, stopped (via
`gcloud compute instances stop`, confirmed TERMINATED before proceeding): `canonical-migration-defi-per-instrument-*`
(DEFI raw-tick migration, writes DEFI manifest), `pyth-lst-backfill-*` (CEFI raw-tick backfill),
`datapoint-validation-tradfi-*`, `orphan-sweep-{cefi,defi,prediction}-*` (read-only reconciliation sweeps, stopped
anyway for a clean baseline).

**LESSON — the drain is NOT durable across a multi-hour operation**: re-checked GCP ~1h after the initial drain and
found several of the same VMs had respawned — `canonical-migration-defi-per-instrument-20260722-164109`,
`orphan-sweep-defi-20260722-161453`, `datapoint-validation-{cefi,defi,prediction}-20260722-15xxxx`,
`pyth-lst-backfill-20260722-151120`. Investigated: these are on independent scheduled crons (~7-11h cadence based on the
gap between the stopped instance and its respawn), NOT a watchdog "undoing" the manual stop (a plain
`gcloud compute instances stop` is not a SPOT-preemption event, so `RelaunchPreemptedVm`'s auto-recover path does not
fire on it). **Adopted a just-in-time re-drain pattern**: re-check + re-stop the in-scope VMs immediately before each
AG's real launch, rather than assuming one upfront drain holds for the whole multi-AG sequence. Residual risk is
accepted as low (disjoint object prefixes vs `processed_candles/`, per-VM manifest shards, and the candle migration's
own copy-verify-delete is idempotent/crc32c-verified regardless) but NOT zero — flagging explicitly rather than silently
assuming perfect isolation. Re-drained DEFI-specifically before the P7a launch below.

**P6 manifest consolidation**: triggered the 4 relevant Cloud Run jobs directly
(`gcloud run jobs execute uts-prod-manifest-consolidator-market-data-{defi,prediction,cefi,tradfi} --region=asia-northeast1`),
polled each to a terminal state (not fire-and-forget) — all 4 `Completed/True`, tradfi (largest) took ~5m40s, the other
3 finished within ~2min. "Snapshot" in the pre-migration-drain sense (per
`codex/02-data/gcs-and-manifest-delete-safety- protocol.md` §"Pre-delete drain") is satisfied by drain+consolidate; the
migration executor's OWN safety model (dry-run classify + 0-orphan reconcile before any write, copy→verify→delete never
deleting without a proven distinct verified copy) is the actual delete-safety mechanism, not a separate storage-level
snapshot action.

**P7 launcher: new `<ag>-candle-apply` category, 3 real bugs found + fixed via adversarial self-testing** (no subagent
available this segment — the workflow tool's weekly agent-dispatch limit was hit earlier this session, resets 2026-07-24
20:00 London; did this directly instead of waiting). Full details + exact bug mechanics are in the commit message
(`deployment-service@3af1a67`) and the 9 new `TestCandleApplyCategory` regression tests
(`deployment-service/tests/unit/test_vm_launcher_scripts.py`). Summary: (1) `DRY_RUN=true` never actually gated the real
`gcloud compute instances create` call for ANY category in this launcher, ever — a defi-candle-apply DRY_RUN=true
"preview" during testing silently created and ran a real VM (harmless only because that specific preview also happened
to pass `dry` mode internally); (2) the shard-suffixed vm_name for the longer `<ag>-candle-apply` names overflowed GCE's
63-char limit (measured worst case: `prediction-candle-apply` + 2-digit shard → 71 chars, GCE rejected the create call);
(3) fixing (2) introduced a `set -u` unbound-variable crash on the non-sharded single-VM launch path. All caught + fixed
BEFORE any real production object was touched.

**DEFI real `--apply` canary — ✅ SUCCEEDED, hard-verified on real GCS.** VM
`canonical-migration-defi-cdlap-20260722-175209` (zone `asia-northeast1-c`, self-deleted on completion per
`VM_SHUTDOWN_ON_COMPLETION=true` — will not appear in `gcloud compute instances list`), launched with
`LIMIT=200 SHARD_OF=1` + explicit SHA pins for reproducibility (`MDPS_TARBALL_SHA=c64a7dfa9d9f0689e...`,
`UAC_TARBALL_SHA=c4e1acee147a53aaf...`, `UTL_TARBALL_SHA=b0ec1da02c5fe7dfd...` — full SHAs in the commit that launched
it). Terminal `EXIT_STATUS=0`; `run.log` shows `apply COMPLETE — outcomes: {'MIGRATED': 200}` /
`shard 0/1 fully migrated cleanly (0 non-success outcomes)` — every one of the 200 sampled objects was MIGRATE
disposition (matches DEFI's census profile: overwhelmingly MIGRATE, near-zero quarantine/content-repair) and succeeded.
**Independently hard-verified** (not just trusting the script's own log) by reading the staged mapping TSV
(`gs://deployment-scripts-central-element-323112/canonical-migration-candle-apply/20260722-175209/.../ candle_apply_mapping.tsv`)
and directly `gsutil stat`-ing one real object pair on production GCS: the NEW canonical path
(`.../data_type=dex_pool_swaps/instrument_type=POOL/venue=BALANCER-ARBITRUM/BALANCER-ARBITRUM:POOL:0xd897... .parquet`)
exists (created 2026-07-22T16:59:36Z); the OLD non-canonical path (same but missing `instrument_type=`) returns "No URLs
matched" — genuinely copy→verify→delete happened, not just log claims. **DEFI's full corpus `--apply` (no LIMIT,
sharded) has NOT been launched yet** — that is the next concrete action, not yet started.

**Prior real-infra proof for DEFI** (already established earlier this session, not re-litigated): the same launcher
category in `dry` mode (accidentally launched during earlier bug-hunting, VM
`canonical-migration-defi-cdlap-20260722-162220`) ran a full real dry-run classify pass over the ENTIRE DEFI corpus and
reproduced the P0 census numbers EXACTLY (1,124,849 total, 1,123,407 MIGRATE, 1,442 QUARANTINE_CORRUPT, 0
CANONICAL_NOOP, ORPHAN=0) — confirms the classify logic is stable/reproducible and DEFI's corpus is clean (no
content-repair needed, minimal quarantine), independent of the LIMIT=200 apply canary's own result.

## Deferred work after 2026-07-22

| #   | Item                                                                                                                                                                                                                                                                                                                                          | State / why deferred                                                                                                                                                                                                                                      | Blocked-on                                                                       |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 1   | ~~P0 census~~ **DONE 2026-07-22** — all 4 AGs, ~10.9M objects, ORPHAN=0 everywhere (see Progress Log entry above for the full disposition table)                                                                                                                                                                                              | Shipped (`deployment-service@865d0f9` launcher + 4 real SPOT VM runs; results in GCS, not in git — see Progress Log for exact paths)                                                                                                                      | —                                                                                |
| 2   | ~~Todos 12/14/17/18 (prep risk items)~~ **DONE 2026-07-22** — resume checkpoint (adversarially reviewed, 4 findings fixed) + CEFI wire-symbol/KRAKEN-SPOT classifier fixes (see Progress Log entry above)                                                                                                                                     | Shipped `mdps@efa559a`/`deployment-service@0ed7cf5`/`mdps@6b9ee49`, all QG-green                                                                                                                                                                          | —                                                                                |
| 3   | ~~P6 drain/snapshot~~ **DONE 2026-07-22** — see Progress Log entry above (AWS pre-clear, 6 GCP VMs stopped, 4 manifest consolidators run to terminal)                                                                                                                                                                                         | Done, but NOT durable across the whole multi-AG operation (recurring crons respawn) — re-drain per-AG just before each real launch                                                                                                                        | —                                                                                |
| 4   | ~~DEFI `--apply` canary (LIMIT=200)~~ **DONE 2026-07-22** — 200/200 MIGRATED cleanly, hard-verified on real GCS (see Progress Log entry above)                                                                                                                                                                                                | Shipped, proven — the P7 mechanism works end-to-end on real production data                                                                                                                                                                               | —                                                                                |
| 5   | ~~DEFI + PREDICTION full `--apply`~~ **DONE 2026-07-22** — DEFI: run 1 (1,131,814 objects, 211 transient-503 stragglers) + idempotent retry, 0 non-success. PREDICTION: 1,165,459 objects, clean on first pass, 0 non-success. Both hard-verified via real `gsutil stat`. **CEFI → TRADFI `--apply`, then P8 verify/reconcile** still pending | DEFI + PREDICTION fully migrated+purged, 0 outstanding legacy-path candle objects in either bucket. CEFI/TRADFI not started. Proceeds under the SAME standing `/autonomous` authorization (no new operator ask needed)                                    | Nothing — start CEFI JIT-redrain (prefix-aware) then launch its full `--apply`   |
| 6   | Todo 13 (`ProvisionalTargetIndex` bucket-key precision — cosmetic split-brain COUNT inflation) + Todo 15 (stale UTL docstring example)                                                                                                                                                                                                        | **Not done** — P3, cosmetic, doesn't affect migration safety                                                                                                                                                                                              | nobody — pick up any time, not on the critical path                              |
| 7   | `cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md` (CEFI has no registered candle SchemaContract for standalone `instrument_type=FUTURE`)                                                                                                                                                                                  | **Not done** — orthogonal finding, own issue doc, own todos.                                                                                                                                                                                              | nobody — pick up any time; not on the candle-canonical migration's critical path |
| 8   | Confirming the P5 executor's TradFi content-resolution rate against real prod parquet content (the `E1AF0_*_migrated_*` objects' `instrument_id` COLUMN shape is unverified)                                                                                                                                                                  | **Not done** — the P0 census COUNTED the class exactly (6,487,045 `NEEDS_CONTENT_TRADFI_ID`) but did not sample/verify actual column shapes (dry-run never reads content); still needs a targeted content-read sample before trusting the resolution rate | nobody — pick up any time; a small sampled read, doesn't need a full VM          |
| 9   | Todo 16 (investigate `24h` force-leg `off_template=29` classification — possibly a stale §3A "RAW token" docstring, same class as the data_type staleness todo 6 fixed)                                                                                                                                                                       | **Not done** — P3, non-blocking                                                                                                                                                                                                                           | nobody — pick up any time                                                        |
| 10  | Fresh CEFI census re-run to measure the ACTUAL post-fix QUARANTINE_CORRUPT residual (todos 14/18's fix is proven correct via regression tests on the exact real shapes, but the aggregate corpus-wide count after the fix is not yet re-measured)                                                                                             | **Not done** — nice-to-have confidence check, not blocking (P7 `--apply` re-derives classification fresh regardless)                                                                                                                                      | nobody — pick up any time, or just let P7's own run be the measurement           |

**Recommended NEXT session action**: DEFI is DONE — do NOT re-launch it. Move to PREDICTION next: JIT-redrain
PREDICTION-relevant VMs just-in-time (apply the TIGHTENED rule from the mid-flight-watch Progress Log entry above —
bucket match alone is not sufficient, confirm the candidate VM's object-prefix actually overlaps
`processed_candles/by_date/` on `market-data-tick-pred-{env}-{pid}` before stopping it), then launch PREDICTION's full
`--apply` (measure its own throughput/shard-count the same way DEFI's was derived — don't assume SHARD_OF=10 transfers
directly, PREDICTION's corpus size differs). **Expect the same run-1-has-stragglers-then-retry-clean pattern** — treat a
first-pass `exit=5` with a small (<0.1%) transient-503 straggler count as expected, not a failure; the retry (identical
shard-of/shard-index/SHA pins) is the proven recovery path, not a targeted resume (checkpoint state doesn't survive
`VM_SHUTDOWN_ON_COMPLETION=true` on a non-zero exit). Then CEFI, then TRADFI in that order (already-ruled sequencing,
tradfi last, ~99% id-canonicalisation), then P8 verify/reconcile. This entire sequence is already operator-authorized
(`/autonomous`) — no new confirmation needed unless something contradicts the documented intent above.

## Progress Log — 2026-07-22 (P7a-full: DEFI full `--apply` LAUNCHED, in flight, NOT YET VERIFIED)

**JIT re-drain before launch** (per item 3's lesson — recurring cron respawns): surveyed `gcloud compute instances list`
and found 3 DEFI-tagged VMs RUNNING again since the canary: `canonical-migration-defi-rebuild-20260722-193748` (writing
to `market-data-tick-defi-prd-central-element-323112/_index/per_vm/...` — SAME bucket the apply mutates),
`orphan-sweep-defi-20260722-165131` (actively enumerating the same bucket, 3.35M objects swept and counting), and
`instr-backfill-defi-targeted` (writing to `instruments-store-defi-prd-central-element-323112` — a DIFFERENT bucket,
instrument reference data not candles, mid-retry on a real backfill shard). Stopped the first two
(`gcloud compute instances stop`, zone `asia-northeast1-c`); deliberately LEFT `instr-backfill-defi-targeted` running —
it never touches the candle bucket the migration mutates, and stopping it would discard real in-progress backfill work
for no safety benefit. **Rule for future re-drains: scope to the exact bucket the migration writes, not just the `DEFI`
tag** — `instr-backfill-defi-targeted` would have been a false-positive stop under the coarser "any DEFI VM" rule from
item 3.

**Sizing the shard count from measured canary throughput** (not guessed): the canary's own `run.log` gave real numbers —
full-bucket enumeration (`gcloud storage ls -r` over all 1,124,849 DEFI candle objects) took ~168s; apply of 200 objects
at `--workers 16` took 16:59:36.015→16:59:39.286 = **3.27s for 200 objects ≈ 61 obj/s per VM**. Extrapolated single-VM
full-corpus time: 1,124,849 / 61 ≈ 5.1 hours. Chose **SHARD_OF=10** (workers left at the canary-proven 16, not bumped,
to keep the run a one-new-variable test — fleet width, not worker concurrency, is the untested lever) for an estimated
~31 min apply + ~3 min enum overhead ≈ **~34 min wall-clock**, matching the `data-pipeline-check-mdps` skill's
documented guidance that fleet width is DEFI/MDPS's dominant, unbounded lever (no Tardis-style shared-IP cap applies
here — this mutates GCS directly, no vendor fetch).

**Reproducibility — pinned to the EXACT canary-proven tarball SHAs, not fresh HEAD**: re-fetching current tarball
manifests showed MDPS and UAC had both moved forward since the canary (fresh `mdps=52afe59c...`, `uac=68c4c371...` vs
the canary's `mdps=c64a7dfa9d9f0689e13c92839e386cd45978a718`, `uac=c4e1acee147a53aaf0df4e0d8dad1289e2210f79`; UTL
unchanged at `b0ec1da02c5fe7dfd94550a9354542fc2a00fc0b`). Deliberately launched against the **canary's exact SHAs**
(confirmed those `@<sha>.tar.gz` artifacts still exist in `gs://deployment-scripts-central-element-323112/code/`) —
using fresh HEAD would have put unvalidated code into the first full-scale production run, breaking the
canary-then-scale discipline this whole effort has followed.

**Launch mechanics + a naming quirk worth recording**:
`SHARD_OF=10 bash launch-canonical-migration-vm.sh defi-candle-apply 2020-01-01 2026-07-22 full` (with the 3
`*_TARBALL_SHA` pins above) fans out one VM per shard via the launcher's internal loop, which sets
`VM_NAME_SUFFIX=shard{i}of{N}` — but this call **times out in a 2-minute foreground shell** (10 sequential
`gcloud compute instances create` calls, ~35-40s apart) before finishing; it got through shards 0-2 (named
`...{ts}-s0of10`/`-s1of10`/`-s2of10`) before being killed. Recovered by launching shards 3-9 via 7 SEPARATE invocations,
each with `SHARD_INDEX=<i>` PINNED as an env var — this is correct and safe (each VM still gets the right
`--shard-of 10 --shard-index N` baked into its python command via `_candle_apply_cmd`), but pinning `SHARD_INDEX`
externally bypasses the launcher's INTERNAL fan-out loop (which is the only place `VM_NAME_SUFFIX` gets set), so shards
3-9 got plain timestamp names with **no `-s{i}of10` suffix**. Not a correctness bug — confirmed via each VM's own
`run.log` startup command (`--shard-index N` is present and correct) — but a VM's NAME alone doesn't tell you its shard
index for these 7. **Full name→shard mapping** (confirmed for shards 3-5 directly via `run.log` grep; 6-9 inferred from
strict launch order, which matches creation timestamps):

| Shard | VM name                                                 |
| ----- | ------------------------------------------------------- |
| 0/10  | `canonical-migration-defi-cdlap-20260722-195057-s0of10` |
| 1/10  | `canonical-migration-defi-cdlap-20260722-195057-s1of10` |
| 2/10  | `canonical-migration-defi-cdlap-20260722-195057-s2of10` |
| 3/10  | `canonical-migration-defi-cdlap-20260722-195327`        |
| 4/10  | `canonical-migration-defi-cdlap-20260722-195406`        |
| 5/10  | `canonical-migration-defi-cdlap-20260722-195449`        |
| 6/10  | `canonical-migration-defi-cdlap-20260722-195524`        |
| 7/10  | `canonical-migration-defi-cdlap-20260722-195603`        |
| 8/10  | `canonical-migration-defi-cdlap-20260722-195642`        |
| 9/10  | `canonical-migration-defi-cdlap-20260722-195733`        |

(Minor P3 follow-up, not blocking: the launcher's per-invocation `SHARD_INDEX`-pinned path could set
`VM_NAME_SUFFIX="shard${SHARD_INDEX}of${SHARD_OF}"` too when `SHARD_INDEX_EXPLICIT` is set and `SHARD_OF>1`, for
consistent naming across both invocation styles — cosmetic, not tracked as a numbered todo since it doesn't affect
correctness or safety.)

**STATUS AS OF THIS WRITING: IN FLIGHT, NOT YET VERIFIED.** All 10 VMs confirmed `RUNNING` in
`gcloud compute instances list`; shards 0-2 confirmed booted cleanly (serial console shows startup script finished, task
launched) but had not yet produced a `run.log` at last check (still inside the ~3min enumeration window observed in the
canary); shards 3-5 confirmed via `run.log` grep to have the correct `--shard-index` baked in; shards 6-9 were still
booting at last check. **No shard has reached `EXIT_STATUS` yet — do not assume this run has completed.** A fresh
session (or the next `/autonomous` tick) should check
`gs://deployment-scripts-central-element-323112/vm-logs/<vm-name>/EXIT_STATUS` for all 10 VMs above before doing
anything else with DEFI candle data; if all 10 show `EXIT_STATUS=0`, hard-verify via a real `gsutil stat` sample (old
non-canonical path gone, new canonical path exists — same method as the canary) before marking this item done, updating
the Deferred table, and moving to PREDICTION.

## Progress Log addendum — 2026-07-22 (mid-flight watch: JIT-redrain rule needs a second tightening)

While polling the 10 shards' progress (all healthy — real `apply:` counters climbing, tens of thousands of objects each,
no shard preempted), `gcloud compute instances list` showed a VM I hadn't seen before:
`canonical-migration-defi-rebuild-20260722-194751`, `RUNNING`, created ~3min after I stopped
`canonical-migration-defi-rebuild-20260722-193748` (the earlier same-bucket stop from the JIT-redrain item above) and
~3min before my shard fan-out began — i.e. it looks like an automated relaunch of the exact class of VM I'd just
stopped, on the exact bucket (`market-data-tick-defi-prd-central-element-323112`) my 10 apply shards are concurrently
mutating. Investigated before touching it (never stop-first-ask-later on a live migration):

- `run.log` shows it runs
  `market_tick_data_service.scripts.rebuild_defi_manifest --bucket market-data-tick-defi-prd-central-element-323112 --start-date 2022-04-29 --end-date 2026-12-31`
  — scans `raw_tick_data/by_date/day={...}/(category|asset_group)=defi/` and writes ONLY to
  `_index/per_vm/canonical-migration-defi-rebuild-20260722-194751.parquet`.
- `migrate_candle_canonical_2026_07.py` operates exclusively under `CANDLE_ROOT = "processed_candles/by_date/"`
  (confirmed via grep — the script's own docstring calls out `raw_tick_data/` as the disjoint sibling migrator's
  territory, not this one's).
- **No object-level overlap**: disjoint read/write prefixes (`raw_tick_data/` vs `processed_candles/`), and the rebuild
  job's only write target (`_index/per_vm/<its-own-name>.parquet`) is never read or written by the candle apply.

**Verdict: false alarm, left running.** But this is the SECOND real near-miss this session on the JIT-redrain heuristic
(first was `instr-backfill-defi-targeted`, same-bucket-but-different-bucket that time; this time
same-bucket-same-service-family but disjoint prefix). **Tightening the rule accordingly: "same bucket" is necessary but
not sufficient — before stopping any VM found running during a JIT redrain, confirm it actually reads/writes the SAME
OBJECT PREFIX the migration's `--apply` touches** (grep the target script's root-prefix constant, as done here), not
just the bucket name or an asset_group tag. Apply this tightened check for the PREDICTION/CEFI/TRADFI JIT redrains next
— a same-bucket VM on a disjoint prefix is not a conflict and should be left alone.

## Progress Log — 2026-07-22 (P7a-full: DEFI full apply RUN 1 COMPLETE — all 10 shards exit=5, 211 stragglers, retry launched)

All 10 shards reached `EXIT_STATUS` between 19:30-19:36 UTC. **All 10 exited `rc=5`, not `0`** — this is the migration
script's own convention for "COMPLETE WITH STRAGGLER(S)", not a crash: each shard fully walked its enumeration
(`apply: N processed` reached the shard total for all 10), and the non-success outcomes are 100% transient GCS errors
during `copyTo` (`ServiceUnavailable`/`GatewayTimeout`, "We encountered an internal error. Please try again."),
consistent with backend write-QPS throttling from 10 concurrent VMs bulk-copying against one bucket simultaneously.

**Aggregate**: 1,131,814 objects processed across the 10 shards; 211 total stragglers (17-29 per shard); every straggler
breakdown is `ERROR:ServiceUnavailable`/`ERROR:GatewayTimeout` only — no `ERROR:` category indicating a real data/logic
bug. **211/1,131,814 ~= 0.019% failure rate.** Per the script's own log line: "these objects were attempted but did NOT
complete and remain at their legacy path. A re-run with the SAME --enumeration/--out/--shard-of/
--shard-index/--limit/gates is safe (idempotent) and will retry them" — data is NOT lost or corrupted, the straggler
objects simply weren't moved this run.

**Per-shard result** (VM name -> processed / stragglers):

| Shard | VM name     | processed | stragglers |
| ----- | ----------- | --------: | ---------: |
| 0     | `...s0of10` |   112,380 |         17 |
| 1     | `...s1of10` |   112,469 |         27 |
| 2     | `...s2of10` |   112,347 |         20 |
| 3     | `...195327` |   112,292 |         20 |
| 4     | `...195406` |   112,793 |         19 |
| 5     | `...195449` |   112,381 |         17 |
| 6     | `...195524` |   112,823 |         24 |
| 7     | `...195603` |   113,436 |         17 |
| 8     | `...195642` |   115,301 |         29 |
| 9     | `...195733` |   115,592 |         21 |

**Caveat found while planning the retry**: `_candle_apply_cmd`'s compound shell command only uploads `mappings/` to GCS
on the `&&`-gated SUCCESS path (`... && gcloud storage cp -r mappings/ ${stage}`) — since the python step exited
non-zero (rc=5), that upload never ran, AND `VM_SHUTDOWN_ON_COMPLETION=true` already self-deleted all 10 VMs. So the
per-run checkpoint/mapping state is NOT recoverable from GCS for a targeted "resume from exact checkpoint" retry — the
only available retry path is a fresh full-shard re-run (same as the original invocation). This is fine: `_stable_shard`
hashes by object path (not enumeration line position), so a fresh `gcloud storage ls -r` enumeration this run still
partitions objects identically, and the script's own `VERIFIED_INPLACE` classification means the ~99.98% already-
migrated objects will short-circuit as cheap existence-checks rather than being re-copied — so the retry's actual GCS
write-QPS (the likely 503 root cause) should be far lower than run 1's, since run 1 was doing ~1.13M real `copyTo` calls
and this retry only needs ~211.

**Action taken**: launched 10 retry shards (`SHARD_OF=10`, `SHARD_INDEX=0..9` explicitly pinned per invocation — same
recovery pattern as the original run's shards 3-9, run via a single backgrounded loop to avoid the foreground 2-min
timeout from the start this time), same proven tarball SHA pins (`MDPS=c64a7dfa9d9f0689e13c92839e386cd45978a718`,
`UAC=c4e1acee147a53aaf0df4e0d8dad1289e2210f79`, `UTL=b0ec1da02c5fe7dfd94550a9354542fc2a00fc0b`), `WORKERS=16`,
`MODE=full`.

## Progress Log — 2026-07-22 (P7a-full: DEFI — RETRY SUCCEEDED, all 10 shards clean, HARD-VERIFIED, item DONE)

Retry converged exactly as predicted: all 10 shards reached `EXIT_STATUS=0` (14 min total wall-clock, vs ~35-45 min for
run 1 — the retry's `VERIFIED_INPLACE` counts landed at ~99.98% of each shard, matching run 1's per-shard totals almost
exactly, confirming most work this pass was a cheap existence-check, not a re-copy). Every shard's `run.log` ends with
`apply COMPLETE — shard N/10 fully migrated cleanly (0 non-success outcomes)`, and the `MIGRATED` count in each retry —
17, 27, 20, 20, 19, 17, 24, 17, 29, 21 for shards 0-9 respectively — is an **exact** match to run 1's straggler counts
per shard, confirming the retry fixed precisely (and only) the 211 objects that failed transiently in run 1; nothing
else moved.

**Hard-verify** (real `gsutil stat`, not just log trust): sampled 2 of the 211 previously-straggling objects (shard 0's
`day=2024-09-01/timeframe=15s/.../0xc2e9f25be6...parquet` and shard 9's
`day=2025-11-03/timeframe=5m/.../0xcd8286b489...parquet`). Both: legacy path `gsutil stat` → `No URLs matched` (gone);
canonical path (`pipeline_mode=batch_databento/.../instrument_type=POOL/...`) → real object present, `Creation time`
matching the retry's run window (19:48/19:59 UTC), correct `Content-Length`/hashes present.

**DEFI candle canonical-path migration+purge: DONE.** 1,131,814 objects processed (run 1) + 211 re-verified/re-migrated
(retry) = 0 outstanding legacy-path candle objects in `market-data-tick-defi-prd-central-element-323112`. Moving to
PREDICTION next, applying the tightened prefix-aware JIT-redrain rule (bucket match alone is not sufficient — confirm
object-prefix overlap before stopping any VM found running).

## Progress Log — 2026-07-22 (P7b-prep: PREDICTION JIT-redrain — nothing to stop; sizing from existing census, no new walk)

**JIT-redrain**: surveyed `gcloud compute instances list` (all RUNNING VMs, both clouds relevant here is GCP-only per
current state) — only one PREDICTION-tagged VM: `datapoint-validation-prediction-20260722-151911`
(`validate_datapoint_schema_id.py`). Applied the tightened prefix-aware rule from the DEFI mid-flight finding: read the
script (`instruments-service/scripts/validate_datapoint_schema_id.py`) — it reads `market-data-tick-prediction`
(`data_bucket`, via `resolve_bucket_name`) for validation but its ONLY write (`_flush_shard` →
`client.upload_from_file_obj`) targets `results_bucket = resolve_bucket_name(kind="datapoint-validation")`, a completely
disjoint bucket. It is a reader of the migration's target bucket, never a writer of `processed_candles/**` — not a
JIT-redrain conflict (the rule protects against concurrent WRITERS, not readers; a validator racing an in-flight delete
of a legacy-path object would at worst hit one transient read miss, not corrupt anything). **Verdict: nothing to stop.**
No other PREDICTION-relevant VM found running.

**Shard sizing**: per the workspace's single-walk-discipline rule, did NOT run a fresh census/enumeration — the P0
census (this doc, `## Full results` table) already measured PREDICTION's real corpus: **1,165,459 total objects**
(1,165,458 `SPLIT_BRAIN_DUPLICATE`, 1 `MIGRATE`) — within 4% of DEFI's 1,124,849, and that classification was already
exercised + safety-verified (`ORPHAN=0`) on this exact data via the census dry-run (same script, same code path, just
without `--apply`/`--quarantine`/`--content-repair`). Proceeding with `SHARD_OF=10` (justified by corpus-size parity
with DEFI, not blindly copied), `WORKERS=16`, same proven tarball SHA pins. PREDICTION being ~100% split-brain-dedup
rather than DEFI's ~100% plain-MIGRATE is a different disposition mix — if per-shard throughput differs materially from
DEFI's measured ~61 obj/s/VM, that's new information to carry into CEFI/TRADFI sizing, not a blocker here.

**Action**: launched 10 shards (`SHARD_OF=10`, `SHARD_INDEX=0..9` explicit pin, single backgrounded loop, same SHA pins
as DEFI: `MDPS=c64a7dfa9d9f0689e13c92839e386cd45978a718`, `UAC=c4e1acee147a53aaf0df4e0d8dad1289e2210f79`,
`UTL=b0ec1da02c5fe7dfd94550a9354542fc2a00fc0b`).

## Progress Log — 2026-07-22 (P7b: PREDICTION full apply — CLEAN on first pass, hard-verified, DONE)

All 10 shards reached `EXIT_STATUS=0` on the FIRST run — no straggler retry needed this time (unlike DEFI). Every
shard's `run.log` ends `apply COMPLETE — shard N/10 fully migrated cleanly (0 non-success outcomes)`. Per-shard
`MIGRATED` counts: 116827, 116732, 116512, 116232, 116849, 116524, 116955, 116280, 116730, 115818 (shards 0-9) — **sum =
1,165,459, an EXACT match to the P0 census total**, confirming full coverage with no double-processing or drops. Shards
5-9 additionally show small `VERIFIED_INPLACE` counts (123-3,335) — pre-existing already-canonical objects,
expected/harmless.

**Hard-verify**: sampled the live bucket directly (`gsutil ls .../processed_candles/by_date/day=2025-03-14/**`) — every
returned object carries the canonical `pipeline_mode=.../instrument_type=.../` shape. Confirmed the corresponding legacy
(non-canonical) path for one sampled object is gone (`gsutil stat` → no match), and a broader probe for ANY remaining
non-canonical object under that same `day=/timeframe=` partition (grep excluding `pipeline_mode=`) returned zero
matches.

**PREDICTION candle canonical-path migration+purge: DONE.** Moving to CEFI next — same JIT-redrain (prefix-aware) +
existing-census-sizing approach (CEFI's P0 census: 940,606 objects — but note the census's 13.9% `QUARANTINE_CORRUPT`
figure is STALE: todos 14/18 (shipped, see the "Prep work COMPLETE" entry above) already fixed the root cause
(`_renormalize_wire_cefi` wasn't wired for CEFI's classify branch, wrongly quarantining 128,218 of 130,906 objects) + a
separate KRAKEN-SPOT `/`-in-symbol parsing bug, BEFORE this P7 sequence started — `--apply` re-derives classification
fresh with the fixed classifier, so expect the real quarantine rate to land far below 13.9%).

## Progress Log — 2026-07-22 (P7c-prep: CEFI JIT-redrain — nothing to stop; apply launched)

**JIT-redrain**: only `datapoint-validation-cefi-20260722-151832` is CEFI-tagged among running VMs — the same
`validate_datapoint_schema_id.py` script already analyzed for PREDICTION (reads the tick bucket, writes only to the
disjoint `datapoint-validation` results bucket, never `processed_candles/`). Not a conflict, left running. No other
CEFI-relevant VM found.

**Action**: launched 10 shards (`SHARD_OF=10`, `SHARD_INDEX=0..9`, same proven SHA pins, `WORKERS=16`, `MODE=full`)
against CEFI's 940,606-object corpus.

## Progress Log — 2026-07-22 (P7c: CEFI run 1 — 1 shard genuinely SPOT-preempted, 9 clean stragglers, combined retry launched)

**Watchdog hit its 90-min ceiling with 9/10 terminal** — a real anomaly, not just slow, diagnosed before assuming
anything. `gcloud compute instances describe` on the missing shard's VM
(`canonical-migration-cefi-cdlap-20260722-215112`, shard 2/10) showed `status=TERMINATED`;
`gcloud compute operations list --filter=targetLink~<vm>` confirmed a genuine `compute.instances.preempted` operation at
21:15:15 UTC, matching exactly where its `run.log` progress stream stops (last line: 70,000/~94,000 processed,
`MIGRATED: 58685`). This is expected SPOT behavior on this workspace's own terms (backfill VMs default SPOT, idempotent
shards re-run on preemption) — not a script bug, not a hang.

**The 9 completed shards all exited `rc=5`** — same "COMPLETE WITH STRAGGLER(S)" convention as DEFI, but a DIFFERENT
root cause this time: `CRC32C_MISMATCH_KEPT_SRC` / `SIZE_MISMATCH_KEPT_SRC` (2-31 per shard, ~140 total) rather than
DEFI's `ServiceUnavailable`/`GatewayTimeout`. This is the script's own post-copy integrity verification catching a
checksum/size mismatch and safely KEEPING THE SOURCE rather than deleting it — a safety guard working as intended, not
data corruption. The script's own log line treats it as retriable the same way ("re-run ... is safe (idempotent) and
will retry them"). New disposition categories also appeared here (`CONTENT_REPAIR_UNRESOLVED_QUARANTINED`, ~13-14% of
each shard) — this is the EXPECTED post-todo-14/18-fix quarantine bucket (genuinely-unresolvable content, distinct from
the pre-fix over-quarantine bug), not a regression.

**Action**: launched a single combined retry covering all 10 shards (same `SHARD_OF=10`/SHA pins/`WORKERS=16`) — this
both mops up the ~140 CRC/size-mismatch stragglers across the 9 completed shards AND fully redoes the preempted shard 2
from scratch (its ~59K already-migrated objects will short-circuit via `VERIFIED_INPLACE`, the remaining ~35K get
freshly processed; checkpoint/mapping state does not survive a preemption or non-zero exit, same caveat as DEFI, so a
full shard re-run — not a targeted resume — is the only available path).

## Progress Log — 2026-07-23 (P7c: CEFI retry — another 3-shard SPOT preemption burst; ROOT-CAUSED the CRC/SIZE-mismatch non-convergence)

**Retry 1 also hit preemptions**: 3 of the 10 retry shards (0, 1, 5) were preempted within 3-7 minutes of boot
(`gcloud compute operations list` confirmed `compute.instances.preempted` for all 3, timestamped right where each
`run.log` stream stops) — a real capacity-contention burst in `asia-northeast1-c` at this time, not a bug. This is the
SAME expected-SPOT-behavior class as shard 2's preemption in run 1, just three at once this time.

**The 7 shards that DID complete this retry reproduced their CRC32C/SIZE-mismatch stragglers at (nearly) IDENTICAL
counts to run 1** — e.g. shard 3: 6 CRC32C + 2 SIZE both times; shard 7: 10 CRC32C + 9 SIZE both times; shard 8: 8+4
both times; shard 9: 14+13 both times (only shard 6 differed, by exactly 1). Per the discipline set for DEFI ("if it
doesn't converge after ~3 attempts, investigate rather than blindly retry"), read `_copy_verify_delete()`
(`migrate_candle_canonical_2026_07.py:794-831`) to find out why — **and found the actual root cause**:

```python
dmeta = gcs_describe_object(dst_uri)
if dmeta is None:
    gcs_copy_object(src_uri, dst_uri)      # <-- COPY only happens when dst is MISSING
    dmeta = gcs_describe_object(dst_uri)
...
if smeta.size != dmeta.size: return "SIZE_MISMATCH_KEPT_SRC"
if smeta.crc32c != dmeta.crc32c: return "CRC32C_MISMATCH_KEPT_SRC"
```

The copy step is gated on `dmeta is None` — it only fires when the destination doesn't exist yet. DEFI's stragglers
(`ServiceUnavailable`/`GatewayTimeout`) were copy-operation EXCEPTIONS, meaning the destination object was never
created, so `dmeta` stays `None` on retry and a fresh (successful) copy fires — genuinely transient, converges. CEFI's
stragglers are different: the copy DID complete once (dst exists), but post-copy verification found it doesn't match the
source. On any subsequent run, `dmeta is not None`, so the copy step is SKIPPED — the script only re-_compares_ the same
already-existing (bad) destination against the source, forever. **This class of straggler cannot converge by retrying,
no matter how many times — the retry logic has no path to fix a "copied-but-wrong" destination**, only a
"copy-never-happened" one. This isn't data corruption or loss (the SOURCE is never touched on any `KEPT_SRC` outcome, by
design — the delete-safety protocol's whole point), but it IS a real, previously-unknown gap in this script's retry
model.

**Why not just fix the script live and re-run?** Couldn't reliably identify the SPECIFIC affected objects to verify a
fix against: the WARNING lines only log `"non-success outcome '<TYPE>' at shard-local index N"`, never the object URI
(unlike the exception-path `"apply failed for %s: ..."` at line 991, which DOES log the path) — no per-object path is
logged for a `KEPT_SRC` return. The `--out` mapping TSV (which would have full path detail) only uploads to GCS on the
`&&`-gated success path, and these runs exited rc=5, so it never uploaded; the VMs then self-deleted
(`VM_SHUTDOWN_ON_COMPLETION=true`), taking local disk with it. Patching the copy-verify-delete safety mechanism —
untested — directly against a live production migration, with no way to confirm the fix against the actual failing
objects, is worse than leaving ~140-200 objects (out of ~940K, ~0.02%) safely un-migrated at their legacy path pending a
proper code fix.

**Verdict**: accepting this as a genuine, small, SAFE residual (source data fully intact, nothing lost, nothing
corrupted downstream since these stay at the LEGACY path, not partially/incorrectly canonicalized) — not blindly
retrying a 3rd/4th/Nth time for this specific straggler class, since the code proves it cannot converge. Relaunched ONLY
the 3 preempted shards (0, 1, 5 — their bulk migration work is unrelated to this finding and still needs to complete);
once terminal, will tally the final residual CRC/SIZE-mismatch count across all 10 CEFI shards and record it honestly
(NOT claim "0 outstanding" the way DEFI/PREDICTION could). **New follow-up needed** (not filed as a numbered todo yet —
will file before closing this session): fix `_copy_verify_delete` to distinguish a verified-correct existing destination
(current `VERIFIED_INPLACE` short-circuit, working correctly) from a verification-FAILED existing destination (should be
treated as if absent — i.e., overwrite + re-verify — not skip-compare forever), with proper tests, then run ONE surgical
mop-up pass against just the residual objects. **This same latent gap applies to TRADFI's upcoming run** — if TRADFI
hits any KEPT_SRC-class stragglers, apply this same accept-and-track discipline rather than expecting convergence from
more retries.
