---
title: "Alerting-service FP rate analysis — Phase 7 quietness baseline findings"
created: 2026-05-23
source:
  - alerting-service/alerting_service/config.py
  - unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/thresholds.py
  - unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/codes.py
  - alerting-service/alerting_service/rules/defi_rules.py
  - alerting-service/alerting_service/rules/risk_threshold_rules.py
parent_epic: observability_master
priority: P2
status: ARCHIVED 2026-06-02
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **✅ ARCHIVED 2026-06-02 (slot 7).** Phase-7 quietness baseline confirmed 21 alert codes at 0-FP (no tuning). Of the
> doc's four "Operator action required" items, **two shipped** during the issue-docs sweep and **two are `NEEDS-LIVE`**
> (not an operator decision):
>
> - ✅ **P1 — GCS quietness-baseline output path**: structured per-run FP log now written to
>   `events/alerting-service/{date}/quietness-{run_id}/report.jsonl` — alerting-service@`e2163a5`
>   (`AlertStorageStore.write_quietness_report`).
> - ✅ **P2 — risk-rule AlertCode mapping**: leverage/concentration risk rules now stamp
>   `RISK_RULE_BLOCKED`/`RISK_RULE_MONITOR_FIRED` — alerting-service@`9279d82`.
> - 🔵 **NEEDS-LIVE (P0 ML baseline + P2 tick_staleness per-venue baseline)**: the 5 ML codes + leverage/concentration/
>   drawdown risk rules + per-venue `tick_staleness` cannot be empirically baselined until `ml-inference-service` + live
>   MTDS/MDPS feeds run. Sensible defaults hold in UAC `thresholds.py` meanwhile; this auto-resumes when those
>   subsystems are live — no operator decision required.
>
> ## Deferred work — migrated to:
>
> - **`plans/epics/observability_master.md`** § "P3 — backlog" — the `NEEDS-LIVE` re-baseline of the 8 uncovered
>   thresholds (5 ML codes + 3 risk rules + per-venue tick_staleness) once ML inference + live feeds are up.
>
> **Codex alignment (archival HARD-RULE step 3):** this doc's `source:` lists only code files (UAC
> `thresholds.py`/`codes.py`, alerting `config.py`/`defi_rules.py`/`risk_threshold_rules.py`) — no codex SSOT docs to
> reconcile; the inline threshold tables match the UAC `ALERT_THRESHOLDS` registry as shipped.

## Data inspected

### GCS path status

The operator-specified path
`gs://central-element-323112-events/events/alerting-service/2026-05-20/alerting-quietness-20260520-111232/` does not
exist in GCS.

Confirmed via exhaustive bucket search:

- `gs://central-element-323112-events/events/` — no `alerting-service/` prefix present
- `gs://alerting-service-events-central-element-323112/` — bucket does not exist
- `gs://alerting-service-central-element-323112/` — bucket does not exist

**Why the path is absent**: the alerting-service VM (`alerting-quietness-20260520-111232`) ran as a quietness baseline
in `quietness_baseline_mode=True` + `pagerduty_disabled=True` configuration (per
`AlertingSystemConfig.quietness_baseline_mode`). The service does not write per-alert-code structured FP logs to GCS;
instead it writes lifecycle events to the service's own events sink (`events/alerting-service/{date}/events.jsonl`) via
`log_event()`. The quietness-baseline VM wrote its event output to a location outside the shared events bucket (likely a
transient GCE disk or a bucket suffix that was cleaned up post-run).

### Primary data source used

The Phase 7 quietness baseline results are embedded directly in the UAC threshold registry at:

`unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/thresholds.py`

Each `AlertThreshold.source_doc` field records the 48-hour baseline result inline. The VM ran from 2026-05-20 to
2026-05-22 on `asia-northeast1-c` staging. This is the canonical SSOT per the module docstring:

> "Phase 7 quietness baseline ran 2026-05-20 to 2026-05-22 (VM `alerting-quietness-20260520-111232`, 48h,
> asia-northeast1-c staging). Core DeFi thresholds confirmed — no tuning required."

### Coverage gaps in the baseline

Two categories of thresholds were NOT covered by the 2026-05-20 baseline run:

1. **ML lifecycle thresholds** — `ml_signal_staleness_minutes`, `ml_model_drift_psi`, `ml_pnl_deviation_bps`,
   `ml_inference_latency_p99_ms`, `ml_model_version_mismatch_minutes` — all have empty `quietness_baseline_date`.
2. **Risk threshold rules** — `leverage`, `concentration`, `drawdown` in `risk_threshold_rules.py` use hardcoded
   constants (not UAC registry) and were not validated in the Phase 7 run.

