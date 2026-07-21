---
doc_type: codex-ssot
title: Four-surface reconciliation procedure (GCS path ⇄ parquet content ⇄ manifest atom ⇄ catalogue render)
summary: >-
  The executable comparison loop for ONE shard across the four canonical surfaces — GCS object path/filename, parquet
  content columns, the manifest `_index` shard-atom key, and the catalogue / data-status render. Defines the shard atom
  as the comparison grain and the rule that the atom is ONE definition across writer/manifest/status/gate/UI, names the
  machine oracle (UAC `canonical_path_violations()`) as the only authority on canonical-vs-non-canonical, states the
  single-walk constraint and its three sanctioned no-walk routes, and records the per-asset-group deviations. This is
  the core loop of the `/data-pipeline-reconciliation` skill. Finding CLASSIFICATION lives in
  `reconciliation-finding-taxonomy.md` and is REFERENCED, not restated here.
status: current
nature: ssot
asset_group: [meta]
stage: [data]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
    market-tick-data-service,
    instruments-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, shard-atom, manifest, gcs-paths, catalogue, single-walk, machine-oracle]
related:
  [
    cross-asset-canonical-target-ssot.md,
    reconciliation-finding-taxonomy.md,
    availability-manifest-and-data-status.md,
    honest-coverage-model.md,
    defi-canonical-naming-ssot.md,
    pipeline-mode-partition.md,
    ../05-infrastructure/bucket-isolation-model.md,
    ../05-infrastructure/gcs-object-operations.md,
    ../../plans/active/data_pipeline_reconciliation_skill_2026_07_20.md,
  ]
created: 2026-07-20
authoritative_for:
  [
    the four-surface reconciliation procedure for one shard,
    the machine-oracle rule for canonical-vs-non-canonical,
    surface-unavailability handling during reconciliation,
    the three sanctioned no-walk routes for reconciliation reads,
  ]
referenced_by:
  [
    codex/02-data/reconciliation-finding-taxonomy.md,
    codex/02-data/orphan-object-detection.md,
    codex/02-data/non-canonical-path-inventory.md,
  ]
owner:
last_reviewed: 2026-07-20
code_refs:
  [
    unified-api-contracts/unified_api_contracts/canonical/partition_paths.py,
    unified-api-contracts/unified_api_contracts/canonical/domain/sports/gcs_paths.py,
    unified-api-contracts/unified_api_contracts/registry/possible_manifest.py,
    unified-trading-library/unified_trading_library/manifest_writer/_rows.py,
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
    deployment-api/deployment_api/services/data_status/reference_scope.py,
  ]
---

# Four-surface reconciliation procedure

> **What this doc is.** `cross-asset-canonical-target-ssot.md` §0 NAMES the four canonical surfaces and §1 defines the
> shard-atom grain patterns; `availability-manifest-and-data-status.md` §10 states the triad-agreement HARD RULE.
> Neither composes them into a procedure you can execute. This doc is that procedure: given ONE shard atom, how you
> obtain each of the four surface values, in what order, what to do when a surface is unavailable, and where the
> resulting disagreement gets classified.
>
> **What this doc is NOT.** It does not define the finding types. The closed, named set — its exact type names, their
> detection methods, default severities, safe remediations, delete-eligibility, and the operator-accepted exception list
> — lives in **`codex/02-data/reconciliation-finding-taxonomy.md`**, which is authoritative for all of them. Classify
> there; compare here. **Do not restate the type names here**: a second enumeration is precisely how the two docs drift
> (this paragraph previously carried three names — `orphan`, `masked-stale`, `drift-axis-false-positive` — that the
> taxonomy does not use, one of which it had explicitly rejected).
>
> **This doc is the RAW-TICK layer. There is a candle-LAYER variant (added 2026-07-21).** The MDPS processed-candle
> layer (`--layer candles`) reconciles the same four surfaces but with four deltas, so it has its own SSOT —
> `codex/02-data/mdps-candle-canonical-reconciliation.md` — do NOT apply this doc's raw-tick rules to candles: (1) the
> candle shard atom **adds a `timeframe` axis** and keys `data_type` on the AGGREGATED `mdps_data_type_key`, with S3
> rows filtered `service_name == "market-data-processing-service"`; (2) the candle namespace (`processed_candles/`) is
> **oracle-EXEMPT** — `canonical_path_violations()` hardcodes `raw_tick_data/by_date/` (`partition_paths.py:67`) and
> false-flags every candle path, so candle canonicality is checked against the ratified Option-A registry template, not
> the machine oracle; (3) **S4 is UNAVAILABLE for the whole candle layer by construction** (candles are derived — no
> catalogue); (4) the candle reconciliation is **GCS-object-driven, not manifest-driven** (the candle manifest is
> near-empty). The whole candle corpus is `migration_pending` behind the ruled Option-A migration (operator,
> 2026-07-21). See the candle SSOT for the full grammar and per-AG deltas.

