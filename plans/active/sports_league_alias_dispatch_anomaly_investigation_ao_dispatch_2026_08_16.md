---
doc_type: plan
title: Investigate sports league-alias dispatch anomalies (SEGUNDA_DIVISION→LA_LIGA_2 and similar) as a bounded, separate root-cause
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 9): investigate the league-alias dispatch
  anomaly SEPARATELY from the league-vocabulary contamination Big Finding (both docs' contamination is real, but
  the operator wants the root cause of the dispatch behavior confirmed independently before assuming they share
  a fix). Measured 2026-08-10 (sports-drop-stale dry-run, canonical-migration VM
  canonical-migration-sports-drop-stale-20260810-100832): 42,920 raw SKIPs in the twin-coverage gap are dominated
  by FOOTYSTATS-sourced batch_footystats raw odds whose computed batch_odds_api canonical twin is absent
  (15,981) plus various batch_odds_api venue-trades objects (MATCHBOOK/PINNACLE/BETFAIR/DRAFTKINGS...) including
  league-alias dispatch anomalies e.g. SEGUNDA_DIVISION→LA_LIGA_2 — flagged there as "worth investigating as
  possible dispatch bugs, not just missing twins," never actually investigated as its own item.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, unified-api-contracts]
scope: [engineer]
tags: [sports, dispatch, league-alias, root-cause, twin-coverage]
related:
  [
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    /plans/active/sports_satellite_ao_dispatch_batch12_2026_08_09.md,
    /plans/archive/2026_08/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-20"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
effort: max
drift_direction: none
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 9, 2026-08-16 — operator ruling: investigate separately from Big Finding #3"
locked_by:
context_scope:
  [
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    /plans/active/sports_satellite_ao_dispatch_batch12_2026_08_09.md,
    /plans/archive/2026_08/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md,
  ]
locked_since:
resolved_by:
---

# Investigate sports league-alias dispatch anomalies

## Todos

- [ ] [DATA] P2. **Root-cause the league-alias dispatch anomaly (SEGUNDA_DIVISION→LA_LIGA_2 and similar) found in the 2026-08-10 sports-drop-stale dry-run's no-twin population**, as a bounded step SEPARATE from Big Finding
      #3's league-vocabulary contamination (`sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`).
      Determine: is this a real DISPATCH BUG (the writer routes SEGUNDA_DIVISION-labeled odds under a
      LA_LIGA_2-keyed canonical path or vice versa, producing a spurious no-twin SKIP), or is it purely the
      SAME dual-registration root cause as Big Finding #3 (UAC registers both SEGUNDA_DIVISION and LA_LIGA_2, so
      the "gap" is an artifact of which alias a given writer happened to use)? Report the finding into both
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`'s twin-coverage discussion
      and `sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`'s Progress Log — do not assume
      the connection either way. This is a bounded measurement (sample the affected objects, trace the writer
      code path), not a design decision. Repos: market-data-processing-service, unified-api-contracts.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 9, operator ruling)**: extracted as a standalone
  investigation per operator's explicit choice to NOT assume the same root cause as Big Finding #3.
- **context-scout 2026-08-17**: populated context_scope (3 entries) — re-verified all 3 resolve; a fingerprint grep on
  this doc's cited VM name (`canonical-migration-sports-drop-stale-20260810-100832`) and its measured counts
  (42,920 / 15,981) confirms both other matching docs (`sports_satellite_ao_dispatch_batch12_2026_08_09.md`,
  `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`) are already in this list.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
