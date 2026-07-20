# reference-tradfi — per-AG expansion for `/data-pipeline-reconciliation --asset-group tradfi`

Expansion of the `tradfi` row in [`SKILL.md`](SKILL.md) § 3d. Pointers + hazards only — the durable rules live in codex.

## Path grammar (this AG)

```
raw_tick_data/by_date/day={D}/pipeline_mode={mode}_{source}/asset_group=tradfi/
  venue={VENUE}/instrument_type={it_lower}/data_type={dt}/<TAIL>
```

| Grain                                                                                   | Tail                                                          |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| chains (`futures_chain` / `options_chain`) — matches cefi 1:1, shipped 07-19            | `underlying={BASE}/quote={QUOTE}/margin={MODE}/ticks.parquet` |
| singles (equity, etf, index, currency, bond, cds, commodity, future, option, spot_pair) | `{FULL_CANONICAL_ID}.parquet`                                 |

Example (chain):
`raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/instrument_type=futures_chain/data_type=trades/underlying=SP500/quote=USD/margin=linear/ticks.parquet`
(the margin token is the word-form **`linear`** / `inverse`, verified in the writer scripts — not the `lin` abbreviation
of the id `@LIN` suffix.)

Segment shape: `_AG_SEGMENT_SHAPE[TRADFI]` —
`unified-api-contracts/unified_api_contracts/registry/possible_manifest.py:157` (identical to cefi; no `chain=`).

## Buckets — resolve, never hand-build

`resolve_bucket_name(cloud, kind, asset_group="tradfi", deployment_env="prd")`:

| Layer     | `kind`                               | Resolves to                          |
| --------- | ------------------------------------ | ------------------------------------ |
| raw tick  | `market-data` (or alias `tick-data`) | `market-data-tick-tradfi-prd-{pid}`  |
| reference | `instruments-store`                  | `instruments-store-tradfi-prd-{pid}` |
| features  | `features`                           | `features-tradfi-prd-{pid}`          |

Verified in `unified-trading-pm/configs/cloud-providers.yaml:93-102` and `:59-63`; alias at
`unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py:108`.

## Shard atom + (KEY)

`[pipeline_mode, date, asset_group, venue, instrument_type, data_type, (KEY), quote, margin, source]`.

