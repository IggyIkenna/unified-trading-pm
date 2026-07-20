# reference-prediction — per-AG expansion for `/data-pipeline-reconciliation --asset-group prediction`

Expansion of the `prediction` row in [`SKILL.md`](SKILL.md) § 3d. Pointers + hazards only — the durable rules live in
codex.

> ⚠️ **READ H1 BEFORE TOUCHING THIS ASSET GROUP.** Running the phantom reconciler against prediction is **destructive**.

## Path grammar (this AG)

```
raw_tick_data/by_date/day={D}/pipeline_mode={mode}_{source}/asset_group=prediction/
  venue={V}/instrument_type=prediction_market/data_type={dt}/{conditionId}.parquet
```

Example:
`raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_polymarket_gamma_api/asset_group=prediction/venue=POLYMARKET/instrument_type=prediction_market/data_type=trades/0x1a2b….parquet`

The filename is the **per-`conditionId`** stem. Filenames sanitize `/` → `_`; an empty/absent `condition_id` becomes the
literal `_unknown_` stem.

> **There is NO `canonical_question_group=` path segment**, and no `prediction_canonical_question_group` raw-object tree
> (verified: 0 such objects). The CQG bundle is **manifest-only**, recomputed at rebuild.

> **Vocabulary caveat:** `_AG_SEGMENT_SHAPE[PREDICTION]` is the **empty string** —
> `unified-api-contracts/unified_api_contracts/registry/possible_manifest.py:160`. So
> `canonical_path_templates("prediction")` returns prefixes that stop at `asset_group=prediction/` and carry **no**
> `venue=` / `instrument_type=` / `data_type=` tail. That is fine for prefix-scoped listing, but it means the templates
> do **not** hand you the per-segment vocabulary the way they do for cefi/tradfi/defi — derive those from the manifest
> rows instead, and say so in the report rather than implying the templates covered them.

## Buckets — resolve, never hand-build

Prediction uses **dedicated flat yaml keys**, not the per-AG dicts, and the on-disk token is the **short `pred`**, not
`prediction`:

| Layer     | `kind`                         | Resolves to                                       |
| --------- | ------------------------------ | ------------------------------------------------- |
| raw tick  | `market-data-tick-prediction`  | `market-data-tick-pred-prd-{pid}`                 |
| reference | `instruments-store-prediction` | `instruments-store-pred-prd-{pid}`                |
| features  | `features-prediction`          | `features-pred-prd-{pid}`                         |
| strategy  | `strategy-store-prediction`    | `strategy-store-pred-prd-{pid}` (currently EMPTY) |

Verified at `unified-trading-pm/configs/cloud-providers.yaml:108-111`. Note the `features` per-AG dict **also** carries
a `PREDICTION` key resolving to the same `features-pred-…` name (`:63`) — either kind reaches the same bucket; prefer
the dedicated key for consistency with the other three layers.

**Do not** pass `kind="market-data"` with `asset_group="prediction"` — the `market-data` dict has only CEFI / DEFI /
TRADFI / SPORTS (`:93-97`), so it will not resolve.

## Shard atom + (KEY)

`[pipeline_mode, date, asset_group, venue, instrument_type, data_type, canonical_question_group, source]` — grain
pattern **#3**, the manifest-only CQG bundle.

**`canonical_question_group` is the KEY. `instrument_id` is NOT.** Raw objects are per-`conditionId`; the manifest row
is per-CQG bundle. These are different grains and the mapping is many-to-one.

## Instrument-id grammar

`VENUE:PREDICTION_MARKET:{condition_id|ticker}` — e.g. `POLYMARKET:PREDICTION_MARKET:0x1a2b…`,
`KALSHI:PREDICTION_MARKET:INXD-26JUL01-B5000`. This id identifies an **object**, never a manifest row's key.

> ⚠️ **The manifest `instrument_id` COLUMN is a display-only `OTHER`/blank placeholder for CQG rows — do NOT compute an
> id-form % over it** (measured 2026-07-20: naively it reads ~39% id-form and manufactures a false finding). Check
> id-form on the on-disk **filename stem** (`VENUE:PREDICTION_MARKET:{id}`) instead; the manifest key is
> `canonical_question_group`, not `instrument_id` (H1).

## Catalogue (surface 4)

`instruments-store-pred-prd-{pid}/prod/catalog.parquet` — the only AG whose `CATALOG_COLUMNS` carry a `data_type` grain
binding. Plus an **ORPHAN stale `prd/catalog.parquet` shadow** (65 MB vs the live 202 MB). Read `prod/`; report the
shadow once.

## HAZARDS

### H1 — DO NOT RUN THE PHANTOM RECONCILER AGAINST PREDICTION. It wipes CQG bundle rows.

