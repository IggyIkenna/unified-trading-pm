---
name: tradfi-master
slug: tradfi_master_2026_05_07
date: 2026-05-07
owner: claude-code
status: active
priority: P1
phase: pending_approval
domain: tradfi
asset_group: tradfi
type: umbrella
locked_by: live-defi-rollout
locked_since: 2026-05-07
folds_in:
  - instrument_schema_cohesion_and_market_hours_2026_03_31
  - sp500_ml_readiness_master_2026_05_05
  - cefi_tradfi_tick_data_backfill_2026_04_10 # TradFi half (CeFi half went to cefi_master)
  - market_tick_data_to_100pct_2026_05_05 # TradFi slice
related_plans:
  - master_to_live_defi_2026_05_23
  - writegate_honest_coverage_endtoend_2026_05_06
---

# TradFi Master — asset_group umbrella

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 18 of 18 unchecked todos
- **Mis-marked DONE → flipped**: 0
- **In-flight (running VMs)**: 5 VMs — `mdps-tradfi-2021/22/23/24/25-20260506-125828`, created 2026-05-06T05:00 UTC,
  T+22h, ETA 2026-05-08
- **Blocked by**: `cefi_master:24-VM drain` (shares MDPS pipeline ground-truth assertion);
  `writegate_honest_coverage_endtoend:Phase 2.A` (placeholder deletion for honest coverage % across MDPS — MDPS@e9520a0
  already migrated tradfi adapters off `_create_empty_output()`)
- **Blocks**: `master_to_live_defi_2026_05_23:G` (DART manual-trade gate; ML pipeline running on representative sample
  is a hard floor); does NOT block live trading per master plan ("batch-only this cutover cycle")
- **Last meaningful commit**: MDPS@`e9520a0` (Tier 2E tradfi adapters A/B/C migration off `_create_empty_output`);
  UAC@`121e6c5` (tradfi_symbology pure-calendar fallback for ES.OPT cluster activity); UAC@`198a39a` (export
  ES_OPTIONS_CLUSTERS + extract_es_options_cluster); UAC@`2a970c5` (non_trading_day_reason discriminator — TradFi
  calendar pre-skips emit EXPECTED_HOLIDAY/WEEKEND); strategy@`d7dad8d` (FUTURES_ROLL emission helper + 16 roll-boundary
  tests)
- **Recommendation**: KEEP ACTIVE. P1 priority is correct — TradFi is not on May 23 critical path for live trading. Most
  market-hours integration items remain (12 affected repos to QG-pass). 5 mdps-tradfi VMs running shapes 2024 + 2025
  fills; 2021/22/23 backfilling. Post-VM-drain (2026-05-08), run data-status rollup to confirm tradfi shards count vs
  expected. ES.OPT 2020-2022 ad-hoc backfill (line 110) needs ground-truth check via
  `gcloud compute instances list --filter='name~tradfi-bf-es-opt'`.

## Scope

Single source of truth for **TradFi asset_group** work. Per master plan asset-group readiness ladder, TradFi is
**batch-only this cutover cycle** (no live trading by 2026-05-23) but the ML pipeline must be **running on a
representative sample** so post-cutover archetype launches can flip live quickly.

Covers:

- **TradFi futures + ETFs + options** instrument coverage (CME ES/NQ/MES, CBOE VIX, NASDAQ ETFs, NYSE ETFs).
- **TradFi tick data backfill** (Databento + Barchart sources) to ≥99% coverage.
- **Market-hours + holiday calendar SSOT** integration end-to-end (instruments → MTDS → MDPS → features → ML +
  strategy + execution).
- **S&P 500 ML readiness**: ES futures continuous-series, VIX 15m + features, full backtest train/test split.
- **MTDS TradFi slice to ≥99%** (ETFs per-instrument; futures/options bundled by root).

**Not covered here**: live TradFi trading (out-of-cycle for May 23). DeFi / CeFi / Sports / Predictions live in their
respective umbrellas.

## Current state (2026-05-07)

- **Instrument schema cohesion + market hours** at 36/14 = 72% done. Open work concentrates in `data_filters.py`
  (replace hardcoded NYSE), mock_feature_generator (remove `_US_HOLIDAYS_2023`), and end-to-end pipeline runs.
- **S&P 500 ML readiness** at 13/15 = 87% done. Phase 1 backfill mostly shipped; continuous-series stitcher + VIX
  feature calculator + full backtest run pending.
- **CeFi+TradFi tick data backfill** at 15/24 = 62% done. TradFi half: CBOE VIX 15m wiring landed via VIX layering rule
  (CLAUDE.md); CME ES/MES backfill ongoing; ETF cleanup pending.
- **Per VIX 15m source layering rule** (CLAUDE.md): Barchart preload 2020-01-02 → 2025-11-12; Yahoo rolling 60-day for
  post-cutoff; honest gap 2025-11-13 → today−60d.

## Critical path

