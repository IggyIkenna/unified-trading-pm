---
doc_type: issue
title:
  DRIFT Helius perp_funding shards contain ZERO funding rates — 1.2M mislabeled signature rows/day counted as captured
summary:
  "The Helius `perp_funding` path writes rows whose funding fields are ALL hardcoded 0.0 — it captures transaction
  signatures, not funding. Verified on prod: day=2025-01-09 `drift_helius_SOL-PERP_20250109.parquet` = 1,209,478 rows,
  data_quality='helius_v2_signatures_only' (100%), funding_rate_24h/mark_price/oracle_price nonzero=0/1209478, every row
  stamped symbol='SOL-PERP' + market_index=0 though the sig index is DRIFT-PROGRAM-wide (all markets/liquidations/
  oracle cranks), and written under the WRONG partition pipeline_mode=batch_hyperliquid. These shards count as
  `captured` perp_funding, satisfying the mvp_backfill_defi_onchain_v10 MVP gate with data containing no funding rates.
  The correct data already exists beside them: the Velocity per-day CSV path writes 24 real hourly rows/day
  (batch_onchain_rpc/SOL-PERP.parquet, funding_rate=0.002007041 …, per-market, ~7 KB). Recommendation: delete the helius
  shards, retire the Helius perp_funding path, let the Velocity API own history."
status: superseded
nature: record
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, drift, perp-funding, helius, data-correctness, mislabeled, mvp-gate, pipeline-mode, silent-corruption]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/issues/drift_v2_sig_index_program_wide_helius_oom_2026_07_15.md,
    plans/active/issues/mtds_solana_drift_backfill_manifest_staleness_redoes_captured_days_2026_07_15.md,
    plans/active/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md,
  ]
created: 2026-07-16
assigned_vm: NA
source:
  ["operator question 2026-07-16 (does Drift's public API give us full history)", "live parquet + API verification"]
parent_epic: defi_master
priority: P0
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-16T07:55Z
---

> 🔴 **SUPERSEDED (2026-07-16, operator ruling, verbatim):** "kill drift entirely from our whole system it's pointless —
> Jupiter is the main one let's just use that. kill all other solana perp dex's. uac, code, adaptors, manifest, gcs,
> everything. no instruments no mvp nothing." The DRIFT venue this doc's finding concerns has been **removed entirely**
> (Drift was hacked ~$280M on 2026-04-01, rebranded to Velocity DEX 2026-07-01, now a ~2-week-old private beta with ~$0
> listed TVL) — all Solana perp DEXes are dropped except Jupiter (not integrated). This doc's finding/fix is now moot;
> kept for historical record only. SSOT for the removal: `codex/04-architecture/solana-defi-coverage.md` (tombstone
> banner).

# DRIFT Helius perp_funding shards are zero-valued signature noise (2026-07-16)

> **🟢 SUPERSEDED 2026-07-16 (operator kill ruling, later same day)** — operator ruled to kill DRIFT (and all other
> Solana perp DEXes except Jupiter) entirely: "kill drift entirely... uac, code, adaptors, manifest, gcs, everything."
> The `[SCRIPT]` P0 purge todo directly below (enumerate + delete the `drift_helius_*.parquet` shards) is now moot on
> its own terms — those shards died with the whole DRIFT venue in the broader purge, not as a standalone reclass.
> Evidence: 10 `drift_helius_*.parquet` objects found + deleted under
> `pipeline_mode=batch_hyperliquid/asset_group=defi/venue=DRIFT/` as part of the venue-wide raw-tick delete. The
> `[CODE]` P0/P1 todos below (retire the Helius write path, fix the partition bug) are superseded too — the whole
> `solana_defi_drift_helius.py` adapter is gone per the sibling CODE-track removal, not merely the write-path fixed. See
> `plans/active/issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md` for the full purge record (counts, evidence,
> scripts). The `[DATA] P1` on-chain-decoder-gap todo below and its own `perp_funding`/`perp_trades` data are likewise
> moot — DRIFT has no MVP data path anymore.