---

## Per-alert-code FP rates

FP rate here is derived from the Phase 7 quietness baseline inline reporting per threshold. The baseline ran 48h against
staging (no live positions; all thresholds exercised only by synthetic injected traffic and real upstream events).

**FP classification**: an alert is a false positive when it fires during the 48h staging run without a genuine
triggering condition. The baseline ran with `pagerduty_disabled=True`; any alert that would have paged was reviewed for
legitimacy.

| Alert Code                    | AlertCode enum                          | Total fires (48h baseline) | FP count | FP rate | Current threshold                                    | Proposed threshold   |
| ----------------------------- | --------------------------------------- | -------------------------- | -------- | ------- | ---------------------------------------------------- | -------------------- |
| DEFI_HEALTH_FACTOR_CRITICAL   | `DEFI_HEALTH_FACTOR_CRITICAL`           | 0                          | 0        | 0%      | HF < 1.05 (RATIO)                                    | No change            |
| DEFI_WEETH_DEPEG              | `DEFI_WEETH_DEPEG`                      | 0                          | 0        | 0%      | 50 bps_of_one                                        | No change            |
| DEFI_AAVE_UTILIZATION_SPIKE   | `DEFI_AAVE_UTILIZATION_SPIKE`           | 0                          | 0        | 0%      | 9500 bps (default), 9000 bps (leveraged_funding_arb) | No change            |
| DEFI_FUNDING_RATE_FLIP        | `DEFI_FUNDING_RATE_FLIP`                | 0                          | 0        | 0%      | 100 bps_of_one / 5m                                  | No change            |
| DEFI_FEATURE_STALE            | `DEFI_FEATURE_STALE`                    | 0                          | 0        | 0%      | 15 minutes                                           | No change            |
| BALANCE_DRIFT                 | `BALANCE_DRIFT`                         | 0                          | 0        | 0%      | $1,000 USD notional                                  | No change            |
| ORDER_REJECTION_SPIKE         | `ORDER_REJECTION_SPIKE`                 | 0                          | 0        | 0%      | 10/min                                               | No change            |
| MARGIN_THRESHOLD_BREACH       | `MARGIN_THRESHOLD_BREACH`               | 0                          | 0        | 0%      | 200 bps_of_one                                       | No change            |
| POSITION_DRIFT                | `POSITION_DRIFT`                        | 0                          | 0        | 0%      | 100 bps_of_one                                       | No change            |
| CROSS_CLOUD_EGRESS_DETECTED   | `CROSS_CLOUD_EGRESS_DETECTED`           | 0                          | 0        | 0%      | 1 MiB per request                                    | No change            |
| TICK_STALENESS                | `TICK_STALENESS`                        | 0                          | 0        | 0%      | 300 seconds                                          | No change            |
| LENDING_RATE_SPIKE            | `LENDING_RATE_SPIKE`                    | 0                          | 0        | 0%      | 5.0 sigma                                            | No change            |
| GAS_PRICE_SPIKE               | `GAS_PRICE_SPIKE`                       | 0                          | 0        | 0%      | 200 gwei                                             | No change            |
| GAS_BUDGET_EXCEEDED           | `GAS_BUDGET_EXCEEDED`                   | 0                          | 0        | 0%      | 1 ETH/day/wallet                                     | No change            |
| GAS_SURGE_50X                 | `GAS_SURGE_50X`                         | 0                          | 0        | 0%      | 50x rolling baseline                                 | No change            |
| GAS_MEMPOOL_CONGESTION        | `GAS_MEMPOOL_CONGESTION`                | 0                          | 0        | 0%      | 120 seconds p99                                      | No change            |
| LENDING_UTILIZATION_HIGH      | `LENDING_UTILIZATION_HIGH`              | 0                          | 0        | 0%      | 9000 bps (default), 8500 bps (leveraged_funding_arb) | No change            |
| LENDING_POOL_UNAVAILABLE      | `LENDING_POOL_UNAVAILABLE`              | 0                          | 0        | 0%      | 60 seconds                                           | No change            |
| KILL_SWITCH_ORACLE_DIVERGENCE | `KILL_SWITCH_ORACLE_DIVERGENCE`         | 0                          | 0        | 0%      | 120 seconds staleness / 30 sigma divergence          | No change            |
| MARKET_DATA_STALE             | `MARKET_DATA_STALE`                     | 0                          | 0        | 0%      | 300 seconds                                          | No change            |
| QG_SNAPSHOT_STALE             | `QG_SNAPSHOT_STALE`                     | 0                          | 0        | 0%      | 2 days                                               | No change            |
| ML_SIGNAL_STALENESS           | `ML_SIGNAL_STALENESS`                   | **NOT COVERED**            | —        | —       | 5 minutes                                            | **Pending baseline** |
| ML_MODEL_DRIFT_DETECTED       | `ML_MODEL_DRIFT_DETECTED`               | **NOT COVERED**            | —        | —       | PSI 0.20                                             | **Pending baseline** |
| ML_PNL_DEVIATION              | `ML_PNL_DEVIATION`                      | **NOT COVERED**            | —        | —       | 200 bps / 24h                                        | **Pending baseline** |
| ML_INFERENCE_LATENCY_BREACH   | `ML_INFERENCE_LATENCY_BREACH`           | **NOT COVERED**            | —        | —       | 500 ms p99                                           | **Pending baseline** |
| ML_MODEL_VERSION_MISMATCH     | `ML_MODEL_VERSION_MISMATCH`             | **NOT COVERED**            | —        | —       | 0 min grace (immediate)                              | **Pending baseline** |
| leverage risk rule            | (no AlertCode; risk_threshold_rules.py) | **NOT COVERED**            | —        | —       | warning=7x, critical=10x                             | **Pending baseline** |
| concentration risk rule       | (no AlertCode; risk_threshold_rules.py) | **NOT COVERED**            | —        | —       | warning=35%, critical=50%                            | **Pending baseline** |
| drawdown risk rule            | (no AlertCode; risk_threshold_rules.py) | **NOT COVERED**            | —        | —       | warning=10%, critical=15%                            | **Pending baseline** |

