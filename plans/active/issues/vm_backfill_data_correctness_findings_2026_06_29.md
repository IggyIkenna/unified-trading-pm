---
doc_type: issue
title: Backfill-VM data-correctness findings (footystats odds / Aster funding / FX / Curve / bybit / lending)
summary: Six data-pipeline defects found while auditing running GCP backfill VMs 2026-06-29 — backfills are "alive"
  (heartbeating) but several produce invalid/empty output. Code-fixable defects fixed so the next VM generation runs clean.
status: active
nature: bug
asset_group: [SPORTS, DEFI, CEFI, TRADFI]
stage: foundation-data
repos: [instruments-service, market-tick-data-service]
scope: data-correctness
tags: [backfill, data-quality, footystats, aster, fx, curve, bybit, lending, honest-absence]
related:
  - market-tick-data-service/issues/DEFI-ASTER-LOG-REVIEW.md
  - codex/02-data/data-pipeline-correctness-hard-rule.md
  - codex/02-data/honest-absence-downstream-handling.md
  - codex/09-strategy/mvp-universe-per-asset-group.md
created: 2026-06-29
priority: P1
source: VM spend/health audit 2026-06-29 (gcp_vm_spend_audit.md)
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Backfill-VM data-correctness findings — 2026-06-29

## Context

While auditing the running GCP backfill VMs (`central-element-323112`, zone `asia-northeast1-c`) for spend, a deeper
work-product check (run.log content, not just heartbeat/CPU) surfaced that several backfills are **alive and heartbeating
but producing invalid or empty data**. The supervising orchestrator agent only checks liveness, so these passed unnoticed.

Per `codex/02-data/data-pipeline-correctness-hard-rule.md`, these freeze downstream feature/backtest work for the
affected streams (foundation-completion-gate). Evidence = per-VM `run.log` under
`gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log`, sampled 2026-06-29 ~11:38 UTC.

## Findings (prioritized)

### F1 — ✅ FIXED (instruments-service@a4dfa6b) — footystats odds `kickoff_utc` serialization

- **VM:** `fs-backfill-20260629-062206` (SPORTS, footystats odds). **MVP-critical** (odds = sports backtest input).
- **Symptom:** 179× `ERROR validation error in instruments-service.footystats_odds_fetch:
  ("Expected bytes, got a 'Timestamp' object", 'Conversion failed for column kickoff_utc with type object')`.
- **Root cause:** pyarrow write failure. The NaN-fill path injects scheduled-fixture rows with `kickoff_utc` as a
  `pd.Timestamp` (`instruments_service/engine/orchestrator/footystats.py` ~L759/L672-678), which collide with the
  API odds rows' `kickoff_utc` (string), yielding an object-dtype column pyarrow can't serialize against the table schema.
- **Fix:** coerce `kickoff_utc` to a single consistent dtype before write (normalize across API + NaN-fill rows).
- **Repo/file:** `instruments-service/.../engine/orchestrator/footystats.py`.

### F2 — ✅ FIXED (market-tick-data-service@7da5f6ad) — Aster aggTrades 4xx storm (wrong genesis date)

- **VM:** `mtds-perp-funding-backfill` (DEFI). Aster is an MVP bridge-perp venue.
- **Symptom:** 113,000+ `WARNING Failed to fetch Aster aggTrades for <sym> on <date>: 4xx Client Error`. Hyperliquid +
  GMX funding write fine; Aster yields only errors. Unlike Kalshi/Polymarket (which log `EXPECTED_PRE_VENUE_LAUNCH`),
  Aster spams 4xx for pre-launch / unavailable dates instead of recording honest-absence.
- **2026-06-29 ROOT CAUSE (verified, UAC dates confirmed):** there are **two distinct Aster genesis dates** and the
  trades leg uses the wrong one. (1) **Funding** genesis = `2023-07-22` (UAC `registry/venue_launch_dates.py "ASTER"` +
  `perp_funding_handler.py:127 _ASTER_FUNDING_START_DATE`, *operator-confirmed 2026-06-17*: funding reaches back via the
  Astherus pre-rebrand, Binance-proxied) — so the **funding leg is correct** to run 2023-11→2024-06 and is already gated
  (`_perp_funding_hl_aster.py:184`). (2) **Native trades (aggTrades)** genesis = `2024-09-01` (UAC
  `registry/chain_env.py ("BSC","ASTER")` — "Aster DEX launched on BSC ~Q3 2024"). The 113K 4xx are the **trades leg**
  (`_write_aster_trades`, `_perp_funding_hl_aster.py:428`) running from the *funding* start (2023-07-22) while Aster's
  native tape only exists from ~2024-09 → every pre-launch date 4xxes.
