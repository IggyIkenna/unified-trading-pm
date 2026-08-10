---
doc_type: issue
title: >-
  API-Football sports completion campaign residual: ~976-object tail (fresh 2026-08-10 re-census) has no tracked owner —
  the re-census gate in sports_af_full_entity_completion_2026_08_03.md is parked pending ~0, but no todo runs the
  residual completion pass.
summary: >-
  Slot 25's 2026-08-10 re-census of the 8 in-scope AF entities found a ~976-object residual tail (was 146,640):
  PLAYER_STATS 3 · INJURIES 334 · STANDINGS 271 · TEAMS 96 · FIXTURE_STATS 136 · FIXTURE_LINEUPS 136, ~all
  `expected_unattempted`/absent tail, 19 TEAMS `attempted_failed`. The completion campaign's P0 re-census gate
  (`sports_af_full_entity_completion_2026_08_03.md`) is durably PARKED by slot 25 because its done-when (~0 needed) is
  unmet — but the residual pass that would actually close the tail was only a prose recommendation in that doc's
  Progress Log, never a tracked todo. This issue owns the completion pass so the campaign can genuinely converge and the
  re-census gate can then pass + the AF plan downgrade.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [sports, api-football, backfill, completion, data-correctness]
related: [/plans/active/issues/sports_af_full_entity_completion_2026_08_03.md]
created: "2026-08-10"
author: main agent (agt-fe67fd) — routing the slot-25 re-census residual (2026-08-10)
source: sports_af_full_entity_completion_2026_08_03.md slot-25 re-census progress entry (2026-08-10)
resolved_by:
locked_by:
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: data_engineering
drift_direction: advance-data
depends_on: []
---

## Todos

- [ ] [SCRIPT] P1. **Residual completion pass — close the ~976-object tail** (fresh 2026-08-10 re-census, slot 25):
      PLAYER_STATS 3 · INJURIES 334 · STANDINGS 271 · TEAMS 96 · FIXTURE_STATS 136 · FIXTURE_LINEUPS 136 = ~976 (was
      146,640); ~all `expected_unattempted`/absent tail, 19 TEAMS `attempted_failed`. Launch the `af-backfill-*`
      residual pass (`--entity` per remaining non-zero entity, respecting the `af-backfill-*`/`af-audit-*` singleton
      lock — one `af-backfill-*` VM at a time against the shared API key, self-check the lock before launching),
      resuming from each entity's `PROGRESS.json` checkpoint where present. Done when: a fresh re-census shows every
      in-scope entity at ~0 needed (only genuine honest-absence floors remain, e.g. FIXTURE_EVENTS' ~1,943-stub
      pattern), i.e. the re-census gate in `/plans/active/issues/sports_af_full_entity_completion_2026_08_03.md` can
      pass. Then unpark/flip the re-census condition (`auto_unpark__sports_af_full_entity_completion-9798da269f23`) so
      it dispatches and closes that doc. (repo: instruments-service / market-tick-data-service)

## Progress Log

- **2026-08-10 (main agent, agt-fe67fd)**: Filed this doc to give the slot-25 re-census residual an owner. The re-census
  task `sports_af_full_entity_completion-9798da269f23` is durably parked (cooldown GATED + prereq
  `auto_unpark__...-9798da269f23`=0, set_by slot-25 2026-08-10 09:51:52) and correctly so — its done-when (~0) is unmet.
  But nothing tracks the ~976-object completion pass itself; this doc owns it. Fleet impact of leaving it unowned: the
  parked re-census is the top idle-blocker-inferred source (17 events) holding ~270 downstream tasks.
