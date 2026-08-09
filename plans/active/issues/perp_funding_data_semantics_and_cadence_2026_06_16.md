---
doc_type: issue
title:
  "Perp funding data-semantics + cadence: registry inconsistency, funding_timestamp one-settlement offset, no historical
  cadence tracker"
summary:
  Three related correctness gaps in how perp **funding** is annualised and time-stamped across the workspace, found
  while building a `carry_staked_basis` funding-carry analysis that reads `data_type=...
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-service,
    e2e-testing,
    execution-service,
    features-service,
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [data-correctness, cefi, defi, uac, mtds, backfill, deribit, data-pipeline]
related:
  [
    /plans/archive/issues/aster_perp_funding_backfill_stale_launcher_and_genesis_conflict_2026_07_28.md,
    /plans/archive/2026_08/issues/cefi_onchain_perp_forward_capture_outage_2026_08_03.md,
  ]
created: 2026-06-16
author: unknown
parent_epic: mtds_mdps_master
priority: P1
source:
  [
    2026-06-16 carry_staked_basis funding-carry scan (e2e-testing/scripts/defi/staked_basis_funding_scan.py) — empirical
    exchange-API spot-checks vs GCS derivative_ticker,
  ]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
context_scope:
  [
    /codex/02-data/carry-venue-live-integration-reference.md,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    unified-api-contracts/unified_api_contracts/registry/perp_funding_cadence.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py,
    /plans/archive/issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-04
---

# Perp funding data-semantics + cadence (2026-06-16)

Three related correctness gaps in how perp **funding** is annualised and time-stamped across the workspace, found while
building a `carry_staked_basis` funding-carry analysis that reads `data_type=derivative_ticker` funding from GCS and
cross-checks against the venue APIs. Funding is a P0 input to `carry_staked_basis` net-carry — a cadence error mis-ranks
the whole book.

## What I found

### Finding 1 — two funding-cadence registries disagree; one is wrong (P1, data-correctness)

Two SSOTs encode per-venue funding cadence and they **disagree**:

- `unified_api_contracts/registry/perp_funding_cadence.py` → `FUNDING_CADENCE_SECONDS` (consumed by
  `annualise_funding_rate_bps`, features-service, risk): **aster = 8h, deribit = 1h**.
- `unified-trading-library/unified_trading_library/return_metrics.py:58` → `FUNDING_PERIODS_PER_DAY`: **ASTER = 24.0
  (1h), DERIBIT = 3.0 (8h)** — the inverse for both.

**Empirically resolved against the exchange APIs (2026-06-16):**

| Venue       | API probe                                                                  | True cadence    | UAC `perp_funding_cadence` | UTL `FUNDING_PERIODS_PER_DAY` |
| ----------- | -------------------------------------------------------------------------- | --------------- | -------------------------- | ----------------------------- |
| Binance     | `fapi/v1/fundingRate` `fundingTime` spacing = 28 800 s                     | 8h (3/day)      | 8h ✅                      | 3.0 ✅                        |
| **Aster**   | `fapi.asterdex.com/fapi/v1/fundingRate` `fundingTime` spacing = 28 800 s   | **8h (3/day)**  | 8h ✅                      | **24.0 ❌ (8× over)**         |
| **Deribit** | `public/get_funding_rate_history` returns **hourly** rows w/ `interest_1h` | **1h (24/day)** | 8h ✅ [^1]                 | **3.0 ❌ (8× under)**         |
| Hyperliquid | `info fundingHistory` spacing = 3 600 s                                    | 1h (24/day)     | 1h ✅                      | 24.0 ✅                       |
| OKX         | `funding-rate-history` `fundingTime` spacing = 28 800 s                    | 8h (3/day)      | 8h ✅                      | 3.0 ✅                        |

[^1]:
    **Corrected 2026-07-12** (doc-reconciliation finding 176, §A2 "50 reclassified" blanket ruling; was: `1h ✅`). This
    table records the state as originally probed 2026-06-16; this doc's own later, dated resolution (todos below,
    "CONFIRMED 2026-06-17") found UAC's stored Deribit `derivative_ticker.funding_rate` figure is the **8h** aggregate
    (`interest_8h`), not the per-hour rate, so `FUNDING_CADENCE_SECONDS["deribit"]` was corrected `1h → 8h` to match
    what's actually stored (the prior 1h value over-stated Deribit APY 8×). The "True cadence" column is unchanged —
    Deribit's underlying settlement mechanics remain hourly; only the UAC registry value (which must match the stored
    figure, not the raw settlement frequency) was corrected.

So **`perp_funding_cadence` (UAC) is correct; `FUNDING_PERIODS_PER_DAY` (UTL) is wrong for Aster (8× over-states) and
Deribit (8× under-states).** Any consumer of `FUNDING_PERIODS_PER_DAY` mis-annualises Aster/Deribit funding by 8×.
`strategy-service/.../trace_carry_staked_basis.py` and `return_metrics.py` are the suspected consumers — audit + repoint
to the UAC SSOT, then delete `FUNDING_PERIODS_PER_DAY` (no parallel registries).

> Note — Deribit funding normalisation: Deribit charges **hourly** (`interest_1h`) but also publishes an `interest_8h`
> figure. Whatever MTDS stores in the Deribit `derivative_ticker.funding_rate` must be annualised at the cadence that
> matches that figure (1h if it's the per-hour rate). Confirm the Tardis→MTDS Deribit funding field is the per-hour rate
> before trusting `annualise(rate, "deribit")` at 24/day.

### Finding 2 — `funding_timestamp` is offset by one settlement vs the venue's official `fundingTime` (P1)

GCS `derivative_ticker.funding_rate` **values match the exchange API exactly** (verified Binance BTCUSDT 2026-04-29:
`+0.00001305 / −0.00002840 / +0.00003571` identical) — the data is clean. **But** the pairing is offset: grouping the
GCS rows by `funding_timestamp` and taking the rate yields each rate paired with the **next** settlement, whereas the
venue's official `fundingTime` is the settlement instant the rate is **charged at**. Concretely the rate Binance charges
at 08:00 appears in GCS under `funding_timestamp` 16:00.

Consequence: you **cannot currently read exact discrete per-settlement funding** off the parquet by grouping on
`funding_timestamp` — it mislabels at day boundaries (and double-counts the boundary rate). The analysis harness works
around it with the **day-mean of the rate column** (offset-robust, matches what features-service effectively does), but
that is a workaround, not the target. **We should be able to use exact discrete funding** (per-settlement, correctly
time-stamped to the charge instant) — for accurate realised-funding accounting and for using `predicted_funding_rate`
(already a column) to gauge entry on venues that publish a forward rate. Likely fix: have the MTDS adapter persist the
funding settlement as `(fundingTime = charge instant, fundingRate = rate charged then)` matching the venue API, OR add a
canonical `funding_settlement` data_type with one row per settlement. Audit `funding_timestamp` semantics across
adapters (Tardis cefi, hyperliquid, the OKX `next_funding_timestamp` mapping) and document the canonical meaning.

### Finding 3 — `perp_funding_cadence` is STATIC; no historical cadence tracker (P2)

`FUNDING_CADENCE_SECONDS` is a single static dict — it has **no historical versioning**, so a venue changing its funding
interval over time (e.g. a pair moving 8h→4h, or a venue-wide change) is invisible and would silently mis-annualise
historical windows. We need a **historical funding-cadence tracker in GCS**, sourced either canonically (from venue docs
via a maintained script) or **inferred from the observed frequency of funding_timestamp/`fundingTime` updates** in the
captured data (the data already lets us count settlements/day per instrument per day). The analysis harness already
records observed `n_settlements` per shard as a cross-check seed for this.

### Finding 4 — DERIBIT `funding_timestamp` cannot be safely DERIVED from scratch: it has no discrete charge instant, unlike every other venue this reprocessing fix covers (investigated 2026-07-28, STOPPED pending operator decision)

Follow-up to the DERIBIT line inside the P2 scale-out todo above (which correctly found DERIBIT 100% null and no-op's
it). The operator separately asked: since DERIBIT `funding_rate` is populated but `funding_timestamp` is 100% null and
there's no `next_funding_timestamp` column at all, why not DERIVE both from scratch for every historical row, using the
tick's own `timestamp` + Deribit's known 8h funding cadence (already registered,
`FUNDING_CADENCE_SECONDS["deribit"] = 28800`)? The explicit ask was to verify the **anchor** (is the 8h grid
UTC-midnight-aligned — 00:00/08:00/16:00 UTC — the BitMEX/Deribit-pioneered industry convention — or offset
differently?) empirically, not by assumption, and to STOP and report honestly if genuinely uncertain rather than guess,
"since an off-by-one here is worse than leaving it null."

**Real production-sample re-confirmation (2026-07-28, extends the shipped script's 3-date spot-check to 7 real shards
spanning the full history):** pulled real captured parquet directly from
`gs://market-data-tick-cefi-prd-central-element-323112` —
`DERIBIT:PERPETUAL:{BNB-USDC@LIN, BTC-USD@INV, ETH-USD@INV, BTC-USDC@LIN, ETH-USDC@LIN}` across
`day={2019-06-01, 2020-06-01, 2022-01-01, 2023-06-01, 2024-01-01, 2026-05-01}` (7 shards total). **Every single shard**:
`funding_rate` 0/N null (100% populated), `funding_timestamp` schema-inferred type `null` and N/N null (100% null — has
literally never had a non-null value in this passthrough), no `next_funding_timestamp` column. Confirms + extends the
original 3-date spot-check cited in the shipped script's docstring.

**Anchor verification — rigorous, multi-source, NOT an assumption:**

1. **The premise itself does not hold.** Deribit's own live ticker API
   (`GET /api/v2/public/ticker?instrument_name=BTC-PERPETUAL`, queried live 2026-07-28) returns only two funding-related
   SCALARS — `current_funding` and `funding_8h` — **no next-funding-time / funding-timestamp field of any kind**. This
   is a structural difference from Binance/Bybit/OKX's own APIs, which DO expose a genuine discrete
   `fundingTime`/`nextFundingTime` field (the real field the already-shipped 6-venue fix shifts back one cadence
   period). Tardis's own documented behavior for `derivative_ticker.funding_timestamp`: "the timestamp of the next
   funding event... empty if the exchange does not provide one" — which is exactly why our bulk-CSV passthrough has
   always captured it null for Deribit: **Deribit itself has never had one to relay.**
2. **Deribit's own support/education documentation** (`insights.deribit.com/education/perpetual-swap-funding`, queried
   live 2026-07-28): funding is "calculated in real time and transferred every few seconds" — i.e. continuously, not in
   a lump sum at fixed instants — and separately, account-level settlement (crystallising the continuously-accrued
   funding PnL into cash balance) happens **once daily at 08:00 UTC**, not three times daily. The "8 hour rate" Deribit
   displays/stores is explicitly a **comparison-normalisation convention** ("the 8 hour rate is displayed to make
   comparison simpler... it is actually calculated in real time"), not evidence of a discrete charge event.
3. **Deribit's own live `get_funding_rate_history` endpoint** (queried live 2026-07-28, `BTC-PERPETUAL`, 48 hourly rows
   spanning 2025-05-01→02): `interest_8h` is a continuously-evolving, hourly-sampled ROLLING window (e.g. 01:00=8.86e-7
   → 08:00=1.45e-6 → 09:00=2.63e-6 → 12:00=1.24e-5 → 15:00=1.23e-5 → 16:00=1.19e-5 → 20:00=1.74e-6 →
   00:00(May-2)=3.96e-6) — **no reset or discontinuity pattern at ANY of the 00:00/08:00/16:00 UTC boundaries**,
   consistent with a trailing average, not a periodic settlement.
4. **Real captured parquet** (`DERIBIT:PERPETUAL:BNB-USDC@LIN`, 2026-05-01, 55,291 rows — the operator's own reference
   sample): `funding_rate` changes value **~1,454 times across the single day** (roughly every 1-90 seconds),
   continuously tracking the mark/index basis — **no discontinuity precisely at 00:00:00 / 08:00:00 / 16:00:00 UTC**
   distinguishable from the ambient minute-to-minute noise.