> Found while answering the operator's question "does Drift's public API give us what we need for full history?". The
> answer turned out to be yes — and in proving it, the Helius shards were shown to contain no funding data at all.

## Evidence (measured on prod, not inferred)

**The Helius shard** —
`day=2025-01-09/pipeline_mode=batch_hyperliquid/…/venue=DRIFT/…/data_type=perp_funding/ drift_helius_SOL-PERP_20250109.parquet`:

| check                                 | result                             |
| ------------------------------------- | ---------------------------------- |
| rows                                  | **1,209,478**                      |
| `data_quality`                        | `helius_v2_signatures_only` (100%) |
| `funding_rate_24h` nonzero            | **0 / 1,209,478**                  |
| `mark_price` / `oracle_price` nonzero | **0 / 1,209,478**                  |
| `market_index` nonzero                | 0 / 1,209,478 (hardcoded)          |
| distinct `symbol`                     | `['SOL-PERP']` — all 1.2M rows     |
| partition `pipeline_mode`             | **`batch_hyperliquid`** (wrong)    |

Code: `market_tick_data_service/cli/handlers/solana_defi_drift_helius.py::_parse_helius_batch` (~:229-272) hardcodes
`funding_rate_24h/7d/30d = 0.0`, `oracle_price = 0.0`, `mark_price = 0.0`, `oi_long/short = 0.0`, `market_index = 0`,
and stamps `"symbol": market` (the CLI-provided string) on every row unconditionally — while the sig index it reads is
built at the **DRIFT V2 PROGRAM level** (every instruction touching the program: all markets, trades, funding
settlements, liquidations, oracle cranks) per `drift_v2_sig_index_program_wide_helius_oom_2026_07_15.md`. So the rows
are (a) not funding data and (b) not SOL-PERP's transactions.

**The correct data, already present for the same day/market** —
`…/pipeline_mode=batch_onchain_rpc/…/perp_funding/ SOL-PERP.parquet` (written by the AO-launched
`backfill_drift_v2_historical`, Velocity per-day CSV path):

| check            | result                                                                                                                                                                                            |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| rows             | **24** — exactly the day's hourly funding settlements (ts deltas ≈3600s)                                                                                                                          |
| `funding_rate`   | **real** — 24/24 nonzero, e.g. `0.002007041`                                                                                                                                                      |
| schema (23 cols) | `ts, tx_sig, tx_sig_index, slot, record_id, market_index, symbol, funding_rate, funding_rate_long, funding_rate_short, cumulative_funding_rate_long/short, oracle_price_twap, mark_price_twap, …` |
| labeling         | per-market by URL **and** `symbol` carried in the payload; `market_index=0` is genuinely correct (SOL-PERP IS marketIndex 0)                                                                      |
| size             | ~7 KB vs the Helius shard's 1.2M rows                                                                                                                                                             |

**Velocity API coverage envelope** (probed live 2026-07-16,
`data.api.drift.trade/market/{MKT}/{fundingRates|trades}/ {Y}/{M}/{D}?format=csv`): real data genesis **2022-11-04 →
~2026-03-31**; **2026-04-05+ returns HTTP 200 with 0 bytes** (archive lags real-time ~3.5 months; bisected 03-29 ✓ /
04-05 ✗). Trades paginate at 4,999 rows/page via `page=N` (`limit`/`offset`/`cursor` are silently ignored) — SOL-PERP
2025-01-09 = 17,219 trades across 4 pages; `drift_v2_historical_handler.py` already paginates correctly (docstring:
"5000 rows/page; pages iterate until empty body").

## Why it matters

- These shards are `capture_status=captured` for `perp_funding` — an MVP gate data_type on
  `mvp_backfill_defi_onchain_v10` — so **the gate is being satisfied by rows with no funding rates**, and the DeFi
  captured% on the Honest Coverage panel is inflated by them.
