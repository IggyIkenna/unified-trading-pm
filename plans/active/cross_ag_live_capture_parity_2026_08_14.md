---
doc_type: plan
title: Cross-AG live capture parity — wired but not producing
summary: |
  A batch-vs-live venue parity audit measured code wiring against prod manifest reality across all five asset groups and
  found five separable defects that no active plan owns — a connector-factory fallthrough that would stamp trades ticks
  with another data_type, DeFi live connectors registered under runtime-unreachable keys, deployed live shards producing
  zero rows in three asset groups, 40 DeFi venues left as BLOCKED-BUILD placeholders with no tracked follow-up, and a
  17k-object DeFi index prefix carrying tens of GB of stale backups.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, e2e-testing, deployment-service]
scope: [engineer]
tags: [live-trading, mtds, batch-live, data-correctness, manifest, wsfeedconnector]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/05-infrastructure/live-pipeline-architecture.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/archive/issues/wsfeedconnector_phase35_gap_2026_07_06.md,
    /plans/active/mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14.md,
  ]
created: 2026-08-14
last_updated: 2026-08-14
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: data_engineering
effort: high
drift_direction: advance-code
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/connectors/,
    market-tick-data-service/market_tick_data_service/cli/handlers/websocket_streaming_handler.py,
    e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py,
    deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh,
  ]
supersedes:
superseded_by:
depends_on:
locked_by:
locked_since:
source: Batch-vs-live venue parity audit, 2026-08-14 interactive session
---

# Cross-AG live capture parity — wired but not producing

> **Track**: LOCAL / human plan (`assigned_vm: NA`). Hand to a Sonnet-5 worker; audit on completion. Covers cefi, defi,
> tradfi and prediction — the sports leg of Finding C is owned by the sports MTDS plan and is cross-referenced, not
> duplicated, here.

## How this was measured (2026-08-14)

Universe taken as UAC `VENUES_BY_ASSET_GROUP` (168 venues), batch capability from `VENUE_DATA_TYPE_CAPABILITIES` (128
venues declared). Live wiring measured by calling `register_all()` and instantiating every `(venue, data_type)` factory,
classifying the result by MRO so BLOCKED-CREDENTIALS and placeholder base classes do not count as coverage. Reality
measured by reading each asset group's prod availability index and grouping live-mode rows by venue, data_type and
capture_status.

Venue-level result, batch-capable venues only:

| asset_group | batch-capable | real live connector | stub/scaffold only | none |
| ----------- | ------------- | ------------------- | ------------------ | ---- |
| cefi        | 22            | 21                  | 0                  | 1    |
| defi        | 96            | 4                   | 40                 | 52   |
| prediction  | 2             | 2                   | 0                  | 0    |
| tradfi      | 8             | 4                   | 0                  | 4    |

DeFi live-manifest rows were NOT measured — the defi availability index is 7.3 GB and the read did not complete in
session. What is directly evidenced: no `mtds-live-defi` VM exists in the running fleet and
`deployment-service/scripts/vm/` has no defi live launcher, so no defi live-capture process exists.

## Finding A — connector factory falls through to the trades connector for unsupported data_types

`_deribit_factory` branches on `book_snapshot_5`, `derivative_ticker` and `depth_of_book_10`, then returns
`DeribitWSFeedConnector` for everything else. `DeribitWSFeedConnector._send_sub_batch` subscribes only to
`trades.<instrument>.100ms` regardless of the `data_type` it was constructed with, and `manifest_recorder` stamps rows
with the shard's declared data_type. So a `cefi:DERIBIT:options_chain` live shard would subscribe to trades and record
the resulting ticks as `options_chain`.

The same shape holds for `_bybit_factory` (its connector matches only the `publicTrade.` topic, yet `liquidations` and
`futures_chain` fall through to it) and `_binance_futures_factory`. Not currently exercised — none of those shards are
launched — but it is a live trap, not a theoretical one, and the launcher comment for the cefi VM explicitly notes
"options_chain WS not yet wired" while the factory silently accepts it.

