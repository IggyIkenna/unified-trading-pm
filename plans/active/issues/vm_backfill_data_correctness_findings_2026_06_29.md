---
doc_type: issue
title: Backfill-VM data-correctness findings (footystats odds / Aster funding / FX / Curve / bybit / lending)
summary:
  Six data-pipeline defects found while auditing running GCP backfill VMs 2026-06-29 — backfills are "alive"
  (heartbeating) but several produce invalid/empty output. Code-fixable defects fixed so the next VM generation runs
  clean.
status: open
nature: notes
asset_group: [sports, defi, cefi, tradfi]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [backfill, data-quality, footystats, aster, fx, curve, bybit, lending, honest-absence]
related:
  [
    market-tick-data-service/issues/DEFI-ASTER-LOG-REVIEW.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/09-strategy/mvp-universe-per-asset-group.md,
  ]
created: 2026-06-29
parent_epic: infrastructure_master
priority: P1
source: VM spend/health audit 2026-06-29 (gcp_vm_spend_audit.md)
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
audited_scope: data-correctness
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated:
  "2026-06-30 (was: 2026-06-27 — verify-rerun-2 finding 95, corrected 2026-07-14 — last_updated predated
  created:2026-06-29 by 2 days [copy-paste template artifact]; corrected to match the Progress Log's actual latest
  entry, 2026-06-30)"
locked_since: 2026-05-21
---

# Backfill-VM data-correctness findings — 2026-06-29

## Context

While auditing the running GCP backfill VMs (`central-element-323112`, zone `asia-northeast1-c`) for spend, a deeper
work-product check (run.log content, not just heartbeat/CPU) surfaced that several backfills are **alive and
heartbeating but producing invalid or empty data**. The supervising orchestrator agent only checks liveness, so these
passed unnoticed.

Per `/codex/02-data/data-pipeline-correctness-hard-rule.md`, these freeze downstream feature/backtest work for the
affected streams (foundation-completion-gate). Evidence = per-VM `run.log` under
`gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log`, sampled 2026-06-29 ~11:38 UTC.

## Findings (prioritized)

### F1 — ✅ FIXED (instruments-service@a4dfa6b) — footystats odds `kickoff_utc` serialization

- **VM:** `fs-backfill-20260629-062206` (SPORTS, footystats odds). **MVP-critical** (odds = sports backtest input).
- **Symptom:** 179×
  `ERROR validation error in instruments-service.footystats_odds_fetch: ("Expected bytes, got a 'Timestamp' object", 'Conversion failed for column kickoff_utc with type object')`.
- **Root cause:** pyarrow write failure. The NaN-fill path injects scheduled-fixture rows with `kickoff_utc` as a
  `pd.Timestamp` (`instruments_service/engine/orchestrator/footystats.py` ~L759/L672-678), which collide with the API
  odds rows' `kickoff_utc` (string), yielding an object-dtype column pyarrow can't serialize against the table schema.
- **Fix:** coerce `kickoff_utc` to a single consistent dtype before write (normalize across API + NaN-fill rows).
- **Repo/file:** `instruments-service/.../engine/orchestrator/footystats.py`.

### F2 — ✅ FIXED (market-tick-data-service@7da5f6ad) — Aster aggTrades 4xx storm (wrong genesis date)

- **VM:** `mtds-perp-funding-backfill` (DEFI). Aster is an MVP bridge-perp venue.
- **Symptom:** 113,000+ `WARNING Failed to fetch Aster aggTrades for <sym> on <date>: 4xx Client Error`. Hyperliquid +
  GMX funding write fine; Aster yields only errors. Unlike Kalshi/Polymarket (which log `EXPECTED_PRE_VENUE_LAUNCH`),
  Aster spams 4xx for pre-launch / unavailable dates instead of recording honest-absence.
- **2026-06-29 ROOT CAUSE (verified, UAC dates confirmed):** there are **two distinct Aster genesis dates** and the
  trades leg uses the wrong one. (1) **Funding** genesis = `2023-07-22` (UAC `registry/venue_launch_dates.py "ASTER"` +
  `perp_funding_handler.py:127 _ASTER_FUNDING_START_DATE`, _operator-confirmed 2026-06-17_: funding reaches back via the
  Astherus pre-rebrand, Binance-proxied) — so the **funding leg is correct** to run 2023-11→2024-06 and is already gated
  (`_perp_funding_hl_aster.py:184`). (2) **Native trades (aggTrades)** genesis = `2024-09-01` (UAC
  `registry/chain_env.py ("BSC","ASTER")` — "Aster DEX launched on BSC ~Q3 2024"). The 113K 4xx are the **trades leg**
  (`_write_aster_trades`, `_perp_funding_hl_aster.py:428`) running from the _funding_ start (2023-07-22) while Aster's
  native tape only exists from ~2024-09 → every pre-launch date 4xxes.
