---
doc_type: issue
title: venue_e2e_wiring's 5 AG batches need re-scoping from the 353-pair denominator to the shipped 660-triple axis
summary: >-
  Operator-authorized follow-up (BLK-f87a4927, answered B, 2026-08-19T18:46:58Z): venue_e2e_wiring_2026_08_16.md's
  5 dependent AG batch plans (defi/cefi/sports/tradfi/prediction venue_e2e_batch1) were scoped and largely executed
  against a 353 (venue, data_type)-pair denominator, superseded 2026-08-17 by a shipped, operator-ruled
  unified-api-contracts@d19866d339 (660 (venue, instrument_type, data_type) triples, 12 cells unresolved). The
  operator explicitly chose NOT to disturb the 5 in-flight/already-archived AG batches — this doc tracks the
  separate re-derivation work instead.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [venue-readiness, denominator-drift, re-scoping, plan_reconciler]
related:
  [
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/nick_ai_platform_readiness_remediation_finalize_2026_08_16.md,
  ]
created: "2026-08-19"
author: plan_reconciler
source: agt-b2fcb2
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    unified-api-contracts/scripts/generate_venue_universe_denominator.py,
    unified-api-contracts/scripts/generate_venue_work_list.py,
  ]
---

# venue_e2e_wiring — re-scope the 5 AG batches from 353 pairs to 660 triples

## Why this exists

`venue_e2e_wiring_2026_08_16.md` (P0) walks the Venue Readiness Contract per unit, forked into 5 AG batch plans
(`defi_venue_e2e_batch1_2026_08_16` 200 rows, `cefi_venue_e2e_batch1_2026_08_16` 70, `sports_venue_e2e_batch1_2026_08_16`
31, `tradfi_venue_e2e_batch1_2026_08_16` 16, `prediction_venue_e2e_batch1_2026_08_16` 4 — defi/cefi/tradfi/prediction
already archived done, sports still active) — all scoped against **353 `(venue, data_type)` pairs** from
`VENUE_DATA_TYPE_CAPABILITIES`.

That denominator was superseded 2026-08-17: `unified-api-contracts@d19866d339` shipped the instrument_type axis,
re-measuring the real unit as **660 `(venue, instrument_type, data_type)` triples** (12 cells unresolved, 3.4%) —
see `nick_ai_platform_readiness_remediation_finalize_2026_08_16.md`'s 2026-08-18 Progress Log entry. Flagged live in
`venue_e2e_wiring_2026_08_16.md` with a staleness banner (`unified-trading-pm@c0ca00144f`, 2026-08-19).

**Operator ruling (`BLK-f87a4927`, answered `B`, 2026-08-19T18:46:58Z)**: leave the 5 AG batches
running/closed against the old 353-pair model as-is — do not disturb in-flight or already-archived dispatch work.
This doc is the "separate follow-up plan" the operator's answer explicitly called for, to close the 353→660 gap
independently rather than reopening the 4 already-archived batches.

## Todos

- [ ] [DIAG] P1. Re-run (or write, if it doesn't yet exist) the 660-triple equivalent of
      `unified-api-contracts/scripts/generate_venue_work_list.py` against
      `unified-api-contracts@d19866d339`'s instrument_type axis, and diff the resulting row set against the union
      of all 5 AG batches' already-closed/open todos (321 mapped + 32 `UNMAPPED` rows under the old 353-pair model).
      Definition of done: a concrete delta list — which of the new 660 triples have NO corresponding closed work
      under the old 353-pair sweep — cited by (venue, instrument_type, data_type), not just a count.
- [ ] [BACKEND] P2. For every delta row identified above, decide whether it's covered implicitly by existing
      per-venue wiring (the instrument_type axis may already be satisfied as a side effect of the (venue,
      data_type)-level work) or is genuinely new, undone work — record the verdict per row, not just in aggregate.
- [ ] [BACKEND] P2. For rows confirmed genuinely new/undone, fork a fresh AG-scoped dispatch batch (mirroring the
      `<ag>_venue_e2e_batch2_2026_08_19`-style naming the original 5 batches used) per affected asset_group, citing
      this doc + the delta list as its source.
- [ ] [DOC] P3. Once every delta row is either covered-confirmed or forked into a fresh batch, update
      `venue_e2e_wiring_2026_08_16.md`'s staleness banner to point here as the closed-out remediation record, and
      correct its own "353"/"192 declared venues" prose to the 660-triple figures for future readers.

## Progress Log

- **2026-08-19T18:47Z**: filed by `plan_reconciler` (dispatch `agt-b2fcb2`, cross-cutting tranche) applying the
  operator's `BLK-f87a4927` answer (B). No re-derivation attempted here — that is real engineering work (estimate
  class `research`), out of this run's own remit (detect/verify/route, not execute multi-AG re-scoping).
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, batch 3/3): RECLASSIFY (whole-doc), `assigned_vm: NA
  → planning`. All 4 open todos are sequential, procedural follow-through on an already-decided operator ruling
  (`BLK-f87a4927`, answered B) — re-run/write a diff script with a precisely-stated done-when (a concrete delta list
  by triple, not a count), record a per-row coverage verdict, fork fresh AG batches for confirmed-new rows, update
  a banner — no further design/judgment call remains open. Conflict-check: `venue_e2e_wiring_2026_08_16.md`
  (`assigned_vm: planning`) already explicitly cross-references this doc as the separate follow-up tracking the
  353→660 gap and does not itself re-attempt the re-derivation — no duplicate coverage found.
