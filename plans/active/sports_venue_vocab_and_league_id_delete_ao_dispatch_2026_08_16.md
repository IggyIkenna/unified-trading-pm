---
doc_type: plan
title: Sports Track C venue-vocab cleanup dispatch + Track V league_id delete live-writer check
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 4) — two items from
  sports_consolidated_closeout_2026_07_19.md: dispatch Track C's venue-vocabulary cleanup
  (LADBROKES_UK->LADBROKES, SPORT888->BET888SPORT re-stamps, KALSHI/POLYMARKET purge) trusting
  current dispositions, and run a fresh live-writer check on the raw-keyed league_id population
  BEFORE Track V's 5-part-proof-gated DELETE fires, given a sibling doc found a live writer
  re-contaminating a different league-vocabulary population as recently as 2026-08-10.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [sports, canonicalization, venue, league_id, gcs-delete]
related:
  [/plans/active/sports_consolidated_closeout_2026_07_19.md]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 4, 2026-08-16"
locked_by:
context_scope:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
locked_since:
resolved_by:
---

# Sports Track C venue-vocab cleanup + Track V league_id delete live-writer check

## Todos

- [ ] [DATA] P2. Execute Track C's venue-vocabulary cleanup (`sports_consolidated_closeout_2026_07_19.md`):
      LADBROKES_UK->LADBROKES, SPORT888->BET888SPORT re-stamps, and the KALSHI/POLYMARKET purge. Operator ruled
      2026-08-16: trust the current dispositions, no fresh reconfirmation needed despite the doc's history of
      casing/vocabulary reversals — dispatch directly. (repo: market-tick-data-service)
- [ ] [DATA] P1. Before Track V's 5-part-proof-gated DELETE of the old raw-keyed `league_id` GCS objects fires, run a
      fresh live-writer check on THIS population specifically — confirm no live writer is still emitting the
      raw-keyed form. A sibling doc found a live writer re-contaminating a DIFFERENT league-vocabulary population as
      recently as 2026-08-10, so this class of bug is active in this codebase right now; do not assume the existing
      5-part proof already covers a writer that started contaminating after that proof was last run. Only once this
      check comes back clean does Track V's existing delete proceed under its own gate. (repos: instruments-service,
      market-tick-data-service)

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 4, operator ruling)**: extracted from
  `sports_consolidated_closeout_2026_07_19.md`. Track V's underlying 5-part-proof-gated delete is unchanged by this
  plan — only the pre-check is new.
