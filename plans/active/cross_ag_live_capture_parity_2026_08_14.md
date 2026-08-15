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
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/websocket_streaming_handler.py,
    /plans/active/issues/prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md,
    /plans/archive/issues/wsfeedconnector_phase35_gap_2026_07_06.md,
    /plans/active/issues/uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md,
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

- [x] [DATA] P0. Unblock market-tick-data-service commits — `market_tick_data_service/live/websocket_runner.py` is 902
      lines against the flat 900-line hard gate, taken from 892 to 902 by `market-tick-data-service@0974060a`
      (2026-08-14, "lazily register a buffer for fan-out connector tick ids"), so `quality-gates.sh` fails for every
      MTDS change regardless of what it touches — DoD: `bash scripts/quality-gates.sh` green in
      market-tick-data-service; coordinate with whoever owns 0974060a before editing, the commit is hours old and the
      slot is shared. ✅ Resolved by the introducing commit's own author, `market-tick-data-service@adf74dcf11`
      (extracted `_register_lazy_buffer()`, 897 lines, quality gates green — 10,676 tests). See
      `/plans/active/issues/mtds_websocket_runner_over_900_line_cap_blocks_commits_2026_08_14.md`.
- [ ] [DATA] P1. Close the pending captured-row verification for the four cefi shards — the fix is deployed but recovery
      was never proven, because instruments-service had published 0 CEFI catalog blobs for 2026-08-14 at check time (vs
      22 on 08-12/08-13), blocking every venue on the VM uniformly — DoD: at least one `captured` live row for each of
      BYBIT-FUTURES, DERIBIT derivative_ticker, COINBASE-SPOT depth_of_book_10 and OKX-SWAP depth_of_book_10 dated after
      the fix; if the catalog gap recurs, file it as its own issue rather than re-deferring this.

