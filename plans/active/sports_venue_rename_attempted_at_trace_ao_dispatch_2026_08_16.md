---
doc_type: plan
title: Trace which renamed sports venue keys absorbed pre-clobber snapshot rows (Track O follow-on)
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 10) — dispatch
  sports_track_o_attempted_at_keys_extinct_2026_08_14.md's DIAG P2 todo as-is. The original Track O repair todo
  (sports_consolidated_closeout_2026_07_19.md) targeted venue IN (BETFAIR, MATCHBOOK, PINNACLE), data_type='trades'
  — a dry-run join found 0 live matches: BETFAIR was split into BETFAIR_SB_UK/_EX_EU/_EX_UK by a later
  venue-taxonomy migration, and live data_type='trades' now belongs only to venue=ODDS_API. Trace which renamed
  venue(s) actually absorbed the pre-clobber snapshot's rows before any repair write is designed.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [sports, manifest, attempted_at, venue-rename, track-o]
related:
  [
    /plans/active/issues/sports_track_o_attempted_at_keys_extinct_2026_08_14.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
effort: max
drift_direction: none
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 10, 2026-08-16"
locked_by:
context_scope:
  [
    /plans/active/issues/sports_track_o_attempted_at_keys_extinct_2026_08_14.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
locked_since:
resolved_by:
---

# Trace which renamed sports venue keys absorbed pre-clobber snapshot rows

## Todos

- [ ] [DIAG] P2. Trace which renamed venue(s) (`BETFAIR_SB_UK`/`BETFAIR_EX_EU`/`BETFAIR_EX_UK`, and
      MATCHBOOK/PINNACLE's current `trades`-equivalent) absorbed the pre-clobber snapshot's rows — check
      `sports_taxonomy_p2_migration_2026_08_08.md` and Track C's footystats/casing work for the split mechanism.
      Re-run the pre-clobber-snapshot join (both base and full production dedup key, `_dedup_key_sql`-normalized)
      against the renamed keys to determine whether the `attempted_at` clobber defect persists under the new
      names. If it does, re-target the repair (CAS write, no consolidator pause needed — already resolved). If
      the 2026-06-21 true-value window has no live counterpart at all, close as moot. Report into
      `sports_track_o_attempted_at_keys_extinct_2026_08_14.md`'s Progress Log. Repos: market-tick-data-service,
      unified-trading-library.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 10, operator ruling)**: extracted from
  `sports_track_o_attempted_at_keys_extinct_2026_08_14.md` for AO dispatch, since the parent doc stays
  `assigned_vm: NA`.
- **context-scout 2026-08-17**: refreshed context_scope (3 entries) -- added
  `sports_consolidated_closeout_2026_07_19.md`, the confirmed owner of "Track C" (the split mechanism this doc's own
  todo says to check), named but not linked in the todo's own prose.