- [x] [DATA] P1. Make every CeFi connector factory reject an unsupported data_type with a typed error instead of falling
      through to the trades connector — DoD: `_deribit_factory("cefi", "DERIBIT", "options_chain")` raises, and a
      parametrised test asserts every registered venue rejects at least one known-unsupported data_type. — DONE
      2026-08-14: `_deribit_factory`/`_bybit_factory`/`_binance_futures_factory` now raise `NotImplementedError` for any
      `data_type != "trades"` instead of falling through
      (market-tick-data-service/market_tick_data_service/live/connectors/{deribit_ws,bybit_ws,binance_futures_ws}.py);
      parametrised rejection + still-accepts-trades tests added in
      market-tick-data-service/tests/unit/test_cefi_book_ticker_ws_connectors.py
      (`TestFactoryRejectsUnsupportedDataType`).
- [x] [DATA] P1. Audit the manifest for rows whose data_type could have been mis-stamped by this fallthrough before the
      fix — DoD: a query over live rows for the affected (venue, data_type) pairs returning zero `captured` rows, or a
      list of affected rows for remediation. — DONE 2026-08-14: read cefi prod `_index/availability_index.parquet`
      (28,314,889 total rows / 155,406 live rows), filtered to the 7 affected (venue, data_type) pairs (DERIBIT
      options_chain/futures_chain, BYBIT-FUTURES liquidations/futures_chain, BINANCE-FUTURES
      liquidations/options_chain/futures_chain) — **zero rows exist for any of the 7 pairs** (never launched). No
      mis-stamped data in prod; no remediation needed.

## Finding B — DeFi live connectors registered under runtime-unreachable keys

`websocket_streaming_handler` resolves a venue by exact match, then `.lower()`, then `.upper()`. These registered keys
are none of those for any canonical venue: `curve`, `morpho`, `orca`, `raydium`, `phoenix`, `jito`, plus the bare
protocol umbrellas `AAVE_V3` and `COMPOUND_V3`. `CURVE-ETHEREUM`.lower() is `curve-ethereum`, which never matches
`curve`, so a canonical shard-spec cannot reach these connectors even though they are real polling implementations.

The batch-live smoke-matrix validator hides this: its `_normalize_venue_for_match` strips a trailing chain suffix before
matching, so `CURVE-ETHEREUM` resolves to `curve` in the validator and the cell reads as wired. The validator is more
permissive than the runtime it is meant to prove.

- [x] [DATA] P1. Re-register the affected DeFi connectors under canonical `VENUES_BY_ASSET_GROUP` venue names — DoD: for
      every defi venue with a real connector, `WS_FEED_CONNECTOR_FACTORIES` resolves the exact canonical token; a test
      iterates the venue list and asserts resolution with no normalisation. — DONE 2026-08-14: `curve`/`morpho`/`orca`/
      `raydium` now also register under `CURVE-ETHEREUM`/`MORPHO-ETHEREUM`/`ORCA-SOLANA`/`RAYDIUM-SOLANA` (bare legacy
      keys kept for existing callers) —
      market-tick-data-service/market_tick_data_service/live/connectors/{curve_defi_ws,morpho_defi_ws,orca_defi_ws,raydium_defi_ws}.py@44db26bce0.
      `jito` was already correctly dual-registered under `JITO-SOLANA`; `phoenix` handled separately below (no canonical
      target exists). Canonical-key resolution tests added per connector in
      market-tick-data-service/tests/unit/test_{curve,morpho,orca,raydium}_defi_ws_connector.py@44db26bce0.
- [x] [DATA] P1. Make the validator's venue matching identical to the runtime handler's, or have it call the handler's
      resolver directly — DoD: a venue reachable in the validator but not at runtime RED-fails the smoke matrix; prove
      with the pre-fix `CURVE-ETHEREUM` case. — DONE 2026-08-14: extracted the exact/`.lower()`/`.upper()` lookup order
      out of `_resolve_connector` into a new shared `resolve_ws_feed_venue_key()` —
      market-tick-data-service/market_tick_data_service/cli/handlers/websocket_streaming_handler.py@44db26bce0;
      `validate_batch_live_smoke_matrix.py`'s `resolve_live_venue_key` now delegates to it instead of its own
      chain-suffix-stripping `_normalize_venue_for_match` (deleted) —
      e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py@bb2e2316d5. Pre/post-fix `CURVE-ETHEREUM` case
      proven directly in
      market-tick-data-service/tests/unit/test_websocket_streaming_handler.py::TestResolveWsFeedVenueKey@44db26bce0
      (e2e-testing has no service-to-service dependency on MTDS, so its own test suite proves delegation via a stub
      injection instead — e2e-testing/tests/unit/test_validate_batch_live_smoke_matrix.py@bb2e2316d5).

