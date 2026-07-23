---
doc_type: issue
title:
  "coinbase_bare_name_migration_2026_07_06.md Step S2's 'safe to land before S3' ordering note is wrong — verified it
  breaks 2 regression tests + the real IS cefi venue producer"
summary: |
  Step S2 of the plan (delete the dead `elif venue == "COINBASE"` alias in
  `instruments-service/instruments_service/engine/orchestrator/venue_core.py:145-146`) carries an "Ordering note"
  claiming it is safe to land before Step S3 (the UAC bare-COINBASE removal) because it "does not READ the UAC dict."
  Dispatched to slot 9 (data_engineering) 2026-07-10 as task `coinbase_bare_name_migration-002`. Attempting the
  literal S2 diff and running `bash scripts/quality-gates.sh` in instruments-service proved the note false: with the
  alias branch deleted and S1/S3 not yet landed, UAC's `VENUES_BY_ASSET_GROUP["cefi"]` still emits bare `COINBASE`,
  so the IS cefi venue producer now passes bare `COINBASE` straight through instead of mapping it to
  `COINBASE-SPOT` — a real production regression (not just a test artifact), and it fails 2 existing regression
  tests. Reverted the change (repo left clean, nothing shipped) and annotated the plan's S2 section with a blocked
  banner. Filing this for the operator/main-agent re-sequencing decision.
