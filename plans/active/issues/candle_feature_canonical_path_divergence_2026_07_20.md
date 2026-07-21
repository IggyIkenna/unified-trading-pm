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
      These cannot be attributed to a shard. **Pending P5 executor (census phase).**
- [ ] 3. [DATA] P1. Canonicalise **TradFi candle leaf ids** (`E1AF0_C3200_migrated_*` → `VENUE:TYPE:SYMBOL`) or rule the
      migration naming acceptable. **Pending P5 executor (quarantine-if-unresolvable, per the LOCKED spec above).**
- [x] 4. ✅ [SCRIPT] P1. **volatility writer**: pass the declared `prefix=` to `get_data_sink` so output lands under
      `volatility/by_date/` per its own SSOT. Fixed + shipped `features-service@99d5554e`.
- [x] 5. ✅ [SCRIPT] P2. Reconcile the **UTL paths-registry `delta_one` entry** with the real writer — readers now
      dual-read via `candle_read_prefixes` (canonical + legacy, both pre/post-migration) rather than relying on a single
      hand-rolled template. Shipped `unified-trading-library` (staging-first landing) + `features-service@99d5554e`.
- [ ] 6. [SCRIPT] P2. Re-point `/data-pipeline-check-mdps` + `/data-pipeline-check-features` canonical legs at the
      LOCKED template (was ratified 2026-07-21) so a clean canonical sweep is achievable post-migration. **Pending — do
      after the P4 -test- verification confirms the writer emits the LOCKED shape.**

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
- [ ] 10. [SCRIPT] P1. **Extend the UAC canonical oracle to the `processed_candles/` (+ features) namespace** (addendum
      iii-b): `canonical_path_violations()` today only knows `raw_tick_data/by_date/` and flags every candle path as a
      structural violation, so it cannot govern candle shape. After the A/B/C ruling, teach the oracle the ratified
      candle template (incl. the `pipeline_mode=` insert decision) and re-point the skill canonical legs at it (todo 6)
      so candle canonicality becomes machine-checkable instead of bespoke.

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