**2026-08-14 correction to this finding's venue list — `phoenix` is not a casing bug.** Re-registration landed for
`curve`→`CURVE-ETHEREUM`, `morpho`→`MORPHO-ETHEREUM`, `orca`→`ORCA-SOLANA`, `raydium`→`RAYDIUM-SOLANA` (all single-chain
real connectors; `jito` was already correctly dual-registered under `JITO-SOLANA`). `phoenix` could not be fixed the
same way: `PHOENIX-SOLANA` is not in current UAC `VENUES_BY_ASSET_GROUP` at all (verified live — 168-venue universe,
zero `phoenix` substring match). It was deliberately excluded 2026-07-22
(`unified_api_contracts/registry/defi_venues.py:800`) after its REST API (`api.phoenix.trade`) went NXDOMAIN —
deprecated 2026-05-15 per `unified_api_contracts/external/phoenix/schemas.py`. So `phoenix_ws.py`'s registration isn't
reachable under any canonical key because there IS no canonical key, not because of a resolver mismatch — re-registering
it would mean inventing a venue UAC has already ruled out. The validator/resolver fix above still applies to this
connector (correctly), it just can never turn green for `phoenix` while the venue stays excluded.

- [ ] [OPERATOR] P2. Rule on `phoenix_ws.py`: delete it as dead code targeting a UAC-excluded venue (the honest option,
      since Jupiter-routed polling still can't produce a `PHOENIX-SOLANA` canonical row), or make the case to restore
      `PHOENIX-SOLANA` to `VENUES_BY_ASSET_GROUP` for live-only coverage despite the dead REST API — DoD: the ruling is
      recorded here and `phoenix_ws.py` either removed or left in place with the ruling cited in its docstring.

## Finding C — deployed live shards producing zero rows in three asset groups

Measured from prod manifests on 2026-08-14:

- **Sports** — `mtds-live-sports-odds-api-trades` has been RUNNING since 2026-08-04. All 97 live sports rows are
  `empty_confirmed` or `attempted_failed`; `ODDS_API` trades `empty_confirmed` as recently as 2026-08-14. Zero captured.
- **Prediction** — three live VMs RUNNING since 2026-08-03. Real captured rows exist but stop at 2026-08-03
  (`book_snapshot_5`) and 2026-08-05 (`trades`) — roughly nine days stale while the processes run.
- **TradFi** — `mtds-live-tradfi-cme-trades` RUNNING since 2026-08-09. 212 live rows total, of which 28 are `captured`
  (`CME` trades, 2026-06-22..2026-08-11); `ohlcv_15m` is 64 rows of `attempted_failed`.
- **CeFi** — healthy for six venues through 2026-08-14 (ASTER, BINANCE-FUTURES, HYPERLIQUID, KRAKEN-FUTURES,
  OKX-FUTURES, plus BYBIT in June), but several launched shards produce nothing: every `BYBIT-FUTURES` data_type is
  `empty_confirmed`, `DERIBIT` `derivative_ticker` is `empty_confirmed` only, and `COINBASE-SPOT` / `OKX-SWAP`
  `depth_of_book_10` are `empty_confirmed` only.

The sports leg is already owned by `/plans/active/mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14.md` P0.
The rest is unowned.

- [ ] [DATA] P1. Diagnose the prediction live-capture stall — captured rows stop 2026-08-03/08-05 while three VMs run —
      DoD: root cause named with evidence, then a captured row dated after the fix.
- [ ] [DATA] P1. Diagnose the tradfi CME live shard producing 28 rows since 2026-06-22 and `ohlcv_15m` failing outright
      — DoD: root cause named; state whether the Databento live subscription actually covers the requested schema.
- [ ] [DATA] P1. Diagnose the four cefi shards launched but producing only `empty_confirmed` (BYBIT-FUTURES all
      data_types, DERIBIT derivative_ticker, COINBASE-SPOT and OKX-SWAP depth_of_book_10) — DoD: per-shard root cause; a
      shard that is correctly empty by design is re-labelled as such rather than left looking broken.
- [ ] [DATA] P1. Add a standing live-capture-productivity check across all asset groups — a shard with a running process
      and zero `captured` rows over N days must page — DoD: replaying the check against the 2026-08 manifest window
      fires on sports, prediction and the four cefi shards; routes per the actionable-only alerting rule.

## Finding D — 40 DeFi venues are BLOCKED-BUILD placeholders with no tracked follow-up

`dex_swap_scaffold_ws.py` and `defi_lending_scaffold_ws.py` register 40 canonical DeFi venues whose `connect()` raises
`NotImplementedError` with a BLOCKED-BUILD message. That was the correct honest-absence move at the time. But
`/plans/archive/issues/wsfeedconnector_phase35_gap_2026_07_06.md` closed `status: resolved` with 17/17 todos done, and
its own text defers the real work to "10 P2 CODE tasks (one per protocol family) — real subgraph pollers ... file as
separate CODE tasks after operator triage". A grep of `plans/active/` for that follow-up returns **zero** hits.

So the tracked record says DeFi live is resolved, while 40 venues cannot stream and 52 more have no connector at all.

- [ ] [OPERATOR] P1. Decide whether DeFi live capture is in scope at all before any build — there is no defi live VM, no
      defi live launcher, and DeFi is nominally the May-23 critical path; the honest options are to build the pollers,
      or to declare DeFi live BATCH-ONLY-BY-DESIGN and stop carrying 40 placeholder registrations that read as coverage
      — DoD: the ruling is recorded here.
- [ ] [DATA] P1. Whichever way that ruling goes, make the archived gap doc's status honest — DoD: either the follow-up
      tasks exist as tracked todos, or the placeholders are reclassified with the ruling cited; "resolved" must not mean
      "scaffolded".

## Finding E — DeFi index prefix carries 17k objects and tens of GB of stale backups

The defi market-data bucket's `_index/` prefix holds 17,191 objects. `availability_index.parquet` alone is 7.3 GB, and
alongside it sit at least a dozen multi-GB `.bak` snapshots (several `dex_pool_fees_*` backups at ~6.4 GB each, plus
`.undelist`, `.deindexed`, `.dualform` and other dated variants) totalling tens of GB. The 7.3 GB live index is also why
any full-index read is impractical — it defeated a read in this session and is worth knowing before anyone plans one.

Note the manifest consolidator itself is healthy — `uts-prod-manifest-consolidator-market-data-defi` executes every 60s
and succeeded on all recent runs; the index's age reflects the incremental-cutoff design and scale, not a broken job.

- [ ] [OPERATOR] P1. Rule on retention for the `_index/*.bak*` snapshots in the defi prod bucket — prod-bucket deletes
      are human-only unless reversibility-qualified; cite `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` —
      DoD: a retention rule recorded here, then executed under that protocol.
- [ ] [DATA] P2. Give consumers a projected/filtered read path for the defi index so an audit does not need the full 7.3
      GB — DoD: a documented `read_availability_index` call pattern (column projection plus pipeline_mode filter) that
      answers "which live shards captured" without a full decode.

## Progress Log

_(append dated entries here)_

- **2026-08-14**: Findings A and B (both todos each) DONE. Finding A: cefi factory fallthrough fixed
  (market-tick-data-service@44db26bce0) + manifest audit found zero mis-stamped rows (bug was live but never exercised —
  7 affected (venue, data_type) pairs, all zero rows). Finding B: curve/morpho/orca/raydium re-registered under
  canonical UAC keys, resolver logic deduplicated into a shared `resolve_ws_feed_venue_key()` used by both the runtime
  handler and the smoke-matrix validator (market-tick-data-service@44db26bce0, e2e-testing@bb2e2316d5). Correction
  recorded in-finding: `phoenix` cannot be fixed by re-registration — `PHOENIX-SOLANA` isn't in current UAC
  `VENUES_BY_ASSET_GROUP` (excluded 2026-07-22, dead REST API) — new `[OPERATOR]` P2 todo added under Finding B to rule
  on deleting `phoenix_ws.py` vs restoring the canonical venue. Findings C, D, E untouched (out of scope — owned by
  Workers A/C per the 3-way split).
