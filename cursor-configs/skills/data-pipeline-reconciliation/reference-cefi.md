# reference-cefi — per-AG expansion for `/data-pipeline-reconciliation --asset-group cefi`

Expansion of the `cefi` row in [`SKILL.md`](SKILL.md) § 3d. Pointers + hazards only — the durable rules live in codex.

## Path grammar (this AG)

```
raw_tick_data/by_date/day={D}/pipeline_mode={mode}_{source}/asset_group=cefi/
  venue={VENUE_UPPER}/instrument_type={it_lower}/data_type={dt}/<TAIL>
```

Two tails, by grain pattern:

| Grain                                        | Tail                                                      |
| -------------------------------------------- | --------------------------------------------------------- |
| singles (perpetual, spot, future, option, …) | `{FULL_CANONICAL_ID}.parquet`                             |
| chains (`options_chain` / `futures_chain`)   | `underlying={U}/quote={Q}/margin={m_lower}/ticks.parquet` |

Example (single):
`raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_tardis/asset_group=cefi/venue=BINANCE/instrument_type=perpetual/data_type=trades/BINANCE:PERPETUAL:BTC-USDT@LIN.parquet`

The single filename is the **full canonical id**, never the bare venue-native symbol. Confirm the segment shape against
`_AG_SEGMENT_SHAPE[CEFI]` — `unified-api-contracts/unified_api_contracts/registry/possible_manifest.py:156`.

## Buckets — resolve, never hand-build

`resolve_bucket_name(cloud, kind, asset_group="cefi", deployment_env="prd")`:

| Layer     | `kind`                               | Resolves to                        |
| --------- | ------------------------------------ | ---------------------------------- |
| raw tick  | `market-data` (or alias `tick-data`) | `market-data-tick-cefi-prd-{pid}`  |
| reference | `instruments-store`                  | `instruments-store-cefi-prd-{pid}` |
| features  | `features`                           | `features-cefi-prd-{pid}` (folded) |

Verified in `unified-trading-pm/configs/cloud-providers.yaml:93-102` (`market-data` / `instruments-store` per-AG dicts)
and `:59-63` (`features`). The `tick-data` → `market-data` alias is
`unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py:108`. Features is **folded** — the old
per-kind buckets are now object-key prefixes (`delta_one/ volatility/ onchain/ xinstrument/ mtf/`) inside the one
bucket.

## Shard atom + (KEY)

`[pipeline_mode, date, asset_group, venue, instrument_type, data_type, (KEY), quote, margin, source]`.