- Anything reading `perp_funding` for DRIFT gets 1.2M zero-funding rows instead of 24 real ones.
- Interaction with `mtds_solana_drift_backfill_manifest_staleness_redoes_captured_days_2026_07_15` (skip-gate,
  `mtds@6d91aa33`): the gate correctly stops re-walking "captured" days — but for these days the captured data is WRONG,
  so they must be deleted (making them genuinely uncaptured) rather than skipped. Order matters: delete first, then the
  Velocity backfill refills them.

## Todos

- [ ] [SCRIPT] P0. Enumerate every `drift_helius_*.parquet` shard (all dates/markets; bounded prefix scan) + their
      manifest rows. Report counts. (Jan-2025 sample: 8 files.) Repo: market-tick-data-service.
- [ ] [SCRIPT] P0. Delete them + their manifest rows (or reclass to honest absence) so the days become genuinely
      uncaptured and the Velocity backfill refills them. Follow the ICE-purge precedent
      (`purge_tradfi_ice_non_24h_2026_07_14.py`): snapshot → pause the defi consolidator cron → dry-run → apply → verify
      row deltas → GCS-delete via UTL `gcs_delete_object` → resume + confirm a green cycle. Repo:
      market-tick-data-service.
- [ ] [CODE] P0. Retire the Helius `perp_funding` write path (`_backfill_drift_helius_date` / `_parse_helius_batch` /
      `_resolve_helius_rows`, `solana_defi_drift_helius.py`) — it cannot produce funding rates by construction
      (signature metadata only) and the Velocity path supersedes it for genesis→~2026-03-31. Delete rather than shim
      (no-shims rule). Keep/park the sig-index work only if some OTHER data_type genuinely needs it — state which, or
      delete that too. Repo: market-tick-data-service.
- [ ] [CODE] P1. Fix the partition bug: DRIFT Helius shards were written under `pipeline_mode=batch_hyperliquid`
      (verified live). If the Helius path is deleted per the todo above this dies with it — otherwise fix the mode
      resolution. Audit whether any OTHER venue's shards carry a foreign `pipeline_mode`. Repo:
      market-tick-data-service.
