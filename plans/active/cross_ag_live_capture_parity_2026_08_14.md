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
    /plans/archive/2026_08/issues/uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md,
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

> **CORRECTION 2026-08-17 (`defi_operator_ruling_ao_dispatch_2026_08_15.md` todo 1) — the "not in current UAC
> ... at all" premise above was factually wrong; do NOT delete `phoenix_ws.py`.** Live-verified today:
> `PHOENIX-SOLANA` IS a real, currently-registered `ALL_DEFI_VENUES` member (`defi_venues.py`, 170 total),
> `DEFI_VENUE_PHASE="pipeline"` — it was never removed from that registry (confirmed already present as of the
> 2026-08-09 registry-gap doc, `/plans/archive/2026_08/issues/uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md`).
> This finding conflated "not in the narrower live-phase `VENUES_BY_ASSET_GROUP['defi']` subset" (TRUE, still true
> today, 103 members, by design — the `_DEFI_VENUE_PHASE == "live"` filter, unrelated to the dead REST API) with
> "not in UAC at all" (FALSE). `VENUE_TO_ASSET_GROUP["PHOENIX-SOLANA"] == "defi"` today, per the 2026-08-09 fix
> (`unified-api-contracts@7b96791e`). Full evidence + the resolved decision:
> `/plans/archive/2026_08/defi_operator_ruling_ao_dispatch_2026_08_15.md`'s Progress Log, 2026-08-17 entry.

- [x] ✅ [OPERATOR] P2. **RESOLVED 2026-08-17 — do NOT delete; the "UAC-excluded venue" premise was wrong.** See
      the correction block above. `phoenix_ws.py` is a real, working connector (Jupiter-routed, does not depend on
      the dead REST API) that IS actively imported via `connectors/__init__.py::register_all()` — not orphaned
      code. It sits unreachable at DISPATCH time for a different, fixable reason: it registers under bare
      lowercase venue key `"phoenix"`, which `resolve_ws_feed_venue_key()`'s exact/`.lower()`/`.upper()` chain
      cannot bridge to the canonical `"PHOENIX-SOLANA"` dispatch key (same resolver-mismatch class already fixed
      for curve/morpho/orca/raydium above). Two genuine follow-up decisions remain, tracked as their own todos
      immediately below rather than left in prose. Original text (superseded by the correction above):
      ~~Rule on `phoenix_ws.py`: delete it as dead code targeting a UAC-excluded venue~~, or make the case to
      restore `PHOENIX-SOLANA` to `VENUES_BY_ASSET_GROUP` for live-only coverage despite the dead REST API — DoD:
      the ruling is recorded here and `phoenix_ws.py` either removed or left in place with the ruling cited in
      its docstring.
- [ ] [CODE] P3. Re-register `phoenix_ws.py`'s `PhoenixWSFeedConnector` under the canonical chain-suffixed key
      `PHOENIX-SOLANA` (mirroring the `curve`→`CURVE-ETHEREUM`/`orca`→`ORCA-SOLANA`/`raydium`→`RAYDIUM-SOLANA` fix
      above) instead of the bare `"phoenix"` key, so `resolve_ws_feed_venue_key()` can actually find it. Only
      meaningful paired with the next todo — do both together or neither. Source:
      `defi_operator_ruling_ao_dispatch_2026_08_15.md`'s 2026-08-17 finding. (repo: market-tick-data-service)
