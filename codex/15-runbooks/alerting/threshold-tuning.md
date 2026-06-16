---
scope: [engineer, admin]
title: Alerting Threshold Tuning
status: active
created: 2026-05-07
updated: 2026-05-07
authoritative_for:
  How alert thresholds are set, who owns each threshold, when they get reviewed. Avoids the "alert on a number nobody
  can defend" failure mode that produces noise + alert fatigue. Phase 1 (UAC SSOT + 10 seed thresholds) shipped
  UAC@d00326d.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/alert-code-taxonomy.md
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/rehearsal-procedure.md
---

# Alerting Threshold Tuning

> **Status:** ACTIVE — Phase 1 (UAC `ALERT_THRESHOLDS` registry with 10 seed values + explicit units) shipped 2026-05-07
> at UAC@d00326d. Phase 7 (quietness baseline) tunes the values against 48-hour live data; Phase 8 (rehearsal) validates
> pages fire correctly.

> **Severity vocabulary SSOT** — when a threshold is paired with a `severity=AlertSeverity.<MEMBER>` declaration, see
> [`README.md` § Severity glossary](README.md#severity-glossary) for the canonical CRITICAL / HIGH / WARN / INFO ↔
> PagerDuty P0 / P1 / P2 / P3 ↔ routing mapping. Phase 5's "Deploy in WARNING-only mode" step uses `AlertSeverity.WARN`
> (per the glossary) — once the threshold is tuned the rule's severity moves up to HIGH or CRITICAL per the rule owner's
> call.

## Purpose

Every alert threshold answers a question: "above what value does this become important?" Wrong thresholds either page
the operator on noise (alert fatigue) or fail to page on a real incident. This doc is the SSOT for how thresholds get
set, who owns them, and when they get re-tuned.

## Where thresholds live

The `ALERT_THRESHOLDS` registry is in
[`unified_api_contracts/canonical/crosscutting/alerting/thresholds.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/thresholds.py),
re-exported through `unified_api_contracts.ALERT_THRESHOLDS`. Each entry is an immutable `AlertThreshold` dataclass
with:

- `key: str` — the canonical lookup name. AlertRule references via `threshold_key`.
- `unit: ThresholdUnit` — explicit unit (`BPS_OF_ONE` / `RATIO` / `USD` / `MINUTES` / `COUNT_PER_MINUTE`). Resolves the
  "is 9500 95% or 95bp?" ambiguity at the type level.
- `default_value: Decimal` — the workspace default.
- `per_archetype_overrides: dict[str, Decimal]` — strategy-archetype-keyed overrides;
  `for_archetype("leveraged_funding_arb")` returns the override or falls back to default.
- `source_doc: str` — citation for the value (link to plan, codex doc, audit ID, external URL).
- `description: str` — operator-facing one-liner.

Construction is `frozen=True` — runtime mutation is impossible; updates ship via UAC commit.

## Initial seed values (Phase 1, 2026-05-07)

| Key                                    | Unit               | Default | Per-archetype override              | Source                                                                                                          |
| -------------------------------------- | ------------------ | ------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `defi_health_factor_critical`          | `RATIO`            | 1.05    | —                                   | Aave V3 docs HF<1 → liquidation; 5% buffer matches industry tools (Tenderly, Hypernative, Gauntlet).            |
| `defi_weeth_depeg_bps`                 | `BPS_OF_ONE`       | 50      | —                                   | weETH historical max depeg ≈ 30 bps; 50 bps catches abnormal events without firing on chop.                     |
| `defi_aave_utilization_spike_bps`      | `BPS_OF_ONE`       | 9500    | `leveraged_funding_arb`: 9000 (90%) | Aave V3 InterestRateStrategy `optimalUsageRatio=0.95 RAY` for WETH/USDC/USDT/DAI — the rate-curve "kink".       |
| `defi_funding_rate_flip_bps_5m`        | `BPS_OF_ONE`       | 100     | —                                   | 1.00% APR funding flip in 5min → regime change for `leveraged_funding_arb`.                                     |
| `defi_feature_stale_minutes`           | `MINUTES`          | 15      | —                                   | LST yields update on epoch boundary (Solana ≈12min, Ethereum ≈12sec); 15min is generous lower bound.            |
| `balance_drift_usd`                    | `USD`              | 1000    | —                                   | Operator-confirmed acceptable noise for the initial wallet (Phase 4 operator action: confirm post-funding).     |
| `order_rejection_spike_per_min`        | `COUNT_PER_MINUTE` | 10      | —                                   | Sub-noise vs typical CeFi exchange reject rate; spike == venue health degradation.                              |
| `margin_threshold_breach_bps`          | `BPS_OF_ONE`       | 200     | —                                   | 2.00% buffer from initial-margin-call line; per-venue overrides via `per_archetype_overrides` (broker-defined). |
| `position_drift_bps`                   | `BPS_OF_ONE`       | 100     | —                                   | 1.00%-from-target rebalance trigger; common industry standard for portfolio-drift monitoring.                   |
| `cross_cloud_egress_bytes_per_request` | `USD`\*            | 1048576 | —                                   | Audit 2026-05-07 dual-cloud-active: any single dashboard request >1 MiB across cloud boundaries is a bug.       |

\* `cross_cloud_egress_bytes_per_request` reuses the `USD` unit as a budget proxy (1 byte ≈ negligible USD). A dedicated
`BYTES` unit could be added in v2 if more byte-budget thresholds appear.

## Setting a new threshold

1. **Identify the question** — "above what value does X become important?" If you can't answer, stop — the alert isn't
   ready.
2. **Pick the unit explicitly** — bps_of_one, ratio, USD, minutes, count_per_minute. Add a new `ThresholdUnit` member if
   none fits. Never collapse units to `Decimal` ambiguously.
3. **Start with a percentile of healthy historical observation** — p99 of normal-mode behaviour is a safe default;
   tighten via Phase 7 quietness baseline.
4. **Validate via backtest replay** — replay 30-90 days of historical events through the proposed threshold; count
   would-be alerts; classify true vs false positives.
5. **Deploy in WARNING-only mode for one week** (`severity=AlertSeverity.WARN`, `channels=(AlertChannel.TELEGRAM,)`) —
   pages off, just notifications.
6. **Promote to PAGE** when false-positive rate is < 5% per 24h.

## Re-tuning

A false-positive cluster triggers a re-tune. Process:

1. Owner reviews the cluster (timestamp, code, severity, payload, was-it-real?).
2. Owner proposes a new value with evidence (historical-data link, formula, citation).
3. UAC PR updates `default_value` (or `per_archetype_overrides`) — same PR may also update the `source_doc` citation.
4. Test suite re-runs; if `tests/internal/unit/test_alerting_taxonomy.py` passes, merge.
5. Owner annotates the threshold's `source_doc` with the quietness-baseline date the new value was tuned against.

## Per-archetype overrides

`AlertThreshold.per_archetype_overrides` is a dict keyed by strategy archetype slug. `for_archetype(archetype)` returns
the override or falls back to the registry default.

Live example (shipped Phase 1): `defi_aave_utilization_spike_bps` defaults to 9500 (95.00%) but `leveraged_funding_arb`
overrides to 9000 (90.00%) — the funding-arb archetype's borrow-spread alpha erodes faster than carry's, so it wants an
earlier signal.

`alerting-service/alerting_service/rules/defi_rules.py:check_aave_utilization` accepts an optional `archetype` parameter
that flows through to the override lookup.

## Backtest / replay tooling

> **[DELTA 2026-05-22]** **Current state:** No automated backtest/replay tooling — Phase 7 of
> `plans/active/alerting_service_live_rules_2026_05_07.md` not yet shipped. Threshold changes are manually validated via
> ad-hoc historical queries. **Planned delta:** `alerting-service/scripts/replay_threshold.py` ships as part of Phase 7
> (quietness baseline). **Target:** Every threshold change validated against 30-90 day replay before merge.

Post-cutover (Phase 7) — not yet implemented. Recommended shape:

```python
from unified_api_contracts import ALERT_THRESHOLDS

threshold = ALERT_THRESHOLDS["defi_health_factor_critical"]
historical_events = load_historical_hf_observations(since="2025-01-01")
would_be_alerts = [
    e for e in historical_events
    if e.health_factor < threshold.for_archetype(e.archetype)
]
print(f"would_be_alerts={len(would_be_alerts)}, true_positives={...}")
```

Phase 7 ships this as `alerting-service/scripts/replay_threshold.py`.

## Alert-fatigue ratchet

If a code generates >10 false positives per 24-hour window during Phase 7 quietness baseline, the threshold is
auto-flagged for review. Threshold-research sub-agent (planned in
[`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md)) proposes a
tightened value with citation; operator approves before merge.

## Cross-references

- **Plan(s) implementing this:**
  [`alerting_service_live_rules`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
- **Related codex SSOTs:** [`alert-code-taxonomy`](./alert-code-taxonomy.md),
  [`operator-playbook`](./operator-playbook.md), [`rehearsal-procedure`](./rehearsal-procedure.md).
- **Code:** UAC `unified_api_contracts.ALERT_THRESHOLDS` + `unified_api_contracts.AlertThreshold`
  - `unified_api_contracts.ThresholdUnit`.

## Open questions

- Do we ship a "shadow" alerting mode (compute the threshold, log the would-be alert, don't page) for new codes? Yes —
  recommended for first week of every new code (currently informal; Phase 7 scripts make it formal).
- How do we A/B-test threshold changes safely in production? Recommend: shadow new threshold + diff the would-be alerts
  vs current production for one week.
- Should owners be individuals or rotations? Recommend: rotations for cross-archetype, individual for single-strategy.
  Owner field not yet in the dataclass — add via `owner: str` field in v2.