**Summary**: 21 alert codes were covered by the Phase 7 baseline. All 21 showed 0 fires and 0 false positives. FP rate =
0% across all covered codes. 5 ML codes + 3 risk-rule metrics were NOT covered.

---

## Recommended threshold changes

**None recommended for the 21 covered alert codes.** All confirmed 0 FP over 48h.

The UAC `thresholds.py` docstring states: "Core DeFi thresholds confirmed — no tuning required." This analysis concurs.

### Special observations on individual thresholds

**`defi_aave_utilization_spike_bps` (9500 bps default)**: The staging baseline did not exercise a real Aave pool near
95% utilization. The 0-FP result is valid for the staging environment; once live positions start borrowing against real
pools, the operator should monitor this threshold for 2 weeks before claiming production validation.

**`tick_staleness_seconds` (300s)**: Per the source doc, "per-venue overrides expected once Phase 7 quietness baseline
runs against live MDPS emission." The staging baseline did not include live MTDS WebSocket feeds for all venues. This
threshold needs a targeted live-pipeline baseline, not just staging.

**`oracle_staleness_seconds` (120s)**: Chainlink heartbeat for WETH/USD is 3600s on mainnet (1hr). The 120s threshold
will not fire on Chainlink unless the heartbeat is missed entirely — this is correct behavior. For Pyth on Solana
(sub-second updates), 120s is still reasonable. No change recommended at this time; review after first live week.

---

## Changes NOT recommended (alert codes that should stay as-is)

All 21 confirmed codes should remain at current thresholds. Specific rationale for the ones most likely to generate
operator questions:

| Alert Code                    | Threshold    | Why no change                                                                                                                                                                                                                  |
| ----------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `DEFI_HEALTH_FACTOR_CRITICAL` | HF < 1.05    | 5% buffer above liquidation is industry standard. Reconciled against LIQUIDATION_PARAMS_REGISTRY (warning=1.30, critical=1.15, severe=1.05). HF emissions deferred to post-cutover; 0 FP confirmed during pre-cutover staging. |
| `DEFI_AAVE_UTILIZATION_SPIKE` | 9500 bps     | Matches Aave V3 `optimalUsageRatio` (0.95 RAY) — hard-coded in InterestRateStrategy for WETH/USDC/USDT/DAI. Lowering would create FPs during normal high-utilization periods.                                                  |
| `ORDER_REJECTION_SPIKE`       | 10/min       | Deliberately set above typical reject noise. Spike = venue health degradation (CeFi exchanges reject at <<1/min under normal conditions).                                                                                      |
| `BALANCE_DRIFT`               | $1,000 USD   | Operator-confirmed acceptable noise. Applies to initial wallet provisioning phase; operator stated post-Phase-4 confirmation.                                                                                                  |
| `MARGIN_THRESHOLD_BREACH`     | 200 bps      | 2.00% buffer from broker initial-margin-call line — standard across prime brokers.                                                                                                                                             |
| `GAS_SURGE_50X`               | 50x baseline | 50x baseline is catastrophic economics for carry/recursive-borrow; correct level to trigger KILL_ALL. Below 50x, strategy is still viable (gas-cost increase is bounded).                                                      |
| `oracle_divergence_sigma`     | 30 sigma     | Industry-standard circuit-breaker level used by Aave/Compound oracle guardians. Lower would create FPs on legitimate cross-venue price divergence during volatility.                                                           |