The phantom reconciler **mis-keys** prediction: it keys on the per-object `instrument_id` instead of
`canonical_question_group`. Because the manifest row is a CQG **bundle** and the objects are per-`conditionId`, keying
on `instrument_id` finds no matching object for the bundle row and demotes/wipes it. This is the single most destructive
mistake available on this asset group.

Generalised: **keying prediction on `instrument_id` is how CQG bundle rows get wiped** (`SKILL.md` shard-atom line). Any
tool you point at prediction must be checked for which key it uses before it runs, even in dry-run — and this skill
never runs `--apply` anyway.

### H2 — prediction is NOT MVP-backfill-ready

Phase-B manifest canonicalisation is **HELD** pending a drain window currently occupied by the concurrent tradfi and
cefi migrations. The closeout states explicitly that prediction is **not MVP-ready**. Report findings against that
state; do not treat held work as a regression.

### H3 — the catalogue-gates-download (G4) contract does not hold here

Prediction is **not registered** in MTDS `_CATALOG_ASSET_GROUPS` (which carries only sports / cefi / defi / tradfi), and
**no `prediction_catalog_reader.py` exists**. So surface 4's normal gating semantics are absent for prediction. State
this as a declared **coverage gap** in the report rather than silently producing a surface-4 verdict that has no
mechanism behind it.

### H4 — the write path is UNGUARDED and keeps a silent fan-in

- The write-time canonical guard is **tradfi-only** —
  `market-tick-data-service/market_tick_data_service/engine/orchestrator/partitioned_writer.py:258-259` calls
  `_assert_canonical_tradfi_path` under `if self._asset_group == "tradfi":`. MTDS W1 prediction writes are therefore
  unguarded and fail **silent**.
- W1 keeps the silent `return "ticks.parquet"` fan-in for symbol-less shards — several distinct shards can collapse onto
  one object. A `ticks.parquet` under a prediction path is that fan-in, not a chain bundle.
- `build_prediction_partition_path` has **no `pipeline_mode` kwarg**; the segment is string-rewritten by the dispatcher,
  so a missed rewrite is a silent non-canonical write (same defect class as cefi H3).
- Both prediction adapters have **no `VENUE:TYPE:` wrap at all** in the `canonical_id_builder` retrofit checklist.

### H5 — cross-AG bleed INTO the sports bucket

**≥6,597 `asset_group="prediction"` manifest rows are physically in the sports bucket manifest** (a **growing floor** —
was 4,097 dated 2026-06-26 → 07-18, re-measured **≥6,597 dated 07-16 → 07-19 on 2026-07-20**; the sports index was in
stale per-VM-shard fallback so treat the count as a lower bound and re-measure). Root cause **unlocated** as of
2026-07-20. Two consequences:

1. A prediction-scoped manifest read against only the prediction bucket **under-counts** by those rows.
2. Do not "fix" them from this skill — it is read-only, and the root cause is unknown. Report the count and cross-link
   the sports sheet ([`reference-sports.md`](reference-sports.md) H4).

## Known-good spot-check — run BEFORE trusting any absence result

The generalised lesson from the defi `solana_amm_pool` false negative (`SKILL.md` § 4b): **an absence result is only
evidence once you have confirmed you probed the vocabulary the writer actually emits.** Prediction's version:

1. Enumerate prefixes from `canonical_path_templates("prediction")` —
   `unified-api-contracts/unified_api_contracts/registry/possible_manifest.py:352`. Note H1's caveat: the tail is empty,
   so these give you day + `pipeline_mode` + `asset_group` only.
2. Confirm the list includes the prediction **extra live-probe** prefixes. `_EXTRA_LIVE_PROBE_SOURCES_BY_AG`
   (`possible_manifest.py:256`, applied at `:340-349`) appends `live_<source>` shapes the capability-derived loop cannot
   emit (e.g. batch-only `polymarket_gamma_api`). Probing only `batch_` previously false-phantomed **13,292** KALSHI /
   POLYMARKET `book_snapshot_5` / `trades` rows (the 2026-07-11 CF-15 finding, cited in that function's own comments).
3. Confirm you are keying the manifest side on `canonical_question_group`, not `instrument_id` (H1).
4. Pick one `(date, venue)` known-captured and confirm your probe returns non-zero, remembering the object stem is a
   `conditionId` — and that `_unknown_` is a legitimate stem, not corruption.
5. Only then treat a zero as a finding.

## Cross-links

`SKILL.md` · [`reference-sports.md`](reference-sports.md) (H5 bleed) · `codex/02-data/prediction-data-types-catalog.md`
· `codex/02-data/prediction-schema-paths.md` · `codex/02-data/four-surface-reconciliation-procedure.md` ·
`codex/02-data/reconciliation-finding-taxonomy.md` · `codex/02-data/canonical-cutover-register.md` ·
`codex/02-data/orphan-object-detection.md` · `codex/05-infrastructure/bucket-isolation-model.md`