- **Fix (specified, not blocked):** gate `_write_aster_trades` by the **native-trades genesis** (UAC `("BSC","ASTER")` =
  2024-09-01, NOT the funding start) — early-return + **record honest-absence** (`record_zero_rows` /
  `EXPECTED_PRE_VENUE_LAUNCH`, per QG STEP 5.86, mirroring the funding leg's pre-launch path) instead of attempting the
  aggTrades fetch. Funding leg unchanged. Add a `_ASTER_TRADES_START_DATE` constant sourced from UAC chain_env. + test.
- **Repo/file:** `market-tick-data-service/.../cli/handlers/_perp_funding_hl_aster.py` (`_write_aster_trades`), date
  SSOT `unified-api-contracts/.../registry/chain_env.py`.

### F3 — ✅ FIXED (market-tick-data-service@75c8f148) — TradFi FX backfill wrote zero rows (timestamp-bias rejection)

> Operator decision 2026-06-29: **bug fixed for correctness, but NO new FX VMs launched** (FX is out of TradFi MVP).
> Same fix also covers the KRX Yahoo daily-bar path (identical bug). Root cause: Yahoo daily bars are close-edge stamped
> (bar for day D closes at D+1 00:00); the FX/KRX records omitted `bar_edge="close"`, so the day-partition validator
> (`partitioned_writer.py:232` keys `close_edge` off that column) rejected every bar. Fix sets the marker.

- **VM:** `tradfi-bf-fx-ohlcv-24h-2026` (TRADFI). **Out of named MVP** (FX not in TradFi MVP universe).
- **Symptom:** 24×
  `ERROR Venue FX: adapter error: UpstreamTimestampBiasError: expected_day=<d>, observed_range=[…], n_ticks_seen=N — adapter received ticks but ALL fell [outside expected day]`;
  204× `SHARD_INCOMPLETE … missing ['FX']`; 0 rows written across 149 dates.
- **Root cause:** 24h-bar FX adapter day-boundary/timezone mismatch — ticks land outside the expected UTC day window and
  are all rejected.
- **Fix:** correct the FX 24h-bar day-window alignment. **Lower priority** — FX is out of MVP; the VM itself should be
  killed regardless (see audit doc). Fix only if FX capture is wanted.

### F4 — [P2][CONFIG] Curve DEX pools dead — decommissioned subgraph

- **VM:** `mtds-dex-pools-backfill` (DEFI).
- **Symptom:** 1,207× `WARNING Subgraph query errors … 'subgraph not found: no allocations'` +
  `All query schemas failed for curve/<id>` → `curve_* = 0` pools every date. Uniswap/Sushi/Pancake/Aerodrome OK.
- **Root cause:** `curve_adapter.py` `SUBGRAPH_URL = https://api.thegraph.com/subgraphs/name/lnfi/ln` — The Graph's
  hosted service (`/subgraphs/name/...`) was decommissioned; must use the gateway subgraph-id endpoint.
- **2026-06-29 LIVE-ENDPOINT VERIFICATION (operator-requested):** Curve REST
  `api.curve.finance/v1/getPools/all/ethereum` is **alive** (HTTP 200, 2,347 pools) — BUT returns only **current** pool
  snapshots. `mtds-dex-pools-backfill` needs **historical** `dex_pool_state` per day (block-level), which REST cannot
  provide. The dex-pools handler routes curve through the subgraph only
  (`_dex_pools_subgraph.py:216 fallbacks["curve"]=[messari_basic]`); the gateway subgraph ID returns `no allocations`
  (no indexers serve it). **The fix is NOT a simple REST cutover** — historical pool-state needs either (a) a **current
  indexer-allocated Curve subgraph ID** (The Graph gateway — needs the API key to verify which subgraph is live), or (b)
  **RPC at historical blocks** via `_query_curve_pool_at_block` (needs Alchemy/RPC key). → **BLOCKED-CREDENTIALS /
  operator decision**: provide The Graph key (find a live Curve subgraph) or RPC key, or accept honest-absence for Curve
  pools until a source is wired. (REST stays usable for current-state instrument discovery.)

### F5 — [P2][DATA] bybit dated-futures fetches time out en masse (Tardis)

- **VMs:** `cefi-bybit-2025-light`, `cefi-bybit-2026-light` (CEFI). bybit is an MVP venue.
- **Symptom:** ~2,600 failed fetches each — `TimeoutError` / `ConnectionTimeout` / HTTP errors fetching bybit **dated
  futures** (`BTC-26DEC25`, `MNTUSDT-29MAY26`) from `datasets.tardis.dev`. Perps succeed; dated futures mostly fail, yet
  the date is marked OK.
- **Root cause (to confirm):** likely those dated contracts are not in Tardis's archive (vendor gap) OR transient
  network. **Open question:** are these failures recorded as honest-absence (`record_captured` failed/unattempted) or
  silently dropped? — verify before code change.
- **Fix:** (a) confirm honest-absence recording; (b) if vendor-gap, skip-list nonexistent dated contracts to stop
  infinite-retry burn rather than treat as code bug.

### F6 — [P3][DATA] DeFi lending-indices: heavy instruments-store fallback, ~39% zero-row writes

- **VM:** `mtds-lending-indices-20260628` (DEFI).
- **Symptom:** 18k×
  `WARNING instruments-store-defi parquet missing for {aave_v3,compound_v3}/<chain>/<date>; falling back to subgraph discovery`;
  ~39% of writes are 0-row (aave OPTIMISM/LINEA, compound mostly empty).
- **Root cause:** upstream instruments-service reference data missing for those venue/chain/date combos → fallback
  yields little. May be legit (venue not deployed on chain in period) or an instruments-service backfill gap.
- **Fix:** confirm whether the missing instruments-store reference data is an instruments-service backfill gap; if so,
  backfill it. Not a quick MTDS code fix.

### F7 — [P1][SCOPE] TradFi capture is NOT `is_mvp`-gated — a whole un-gated asset group (FX was one symptom)

**Audit (2026-06-30, operator-requested "find the other FX-class items"). INVENTORY ONLY — no fix yet (operator
decision). SSOT: `unified_api_contracts.canonical.crosscutting.mvp_scope` v12 (`is_mvp` predicate).**

Systemic root: **CeFi + DeFi capture ARE `is_mvp`-gated** (`market-tick-data-service/.../engine/cefi_catalog_reader.py`,
`defi_catalog_reader.py`, `market_interface/adapters/tradfi/tardis_symbol_resolution.py` all call `is_mvp`). **TradFi
capture is gated NOWHERE** — the per-venue launchers fetch their full hardcoded universes and no `is_mvp`/underlier gate
exists in any TradFi catalog reader. FX was not a one-off; it was one symptom of an entirely un-gated asset group. All
items below are dispatched by the **same 3-hourly `wave_launcher.py` host cron** that was relaunching FX.

**A. Confirmed active out-of-scope (highest priority — proven-live cron):**

- **F7a — NASDAQ/NYSE equities, full universe.** `launch-tradfi-bf-nasdaq-ohlcv-1m.sh:70` (and NYSE twin) fetch
  `SP500_TICKERS ∪ NASDAQ_TICKERS ∪ ETF_TICKERS` with **no gating**. In scope = the **105**-ticker
  `TRADFI_EQUITY_PERP_BASIS_UNIVERSE` (the `is_mvp` equity-basis carve-out, `mvp_scope.py:1100-1119`). Out of scope =
  **173/200 SP500 + 54/78 ETF tickers (~227)**. These ride INSIDE the per-year VM (extra runtime/storage, not extra VMs;
  `PER_YEAR_VENUES`).
- **F7b — CME roots (biggest VM-count waste).** `launch-tradfi-bf-cme-ohlcv-1m.sh` `CME_ROOTS` = **49** roots; CME
  shards one VM **per (root, year)** (`PER_ROOT_VENUES`, `--only-root`). MVP CME underliers (`mvp_scope.py:628`) =
  **9**: ES NQ GC SI PL PA NG CL HG (VX is on **CBOE**, captured separately). Out of scope = **~39 roots**, each its own
  VM/year: 6A 6B 6C 6E 6J 6L 6M 6N 6S 6Z (**10 FX FUTURES — FX returns in futures form**), ZB ZF ZN ZT (treasuries), ZC
  ZL ZM ZS ZW (grains), HE LE (livestock), CT HO RB (softs/refined), NKD YM RTY (equity index), **BTC ETH MBT MET
  (crypto — operator confirms OUT)**, MES (micro S&P — operator confirms micros OUT), XAB XAF XAI XAK XAP XAU XAV XAY,
  ECES ECBTC ECRTY ECYM ECGC ECCL ECNG EC6E ECNQ (9 event contracts).
- **F7c — `ohlcv_1s`.** `wave_launcher.py:110` `OHLCV_DATA_TYPES={ohlcv_1m, ohlcv_1s}`; TradFi MVP = **`ohlcv_1m` only**
  (decision #7, `mvp_scope.py:603-627`). **Operator decision: KEEP pending per-item review** (likely a free byproduct of
  the same Databento pull → storage cost only, not VM cost; may feed the features layer). Do NOT auto-strip.

  **Open keystone (one check before any fix):** whether the TradFi `expected_unattempted` enumerator itself filters by
  `is_mvp` (decides whether F7a/F7b cells become gap cells → dispatched, vs merely capturable). No tradfi `is_mvp` usage
  found in catalog readers (unlike cefi/defi) — strongly suggests NOT gated → out-of-scope cells ARE enumerated +
  dispatched. Confirm before the fix.

**B. Out-of-scope launcher exists — verify cron-active before cleanup:**

- DeFi wrong-chain/version venues — `launch-defi-backfill-vm.sh` hardcodes CURVE-AVALANCHE, CURVE-OPTIMISM,
  UNISWAP_V3-POLYGON, UNISWAP_V4-ETHEREUM (MVP = CURVE/UNISWAP_V3-**ETHEREUM** only; 4 of 7 venues out).
- DeFi LST beyond Lido — `launch-mtds-lst-rates` covers Lido + **Marinade/Jito (Solana) + Rocketpool** (MVP LST =
  LIDO-ETHEREUM only; Rocketpool removed v12).
- DeFi lending beyond Aave/Compound-Ethereum — `launch-mtds-lending-indices` (RUNNING NOW) covers Aave + **Morpho/Spark/
  Fluid/Kamino** (MVP lending = AAVE_V3 + COMPOUND_V3 Ethereum only). Check what protocols/chains it actually iterates.
- Sports non-football — odds launcher hardcodes ~6 leagues incl **NFL/NBA/MLB/NHL/tennis** (MVP = 94 football leagues).
- Prediction `financial` — backfill captures all conditionIds incl the **financial** market_group (MVP =
  crypto/politics/ sports).
- DeFi non-MVP data_types — `gas_fees` (8 EVM chains), `vault_share_price`, `eigenlayer_rewards`, `flash_loan_events`,
  `risk_params`, `user/LP positions`, `liquidations` — none in MVP DeFi data_type set. **Operator decision: KEEP pending
  per-item review** (may be deliberate features-layer inputs). Do NOT auto-strip.

**C. Dormant / handled:** FX Yahoo `ohlcv_24h` (already descoped, `deployment-service@b38dbff`); ICE (empty scaffolding,
no source).

**Operator scope decisions (2026-06-30):** (1) inventory only, no code changes yet; (2) CME crypto + micros (BTC/ETH/
MBT/MET/MES) confirmed OUT; (3) `ohlcv_1s` + DeFi extra data_types = KEEP pending per-item review (possible features
inputs) — flag, don't strip. Proposed structural fix (deferred): gate the TradFi launchers + `wave_launcher` addressable
set through `is_mvp` (NASDAQ/NYSE → 105 basis tickers; CME `--only-root` → 9 MVP underliers), mirroring CeFi.

## Cross-cutting observation (separate issue)

The orchestrator agent that supervises these VMs gates only on **heartbeat/liveness**, not output correctness. It
relaunches VMs that fail to _start_, but is blind to all-NaN output, WriteGate rejections, 4xx storms, and 0-row writes.
A correctness/output check is needed. Also: the feature-sports backfill (`fss-backfill-vm-*`) computes 66 leagues vs the
Top-5-European MVP — scope, tracked in `gcp_vm_spend_audit.md`.

## Fix order

1. F1 footystats odds (P0, code, MVP-critical) ← start here
2. F4 Curve subgraph (P2, config) and F2 Aster honest-absence (P1, code)
3. F3 FX (P2, code, out-of-MVP — fix or kill)
4. F5 bybit / F6 lending (P2/P3, data/verify-first)

## Progress Log

- 2026-06-29: Findings captured from VM audit. Issue doc created. Starting F1.
- 2026-06-29: **F1 FIXED** — `instruments-service@a4dfa6b` (quickmerge → live-defi-rollout). Extracted
  `_kickoff_iso_or_none()` helper; both odds NaN-fill sites now emit ISO-string `kickoff_utc` instead of `pd.Timestamp`.
  Added regression test `tests/unit/test_footystats_odds_kickoff_serialization.py` (4 tests incl. one reproducing the
  pyarrow `Expected bytes, got Timestamp` failure). QG green (139s).
- 2026-06-29: **F3 FIXED** — `market-tick-data-service@75c8f148` (quickmerge → live-defi-rollout). Set
  `bar_edge="close"` on Yahoo FX + KRX `ohlcv_24h` records so the day-partition validator accepts close-edge daily bars.
  Regression test `tests/unit/test_yahoo_fx_close_edge.py` (mocks a close-edge bar; asserts marker + validator passes
  with close_edge, raises without). QG green. Operator: fix-only, no new FX VMs launched.
- 2026-06-29: **F4 VERIFIED (operator-requested live check)** — Curve REST is alive (2,347 pools) but returns only
  CURRENT snapshots; historical `dex_pool_state` backfill needs an indexer-allocated subgraph ID (The Graph gateway key)
  or RPC (`_query_curve_pool_at_block`, Alchemy key). **→ BLOCKED-CREDENTIALS / operator decision** (provide a key or
  accept Curve honest-absence). Not a code-only fix.
- 2026-06-29: **F2 ROOT-CAUSED (UAC dates confirmed — operator was right, it's in UAC)** — two genesis dates: funding
  2023-07-22 (correct, gated) vs native-trades 2024-09-01 (`chain_env ("BSC","ASTER")`). The 4xx storm is the trades leg
  using the funding start.
- 2026-06-30: **FX wave-launcher descoped** — `deployment-service@b38dbff` (quickmerge → live-defi-rollout). Root cause
  of the FX-VM respawns: a **3-hourly host cron** (`0 */3 * * *`, `wave_launcher_scheduler.tf`) runs `wave_launcher.py`
  on the orchestrator VM (`13.113.200.22`, as `ikenna@`) and relaunches a per-year FX VM whenever none exists (confirmed
  by audit log: FX re-inserted at 18:00 + 00:00 after manual deletes, each self-completing). Removed FX from
  `wave_launcher.py` (`PER_YEAR_VENUES` + `LAUNCHER_FOR_VENUE` + `VENUE_DATA_TYPES`) since `is_mvp(tradfi, FX, …)=False`
  (TradFi MVP `venues={CME}`; FX absent from `mvp_scope.py`). The launcher script + Yahoo adapter remain for future
  re-scope. NOTE: takes effect once the orchestrator cron's checkout/image picks up the new `wave_launcher.py`.
- 2026-06-29: **F2 FIXED** — `market-tick-data-service@7da5f6ad` (quickmerge → live-defi-rollout). Added
  `_ASTER_TRADES_START_DATE = "2024-09-01"` (perp_funding_handler.py:136, cites UAC chain_env SSOT) + a native-launch
  guard at the top of `_write_aster_trades` (early-return + log, mirroring the funding leg's pre-launch pattern) so the
  aggTrades fetch is skipped for pre-native dates. Funding leg unchanged. Regression test
  `tests/unit/test_aster_trades_launch_guard.py` (asserts no aggTrades fetch for 2024-06-01). QG green (106s). **Status:
  3 of 6 fixed (F1, F3, F2). F4 = BLOCKED-CREDENTIALS (operator key decision). F5/F6 = verify-first/upstream.**
- 2026-06-30: **F7 captured (out-of-scope capture audit, operator-requested "find the other FX-class items")** — TradFi
  capture is the un-gated class: CeFi/DeFi readers call `is_mvp`, TradFi gates nowhere. Confirmed active out-of-scope
  under the same wave_launcher cron: NASDAQ/NYSE full equity universe (~227 of ~278 tickers out vs the 105 basis
  universe; `launch-tradfi-bf-nasdaq-ohlcv-1m.sh:70`), CME 49-root list vs 9 MVP underliers (~39 out, incl. **10 FX
  futures** + crypto BTC/ETH/MBT/MET + micros — each a separate VM/year), `ohlcv_1s` (`wave_launcher.py:110`). Plus a
  B-tier list (DeFi wrong-chain venues / non-Lido LST / multi-protocol lending / sports non-football / prediction
  financial / DeFi non-MVP data_types) needing a cron-active check. **INVENTORY ONLY per operator** — no code changed.
  Operator scope decisions recorded in F7: CME crypto/micros OUT; `ohlcv_1s` + DeFi extra data_types KEEP pending
  per-item review. Open keystone: confirm whether the TradFi `expected_unattempted` enumerator is `is_mvp`-gated.