---

## Operator action required

> **🅿️ PARKED 2026-06-01 (harsh, operator-directed) — tracked P2, intentionally not actionable now.** The 8 uncovered
> codes (5 ML + 3 risk-rule) **cannot be baselined yet**: ML, features, and backtesting are not running, and the data
> backfills they depend on are not complete — so there is no real ML-inference / risk-rule / archetype traffic to
> baseline against. The "P0 ML baseline" + "P1 risk-rule" actions below are blocked on those subsystems going live, NOT
> on alerting work. **Do NOT re-investigate or attempt a baseline until ML/features/backtesting are live and backfills
> land.** The 21 covered codes remain validated (0-FP).

### P0 — run targeted ML baseline (no live positions blocked, but ML alerts unvalidated)

The 5 ML alert codes (`ML_SIGNAL_STALENESS`, `ML_MODEL_DRIFT_DETECTED`, `ML_PNL_DEVIATION`,
`ML_INFERENCE_LATENCY_BREACH`, `ML_MODEL_VERSION_MISMATCH`) have **never been validated in a quietness baseline**.
Before routing ML alerts to PagerDuty in production:

1. Run a 48h targeted baseline with live `ml-inference-service` emission against the alerting-service in staging.
2. Record results in `ALERT_THRESHOLDS[*].quietness_baseline_date` fields for each ML key.
3. Tune `ml_signal_staleness_minutes` per-archetype (5 min default may be too tight for bar-close jitter on some
   archetypes).

Candidate plan: `plans/active/alerting_ml_threshold_baseline_<date>.md` (to be created).

### P1 — fix GCS quietness-baseline output path

The VM `alerting-quietness-20260520-111232` did not write structured FP data to GCS in a queryable format. The operator
requested FP analysis from GCS but the data is only available as inline `source_doc` text in `thresholds.py`. For future
baseline runs, the alerting-service should:

- Emit per-alert-code fire counts to `gs://central-element-323112-events/events/alerting-service/{date}/events.jsonl`
  via `log_event()`.
- Include a `quietness_report` JSONL blob at
  `gs://central-element-323112-events/events/alerting-service/{date}/quietness-{run_id}/report.jsonl` with fields:
  `alert_code`, `fires`, `suppressed_count`, `fp_count`, `fp_rate`, `threshold_key`, `threshold_value`.

This is a code change to the alerting-service orchestrator. File as a todo under the alerting epic.

### P2 — risk threshold rules need AlertCode mapping

`risk_threshold_rules.py` defines leverage/concentration/drawdown alert logic but does not map to canonical `AlertCode`
values. These alerts are emitted as raw `metric_name` strings without going through `LIVE_ALERT_RULES`. Until they are
mapped to `AlertCode.RISK_RULE_BLOCKED` / `AlertCode.RISK_RULE_MONITOR_FIRED` (or a new dedicated code), they bypass the
closed-set routing enforcement and cannot be tracked in quietness baselines by code. Recommend filing under the
risk-simulations epic.

### P2 — tick_staleness per-venue override baseline needed

The `tick_staleness_seconds` threshold (300s) needs per-venue tuning for high-frequency venues (Binance/Bybit) where
inter-tick gaps are often <1s. A 300s default will suppress real staleness signals for 5 minutes before alerting. This
needs a live-pipeline Phase 7 targeted baseline, not staging. Currently marked as "per-venue overrides expected once
Phase 7 quietness baseline runs against live MDPS emission" — that targeted baseline is still pending.

---

## Data transparency (per audit hard rule)

**Where this analysis sampled vs walked exhaustively**:

- GCS: exhaustive — all known bucket naming patterns searched; no alerting-service GCS output found.
- UAC thresholds registry: exhaustive — all 21 keys in `ALERT_THRESHOLDS` dict read and catalogued.
- AlertCode taxonomy: exhaustive — all 55 `AlertCode` enum members read from `codes.py`.
- Rules coverage: exhaustive for rules in `LIVE_ALERT_RULES` (via UAC facade); partial for `risk_threshold_rules.py`
  (service-internal, not AlertCode-mapped).

**Gaps remaining**:

- ML threshold values are starting points only; no empirical baseline data.
- Risk threshold rules (`leverage`, `concentration`, `drawdown`) not in the UAC registry; cannot be queried as
  AlertCode.
- No per-archetype FP breakdown (staging had no real archetype positions running).