---

## 1. The four surfaces

Per `cross-asset-canonical-target-ssot.md:70-82` (§0), every shard must agree on instrument identity across four
independent representations:

| #      | surface                              | where it physically lives                                                                                                                                                                                            | how you read it                                                                                                                                                                                                                                            |
| ------ | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **S1** | **GCS object path + filename**       | the parquet object under the raw-tick prefix (`raw_tick_data/by_date/…`; sports uses `sports_reference/by_date/…`)                                                                                                   | prefix-scoped listing (§5) or a direct `gcs_describe_object` on a constructed path                                                                                                                                                                         |
| **S2** | **parquet CONTENT columns**          | inside the object — `instrument_id`, and for defi additionally `canonical_instrument_id`                                                                                                                             | read the object's columns; content, never the path, is the claim about what the file HOLDS                                                                                                                                                                 |
| **S3** | **manifest `_index` shard-atom key** | the availability-manifest canonical index row                                                                                                                                                                        | `read_availability_index()` / `merge_canonical_with_outstanding_shards()` — `unified-trading-library/unified_trading_library/manifest_writer/_read_index.py:296,1118`                                                                                      |
| **S4** | **catalogue / data-status render**   | (a) deployment-api reference scope: `data-catalogue.instruments-service.yaml` → `shard_status[ASSET_GROUP][VENUE].start_date`; (b) the instrument's `available_from`→`available_to` window in `prod/catalog.parquet` | `deployment_api/services/data_status/reference_scope.py:19,64-77` parses the `shard_status` map into `{(asset_group, venue): genesis}`; the `available_from/to` window is the §10 triad's third leg (`availability-manifest-and-data-status.md:1666-1667`) |

S4 is deliberately **two-part**. `reference_scope.py:24` states its grain explicitly: _"Grain = venue/day.
Per-instrument_type scoping is a separate follow-on tied to a manifest-schema change and is intentionally NOT attempted
here."_ So the deployment-api leg answers **"is this `(asset_group, venue, day)` in scope at all?"**, not "is this
instrument expected?". The per-instrument expectation comes from the catalogue window. **Never** compare S4 at a grain
finer than venue/day for the deployment-api leg — doing so manufactures disagreements the surface never claimed.

---

## 2. The shard atom is the comparison grain — and it is ONE definition

The full atom (superset), per `cross-asset-canonical-target-ssot.md:86-91`:

```
pipeline_mode({mode}_{source}) · date · asset_group · venue · [chain] · instrument_type · data_type
  · (KEY) · [quote · margin] · source
```

`chain` is defi-only. `[quote · margin]` is cefi bundles + prediction perps.

**HARD RULE — the atom is identical across writer / manifest / status / gate / UI. The reconciliation procedure never
invents its own key.** A comparison keyed on anything other than the shard's own `(KEY)` is not a reconciliation; it is
a fabricated diff. UTL enforces a fragment of this at the writer boundary —
`_SHARD_ATOM_KEYS = {"instrument_id", "chain"}` raises `MalformedRowKeyError` when a caller supplies the key blank
(`unified-trading-library/unified_trading_library/manifest_writer/_rows.py:276-280`).

### 2.1 The `(KEY)` slot varies by grain pattern

Per `cross-asset-canonical-target-ssot.md:93-99` (§1 table):

| pattern                      | who                                                                                                   | `(KEY)`                                                                                                                                             |
| ---------------------------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| **#1 flat-per-contract**     | cefi spot/perp/dated-future, tradfi equity, kalshi raw trades, **all defi (target 2026-07-18)**       | **`instrument_id`** — filename stem == `instrument_id` column == manifest key, byte-identical                                                       |
| **#2 bundle-per-underlying** | cefi `options_chain`/`futures_chain` (DERIBIT/OKX), tradfi `futures_chain`/`options_chain` (CME/CBOE) | **`underlying`** — one parquet per underlying; per-contract ids live in the column; the manifest row MAY carry a null `instrument_id` **by design** |
| **#3 prediction CQG bundle** | POLYMARKET / KALSHI vanilla markets                                                                   | **`canonical_question_group`** (`data_type=prediction_canonical_question_group`) — **MANIFEST-ONLY**, never a path segment                          |

### 2.2 Two rules that have already destroyed data

- **`underlying` is a KEY ONLY in pattern #2.** Everywhere else — prediction (#3) included — it is a **display-only row
  column**, never the shard key (`cross-asset-canonical-target-ssot.md:103-105`). Treating a display axis as a key
  splits one shard into many phantom shards.