**Conclusion: the anchor cannot be verified because the premise it would anchor does not hold.** Binance/Bybit/OKX/etc.
genuinely charge funding in discrete lump sums at their own venue's real, discrete `fundingTime` — shifting that raw
value back one registered cadence period (the already-shipped fix) is a real correction of a real forward-looking
timestamp. **Deribit has no analogous discrete charge instant to correct or derive** — its funding accrues and is paid
continuously, and its own APIs (ticker + funding-rate-history) confirm no fixed-instant reset pattern exists at
00:00/08:00/16:00 UTC or anywhere else. Fabricating a calendar-aligned `funding_timestamp`/`next_funding_timestamp` pair
for DERIBIT — even using the industry-standard 00:00/08:00/16:00 UTC grid — would assert a "charge instant" Deribit
itself has never reported and does not appear to have, silently changing `CanonicalDerivativeTicker.funding_timestamp`'s
documented meaning ("the instant funding_rate was actually CHARGED") to mean something different (a reporting-bucket
label) for exactly one venue, with no code-visible way for a downstream consumer to tell the difference. Per the
operator's own stated bar ("an off-by-one here is worse than leaving it null"), this session **STOPS here and does not
build the derivation** — see the new todo below for the three options this needs an operator decision on. **No
market-tick-data-service code path was added**; the reprocessing script's docstring was updated (comment-only) to record
this finding at the DERIBIT `skipped_all_null_no_forward_value` bullet it already documents, so a future reader doesn't
have to re-derive it. Real full-historical DERIBIT scope RE-VERIFIED this session (fresh `--mode scan` run, not trusted
from the prior pass): **4,631 shards / 219,152,270 rows, 2019-03-30→2026-05-01** — unchanged from the original scoping
pass.

## Why it matters

`carry_staked_basis` ranks the entire perp book by annualised funding; an 8× cadence error on Aster/Deribit, a
boundary-mislabelled discrete read, or a silently-stale static cadence all corrupt the ranking → wrong coins selected,
wrong net carry, wrong promote decision. This is the data-pipeline-correctness heartbeat for the CeFi funding leg.

## Recommended decision / todos

- [x] ✅ [DATA] P1. Audit every consumer of UTL `return_metrics.FUNDING_PERIODS_PER_DAY`; repoint to UAC; delete it (no
      parallel registry); UAC unit test. **DONE 2026-06-17** via the e2e correctness dispatch
      (`e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md`): UTL dict DELETED
      (unified-trading-library@b587b91b/ ed622af8), execution decision-trace repointed (execution-service@38c7e06f),
      strategy docstring repointed (strategy-service@b91d3e1f), delta_one funding_oi repointed (features-service,
      pending peer-UAC-dirt), UAC regression tests (aster=8h, deribit=8h-figure, venue-dir norm)
      (unified-api-contracts@7fade10/fd5bcfa). **NB the test asserts deribit=8h-FIGURE, not 1h** — superseded by the
      next todo's confirmation.
- [x] ✅ [DATA] P1. Confirm the MTDS Deribit `derivative_ticker.funding_rate` figure. **CONFIRMED 2026-06-17 (e2e
      empirical probe): it is the 8h FIGURE** (≈ API `interest_8h` ~ -1e-6, not `interest_1h` ~ -1e-8), NOT the per-hour
      rate. Resolution: UAC `FUNDING_CADENCE_SECONDS["deribit"]` corrected `1h → 8h` so `annualise(rate,"deribit")`
      matches the stored 8h figure (preserves the data-matches-API invariant; the prior 1h over-stated Deribit APY 8×).
      Documented in the `perp_funding_cadence.py` module docstring (figure-vs-charge distinction). The codex/02-data doc
      update rides the codex-audit below.
- [x] ✅ [DATA] P1. Make exact discrete per-settlement funding readable: persist funding settlements time-stamped to the
      charge instant (matching venue `fundingTime`), or add a canonical per-settlement funding data_type. Document the
      canonical `funding_timestamp` meaning across adapters. **Repo: market-tick-data-service + unified-api-contracts.**
      **DONE 2026-07-27** — audited every `funding_timestamp`/`next_funding_timestamp` write path (OKX, Binance, Bybit,
      Aster, Deribit, Hyperliquid, Tardis WS-replay + bulk CSV). Found + fixed three go-forward bugs: (1)
      `market-tick-data-service` MTDS-local `okx.py` adapter had OKX's `fundingTime` (the charge instant per OKX's own
      API) swapped into `next_funding_timestamp` instead of `funding_timestamp`, and never read `nextFundingTime` at
      all; (2) `hyperliquid_s3.py`'s `_build_funding_ticker` (the `funding_history` REST backfill path) never populated
      `funding_timestamp` at all even though its raw `time` field already IS the charge instant; (3) UAC
      `external/tardis/normalize.py::normalize_tardis_derivative_ticker` (the WS-replay/live path) never populated
      `funding_timestamp` and never read the raw `funding_timestamp` key at all — now derives the true charge instant by
      shifting the raw (forward-looking) value back one cadence period via the `perp_funding_cadence` registry, only
      when the venue's cadence is registered (honest-absence otherwise, no guessing). Documented the canonical
      `funding_timestamp` (charge instant) vs `next_funding_timestamp` (forward-looking) meaning on
      `CanonicalDerivativeTicker`'s field docstrings. Aster/Bybit/OKX-UAC-reference were already correct (Aster fixed
      2026-06-17; Bybit's `fundingRateTimestamp` and OKX-UAC's `funding.fundingTime` were already split correctly) —
      confirms this was NOT a single repeated bug but two distinct bug classes (Tardis's raw-wire semantic + an
      MTDS-local OKX field-swap) producing the same symptom. Shipped: `unified-api-contracts@22689df5`
      (CanonicalDerivativeTicker docs + tardis normalize derivation + new test
      `test_tardis_normalize_derivative_ticker.py`), `market-tick-data-service@466d5670` (okx.py + hyperliquid_s3.py
      fixes + new/updated tests `test_adapter_okx.py`, `test_hyperliquid_s3.py`). **NOT fixed here (see follow-up todo
      below): the bulk historical Tardis-CSV passthrough** — the dominant source for CeFi derivative_ticker backfills —
      still writes the raw Tardis wire `funding_timestamp` column (forward-looking) straight through unrenamed, so
      already-written historical parquet has `funding_timestamp` one cadence period ahead of the true charge instant.
      This is a schema-agnostic streaming pass-through (`tardis_stream_processor.py`) shared across every CeFi
      data_type, and `tardis_shared.py`'s own `_WIRE_COLUMN_RENAMES` docstring already documents `derivative_ticker` as
      deliberately untouched (no registered SchemaContract; consumers still expect the raw wire column names) —
      correcting it is a cross-cutting reprocessing/schema decision, not a same-blast-radius fix, so it's tracked as its
      own todo below rather than resolved unilaterally.