- **Fix (specified, not blocked):** gate `_write_aster_trades` by the **native-trades genesis** (UAC `("BSC","ASTER")`
  = 2024-09-01, NOT the funding start) — early-return + **record honest-absence** (`record_zero_rows` /
  `EXPECTED_PRE_VENUE_LAUNCH`, per QG STEP 5.86, mirroring the funding leg's pre-launch path) instead of attempting the
  aggTrades fetch. Funding leg unchanged. Add a `_ASTER_TRADES_START_DATE` constant sourced from UAC chain_env. + test.
- **Repo/file:** `market-tick-data-service/.../cli/handlers/_perp_funding_hl_aster.py` (`_write_aster_trades`),
  date SSOT `unified-api-contracts/.../registry/chain_env.py`.

### F3 — ✅ FIXED (market-tick-data-service@75c8f148) — TradFi FX backfill wrote zero rows (timestamp-bias rejection)

> Operator decision 2026-06-29: **bug fixed for correctness, but NO new FX VMs launched** (FX is out of TradFi MVP).
> Same fix also covers the KRX Yahoo daily-bar path (identical bug). Root cause: Yahoo daily bars are close-edge
> stamped (bar for day D closes at D+1 00:00); the FX/KRX records omitted `bar_edge="close"`, so the day-partition
> validator (`partitioned_writer.py:232` keys `close_edge` off that column) rejected every bar. Fix sets the marker.


- **VM:** `tradfi-bf-fx-ohlcv-24h-2026` (TRADFI). **Out of named MVP** (FX not in TradFi MVP universe).
- **Symptom:** 24× `ERROR Venue FX: adapter error: UpstreamTimestampBiasError: expected_day=<d>, observed_range=[…],
  n_ticks_seen=N — adapter received ticks but ALL fell [outside expected day]`; 204× `SHARD_INCOMPLETE … missing ['FX']`;
  0 rows written across 149 dates.
- **Root cause:** 24h-bar FX adapter day-boundary/timezone mismatch — ticks land outside the expected UTC day window and
  are all rejected.
- **Fix:** correct the FX 24h-bar day-window alignment. **Lower priority** — FX is out of MVP; the VM itself should be
  killed regardless (see audit doc). Fix only if FX capture is wanted.

### F4 — [P2][CONFIG] Curve DEX pools dead — decommissioned subgraph

- **VM:** `mtds-dex-pools-backfill` (DEFI).
- **Symptom:** 1,207× `WARNING Subgraph query errors … 'subgraph not found: no allocations'` + `All query schemas failed
  for curve/<id>` → `curve_* = 0` pools every date. Uniswap/Sushi/Pancake/Aerodrome OK.
- **Root cause:** `curve_adapter.py` `SUBGRAPH_URL = https://api.thegraph.com/subgraphs/name/lnfi/ln` — The Graph's
  hosted service (`/subgraphs/name/...`) was decommissioned; must use the gateway subgraph-id endpoint.
- **2026-06-29 LIVE-ENDPOINT VERIFICATION (operator-requested):** Curve REST `api.curve.finance/v1/getPools/all/ethereum`
  is **alive** (HTTP 200, 2,347 pools) — BUT returns only **current** pool snapshots. `mtds-dex-pools-backfill` needs
  **historical** `dex_pool_state` per day (block-level), which REST cannot provide. The dex-pools handler routes curve
  through the subgraph only (`_dex_pools_subgraph.py:216 fallbacks["curve"]=[messari_basic]`); the gateway subgraph ID
  returns `no allocations` (no indexers serve it). **The fix is NOT a simple REST cutover** — historical pool-state needs
  either (a) a **current indexer-allocated Curve subgraph ID** (The Graph gateway — needs the API key to verify which
  subgraph is live), or (b) **RPC at historical blocks** via `_query_curve_pool_at_block` (needs Alchemy/RPC key).
  → **BLOCKED-CREDENTIALS / operator decision**: provide The Graph key (find a live Curve subgraph) or RPC key, or accept
  honest-absence for Curve pools until a source is wired. (REST stays usable for current-state instrument discovery.)

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
- **Symptom:** 18k× `WARNING instruments-store-defi parquet missing for {aave_v3,compound_v3}/<chain>/<date>; falling
  back to subgraph discovery`; ~39% of writes are 0-row (aave OPTIMISM/LINEA, compound mostly empty).
- **Root cause:** upstream instruments-service reference data missing for those venue/chain/date combos → fallback yields
  little. May be legit (venue not deployed on chain in period) or an instruments-service backfill gap.
- **Fix:** confirm whether the missing instruments-store reference data is an instruments-service backfill gap; if so,
  backfill it. Not a quick MTDS code fix.

## Cross-cutting observation (separate issue)

The orchestrator agent that supervises these VMs gates only on **heartbeat/liveness**, not output correctness. It
relaunches VMs that fail to *start*, but is blind to all-NaN output, WriteGate rejections, 4xx storms, and 0-row writes.
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
- 2026-06-29: **F2 FIXED** — `market-tick-data-service@7da5f6ad` (quickmerge → live-defi-rollout). Added
  `_ASTER_TRADES_START_DATE = "2024-09-01"` (perp_funding_handler.py:136, cites UAC chain_env SSOT) + a native-launch
  guard at the top of `_write_aster_trades` (early-return + log, mirroring the funding leg's pre-launch pattern) so the
  aggTrades fetch is skipped for pre-native dates. Funding leg unchanged. Regression test
  `tests/unit/test_aster_trades_launch_guard.py` (asserts no aggTrades fetch for 2024-06-01). QG green (106s).
  **Status: 3 of 6 fixed (F1, F3, F2). F4 = BLOCKED-CREDENTIALS (operator key decision). F5/F6 = verify-first/upstream.**
