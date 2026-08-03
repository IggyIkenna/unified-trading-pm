---
doc_type: issue
title: >-
  sports_reference_v2_1492_row_canonical_copy_2026_08_03.md directs copying pre-floor data to canonical — contradicts
  the ratified sports-2020-06 data-floor SSOT (same operator, same population class, already wiped elsewhere)
summary: >-
  Dispatched task sports_reference_v2_1492_row_canonical_copy-002 ("copy the 1,492 confirmed rows to canonical storage")
  traces back to plan_reconcile_parked_operator_decisions_2026_08_02.md § 1b, option B ("resolve the 1,492 rows first
  (copy to canonical)"), operator-confirmed 2026-08-03. That option was never cross-checked against
  /codex/02-data/sports-2020-06-data-floor.md — the SAME operator's 2026-07-21 ruling that "every sports artifact dated
  before 2020-06-06 is fabrication-by-construction" and must be WIPED (delete), NOT backfilled. The floor doc records
  the wipe as ALREADY DONE for the canonical entity-equivalent population (`sports_reference/fixtures` 4,735 objects,
  `sports_reference/by_date` 398,240 objects) — proving FIXTURES-type pre-floor data does not get a "historical fact"
  exemption. The 1,492 sports_reference_v2/by_date/ rows (days 2018-01-02..2020-05-25) are the same
  fabrication-by-construction category, just under a v2-staging prefix the original wipe campaign didn't reach
  (confirmed in sports_legacy_duplicate_triage_2026_07_22.md §2, whose own §7 todo 1 recommendation was to fold them
  into the pre-floor-wipe scope — i.e. DELETE — not preserve them). Executing the copy task as literally worded would
  write 1,492 rows of fabrication-by-construction data into live canonical storage, reversing the intent of an
  already-executed operator-authorised wipe campaign. NOT executed pending operator reconfirmation.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [sports, data-floor, delete-safety, ssot-contradiction, canonical-copy, big-finding]
related:
  [
    /codex/02-data/sports-2020-06-data-floor.md,
    /plans/active/issues/sports_reference_v2_1492_row_canonical_copy_2026_08_03.md,
    /plans/active/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md,
    /plans/active/issues/sports_legacy_duplicate_triage_2026_07_22.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: none
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Worker slot 15, task sports_reference_v2_1492_row_canonical_copy-002 (backend/data_engineering), 2026-08-03 —
  surfaced before executing the copy."
---

# sports_reference_v2 1,492-row copy contradicts the ratified pre-floor wipe policy

## What I found

Task `sports_reference_v2_1492_row_canonical_copy-002` (todo 2 of
`/plans/active/issues/sports_reference_v2_1492_row_canonical_copy_2026_08_03.md`) instructs: "Copy the confirmed rows to
canonical storage (the same target path/schema the rest of the sports corpus already uses)." That doc's own `source:`
field traces it to `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 1b, option B — **operator- confirmed
2026-08-03** ("resolve the 1,492 rows (copy to canonical) first, then the two todos revert to self-justified").

Cross-checking against `/codex/02-data/sports-2020-06-data-floor.md` (authoritative, `status: current`, the SAME
operator's ruling from 2026-07-21, `last_reviewed: 2026-07-21`):

> "Sports ODDS tick data starts 2020-06-06... every sports artifact dated before 2020-06-06 is
> fabrication-by-construction... The honest resolution is to DELETE pre-floor sports data from GCS + manifest — not
> backfill it."

The floor doc records the wipe as **already executed** for the canonical-tree equivalent of this exact entity class:
`instruments-store-sports-prd` = 437,124 objects deleted, itemized as `sports_reference/by_date 398,240` ·
`sports_reference/fixtures 4,735` · `instrument_availability/by_date 34,149`. `sports_reference/fixtures` is the
FIXTURES entity in the flat canonical layout — proving the operator's own wipe campaign did NOT carve out an exemption
for fixture-result data as "historical fact independent of odds" the way one might argue. Pre-floor FIXTURES data was
wiped just like everything else.

The 1,492 `sports_reference_v2/by_date/day={D}/entity={fixtures|fixture_stats}/...` rows (days 2018-01-02 through
2020-05-25, confirmed 15/15 still present) are the **same fabrication-by-construction population**, sitting under the v2
migration-staging prefix that the 2026-07-21 wipe campaign's scope (`sports_reference/by_date` +
`sports_reference/fixtures`) never reached — confirmed directly in
`/plans/active/issues/sports_legacy_duplicate_triage_2026_07_22.md` §2: "these 1,492 rows... are not a 'legacy duplicate
awaiting twin-verified delete' question at all — they are the same fabrication-by-construction category already being
wiped elsewhere, just under a prefix the existing wipe missed." That doc's own §7 todo 1 recommendation was explicit:
**fold into the existing pre-floor-wipe operator-gated process** (extend `deployment-service`'s
`wipe_pre_floor_sports_2026_07_21.py`-style tool to also cover `sports_reference_v2/`) — i.e. DELETE, never
copy-to-canonical. `sports_consolidated_closeout_2026_07_19.md`'s own cull-todo citation (added by the 2026-08-02
`/plan-reconcile` pass) repeats this verbatim: "ruled that they fold explicitly into the pre-floor-wipe scope per
`/codex/02-data/sports-2020-06-data-floor.md`."

Somewhere between that correct 2026-07-22/2026-07-28 disposition and the § 1b conflict-resolution options drafted
2026-08-02, the framing drifted from "fold into the wipe (delete)" to "copy to canonical (preserve)" — the § 1b options
(A/B/C) reasoned only about the delete-safety twin-existence proof for the **cull todos**, and never re-examined whether
the floor policy independently forbids preserving this data at all, regardless of twin existence. The operator's
2026-08-03 confirmation of option B inherited that gap rather than resolving it.

## Why it matters

Executing the dispatched task as literally worded would **write 1,492 rows of already-ruled fabrication-by-construction
data into live canonical `sports_reference/by_date/` storage** — the exact outcome the 2026-07-21 wipe campaign was
authorised to prevent, for the exact same entity class it already wiped 402,975 objects of. This is not a stylistic nit:
any downstream honest-coverage denominator, feature computation, or fixture expectation that reads the canonical tree
would then see pre-floor days as covered, silently reintroducing the "fabricated `derived_features` computed for a day
with no odds" failure mode the floor doc was written to eliminate (`/codex/02-data/sports-2020-06-data-floor.md` § "What
is MOOT after the floor" explicitly calls any pre-2020-06 backfill "moot" and "inside the wipe's blast radius"). Per
CLAUDE.md's data-pipeline-correctness HARD RULE, this is a "big finding" (SSOT contradiction) that must not be silently
absorbed or executed past.

## Recommended decision

**Recommend**: treat the floor SSOT as controlling (it is more specific — it directly answers "should pre-floor sports
data exist in canonical storage at all", where § 1b's options never asked that question) and **extend the pre-floor wipe
to cover `sports_reference_v2/by_date/`, deleting the 1,492 rows, instead of copying them to canonical** — exactly the
original 2026-07-22 triage recommendation. This also resolves the underlying § 1b cull-safety concern for free: once
these rows are wiped rather than preserved, there is no "sole surviving copy" to protect, so
`sports_consolidated_closeout_2026_07_19.md`'s and `sports_consolidated_native_ao_extract_2026_07_25.md`'s
`sports_reference_v2/by_date/` cull todos can revert to self-justified without any copy step.

**Alternative**: if the operator specifically intends a carve-out preserving these 1,492 rows despite the floor (e.g. a
deliberate exception for FIXTURES/FIXTURE_STATS results as objective historical fact, distinct from odds-derived
predictive features) — note this would be a NEW, narrower amendment to the floor SSOT, since the floor doc's own
already-executed wipe did not apply that distinction to the 4,735 `sports_reference/fixtures` pre-floor objects it
already deleted. That inconsistency (deleting flat pre-floor FIXTURES objects but preserving v2-staging pre-floor
FIXTURES objects of the same days) would itself need to be reconciled or explicitly accepted.

Either way, this is a genuine SSOT-level policy question the operator's own two rulings (2026-07-21 floor; 2026-08-03 §
1b option B) now disagree on — a worker cannot silently pick a side. Filed `/blocked` (`BLK-` — see task progress)
rather than executing the copy.

## Todos

- [ ] [REVIEW] P0. Operator/main: reconcile the 2026-07-21 floor ruling against the 2026-08-03 § 1b option-B
      confirmation for these 1,492 rows — confirm whether the correct disposition is (a) extend the pre-floor wipe to
      `sports_reference_v2/by_date/` and delete them (recommended, matches the floor SSOT + the original 2026-07-22
      triage), or (b) explicitly carve out a floor exception for this population and reconcile it against the already
      -executed `sports_reference/fixtures` wipe of the same-shaped data.
- [ ] [DATA] P1. Once ruled: either (a) extend `deployment-service`'s `wipe_pre_floor_sports_2026_07_21.py`-style tool
      to cover `sports_reference_v2/by_date/` and execute the delete (human-only per delete-safety protocol unless
      reversibility-qualified), retiring `sports_reference_v2_1492_row_canonical_copy_2026_08_03.md`'s copy todos as
      superseded; or (b) proceed with the original copy-to-canonical task, now with an explicit, documented floor
      exception cited inline so future readers don't re-discover this same contradiction. (repo:
      `market-tick-data-service`, `instruments-service`, `deployment-service`)

## Progress Log

- **2026-08-03** (slot 15, backend/data_engineering, task `sports_reference_v2_1492_row_canonical_copy-002`) — Filed
  before executing the copy. Did not implement any code change; no GCS object read or written for this task.