- **singles → `instrument_id`** (grain pattern #1, flat-per-contract).
- **chains → `underlying`** (grain pattern #2, bundle). `underlying` is a KEY **only** here.

## Instrument-id grammar

`VENUE:TYPE:BASE-QUOTE@MARGIN[-YYYYMMDD][-STRIKE-C|P]` — e.g. `BINANCE:PERPETUAL:BTC-USDT@LIN`,
`DERIBIT:OPTION:BTC-USD@INV-20261225-100000-C`. No `chain=` anywhere in cefi.

## Catalogue (surface 4)

`instruments-store-cefi-prd-{pid}/prod/catalog.parquet` — the only genuinely produced cefi catalogue (~45
`CATALOG_COLUMNS`), built by `instruments-service/scripts/build_instrument_catalogue.py`.

## HAZARDS

### H1 — v5/v6 DUAL chain-tail. Scan for BOTH or you under-count by a whole lane.

Two writers emit cefi chains on **different tails for the same shard**:

- **W2 (Tardis lane)** emits the canonical v6 tail. `tardis_shared.py` returns
  `underlying=…/quote=…/margin=…/ticks.parquet` only when `is_chain and quote_asset and margin_type and underlying`,
  else it falls through to `{file_stem}.parquet`.
- **W1 (`PartitionedTickWriter`)** derives `quote_asset` / `margin_type` **only for tradfi**:

  ```python
  quote_asset, margin_type = "", ""
  if is_derivative and self._asset_group == "tradfi" and itype_str in ("futures_chain", "options_chain"):
      underlying_str, quote_asset, margin_type = _tradfi_chain_partition_dims(underlying_str)
  ```

  — `market-tick-data-service/market_tick_data_service/engine/orchestrator/partitioned_writer.py:290-293`. For cefi both
  stay `""`, so W1 can emit the bare **v5** `underlying={U}/ticks.parquet`.

**Do**: probe both tails per chain shard and report the divergence as a typed finding. **Do not** conclude "chain data
absent" from a v6-only probe.

> **MEASURED 2026-07-20 — cefi chains are 0% captured.** `options_chain` / `futures_chain` hold 0 captured rows (all
> `empty_confirmed` / `expected_unattempted`; 0 v6 rows behind the fork). **Neither tail exists in captured data**, so
> the v5/v6 dual-tail hazard above is currently **latent**, not live. The OPEN QUESTION is therefore not "which tail
> does W1 emit" but **"is ANY cefi chain shard captured at all"** — confirm at least one captured chain shard exists
> before probing tails, and report the measured 0-capture state rather than asserting either tail is reachable.

### H2 — the write-time canonical guard does not cover cefi batch

`_assert_canonical_tradfi_path` **raises** on a non-canonical path, but is called under
`if self._asset_group == "tradfi":` (`partitioned_writer.py:258-259`; guard body `:83-96`). cefi **batch** regressions
therefore fail **silent**. The cefi **live** lane is guarded (`live/websocket_runner.py`, per the guard's own docstring)
— so a batch-vs-live path divergence is possible, which is a batch=live invariant concern. Treat any cefi non-canonical
path found as un-gated drift, not a one-off.

### H3 — `build_cefi_partition_path` has no `pipeline_mode` kwarg

Unlike the defi/tradfi builders, callers bolt the segment on via `.replace()`. A missed replace is a silent
non-canonical write. When you find a cefi object missing `pipeline_mode=`, classify it as this defect class, not as
pre-cutover history — check the cutover date in `codex/02-data/canonical-cutover-register.md` first.

### H4 — migration is IN FLIGHT and `--apply` has NOT run

Phase-C scripts are written and dry-run-validated; the cutover is drain-gated. Expect a **mixed** estate. Do not report
non-canonical counts as regressions — report them against the cutover register. Only ~4 of 63 adapters route through the
shared canonical-id builder, so **new writes can re-drift** even after cutover.

### H5 — `instruments-store-cefi` is not phantom-checked

It is absent from the phantom reconciler's `_BUCKET_KIND_MAP`, so its rows have never been phantom-checked. Absence of
phantom findings there is **absence of evidence**, not evidence of absence — say so in the coverage-gap section.

### H6 — `source=` write-wiring is a RED gap

cefi cells land with `source=""`. Do not read an empty `source` as a data defect per-shard; report it once as the known
wiring gap.

### H7 — the `chain` content column is populated for on-chain perp DEXes — it is display residue, not a path defect

~817k cefi rows (ASTER / HYPERLIQUID / EXTENDED / LIGHTER) carry a non-null `chain` **content** column even though cefi
has **no `chain=` path axis** (measured 2026-07-20). This is display residue, not a canonicalisation defect — do not
flag it as a path/atom violation; report it once if at all.

## Known-good spot-check — run BEFORE trusting any absence result

The generalised lesson from the defi `solana_amm_pool` false negative (SKILL.md § 4b): **an absence result is only
evidence once you have confirmed you probed the vocabulary the writer actually emits.**

1. Enumerate prefixes from the SSOT, never by hand: `canonical_path_templates("cefi")` —
   `unified-api-contracts/unified_api_contracts/registry/possible_manifest.py:352`. It emits **both**
   `pipeline_mode=batch_<source>/` and `pipeline_mode=live_<source>/` prefixes per source (`:315-336`) — probing only
   `batch_` false-phantoms every live-captured cell.
2. **Tardis N=1 — only ONE pipeline_mode/venue is captured per recent day.** `list` the `day={D}/` child prefixes FIRST
   to see which venue actually captured that day; do not assume an arbitrary `(date, venue)` has data (measured: two
   probe rounds burned on recent days with no data for the chosen venue).
3. Pick one `(date, venue)` you already know is captured from the manifest, and confirm your probe returns non-zero
   there.
4. For a **chain** shard, first confirm ANY chain shard is captured (H1 — currently 0%), then probe the v5 tail **and**
   the v6 tail before recording absence.
5. Only then treat a zero as a finding.

## Cross-links

`SKILL.md` · `codex/02-data/four-surface-reconciliation-procedure.md` ·
`codex/02-data/reconciliation-finding-taxonomy.md` · `codex/02-data/canonical-cutover-register.md` ·
`codex/02-data/non-canonical-path-inventory.md` · `codex/02-data/cefi-capture-universe.md` ·
`codex/05-infrastructure/bucket-isolation-model.md`
