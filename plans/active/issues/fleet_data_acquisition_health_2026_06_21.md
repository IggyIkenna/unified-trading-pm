---
title: Fleet data-acquisition health sweep 2026-06-21 — fixable code errors (no rate-limiting)
created: 2026-06-21
source:
  - GCS vm-logs sweep of ~75 running VMs (all lanes), 2026-06-21 ~16:10 UTC
locked_by: live-defi-rollout
priority: P2
status: active
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

## UPDATE 2026-06-21 (cefi-lane, after fixing #1) — next bug: live capture fails tick-schema validation

Fixing #1 (canonical instrument-ids `HYPERLIQUID:PERP:<coin>`) **worked** — HL trades now reach the runner buffers and
windows capture. But the NEXT first-run bug surfaced (cefi live VM `…161527` run.log):

```
RowSchemaValidationError (venue=HYPERLIQUID): missing required columns:
['instrument_id','symbol','ts_event','price','size','side']
  … MTDSShardManifestRecorder.record_captured → ManifestWriter.record_captured
  → _maybe_validate → _validate_with_source → validate_row_df  (RAISES)
```

**Root cause:** the live `record_captured` passes a **bookkeeping** `_make_row_count_only_df` (just `row_count`) — its
own docstring says "row_count alone satisfies the manifest contract; the canonical write path lives in the runner's
`LiveWebsocketTickSink`". But `ManifestWriter.record_captured` runs `_maybe_validate` → `validate_row_df` against the
FULL tick contract and **raises** (strict on this VM). So **captured windows error out; only empty windows record** →
the manifest shows `empty_confirmed` even though trades ARE flowing. (live-mode never ran before → never exercised.)

**Fix (live-pipeline lane — slot-3 owns `manifest_recorder.py` + the UTL writer, shipped 46adace):** the live
`record_captured` bookkeeping df must **skip row-schema validation** (the real ticks are validated+written by
`LiveWebsocketTickSink` separately) — e.g. a `validate=False`/`skip_row_validation` kwarg on
`ManifestWriter.record_captured` passed by the live recorder; OR have the runner pass the REAL aggregated tick df
(instrument_id/symbol/ts_event/price/size/side) instead of the row-count-only synthetic. cefi-lane did NOT patch this
(slot-3's actively-churning file; collision-risk + a UTL+mtds design call). The cefi live VM stays up emitting
`live_hyperliquid` rows; it flips empty→captured the moment this lands. This is the LAST blocker for end-to-end live
trade capture — the 7-bug first-run chain: GCS-deploy · topic · IAM · row_key(asset_group) · row_key(day→date) ·
instrument-id-buffer-key · capture-schema-validation.

## UPDATE 2026-06-21 (cefi-lane) — bug#7 FIXED + durably shipped; bug#8 surfaced + fixed (MissingSourceError)

**Bug#7 RESOLVED (operator-directed "fix both paths"):** UTL `ManifestWriter.record_captured` gained a
`validate: bool = True` gate; the live recorder passes `validate=False` (bookkeeping df — real ticks
validated+written by `LiveWebsocketTickSink`; `pipeline_mode`+`source` carry provenance). Shipped durably to
`live-defi-rollout` via isolated name-correct worktrees (churn-immune; both QG-green): UTL@`057264fd` (converged with
slot-3's `78481472`) + market-tick-data-service@`e6b0f29`. Tarballs rebuilt+deployed; VM
`mtds-live-cefi-hyperliquid-trades-20260621-175349` relaunched. **`RowSchemaValidationError` is GONE** (confirmed in
that VM's run.log — the fix works end-to-end).

**Bug#8 surfaced (8th first-run bug) — `MissingSourceError`:** with schema-validation correctly skipped, the live
`record_captured` then raised:

```
MissingSourceError: Manifest write passed source='hyperliquid' which is not a registered source for
asset_group='cefi' data_type='trades'. Allowed (UAC SOURCE_PRIORITY): ['tardis'].
  row_key={venue=HYPERLIQUID, data_type=trades, date=2026-06-21, instrument_type=PERPETUAL, instrument_id=HYPERLIQUID:PERP:SOL}
```

**Root cause:** HYPERLIQUID/ASTER were reclassified to `cefi` (UAC 0.30.0) but their **sources were never registered**
in `SOURCE_PRIORITY` for the cefi data_types they produce — `(cefi, trades)` etc. listed only `['tardis']`, so the
writer-side source gate (`_resolve_and_validate_source`) rejected `source='hyperliquid'`. This is the documented cefi
**source-provenance RED gap** (CLAUDE.md § "source= provenance is CROSSCUTTING — cefi/defi/sports are RED gaps").

**Fix (cefi-lane, UAC):** registered `hyperliquid` + `aster` as cefi sources on the 5 cefi perp market-data types they
produce — `(cefi, trades|ohlcv_1m|book_snapshot|liquidations|derivative_ticker)` (additive; `tardis` stays index-0 batch
primary; mirrors the pre-existing `aster`-in-`derivative_ticker` registration). `unified-api-contracts`
`canonical/crosscutting/_source_priority_data.py`. Additive + matches the venue-override per-venue source-stamp design.

**Correction to issue `live_tardis_machine_and_hl_aster_s3_batch_2026_06_21.md` §2 (STALE PREMISE):** that doc says the
cefi download "STRIPS HL/ASTER (they're defi in VENUE_TO_ASSET_GROUP)." **Verified 2026-06-21: `VENUE_TO_ASSET_GROUP`
now resolves `HYPERLIQUID`→`cefi` and `ASTER`→`cefi`** (post UAC 0.30.0 — NOT defi). So the strip premise is stale; the
actual 48.5k-cell `attempted_failed` cause needs fresh diagnosis (and the **defi lane is actively running on HL S3
data** → a blind cefi HL/ASTER batch could collide — diagnose-first, not blind-execute). First-run chain now 8 bugs:
…instrument-id-buffer-key · capture-schema-validation(bug#7) · source-registration(bug#8).
