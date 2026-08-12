---
doc_type: issue
title: instruments-service QG RED — FOOTYSTATS overlaps UAC sports venues, golden EXPECTED matrix drift
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [qg-red, sports, footystats, golden-fixture, uac-invariant, duplicate]
related: [/plans/archive/issues/instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md]
created: "2026-07-30"
author: unknown
assigned_vm: planning
parent_epic: sports_master
superseded_by: instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30
resolved_by:
source: >-
  Discovered while shipping todo 1 of /plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_2026_07_30.md (a DeFi
  instruments-service task, unrelated to sports) — full `quality-gates.sh` run surfaced 2 pre-existing RED tests,
  verified byte-identical on a clean `git stash` tree at LDR HEAD `cccc6ef5` before this session's DeFi diff.
summary: >-
  SUPERSEDED — duplicate discovery of the same instruments-service QG-RED blocker (FOOTYSTATS violates the IS/UAC
  sports-venue disjointness invariant + a golden-fixture drift) already filed, more completely, in the archived
  `instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md`; kept for corpus trail only, do not dispatch its
  todos.
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

> **🗄️ ARCHIVED 2026-08-12 (/plan-reconcile, operator ruling)** — superseded + zero real remaining work was deliberately
> kept unarchived "for the corpus trail"; operator ruled to archive now like any other superseded doc rather than
> special-case it indefinitely.

> **SUPERSEDED** — duplicate discovery of the same repo-blocker (RB-ecfc50de), filed minutes before slot-11's
> independent, more complete report which already identifies the exact root-cause commit
> (`unified-api-contracts@26092ac8`). See
> `/plans/archive/issues/instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md` for the authoritative
> version + tracked todos. This doc is kept for the corpus trail only — do not dispatch its todos below (they duplicate
> that doc's).

## What I found

`bash scripts/quality-gates.sh` on `instruments-service` fails 2 tests, both pre-existing (reproduced on a clean stash
of LDR HEAD, unrelated to any DeFi/adapter work):

1. `tests/unit/test_orchestrator_helpers.py::TestVenueProducerUACInvariant::test_sports_exempt_is_disjoint_from_uac_sports`
   — `AssertionError: IS sports and UAC sports must be disjoint (two-registry model): overlap={'FOOTYSTATS'}`. IS's
   `get_venues_for_asset_groups(["SPORTS"])` and UAC's `VENUES_BY_ASSET_GROUP["sports"]` are supposed to be disjoint
   sets by design (Decision C, operator 2026-06-29: IS sports = reference-data providers; UAC sports = market-data/odds
   venues) — `FOOTYSTATS` now appears in both.
2. `tests/unit/scripts/test_expected_universe_golden.py::TestGoldenByteIdentical::test_expected_matches_golden[sports]`
   — golden fixture drift: `golden=27, actual=31`, 4 extra `(venue, data_type, shard)` tuples: `BET888SPORT`,
   `FOOTYSTATS`, `LADBROKES`, `SMARKETS` (all `odds`/`trades`).

Both point at the same root cause: UAC's sports venue registry (`VENUES_BY_ASSET_GROUP["sports"]`) picked up
`BET888SPORT` / `FOOTYSTATS` / `LADBROKES` / `SMARKETS` since the golden fixture was last regenerated, and `FOOTYSTATS`
specifically collides with IS's own reference-provider registry (`FOOTYSTATS` is one of IS's sports reference-data
adapters — see `factory._ADAPTERS["footystats"]`), violating the disjoint two-registry invariant.

## Why it matters

This is a QG-blocking RED on `instruments-service` — any worker shipping ANY change through this repo's
`quality-gates.sh` (regardless of what they're actually working on) hits these 2 failures and cannot get a green
sentinel, per the HARD RULE "commit only from a `quality-gates.sh`-green tree." Declaring a repo-blocker so the
backend's `RepoHealthWatcher` tracks resolution and un-sticks waiters.

## Recommended decision

Two real options, an operator/data-engineering call (not picked here — outside this session's DeFi-adapter scope):

1. **If the 4 new UAC sports venues are intentional** (a real onboarding of BET888SPORT/LADBROKES/SMARKETS as odds
   venues + FOOTYSTATS legitimately needing dual roles): regenerate the golden fixture per its docstring recipe, AND
   resolve the `FOOTYSTATS` disjointness violation — either by giving IS's reference-provider role a distinct venue
   spelling from UAC's odds-venue `FOOTYSTATS`, or by widening the disjointness invariant's documented exemption (like
   the existing sports-exempt carve-out) if dual-role venues are now an intended pattern.
2. **If this is accidental UAC registry drift** (e.g. a recent UAC commit widened `VENUES_BY_ASSET_GROUP["sports"]`
   without the corresponding IS-side reconciliation): revert/scope the UAC addition instead.

## Todos

Superseded — the tracked, dispatchable todos for this finding live in
`/plans/archive/issues/instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md`, not here (kept as plain
bullets, not checkboxes, so backlog regen does not double-dispatch this duplicate):

- Diagnose which UAC commit introduced BET888SPORT/FOOTYSTATS/LADBROKES/SMARKETS into `VENUES_BY_ASSET_GROUP["sports"]`
  — ALREADY ANSWERED by the superseding doc: `unified-api-contracts@26092ac8`.
- Resolve the `FOOTYSTATS` IS/UAC disjointness violation (`test_sports_exempt_is_disjoint_from_uac_sports`).
- Regenerate/reconcile the sports golden EXPECTED-matrix fixture (`test_expected_matches_golden[sports]`).