- [ ] [DATA] P1. Diagnose the prediction live-capture stall — captured rows stop 2026-08-03/08-05 while three VMs run —
      DoD: root cause named with evidence, then a captured row dated after the fix. **DIAGNOSED 2026-08-14, NOT CLOSED —
      DoD's captured-row half unmet, fix is out of this session's ownership.** Two independent root causes, both with
      full log/GCS evidence: (A) `LiveWebsocketRunner`'s hot-reload path
      (`InstrumentCacheRefreshConsumer`/`apply_instrument_delta`,
      `market_tick_data_service/live/websocket_runner.py:325-390`) is never wired into the real entrypoint —
      `WebsocketStreamingHandler.run()` (`cli/handlers/websocket_streaming_handler.py:220-266`) constructs
      `LiveWebsocketRunner(...)` without `cache_refresh_consumer=`, so every live VM resolves its instrument universe
      exactly ONCE at boot (confirmed: `resolved N instruments prediction/<VENUE>` appears exactly once in each VM's
      full run.log, never again) and never picks up newly-listed markets as old ones settle. (B) Independently,
      instruments-service's POLYMARKET `instrument_availability` catalog writer stopped producing entirely after
      2026-08-05 (KALSHI's writer, same service, stayed fresh every day through 08-14) — confirmed via direct GCS
      listing. Both are inside `market_tick_data_service/live/**`/`cli/handlers/websocket_streaming_handler.py` (owned
      by the connector/handler worker on this plan, not VM-launchers/shard-configs/alerting) and instruments-service
      respectively — filed as
      `/plans/active/issues/prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md`
      with both root causes as tracked `- [ ]` todos. Leaving this todo OPEN until that doc's fix lands and produces a
      captured row after — no restart/relaunch of the prediction VMs would help without the code fix, so none was
      attempted.
- [x] [DATA] P1. Diagnose the tradfi CME live shard producing 28 rows since 2026-06-22 and `ohlcv_15m` failing outright
      — DoD: root cause named; state whether the Databento live subscription actually covers the requested schema. —
      DONE 2026-08-14: root cause is a Databento account billing outage, NOT a code bug —
      `mtds-live-tradfi-cme-     trades-20260809-163443`'s run.log shows `gateway error code=api_key_deactivated` +
      `CRAM authentication error: ... unpaid invoice` at 2026-08-12T00:03:57Z, one failed reconnect, then silence for
      ~50h with the process still heartbeating (invisible to any liveness check). Manifest confirms the exact boundary:
      captured cleanly 08-09..08-11, 100% `empty_confirmed` from 08-12 onward. This is a RECURRENCE of
      `/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md` (resolved 2026-08-10, broke again
      2026-08-12) — updated that doc with the new evidence, reopened `status: blocked`, added a fresh `[OPERATOR] P0`
      pay-the-invoice-again todo (kept the original as history) and a `[CODE] P2` todo flagging the connector's missing
      reconnect/backoff for its owner. **Schema question answered directly: NO** — Databento's live API only streams
      `ohlcv-1s`/`ohlcv-1m` (confirmed in both the live connector's `_DATA_TYPE_TO_SCHEMA` map and
      `/codex/02-data/tradfi-databento-sourcing-ssot.md`); `ohlcv_15m` is MDPS-derived-only and structurally cannot be
      requested live — no VM is currently launched with that shard-spec (confirmed via `gcloud compute instances list`,
      only one `mtds-live-tradfi-*` VM exists, `trades` only), so the 64 historical `attempted_failed` rows are a
      pre-existing artifact, nothing currently running to fix. Did not restart the VM — the feed is dead on the vendor
      side, a restart would not fix anything, per diagnose-before- restart.
- [x] [DATA] P1. Diagnose the four cefi shards launched but producing only `empty_confirmed` (BYBIT-FUTURES all
      data_types, DERIBIT derivative_ticker, COINBASE-SPOT and OKX-SWAP depth_of_book_10) — DoD: per-shard root cause; a
      shard that is correctly empty by design is re-labelled as such rather than left looking broken. — DONE 2026-08-14:
      all four are GENUINE BUGS (none correctly-empty-by-design), all already root-caused and code-fixed upstream
      between 2026-08-09 13:13-14:13 UTC — `mtds-live-cefi-consolidated-20260809-121034` (booted 12:12 UTC that day,
      confirmed via `creationTimestamp == lastStartTimestamp` never restarted) was just running pre-fix code. Per-shard
      cause: **BYBIT-FUTURES** (all data_types) — Tardis-alias venue name never resolved to IS's `BYBIT`-keyed
      instruments.parquet, zero instruments ever subscribed (`market-tick-data-service@e3bd10b9`,
      `_resolve_is_lookup_venue`). **DERIBIT derivative_ticker** — the combined ~2,997-instrument `public/subscribe`
      request exceeds Deribit's channel limit and is rejected/closed, looping forever (`@90e2336c`, chunked subscribe).
      **COINBASE-SPOT depth_of_book_10** — subscribed to the deprecated auth-only `level2` channel and silently
      swallowed the rejection frame (`@cc736408`, switched to `level2_batch`). **OKX-SWAP depth_of_book_10** —
      instrument-ID builder didn't round-trip the `@LIN`/`@INV` margin marker IS attaches, so every subscribe targeted a
      nonexistent wire id (`@52383e87`+`@98fad5ad`). Verified none is the Finding-A fallthrough (all four factories
      explicitly branch on their data_type). **Fix applied**: 3-signal staleness check (boot==last-start timestamp; live
      log tail; 8-61GB per-shard log files from continuous retry-fail spam, matching each diagnosed cause) confirmed the
      VM was safe to cycle — deleted `mtds-live-cefi-consolidated-20260809-121034`, relaunched via
      `launch-mtds-live-cefi-consolidated.sh` (`mtds-live-cefi-consolidated-20260814-041422`), confirmed the new VM's
      on-disk code contains `_resolve_is_lookup_venue`/`_MAX_CHANNELS_PER_SUBSCRIBE_MSG` (the fix functions). Caught and
      stopped a duplicate-VM race from a too-fast second launch attempt before it created a second VM. **Captured-row
      verification NOT YET obtained** — as of this session, instruments-service had not yet published 2026-08-14's CEFI
      instrument catalog at all (0 blobs under `instrument_availability/by_date/day=2026-08-14/`, vs 22 on 08-12/08-13;
      08-13's catalog itself wasn't published until 13:37 UTC) — this affects EVERY cefi venue on the VM uniformly,
      including the 6 previously-healthy ones, confirming it's an unrelated IS daily-catalog-timing gap, not a
      regression from this fix. Re-check after ~13:00 UTC today for captured rows on all four shards.
- [x] [DATA] P1. Add a standing live-capture-productivity check across all asset groups — a shard with a running process
      and zero `captured` rows over N days must page — DoD: replaying the check against the 2026-08 manifest window
      fires on sports, prediction and the four cefi shards; routes per the actionable-only alerting rule. — DONE
      2026-08-14: added **DP-LIVE-004** to
      `deployment-service/deployment_service/data_pipeline_monitors/     live_stream_watcher.py`
      (`check_live_capture_productivity` + `build_running_live_shards`, generalized across every registered
      `LONG_LIVED_LIVE` VM prefix — not just prediction — and grouped per `(venue, data_type)` so a single consolidated
      multi-shard VM, e.g. the cefi VM, is evaluated per-shard) — fires when a shard's `attempted_at` is recent (proving
      it's still alive, not DP-LIVE-001's job) but its last `captured` row (if any) is older than `stale_capture_days`
      (default 3d) or never happened. Routes via the existing `DP_CRON_DID_NOT_FIRE` → `#data-pipeline-alerts` →
      PAGE_OPERATOR path (actionable-only, matches the alerting rule). Replay-tested with 3 unit tests mirroring the
      exact diagnosed shapes: sports (recent attempts, never captured), prediction (fresh attempts, last captured 9 days
      ago), and the cefi consolidated VM (5 dead venue/data_type groups fire, 2 healthy ones on the SAME shard correctly
      don't) — all pass (`tests/unit/test_data_pipeline_monitors.py::test_dp_live_004_*`). Also fixed an adjacent bug
      found in the same file: `build_prediction_live_shards()` resolved a GCS bucket kind (`"market-data"`) that has no
      per-asset_group entry for prediction, silently returned `[]` on every sweep via a blanket `except`, and so
      DP-LIVE-001/002 had never evaluated a single prediction VM — fixed to the correct flat
      `market-data-tick-prediction` kind (mirrors the existing DP-FETCH-009 fix for the same class of bug) and stopped
      swallowing the failure silently. Shipped: `deployment-service@ebeef843c9` (landed on `live-defi-rollout`).

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

- **2026-08-14 (Finding C, non-sports legs — VM-launchers/shard-configs/alerting-check scope)**: tradfi CME todo DONE
  (Databento billing recurrence root-caused, `ohlcv_15m` schema question answered NO — see todo for full evidence; issue
  doc `tradfi_databento_account_billing_suspended_2026_08_09.md` updated + reopened `blocked`). Four-cefi-shards todo
  DONE (all genuine bugs, all already fixed upstream 2026-08-09, root-caused per-shard; cycled the stale
  `mtds-live-cefi-consolidated-*` VM to deploy the fix, confirmed the fix code is present on the new VM; caught and
  stopped a duplicate-VM race mid-launch). Productivity-check todo DONE — shipped DP-LIVE-004
  (`deployment-service@ebeef843c9`) plus an adjacent DP-LIVE-001/002 bucket-kind fix for prediction found in the same
  file. Prediction-stall todo left OPEN — two root causes fully diagnosed with evidence (instrument-cache never
  refreshed post-boot; instruments-service's Polymarket catalog gap since 08-05), both filed as tracked todos in a new
  issue doc (`prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md`) since both
  fixes are outside this session's ownership (the websocket handler/live connectors, and instruments-service
  respectively). Captured-row verification for the cefi fix is pending — instruments-service had not yet published
  today's (08-14) CEFI instrument catalog as of this session (confirmed via direct GCS check: 0 blobs vs 22 on
  08-12/08-13, and 08-13's own catalog wasn't published until 13:37 UTC), blocking every venue on the VM uniformly
  including the 6 already-healthy ones — an unrelated IS daily-cadence gap, not a fix regression. Re-check after ~13:00
  UTC. Also resolved a STALE (3-day-old, non-live) git conflict on `scripts/dev/ff-starvation-detect.sh` in this shared
  `.tabs/4` checkout that was blocking every commit here (`needs merge`, `git commit` hard-refuses regardless of
  pathspec scoping) — both conflicting hunks were purely cosmetic comment-rewording with zero functional difference;
  resolved to the `Updated upstream` side, which turned out byte-identical to HEAD (nothing to commit for that file —
  the conflict was pure stash-pop residue, not a real content difference). Left the now-redundant `autostash` stash
  entry in place (its content was already fully applied/resolved in the working tree; `git stash drop` is hard-blocked
  for agents by the orchestrator guardrail, correctly).