status: resolved
nature: notes
asset_group: [cefi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [venue-canonicalisation, cefi, coinbase, sequencing, plan-drift, data-pipeline-correctness]
related:
  [/plans/archive/2026_07/coinbase_bare_name_migration_2026_07_06.md, issues/wsfeedconnector_phase35_gap_2026_07_06.md]
created: 2026-07-10
last_updated: 2026-07-10
parent_epic: instruments_master
priority: P2
source:
  orchestrator task `coinbase_bare_name_migration-002` (slot 9, data_engineering), dispatched 2026-07-10 from
  `plans/archive/2026_07/coinbase_bare_name_migration_2026_07_06.md` Step S2
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by: "unified-trading-pm@6e8a48424 — see Resolution section below"
audited_scope: single-step-verification
---

# coinbase_bare_name_migration Step S2 ordering note is disproven

## What I was asked to do

Task `coinbase_bare_name_migration-002`: in `instruments-service/instruments_service/engine/orchestrator/venue_core.py`,
delete lines 145-146 (`elif venue == "COINBASE": result.append("COINBASE-SPOT")`), update the docstring references at
lines 97/115/126/317, and add a regression test `test_expand_cefi_tardis_endpoints_no_bare_coinbase_input`. Plan gate:
"QG green; test added; no downstream IS producer regressions in `tests/unit/`."

## What I found

Made the exact diff the plan specifies (branch deletion + docstring updates + the named regression test), then ran
`bash scripts/quality-gates.sh`. Two existing tests failed:

- `tests/unit/test_adapter_routing_uac_invariant.py::TestAdapterRoutingUACInvariant::test_expanded_cefi_enumeration_fully_resolvable`
  — `expand_cefi_tardis_endpoints(list(VENUES_BY_ASSET_GROUP["cefi"]))` now includes bare `COINBASE` unmapped, and
  `VENUE_TO_ADAPTER_KEY["COINBASE"] = NO_ADAPTER_YET` (that entry is only removed in Step S3), so the test's "every
  expanded venue resolves to a real adapter" invariant fails.
- `tests/unit/test_new_orchestrator.py::test_process_instruments_cefi_venues_available` — asserts
  `"COINBASE-SPOT" in venues` for the CEFI producer; with the alias branch gone and UAC still emitting bare `COINBASE`,
  `COINBASE-SPOT` never gets added (only the now-unmapped bare `COINBASE` does), so the assertion fails.

Root cause: the plan's S2 "Ordering note" reasons that the branch "does not READ the UAC dict" and is therefore inert
until S3 runs. That's true of the branch's own code, but it ignores that `expand_cefi_tardis_endpoints` is CALLED with
the live UAC `VENUES_BY_ASSET_GROUP["cefi"]` list at runtime (via `get_venues_for_asset_groups`), which still contains
bare `COINBASE` today. Deleting the branch before S3 removes bare `COINBASE` from UAC therefore converts a
previously-correct alias-expansion into a silent pass-through of an unmapped venue name — exactly the kind of "trust the
actual distribution, not the constant" case the data-correctness hard rule warns about.

I reverted both files (`git checkout --`) — instruments-service is back to a clean, QG-green state; nothing was shipped
under this task. I also added a `> **🔴 BLOCKED**` banner directly under the S2 heading in
`coinbase_bare_name_migration_2026_07_06.md` linking back to this doc, and struck through the disproven ordering note
with the verification details inline, so no other worker re-attempts S2 in isolation.

## Why it matters

This is the exact multi-repo, data-correctness-adjacent sequencing bug the plan's own §4 DAG section says it was
designed to avoid ("no intermediate LDR state is data-incorrect"). If S2 had shipped alone, the real IS cefi
instrument-fetch venue list would have silently dropped `COINBASE-SPOT` fetches (or produced an unresolvable bare
`COINBASE` lookup) until S3 landed — an availability regression on a live venue, not just a red test suite.

## Recommended decision

Pick one (operator / main-agent call — this is a plan re-sequencing decision, not a code fix I can make unilaterally
within a single-repo, one-task-at-a-time worker session):

- [x] [PLAN] P2. ✅ **Option A (recommended)** — gate S2's dispatch on S3 having landed first: add `depends_on: [S3]`
      semantics to the S2 todo (or simply reorder the plan body so S2 follows S3), then re-dispatch S2 standalone once
      S3 is confirmed on LDR. (repo: unified-trading-pm) — **DONE 2026-07-10** — see Resolution section below.
- [x] **Option B — NOT TAKEN 2026-07-10.** Option A (the recommended, lower-coordination-cost choice) was implemented
      instead; see Resolution section below. Mutually exclusive with A — checked off (not struck-through, to avoid a
      Prettier markdown-reflow hazard where a `~~`-prefixed list item merges into the preceding bullet's paragraph) so
      regen never dispatches this as a separate, now-redundant task. Original text: ~~[CODE] P2. combine S2 and S3 into
      one coordinated cross-repo shippable unit (a single task/commit pair landing the UAC removal and the IS dead-code
      deletion together) so no intermediate broken state exists on LDR. Higher coordination cost but matches the plan's
      own "no intermediate LDR state is data-incorrect" design goal more literally. (repo: instruments-service,
      unified-api-contracts)~~
- [x] [DESIGN] P3. ✅ Whichever option is chosen, add a short "verify before land" step to the plan's own template
      guidance for multi-repo DAG plans: when a step's gate says "no downstream regressions," actually run
      `quality-gates.sh` with the isolated diff BEFORE marking an ordering note as "safe" — this plan's S1 ordering note
      (single-file `_CEFI_VENUE_FOLD` invert) may deserve the same spot-check before its own dispatch. (repo:
      unified-trading-pm) — **DONE 2026-07-10** — added a new bullet to `plans/active/task_template.md` §4
      (AO-DISPATCHED plans — STRICT rules), right after the "Ordering" bullet: "Verify an 'Ordering note' before
      asserting it's safe" — requires an isolated-diff QG run before writing "safe to land before M", and points authors
      at `sequential: true` / explicit `prereqs.completed_tasks` as the actual dispatch-gate mechanism instead of a
      human-readable blocked banner. Cites this issue doc + the S2/S3 case study as the worked example. NOTE: S1's own
      ordering-note spot-check (mentioned in this todo's text) was already independently verified DONE on landing per
      S1's Progress Log entry in `coinbase_bare_name_migration_2026_07_06.md` (ran
      `measure_honest_coverage.py --diagnose-layer1` against the live production manifest before/after) — no outstanding
      action there.

## Resolution

Implemented Option A in `coinbase_bare_name_migration_2026_07_06.md` (unified-trading-pm, plan-file-only edit — no
service-repo code diff):

1. Added `sequential: true` to the plan's frontmatter. Per `regen_backlog_from_plan.py`'s `_wire_sequential_prereqs`,
   this auto-chains every remaining unchecked todo's `prereqs.completed_tasks` to its immediate predecessor by
   `plan_order` (file order among the plan's own still-open todos) — re-derived every regen tick, so it self-heals
   around future inserts/reorders. This is the ONLY mechanism available for genuine intra-plan dispatch gating today
   (plain `plan_order` is a tie-break, not a gate; cross-plan `depends_on`/`gate_on_depends` only gates one whole PLAN
   on another PLAN, not one todo on a sibling todo in the SAME plan).
2. Physically moved the `### Step S3` section to appear BEFORE `### Step S2` in the plan body (`sequential: true` chains
   by file-order position, so the direction of the swap matters — S3 must sit earlier than S2 for the auto-chain to make
   S2 wait on S3, not the reverse).
3. Updated S2's banner from a human-readable "🔴 BLOCKED, don't re-dispatch" note to document the machine gate now in
   place; kept the disproven "safe before S3" ordering note struck through for history.
4. As a consequence, the plan's other 2 remaining open steps (S5, S6) are now also chained into the same strict-serial
   order (S3 → S2 → S5 → S6) — a stronger fix than the narrow S2-on-S3 gate this issue asked for, but it directly closes
   the gap the plan's own 2026-07-10 S4 Progress Log entry flagged: "this plan's S1→S6 steps have a real internal
   dependency chain … but no `depends_on`/`sequential: true` gating between the per-step backlog tasks … S4 happened to
   be safe … but that was a lucky audit outcome, not a guarantee." `sequential: true` is documented in
   `regen_backlog_from_plan.py` as intended precisely "for audit→fix→verify / migration plans" — this plan is exactly
   that shape.
5. Option B (combine S2+S3 into one cross-repo shippable unit) was NOT taken — struck through above as mutually
   exclusive with A, so regen never surfaces it as a live, redundant alternative task.
6. The P3 DESIGN todo (add a "verify before land" step to the plan-authoring template guidance) is left open as a
   separate, smaller follow-on — not required to close THIS ordering bug, but a reasonable process improvement the next
   dispatch can pick up independently.