- [x] ✅ [DECISION] P1. The ~2026-04-01→today tail has NO Velocity archive coverage (200/0 bytes). Decide the source for
      it: (a) wait — the archive lags ~3.5 months and should backfill itself; (b) live capture forward from now; (c)
      another source. Note the DRIFT `derivative_ticker` leg is separately broken (legacy
      `fundingRates?     marketName=` endpoint now 403 — see
      `defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15`). — **RULED + BUILT 2026-07-16
      (data_engineering)**: operator ruled (b) properly-decoded on-chain — see "OPERATOR RULING 2026-07-16" below — and
      it's now shipped: `market-tick-data-service@3bad0745` adds `drift_v2_onchain_decoder.py` (pure Anchor
      `FundingRateRecord` event decode — discriminator + fixed-width borsh fields + PDA derivation, all hand-rolled with
      zero new deps, verified byte-for-byte against the Rust source + published IDL) and wires
      `DriftV2HistoricalIngester.collect_funding_rates_onchain` as the `perp_funding` source for `day >= 2026-04-01`,
      tagged `pipeline_mode=batch_solana_rpc` (distinct from Velocity's `batch_onchain_rpc`). **Acceptance gate
      PASSED**: decoding the real captured `Program data:` log line for tx_sig
      `Zv6vmk3b2K4ECF4mEM6qfEHeGW9A7R3uydpeTYuKxy5k7JJ4J73cTa4SrAaoet9YSo9GWQHvZspsHQPR2Uhhb2c` (slot 312968596,
      2025-01-09) reproduces the known-good SOL-PERP Velocity row FIELD-FOR-FIELD, including exact fixed-point decimal
      strings (`funding_rate="0.002007041"`, `cumulative_funding_rate_long="53.711133650"`, …) — see
      `test_drift_v2_onchain_decoder.py::TestKnownGoodParity`. **Source-strategy decision**: chose per-market
      `PerpMarket`-PDA-scoped `getSignaturesForAddress` (option ii, "narrower is better if real") over the operator's
      literal "walk the whole program once" fallback — measured live: program-wide is ~1.2M sigs/day (the exact volume
      that OOM-killed the old Helius path); PDA-scoped avoids that class entirely (proven: SOL-PERP's PDA correctly
      cross-matched a real Jan-2025 funding tx's `loadedAddresses`). **BUT see the new P1 finding below — live
      verification on the requested 2026-04+ gap surfaced a real, unresolved data-availability problem this decision
      does NOT yet fully solve.**
- [ ] [DATA] P1. **NEW FINDING 2026-07-16 (data_engineering), surfaced while proving the on-chain decoder on a real gap
      day per the work order's step 6.** The decoder is CORRECT (parity test passes field-for-field) but LIVE
      verification against the 2026-04→2026-07 gap reveals the per-market-PDA-scoped signature walk is currently NOT
      finding real funding-settlement transactions for Drift's top 3 markets. Measured live 2026-07-16 (Helius RPC,
      `getSignaturesForAddress` scoped to each market's `PerpMarket` PDA): walked ~125,000 signatures for SOL-PERP (120
      pages × ~1,000, spanning 2026-04-15 → 2026-07-16) plus spot-checks on BTC-PERP/ETH-PERP — **ZERO transactions with
      `err: null` (i.e. zero SUCCESSFUL transactions of ANY kind) touch any of these three PerpMarket PDAs anywhere in
      that window.** Every single sampled signature failed, overwhelmingly with Anchor error code 101 (framework-level
      "instruction fallback not found" — the discriminator doesn't match any handler in the currently-deployed program)
      plus some 6012 (`InvalidRepegRedundant`). Corroborating evidence: the `drift-labs/protocol-v2` "master" branch
      source (`programs/drift/src/lib.rs` lines ~743/751) shows the standalone `update_funding_rate` /
      `update_perp_bid_ask_twap` instruction entrypoints are COMMENTED OUT — i.e. Drift removed/moved these as
      directly-callable top-level instructions at some point; funding updates now happen as a side effect inside
      order-fill logic (`controller/orders.rs:1421` calls `controller::funding::update_funding_rate` internally). The
      failure wall is consistent with a large population of stale keeper/MEV bots still calling the OLD discriminators
      against the CURRENT program and getting "instruction fallback not found" on every attempt, burying any genuine
      (rarer, fill-embedded) successful touch under sheer volume. Cross-check: the Drift PROGRAM address itself is
      healthy (174/200 and 282/1000 recent samples succeed — Drift is very much alive) but a 61-tx spot-check of recent
      PROGRAM-wide successes found NONE that reference the SOL-PERP PDA — current perp-market activity in the sampled
      window skews toward lending/staking/spot rather than the classic direct-PerpMarket-touch pattern the 2025
      Velocity-era data used. **Practical effect**: for the SPECIFIC example day the work order suggested (2026-05-15,
      SOL-PERP) the shipped decoder correctly, honestly returns 0 rows in ONE RPC call (page 0 already spans
      2026-05-12→2026-07-14 with zero entries landing in the 05-15 window specifically — not a page-budget bug, a
      genuine data gap in this account's signature history) — this is the CORRECT honest-absence behaviour, not a
      defect, but it means the 2026-04+ gap is NOT yet actually filled for these markets pending this follow-up.
      **Recommended next steps (not actioned here — this todo's own scope is DATA/investigation, ~0.5-1d)**: (a)
      identify the CURRENT correct on-chain touchpoint for funding settlement post-upgrade (may require the current
      Anchor IDL/instruction list rather than the "master" git branch, which may itself lag or lead what's actually
      deployed) — grep for which anchor instruction currently wraps `fillPerpOrder`/`placeAndTakePerpOrder` and check
      whether ITS account list reliably includes the `PerpMarket` PDA as writable (if so, scope the signature walk to
      that instruction's typical account set instead, or accept sparser/costlier discovery); (b) try scoping the
      signature walk to a genuine Drift keeper wallet (the earlier known-good 2025 funding tx's fee-payer,
      `FetTyW8xAYfd33x4GMHoE7hTuEdWLj1fNnhJuyVMUGGa`) instead of the market PDA — a real keeper's own signature history
      wouldn't be polluted by unrelated bots' stale-discriminator failures; (c) confirm with Drift's current
      docs/Discord whether SOL-PERP/BTC-PERP/ETH-PERP funding settlement genuinely still happens on-chain via a
      `FundingRateRecord`-emitting path at all in mid-2026, or whether it moved off-chain/into a different settlement
      cadence. Repo: market-tick-data-service.

## Drift public-API migration — MEASURED 2026-07-16 (answers "how do we fill the 3.5-month gap?")

Drift retired its free data surface in stages; the gap is **structural, not a lag — waiting will never fill it**:

| host                                                          | probed state 2026-07-16                                                                                                                                                                                       |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `data.api.drift.trade/market/{M}/{dt}/{Y}/{M}/{D}?format=csv` | ALIVE but archive **FROZEN ~2026-03-31** (2026-04-05+ → HTTP 200, 0 bytes; market-wide: BTC/ETH/SOL all empty)                                                                                                |
| `data.api.drift.trade/fundingRates?marketName=…`              | **403** (the endpoint `drift_adapter.py:12` still uses)                                                                                                                                                       |
| `data.api.drift.trade/` `/docs` `/health`                     | **403** (CloudFront serves data paths only — no discoverable index)                                                                                                                                           |
| `drift-historical-data-v2.s3.eu-west-1.amazonaws.com`         | ALIVE but **FROZEN at 2025-01-08** — SOL-PERP `fundingRateRecords` = 793 keys, 2022-11-04→2025-01-08, `IsTruncated=false`. Layout is `{dt}/{year}/{YYYYMMDD}`, data_types `fundingRateRecords`/`tradeRecords` |
| `dlob.drift.trade` (in UAC config)                            | **NXDOMAIN** — retired                                                                                                                                                                                        |
| `api.drift.trade`                                             | **NXDOMAIN**                                                                                                                                                                                                  |
| **`mainnet-beta.api.drift.trade`**                            | **ALIVE + HEALTHY** — `/health` → `{"success":true}` — but `/fundingRates` and `/markets` → **401 Unauthorized** (server: envoy/CloudFront)                                                                   |

**Conclusion: Drift moved to an AUTHENTICATED API.** The free chain (S3 → Velocity archive) ends at 2026-03-31, which is
exactly where our DRIFT data stops. Verified independently: **zero DRIFT objects of ANY data_type** exist in the defi
bucket for 2026-04-15 → 2026-07-15.

**OPERATOR RULING 2026-07-16 — take path (b): decode on-chain properly.** Rejected (a) "get a Drift API key" as the
primary path (vendor dependency; their next migration breaks us again). The decoder is ALSO the correct version of what
the Helius path pretended to do. Note this REVERSES the earlier "retire, don't redesign" advice in a specific way:
retire the Helius path for HISTORY (Velocity covers 2022-11→2026-03 correctly and for free), but build a REAL on-chain
event decoder for the 2026-04→forward window — the operator's original design instinct ("grab at once and filter, keep
per-instrument-per-day writes") was right for exactly this window.

## Progress log

- 2026-07-16: Filed. Operator asked whether Drift's public API covers full history; proving it out surfaced that the
  Helius shards it would replace contain no funding data at all. Operator's initial instinct was to redesign the Helius
  adapter (fetch program-wide once, filter per market, keep per-instrument-per-day writes) — that design is sound in the
  abstract but unnecessary: the Velocity API already returns correct per-market funding directly, so the recommendation
  is RETIRE rather than redesign. Nothing deleted yet — purge is the P0 todo above.

- 2026-07-16 (data_engineering, on-chain-decoder build): Built + shipped the real on-chain `FundingRateRecord` decoder
  per the operator ruling above. **Research**: fetched the published Drift Anchor IDL (`sdk/src/idl/drift.json`) and the
  `programs/drift/src/state/events.rs`/`controller/funding.rs` Rust source (shallow sparse-clone of
  `drift-labs/protocol-v2`) — confirmed the exact field layout/order/precision of the `#[event] FundingRateRecord`
  struct, computed its Anchor discriminator (`sha256("event:FundingRateRecord")[:8]`), and hand-verified the whole
  decode chain against a REAL transaction fetched live from Solana mainnet (public RPC `getTransaction` on the
  known-good day's tx_sig) — the decode reproduced the known-good SOL-PERP 2025-01-09 Velocity row exactly, including
  the `market_index=0` PDA (`8UJgxaiQx5nTrdDgph5FiahMmzduuLTLf5WmsPegYA6W`, derived via a hand-rolled ed25519-off-curve
  `find_program_address` — no solana-py/solders dependency added). **Design decision**: evaluated program-wide "grab
  once, filter" (the operator's literal fallback) vs per-market `PerpMarket`-PDA-scoped `getSignaturesForAddress` (the
  "narrower source" option) — chose the latter because it measured orders of magnitude smaller than program-wide
  (avoiding the exact OOM class from `drift_v2_sig_index_program_wide_helius_oom_2026_07_15`) while still being a REAL,
  cheap, per-account RPC primitive (not a filter I invented — `getSignaturesForAddress` genuinely indexes any account a
  tx references). **Shipped**: `market-tick-data-service@3bad0745` — new `drift_v2_onchain_decoder.py` (pure
  decode/PDA/base58, zero new deps), 2 new RPC primitives in `_solana_rpc_async.py`
  (`solana_get_signatures_for_address`/`solana_get_transaction`),
  `DriftV2HistoricalIngester.collect_funding_rates_onchain` wired as the `perp_funding` source for `day >= 2026-04-01`
  tagged `pipeline_mode=batch_solana_rpc` (distinct from Velocity's `batch_onchain_rpc` — both pre-registered in UAC's
  `_KNOWN_BATCH_SOURCES_BY_AG[DEFI]`, no UAC changes needed). 44 new/extended unit tests incl. the field-for-field
  parity acceptance test; full `quality-gates.sh --no-fix` green (6233 passed, sentinel `ba866544...`); quickmerge
  landed clean on `live-defi-rollout`. **Gap-day proof (work order step 6) — HONEST result, not the hoped-for one**: ran
  the shipped decoder live against the operator's suggested example (2026-05-15, SOL-PERP) — 0 rows, correctly and
  cheaply (1 RPC call, honest per-day window check, not a bug). Dug deeper (see the new P1 todo above) because 0 rows on
  the FIRST example day warranted verification it wasn't a decoder defect: found a much bigger, genuine discovery — zero
  SUCCESSFUL transactions touch the SOL-PERP/BTC-PERP/ ETH-PERP `PerpMarket` PDAs anywhere across ~125,000 sampled
  signatures spanning 2026-04-15→2026-07-16, apparently because Drift's currently-deployed program no longer has
  standalone `update_funding_rate`/ `update_perp_bid_ask_twap` entrypoints (commented out in the "master" source) and a
  large population of stale bots keep failing against the old discriminators, burying whatever genuine fill-embedded
  funding-settlement activity remains. **This means the decoder is proven CORRECT but the 2026-04+ gap is not yet
  actually FILLED for these markets** — filed as the new P1 todo above with 3 concrete next-step options, not resolved
  in this session (out of this session's scope — the work order asked to build+prove the decoder, not to solve a
  freshly-discovered protocol-side data-availability question). No fabricated success reported; the manifest-facing
  behaviour (honest zero via `record_zero_rows`) is unaffected and correct either way.
