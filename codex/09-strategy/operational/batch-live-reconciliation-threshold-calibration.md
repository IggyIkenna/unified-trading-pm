---
scope: [engineer, admin]
---

# Batch-Live Reconciliation — Threshold Calibration Analysis

## Purpose

This document specifies the **smoke reconciler pass/fail criteria** for the F21 batch-live reconciliation service
(`batch-live-reconciliation-service`) and defines the calibration procedure for refining thresholds during the 7-day
paper-soak (Tab 8 of `batch_live_symmetry_2026_05_10.md`).

**Written pre-soak so the Tab 6 + Tab 8 agents have unambiguous pass/fail criteria when the paper VM comes online.**
Read this before executing Tab 6 P0 (paper-mode smoke) or Tab 6 P1 (7-day soak calibration).

---

## SSOT for threshold values

```python
# unified_api_contracts/canonical/crosscutting/alerting/thresholds.py
RECON_GREEN_THRESHOLDS: Final[dict[str, dict[str, Decimal]]] = {
    "carry_staked_basis": {
        "bps_delta_max": Decimal("50"),    # P&L delta gate
        "drawdown_pct":  Decimal("2.0"),   # intraday drawdown gate
        "fill_rate_min": Decimal("0.95"),  # fill execution gate
    },
    "leveraged_funding_arb": {
        "bps_delta_max": Decimal("75"),
        "drawdown_pct":  Decimal("3.0"),
        "fill_rate_min": Decimal("0.92"),
    },
}
```

These are the **operative** thresholds. All calibration updates must land here — never hard-code values in service code.
When the values change, bump UAC version + update `source_doc` in the `AlertThreshold` docstring.

---

## The three pass/fail gates

### Gate 1 — P&L delta (`bps_delta_max`)

**Formula**: `|batch_pnl - live_pnl| / live_pnl_notional > bps_delta_max / 10000`

- **Measured per trade** in `stage3_execution_recon.py` (`alpha_pnl_gap_bps`).
- **Aggregated daily**: if any single-trade breach exceeds threshold, the reconciler emits `BATCH_VS_LIVE_RECON_DRIFTED`
  for that archetype + date.
- **Alert levels**:
  - `WARNING`: any single-trade `alpha_pnl_gap_bps` ∈ [1×, 2×) threshold
  - `CRITICAL`: any single-trade `alpha_pnl_gap_bps` > 2× threshold → PagerDuty + Telegram

**Why these starting values?**

The 50/75 bps defaults are the **95th-percentile backtest bid/ask spread for each archetype plus 2× expected slippage
margin** (derivation: 2-year daily backtest delta distribution, aggregated per archetype):

| Archetype               | Venues                            | 95p spread est. | 2× slippage margin | Starting `bps_delta_max` |
| ----------------------- | --------------------------------- | --------------- | ------------------ | ------------------------ |
| `carry_staked_basis`    | LST/AAVE/CEX spot + perp (3 legs) | ~25 bps         | ~25 bps            | 50 bps                   |
| `leveraged_funding_arb` | Multi-venue CEX perp (5+ venues)  | ~35 bps         | ~40 bps            | 75 bps                   |

The wider margin for `leveraged_funding_arb` reflects higher path variance from multi-venue execution (cancel + retry
risk on any one leg shifts realized vs simulated P&L more).

### Gate 2 — Intraday drawdown (`drawdown_pct`)

**Formula**: `(peak_nav - current_nav) / peak_nav > drawdown_pct / 100`

- **Measured end-of-day** by `stage4_risk_recon.py` (or equivalent).
- **Purpose**: catch cases where batch-simulated trades were systematically more profitable than live, indicating
  simulation bias rather than stochastic noise.
- **Values** anchored to 2-year backtest 95p intraday drawdown + 2× margin:
  - `carry_staked_basis`: 2.0% (LST carry is low-vol; 2% breach = outlier drift, not normal chop)
  - `leveraged_funding_arb`: 3.0% (multi-venue spread has higher intraday volatility)

### Gate 3 — Fill rate (`fill_rate_min`)

**Formula**: `fills_executed / fills_intended ≥ fill_rate_min`

- **Measured per day** by the execution stage.
- **Purpose**: detect systematic fill failures in live that aren't replicated in batch simulation.
- **Values**:
  - `carry_staked_basis` 0.95: LST venues (Lido/RocketPool/Binance) have tight queues; <95% fill rate = venue issue, not
    expected slippage
  - `leveraged_funding_arb` 0.92: multi-venue hedges occasionally cancel on one leg; 0.92 gives 8% cancel headroom while
    catching systematic issues

---

## Pre-soak smoke criteria (before 7-day soak data available)

Run the reconciler against the **2-yr backtest output** (Tab 8 Step 1 VM) using these **STRICT pre-soak pass criteria**:

| Gate            | Pre-soak pass threshold                                | Rationale                                |
| --------------- | ------------------------------------------------------ | ---------------------------------------- |
| `bps_delta_max` | ≤ `RECON_GREEN_THRESHOLDS[archetype]["bps_delta_max"]` | Use defaults until live data available   |
| `drawdown_pct`  | ≤ `RECON_GREEN_THRESHOLDS[archetype]["drawdown_pct"]`  | Same                                     |
| `fill_rate_min` | ≥ `RECON_GREEN_THRESHOLDS[archetype]["fill_rate_min"]` | Backtest fill rate should be near 1.0    |
| Alert rate      | ≤ 2 `BATCH_VS_LIVE_RECON_DRIFTED` events per day       | Risk #3 mitigation: no false-alarm storm |

