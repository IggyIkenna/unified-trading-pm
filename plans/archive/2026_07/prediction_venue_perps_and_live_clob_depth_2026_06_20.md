---
doc_type: plan
title: Kalshi + Polymarket perpetual futures + live CLOB depth/quotes (funding/basis/dispersion arb) — SPLIT 2026-07-24
summary: >-
  SUPERSEDED 2026-07-24 — split into 3 successor plans (parked KALSHI_PERP/POLYMARKET_PERP crypto-perps track / live
  CLOB-depth capture infra / cross-venue arb+coverage) per the plan line-cap remediation. All content (every todo + the
  full Progress Log) was moved verbatim into the successors; this file is retained frozen as the historical record and
  carries no open todos of its own.
status: superseded
nature: process
asset_group: [prediction, cefi]
stage: [meta]
repos:
  [agent-orchestrator, deployment-api, deployment-service, e2e-testing, features-service, fund-administration-service]
scope: [engineer, admin]
tags: [prediction, kalshi, polymarket, perps, clob, live-data, arb, funding-rate, basis, plan-split]
related:
  [
    plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
    plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    plans/active/prediction_perps_kalshi_polymarket_parked_2026_07_24.md,
    plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: 2026-06-20
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
  [
    prediction_perps_kalshi_polymarket_parked_2026_07_24,
    prediction_live_clob_depth_capture_2026_07_24,
    prediction_cross_venue_arb_and_coverage_2026_07_24,
  ]
depends_on:
source: >-
  Split per plans/active/issues/plan_line_cap_remediation_2026_07_23.md row 23 (2354 lines / 87 todos, HARD over the
  1000L line-cap) — operator approved unlocking `locked_by: live-defi-rollout` and a 3-way clean-partition, 2026-07-24.
assigned_role: data_engineering
drift_direction: advance-code
---

# Kalshi + Polymarket perps + live CLOB depth — SUPERSEDED (split 2026-07-24)

> **🟢 2026-07-24 — PLAN SPLIT (plan line-cap remediation, operator-approved unlock).** This plan grew to 2354 lines /
> 87 todos and was flagged by `scripts/plan-hygiene/check_line_caps.sh` as HARD over the 1000-line cap
> (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 23). The operator approved unlocking
> `locked_by: live-defi-rollout` and splitting this plan 3 ways along its natural topic boundaries. **All content (every
> todo + the full Progress Log) was moved VERBATIM — nothing was dropped or summarized** — into:
>
> 1. **`plans/active/prediction_perps_kalshi_polymarket_parked_2026_07_24.md`** — the parked KALSHI_PERP /
>    POLYMARKET_PERP crypto-perpetuals track (blocked per the 2026-07-14 operator ruling; cross-references, does not
>    duplicate, the actual Kalshi-perp-adapter repoint work tracked in
>    `plans/active/prediction_capture_incident_remediation_2026_07_06.md` Workstream B).
> 2. **`plans/active/prediction_live_clob_depth_capture_2026_07_24.md`** — the live+batch CLOB depth/quotes capture
>    infrastructure for the PREDICTION Kalshi/Polymarket YES-NO markets (WS connectors, transport/sink bugs, message-
>    shape fixes, live producer VM operations).
> 3. **`plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md`** — the cross-venue Kalshi↔Polymarket arb
>    detector, cqg canonicalization, the honest-coverage correctness chain, and historical backfill/manifest work.
>
> This file is retained (frozen) as the historical record of how the original single plan evolved; it carries no open
> todos of its own. Consult the 3 successor plans above for all current/open work and full evidence trails.

## What this plan originally covered

Operator 2026-06-20: Kalshi (May–Jun 2026, 13 CFTC crypto perps BTC+alts) and Polymarket (Apr 21 2026 beta,
crypto+stocks, 10–20x) both launched perpetual futures; add them to the crypto-perp universe for basis trades,
funding-rate arb, and cross-venue dispersion. Also: historical prediction data is trades-only, but live CLOB quotes +
depth can be recorded — capture + dump it live for proper arb backtesting. The plan grew over 5+ weeks (2026-06-20 →
2026-07-06) to cover the perps venue build, the full PREDICTION live/batch capture pipeline, and the downstream
cross-venue arb + honest-coverage correctness work — see the 3 successor plans above for the complete, verbatim history
(every todo, evidence block, and dated Progress Log entry).