- **context-scout 2026-08-15**: populated context_scope (6 entries) — swapped the two DONE-item targets
  (`validate_batch_live_smoke_matrix.py`, `launch-mtds-live-cefi-consolidated.sh`) for the still-open work:
  `live/websocket_runner.py` (the prediction-stall root-cause fix target, `LiveWebsocketRunner`'s never-wired hot-reload
  path), the new prediction-stall issue doc, and the archived Finding-D gap doc. **Fingerprint cross-reference (step
  4a)**: Finding B's `PHOENIX-SOLANA` exclusion claim (`defi_venues.py:800`, deliberately excluded 2026-07-22) shares
  the literal `PHOENIX-SOLANA` with `/plans/active/issues/uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md`
  (open, `assigned_vm: planning`), which independently found `PHOENIX-SOLANA` IS present in `ALL_DEFI_VENUES`
  (`defi_venues.py`, 135 members) but missing from `VENUES_BY_ASSET_GROUP["defi"]` (`market_data_categories.py`, 103
  members) — one of 33 venues affected by a separate, still-open registry-gap bug. Different registries, not necessarily
  contradictory, but the open registry-gap fix (adding all 33 missing venues back to `VENUES_BY_ASSET_GROUP`) could
  silently re-surface a venue this doc's Finding B found was deliberately excluded for a dead REST API — added to
  context_scope so the pending `[OPERATOR]` phoenix ruling accounts for it; the other doc is outside this batch,
  reported for its own pickup.
