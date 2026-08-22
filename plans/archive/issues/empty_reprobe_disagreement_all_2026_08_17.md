---
doc_type: issue
title: Empty re-probe disagreements — today's new empties may be C1 bugs (2026_08_17)
summary: >-
  Daily data-pipeline empty re-probe audit (`reprobe_new_empty_confirmed.py`, Wave 4b Phase 5 scripted→LLM escalation
  hop) found cells across cefi/defi/prediction/sports/tradfi that became `empty_confirmed`+`SOURCE_RETURNED_ZERO` today
  where the UAC coverage oracle expected data or a wired re-fetch returned rows, plus ambiguous cells with no oracle/
  re-fetch signal. A non-empty ORACLE_EXPECTS_DATA/REPROBE_RETURNED_ROWS verdict is the operator's #1 failure class
  (C1) — a real-empty misclassified as honest-absence, i.e. a code bug not a true gap — and needs a worker to trace the
  adapter path and route to `record_failed`; AMBIGUOUS verdicts need judgment (real-gap vs new-venue) to extend the
  oracle.
status: resolved # corrected 2026-08-19, plan-reconcile observability_master: sole todo is [x] w/ HARD evidence
  # (market-tick-data-service@bf9fe5c4cc, verified ancestor of origin/live-defi-rollout) -- was stale "open"
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [empty-reprobe, honest-absence, c1-misclassified-empty, data-pipeline-audit, oracle-disagreement]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-17
parent_epic: observability_master
priority: P1
source: [reprobe_new_empty_confirmed.py, data_pipeline_hardening_self_monitoring_2026_06_22.md]
assigned_vm: planning
resolved_by: plan_reconciler 2026-08-19 (epic-scoped observability_master pass) — sole todo [x] w/ HARD evidence
locked_by:
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/tick_data_handler.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/sentinels.py,
    unified-api-contracts/unified_api_contracts/registry/expected_coverage.py,
  ]
author: reprobe_new_empty_confirmed.py (data-pipeline daily audit)
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

> **📦 ARCHIVED 2026-08-22 (archival pass 2)** — `locked_by: live-defi-rollout` placeholder cleared (corpus-wide
> fix, `scripts/plans/clear_locked_by_placeholder_2026_08_12.py --apply`); 0 open todos, `status: resolved`.
> Kept as a historical daily-monitor record.
# Empty re-probe disagreements — today's new empties may be C1 bugs (2026_08_17)

> Auto-filed by the daily data-pipeline audit `reprobe_new_empty_confirmed.py` (Wave 4b, Phase 5
> scripted→LLM escalation hop). A deterministic candidate list was non-empty — the
> verdicts below need a worker's judgment (real gap vs code bug, straggler
> vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily empty re-probe found cells that became empty_confirmed+SOURCE_RETURNED_ZERO today where the UAC coverage oracle SHOULD_HAVE_DATA (or a wired re-fetch returned rows), plus ambiguous cells. AGs: cefi, defi, prediction, sports, tradfi.

Candidate list(s) (deterministic, machine-written):

- `/app/unified-trading-pm/plans/audit/results/empty_reprobe_tradfi_2026_08_17.csv`

## Why it matters

This is the operator's #1 failure class (C1): a real-empty misclassified as honest-absence. An ORACLE_EXPECTS_DATA / REPROBE_RETURNED_ROWS verdict means the data exists but we recorded empty — a code bug, not a true gap. AMBIGUOUS verdicts need judgment (oracle silent + no re-fetch hook).

## Recommended decision

For each disagreement: trace the adapter path that recorded the empty and route it to record_failed (thread fetch_evidence per Phase 1). For ambiguous: decide real-gap vs new-venue, extend the oracle. Per data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 1/5.

Cold-start context: read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
in full + `/codex/05-infrastructure/data-pipeline-alerts.md` + the candidate CSV(s)
above before acting.

## Todos

- [x] ✅ [CODE] P1. Empty re-probe disagreements — today's new empties may be C1 bugs (2026_08_17) — diagnose + fix the root cause (misclassified-empty vs real gap, not-v9 schema row, or oracle-expects-but-empty divergence) in `market-tick-data-service`. Read `SUB_AGENT_MANDATORY_RULES.md` + the data-pipeline codex SSOT + the candidate CSV(s) above first (source `reprobe_new_empty_confirmed.py`). — market-tick-data-service@bf9fe5c4cc

## Progress Log

- 2026-08-17: Diagnosed the single tradfi candidate — `(CME, trades, 2026-08-17)`, verdict `ORACLE_EXPECTS_DATA`
  (`oracle SHOULD_HAVE_DATA (None) but cell is empty_confirmed`). Root cause: **misclassified-empty**, not a real gap
  or oracle-expects-but-empty divergence. CME is Databento-sourced (GLBX.MDP3) with the same T+1 archive-ingestion
  settlement lag as NASDAQ/NYSE (`tick_data_handler.py::_needs_full_day_elapsed` already gates ALL of TRADFI for
  this, not just NASDAQ/NYSE) — but the Tier-3 sentinel's delivery-lag classification branch
  (`sentinels.py::_emit_tier3_for_dt`) only recognized `{"NASDAQ", "NYSE"}`, so a same-day CME zero-row cell fell
  through to the permanent `SOURCE_RETURNED_ZERO` branch instead of `EXPECTED_SOURCE_DELIVERY_LAG`, which is exactly
  why the oracle (which has no same-day-not-yet-settled awareness) flagged it as a disagreement. Fix: widened the
  delivery-lag venue set to `{"NASDAQ", "NYSE", "CME", "CBOE"}` (CBOE is also Databento-sourced via XCBF.PITCH;
  ICE/FX/KRX/FRED deliberately excluded — not Databento-sourced per `expected_coverage.py`'s `_TRADFI` dict). Added
  a regression test (`test_tier3_cme_same_day_zero_row_stamps_delivery_lag_reason`) mirroring the existing
  HYPERLIQUID delivery-lag regression test. Shipped `market-tick-data-service@bf9fe5c4cc`; QG green
  (`bash scripts/quality-gates.sh --no-fix`, exit 0); ancestry-verified on `origin/live-defi-rollout`.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