- **singles → `instrument_id`** (grain pattern #1).
- **chains → `underlying`** (grain pattern #2). `underlying` is a KEY **only** here.

## Instrument-id grammar

- dated derivative: `VENUE:TYPE:PRODUCT_ROOT-USD@LIN-YYYYMMDD[-STRIKE-C|P]` — the product **root** is resolved, not the
  venue code (`ES` → `SP500`, `VX` → `VIX`).
- cash: `VENUE:EQUITY:SYM-USD` — the `-USD` suffix is present on **all four surfaces**, not just the id.

> `unified-api-contracts/docs/canonical-instrument-ids.md`'s per-type table is **pre-2026-07-18 stale** (shows
> `NASDAQ:EQUITY:AAPL` without `-USD`, `CME:FUTURE:ES-USD` without root resolution). Do not use it as the tie-breaker;
> use `codex/02-data/cross-asset-canonical-target-ssot.md`.

## Catalogue (surface 4)

`instruments-store-tradfi-prd-{pid}/prod/catalog.parquet`.

> ⛔ **STALE — RE-MEASURED 2026-07-20.** The old "**0 of 1,111,322 rows canonical / expect surface 4 to fail
> wholesale**" claim is no longer true: the catalogue was **rebuilt 2026-07-20T01:05** and measures **1,391,725 rows,
> ~92% space-free structured canonical ids** (e.g. `CBOE:FUTURE:VIX-USD@LIN-20210120`, VX→VIX resolved). Measure the
> current canonical fraction yourself; do not carry the "0 canonical" figure. (The same stale figure lives in
> `canonical-cutover-register.md` § 4 — a flagged **codex contradiction** for the orchestrator, not an executor fix.)

## HAZARDS

### H1 — the write-time guard RAISES (tradfi is the only AG with it)

`_assert_canonical_tradfi_path` calls `canonical_path_violations(gcs_path, require_pipeline_mode=True)` and raises
`ValueError` on any violation —
`market-tick-data-service/market_tick_data_service/engine/orchestrator/partitioned_writer.py:83-96`, invoked at
`:258-259` under `if self._asset_group == "tradfi":`. Consequence for reconciliation: **any non-canonical tradfi object
you find in the raw-tick bucket predates the guard** (or was written by a lane that bypasses this writer). Date-bound
the finding against `codex/02-data/canonical-cutover-register.md` before calling it a live regression.

### H2 — `batch_massive` read-recognition is DELIBERATELY KEPT. Flagging it is a FALSE POSITIVE.

Massive (formerly Polygon.io) was removed as a tradfi **source** 2026-07-19, but the `batch_massive` `PipelineMode` +
`possible_manifest` **read-recognition** is intentionally retained until the gated GCS purge. Roughly **1.47M objects**
(1,696,166 in the `PURGE_MASSIVE` disposition class) sit under `pipeline_mode=batch_massive/`.

- **Do not** report them as orphans, phantoms, or non-canonical. That is a known accepted exception — suppress with a
  count + pointer per `SKILL.md` § 5.
- **Do not** propose the purge as a delete suggestion above `unknown`. The purge is a **human-only hard stop**
  (`SKILL.md` § 4b), and **571 Massive-only shards still need a Databento backfill first** — purging before that
  backfill destroys the only copy.
- Pointer: `codex/02-data/tradfi-databento-sourcing-ssot.md`,
  `plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md`.

### H3 — `combo` is EXCLUDED from the full-id filename guard, but the live writer emits the FULL chain tail

The UAC builder deliberately excludes `combo` from both the chain-tail set and the singles full-id filename guard
(leg-id shape is unsettled, parked axis B2). **But the live writer does NOT emit a bare `underlying=/ticks.parquet`
fan-in for combo — measured day=2026-07-01 it writes the FULL chain tail
`underlying=/quote=USD/margin=linear/ticks.parquet`, identical to chains.** The oracle accepts both shapes, so it is not
a `non_canonical_path`. The load-bearing consequence is the **writer/reader disagreement**: the writer partitions combo
by `underlying=` while the reader probes it as a single — that is the **HIGH cross-repo finding (AE-2 adjacent), NOT a
suppressed exception**. Do not describe combo on disk as "bare underlying"; report the writer/reader mismatch.

### H4 — QUARANTINE classes: never fake-canonicalize, never delete

Two classes must be reported as `quarantine`, distinct from both "canonical" and "delete candidate":

| Class                   | Count  | What it is                                                                                               |
| ----------------------- | ------ | -------------------------------------------------------------------------------------------------------- |
| `QUARANTINE_GARBAGE_UL` | 14,633 | garbage `underlying=` — numeric Globex group codes `12` / `13`, opaque CBOE leg codes `GN` / `VT` / `3W` |
| `QUARANTINE_CORRUPT`    | 1,180  | corrupt objects                                                                                          |

There is no defensible canonical id to rename these to. Inventing one manufactures fake canonical data; deleting them
loses whatever they contain. Quarantine is the only correct disposition.

### H5 — the estate is MEASURED and TOOLED, `--apply` is operator-gated

Physical enumeration is complete: **2,734,646 objects across 95 legacy path shapes** with a **0-orphan** disposition map
(`PURGE_MASSIVE` 1,696,166 · `MIGRATE_CHAIN_ADDQM` 528,961 · `MIGRATE_SINGLE_RENAME` 389,703 · `MIGRATE_HYPHEN` 100,698
· `QUARANTINE_GARBAGE_UL` 14,633 · `MIGRATE_CONTENT_REPAIR` 1,478 · `QUARANTINE_CORRUPT` 1,180 · `MIGRATE_NONHIVE_EQ`
920 · `MIGRATE_SINGLE_NOOP` 907). Writer lockstep is SHIPPED; the executor is **dry-run only**. Reconcile against this
map — do not re-enumerate the corpus (single-walk discipline, `SKILL.md` § 3).

Report the four surfaces separately or you will collapse a real filename-vs-manifest divergence into one misleading
verdict. **Do NOT carry the stale "manifest measures 0 canonical across all years" claim** — re-measured 2026-07-20 the
manifest non-null ids are ~81% structured (`NASDAQ:EQUITY:NVDA-USD`) and the catalogue ~92% (above). Measure the current
fraction per surface; the "0 canonical" figure is stale (codex contradiction, above).

### H6 — parked axes: report the block, do not pick a side

- **B1** — keep `etf` as a distinct `instrument_type` or fold into `equity` (270,460 rows).
- **B2** — `combo` top-level id shape.
- **B4** — 4,655 retired-vendor `barchart` rows + 9,119 `BARCHART` venue rows + the `batch_barchart` pipeline_mode.

Per `SKILL.md` § 3e, surface these with citations and a severity; do not resolve or migrate them.

## Known-good spot-check — run BEFORE trusting any absence result

1. Enumerate prefixes from `canonical_path_templates("tradfi")` —
   `unified-api-contracts/unified_api_contracts/registry/possible_manifest.py:352`. Never hand-list venues or sources:
   the hand-listed prefix set is the Axis-10 drift bug.
2. Confirm the returned list **includes** a `pipeline_mode=batch_massive/` prefix (the retained legacy recognition, H2).
   If it does not, your UAC checkout predates the carve-out and every Massive object will false-flag.
3. Pick one `(date, venue)` known-captured from the manifest and confirm your probe returns non-zero.
4. For a chain shard, probe the `underlying=/quote=/margin=/` tail; for a `combo` shard, probe the **bare**
   `underlying=` tail (H3). One vocabulary does not cover both.
5. Only then treat a zero as a finding.

## Census / vocabulary nuance

Added 2026-07-20 — the in-session distinct-value census (`codex/02-data/reconciliation-census-and-compute-tiers.md` §
1).

- **`batch_massive` (source / `pipeline_mode` axis) is SUPPRESSED, never a `non_canonical_axis_value`** — the
  read-recognition is deliberately KEPT until the gated GCS purge (H2); the census routes it to the accepted-exception
  line with a count + pointer, not a finding.
- **`instrument_type` is compared EXACT case-sensitive** (cefi/tradfi grain rule) — a case-ONLY diff is the C2a
  column-casing axis (RULED UPPERCASE-target, `migration_pending`), SUPPRESSED during the window; a non-case out-of-enum
  value IS a `non_canonical_axis_value`.

## Cross-links

`SKILL.md` · `codex/02-data/four-surface-reconciliation-procedure.md` ·
`codex/02-data/reconciliation-finding-taxonomy.md` · `codex/02-data/canonical-cutover-register.md` ·
`codex/02-data/non-canonical-path-inventory.md` · `codex/02-data/gcs-and-manifest-delete-safety-protocol.md` ·
`codex/02-data/tradfi-databento-sourcing-ssot.md` · `codex/05-infrastructure/bucket-isolation-model.md`