A backtest run that passes these criteria is sufficient to declare the reconciler **structurally sound** (the pipeline
computes correct deltas and emits events at the right threshold). Threshold tightening happens in soak.

**If pre-soak smoke fails**: diagnose in this priority order:

1. `fill_rate_min` fail → check execution stage fill-count logic vs backtest fill manifest
2. `bps_delta_max` fail on >50% of backtest dates → simulation bias (batch uses mid-price; live uses mark) → fix fill
   price source, not the threshold
3. `bps_delta_max` fail on <5% of dates → noise; threshold is OK, widen 10 bps and note in UAC docstring

---

## 7-day soak calibration procedure (Tab 6 P1)

Once Tab 8 Step 4 paper-VM is running and emitting live fills:

### Day 1-3: collect distribution

Each morning, run:

```bash
cd batch-live-reconciliation-service
# NOTE: analysis.threshold_distribution module not yet built (BLRS audit 2026-05-27, G5). Correct package path below.
python3 -m batch_live_reconciliation_service.analysis.threshold_distribution \
    --archetype carry_staked_basis \
    --start-date $(date -v-3d +%Y-%m-%d) \
    --end-date $(date +%Y-%m-%d)
```

Record the **observed daily P&L delta 95th percentile** + **max drawdown** + **min fill rate** in the calibration ledger
table below.

### Day 3: interim assessment

If observed 95p delta is:

- **≤ 0.7× current `bps_delta_max`**: threshold is conservative. Tighten to 95p_observed + 15% buffer after Day 7.
- **0.7×–1.0×**: threshold is well-calibrated. No change unless Day 7 shows persistent pattern.
- **> 1.0× current `bps_delta_max`**: threshold is too tight OR simulation bias detected. Investigate + widen to
  `95p_observed × 1.2` immediately (don't wait for Day 7). File P0 issue, do NOT widen silently.

### Day 7: final recalibration

Collect the full 7-day distribution. For each archetype and each gate:

```
new_bps_delta_max  = ceil(percentile_95(observed_alpha_pnl_gap_bps) * 1.2)
new_drawdown_pct   = ceil(max(observed_drawdown_pct) * 1.2, 1 decimal place)
new_fill_rate_min  = floor(min(observed_fill_rate) * 0.99, 2 decimal places)
```

The 1.2× buffer on `bps_delta_max` / `drawdown_pct` gives a 20% margin above observed worst-case. The 0.99 floor on
`fill_rate_min` keeps a tight SLO while allowing for one-off infra glitch.

After computing new values:

1. Update `RECON_GREEN_THRESHOLDS` in UAC `thresholds.py`.
2. Bump UAC minor version.
3. Update `source_doc` in the `AlertThreshold` docstring to reference calibration date + observed distribution summary.
4. Flip Tab 6 P1 checkbox in `batch_live_symmetry_2026_05_10.md`.

### Calibration ledger (fill in during soak)

| Date | Archetype               | 95p delta (bps) | Max drawdown (%) | Min fill rate | Verdict      |
| ---- | ----------------------- | --------------- | ---------------- | ------------- | ------------ |
| TBD  | `carry_staked_basis`    | —               | —                | —             | PENDING soak |
| TBD  | `leveraged_funding_arb` | —               | —                | —             | PENDING soak |

---

## Alert suppression during soak

During the 7-day soak window, `CRITICAL` → PagerDuty alerts are **suppressed** to avoid on-call noise while calibrating.
`WARNING` → Telegram alerts remain active (informational). Suppression MUST be a typed config field on `ReconConfig`
(not `os.getenv` — the workspace bans environment reads in service code):

```python
# batch-live-reconciliation-service/batch_live_reconciliation_service/config.py
class ReconConfig(UnifiedCloudConfig):
    soak_mode: bool = False  # suppress CRITICAL→PagerDuty during 7-day soak; WARNING→Telegram stays on
```

> **NOT YET BUILT** (BLRS audit 2026-05-27, G4): `soak_mode` is not implemented in `ReconConfig` or the orchestrator.
> When built, set it via the config layer for the soak window, then back to `false` (default) after Day-7 calibration.

---

## Decision authority

| Decision                                  | Who decides                             |
| ----------------------------------------- | --------------------------------------- |
| Widen threshold by ≤ 20% after soak       | Agent (update UAC + flip P1 checkbox)   |
| Widen threshold by > 20% before soak ends | Operator sign-off required              |
| Narrow threshold below current defaults   | Agent (always safe — more conservative) |
| Skip 7-day soak entirely                  | Operator explicit [ack] required        |

---

## SSOT pointers

- Threshold dict: `unified_api_contracts/canonical/crosscutting/alerting/thresholds.py` `RECON_GREEN_THRESHOLDS`
- Reconciler engine: `batch-live-reconciliation-service/engine/orchestrator.py`
- Alert rule: `alerting-service/alerting_service/rules/reconciliation_rules.py`
- Parent plan: `plans/active/batch_live_symmetry_2026_05_10.md` § Tab 6 (P0 smoke + P1 7-day calibration)
- Pre-audit risk §6 #3: `plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md`
