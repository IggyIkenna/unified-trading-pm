---
doc_type: issue
title:
  "CeFi Tardis write-time SchemaContract validation cannot be turned on as-is — the registered contracts require columns
  (ts_event, size) that the real Tardis wire format never produces (timestamp, amount); flipping validate=True today
  would fail-hard 100% of real CeFi Tardis trades/liquidations/quotes shard writes"
summary: >-
  batch_live_filename_divergence_sanitize_symbol_2026_07_20.md § 5 open-work item 3 asks to turn `validate=True` on the
  two `tardis_cefi_shards.py` write sites and make `finalise_rows_and_path` violations FATAL. The FATAL-enforcement
  mechanism is safe and has been shipped (mirrors the DeFi `write_defi_rows`/`canonical_write.py` precedent — raises
  ValueError + emits SCHEMA_CONTRACT_VIOLATION on any violation when `validate=True`). Turning `validate=True` on AT THE
  TWO CEFI CALL SITES was NOT done — verified by reading the real Tardis CSV wire header
  (`exchange,symbol,timestamp,local_timestamp,id,side,price,amount` — see
  `tests/market_interface/clients/test_tardis_stream_processor.py:30`) against every registered CeFi trades/
  liquidations/quotes SchemaContract (`CEFI_PERPETUAL_TRADES`, `CEFI_SPOT_PAIR_TRADES`, `CEFI_PERPETUAL_LIQUIDATIONS`,
  `CEFI_PERPETUAL_QUOTES`, `CEFI_OPTIONS_CHAIN_TRADES`, `CEFI_FUTURES_CHAIN_TRADES` — `unified-api-contracts/
  unified_api_contracts/internal/schemas/contracts.py:216-351`), all of which require `ts_event` (datetime64[ns, UTC])
  and `size` (float64) columns that NO real Tardis-sourced DataFrame ever carries at the point `finalise_rows_and_path`
  is called — the raw wire columns are `timestamp` (epoch int, unit undetermined) and `amount` (float64). No rename or
  cast step exists anywhere in the write path (grepped `tardis_shared.py`, `tardis_cefi_shards.py`, `tardis_adapter.py`,
  `tardis_batch_download.py`, `tardis_csv_transport.py` — zero hits for `ts_event` or `timestamp`→`ts_event` handling).
  Flipping `validate=True` today would make EVERY real CeFi Tardis trades/liquidations/quotes shard write fail its
  schema contract and self-isolate as `attempted_failed` (shard-level isolation swallows the raise, so the failure is
  silent — zero crash, zero data written, retried and re-failed every future backfill wave forever) — exactly the silent
  `attempted_failed` billing-waste pattern the workspace already audits for.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [data-correctness, schema-contract, write-time-guard, fail-hard, tardis, operator-notify]
related: [batch_live_filename_divergence_sanitize_symbol_2026_07_20, fail_hard_canonical_enforcement_design_2026_07_20]
created: 2026-07-27
priority: P1
parent_epic: cefi_master
source:
  "Surfaced while executing batch_live_filename_divergence_sanitize_symbol_2026_07_20.md open-work item 3 (turn
  validate=True on the two tardis_cefi_shards.py write sites)."
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# CeFi Tardis write-time SchemaContract validation blocked on a real column-name mismatch

> **🔴 OPERATOR-NOTIFY — data pipeline correctness.** Turning on write-time schema enforcement for CeFi Tardis writes,
> as directed, would silently zero out every future CeFi Tardis backfill/live-capture wave (100% shard failure, isolated
> so it never crashes — just never writes anything, forever, on retry). NOT shipped as-is.

## 1. What was asked