| Workstream                                | Status                                                                | Source                                         |
| ----------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------- |
| Market-hours + holiday SSOT integration   | 72% done                                                              | `instrument_schema_cohesion_and_market_hours`  |
| S&P 500 ML readiness backtest run         | 87% done; backtest pending                                            | `sp500_ml_readiness_master`                    |
| ES + MES + VIX backfill to ≥99%           | partial                                                               | `cefi_tradfi_tick_data_backfill` (TradFi half) |
| MTDS TradFi shards to ≥99%                | partial                                                               | `market_tick_data_to_100pct` (TradFi slice)    |
| ETF cleanup (NYSE / NASDAQ stale rows)    | post-MVP scope reduction                                              | `cefi_tradfi_tick_data_backfill`               |
| TradFi venue trading calendar consumption | per CLAUDE.md "TradFi futures: bundled, non-trading days pre-skipped" | shard-granularity SSOT                         |

## Consolidated todos (P0/P1 only)

### Market-hours + holiday SSOT integration (`instrument_schema_cohesion_and_market_hours`)

- [ ] [AGENT] P0. databento.py adapter: populate `pre_market_open_utc`, `post_market_close_utc`, `holiday_calendar` per
      TradFi instrument. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. `ml-training-service/app/core/data_filters.py`: replace `filter_market_hours()` hardcoded NYSE with
      `venue_trading_calendar` lookup. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. `ml-training-service/app/core/mock_feature_generator.py`: remove `_US_HOLIDAYS_2023` hardcoded
      holidays; consume `venue_trading_calendar` SSOT. [AUDIT 2026-05-07: FRESH — actionable; per MEMORY entry, this
      file has Harsh's pre-existing os.environ violation that masks downstream QG steps — coordinate]
- [ ] [AGENT] P0. Run `bash scripts/quality-gates.sh` on all 12 affected repos. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. Run instruments pipeline for all 3 categories (CEFI, DEFI, TRADFI) and verify: (a) all venues emit
      calendar fields, (b) no hardcoded holidays remain. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P1. `instrument_validation.py`: require `holiday_calendar` + `timezone` for TradFi instruments. [AUDIT
      2026-05-07: FRESH — actionable]
- [ ] [AGENT] P1. Add diagnostic: TradFi venue returning 0 rows on a trading day → WARN (potential upstream issue).
      [AUDIT 2026-05-07: FRESH — actionable; instruments-service@8b5eca3 Tier 2B already emits
      EXPECTED_WEEKEND/EXPECTED_HOLIDAY for non-trading-day pre-skips — extend to active-day-zero diagnostic]
- [ ] [AGENT] P1. Strategy base class config: `market_hours_only: bool = True` default for TradFi. [AUDIT 2026-05-07:
      FRESH — actionable]
- [ ] [AGENT] P1. Expiry guard: instrument `status=EXPIRED` or `expiry < now` → reject with reason. [AUDIT 2026-05-07:
      FRESH — actionable]
- [ ] [AGENT] P1. MTDS pipeline TradFi weekend date — verify NYSE / NASDAQ / CME skip with "market closed" log. [AUDIT
      2026-05-07: IN-FLIGHT verification — `mdps-tradfi-2021/22/23/24/25` VMs RUNNING (T+22h, ETA 2026-05-08); event
      stream + manifest will show pre-skip behavior post-drain]

**Acceptance**: MTDS skips closed TradFi markets; execution-service rejects TradFi orders on closed markets; ML training
reads `is_trading_day` from instruments (no hardcoded holidays); all 12 affected repos pass QG.

### S&P 500 ML readiness (`sp500_ml_readiness_master`)

- [ ] [AGENT] P2. Continuous-series stitcher for ES (rolled futures) — back-adjust for roll. [AUDIT 2026-05-07: FRESH —
      actionable]
- [x] [AGENT] P2. `FUTURES_ROLL` event emission in `strategy-service` ML engine on continuous-series roll. [AUDIT
      2026-05-07: DONE — strategy@d7dad8d (FUTURES_ROLL emission helper + 16 roll-boundary tests)]
- [ ] [AGENT] P3. Run `features-delta-one-service` for tradfi/ES across 36 calculators. [AUDIT 2026-05-07: FRESH —
      actionable]
- [ ] [AGENT] P3. Run `features-volatility-service` for tradfi/ES + tradfi/CBOE-VIX (realized-vol + skew). [AUDIT
      2026-05-07: FRESH — actionable]
- [ ] [AGENT] P3. VIX-specific feature calculator (level, contango proxy from VIX 1m vs 1h, momentum +
      volatility-of-volatility). [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P4. Smoke `ml-training-service` 1-month ES window; features land in feature store. [AUDIT 2026-05-07:
      FRESH — actionable]
- [ ] [AGENT] P4. Full backtest 2020-01-01 → 2024-12-31 (train) / 2025-01-01 → 2026-05-05 (test). OOS Sharpe + max
      drawdown + feature importance top-20. [AUDIT 2026-05-07: BLOCKED-ON tradfi_master:5-VM-drain (ETA 2026-05-08) and
      ML smoke above]
- [DEFERRED] Implied-vol skew from ES_OPT chain — gated on Phase 0 ES_OPT 2020-2022 backfill completion.
- [DEFERRED] VX futures term structure — gated on Databento CFE/VX support.
- [DEFERRED] S&P 500 constituent stocks — gated on canonical NASDAQ+NYSE equity backfill.
- [DEFERRED] MES options — gated on Databento MES options availability.

### CeFi+TradFi tick data — TradFi half (`cefi_tradfi_tick_data_backfill`)

- [ ] [AGENT] P0. Verify MTDS orchestrator handles CME via Databento and CBOE via Barchart for target data_types. [AUDIT
      2026-05-07: IN-FLIGHT — 5 mdps-tradfi VMs running; verify post-drain]
- [ ] [SCRIPT] P0. VM launch script for CBOE VIX backfill (ohlcv_15m, dates=2025-11-13→2026-04-10) — VIX layering per
      CLAUDE.md rule. [AUDIT 2026-05-07: STALE — VIX 15m source layering wired per MEMORY/CLAUDE.md (Yahoo rolling
      window + Barchart preload for 2020-01-02 → 2025-11-12); 17 days were filled manually 2026-05-06 per CLAUDE.md "VIX
      15m source layering" closeout. Re-verify the actual gap window; this todo may be effectively closed]
- [ ] [SCRIPT] P0. Run ES_OPT 2020-2022 fill VM `tradfi-bf-es-opt-adhoc-adhoc-20260505-183009` to completion. [AUDIT
      2026-05-07: STALE / DONE? — VM not in current `gcloud running` snapshot so it has either drained or been deleted;
      verify via manifest check (ES.OPT 18 single-parent fills was the original issue per CLAUDE.md "TradFi MVP
      partial-bundle"); UAC@198a39a + UAC@121e6c5 wired the cluster-coverage gate so re-runs correctly bundle-validate]
- [ ] [AGENT] P0. IBIT NASDAQ trades cold backfill — 31 rows all `empty_confirmed` from July 2024 only. [AUDIT
      2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. Port phantom-audit + manifest-rebuild scripts to TradFi (legacy disk path differs). [AUDIT 2026-05-07:
      FRESH — actionable; instruments-service `reconcile_phantom_manifest_rows_all.py --asset-group tradfi` per
      CLAUDE.md is multi-asset-group; needs per-tradfi axis verification (TradFi options 11-cluster taxonomy)]
- [ ] [AGENT] P2. Cleanup stale ETF rows: NYSE ETHE 27, GBTC 27, [other ETFs in MVP scope reduction]. [AUDIT 2026-05-07:
      FRESH — actionable]
- [ ] [AGENT] P2. Yahoo Finance manifest cleanup — 2,211 abandoned `empty_confirmed` rows under `venue=YAHOO_FINANCE`.
      [AUDIT 2026-05-07: FRESH — actionable]

### MTDS TradFi slice (`market_tick_data_to_100pct` — TradFi)

- [ ] [AGENT] P1. Per-venue completion %: CME ES, CME MES, CBOE VIX, NYSE ETFs, NASDAQ ETFs. Surface to deployment-ui.
      [AUDIT 2026-05-07: BLOCKED-ON tradfi_master:5-VM-drain (ETA 2026-05-08)]
- [ ] [AGENT] P1. After backfill VMs drain, run data-status rollup; confirm TradFi shards count vs expected. [AUDIT
      2026-05-07: BLOCKED-ON tradfi_master:5-VM-drain (ETA 2026-05-08)]

## Anti-patterns + workspace-rule cross-references

- **VIX 15m source layering** (CLAUDE.md): Barchart preload + Yahoo rolling + honest gap. MTDS routing in
  `umi_tick_provider.py` MUST short-circuit Barchart-window dates without calling Yahoo.
- **TradFi futures shard-key matrix**: bundled by root; non-trading days pre-skipped via `venue_trading_calendar` +
  recorded as `empty_confirmed`.
- **TradFi options 11-cluster taxonomy**: ES + E1A–E5A weeklies + EW1–EW4 + EOM. Cluster validation at `record_captured`
  per CLAUDE.md "Cluster validation MANDATORY" rule.

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.plan.md`](./master_to_live_defi_2026_05_23.plan.md).
- Sibling asset_group umbrellas: `cefi_master_2026_05_07`, `defi_master_2026_05_07`, `sports_master_2026_05_07`,
  `predictions_master_2026_05_07`.
- VIX 15m layering: CLAUDE.md "VIX 15m source layering" workspace-wide rule.
- Venue trading calendar: `unified_api_contracts.canonical.crosscutting.venue_trading_calendar`.

## Folded plans (archived 2026-05-07)

- `instrument_schema_cohesion_and_market_hours_2026_03_31.plan.md` — market-hours SSOT integration; P0 todos lifted.
- `sp500_ml_readiness_master_2026_05_05.plan.md` — ES + VIX + ML pipeline; remaining work lifted.
- `cefi_tradfi_tick_data_backfill_2026_04_10.plan.md` (TradFi half) — CeFi half went to `cefi_master`.
- `market_tick_data_to_100pct_2026_05_05.plan.md` (TradFi slice) — full plan archived after split per asset_group.
