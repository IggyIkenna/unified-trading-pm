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

### F2 — [P1][CODE] Aster perp-funding fetch fails wholesale (4xx), no honest-absence

- **VM:** `mtds-perp-funding-backfill` (DEFI). Aster is an MVP bridge-perp venue.
- **Symptom:** 113,000+ `WARNING Failed to fetch Aster aggTrades for <sym> on <date>: 4xx Client Error`. Hyperliquid +
  GMX funding write fine; Aster yields only errors. Unlike Kalshi/Polymarket (which log `EXPECTED_PRE_VENUE_LAUNCH`),
  Aster spams 4xx for pre-launch / unavailable dates instead of recording honest-absence.
- **Root cause (suspected):** Aster adapter has no pre-launch / unavailable-date guard and/or wrong endpoint; backfill
  window (2023-11..2024-06) predates Aster launch. See existing `market-tick-data-service/issues/DEFI-ASTER-LOG-REVIEW.md`.
- **Fix:** add venue-launch-date guard → record `EXPECTED_PRE_VENUE_LAUNCH`; verify endpoint for in-range dates.
- **Repo/file:** `market-tick-data-service/.../adapters/onchain_perps/aster_adapter.py`,
  `.../cli/handlers/_perp_funding_hl_aster.py`.

### F3 — [P2][CODE] TradFi FX backfill writes zero rows (timestamp-bias rejection)

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
- **Fix:** migrate Curve to the gateway subgraph ID (or the REST fallback `api.ln.fi`), like balancer/aave do via
  `get_subgraph_id(...)`. **Repo/file:** `market-tick-data-service/.../adapters/defi/curve_adapter.py`.

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
  pyarrow `Expected bytes, got Timestamp` failure). QG green (139s). Next: F4 (Curve subgraph) / F2 (Aster).
