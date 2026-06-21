---
title: Fleet data-acquisition health sweep 2026-06-21 — fixable code errors (no rate-limiting)
created: 2026-06-21
author: cefi-lane (/autonomous, Opus) — operator-requested fleet sweep
source:
  - GCS vm-logs sweep of ~75 running VMs (all lanes), 2026-06-21 ~16:10 UTC
locked_by: live-defi-rollout
---

# Fleet data-acquisition health — 2026-06-21 (operator-requested)

Operator asked: are the VMs running / rate-limited / recovering, should we enforce rate-limit caps vs
exponential-backoff, and are they getting data or failing for fixable code reasons (all data_types × venues × chains
should have data). Swept every lane's `run.log` (~75 VMs).

## Headline

- **All lanes RUNNING.** tradfi / defi / sports / prediction / cefi-live + monitoring.
- **ZERO rate-limiting fleet-wide** — no `429` / `Too Many Requests` / backoff / retry-after in ANY log. So
  exponential-backoff is **not** currently wasting time (it isn't firing). **No rate-limit caps needed today.** The
  proactive-cap-vs-reactive-backoff principle is sound but only bites the one genuinely rate-limited source — **Tardis
  historical** (billing-gated, NOT running). If/when Tardis historical is funded, add a self-enforced token-bucket below
  Tardis's per-key budget (the sharded launcher already singleton-locks for this reason).
- **Most lanes ARE getting data**: tradfi CME-CL done 33.6K rows, NASDAQ 27K, NYSE 76K, CBOE-VX 7.8K, CME-opts
  streaming; defi dex-swaps 69K, pyth 312, gas-fees/dex-pools/lst-rates/lending/liquidations/jito/marinade progressing,
  vault-share + instr-defi completed; sports odds 8.5K + fixtures 220/day.

## Fixable code errors (the operator's real question)

| #   | Lane                | Symptom                                                                                                                                                    | Root cause                                                                                                                                                                                                                           | Fix                                                                                                                                                                                                                                                                                                                                                             | Owner                                                |
| --- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 1   | **cefi live**       | HL WS connects + flushes `live_hyperliquid` rows but `row_count=0` (empty_confirmed)                                                                       | runner buffers keyed by passed instrument_id (`BTC`) but HL connector EMITS canonical `HYPERLIQUID:PERP:BTC` (`_parse_hyperliquid_trades`) → `record_tick` drops every tick (no matching buffer)                                     | **launch-param**: pass `--instrument-ids HYPERLIQUID:PERP:BTC;…` (connector maps back to coin for subscribe + emits matching id). **FIXED** by cefi-lane relaunch (`mtds-live-cefi-hyperliquid-trades-20260621-161527`). Durable fix = launcher should derive canonical instrument-ids from IS (Phase 3.5 catalog-aware enum) instead of the bare-coin default. | cefi-lane (this lane) — launcher-default follow-up   |
| 2   | **prediction live** | `mtds-live-prediction-polymarket-trades` → `NotImplementedError: no WSFeedConnector for 'POLYMARKET'` → DEPLOYMENT_FAILED                                  | venue **case mismatch**: registry has `polymarket` (lowercase, like all defi/prediction venues) but the shard-spec passes `POLYMARKET` (uppercase). cefi venues registered UPPERCASE so they match; defi/prediction lowercase don't. | `websocket_streaming_handler.py::_resolve_connector` (line ~112): case-insensitive lookup — `WS_FEED_CONNECTOR_FACTORIES.get(venue) or next((f for k,f in WS_FEED_CONNECTOR_FACTORIES.items() if k.upper()==venue.upper()), None)`. Unblocks polymarket + jito/curve/orca/raydium/phoenix/morpho/kalshi live.                                                   | live-pipeline lane (slot-3 owns this file — 46adace) |
| 3   | **defi**            | `pyth-lst-backfill` Pyth Hermes historical `HTTP 400 "Failed to deserialize query string. Error: Odd number of digits"` (Chainlink leg OK, Pyth leg fails) | Pyth Hermes price-id query encoding — odd-length hex (missing `0x` / odd nibble count) in the historical query string                                                                                                                | fix the Pyth price-id hex formatter (pad/normalize the `ids[]=` hex) in the Pyth historical client                                                                                                                                                                                                                                                              | defi lane                                            |
| 4   | **sports**          | `mtds-backfill-odds-*` manifest `complete=False missing=['ODDS_API']` despite 8.5K rows written                                                            | expected ODDS_API source not satisfied (fan-out wrote 22 bookmaker shards but the source-completeness check still flags ODDS_API)                                                                                                    | recheck odds source-completeness / cred; verify SOURCE_PRIORITY for sports odds                                                                                                                                                                                                                                                                                 | sports lane                                          |
| 5   | **sports**          | `footystats-fwd-20260621-170000` run.log is 0 bytes                                                                                                        | VM startup/log-upload issue (never emitted)                                                                                                                                                                                          | check VM startup + heartbeat uploader                                                                                                                                                                                                                                                                                                                           | sports lane                                          |
| 6   | **prediction**      | `mtds-prediction-kalshibulk` stuck 50+ min on tar extraction (I/O), no progress markers                                                                    | large bulk tar decompress I/O-bound (not a code error)                                                                                                                                                                               | watch; if no completion, the 33GB bulk download/extract may need a bigger disk or streamed ingest                                                                                                                                                                                                                                                               | prediction lane                                      |

## Recommended decision

No rate-limit caps now (nothing is rate-limited). The data gaps are CODE/CONFIG, not throttling. Items 1 (fixed) + 2
(trivial case-insensitive lookup) are the highest-value — #2 unblocks ALL lowercase-registered live venues (prediction +
defi). Items 3–5 are per-lane backfill/source fixes. The owning lanes (or the operator) should land 2–5; cefi-lane fixed
#1 operationally + will file the launcher-canonical-instrument-id default as a follow-up.