- [ ] [OPERATOR] P3. Rule on whether to promote `PHOENIX-SOLANA` from `DEFI_VENUE_PHASE="pipeline"` to `"live"` in
      `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`, so live dispatch actually
      selects it (a priority/resourcing call — `phoenix_ws.py` is fully built and working via Jupiter-routed
      polling, so the only remaining blocker to real live Phoenix coverage is this phase gate + the resolver-key
      fix above). DoD: ruling recorded here; if promoted, pair with the resolver-key fix todo above in the same
      change. Source: `defi_operator_ruling_ao_dispatch_2026_08_15.md`'s 2026-08-17 finding. (repo:
      unified-api-contracts)

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
      `mtds-live-tradfi-cme- trades-20260809-163443`'s run.log shows `gateway error code=api_key_deactivated` +
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
      stopped a duplicate-VM race from a too-fast second launch attempt before it created a second VM. **2026-08-15
      re-verification (empty_confirmed_and_coverage_correctness_audit_2026_08_15.md todo "Verify/close BYBIT-FUTURES
      captured-row verification")**: confirmed live via SSH into the VM (still `RUNNING`, boot
      `2026-08-13T20:25:34-07:00`) + a direct manifest query. Findings: - The instrument-availability index shows
      BYBIT-FUTURES 100% `empty_confirmed` across all 4,664 historical rows including 4,652 dated today (2026-08-15) —
      as of the moment this query ran, still zero `captured` rows. - Tailing `live-bybit-futures-trades.log` (mirrors
      all 4 BYBIT-FUTURES shards) shows the ORIGINAL fix (`_resolve_is_lookup_venue` routing BYBIT-FUTURES → the primary
      `BYBIT` catalog) is genuinely active and correct, but hit a SEPARATE, previously-undiagnosed problem: every
      5-minute retry from VM boot (2026-08-14 03:27 UTC) through 2026-08-15 06:02 UTC logged
      `read_is_universe_sync: no instruments.parquet for cefi/BYBIT-FUTURES (lookup_venue=BYBIT) day=<date> in either by_date layout`
      — the resolved lookup venue was right, but instruments-service's BYBIT catalog for that UTC day genuinely did not
      exist yet at every checked time, for BOTH 08-14 and 08-15 (not a one-day fluke). **Then, at 2026-08-15 06:07:55
      UTC, the identical retry succeeded**:
      `read_is_universe_sync: resolved 1282 instruments cefi/BYBIT-FUTURES day=2026-08-15` — confirming this is a
      genuine IS daily-catalog PUBLISH-TIMING gap (the catalog for a given UTC day isn't available until sometime in the
      morning UTC, well after the day rolls over), not a code bug in the venue-resolution fix. The retry loop is working
      as designed and does NOT need a restart once the catalog lands. - **Captured-row confirmation: CONFIRMED STILL
      ZERO, a real unresolved bug** — read the live VM's per-VM manifest shard directly
      (`_index/per_vm/mtds-live-cefi-consolidated-20260814-041422.parquet`, NOT the possibly-lagging consolidated index)
      ~1h after the 06:07:55 UTC successful universe resolution: 5,128 BYBIT-FUTURES rows in that shard, **100%
      `empty_confirmed`**, including `data_type=trades` rows dated today — i.e. after the venue-alias fix correctly
      resolved 1,282 instruments, the connector is still writing confirmed-empty markers, not real captured trades. This
      is a THIRD, previously undiagnosed problem, distinct from both the original Tardis-alias bug (fixed, confirmed
      working) and the IS catalog publish-timing gap (real, but not the current blocker — the catalog was available and
      resolved successfully by 06:07:55). Not further root-caused this session (would need the WS connect/subscribe code
      path + a live log grep for subscribe-frame confirmations/errors after the 06:07:55 resolve — out of budget for
      this pass). - [x] ✅ [CODE] P1. **BYBIT-FUTURES live capture is confirmed still fully broken as of 2026-08-15**
      despite the 2026-08-09 venue-alias fix working correctly (universe resolves) — root-cause why the WS connector
      produces zero captured rows across all 4 data_types (trades/book_snapshot_5/derivative_ticker/ depth_of_book_10)
      even after a successful instrument-universe resolve. Start by grepping `live-bybit-futures-trades.log` on
      `mtds-live-cefi-consolidated-20260814-041422` for subscribe-frame confirmations/rejections in the minutes after a
      `resolved N instruments` line, and check whether the connector's subscribe step ever actually fires post-resolve.
      DoD: real `captured` rows appear for at least one BYBIT-FUTURES data_type, or a named root cause + fix is filed. —
      **RESOLVED 2026-08-18** (dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md's carried-over
      [OPERATOR] investigate-the-2-live-capture-stalls todo): the 2026-08-15 diagnosis two lines up already named the
      TWO required fixes — (1) filter the IS-resolved universe to PERPETUAL/FUTURE only (excludes the ~501 SPOT_PAIR
      ids the BYBIT-FUTURES→BYBIT Tardis-alias resolution pulls in) and (2) chunk the subscribe request under Bybit's
      21,000-char cap — but only fix (2) ever actually shipped (`market-tick-data-service@a89bd433`, 2026-08-15); fix
      (1) was designed + stashed (`orchestrator-slot-4-bybit_futures_dp_live_004_subscribe_fix-001`) but never
      committed (severe host RAM contention blocked `quality-gates.sh` at the time) and the stash was never recovered.
      **Live-reconfirmed 2026-08-18** on the CURRENT VM (`mtds-live-cefi-consolidated-20260817-025031`, launched
      2026-08-17 — well after the chunking fix landed): its `_index/per_vm/<vm>.parquet` shard shows ALL 10,258
      BYBIT-FUTURES rows `empty_confirmed`/`SOURCE_RETURNED_ZERO`, with exactly 737 PERPETUAL + 44 FUTURE + 501
      SPOT_PAIR unique instrument_ids attempted — matching instruments-service's unfiltered `venue=BYBIT` catalog
      count exactly, confirming the filter genuinely never shipped (the connector is still subscribing every SPOT_PAIR
      id, and even the legitimate PERPETUAL/FUTURE ones return zero — chunking alone was not sufficient). **Fix
      shipped**: `market-tick-data-service@5f88715e4b` (landed `live-defi-rollout`, `quality-gates.sh --no-fix` ALL
      PASSED — 11082 passed/28 skipped/1 xpassed, 476s) adds `_is_linear_derivative()` (bybit_ws.py) —
      filters to PERPETUAL/FUTURE before any subscribe topic is built — applied in `BybitFuturesWSFeedConnector`
      (trades) `.connect()`/`.subscribe()` and, via the existing `is_bybit_linear_derivative` export re-imported into
      `bybit_futures_book_ticker_ws.py`, in `_BybitBookStateConnector` (book_snapshot_5/depth_of_book_10) and
      `BybitFuturesTickerWSConnector` (derivative_ticker) — all 4 data_types now filtered identically. Updated 2
      pre-existing tests whose fixture ids used the unrealistic legacy `:PERP:` token (would now be silently filtered
      out) to the real canonical `:PERPETUAL:` shape, and added positive/negative filter-coverage tests in both test
      files. DoD's captured-row half NOT YET independently re-verified post-deploy in this session (the fix needs a
      fresh VM cycle to pick up the new code — recorded as a follow-up, not blocking this todo's code-fix closure).
      - [x] ✅ [INFRA] P2. Once `market-tick-data-service@5f88715e4b`'s tarball reaches a fresh
        `mtds-live-cefi-consolidated-*` relaunch (routine cycle or the next redeploy), verify at least one real
        `captured` BYBIT-FUTURES row appears post-relaunch — DoD per the original todo above. — **CLOSED 2026-08-21
        (negative result, root-caused)**: the 2026-08-21 relaunch (`mtds-live-cefi-consolidated-20260821-200626`,
        confirmed fix-provenance via SSH) still shows 0 captured BYBIT-FUTURES rows across all 4 data_types (stable
        across 5 repeated per-VM-shard reads; cross-checked against a genuinely-captured sibling venue on the same
        shard). Root cause: Bybit subscribe/unsubscribe ack frames are silently dropped, unlogged, in both
        `bybit_ws.py` and `bybit_futures_book_ticker_ws.py` — confirmed via SSH log inspection (zero
        subscribe/ack/reject lines across the connector's full run) + a direct code read. Filed
        `/plans/archive/issues/dp_live_004_bybit_futures_subscribe_ack_unobserved_2026_08_21.md` (3 tracked todos:
        add ack-frame logging to both connectors, then re-verify). Closing THIS verification todo per its own
        stated fallback ("root cause named + fix filed"); the parent `[DATA] P1` captured-row todo above stays
        OPEN until a real captured row is confirmed post-ack-logging-fix — this todo only closes the
        post-relaunch-verification step, not the underlying capture gap.
      - [ ] [DATA] P2. File the separate IS daily-catalog PUBLISH-TIMING gap as its own instruments-service issue —
      BYBIT's `instrument_availability/by_date/day=<today>/.../venue=BYBIT/instruments.parquet` was absent at every
      check from VM boot (2026-08-14 03:27 UTC) through 2026-08-15 06:02 UTC, only appearing by 06:07:55 UTC — i.e. the
      same-day catalog isn't reliably available until well into the UTC morning. Likely affects every live shard that
      depends on a same-day IS catalog at boot/early-day, not just BYBIT-FUTURES — worth a dedicated investigation into
      IS's daily catalog cron schedule/duration.
- [x] [DATA] P1. Add a standing live-capture-productivity check across all asset groups — a shard with a running process
      and zero `captured` rows over N days must page — DoD: replaying the check against the 2026-08 manifest window
      fires on sports, prediction and the four cefi shards; routes per the actionable-only alerting rule. — DONE
      2026-08-14: added **DP-LIVE-004** to
      `deployment-service/deployment_service/data_pipeline_monitors/ live_stream_watcher.py`
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

- [x] ✅ [OPERATOR] P1. Already resolved via AskUserQuestion, extracted to `defi_operator_ruling_ao_dispatch_2026_08_15.md` (na-eligibility-audit 2026-08-17 stale-checkbox correction). Decide whether DeFi live capture is in scope at all before any build — there is no defi live VM, no
      defi live launcher, and DeFi is nominally the May-23 critical path; the honest options are to build the pollers,
      or to declare DeFi live BATCH-ONLY-BY-DESIGN and stop carrying 40 placeholder registrations that read as coverage
      — DoD: the ruling is recorded here.
- [x] ✅ [DATA] P1. Already resolved, phased-scoping todo extracted to `defi_operator_ruling_ao_dispatch_2026_08_15.md` (na-eligibility-audit 2026-08-17 stale-checkbox correction). Whichever way that ruling goes, make the archived gap doc's status honest — DoD: either the follow-up
      tasks exist as tracked todos, or the placeholders are reclassified with the ruling cited; "resolved" must not mean
      "scaffolded".

## Finding E — DeFi index prefix carries 17k objects and tens of GB of stale backups

The defi market-data bucket's `_index/` prefix holds 17,191 objects. `availability_index.parquet` alone is 7.3 GB, and
alongside it sit at least a dozen multi-GB `.bak` snapshots (several `dex_pool_fees_*` backups at ~6.4 GB each, plus
`.undelist`, `.deindexed`, `.dualform` and other dated variants) totalling tens of GB. The 7.3 GB live index is also why
any full-index read is impractical — it defeated a read in this session and is worth knowing before anyone plans one.

Note the manifest consolidator itself is healthy — `uts-prod-manifest-consolidator-market-data-defi` executes every 60s
and succeeded on all recent runs; the index's age reflects the incremental-cutoff design and scale, not a broken job.

- [x] ✅ [OPERATOR] P1. Already ruled (leave as-is indefinitely, no dispatch, status quo stands) via `defi_operator_ruling_ao_dispatch_2026_08_15.md` (na-eligibility-audit 2026-08-17 stale-checkbox correction). Rule on retention for the `_index/*.bak*` snapshots in the defi prod bucket — prod-bucket deletes
      are human-only unless reversibility-qualified; cite `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` —
      DoD: a retention rule recorded here, then executed under that protocol.
- [ ] [DATA] P2. Give consumers a projected/filtered read path for the defi index so an audit does not need the full 7.3
      GB — DoD: a documented `read_availability_index` call pattern (column projection plus pipeline_mode filter) that
      answers "which live shards captured" without a full decode.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **2026-08-15 (na-eligibility-audit follow-up, operator ruling)**: three open items ruled via AskUserQuestion. (1)
  `phoenix_ws.py` — **delete as dead code** — extracted to `defi_operator_ruling_ao_dispatch_2026_08_15.md`
  (`assigned_vm: planning`), but that plan's own todo 1 flags a contradiction found AFTER this ruling: this doc's own
  line 383-385 notes `uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md` independently found `PHOENIX-SOLANA` IS
  present in `ALL_DEFI_VENUES` — reconcile before deleting, don't delete on this ruling alone. (2) DeFi live capture
  scope — **operator approved building the ~40 BLOCKED-BUILD pollers** — phased-scoping todo extracted to the same
  dispatch plan. (3) `_index/*.bak*` retention — **leave as-is indefinitely** — no dispatch, status quo stands.

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
  the literal `PHOENIX-SOLANA` with `/plans/archive/2026_08/issues/uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md`
  (open, `assigned_vm: planning`), which independently found `PHOENIX-SOLANA` IS present in `ALL_DEFI_VENUES`
  (`defi_venues.py`, 135 members) but missing from `VENUES_BY_ASSET_GROUP["defi"]` (`market_data_categories.py`, 103
  members) — one of 33 venues affected by a separate, still-open registry-gap bug. Different registries, not necessarily
  contradictory, but the open registry-gap fix (adding all 33 missing venues back to `VENUES_BY_ASSET_GROUP`) could
  silently re-surface a venue this doc's Finding B found was deliberately excluded for a dead REST API — added to
  context_scope so the pending `[OPERATOR]` phoenix ruling accounts for it; the other doc is outside this batch,
  reported for its own pickup.

- **2026-08-15 (data_pipeline_failure escalation agt-f2b4c7, slot-4)**: root-caused the still-open Finding-C todo above
  ("BYBIT-FUTURES live capture is confirmed still fully broken") — dispatched from a fresh `DP_CRON_DID_NOT_FIRE`
  (DP-LIVE-004) page for the SAME VM (`mtds-live-cefi-consolidated-20260814-041422`, venue=BYBIT-FUTURES,
  data_type=trades). Followed the todo's own DoD: SSH'd the VM, tailed `live-bybit-futures-trades.log` — zero
  `"op":"subscribe"`/`success`/`ret_msg` lines anywhere in the whole 6,061-line log (the connector never logs subscribe
  acks at all, confirming the todo's suspicion that the subscribe step is invisible). Traced the code path instead:
  `read_is_universe_sync` (`live/_is_universe.py`) returns EVERY `instrument_key` from IS's `BYBIT` catalog unfiltered
  by `instrument_type` (1,282 rows 2026-08-15 — spot+linear+inverse+options all under the one Tardis-primary `BYBIT`
  venue token), and `LiveWebsocketRunner.run()` passes that whole unfiltered list straight to
  `connector.connect(instrument_ids=...)` with no type filter anywhere in between. All 4 BYBIT-FUTURES connectors
  (`bybit_ws.py`'s trades connector + `bybit_futures_book_ticker_ws.py`'s book_snapshot_5/derivative_ticker/
  depth_of_book_10) then crammed the FULL unfiltered id list into ONE unchunked `{"op":"subscribe","args":[...]}` frame
  to Bybit's LINEAR-only endpoint. Confirmed via web search that Bybit's v5 public-stream docs (ws/connect +
  websocket/trade/guideline) cap the combined `args` topic-string length at **21,000 characters per request** — 1,282
  raw topics comfortably exceeds that, and Bybit does not ack a rejected/oversized frame per-topic, so the failure is
  100% silent (matches the log evidence exactly, and is the same failure SHAPE this connector family already hit + fixed
  3 times before via chunking: `aster_book_liq_ws.py`, `deribit_book_ticker_ws.py`, `polymarket_clob_ws.py`/
  `polymarket_trades_ws.py` — BYBIT-FUTURES was simply never given the same treatment). **Fix applied** (all 4
  connectors, both files): (1) filter `instrument_ids` to PERPETUAL/FUTURE only before building any subscribe topic —
  the only types valid on the LINEAR endpoint; (2) chunk the subscribe `args` by cumulative character length, capped
  under Bybit's 21,000-char limit; (3) log subscribe/unsubscribe ack frames (`success`/`ret_msg`) instead of silently
  discarding them, closing the exact observability gap that made this bug take 2 sessions to root-cause. Also fixed 2
  pre-existing test files (`tests/unit/test_bybit_ws_connector.py`,
  `tests/unit/test_bybit_futures_book_ticker_ws_coverage.py`) whose fixture instrument_ids used an unrealistic `:PERP:`
  type token (real canonical shape is `:PERPETUAL:`/`:FUTURE:`, confirmed via `unified_api_contracts.InstrumentType`) —
  under the new filter those fixtures would have been silently dropped, breaking
  `test_subscribe_new_instruments_updates_set` and its siblings. **NOT YET SHIPPED**: 7 consecutive
  `quality-gates.sh --no-fix` background runs were killed (never completing, mostly still queued behind the governor
  token) across a ~50min window — cross-referenced against
  `/plans/archive/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md` and confirmed the exact matching
  signature live on this host during the attempts (free RAM swinging 547Mi↔13Gi within under a minute, 16Gi/47Gi swap
  used, 10-25 concurrent `quality-gates.sh` processes fleet-wide vs. the documented ≤2 rule, and a live
  `/opt/.qg-governor-glue-shared/.benchmarks/qg-governor/` ledger with dozens of fresh `aborted.*`/`killed.*` markers
  fleet-wide) — genuine, severe, ongoing host contention, not a defect in this fix. Per that doc's own established
  precedent (do not keep blind-retrying once contention is confirmed stable), stopped retrying and **stashed the
  verified-ready fix** in the `market-tick-data-service` slot-4 checkout: `git stash` entry
  `orchestrator-slot-4-bybit_futures_dp_live_004_subscribe_fix-001` (4 files, +155/-60 lines). **Handoff for the next
  session/slot**: `git stash pop` in `.tabs/4/market-tick-data-service` (or a calmer slot), run
  `bash scripts/quality-gates.sh --no-fix` when host contention has eased, ship via
  `quickmerge --agent --files '<the 4 files>'`, then flip the Finding-C todo above to done with the shipped SHA + a
  post-fix `captured` row citation (the todo's own DoD). Did not attempt to verify via a live VM restart/redeploy this
  session — the fix isn't shipped yet, so nothing on the running VM has changed.

- **2026-08-17 (slot 9, data_engineering, `defi_operator_ruling_ao_dispatch_2026_08_15.md` todo 1)**: resolved the
  Finding-B `PHOENIX-SOLANA` contradiction flagged by the 2026-08-15 context-scout fingerprint cross-reference
  above — NOT a real disagreement, two docs correctly describing two different registries. Corrected the stale
  "not in current UAC ... at all" claim in place (see the `> CORRECTION 2026-08-17` block above Finding B's
  `[OPERATOR]` todo) and resolved that todo: do NOT delete `phoenix_ws.py`. Full evidence + the two genuine
  follow-up decisions (canonical-key re-registration; live-phase promotion) are in
  `/plans/archive/2026_08/defi_operator_ruling_ao_dispatch_2026_08_15.md`'s own Progress Log, same date.
- **na-eligibility-audit 2026-08-17** [body-hash:25b58a0e0a5de6c9]: KEEP-NA, stale-items corrected -- closed 3 of 8 open items (DeFi live-capture-scope decision, archived-gap-doc honesty follow-up, _index/*.bak* retention ruling): all already resolved via AskUserQuestion and extracted to the active defi_operator_ruling_ao_dispatch_2026_08_15.md, checkboxes here simply never flipped. Doc stays assigned_vm: NA for its 5 remaining genuinely open items (an OPERATOR ruling, a dependency-blocked pairing todo, a captured-row verification blocked on an unshipped fix, a prediction-stall diagnosis redirected to a different doc, and a genuine build task). Cross-cutting tranche audit.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — 7 open todos: 2 explicit OPERATOR/paired-dependency items (phoenix live-phase-promotion ruling + its paired resolver-key fix, 'do both together or neither'), 2 dependency-blocked-on-other-docs items. (4/7 items tagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE for next-run reassessment.)
- **context-scout 2026-08-19**: re-verified context_scope, no change needed (6 entries), all paths still resolve, still accurate.
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche): KEEP-NA, valid — reassessed the 4 items flagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE 2026-08-19. Phoenix re-registration (Finding B) stays paired with its gating `[OPERATOR]` live-phase-promotion ruling per the todo's own 'do both together or neither' text — not independently dispatchable. Close-pending-captured-row-verification (Finding C) and its 2 nested follow-ups (post-relaunch verify, file the IS daily-catalog publish-timing gap) are observational/wait-then-check items nested inside a 3-bug investigation chain already substantially resolved this session with a shipped fix (`market-tick-data-service@5f88715e4b`) — splitting the residual verification out doesn't reduce genuine judgment content. The projected/filtered defi-index read path (Finding E) is open-ended engineering design ('give consumers X'), not a fully bounded spec. All 4 stay NA; downgrading the flag. 7 open todos unchanged.
- **2026-08-21 (data_engineering, slot 19, dispatched from `dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md`
  todo 2)**: closed Finding C's nested `[INFRA] P2` post-relaunch-verification todo — the 2026-08-21
  `mtds-live-cefi-consolidated-20260821-200626` relaunch still shows 0 captured BYBIT-FUTURES rows across all 4
  data_types, root-caused to Bybit subscribe-ack frames being silently dropped/unlogged in both connector files.
  Filed `/plans/archive/issues/dp_live_004_bybit_futures_subscribe_ack_unobserved_2026_08_21.md`. The parent
  `[DATA] P1` "close the pending captured-row verification for the four cefi shards" todo stays OPEN (it needs all
  4 venues, not just BYBIT-FUTURES, and its DoD is still unmet for BYBIT-FUTURES specifically) — see that todo's
  own text above for the full remaining scope.