- **Keying prediction on `instrument_id` is how CQG bundle rows get wiped.** Prediction's atom is
  `(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)` —
  `market_id` is a row-level parquet column, NOT a shard axis (`availability-manifest-and-data-status.md:57-62`). The
  CQG has **no path segment**: the prediction builder puts the `condition_id` in the FILENAME and the path carries no
  CQG at all (`unified-api-contracts/unified_api_contracts/canonical/partition_paths.py:383-434`, docstring: _"The
  `condition_id` is used as the per-instrument FILENAME … NOT a partition segment"_). So a reconciler that keys
  prediction on per-object `instrument_id` finds N objects and 1 manifest row, declares the row phantom, and deletes the
  bundle that legitimately covers all N. **The phantom reconciler must not be run against prediction.**

---

## 3. The procedure for ONE shard

Inputs: the asset_group (**operator-supplied — never synthesized**, per the sibling backfill skills' `--day` rule), the
day/window, and the atom's non-`(KEY)` axes. Cells are enumerated from the UAC MVP predicate `is_mvp()`
(`unified-api-contracts/unified_api_contracts/canonical/crosscutting/_mvp_scope_predicate.py:229`) and
`canonical_path_templates(ag)` (`unified-api-contracts/unified_api_contracts/registry/possible_manifest.py:352`) —
**never a hardcoded venue/prefix/data_type list**. `canonical_path_templates` documents itself as _"the SINGLE SSOT for
the phantom reconciler's `prefix_tpls` and the orphan sweep's prefix set — replacing every hand-maintained per-consumer
copy (the Axis-10 drift bug)"_ (`possible_manifest.py:361-364`).

Execute the steps **in this order**. The order is load-bearing: S3 is first because it is the cheapest surface and the
only one that can be read without touching the corpus, and it supplies the prefix scoping that keeps S1 inside the
single-walk budget (§5).

**Step 1 — S3, the manifest atom (always first).** Read the canonical `_index` via `read_availability_index()`; where
outstanding per-VM shards may not yet be consolidated, use `merge_canonical_with_outstanding_shards()`
(`_read_index.py:296,1118`). Extract the row's `(KEY)` per §2.1 and its 4-state `capture_status`. Record `absent` if
there is no row.

**Step 2 — resolve the bucket.** `resolve_bucket_name(cloud, kind, asset_group, deployment_env)` over
`cloud-providers.yaml` — never an inline `gs://`, never a bucket-name fragment as a `kind`, and **never mutate process
env to reach a tier; pass `deployment_env=`**. SSOT: `codex/05-infrastructure/bucket-isolation-model.md`. Record which
bucket each read targeted — the report's Bucket-paths table is generated from this.

**Step 3 — S1, the GCS path.** Obtain the object path via one of the three sanctioned routes in §5 — prefix-scoped from
the Step-1 rows by default. Do **not** assert an object exists because a path can be constructed: existence is
`gcs_describe_object(uri)` (`unified-trading-library/unified_trading_library/cloud_interface/gcs_blob_ops.py:51`)
returning non-`None`. All GCS object ops go through the UTL `gcs_*` helpers, never `subprocess gcloud`/`gsutil`
(`codex/05-infrastructure/gcs-object-operations.md`).

**Step 4 — run the machine oracle on the S1 path (§4).** This is the ONLY step that decides canonical vs non-canonical.

**Step 5 — S2, the parquet content.** Read `instrument_id` (and `canonical_instrument_id` for defi) from the object.
**Content, not existence.** A path that looks like a duplicate of a canonical twin is not a duplicate until the CONTENT
is verified — the R5 content-verify overturned a DUP verdict on 98-vs-99 pools whose intersection was only 66
(`plans/active/data_pipeline_reconciliation_skill_2026_07_20.md:70-77`). Delete-adjacent conclusions additionally
require the five-part proof in `codex/02-data/gcs-and-manifest-delete-safety-protocol.md`.

**Step 6 — S4, the catalogue/status render.** (a) `reference_genesis(asset_group, venue)` for the in-scope test at
venue/day grain (`reference_scope.py:120`); note that a role-qualified manifest venue (`OKX-FUTURES`) is matched against
its BASE token before being declared unlisted (`reference_scope.py:109-118`). (b) the instrument's
`available_from`→`available_to` window for the per-instrument expectation.

**Step 7 — compare and classify.** Compare the four values **at the atom grain from §2**. Emit the disagreement to the
finding taxonomy — `codex/02-data/reconciliation-finding-taxonomy.md`. Apply that doc's operator-accepted exception list
BEFORE emitting: re-reporting an accepted exception as a fresh finding destroys the report's signal and makes
consecutive runs undiffable.

**Step 8 — report the number with its formula named.** Any coverage figure must name its formula. The live,
CK3-certified one is `reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)` with
`empty_confirmed` EXCLUDED (`honest-coverage-model.md:219`) — this is **settled**, not contested (§7 O4). The two v1
sites now carry ⛔ SUPERSEDED banners pointing at it. Name the formula anyway: a bare percentage is unfalsifiable even
when the formula is not in doubt.

### 3.1 When a surface is unavailable

A surface you could not read is **`unavailable`, never `absent`**. Collapsing the two is the single most common way a
reconciler manufactures a destructive false positive.

| condition                                                    | verdict for that surface                    | effect on the shard                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------------ | ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| S3 row absent, index readable                                | `absent` (a real observation)               | classify normally                                                                                                                                                                                                                                                                               |
| index unreadable / stale / consolidation outstanding         | `unavailable`                               | **shard is INCONCLUSIVE** — emit no finding, never a delete suggestion                                                                                                                                                                                                                          |
| S1 listing denied / bucket resolution failed                 | `unavailable`                               | INCONCLUSIVE                                                                                                                                                                                                                                                                                    |
| S1 object absent under a prefix that WAS successfully listed | `absent`                                    | classify normally                                                                                                                                                                                                                                                                               |
| S2 unreadable (corrupt / unauthorized)                       | `unavailable`                               | INCONCLUSIVE; explicitly **not** evidence of emptiness                                                                                                                                                                                                                                          |
| S4 catalogue absent or venue unlisted                        | `unavailable` for the render, but see below | `reference_scope._load_genesis_map()` **fails soft** — it logs a warning and caches `{}` on `OSError`/`YAMLError` (`reference_scope.py:88-93`), so an empty genesis map is indistinguishable from "nothing configured". Treat an empty map as `unavailable`, never as "everything out of scope" |

**Bucket-wide rule:** any shard with ≥1 `unavailable` surface is reported as INCONCLUSIVE with the unavailable surface
named. It never rises above `unknown` confidence and never carries a delete suggestion.

---

## 4. The machine oracle — canonical is decided by UAC, never by a downstream rule

**HARD RULE.** Whether a path is canonical is decided by **`canonical_path_violations()`** in
`unified-api-contracts/unified_api_contracts/canonical/partition_paths.py`. It is the deliberate **inverse of the
`build_*_partition_path` builders**. A reconciler, skill, script, or doc that re-implements the rule downstream is
review-blocking — that re-implementation is exactly the drift class the function exists to kill.

> **⚠️ The oracle does NOT validate the filename instrument-id.** It drops the last path segment
> (`partition_segments = segments[:-1]`, _"Last segment is the file name"_) before validating, and only
> `asset_group=tradfi` single-instrument shards have ever carried a stem rule. A CeFi corpus of **~811,200 objects
> carrying raw wire instrument_ids** (`ADAF0:USTF0.parquet`) and double-wrapped catalogue-miss ids
> (`BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0.parquet`) therefore returns **0 violations == CANONICAL**, at both
> `require_pipeline_mode` settings — a **FALSE-CLEAN verdict for surface A**, on the exact defect this procedure exists
> to catch (independent measurement puts the CeFi filename surface at **20.82%** canonical by id-form). **Surface-A
> id-form must be checked separately with the canonical-id check (§ 4.3); a clean oracle result is structure-only.**
> SSOT: `plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`.

```python
def canonical_path_violations(path: str, *, require_pipeline_mode: bool = False) -> list[str]
def is_canonical(path: str, *, require_pipeline_mode: bool = False) -> bool   # thin wrapper, line 828
```

Input is a **bucket-relative** path (no `gs://bucket/` prefix; a leading slash is tolerated and stripped). **Empty list
== canonical.** Read in full at `partition_paths.py:661-825`; its actual clauses today:

1. **Prefix** — must start with `RAW_TICK_DATA_PREFIX = "raw_tick_data/by_date/"` (line 66); otherwise it returns
   immediately with that single violation (`:681-683`).
2. **`day=` first partition** — must be the first partition segment, value ISO `YYYY-MM-DD`. A legacy `day-` hyphen
   segment is its own named violation (`:696-701`).
3. **Hive shape** — every subsequent segment must be `key=value`; a bare segment is a violation (`:707-709`).
4. **`pipeline_mode=` value** — when present, must match `^(batch|live|replay)_[a-z0-9]+(?:_[a-z0-9]+)*$` (`:653`,
   checked `:711-717`).
5. **`asset_group=`** — must be present AND inside the closed set `frozenset(member.value for member in AssetGroup)`
   (`:643`, checked `:721-728`).
6. **`pipeline_mode` required-but-missing** — emitted **only when `require_pipeline_mode=True`** (`:731-735`).
7. **`venue=` glue** — a hyphen in the venue token is flagged as a glued `VENUE-CHAIN` overload **only when
   `asset_group == "defi"`** (`:750-753`); a glued `V{N}` version (`[A-Za-z0-9]V\d`) is flagged for any AG (`:754-758`).
8. **tradfi-only clauses** (`:766-823`) — `pipeline_mode=batch_massive` is forbidden outright; `underlying=` must pass
   `is_recognized_tradfi_underlying()`; a `TRADFI_CHAIN_INSTRUMENT_TYPES` shard must end
   `…/underlying=/quote=/margin=/ticks.parquet`; a `TRADFI_SINGLE_INSTRUMENT_TYPES` shard's filename must be the full
   canonical `instrument_id` (contains `:`), never `ticks.parquet` and never a bare symbol. **This is the ONLY clause
   that reads the filename, and it is tradfi-gated — it has never covered CeFi.**

### 4.3 Path STRUCTURE and instrument-id FORM are ORTHOGONAL — neither alone proves "canonical"

Surface A is really **two** questions. The machine oracle answers only the first:

| question                                                                                                                                                | answered by                                                                                                                             | scope today          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | -------------------- |
| Is the **path STRUCTURE** canonical? (prefix, `day=`, `key=value` hive shape, `pipeline_mode`, `asset_group` closed set, venue glue, tradfi chain tail) | `canonical_path_violations()`                                                                                                           | all asset groups     |
| Is the **instrument-id FORM** canonical? (the filename stem, and the `instrument_id` content column)                                                    | the canonical-id regex/resolver — `_CANON_ID_RE` in `market-tick-data-service/scripts/_cefi_canonical_resolver_migration_2026_07_18.py` | tradfi filename only |

Canonical id grammar: `VENUE:ITYPE:BASE-QUOTE[@LIN|@INV][-YYYYMMDD][-STRIKE-C|P]`, plus a `COMBO` arm.

A path can be structurally perfect and carry a wire-named file; a path can carry a perfect id under a `day-2026-05-01`
legacy prefix. **A surface-A verdict that cites only the path oracle and concludes "canonical" is wrong — it must state
that id-form was not machine-checked, or run the canonical-id check itself and report both.** Legitimately stem-less
shapes (chain `underlying=…/ticks.parquet` bundles, the symbol-less `ticks.parquet` fan-in) have no per-instrument stem
and must never be counted as id-form violations.

### 4.1 CAVEAT — the machine gate is currently WEAKER than the codex declaration

`require_pipeline_mode` **defaults to `False`** (`:661`, documented `:672-676`: _"Default False accepts the back-compat
bare paths the builders still emit (the segment is canonical-but-optional for CeFi/Prediction and back-compat for
DeFi/TradFi)."_) The codex declares `pipeline_mode` canonical (`codex/02-data/pipeline-mode-partition.md`;
`cross-asset-canonical-target-ssot.md:220-229` puts it in every template), but the machine gate does not enforce it by
default. **Consequence: a path missing `pipeline_mode=` passes the oracle while contradicting the declared canonical
form.**

The reconciler therefore keys `require_pipeline_mode` off a **per-asset-group effective-from date** (the
canonical-cutover register, `codex/02-data/canonical-cutover-register.md`): `False` for days before that AG's cutover,
`True` on and after. Without that date the run either floods false positives on legitimately historical data or silently
passes post-cutover regressions.

### 4.2 The oracle does NOT cover sports

`canonical_path_violations` returns immediately for any path not under `raw_tick_data/by_date/` (`:681-683`), and every
sports object lives under `sports_reference/` (§6). **Running the oracle on a sports path returns a 100% false-positive
violation.** `canonical_path_templates("sports")` returns an empty list **by design** — _"Sports is intentionally
template-less here … Returned as an empty list for `sports` so a caller treats it as 'use the sports dispatcher', never
'no paths'"_ (`possible_manifest.py:368-371`). Dispatch to
`unified_api_contracts.canonical.domain.sports.gcs_paths.candidate_parquet_paths()` instead.

---

## 5. The single-walk constraint

**HARD RULE — no new whole-corpus GCS walk; it is review-blocking**
(`availability-manifest-and-data-status.md:1748-1750`). Default reconciliation mode is **manifest-driven**: read the
index (Step 1), derive prefixes from the rows.

Where object listing is unavoidable, only these three no-walk routes are sanctioned:

1. **Prefix-scoped listing per unique `(date, venue[, chain])` derived from manifest rows** — the shape the phantom
   auditor uses. `availability-manifest-and-data-status.md:1759` explicitly permits _"Per-shard / per-bucket targeted
   reads (not walking the full corpus)"_.
2. **Delimiter-based child-prefix listing** — `deployment_api/utils/storage_facade.py:323` `list_prefixes(...)`, which
   enumerates child prefixes rather than objects.
3. **Reuse of the existing single walk** in `instruments-service/scripts/migration_orphan_sweep.py`, bundling every pass
   onto that ONE snapshot. The standing rule: _"bundle any new schema change, partition-rename, or column-backfill into
   the campaign's single walk. Do NOT open a separate corpus walk for a single fix."_
   (`availability-manifest-and-data-status.md:1752-1755`).

> **The exemption test is PREFIX-SCOPING, not "it reads the index".** Corrected 2026-07-20 (P1-11,
> `availability-manifest-and-data-status.md:1769-1775`). The older rationale — that phantom-audit scripts are exempt
> because they "read the manifest index, not the parquet corpus" — is **factually false of the very script it named**:
> `reconcile_phantom_manifest_rows_all.py` calls `client.list_blobs(bucket, prefix=…)` at `:311` and `:425`. It is
> exempt because every listing is prefix-scoped. Never claim an exemption on the grounds that a script "reads the
> index"; claim it on the grounds that every listing it issues is prefix-bounded. For HOW to walk once you are permitted
> to, see [`../05-infrastructure/gcs-object-operations.md`](../05-infrastructure/gcs-object-operations.md) — that doc
> governs mechanics, this one governs WHETHER.

### 5.1 Route #3 in practice — the Tier-2 per-datapoint VM is the sanctioned single walk for S2 (added 2026-07-20)

When a **100% (not sampled) id/schema claim** on the **S2 (parquet content) surface** is required, the Tier-2
per-datapoint validation VM IS an instance of route #3 above: the ONE fresh corpus walk per campaign, on a SPOT VM, that
lifts the four-surface loop's sampled filename-stem/content check (Step 5) to the whole corpus. **G2 (id-canonical) and
G3 (schema) bundle as two PASSES onto that ONE snapshot walk, run in order per object — never two separate walks, never
two VMs.** The skill folds the results into this doc's S2 column by a **read-back of the VM's results manifest**, which
is a slim manifest-`_index` read (single-walk-EXEMPT, exactly like Step 1) — it does **not** count as a second walk.
Default stays Tier-1 sampled (≤500 objects/AG, reported as SAMPLED, never a 100% claim); Tier-2 is opt-in. SSOT for the
compute-tier model, the VM launcher, and the results-manifest read-back:
[`reconciliation-census-and-compute-tiers.md`](reconciliation-census-and-compute-tiers.md) § 3 — do not restate it here.

---

## 6. Per-asset-group deviations

A generic loop over all five asset_groups produces destructive false positives on at least three of them. **One code
path per AG.**

- **sports — NO `asset_group=` key at all.** The tree is
  `sports_reference/by_date/day={D}/entity={folder}/league={L}/{folder}.parquet`, with a bare (no-`league=`) variant and
  a flat non-`by_date` singleton form
  (`unified-api-contracts/unified_api_contracts/canonical/domain/sports/gcs_paths.py:13-22`). `entity=` folder names are
  **non-obvious** and mapped by `SPORTS_DATA_TYPE_TO_FOLDER` — `ODDS → footystats_odds`, `MATCHES → footystats_matches`,
  `XG → understat_xg` (`gcs_paths.py:38-66`). Guessing `entity=odds/` instead of `entity=footystats_odds/` is the
  documented 2026-04-29 incident that _"falsely report[ed] 26% phantom for ODDS when the data was right there"_
  (`gcs_paths.py:5-8`). Shard atom is `(asset_group=sports, venue/source, data_type, league_id, day)`; **`fixture_id` is
  a row column, not a shard axis** (`availability-manifest-and-data-status.md:51-55`). The oracle does not apply (§4.2).
- **prediction — manifest-only CQG.** `canonical_question_group` is the manifest `(KEY)` and appears in **no path
  segment** (§2.2). S1↔S3 therefore compares at DIFFERENT grains by design: many objects (one per `condition_id`
  filename) to one manifest row per `(CQG, day)`. Do not run the phantom reconciler against prediction.
- **defi — `chain=` sits AFTER `venue=`, and the two-id model.** Canonical order is
  `…/asset_group=defi/venue={PROTOCOL}/chain={CHAIN}/instrument_type={it}/data_type={dt}/{file}`, operator-locked venue
  BEFORE chain (`build_defi_partition_path`, `partition_paths.py:88-121`;
  `cross-asset-canonical-target-ssot.md:227-229`). `venue` is the bare PROTOCOL (`AAVE_V3`), never the legacy
  `PROTOCOL-CHAIN` overload — which is precisely what oracle clause 7 catches, and only for defi. S2 carries BOTH
  `instrument_id` and `canonical_instrument_id`.
- **tradfi — the only AG with write-time raising guards in the oracle** (clause 8), including the outright
  `batch_massive` ban. **The gated GCS purge of all ~1.7M historical `batch_massive` objects COMPLETED 2026-07-20**
  (RUN_TS=20260720-193849, 1,701,422 objects removed, 0 collateral — see resolved issue
  `massive_purge_blocked_databento_l1_entitlement_2026_07_20.md`), so `batch_massive` is no longer expected on disk. Per
  taxonomy AE-4's transition rule, the read-recognition exception has **closed**: a surviving `batch_massive` path found
  on READ is now a genuine finding, not an accepted exception — see the taxonomy's exception list.
- **cefi — venue names legitimately contain hyphens** (`BINANCE-FUTURES`, `OKX-FUTURES`). Flagging every hyphen as
  `VENUE-CHAIN` glue _"crashed the cefi LIVE producers at the writer boundary … silently freezing the
  deribit/hyperliquid/binance live VMs for hours (2026-06-23)"_ (`partition_paths.py:742-749`). This is why clause 7 is
  defi-gated.

---

## 7. Open questions — all four now RESOLVED (O2/O3 RULED 2026-07-20)

> **⛔ corrected 2026-07-20, operator rulings D1 + D2 — RE-RECONCILED 2026-07-20 (acceptance review).** ~~"O2 and O3 are
> genuinely UNRULED and BLOCKING — they need an OPERATOR … refuse to migrate the affected axis."~~ **Both were RULED
> 2026-07-20** (recorded in `plans/active/data_pipeline_reconciliation_skill_2026_07_20.md` § "OPERATOR DECISIONS — ALL
> THREE RULED 2026-07-20"). O2 → manifest `instrument_type` COLUMN TARGET is **UPPERCASE**, but is **NOT yet
> implemented** — the column is `migration_pending` (mixed on disk today), so the reconciler does NOT refuse it,
> compares it **case-INSENSITIVELY**, and emits **NO** casing finding until the migration completes (UPPERCASE enforced
> POST-migration). ~~(enforce, do not refuse)~~ — "enforce UPPERCASE now" was an over-correction; the reconciled stance
> is case-insensitive-until-migrated. O3 → defi flat `LENDING` full retire is the RULED **TARGET**, not yet implemented,
> gated on the MTDS lending-writer fix — market/event flat `LENDING` is `migration_pending`, neither a fresh finding nor
> an open axis. The per-item text below is updated in place; nothing in this section is now a live operator question.

**O1 and O4 are RESOLVED** and are retained below only as an audit trail of how each was closed. Neither was ever a real
operator question: both were doc drift — one stale template in the tie-breaker doc, and one formula stated three ways —
and both were closed by evidence (a shipped operator ruling plus a completed migration; a formula the shipping code
already implements). Do not re-open them. The distinction is the point of this section: **an axis blocked on a human
looks nothing like an axis blocked on a doc nobody had updated**, and conflating the two is how a reconciler either
stalls forever or migrates something it had no mandate to touch.

- **O1 — defi leaf filename. ✅ RESOLVED 2026-07-20 — was intra-doc drift, not an operator question.** §8 of
  `cross-asset-canonical-target-ssot.md` carried the RETIRED capture-batch template
  `{venue}_{chain}_{capture_ts}.parquet` while the same doc's §0/§1 pattern-#4 declared that model retired and folded
  into pattern #1. §1 won and §8 has been corrected: the canonical defi leaf is **`{canonical_instrument_id}.parquet`**
  (`filename == manifest key == symbolic canonical id`). Evidence: the operator ruling 2026-07-18
  ([`defi-canonical-naming-ssot.md`](defi-canonical-naming-ssot.md) § WRITE-MODEL SUPERSEDED banner, `:57-65`) **and**
  the completed R3 migration — MIGRATION ALL-TERMINAL 30/30, full 2020q1–2026q2 corpus on per-instrument
  ([`defi_consolidated_closeout_2026_07_18.md`](../../plans/active/defi_consolidated_closeout_2026_07_18.md):1033-1035).
  Both verified 2026-07-20.
  - **Operative caution — a KNOWN RESIDUAL, not a finding.** PERP re-migration is explicitly DEFERRED: the
    `{venue}_{ts}` bundles for ASTER / HYPERLIQUID / GMX remain on disk in the old bundle shape and surface as coarse
    manifest rows, bundled with the pending ASTER/HYPERLIQUID cefi-misfiling decision (same doc `:1041-1044`). **The
    reconciler must NOT emit these as `legacy_duplicate` and must NEVER suggest deleting them** — they are the only copy
    of that data, and their re-migration is gated on an operator decision that has not been made.
- **O2 — manifest `instrument_type` COLUMN case. ✅ RULED UPPERCASE (TARGET) 2026-07-20 (operator ruling D1);
  `migration_pending` today.** Was contested — `cross-asset-canonical-target-ssot.md` §7 said LOWERCASE while the tradfi
  close-out Phase B said UPPERCASE, both citing the same operator on the same date (2026-07-18). **The operator ruled
  the canonical TARGET is UPPERCASE for the manifest COLUMN** (catalogue enum wins; path segment stays lowercase, id
  middle segment stays UPPER — both ALWAYS enforced, neither in question). The two shipped uppercase scripts
  (`instruments-service@555ddf1c` + tradfi Phase-B) are RATIFIED and unfrozen. **The UPPERCASE column is NOT yet
  implemented — the column is `migration_pending` (measured 2026-07-20: mixed on disk — defi both cases present,
  prediction 99.46% UPPER, cefi ~99.41% adjusted).** ~~The reconciler now ENFORCES UPPERCASE for the column~~ **(⛔
  re-reconciled 2026-07-20 — "enforce now" would false-flag all un-migrated data).** So the reconciler **(1)** does NOT
  refuse the axis; **(2)** compares the `instrument_type` COLUMN **case-INSENSITIVELY** and emits **NO** casing finding
  during the `migration_pending` window; **(3)** enforces UPPERCASE only POST-migration. Defi/other rows not yet folded
  UP are `migration_pending`, not a fresh finding. **Gate**: the honest-coverage harness must be made case-robust BEFORE
  the migration flips writers —
  `plans/active/issues/honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md`.
- **O3 — defi flat `LENDING` instrument_type. ✅ RULED 2026-07-20 (operator ruling D2 — full retire is the TARGET, NOT
  yet implemented).** `cross-asset-canonical-target-ssot.md` §5's "`LENDING` is RETIRED (A_TOKEN/DEBT_TOKEN split)" is
  the correct TARGET, but the first attempt was **reversed in code** because it broke 5+ (really 8) MTDS lending writers
  into `attempted_failed`/zero-data. Mandatory order: **fix the writers → migrate ~16.7M rows → re-sync the shard atom**
  — gated on `plans/active/defi_lending_writer_retire_prerequisite_2026_07_20.md`. **Until the migration completes,
  market/event flat `lending` is `migration_pending`** — the reconciler neither flags it as non-canonical nor treats it
  as an open/unruled axis.
- **O4 — honest-coverage formula. ✅ RESOLVED 2026-07-20 — not an open question.** This one was never genuinely unruled:
  it was doc drift, and it is now closed in favour of [`honest-coverage-model.md`](honest-coverage-model.md) § Coverage
  formula — `reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`, `empty_confirmed`
  **EXCLUDED** (CK3-certified 2026-06-29; shipping implementation
  `instruments-service/scripts/measure_honest_coverage.py:600-603`). The two superseded v1 sites now carry ⛔ SUPERSEDED
  banners pointing here — `availability-manifest-and-data-status.md` (:117, :1027, :1968) and
  `../05-infrastructure/manifest-consolidator-ssot.md` (:296), all verified present 2026-07-20. **The reconciler uses
  the `honest-coverage-model.md` formula and does not treat coverage as contested.** Step 8's name-the-formula
  discipline still stands — not because the formula is in doubt, but because a bare percentage is unfalsifiable
  regardless.
  - _Residual, and it is a CODE question rather than a doc contradiction:_ `compute_honest_coverage()` is still a live
    UAC function carrying the v1 shape. Whether it is deleted, re-pointed, or kept as a deliberately distinct all-shards
    metric is unresolved and tracked in P1-09. This does not reopen the formula ruling above.

---

## 8. Where the work lives

Skill authoring, per-AG validation runs, and the codex corrections referenced above are tracked in
`plans/active/data_pipeline_reconciliation_skill_2026_07_20.md`. Sibling SSOTs this procedure composes with:
`reconciliation-finding-taxonomy.md` (classification + exceptions) · `gcs-and-manifest-delete-safety-protocol.md` (the
five-part delete proof) · `non-canonical-path-inventory.md` (the living register of known non-canonical locations) ·
`canonical-cutover-register.md` (the per-AG effective-from dates §4.1 depends on) · `orphan-object-detection.md` (the
inverse case: an object with no manifest row and outside the oracle's expected set).
