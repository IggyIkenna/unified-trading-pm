---
title: Data completion to 100% — all asset groups, batch + live, manifest v9 (MTDS + IS)
created: 2026-06-21
parent_epic: mtds_mdps_master
assigned_vm: planning
estimate_class: infra
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 8
locked_by: live-defi-rollout
priority: P0
status: active
---

# Data completion to 100% — all AGs, batch + live, manifest v9

Operator 2026-06-21: drive MTDS market-data + IS reference-data to **100% honest-coverage across every
asset group, batch AND live, manifest v9** — and DON'T STOP until done. The **only** sanctioned exclusion
is **batch Tardis (cefi historical)** which gates on billing; **live Tardis is free → hook it up**.

## Measured snapshot 2026-06-21 (consolidated v9 `_index`, prd, central-element-323112)

| AG | MTDS rows | MTDS v9% | MTDS honest-cov% | MTDS capture (cap/empty/failed/unattempted) | IS honest-cov% | LIVE rows |
|---|---|---|---|---|---|---|
| cefi | 3.87M | 96.6% | **33.9%** | 1.31M / 1.28M / **802k failed** / 482k | 99.9% | **0** |
| defi | 6.17M | 100% | **6.0%** | 369k / 3.48M / 6k / 2.31M | 100% | **0** |
| tradfi | 1.94M | 99.7% | **5.3%** | 103k / 1.01M / 10k / 818k | 96% (v9 only **46.6%**) | **0** |
| sports | 920k | 100% | **37.7%** | 346k / 574k / 164 / 0 | **15.9%** | **0** |
| pred | 42k | 96.5% | **40.5%** | 17k / 24.5k / 50 / 338 | 100% | **0** |

**Three structural facts:** (1) **LIVE = 0 rows on every AG** (MTDS+IS) — the live/forward pipeline has
never been populated; (2) low defi/tradfi % is mostly `expected_unattempted`+`empty_confirmed` (writer-
seeded honest absence — the unattempted cells need batch runs to convert to captured); (3) cefi carries
**802k `attempted_failed`** (needs re-fetch/diagnosis). Fleet was DRAINED at snapshot time (only
gas-fees + monitoring running) — nothing non-billing was driving to 100%.

## Path to 100% — per-AG launch matrix (the fleet)

Each batch backfill fills `expected_unattempted` → captured; each forward-poll starts the LIVE stream
(live accumulates from launch, continuously). Launch with per-VM T+10min verify (no fire-and-forget).

- [ ] [DATA] P0. **prediction** — Kalshi deep-history seed (bulk→canonical, IN FLIGHT: `mtds-prediction-kalshibulk-*`) + Polymarket batch re-fetch for `expected_unattempted` + `launch-prediction-forward-poll.sh` (LIVE). Repo: deployment-service.
- [ ] [DATA] P0. **defi** — `launch-defi-backfill-vm.sh` (fill 2.31M unattempted: gas-fees [running] + lst-rates + dex-pools/swaps + lending-indices + liquidations + vault-share + pyth) + `launch-defi-forward-poll.sh` (LIVE). Repo: deployment-service.
- [ ] [DATA] P0. **tradfi** — full 3-dataset batch (GLBX done via CME-b; **DBEQ.BASIC** `launch-tradfi-bf-nasdaq/nyse-ohlcv-1m.sh` + **CFE/XCBF**) to fill 818k unattempted + `launch-tradfi-forward-poll.sh` (LIVE). Repo: deployment-service.
- [ ] [DATA] P0. **sports** — `launch-mtds-sports-odds-backfill-vm.sh` + `launch-sports-is-gap-fill.sh` / `launch-sports-full-sweep-vm.sh` (IS sports 15.9%→100%) + `launch-footystats-forward-poll.sh` (LIVE). Repo: deployment-service.
- [ ] [DATA] P0. **cefi** — `launch-cefi-onchain-forward-poll.sh` + **`launch-cefi-forward-poll.sh` (LIVE Tardis — FREE, hook up)** + diagnose+re-fetch the 802k `attempted_failed`. **Batch Tardis (historical) EXCLUDED — billing-gated (operator).** Repo: deployment-service.
- [ ] [IS] P1. **IS tradfi v9 canonicalisation** — only 46.6% at schema_version=9; run the tradfi `_index` canonicalisation walk (8→9: source/asset_group/pipeline_mode) so the index is fully v9. Repo: instruments-service / market-tick-data-service.
- [ ] [DATA] P1. **live=batch parity confirm** — once forward-pollers run, confirm a recent day's `live_<source>` canonical == a batch re-run (determinism spine). Repo: market-tick-data-service.

## Autonomous loop (don't-stop-till-done)

Termination: per-AG MTDS honest-cov% → ~100% (modulo genuine `empty_confirmed` honest absence) AND
≥1 `live_<source>` row present per AG AND IS sports/tradfi v9 complete. Progress metric = per-AG
captured-row count climbing + `live_*` rows appearing. Monitor re-checks the consolidated `_index` per AG
each tick; relaunches any stalled/failed/terminated backfill VM; flat metric → diagnose (`run.log`), never
spin. Excluded from 100%: cefi batch-Tardis historical (billing).

## Codex SSOT updates
- [ ] [DOCS] P2. codex/02-data/availability-manifest-and-data-status.md — add the 2026-06-21 per-AG snapshot + the live-mode-population gap as a tracked baseline.

## Progress Log
### 2026-06-21 — snapshot measured + fleet launch begun
Coverage snapshot above (measured, not memory). Kalshi seed VM re-launched (runner set-u fix mtds@74e228c).
Fleet launch + monitoring loop starting (this plan is the path-to-100% plan-of-record).