- [x] ✅ [DATA] P2. Bulk historical Tardis-CSV `derivative_ticker.funding_timestamp` is forward-looking, not the charge
      instant — reprocessing/schema decision needed. Found + documented (not fixed) while closing the P1 todo above:
      `tardis_stream_processor.py` streams raw Tardis CSV columns straight to parquet with zero per-column
      reinterpretation (shared across every CeFi data_type, so it can't special-case `derivative_ticker` without a wider
      audit), and `tardis_shared.py`'s `_WIRE_COLUMN_RENAMES` already flags `derivative_ticker` as deliberately
      untouched. Two options, needs a design decision (not an in-slot judgment call): (a) add a
      `derivative_ticker`-specific column derivation (rename raw `funding_timestamp` → `next_funding_timestamp`, derive
      true `funding_timestamp` via `perp_funding_cadence` cadence-shift) to the bulk write path going forward, leaving
      already-written historical shards uncorrected-but-documented; or (b) a one-time reprocessing/backfill of existing
      historical `derivative_ticker` parquet across every CeFi Tardis venue (heavy-I/O, VM-launched,
      single-walk-discipline-gated). **Repo: market-tick-data-service** (`tardis_shared.py`,
      `tardis_stream_processor.py`) **+ unified-api-contracts** (documents the gap on
      `CanonicalDerivativeTicker.funding_timestamp`'s docstring already).

      **Operator decision (2026-07-28): option (b) — full historical reprocessing, not a forward-only fix.** Design +
      build + bounded-sample proof DONE this session; the full-corpus run is a separate VM-launched follow-up (still
      open, see the dependent todo below) — this todo itself stays unchecked until that full run completes.
      Shipped: `market-tick-data-service@873c6c73`
      (`scripts/one_offs/reprocess_bulk_tardis_derivative_ticker_funding_timestamp_2026_07_28.py` +
      `tests/unit/scripts/test_reprocess_bulk_tardis_derivative_ticker_funding_timestamp_2026_07_28.py`, quality-gates.sh
      green). Per-shard correction (Arrow-level, byte-identical on every other column): preserves the raw wire value as
      `next_funding_timestamp`; derives `funding_timestamp = raw - cadence` via UAC `perp_funding_cadence`
      (`fundings_per_day`/`is_supported_venue`), mirroring `external/tardis/normalize.py::normalize_tardis_derivative_ticker`'s
      formula exactly. `--mode scan` is the manifest-driven quantify step (no writes); `--mode apply [--apply]` does the
      real per-object backup+CAS-overwrite+verify flow for one `--venue`/date-window.

      **Real scope is wider than this todo's own text assumed** (manifest scan + live-content probe, 2026-07-28) — 10
      CeFi Tardis venues carry `derivative_ticker` via `pipeline_mode=batch_tardis` (not 4):
      `BINANCE-FUTURES`/`BYBIT`/`OKX-SWAP`/`OKX-FUTURES`/`KRAKEN-FUTURES`/`BITGET-FUTURES`/`BITFINEX-FUTURES`/`DERIBIT`/
      `COINBASE-FUTURES`/`EXTENDED-STARKNET` (+ `LIGHTER-ZKSYNC` registered but 0 `captured` rows today). Manifest-row
      shard/row counts (captured, batch_tardis): `BINANCE-FUTURES` 273,703 shards / 23.9B rows (2019-12-30→2026-05-22) ·
      `OKX-SWAP` 194,041 / 25.8B (2021-01-01→2026-05-22) · `KRAKEN-FUTURES` 142,821 / 11.2B (2020-01-01→2026-05-22) ·
      `BYBIT` 139,331 / 6.5B (2020-01-01→2026-05-01) · `BITGET-FUTURES` 117,185 / 6.3B (2024-11-08→2026-05-22) ·
      `OKX-FUTURES` 78,293 / 20.4B (2021-01-01→2026-07-24, all dated-FUTURE) · `BITFINEX-FUTURES` 61,320 / 1.8B
      (2020-01-01→2026-07-24) · `DERIBIT` 4,631 / 219M (2019-03-30→2026-05-01) · `EXTENDED-STARKNET` 281 / 6,744
      (2026-01-14→2026-06-03) · `COINBASE-FUTURES` 40 / 3.4M (2026-07-24 only, brand-new capture).

      **Per-shard REAL content varies genuinely by data, not by a bug in this script** (live-probed samples across each
      venue's date range) — the reprocessing script auto-detects each case, no special-casing needed:
      - `DERIBIT` PERPETUAL shards are **100% null** for `funding_timestamp` across every sampled year (2019/2022/2026)
      — Deribit's raw Tardis wire apparently never populates a forward value for this data_type (funding_rate itself
      IS populated) — **nothing to correct, script no-ops cleanly** (`skipped_all_null_no_forward_value`).
      - Every dated-**FUTURE**-instrument-type shard sampled (`BINANCE-FUTURES`/`BYBIT`/`OKX-FUTURES`/`BITGET-FUTURES`
      dated contracts) is also 100% null — expected, dated futures have no periodic funding — **no-op, correct**.
      - `EXTENDED-STARKNET`'s raw wire schema **lacks the `funding_timestamp` column entirely** — `skipped_no_
      funding_timestamp_column`, no-op.
      - `COINBASE-FUTURES` is populated (real forward-looking values present) but `"coinbase"` is **not yet registered**
      in UAC `perp_funding_cadence.FUNDING_CADENCE_SECONDS` — the script correctly applies honest-absence (preserves
      `next_funding_timestamp`, leaves `funding_timestamp` null rather than guess); registering Coinbase's cadence
      first is a real, small, separate prerequisite if its (currently tiny — 40 shards, one day) history should get a
      derived `funding_timestamp` too.
      - `PERPETUAL` shards for `BINANCE-FUTURES`/`BYBIT`/`OKX-SWAP`/`KRAKEN-FUTURES`/`BITGET-FUTURES`/`BITFINEX-FUTURES`
      are the confirmed real-bug population needing correction: ~926,898 shards / ~75.0B rows.

      **Bounded sample proof (2026-07-28, real production data, full delete-safety protocol)**: BYBIT PERPETUAL
      `derivative_ticker`, 2026-03-25→2026-03-31 (86 real objects, discovered via prefix-scoped listing — NOT via the
      manifest's own row count, which undercounts this venue/window 7×/day vs the real object count, a pre-existing
      manifest-vs-GCS drift unrelated to this fix). Dry-run (staging-only): 86/86 `would_correct`, 0 errors; a spot-check
      confirmed exact math (`next_funding_timestamp - funding_timestamp == 28,800,000,000` µs = 8h for every row, every
      other column byte-identical). Real `--apply`: 86/86 `corrected`, 0 errors — original backed up
      (`_migrations/derivative_ticker_funding_timestamp_fix_2026_07_28/backups/20260728-143731/...`, byte-for-byte
      verified via `gcs_describe_object` size+crc32c match before overwrite), canonical path CAS-overwritten, new content
      verified landed, old (forward-looking) value verified GONE from the canonical path (independently re-checked
      post-hoc, not just the script's own internal assertion). Manifest `capture_status`/`row_count` for the exact
      touched slice (4,207 rows, `row_count` sum 654,890) confirmed **byte-identical** before vs after — the fix does
      not touch the manifest at all.

      **Go-forward gap (option (a)) also now closed, 2026-07-30**: the 2026-07-28 operator decision above deliberately
      scoped this todo to option (b) only, leaving the batch write path (`tardis_shared.py`) unfixed on purpose — a NEW
      `batch_tardis` pull for these venues would have kept reproducing the exact bug this reprocessing corrects for
      existing shards. Confirmed as a real, live risk (not theoretical): `launch-cefi-forward-poll.sh` uses the same
      `--mode batch` / `datasets.tardis.dev` path and is NOT on an automatic Cloud Scheduler cron for CeFi, so the
      exposure was "whenever a human/agent next re-runs a CeFi batch pull," not immediate — but real. Now that (b) is
      proven safe end-to-end on real production data (see the full-corpus completion note below), (a) was also
      implemented: `tardis_shared.py`'s `finalise_rows_and_path` now derives `funding_timestamp` at write time via a
      new `_derive_derivative_ticker_funding_timestamp` step, mirroring `normalize_tardis_derivative_ticker`'s exact
      semantics (same `perp_funding_cadence` registry, `is_supported_venue` + `cadence_seconds_as_of`; honest-absence
      for an unregistered venue, never a guess). 7 new tests including a direct cross-path proof (the same raw wire
      value run through the batch derivation and through the live-path normalizer derives an identical
      `funding_timestamp`). Shipped: `market-tick-data-service@dc7f2651`. Every NEW batch_tardis derivative_ticker
      write for a registered venue is now correct from the moment it's written — this todo's own gap is fully closed,
      not just worked around by periodic reprocessing.

**RESOLVED 2026-08-03 (slot-12, checkbox reconciliation — no new code needed, verified not just trusted).** Both
conditions this todo declared itself gated on ("this todo itself stays unchecked until that full run completes") are now
independently confirmed: (1) the go-forward write-path fix is live — `market-tick-data-service@dc7f2651` confirmed
present in this worktree (`tardis_shared.py::_derive_derivative_ticker_funding_timestamp`, wired into the batch write
path); (2) the full historical reprocessing (option (b), all 6 venues) is CONFIRMED FULLY COMPLETE per the dependent
todo directly below. Independently re-verified this session rather than trusted from prior text alone: downloaded a real
production shard (`BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN`, `day=2025-06-01`, `pipeline_mode=batch_tardis`, from
`gs://market-data-tick-cefi-prd-central-element-323112`) and confirmed
`next_funding_timestamp - funding_timestamp == 28,800,000,000µs` (8h) on every distinct-funding-timestamp row —
`funding_timestamp` now holds the charge instant, `next_funding_timestamp` the raw forward-looking value, exactly the
intended semantics. `gcloud compute instances list --filter="name~canonical-migration-cefi"` returns zero instances —
all migration VMs are gone (self-deleted on completion), consistent with the DEPLOYMENT_COMPLETED records below.
Reconciling this parent checkbox to match reality; no repo change shipped in this session.

- [x] ✅ [DATA] P2. Scale `reprocess_bulk_tardis_derivative_ticker_funding_timestamp_2026_07_28.py --mode apply --apply`
      to the full historical corpus via a VM (heavy-I/O rule — not the operator's/an interactive session's local
      machine), per the bounded-sample proof + real scope above. **GO recommendation** — the mechanism is proven (86/86
      real objects round-tripped with zero errors; manifest-unchanged verified), per-shard classification is data-driven
      (safe to run un-filtered across every venue/date — all-null/no-column/unregistered-cadence shards no-op cleanly,
      confirmed live). Real target: ~926,898 `PERPETUAL`-instrument-type shards / ~75.0B rows across
      `BINANCE-FUTURES`/`BYBIT`/`OKX-SWAP`/`KRAKEN-FUTURES`/`BITGET-FUTURES`/`BITFINEX-FUTURES` (+ `COINBASE-FUTURES`
      once a cadence is registered for it); `DERIBIT` + dated-`FUTURE`-type shards + `EXTENDED-STARKNET` can be included
      for completeness (confirmed no-op) or skipped for cost. Pre-migration drain (pause consolidators, snapshot) + SPOT
      provisioning per the VM-launcher runbook; per-object backup path
      `_migrations/derivative_ticker_funding_timestamp_fix_2026_07_28/backups/<run_ts>/...` — verify manifest
      `capture_status`/`row_count` unchanged for a sample slice per venue after the run, same as the bounded proof
      above. **Repo: market-tick-data-service + deployment-service** (VM launcher).

      **IN PROGRESS 2026-07-28 (slot-4 session, real state independently verified — do not trust prior text reports
      without checking live GCS/VM state, confirmed necessary this session).** `deployment-service/scripts/vm/
      launch-cefi-funding-timestamp-fix-vm.sh` existed committed (`deployment-service@2b232e3`) but had an
      UNCOMMITTED local fix sitting in the slot-4 worktree (`VM_NAME` shortened `canonical-migration-cefi-
      funding-timestamp-{venue}-{ts}` → `...-fts-{venue}-{ts}`) — the original form is 75 chars for the longest venue
      slug (`bitfinex-futures`), over GCE's 63-char instance-name limit, so every launch would have failed at
      instance-create time. That fix (plus a new relaunch-registry binding gap found while verifying it — see below)
      shipped this session: `deployment-service@0545f414`.

      **Real discovery: a PRIOR launch of this exact job (BINANCE-FUTURES/BYBIT/OKX-SWAP/KRAKEN-FUTURES/
      BITGET-FUTURES/BITFINEX-FUTURES, the "original 6") was ALREADY RUNNING on real GCE VMs since ~17:03-17:15 BST
      2026-07-28 — contradicting the "died before ever launching anything" framing this session was briefed with.**
      Confirmed via `gcloud compute instances list` + real `PROGRESS.json`/`run.log` reads (not trusted from any
      text report): all 6 VMs (`canonical-migration-cefi-fts-{binance-futures,bybit,okx-swap,kraken-futures,
      bitget-futures,bitfinex-futures}-20260728-17****`) were RUNNING with monotonic, actively-advancing
      `last_completed_date` checkpoints and real `action=corrected` rows landing in `run.log` — a genuine, healthy,
      already-3+-hours-in run, not a stall. **This session independently (re-)launched the same 6 venues before
      discovering the duplicates via `gcloud compute instances list` — the 6 newer duplicate VMs
      (`...-21****`) were deleted immediately** (`gcloud compute instances delete`, confirmed) once the collision was
      found, to avoid wasted SPOT compute + a possible concurrent-write race on the same GCS objects (the script's
      own `gcs_conditional_put` generation-check would have made a real collision fail loud rather than corrupt
      data, but running 12 VMs instead of 6 for the same job is pure waste). **Status as of this session's end**: the
      6 original 17:0x-launched VMs remain the live, correct, healthy run — checkpoints as of ~20:21 UTC:
      BINANCE-FUTURES `2021-08-08`, BYBIT `2022-10-15`, OKX-SWAP `2022-01-31`, KRAKEN-FUTURES `2023-08-26`,
      BITGET-FUTURES `2025-03-27`, BITFINEX-FUTURES `2024-08-24` (all monotonic, all still far from their respective
      end dates — this genuinely will take many more hours; see the parallelization-threshold flag below).

      **COINBASE-FUTURES: launched fresh this session (`canonical-migration-cefi-fts-coinbase-futures-
      20260728-211633`, 2026-07-24..2026-07-28) and RAN TO COMPLETION within the same turn** — 40/40 real objects
      `corrected`, 0 errors, `exit_code=0`, self-deleted (`VM_SHUTDOWN_ON_COMPLETION=true`). The `"coinbase"` cadence
      registration (`unified-api-contracts@ee7cb341`, already shipped by a sibling agent before this session started)
      was confirmed live in the tarball (`unified-api-contracts` tarball pin `882dabb6e2f1` — verified
      `git merge-base --is-ancestor ee7cb341 882dabb6e2f1` — the fix was genuinely in the code the VM ran, not a
      false-positive). COINBASE-FUTURES is now **DONE** — its tiny real scope (40 shards, one real day) makes this
      the one venue in this todo's scope that reached full completion this session.

      **EXTENDED-STARKNET: BLOCKED, not launched this session — real repo state checked, not assumed.** A new
      launcher (`launch-cefi-extended-starknet-funding-timestamp-vm.sh`, shipped `deployment-service@0545f414`) was
      built for `add_extended_starknet_derivative_ticker_funding_timestamp_2026_07_28.py` (the schema-ADD script,
      distinct from the bulk-shift script — see Finding 5), but **`market-tick-data-service` currently has an
      UNRESOLVED MERGE CONFLICT** (`UU tests/unit/scripts/test_reprocess_bulk_tardis_derivative_ticker_funding_
      timestamp_2026_07_28.py`, no `MERGE_HEAD` — an interrupted rebase/cherry-pick, not a live `git merge`) and the
      add-script itself is **UNTRACKED** (`git ls-files` returns nothing for it) alongside 30+ other modified files —
      almost certainly the real remains of the sibling EXTENDED-STARKNET task's crashed session (matching this
      task's own briefing that a prior attempt died to a usage-limit crash, just attached to a different repo/step
      than the briefing implied). This is NOT this session's WIP and was NOT touched or resolved (never blind-resolve
      an unmerged path or force-commit someone else's in-flight conflict) — it blocks the EXTENDED-STARKNET VM launch
      until whoever owns that WIP resolves the conflict and commits/pushes the add-script + its cadence registration
      is confirmed present in a real tarball. The launcher is ready to fire the moment that lands:
      `bash launch-cefi-extended-starknet-funding-timestamp-vm.sh batch_extended 2025-07-18 2026-07-28` +
      `bash launch-cefi-extended-starknet-funding-timestamp-vm.sh batch_tardis 2026-01-14 2026-07-28`.

      **Side-fix shipped while building the new launcher**: `canonical-migration-cefi-` VM names resolve, via the
      shared relaunch registry (`launcher_registry.LAUNCHER_FOR_VM_PREFIX` / `vm_prefix_registry.
      VM_PREFIX_TO_BUCKET`), to the GENERIC `launch-canonical-migration-vm.sh` on a SPOT-preemption auto-relaunch —
      wrong for these two dedicated launchers (incompatible category/dry-full positional CLI). Registered two more
      specific prefixes (`canonical-migration-cefi-fts-` / `-fts-ext-`, longest-prefix-match wins) so a preempted VM
      relaunches via its own correct launcher. All `test_launcher_registry.py`/`test_validate_vm_prefix_mapping.py`/
      `test_vm_zombie_watchdog.py` guard tests + full `quality-gates.sh` verified green before shipping.

      **DEFERRED — not this task's scope, flagged for follow-up**: (1) at ~1-4 objects/sec single-threaded per the
      script's own design, BINANCE-FUTURES (273,703 shards) / OKX-SWAP (194,041) / KRAKEN-FUTURES (142,821) / BYBIT
      (139,331) / BITGET-FUTURES (117,185) each project into the tens-of-hours range on a single un-sharded VM —
      exceeds the `vm-launcher-runbook.md` "Parallelization Threshold" few-hours guideline; the existing launcher has
      no per-venue date-range sharding (one VM per venue, whole range). Filed as its own real follow-up issue:
      `plans/archive/issues/cefi_migration_vm_launcher_no_sharding_and_spot_preemption_churn_2026_07_28.md`
      (RESOLVED 2026-07-30 — sharding + preemption-recovery both shipped and live-verified) (`SHARD_DAYS`-
      style sharding mirrors `launch-cefi-hl-aster-historical-backfill.sh`'s pattern). (2) A `RUN_LEDGER_RECORDED
      publish failed: 403 IAM_PERMISSION_DENIED (pubsub.topics.publish on
      projects/central-element-323112/topics/run-ledger)` warning fired on the COINBASE-FUTURES VM's shutdown (did
      NOT affect `exit_code=0` or the real data fix) — the currently-active gcloud identity in this workspace
      (`1060025368044-compute@developer.gserviceaccount.com`) itself lacks `pubsub.topics.getIamPolicy` to even
      inspect/self-grant this, so it needs an identity with real IAM-admin on this project, not a worker self-service
      grant from this session.

      **SHARDED + RECOVERED 2026-07-28/29 (autonomous session, real GCE state independently verified).** Manually
      applied the date-range-split workaround the follow-up issue above documents: for each of the 6 running venues,
      computed the midpoint between its live `PROGRESS.json` checkpoint and its end date, and launched a second
      `<VENUE> <midpoint> <end>` VM (independent GCS prefixes, safe concurrently per the launcher's own header) —
      roughly halving each venue's remaining wall-clock time. **Real SPOT preemption churn hit hard**: 5 of the 11
      VMs live at that point (2 originals — BITGET-FUTURES, BITFINEX-FUTURES — + 3 of the new shards — KRAKEN-FUTURES,
      BITGET-FUTURES, BITFINEX-FUTURES) were preempted + auto-deleted (`compute.instances.preempted` confirmed via
      `gcloud compute operations list`) within about 2 hours — one-off migration VMs are NOT wired into the fleet
      monitor (no auto-relaunch), so this required manual detection + recovery. For each, fetched its last
      `PROGRESS.json` (survives VM deletion — it's a GCS object) and relaunched with that measured date as the new
      `START_DATE` (never replayed the original `START_DATE`, per the standing HARD RULE) — 3 of 5 relaunches landed
      as new VMs; 2 hit a same-second VM-name collision with a sibling relaunch covering an overlapping/wider range
      and correctly no-op'd (`already exists`, no wasted duplicate). **Live fleet as of this update: 10 VMs across
      the 6 venues** (5 originals + 3 recovered-preempted + 2 still-alive shards from the first round —
      BINANCE-FUTURES and BYBIT and OKX-SWAP's original shard-2 VMs never got preempted), all confirmed `RUNNING`
      with monotonically-advancing checkpoints. Tarballs re-verified fresh for `market-tick-data-service` (pinned to
      `213bda480e57`, includes the Extended-Starknet fix below) at every (re)launch; `unified-api-contracts`/
      `unified-trading-library`/`deployment-service` tarballs drifted stale mid-session (other concurrent agents
      shipping unrelated work) but the specific content these VMs' job depends on (the reprocess script + the
      `perp_funding_cadence` module) was already baked into the pinned tarball SHA each time — confirmed non-blocking
      for this job's correctness, not just assumed.

      **ALL 6 VENUES CONFIRMED FULLY COMPLETE 2026-07-29/30** (real `DEPLOYMENT_COMPLETED` + full target-range
      verification via `run.log`/`PROGRESS.json`, not assumed from VM presence alone — several rounds of further
      SPOT preemption hit during the remaining run and were each recovered from measured checkpoint, never replaying
      the original `START_DATE`): `BITGET-FUTURES`, `KRAKEN-FUTURES`, `OKX-SWAP`, and `BYBIT` (both shards) each
      reached `exit_code=0`/`DEPLOYMENT_COMPLETED` and self-deleted. `BINANCE-FUTURES` (the largest scope, split
      across 3 date-range shards after repeated preemption) reached full completion on its final shard
      (`2025-04-25..2025-09-16`, 36,262 objects processed, `exit_code=0`) — one shard along the way genuinely finished
      its real correction work (`SUMMARY (APPLIED)`, 13,161 objects) but then hung in its OWN VM-shutdown sequence for
      3+ hours (heartbeat alive, zero real progress) before being noticed and the stuck VM manually deleted; the data
      correction itself was already verified complete and persisted, so no data was at risk — see the stall-watchdog
      fix below. `BITFINEX-FUTURES` completed earlier the same session. This todo's real target (~926,898 shards /
      ~75.0B rows across all 6 venues) is now fully corrected in production.

- [x] ✅ [OPERATOR] P2. **DECIDED 2026-07-28 (autonomous session, operator directive + independent confirmation): Option
      A — leave `funding_timestamp`/`next_funding_timestamp` permanently NULL for DERIBIT.** No code change needed (the
      shipped script's `skipped_all_null_no_forward_value` classification already does this). This is now provably
      LOW-STAKES either way, not just the least-bad option: the operator separately asked "so that we only account for
      funding rate over the time we have the position weighted by the funding rate average over that time vs others
      where we get the funding discretely... check existing plans... implement it" — a full investigation of the
      PnL/accrual layer (not the raw-column layer this todo is about) found that
      `CanonicalDerivativeTickerFundingProvider.day_funding_fraction` (the shared, live-wired funding-leg mechanism)
      already computes a per-day TICK-LEVEL MEAN of the captured `funding_rate` column — mathematically correct for BOTH
      Deribit's continuous accrual AND every discrete venue's accrual at the day-granularity the paper/batch spine uses,
      with ZERO dependency on `funding_timestamp` being populated at all. So Option A's "permanent NULL" never blocks
      correct PnL. Formalized as `unified_api_contracts.registry.perp_funding_cadence.FundingAccrualModel` (`DISCRETE` /
      `CONTINUOUS_TIME_WEIGHTED`, DERIBIT the sole `CONTINUOUS_TIME_WEIGHTED` venue) — shipped
      `unified-api-contracts@c7d2b9ab` (classification + registry + tests) and `strategy-service@1b980d2c`
      (`test_deribit_continuous_vs_discrete_funding_accrual.py`: golden-math, cross-venue formula-identity,
      gap-handling, end-to-end PnL, and paper==batch ε=0 determinism, all against real fluctuating synthetic series —
      proves no venue-conditional branch exists or is needed). Codex documented:
      `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` § "Funding Accrual Model". Options B/C below
      are no longer live candidates — kept for the historical record of what was considered.

      **Original investigation (2026-07-28) — from-scratch raw-column derivation, investigated and STOPPED (not
      built)** because Deribit has no discrete funding-charge instant to derive (its own ticker/funding-rate-history
      APIs show a continuously-evolving rate with no reset pattern at 00:00/08:00/16:00 UTC or any other boundary;
      unlike Binance/Bybit/OKX, Deribit's own API never exposes a next-funding-time field for Tardis to relay). Three
      options, needs an operator decision (not a worker-determinable outcome):

      A: **[WORKER REC] Leave `funding_timestamp`/`next_funding_timestamp` NULL for DERIBIT permanently** (status quo —
      the shipped script's `skipped_all_null_no_forward_value` classification already does this correctly). Honest
      absence for a venue that genuinely has no discrete charge instant; zero risk of false precision.
      B: Populate DERIBIT `funding_timestamp`/`next_funding_timestamp` using the same UTC 00:00/08:00/16:00 8h grid as
      every other 8h-cadence venue, but EXPLICITLY documented (docstring + a distinct `source`/provenance marker, not
      silently identical semantics to Binance/Bybit) as a **reporting-bucket convention** — "which 8h window this rate
      figure is reported against" — not a literal charge-instant claim, matching how the stored `funding_rate` is
      already treated as an "8h figure" by convention (`perp_funding_cadence.py`) even though the real mechanism is
      continuous. Restores cross-venue joinability at the cost of a per-venue semantic asterisk that must be documented
      everywhere the field is consumed.
      C: Populate using DERIBIT's own REAL hourly refresh cadence (`get_funding_rate_history` genuinely returns a fresh
      row every hour, on the hour) instead of the 8h grid — this corresponds to an actual discrete update Deribit's API
      performs, but it is "last/next rate REFRESH", not "last/next CHARGE" — a still-different semantic from every
      other venue's `funding_timestamp`, so it carries the same documentation burden as option B without matching the
      registered 8h cadence.
      Other: operator can specify a different resolution.

      **Repo: market-tick-data-service** (the reprocessing script, if B/C chosen) **+ unified-api-contracts** (a
      `CanonicalDerivativeTicker.funding_timestamp` docstring caveat, if B/C chosen).

- [x] ✅ [DATA] P2. Add a historical funding-cadence tracker in GCS (canonical-from-docs or inferred from observed
      settlement frequency) so historical annualisation survives a venue cadence change. **Repo: unified-api-contracts +
      market-tick-data-service.** **DONE 2026-08-03** — the canonical/docs-sourced half
      (`FUNDING_CADENCE_HISTORY`/`cadence_seconds_as_of`) already shipped `unified-api-contracts@e8b45af4`. This todo's
      remaining GCS-persisted INFERRED half shipped `market-tick-data-service@fd9efc85`
      (`feat(perp-funding): add observed cadence-drift tracker (GCS-persisted)`; citation corrected 2026-08-03 by main
      agt-1756f6 from a wrong-SHA slip that cited `840c816d`, which is slot-10's later unrelated
      `fix(qg): re-measure STEP 5.95 type:ignore ratchet baseline` — the work itself is verified ON-LDR + good):
      `scripts/analysis/measure_perp_funding_cadence_drift.py` samples real captured `derivative_ticker` shards per
      (venue, day) via a prefix-scoped listing (never a whole-corpus walk), counts distinct settlement instants for
      DISCRETE-accrual venues (CONTINUOUS_TIME_WEIGHTED venues like DERIBIT are honestly skipped), and CAS
      read-modify-writes a `(venue, day)`-keyed JSON tracker to
      `_index/perp_funding_cadence_drift/observed_cadence_history.json` in the cefi market-data bucket — flagging
      `drift_detected` whenever the observed cadence disagrees with `cadence_seconds_as_of`. 19 unit tests,
      `quality-gates.sh` green (482s, sentinel `fd9efc85`).
- [x] ✅ [DATA] P2. **Backfill Aster perp funding into GCS — DONE, this todo named a stale launcher (2026-08-03
      verification).** This todo's own named command (`launch-mtds-perp-funding-backfill-vm.sh --perp-protocols aster`)
      targets the RETIRED `perp_funding_handler.py` path (Aster/Lighter standalone `perp_funding` retired 2026-07-08 —
      see `aster_perp_funding_backfill_stale_launcher_and_genesis_conflict_2026_07_28.md` finding 1 for the full
      mechanical detail); running it as written would hit an unknown-protocol branch and write false `attempted_failed`
      rows, not a real backfill. The REAL launcher
      (`deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`,
      `VM_OPERATION=collect-onchain-perp-batch`) **has already been run** — its own header cites "real gap
      2023-07-22→2023-10-31 found + backfilled 2026-07-29" — and this was independently verified live against the
      availability manifest this session (`market-data-tick-cefi-central-element-323112`): `derivative_ticker` rows for
      ASTER across 2023-07-22→2023-07-26 show `capture_status=captured`, `source=aster`, `pipeline_mode=batch_aster`,
      `row_count=3` (real settlement data, not a placeholder). So "the backfill VM was never run for Aster" is no longer
      true. **Two follow-ups spawned, tracked separately, not blocking this checkbox**: (1) the disputed exact genesis
      sub-window (2023-07-22 vs 2023-11-01 vs 2024-01-01) is a pre-existing, already-open, operator-gated question — see
      `aster_perp_funding_backfill_stale_launcher_and_genesis_conflict_2026_07_28.md`, unaffected by this flip; (2)
      while verifying this, found the FORWARD/daily capture for ASTER (+ LIGHTER-ZKSYNC + EXTENDED-STARKNET) had gone
      silently dark since 2026-07-28/29 (no cron ever wired + a 2026-08-01 launcher regression blocked manual recovery)
      — root-caused, launcher regression fixed (`deployment-service@52f02a4`), remediation VMs launched — full detail +
      remaining todos in `cefi_onchain_perp_forward_capture_outage_2026_08_03.md`.
- [x] ✅ [DATA] P2. **Genesis is PER-(venue, data_type), not per-venue — encoded. VERIFIED 2026-08-03** directly against
      `market-tick-data-service/configs/expected_start_dates.yaml` `CEFI.data_type_start_dates.ASTER`:
      `trades: 2023-07-22`, `derivative_ticker: 2023-07-22`, `book_snapshot_5: null` (honest live-capture-only
      absence), `liquidations: 2024-10-01` — four distinct per-data_type genesis values, not one per-venue value. Every
      canonization leg below this todo's own body is done or correctly N/A per its own inline sub-header
      (derivative_ticker + trades ✅ DONE 2026-06-17; OHLCV/klines correctly NOT wired per operator principle 2026-06-17
      — CeFi derives candles from `trades`, only a trades-less venue gets direct `ohlcv_*`; book_snapshot_5 batch
      honest-absence already correct, confirmed by the `null` genesis above). The one genuinely remaining piece — a live
      Aster `book_snapshot_5` WS connector — was never silently dropped: it is its own separately tracked P3 todo below
      ("Aster live `book_snapshot_5` WS connector"), unaffected by this flip. Aster API availability (verified
      2026-06-16): funding **2023-07-22** (operator-confirmed genesis 2026-06-17 — pre-2024 is BINANCE-PROXIED Astherus
      pre-rebrand funding, imported not native → label source honestly), OHLCV/klines **2023-01-01** (the
      `venue_launch_dates` ASTER floor is now 2023-07-22 per GAP 2 — reconciled), mark/index via klines/premiumIndex,
      trades partial (id/time-paginated), **open_interest + L2 book = live-capture-only (no historical endpoint →
      forward-only)**. Canonize the Aster native API INTO the Tardis CEX benchmark schemas (klines→OHLCV,
      aggTrades→`trades`, premiumIndex+funding+OI→`derivative_ticker`, depth-WS→`book_snapshot_5`) so downstream can't
      tell it's not Tardis; record genesis per data_type with `captured`/`expected_unattempted` honest-absence for the
      forward-only ones. **Repo: market-tick-data-service + unified-api-contracts.**

      **— derivative_ticker + genesis leg ✅ DONE 2026-06-17 (operator "fully hook up"): `uac@61d5838` (BATCH_ASTER/
      LIVE_ASTER/REPLAY_ASTER members + aster capability + `(cefi,derivative_ticker)` source priority),
      `utl@3b4bd6b8` (`ASTER→BATCH_ASTER` venue override = self-archive source `aster`, not Tardis), `mtds@5978627`
      (`venue_data_types` += `derivative_ticker`; `_perp_funding_hl_aster._write_aster_derivative_ticker` emits
      `CanonicalDerivativeTicker` at `asset_group=cefi`, source-aware `batch_aster`/`live_aster`, shard-isolated from
      the funding leg; genesis per-(venue,data_type) in `expected_start_dates.yaml`).**

      **— trades leg ✅ DONE 2026-06-17 (operator "yeah wire it"): `mtds@889b131` — `_perp_funding_hl_aster._write_aster_trades`
      fetches `/fapi/v1/aggTrades` (paginated by `fromId`, day-windowed) per symbol, maps onto
      `AsterTrade`→`normalize_aster_trade`→`CanonicalTrade`, writes `data_type=trades` at `asset_group=cefi`,
      `source=aster`, source-aware `batch_aster`/`live_aster`, shard-isolated from the funding leg (Live=Batch, one
      run). `trades` is in the cefi `_LEGAL_DATA_TYPES` + Aster `venue_data_types.yaml`; genesis `2021-08-30` already
      in `expected_start_dates.yaml`. NO UTL change (the `ASTER→BATCH_ASTER` override is data_type-independent). Unit
      test `test_writes_canonical_trades_shard_cefi` asserts the cefi shard path + `m`→buy/sell mapping. NB the
      trades write rides `_collect_aster` (funding-genesis-gated) → it covers the **2023-07-22-forward** window; the
      pre-funding-genesis trades window (2021-08-30→2023-07-22) needs a standalone trades collect (todo below).
      `fetch_klines`+`fetch_depth` adapter scaffolds also landed (one-step-from-ready for the OHLCV+book write legs).**

      **— OHLCV/klines leg: DESIGN DECISION 2026-06-17 — `ohlcv_*` is NOT canonized into the cefi tick-data write
      (intentional, documented).** `ohlcv_1m`/`ohlcv_15m`/`ohlcv_24h` are registered in UAC
      (`market_data_categories.py`/`schema_spec.py`) but are a **TradFi-only** data_type: NOT in the cefi
      `_LEGAL_DATA_TYPES` (`tardis_shared.py:73` — the cefi path builder hard-rejects it), NOT in ANY cefi venue's
      `venue_data_types.yaml`, NOT in cefi `SOURCE_PRIORITY`, with NO cefi consumer (MDPS consumes
      `CanonicalOhlcvBar` for TradFi only; CeFi strategies derive candles from `trades`). The two reference CeFi
      venues (BINANCE-FUTURES/BYBIT) deliberately omit ohlcv. Introducing an orphaned cefi `ohlcv_*` would create
      dead surface + false expected-absent rows — the exact anti-pattern the Aster `venue_data_types.yaml` comment
      warns against. The `fetch_klines` adapter fetch + `normalize_aster_kline` transform ARE ready; see the tight
      remaining todo below for the exact one-step write if a cefi ohlcv consumer is ever wired.

      **— book/`book_snapshot_5` leg: batch honest-absence ALREADY CORRECT (no change needed); live WS connector is
      the tight remaining unit.** Aster book is `L2_MBP`→`book_snapshot_5` (NOT tbbo); `/fapi/v1/depth` is a live
      snapshot only (Binance-compatible, no historical depth) → batch is forward-only honest-absent, already encoded
      (`expected_start_dates.yaml` ASTER `book_snapshot_5: null` + absent from Aster's batch `data_types` → no false
      expected-absent). A live Aster **trades** WS connector exists (`live/connectors/aster_ws.py`); a live **book**
      WS connector does not yet. `fetch_depth` scaffold landed. See the tight live-book todo below. **Repo:
      market-tick-data-service + unified-api-contracts.**

- [x] ✅ [DATA] P3. Aster **pre-funding-genesis trades window** (2021-08-30 → 2023-07-22): **N/A — GAP 4 eliminated this
      window (2026-08-05 verification).** GAP 4 (resolved 2026-07-21, slot-3, `market-tick-data-service@d8efc6d6`)
      clipped the ASTER trades genesis from 2021-08-30 to 2023-07-22 across all 3 `expected_start_dates.yaml`
      locations + UAC `market_data_categories.py`, matching the funding genesis. The 2021-08-30→2023-07-22 window is
      Binance-proxied / pre-venue-launch, not native ASTER coverage. The current trades write path
      (`onchain_perp_batch_handler._fetch_aster` → `AsterAdapter.fetch_trades`) is correctly gated at 2023-07-22 via
      UAC's `get_venue_data_type_start_date()` — no standalone pre-funding-genesis collect is needed because there is no
      native ASTER trades window before 2023-07-22 to backfill. Verified 2026-08-05: all 3 YAML locations + UAC +
      handler gate all read `2023-07-22`. **No code shipped — pure verification + checkbox flip.**
- [x] ✅ [DATA] P3. **Aster OHLCV→cefi write = N/A (resolved by operator principle 2026-06-17).** OPERATOR PRINCIPLE:
      OHLCV (open/high/low/close/volume) is a first-class `data_type` for **TradFi**; on **CeFi** we store `ohlcv_*`
      directly **ONLY for a TRADES-LESS venue** (where OHLCV is the only data the source provides). **When a venue has
      `trades` — as Aster does — we DERIVE candles from `trades` and do NOT store cefi `ohlcv_*`.**

      So the Aster OHLCV leg is correctly not wired: Aster's candles come from its (now-canonicalized)
      `trades`. The `fetch_klines` + `normalize_aster_kline` scaffolds stay available (cross-check use), but
      no `_write_aster_ohlcv` is added for Aster.

- [x] ✅ [DATA] P3. **Latent capability: cefi `ohlcv_*` direct-write for a TRADES-LESS cefi venue** (NOT Aster). Today
      the cefi path builder hard-rejects `ohlcv_*` (`tardis_shared.py:73`), so a future OHLCV-only cefi venue (no trades
      endpoint) could not be wired. IF/WHEN such a venue is onboarded: relax the cefi `_LEGAL_DATA_TYPES` to admit
      `ohlcv_*`, add it to that venue's `venue_data_types.yaml` + cefi `SOURCE_PRIORITY` + genesis, and write
      `CanonicalOhlcvBar` directly (mirror `_write_aster_trades`). Until then it stays a latent capability — wiring it
      now (with every current cefi venue having trades) would be dead surface. **Repo: market-tick-data-service +
      unified-api-contracts.** — market-tick-data-service@497918c2
- [x] ✅ [DATA] P3. Aster **live `book_snapshot_5` WS connector** (forward-only; batch is correctly honest-absent
      already): add a live Aster depth-WS/poll book connector mirroring `live/connectors/aster_ws.py` (the existing live
      trades connector) → parse depth into the 5-level `bid_px_0X`/`bid_sz_0X`/`ask_px_0X`/`ask_sz_0X` shape
      (`normalize_aster_orderbook`), write via `MTDSShardManifestRecorder.record_captured` at
      `data_type=book_snapshot_5`, `pipeline_mode=live_aster`, `source=aster`; register via
      `register_ws_feed_connector(venue="ASTER", …)`. `AsterAdapter.fetch_depth` (`/fapi/v1/depth` snapshot) is the REST
      fallback building block. **Repo: market-tick-data-service.** — market-tick-data-service@497918c2
- [x] ✅ [DATA] P3. Aster margining model (`venue_collateral.py`): USDC (0% haircut, CROSS) / USDT (1%) only — rejects
      spot-coin AND LST collateral. So Aster supports a stablecoin-margined funding-short ONLY (no same-venue
      cash-and-carry, no staking leg). Re-verify against live Aster docs before sizing; the ETH staked-basis needs
      Bybit/OKX/Deribit (stETH/wstETH cross-margin). **Repo: unified-api-contracts (registry verification).** —
      unified-api-contracts@75245222 (verified 2026-08-05: live docs.asterdex.com Multi-Asset Mode confirms USDC/USDT
      99.99%, BTC/ETH 95%, no LSTs — matches registry updated 2026-07-29 per archived issue
      aster_margining_registry_live_docs_drift_2026_07_28.md)
- [x] ✅ [DATA] P1. **NEW 2026-08-04 — CEX-Tardis `derivative_ticker` forward capture has been dark since 2026-05-01/22
      for every venue in this doc's own census (line ~273), NOT just a stale historical range as that census's framing
      implied.** Live bounded `gsutil ls` prefix probes (2026-08-04, single-date single-venue, not a corpus walk)
      confirm ZERO `derivative_ticker` objects for `BINANCE-FUTURES`/`BYBIT`/`OKX-SWAP`/`OKX-FUTURES`/
      `KRAKEN-FUTURES`/`BITGET-FUTURES`/`BITFINEX-FUTURES`/`DERIBIT` on 2026-05-25, 2026-06-15, 2026-07-01, 2026-07-15,
      2026-08-01, 2026-08-03 — matching this doc's own captured-range cutoffs exactly (2026-05-22 for
      BINANCE-FUTURES/OKX-SWAP/KRAKEN-FUTURES/BITGET-FUTURES, 2026-05-01 for BYBIT/DERIBIT). This is the SAME
      silent-forward-capture-outage pattern as
      `/plans/archive/2026_08/issues/cefi_onchain_perp_forward_capture_outage_2026_08_03.md` (no cron ever wired for
      `launch-cefi-forward-poll.sh` per this doc's own line ~313-314 finding — "NOT on an automatic Cloud Scheduler cron
      for CeFi"), but for the CEX/Tardis venues rather than the onchain-perp native sources that doc covers — a
      DIFFERENT launcher/venue population, not yet remediated. **This directly starves a live strategy path**:
      `features-service/features_service/cefi/calculators/perp_funding_corpus.py` computes
      `perp_funding`/`perp_daily_ctx` FROM this exact `derivative_ticker` corpus and writes into the shared DeFi bucket,
      which `strategy_service/engine/core/canonical_perp_funding_provider.py` (the live
      CARRY_BASIS_PERP/CARRY_FUNDING_DISPERSION reader, `strategy_service/cli/handlers/paper_run_handler.py:1987-1988`)
      reads for exactly the 6 `catalog_carry.py`-configured venues — confirmed the DeFi-bucket copy ALSO stops dead on
      2026-05-22 (verified via bounded probe), so the live strategy path has been reading a frozen funding corpus (zero
      new rows) for 2+ months as of 2026-08-04. **Fix**: apply the same remediation
      `cefi_onchain_perp_forward_capture_outage_2026_08_03.md` used for the onchain-perp venues (Cloud-Scheduler-cron
      wiring for the Tardis CEX-venue launcher, mirroring its `[x]` P1 todo 1) to this launcher/venue population; then
      re-verify `CanonicalPerpFundingProvider`'s live read resumes. **Repo: deployment-service** (cron wiring) **+
      market-tick-data-service** (verify `launch-cefi-forward-poll.sh` resumes real captures once cron-triggered).
      Found + filed from `/plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s P2(b) repoint
      investigation (2026-08-04) — see that doc's Progress Log for the cross-reference.

      **RESOLVED 2026-08-04 (slot-6).** Premise was wrong: `launch-cefi-fwd-daily-cron-vm.sh` +
      `cefi-fwd-daily-cron-` registry entries have existed since 2026-05-20 — cron wiring was NOT missing. Real root
      cause: the cron HOST had never been launched even once (zero prior GCE operations for that prefix) until this
      session launched it, and once running its own name collided with the daily worker's singleton-lock filter
      (`name~"^cefi-fwd-"` also matches `cefi-fwd-daily-cron-*`), so the host would have refused every one of its own
      daily fires forever, silently. Fixed: `deployment-service@fa794a1` anchors the filter on the RUN_TS digit
      (same bug + same fix applied to the TradFi twin, `launch-tradfi-forward-poll.sh`); 2 new regression tests.
      Verified live: `launch-cefi-forward-poll.sh` refused pre-fix (blocked by the running cron host), launched
      cleanly post-fix (`cefi-fwd-20260804-014020`) — real `derivative_ticker` rows confirmed resuming (280 shards
      for COINBASE-FUTURES within 15 min; BYBIT/OKX-SWAP/BINANCE-DELIVERY also active as the run continues).
      **Scope note**: this closes the FORWARD gap only. The 2026-05-22→2026-08-02 historical hole is a separate,
      much larger backfill — filed as `/plans/archive/issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04.md`.

## Progress Log — Aster canonicalization remaining legs (2026-06-17, autonomous)

Continuing the line-111 "canonize Aster native API INTO the Tardis CEX schemas" todo. derivative_ticker leg already
landed (uac@61d5838 / utl@3b4bd6b8 / mtds@5978627). This session drives the remaining trades / ohlcv / book legs.

**Verified system reality (read, not assumed):**

- `trades` IS in the cefi tick-data `_LEGAL_DATA_TYPES` (`tardis_shared.py:73`), IS in Aster's `venue_data_types.yaml`
  list, genesis already set (`expected_start_dates.yaml` ASTER `trades: 2021-08-30`). UTL
  `_VENUE_OVERRIDES["ASTER"] = BATCH_ASTER` is data_type-independent → trades resolves source-aware
  `batch_aster`/`live_aster` with NO UTL change. **BUT** no canonical-cefi trades WRITE path exists today (neither Aster
  NOR Hyperliquid — both declared, neither written; the perp_funding handler only writes
  `perp_funding`+`derivative_ticker`). The transform `normalize_aster_trade(AsterTrade)` exists in UAC; aggTrades
  returns the `AsterAggTrade` shape (p/q/T/m).
- `ohlcv_*` (`ohlcv_1m`/`ohlcv_15m`/`ohlcv_24h`) is **NOT** in the cefi `_LEGAL_DATA_TYPES`, **NOT** in ANY cefi venue's
  `venue_data_types.yaml`, **NOT** in cefi `SOURCE_PRIORITY`, and has **NO cefi consumer** — it is a **TradFi-only**
  data_type (CME/CBOE via Databento/Barchart; MDPS consumes `CanonicalOhlcvBar` for TradFi only). The two reference CeFi
  venues (BINANCE-FUTURES / BYBIT) do **NOT** wire ohlcv at all — CeFi strategies derive candles from `trades`. The UAC
  transform `normalize_aster_kline(AsterKline)` exists.
- Aster `book` is `book_type: L2_MBP` → canonical type is **`book_snapshot_5`** (NOT tbbo — tbbo is the TradFi L1 top of
  book). `/fapi/v1/depth` is a **live snapshot only** (Binance-Futures-compatible, no historical depth endpoint).
  `expected_start_dates.yaml` ASTER `book_snapshot_5: null` + the `venue_data_types.yaml` comment already encode the
  forward-only / live-capture-only honest absence (NOT listed in Aster's batch `data_types` → no false expected-absent
  rows). A live Aster **trades** WS connector exists (`live/connectors/aster_ws.py`); NO live book/depth connector yet.

**Design decisions (AUTONOMOUS rule 1 — least-bad path consistent with the documented intent AND the system as wired):**

1. **trades → WIRE FULLY** (in scope, legal, genesis-ready). Mirror `_write_aster_derivative_ticker`: a best-effort,
   shard-isolated `_write_aster_trades` called from `_collect_aster` (Live=Batch single pass), fetching aggTrades per
   symbol for the day, `normalize_aster_trade`→`CanonicalTrade`, written to `data_type=trades` at `asset_group=cefi`,
   `source=aster`, source-aware `batch_aster`/`live_aster`. + per-(venue,data_type,source) manifest row.
2. **ohlcv → DO NOT introduce an orphaned cefi `ohlcv_*` data_type; leave a tight todo.** Wiring a brand-new cefi
   data_type that no cefi venue carries, that `_LEGAL_DATA_TYPES` rejects, that has zero consumer, and that the two
   reference CeFi venues deliberately omit, is the exact anti-pattern (false expected-absent + dead surface). The
   mission authorizes "if disproportionate, leave a tight todo." Adapter scaffold (`fetch_klines`) IS added so the data
   path is one method from ready; the canonical write is the tight remaining step (below). Klines genesis 2023-01-01
   captured in the todo.
3. **book → batch honest-absence is ALREADY correct (live-capture-only); live WS book connector is a tight todo.** No
   batch change needed (already `null` genesis + absent from batch `data_types`). The live depth-WS connector is a
   separate live-infra unit (a new `aster_book_ws` connector + live-manifest wiring) — tight todo below.

## Progress Log — Aster backfill-to-canonical VERIFIED (2026-06-17, verification session)

Operator asked to confirm the Aster e2e funding→canonical fetch works + that the production wiring produces REAL
canonical Aster data at G5. **Verdict: VERIFIED — e2e + production share the same endpoint + the same UAC normalizer;
production is ready to produce real canonical Aster data.** Three findings/gaps below.

**e2e ↔ production parity (CONFIRMED):**

- e2e harness `e2e-testing/scripts/defi/staked_basis_funding_scan.py::_fetch_aster_funding` pulls
  `https://fapi.asterdex.com/fapi/v1/fundingRate?symbol=…` (paginated, no-auth, 8h cadence) →
  `{day: mean per-cycle rate}`. It does NOT canonicalize — it builds an in-memory `FundingPoint` for the carry-rank
  snapshot only.
- Production `_perp_funding_hl_aster._fetch_aster_funding` hits the **SAME** `{ASTER_API_URL}/fapi/v1/fundingRate`
  endpoint, then `_write_aster_derivative_ticker` maps each settlement record `fundingRate`/`markPrice`/`fundingTime` →
  `AsterMarkPrice`+`AsterFundingRate` → `normalize_aster_derivative_ticker` → `CanonicalDerivativeTicker` →
  `data_type=derivative_ticker` at `asset_group=cefi`, `venue=ASTER`, `source=aster`, source-aware
  `batch_aster`/`live_aster`. Same raw API, same fields, same UAC normalizer — production produces the canonical shape
  the e2e harness's proven fetch reads.

**Test result (credential-free, mtds `.venv`):**
`pytest tests/unit/test_perp_funding_handler.py tests/unit/test_perp_funding_normalization.py -k aster` → **7 passed /
58s**. Covers `_collect_aster` → `_write_aster_derivative_ticker` + `_write_aster_trades` (mocked fetch), funding_rate
column presence, and Hyperliquid/Aster same-sign convention.

**Live API → canonical end-to-end (network, real fetch):** fetched 3 live `BTCUSDT` funding records + ran each through
`normalize_aster_derivative_ticker` → valid `CanonicalDerivativeTicker` (`instrument_key=ASTER:PERPETUAL:BTCUSDT`,
`venue=ASTER`, `funding_rate` preserved incl. negative sign, `funding_timestamp` set). Live `fundingTime` spacing 16:00
→ 00:00 → 08:00 UTC = **8h confirmed** → matches UAC `perp_funding_cadence["aster"] = 8*3600` and handler
`_LIVE_VENUE_INTERVAL_S["ASTER"]=28800`. Annualisation will be correct.

**GAP 1 — `mark_price` is NULL from this endpoint (P2, data-completeness).** The live `/fapi/v1/fundingRate` records
return `"markPrice": null` (verified live 2026-06-17). So `_write_aster_derivative_ticker` writes `mark_price=None` —
the derivative_ticker carries funding but NO mark. The carry strategy reads `funding_rate` (present) so this does not
block the funding leg, but if any consumer needs Aster mark on the derivative_ticker shard it must be sourced from
`/fapi/v1/premiumIndex` (Binance-Futures-compatible, carries `markPrice`). Handler docstring/comments assume `markPrice`
"rides the fundingRate record" — TRUE on Binance, but Aster returns null. **Todo (P2):** source mark from `premiumIndex`
in `_collect_aster` (or accept funding-only derivative_ticker for G5).

**GAP 2 — genesis date disagrees across 3 sources (P1) — ✅ RESOLVED 2026-06-17 (operator-confirmed `2023-07-22`).**
Was: handler `_ASTER_FUNDING_START_DATE = "2024-09-25"`; UAC `market_data_categories.py` Aster
`perp_funding: "2024-10-01"`; operator stated `2023-07-22`. The live API returns rows back to `2022-01-01T00:00:00Z`
(oldest queryable), but those very-early rows are a flat `0.00010000` placeholder (synthetic pre-launch backfill, not
real settlements). **Operator confirmed 2026-06-17: genesis = `2023-07-22`** (the Astherus pre-rebrand venue).
**IMPORTANT — pre-2024 Aster funding is BINANCE-PROXIED**: Astherus (pre-rebrand) mirrored Binance funding, so the
2023-07-22 → ~2024 window is _imported_ Binance funding, NOT Aster-native settlements. Label `source` honestly (it is
proxied, not native Aster) and treat the flat-`0.00010000` pre-2023-07-22 rows as pre-launch
(`EXPECTED_PRE_VENUE_LAUNCH`). Reconciled to ONE value across every source: handler
`_ASTER_FUNDING_START_DATE = "2023-07-22"`; UAC `market_data_categories.py` Aster trades/ derivative_ticker/perp_funding
`= "2023-07-22"`; UAC `venue_launch_dates.py` ASTER (CeFi + DeFi dicts) `= "2023-07-22"`; UAC `venue_mapping.py`
`venue_start_dates["ASTER"] = "2023-07-22"`; UAC `_cefi.py` Aster `coverage_start` all data_types `= 2023-07-22`; MTDS +
PM + deployment-service `expected_start_dates.yaml` ASTER `derivative_ticker = "2023-07-22"`; PM + deployment-service
`data-catalogue.market-tick-data-service.yaml` ASTER `start_date = "2023-07-22"`; IS `adapters/cefi/aster.py`
`_ASTER_LAUNCH_DATE` (reads `get_instrument_discovery_start` → now 2023-07-22). Shipped: mtds + unified-api-contracts +
instruments-service + unified-trading-pm (this issue's commit set).

**GAP 3 — Aster DATA absent in GCS by design (NOT a code gap).** The backfill VM is drain-gated at G5; no GCS data yet
is expected. The code path is verified-ready; running it at G5 will produce real canonical `derivative_ticker` (+
`trades`) shards. No code fix needed to start producing data — only the operator G5 drain-release + a backfill run.

**Bottom line:** the Aster e2e→canonical path is REAL and works; production matches it field-for-field via the shared
UAC normalizer; tests pass; live API→canonical proven end-to-end; cadence (8h) correct. Backfill is confirmed ready to
produce real canonical Aster funding data at G5. Two non-blocking gaps to resolve before/at backfill: (P2) mark_price
null → premiumIndex, (P1) reconcile the genesis date to a single operator-confirmed value.

**GAP 4 — the GAP-2 genesis sweep to 2023-07-22 never touched the `trades` entry in `expected_start_dates.yaml`; it now
disagrees with UAC (P1, data-correctness) — found 2026-07-07 during an unrelated ASTER/CEFI audit.**
`market-tick-data-service/configs/expected_start_dates.yaml` still carries `ASTER: "2021-08-30"` for `trades` in three
places (the instruments-service CEFI block, the MTDS CEFI venues block, and the `data_type_start_dates` block),
annotated in its own comment as _"earliest aggTrades observed (BTCUSDT); trades-only; pre-launch data may be
proxy/aggregated."_ GAP 2's resolution (above) swept UAC's `market_data_categories.py` `trades` / `derivative_ticker` /
`perp_funding` for ASTER all to `2023-07-22`, and named `expected_start_dates.yaml`'s `derivative_ticker` entry
specifically as one of the files it touched — but never mentions `trades`, and the `trades` entry in that same file was
left at `2021-08-30`. This was a deliberate carve-out, not solely an oversight: line 151-156 above already plans a
standalone backfill of exactly this 2021-08-30→2023-07-22 window, under the (currently unstated) assumption that
2021-08-30 is a usable trades floor.

Recommendation: **2023-07-22 should win for any coverage %, missing-days, or backfill-target calculation** — the same
logic already applied to funding (a confirmed flat placeholder before real launch) likely applies to trades too, and
this file's own `aggTrades` endpoint has only ~30-day rolling depth, meaning whatever produced the 2021-08-30
observation came from a different (archival/vendor) source than the live Astherus-native path — it is not native ASTER
liquidity in the sense a coverage panel implies. The 2021-08-30 bytes are legitimate to keep archived, but only with an
honest `source=` label (proxied/pre-launch), consistent with the "label source honestly" directive already applied to
the funding leg — never counted as native ASTER coverage. Because this file's own header states it is "used to
accurately calculate completion percentages," the current `trades: 2021-08-30` entry is live-risk, not just stale
documentation: anything reading it today would treat the ~23-month gap as expected-and-missing ASTER trades days,
contradicting `venue_launch_dates.py`'s `EXPECTED_PRE_VENUE_LAUNCH` clipping for the exact same venue and window.

- [x] ✅ [DATA] P1. Reconcile `expected_start_dates.yaml`'s `trades: 2021-08-30` entries for ASTER (all 3 locations)
      against UAC's swept `2023-07-22` — either move the floor to 2023-07-22 to match, or, if the pre-2023-07-22 bytes
      are kept, add an explicit `source=` / proxy annotation so no coverage calculation treats that window as honest
      native ASTER trades coverage. **Do this before executing the pre-funding-genesis trades backfill todo above**, or
      the backfill will write real archived bytes labeled as native ASTER coverage for a period before the venue is
      confirmed to have existed. **Repo: market-tick-data-service + unified-api-contracts.** — **Already done 2026-07-21
      (slot-3), checkbox never flipped.** Found 2026-07-29 (slot 14): all 3 `expected_start_dates.yaml` locations
      (instruments-service CEFI block L59, MTDS CEFI venues block L143, `data_type_start_dates` block L162) already read
      `ASTER trades: "2023-07-22"` with explicit `GAP-4 clip from 2021-08-30 ... Binance-proxied` comments — option 1
      (move the floor to match UAC) was chosen, not the annotation carve-out. Verified via `git blame`:
      `market-tick-data-service@d8efc6d6` ("fix(config): clip ASTER trades genesis to native 2023-07-22 (GAP-4)",
      2026-07-21T19:53:59+0100) touched all 3 lines. No code change needed this touch — pure checkbox false-progress
      fix.

### Finding 5 — EXTENDED-STARKNET `funding_timestamp`: mechanism REVERSE-ENGINEERED with real confidence (both cadence AND anchor); derivation built, registered, and sample-validated on real production data (2026-07-28)

Operator ask (verbatim): "sme for exetedned starknet if we can reverse engineer mechanism" — same treatment as the
DERIBIT investigation above (Finding 4), conditional on reaching REAL confidence, not a guess. **Verdict: YES,
reverse-engineered with confidence, mechanism built, shipped, and sample-validated on real production data — this is a
genuinely different case from DERIBIT, not a repeat of it.**

**Why EXTENDED-STARKNET is a different case from every other venue this issue covers (investigated before assuming
anything):** its canonical `derivative_ticker` schema is candle-shaped
(`open`/`high`/`low`/`close`/`volume`/`funding_rate` all present, OHLC always null on funding rows) — this is NOT
because Extended's funding is candle-derived; it's a harmless artifact of `_umi_extended.fetch_extended_rest`'s
`pd.concat(all_frames, ...)` unioning the separate per-data_type DataFrames (candles + funding + trades) into one wide
frame before `PartitionedTickWriter` splits it back out by `data_type` partition — confirmed live by inspecting the
actual write path (`market_tick_data_service/adapters/_umi_extended.py`,
`market_tick_data_service/cli/handlers/_onchain_perp_batch_umi.py`). More importantly: `funding_timestamp`/
`next_funding_timestamp` never existed as COLUMNS at all for this venue (a schema gap, not a null-value gap) — the
already-shipped `reprocess_bulk_tardis_derivative_ticker_funding_timestamp_2026_07_28.py` script's own live probe
correctly found this and no-op'd it (`skipped_no_funding_timestamp_column`).

**Investigation (per the operator's 3-part ask):**

1. **Corpus grep** (`unified-trading-pm/codex/`, `plans/`, and the MTDS adapter code) for any existing documentation of
   Extended's funding cadence: found the adapter's own docstring already asserted "hourly"
   (`_fetch_extended_funding_for_symbol`'s one-line docstring, present since the function was first written) — a genuine
   prior-engineer belief, but NOT independently cited/verified anywhere in the corpus at the time.
   `unified_api_contracts.registry.perp_funding_cadence.FUNDING_CADENCE_SECONDS` had NO entry for Extended at all before
   this session.
2. **Official API documentation** (fetched live 2026-07-28 — Extended Exchange, a StarkNet perp DEX built by an
   ex-Revolut team, publishes full public docs): `docs.extended.exchange/extended-resources/trading/funding-payments` —
   "funding payments are charged every hour and are applied to all users with open positions at that time";
   `api.docs.extended.exchange` `GET /info/{market}/funding` — "the funding rate is calculated every minute; it is only
   applied once per hour", and its `T` timestamp field is documented as "the timestamp (in epoch milliseconds) when the
   funding rate was calculated and applied" — i.e. Extended's own raw `T` field already IS the charge instant (no
   forward-looking-vs-charge-instant offset exists for this venue the way it did for the Tardis bulk-CSV venues in
   Finding 2 — there is nothing to shift, only a missing column to add).
3. **Real production data, pulled live via GCS** (not assumed): sampled
   `EXTENDED-STARKNET:PERPETUAL:{AAVE,BTC,ETH,SOL,XRP}-USD@LIN` `derivative_ticker` shards across both pipeline_mode
   lanes (`batch_extended` — the declared native lane — and the currently-mislabelled `batch_tardis` copy, see
   `plans/active/issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md`) and across dates spanning the
   venue's funding genesis through the present: `2025-07-18` (genesis day), `2025-07-20`, `2025-08-01`, `2026-01-14`,
   `2026-01-15`, `2026-02-15`, `2026-06-03`. Every sampled shard: exactly 24 rows/day. On `2026-06-03`, EVERY ONE of the
   5 sampled instruments' 24 `timestamp` values is IDENTICAL across instruments (a single system-wide settlement batch,
   not a per-market async job) and lands at `minute=0` of every UTC hour, with sub-second jitter clustering tightly
   around exactly 3600s apart (observed delta range [3599.09s, 3600.94s] — i.e. <=0.95s jitter, consistent with
   "calculated every minute, applied once per hour"). `2025-07-17` (one day pre-genesis) has ZERO objects in either lane
   — honest absence, not a flat/fabricated placeholder, matching the adapter's own pre-activation-rows-are-real `0.0`
   convention for `2025-07-18`/`2025-07-20`.

**Confidence reached: REAL, from two independent sources (official docs + empirical cross-instrument/cross-date
production data), not a guess.** Cadence = 1h (24/day). Anchor = UTC hour boundaries (`:00:00` each hour), not offset.

**Key gotcha found + fixed (registry key FORM, not just the cadence value):** Extended's canonical `venue` value is
ALWAYS the compound `"EXTENDED-STARKNET"` (GCS venue-dir, `instrument_id`, the adapter's own `venue` field literal —
never a bare `"EXTENDED"` anywhere in the codebase), and `-STARKNET` is a CHAIN suffix, not one of
`perp_funding_cadence._VENUE_SUFFIXES`'s registered INSTRUMENT-TYPE suffixes (`-futures`/`-swap`/`-perpetual`/`-perp`).
Registering a bare `"extended"` key (mirroring how Coinbase/Hyperliquid are registered) would have silently made
`is_supported_venue("EXTENDED-STARKNET")` return `False` for every real caller — confirmed live in-session
(`_canonical_venue("EXTENDED-STARKNET") == "extended-starknet"`, no suffix stripped). The registry key is therefore the
full lowercased compound string `"extended-starknet"`. **Related (found, NOT fixed here — out of this task's scope):**
the SAME bug class already exists for the shipped `"lighter"` key — LIGHTER-ZKSYNC's real venue value is also
`"LIGHTER-ZKSYNC"` (a `-ZKSYNC` chain suffix, same shape as `-STARKNET`), so `is_supported_venue("LIGHTER-ZKSYNC")` is
`False` today too (confirmed live: `_canonical_venue("LIGHTER-ZKSYNC") == "lighter-zksync"`). Currently DORMANT/harmless
— every real consumer of `perp_funding_cadence`
(`features-service/features_service/cefi/calculators/perp_funding_rates.py`,
`.../onchain/calculators/perp_funding_rates_defi.py`) is MVP-scoped to Binance/ETH-PERP only and never actually calls in
with `"LIGHTER-ZKSYNC"` yet — but it is a real latent bug, tracked as its own todo below rather than fixed
opportunistically in this session (a different venue's registry key deserves its own deliberate verification, not a
drive-by change riding on the Extended fix).

**What shipped:**

- `unified-api-contracts@ee7cb341` (co-mingled with a concurrent sibling agent's Coinbase-cadence commit in this
  heavily-multi-agent shared checkout — content independently verified identical to what was intended, diff against
  `origin/live-defi-rollout` is empty): `perp_funding_cadence.FUNDING_CADENCE_SECONDS["extended-starknet"] = 3600`
  - a new public `cadence_seconds(venue) -> int` helper (single derivation point for "shift/derive by one cadence"
    corrections, reused by the new MTDS script below) + module-docstring evidence trail + regression tests
    (`test_perp_funding_cadence.py`: `TestFundingsPerYear.test_extended_starknet_one_hour`, `TestCadenceSeconds`, the
    venue-dir-form + key-form-absence guards).
- `market-tick-data-service` (go-forward fix): `adapters/_umi_extended.py::_fetch_extended_funding_for_symbol` now emits
  `funding_timestamp` (a straight alias of the row's own `timestamp` — Extended's `T` already IS the charge instant) and
  `next_funding_timestamp` (`funding_timestamp + cadence_seconds("EXTENDED-STARKNET")`) on every funding row. New test
  `tests/unit/test_umi_extended_funding_timestamp.py` (4 tests: alias-equality, one-cadence-ahead, boundary-exact 24-row
  seam invariant — row N's `next_funding_timestamp` lands EXACTLY on row N+1's `funding_timestamp` with no gap/overlap —
  and day-window-filtering regression).
- `market-tick-data-service` (historical reprocessing, a NEW dedicated script — deliberately NOT an extension of the
  shipped Tardis script, which is schema-agnostic across every OTHER venue and already correctly no-ops
  EXTENDED-STARKNET for a different reason):
  `scripts/one_offs/add_extended_starknet_derivative_ticker_funding_timestamp_2026_07_28.py`. Unlike the Tardis venues'
  fix (SHIFT a raw forward-looking wire value back one cadence), this is a pure column ADD — there is no raw
  forward-looking value to correct, only two new columns to derive from the row's own already-correct `timestamp`.
  Processes both pipeline_mode lanes (`batch_extended` and the currently-mislabelled `batch_tardis` copy) independently
  and does NOT move/merge/delete anything between them (that re-partition is
  `onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md`'s own separate decision). Same delete-safety rigor as the
  sibling script: prefix-scoped discovery (never a whole-corpus walk), stage+verify, then backup+CAS-overwrite+verify
  only under `--apply`. 14 new unit tests
  (`tests/unit/scripts/test_add_extended_starknet_derivative_ticker_funding_timestamp_2026_07_28.py`): happy path,
  boundary-exact 24-row seam (re-proven at the Arrow-column level), every per-shard classification (no-timestamp-column
  / no-funding_rate-column / all-null-funding_rate / idempotency-guard), and the byte-identity assertion's own negative
  cases (raises on row-count change / mutated pre-existing column / unexpected column addition).

**Bounded sample-validate proof (2026-07-28, real production data, full backup-verify-overwrite-verify protocol):**

- `--mode scan` (manifest-driven): manifest under-counts this venue badly for `batch_extended` (shows only
  `2026-07-24`→`2026-07-27`, 335 shards — a separate, pre-existing manifest-vs-GCS drift for this venue, NOT something
  this task fixes) but is accurate for `batch_tardis` (281 shards, `2026-01-14`→`2026-06-03` — matches the number
  already established by the mislabelled-lane characterization script). Real total scope for BOTH lanes combined is
  therefore materially larger than the manifest alone shows (real GCS objects exist back to the `2025-07-18` funding
  genesis for `batch_extended`, confirmed by direct listing) — full-corpus quantification via real (non-manifest)
  listing is left to the VM-launched follow-up below, consistent with the heavy-I/O rule.
- `batch_extended`, `--start-date 2025-07-18 --end-date 2025-07-20` (3 days spanning the funding genesis, both
  instrument coverage and the pre-activation-flat-`0.0` window): dry-run **135/135 `would_add`, 0 errors**; real
  `--apply` **135/135 `added`, 0 errors** — every object backed up
  (`_migrations/extended_starknet_derivative_ticker_funding_timestamp_add_2026_07_28/backups/20260728-165200/...`,
  byte-for-byte verified via `gcs_describe_object` size+crc32c match before overwrite), canonical path CAS-overwritten,
  new content verified landed.
- `batch_tardis` (the currently-mislabelled lane), `--start-date 2026-01-14 --end-date 2026-01-14`: real `--apply`
  **69/69 `added`, 0 errors**, same backup+verify protocol (`.../backups/20260728-165427/...`).
- **Independent re-verification** (a FRESH read, outside the script's own internal assertions — not just trusting the
  script's self-report): re-downloaded a corrected canonical object AND its backup for both lanes
  (`EXTENDED-STARKNET:PERPETUAL:AAVE-USD@LIN`, `2025-07-18` `batch_extended` and `2026-01-14` `batch_tardis`) and
  confirmed live: the backup carries the ORIGINAL column-less schema; the canonical (post-fix) object carries
  `funding_timestamp`/`next_funding_timestamp`; `funding_timestamp` equals `timestamp` exactly on every row;
  `next_funding_timestamp - funding_timestamp == 3600s` exactly on every row; every OTHER column (`open`/`high`/`low`/
  `close`/`volume`/`funding_rate`/`available_at`/...) is byte-identical between backup and corrected canonical.
- This fix never touches the manifest (parquet-content-only) — no manifest verification needed the way the sibling
  Tardis script's proof required one.

- [x] ✅ [DATA] P1. Reverse-engineer + build EXTENDED-STARKNET `funding_timestamp`/`next_funding_timestamp` (mechanism +
      derivation). **DONE 2026-07-28** — see Finding 5 above for the full evidence trail. Shipped:
      `unified-api-contracts@ee7cb341` (`perp_funding_cadence` registration + `cadence_seconds()` helper + tests),
      `market-tick-data-service` (go-forward `_umi_extended.py` fix + new one-off historical-reprocessing script, both
      with unit tests, `quality-gates.sh` green modulo unrelated concurrent foreign WIP in this shared checkout — see
      commit for the exact scoped diff). Bounded sample-validated on real production data: 135/135 `batch_extended`
      objects + 69/69 `batch_tardis` objects corrected, 0 errors, independently re-verified.
- [x] ✅ [DATA] P2. Scale `add_extended_starknet_derivative_ticker_funding_timestamp_2026_07_28.py --mode apply --apply`
      to the full historical corpus (both pipeline_mode lanes) via a VM (heavy-I/O rule — the manifest undercounts this
      venue's `batch_extended` lane, so a real per-day listing pass is needed first to size the true full-corpus scope
      before launching, not just the manifest's 335+281 shard estimate). **GO recommendation** — the mechanism is proven
      (204/204 real objects round-tripped with zero errors across both lanes in the bounded sample). **Repo:
      market-tick-data-service + deployment-service** (VM launcher). — **LAUNCHED 2026-07-28/29 (autonomous session)**:
      the mtds-side blocker (unresolved merge conflict + untracked add-script from the crashed sibling task, see above)
      cleared — resolved the conflict (kept upstream's equivalent `coinbase`→`kucoin` unregistered- venue-fixture swap,
      functionally identical to the stashed `not-a-real-venue` version), shipped `market-tick-data-service@213bda48`.
      Both lanes launched via `launch-cefi-extended-starknet-funding-timestamp- vm.sh`:
      `canonical-migration-cefi-fts-ext-ext-20260729-004416` (`batch_extended`, 2025-07-18..2026-07-28) and
      `canonical-migration-cefi-fts-ext-tar-20260729-004527` (`batch_tardis`, 2026-01-14..2026-07-28), both confirmed
      `RUNNING` with fresh mtds tarball (`213bda48`). The real per-day full-corpus sizing pass this todo's own text
      flagged as a prerequisite has NOT been independently re-verified beyond the manifest-undercount finding already on
      record — the launched VMs' own `--mode scan` step performs this sizing internally before `--apply`, so it does not
      block the launch, just deferred to the VM's own run.log for the final real count.
- [x] ✅ [DATA] P2. Fix the SAME registry-key-form bug for `"lighter"` → `"lighter-zksync"` (LIGHTER-ZKSYNC's real venue
      value, like EXTENDED-STARKNET's, is a compound `<VENUE>-<CHAIN>` string that `_canonical_venue` does not reduce) —
      found as a side-discovery while fixing Extended's identical bug class, currently dormant/harmless (no live
      consumer calls in with the real `"LIGHTER-ZKSYNC"` venue string yet) but a real latent correctness gap. Verified
      no existing caller relies on the bare `"lighter"` key (consumers are MVP-scoped to Binance/ETH-PERP only; the
      Tardis adapter slug `"lighter"` is a separate namespace from this cadence registry). —
      unified-api-contracts@feee6d02
- [x] ✅ [DATA] P2. Fix the pre-existing `batch_extended`/EXTENDED-STARKNET manifest-vs-GCS undercount discovered while
      scoping Finding 5's `--mode scan` (manifest shows only `2026-07-24`→`2026-07-27` for this pipeline_mode; real GCS
      objects exist back to the `2025-07-18` funding genesis) — a separate pre-existing drift, not something this task's
      fix caused or corrects. **Repo: market-tick-data-service@5114bfd8.**

## Progress Log (context-scout)

- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged from prior scout — still accurate: the
  pnl-attribution + carry-venue-integration codex SSOTs, the UAC `perp_funding_cadence` registry, and the MTDS
  `tardis_shared.py` bulk write path).
- **context-scout 2026-08-06**: restored the dropped carry-venue-integration SSOT + added the 08-04 gap follow-up doc. 5
  entries.

## Progress Log — CEX-Tardis forward capture outage discovered (2026-08-04)

- **slot-4 2026-08-04 (data_engineering, AO dispatch)**: while resolving a repoint-feasibility question in
  `/plans/active/issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md`'s P2(b) todo, live bounded GCS probes
  showed this doc's own 2026-07-28 census cutoff (`...→2026-05-22`/`...→2026-05-01`, line ~273) is not a historical
  artifact — it's a STILL-ONGOING outage, unresumed through 2026-08-03. Filed as a new P1 todo above (mirrors the
  already-fixed sibling `cefi_onchain_perp_forward_capture_outage_2026_08_03.md` pattern, different launcher/venue
  population). Not remediated this session — read-only probes only, no cron/launcher change made; flagged for the next
  data_engineering pickup.
