---
title: Pre-audit — strategy repo consolidation (risk-and-exposure, position-balance-monitor, pnl-attribution → strategy-service)
created: 2026-05-19
author: slot-3
source:
  - plans/active/strategy_repo_consolidation_2026_05_19.md
locked_by: live-defi-rollout
---

## What I found

Pre-audit inventory of stale references to archived strategy repos across the workspace before consolidation.

Archived services: `risk-and-exposure-service`, `position-balance-monitor-service`, `pnl-attribution-service`
Consolidated into: `strategy-service`

## Why it matters

Phase -2 Bucket 3 cleanup — stale service names in consumer repos (alerting-service, trading-agent-service,
system-integration-tests, e2e-testing) must be replaced before downstream imports or service discovery fails.

## Recommended decision

Execute Phase 11f (Bucket 3) stale-ref sweep across all consumer repos per the strategy_repo_consolidation plan.