`batch_live_filename_divergence_sanitize_symbol_2026_07_20.md` § 5 open-work item 3: _"Turn `validate=True` on the two
`tardis_cefi_shards.py` write sites and make `finalise_rows_and_path` violations FATAL, not advisory (fail hard, per the
operator's write-path directive)."_

## 2. What shipped (safe half)

`finalise_rows_and_path` (`market-tick-data-service/.../adapters/cefi/tardis_shared.py`) now raises `ValueError` (and
emits a `SCHEMA_CONTRACT_VIOLATION` `log_event`) when `validate=True` and the row-group violates its looked-up UAC
`SchemaContract` — mirroring the existing DeFi precedent (`write_defi_rows`/`canonical_write.py:340-363`, which has done
exactly this for DeFi writes since it shipped). Previously violations were computed but silently discarded as an
"advisory list the caller never inspects." This part is a pure additive safety mechanism: it is a no-op for every caller
that still passes `validate=False`, so it changes ZERO behaviour until a caller opts in.

## 3. What was NOT shipped — the real mismatch

The two CeFi write call sites (`tardis_cefi_shards.py:118` inside `_write_one_cefi_shard`, and `tardis_cefi_shards.py`
inside `_tardis_cefi_shard_router`'s streaming generator) still pass `validate=False`. Turning them to `True` was
reverted after verifying the following:

**The real Tardis CSV wire header** (confirmed via `tests/market_interface/clients/test_tardis_stream_processor.py:30`
and `tests/unit/test_tardis_book_snapshot_v7.py:29-39`, both of which construct fixtures matching Tardis's actual export
format):

```
exchange,symbol,timestamp,local_timestamp,id,side,price,amount
```

**The registered SchemaContracts every CeFi trades/liquidations/quotes write looks up**
(`unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py:216-351` — `CEFI_PERPETUAL_TRADES`,
`CEFI_SPOT_PAIR_TRADES`, `CEFI_PERPETUAL_LIQUIDATIONS`, `CEFI_PERPETUAL_QUOTES`, `CEFI_OPTIONS_CHAIN_TRADES`,
`CEFI_FUTURES_CHAIN_TRADES`) all require:

- `ts_event` — `datetime64[ns, UTC]`, non-nullable
- `size` — `float64`, non-nullable

Neither column is ever produced by the real write path. Grepped for a rename/cast step across every file in the chain
(`tardis_shared.py`, `tardis_cefi_shards.py`, `tardis_adapter.py`, `tardis_batch_download.py`,
`tardis_csv_transport.py`) — zero hits for `ts_event`, and the only place `amount` is touched is a dtype-normalise-to-
float64 (`tardis_csv_transport.py:345-346`), never a rename to `size`. `side` and `price` DO match the contract (present
verbatim on the wire) — the gap is exactly these two columns.

`validate_dataframe` (`unified-api-contracts/.../internal/schemas/_validation.py`) does exact column-name matching, no
aliasing. So with `validate=True`, every real CeFi Tardis `trades`/`liquidations`/`quotes` shard would fail with (at
minimum) `missing_column:size` and `missing_column:ts_event` (or `wrong_dtype:ts_event` if a rename-without-cast were
added) — a **100% write failure rate** for every venue, isolated per-shard so it never crashes, just silently records
`attempted_failed` and retries-and-refails every future wave. Measured today: CeFi Tardis capture has been paused since
2026-06-29 (per `fail_hard_canonical_enforcement_design_2026_07_20.md` § 1 E2), so this has NOT yet hit live traffic —
but it would hit the very next CeFi Tardis backfill or capture-resume the moment this ships.

## 4. Why this needs a decision, not a mechanical fix

Two candidate fixes exist and picking between them is a genuine design call, not a mechanical rename:

- **(a) Fix the writer** — rename `amount`→`size` (trivial, dtype already float64) and derive `ts_event` from
  `timestamp` via `pd.to_datetime(df["timestamp"], unit=<?>, utc=True)`. The unit is the risk: Tardis's documented epoch
  unit for `timestamp`/`local_timestamp` is disputed within this very codebase — the existing `_apply_time_filter`
  helper (`tardis_csv_transport.py:354`) parses `local_timestamp` with `unit="ns"`, but Tardis's own docs describe these
  fields as **microseconds** since epoch. Picking the wrong unit does not raise — it silently produces a
  plausible-looking but WRONG `ts_event` for every row (a far worse outcome than the current fail-closed gap), so this
  needs the unit verified against a real GCS sample before it ships, not guessed.
- **(b) Fix the contracts** — rename `_TS_EVENT`/`_SIZE`'s expected column names to match the real wire
  (`timestamp`/`amount`) for the CeFi trades/liquidations/quotes contracts specifically. This diverges CeFi's column
  vocabulary from every other asset_group's `ts_event`/`size` convention, which may itself be a cross-asset-group
  consistency regression other readers depend on.

Given `fail_hard_canonical_enforcement_design_2026_07_20.md`'s own staged-rollout caution (Stage 1 write-enforce is
approved in principle but explicitly gated on closing 3 adversarially-confirmed gaps first, § 5) and the "Data pipeline
correctness is the heartbeat" hard rule (no deadline deferrals, but also no blind flips that zero out real data), this
is being escalated rather than resolved unilaterally by the worker.

## 5. Recommendation

Recommend (a) with the unit verified against a real captured GCS sample first (compare a `timestamp` value's rendered
date against the `day=` partition it lives under — if `unit="us"` lands in the right day and `unit="ns"` doesn't, that
settles it) before deriving `ts_event`, over (b) — matching every other asset_group's `ts_event`/`size` convention keeps
the CeFi contract from being a one-off exception downstream readers have to special-case.

## 6. Open work

- [x] ✅ [DESIGN] P1. Decide (a) vs (b) above; if (a), verify the real `timestamp` epoch unit against a live GCS sample
      before writing the `pd.to_datetime(..., unit=?)` call (repo: unified-api-contracts or market-tick-data-service
      depending on the decision). — unified-trading-pm (this doc) @ decision below, § 8. **Decided: (a), unit="us".**
- [ ] [SERVICE] P1. Implement the chosen fix (rename `amount`→`size`, derive `ts_event` via
      `pd.to_datetime(df["timestamp"], unit="us", utc=True)`), **plus the price/amount dtype-coercion gap found during
      verification (§ 8.2)** — add explicit `pyarrow.csv.ConvertOptions(column_types={...})` entries for `price` and
      `amount` (trades/liquidations) and `bid_price`/`ask_price`/`bid_size`/`ask_size` (quotes) so they land as
      `float64` regardless of whether the sampled values happen to be all-integer, mirroring the existing v6/v7
      `funding_rate`/`mark_price`/book-snapshot-level precedent in `tardis_csv_transport.py`'s
      `_decompress_and_parse_csv_legacy` — the streaming path (`stream_bulk_csv_to_parquet`, called from
      `download_csv_streaming`) currently passes NO `convert_options` at all, so it needs this typing added from
      scratch, not just extended. Then turn `validate=True` on both `tardis_cefi_shards.py` write sites
      (`_write_one_cefi_shard` and `_tardis_cefi_shard_router`) — the `finalise_rows_and_path` FATAL-enforcement
      mechanism is already shipped and ready to receive `validate=True`. Verify against a real captured GCS sample (not
      just synthetic test rows) that a real shard validates clean before shipping — reuse the sampling recipe in § 8.1
      (a `pipeline_mode=batch_tardis` shard from before the 2026-06-29 capture pause).

## 7. Codex SSOTs

- `plans/active/issues/batch_live_filename_divergence_sanitize_symbol_2026_07_20.md` § 5 — the originating todo.
- `plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md` — the staged fail-hard rollout design this
  todo is Stage-1-adjacent to.
- `/codex/02-data/data-pipeline-correctness-hard-rule.md` — why this is escalated rather than shipped blind.

## 8. Decision (resolved 2026-07-27)

**Decided: (a) — fix the writer.** Rename `amount`→`size`, derive `ts_event` from `timestamp` via
`pd.to_datetime(df["timestamp"], unit="us", utc=True)`. Rejected (b) (loosen the contract to accept `timestamp`/
`amount` verbatim) because: the unit risk that motivated escalating this decision is now closed (§ 8.1); (a) keeps CeFi
on the same `ts_event`/`size` vocabulary every other asset_group's contracts + downstream readers
(features-service/strategy-service/ml-service/batch-live-reconciliation-service) already use, instead of creating a
permanent CeFi-only special case; and (b) would NOT even avoid the implementation work below (§ 8.2) — the dtype gap
exists in the raw wire parse independent of which column names the contract expects.

### 8.1 Epoch unit — verified against a live GCS sample

Sampled a real pre-pause capture (path verbatim, unwrapped so it stays copy-pasteable):

```
gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2026-06-29/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/instrument_type=perpetual/data_type=trades/BITFINEX-FUTURES:PERPETUAL:BTC-USDT@LIN.parquet
```

27,123 rows; `pipeline_mode=batch_tardis` confirms a genuine Tardis-sourced capture, not a synthetic/test fixture.
Parsed `timestamp` (raw wire int64, e.g. `1782691205021000`) under all four candidate units and checked whether the
result lands inside the `day=2026-06-29` partition it was written under:

| unit | result                             | verdict                                                              |
| ---- | ---------------------------------- | -------------------------------------------------------------------- |
| `s`  | `OverflowError` (out of bounds)    | impossible — rejected                                                |
| `ms` | `OverflowError` (out of bounds)    | impossible — rejected                                                |
| `us` | `2026-06-29T00:00:05.021000+00:00` | **lands in day=2026-06-29 — correct**                                |
| `ns` | `1970-01-21T15:11:31.205021+00:00` | silently wrong (no error — would NOT have been caught by validation) |

Not just the first row: parsing the FULL shard's `timestamp` column with `unit="us"` gives `min=2026-06-29 00:00:05.021`
/ `max=2026-06-29 23:59:55.921` — every one of the 27,123 rows lands inside the correct calendar day, exactly the shape
of one day's trades. `local_timestamp` (raw `1782691205033055`) confirms the same result. The derived Series' dtype is
`datetime64[ns, UTC]` — an exact match for the `_TS_EVENT` contract spec, no further cast needed.

This also resolves the disputed existing helper cited in § 4: `_apply_time_filter` (`tardis_csv_transport.py:354`,
parses `local_timestamp` with `unit="ns"`) is confirmed WRONG — it silently produces a 1970-01-21 timestamp with no
error. Traced its blast radius: it only fires when a caller passes `start_time`/`end_time` into `download_csv`; both
real production call sites (`tardis_batch_download.py:811`, `tardis_bulk_download.py:514`) call `download_csv` WITHOUT
`start_time`/`end_time`, and the only other route (`TardisAdapter.fetch_trades` → `market_interface/api.py`'s unified
`fetch_trades`) also never forwards them for Tardis — so this is a real bug but currently dormant/unreachable in
production, not an active data-correctness incident. Left as-is (out of this todo's scope — no live caller exercises
it), but noting it here since it's the same wrong-unit failure mode this decision just resolved for the write path;
worth a P3 cleanup pass if a future caller starts passing `start_time`/`end_time` through to Tardis.

### 8.2 New finding: `price`/`amount` dtype is not guaranteed `float64` (independent of a/b)

While sampling, `price` on the BTC-USDT@LIN shard above came back as `int64`, not `float64` (all 27,123 sampled prices
happened to be whole numbers, e.g. `59601`) — a THIRD schema-contract gap beyond `ts_event`/`size`, since `_PRICE`
requires `float64`. Cross-checked against two more real shards from the same day/venue to rule out a one-off: ADA-USDT
(`price` fractional, e.g. `0.14384`) and AAVE-USDT (`price` fractional, e.g. `92.169`) both came back `float64`. This
confirms the mechanism is PyArrow's per-column type inference sampling the first block of CSV values — the SAME class of
bug this file already fixed for `funding_rate`/`mark_price`/`index_price`/book-snapshot price/amount levels via explicit
`column_types` overrides (see the v6/v7 comments in `_decompress_and_parse_csv_legacy`,
`tardis_csv_transport.py:270-293`) — but plain `price`/`amount` (trades/liquidations) and `bid_price`/`ask_price`/
`bid_size`/`ask_size` (quotes) were never added to that explicit-typing list. Worse, the STREAMING write path
(`stream_bulk_csv_to_parquet`, called from `download_csv_streaming`) passes NO `convert_options` at all — not even the
existing legacy-path coverage — so it has zero protection for ANY column, including `amount` (which the legacy path at
least casts post-hoc via `.astype("float64")` on the materialised DataFrame, a step the streaming path never performs
since it never materialises a DataFrame). Net effect: even after the ts_event/size fix above, `validate=True` would
still intermittently fail — for any symbol/day/shard where sampled prices happen to be all-integer (BTC-USDT and
plausibly other high-value-quote pairs, at least in some windows) — invisibly reintroducing the exact silent
`attempted_failed` failure mode this whole escalation exists to prevent. Folded into item 2 above rather than filed as a
separate issue doc — same root cause, same fix location, same implementer.
