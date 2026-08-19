---
doc_type: issue
title: tradfi_registry_coverage_and_ao_readiness_2026_07_25.md's own checkboxes are stale vs. batch13's already-completed extractions
summary: >-
  Discovered while resolving tradfi_autonomous_session_operator_decisions_2026_07_25.md's item-5 propagation todo
  (operator 2026-08-07 ruling: flip all 8 draft tradfi AO plans to active). 6 of 8 named plans are already
  status:complete+archived; the last 2 (tradfi_registry_coverage_and_ao_readiness_2026_07_25.md + its finalize) are
  still status:draft/assigned_vm:NA. Before flipping them, live-checked for conflicts and found at least 2 of that
  doc's 13 open checkboxes were already independently executed and closed via
  tradfi_satellite_ao_dispatch_batch13_2026_08_13.md (2026-08-15/16), which cited the registry-coverage doc as
  Source without the source doc's own checkboxes ever being updated to match. Flipping the source doc to active
  as-is would re-expose already-done work as fresh AO backlog.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, na-eligibility-audit, stale-checkbox, ao-readiness, dispatch-hygiene]
related:
  [
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25_finalize.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: 2026-08-18
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: backend_engineer
drift_direction: advance-docs
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  na-eligibility-audit, tradfi tranche, dispatch agt-31bfcb, 2026-08-18 — surfaced while resolving
  tradfi_autonomous_session_operator_decisions_2026_07_25.md's item-5 propagation todo.
context_scope:
  [
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13.md,
  ]
---

# tradfi_registry_coverage_and_ao_readiness_2026_07_25.md's checkboxes are stale vs. batch13

## What happened

Resolving `tradfi_autonomous_session_operator_decisions_2026_07_25.md`'s item 5 (operator 2026-08-07 ruling: flip
all 8 draft tradfi AO plans to `status: active`) required live-checking all 8 named docs. 6 of 8 are already
`status: complete` (archived): `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`(+finalize),
`…batch2_2026_07_25.md`(+finalize), `/plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md`
(+finalize). Only `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` + its `_finalize` remain
`status: draft`/`assigned_vm: NA`.

Before flipping those last 2, a conflict-check grep (`tradfi_registry_coverage_and_ao_readiness` across every
active tradfi satellite batch) found `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md` cites the source doc as
`Source:` for at least 4 of its own dispatched todos:

- "VERIFY CME mbp_10/trades/tbbo billing-gated declaration" — `[x]` DONE 2026-08-15 (slot-29)
- "VERIFY KRX equities registry-vs-adapter mismatch fix still holds live" — `[x]` DONE 2026-08-15 (slot-14) — matches
  `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md:142`'s open `[ ]` checkbox verbatim
- "Run distinct-values/axis-value census for tradfi and confirm 0 non-canonical values" — `[x]` DONE 2026-08-15
  (slot-6), flipped 2026-08-16 (plan_reconciler) — matches
  `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md:232`'s open `[ ]` checkbox verbatim
- "Run the tradfi Databento by_date re-feed chain to completion" — marked NOT ACTIONABLE 2026-08-15 (billing
  recurred-blocked since 2026-08-12) — matches `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md:295`'s open
  `[ ]` P0 checkbox

The source doc's own checkboxes were never updated to reflect any of this — they still read as freshly open. This
is exactly the "done-but-unflipped" pattern the corpus has hit repeatedly elsewhere (see e.g.
`tradfi_autonomous_session_operator_decisions_2026_07_25.md`'s own 2026-08-07 Progress Log entry documenting the
identical pattern for items 1/2/6/9).

## Why this wasn't fixed directly in this pass

Fully reconciling all 13 of the source doc's open checkboxes against batch13 (and confirming none of the other 9
have similarly drifted) is real, non-trivial content work — reading each checkbox's current text, matching it
against batch13's evidence, and updating in place — not a mechanical one-line fix, and well outside the scope of
the na-eligibility-audit run that surfaced it (which was resolving a DIFFERENT doc's propagation todo, not auditing
this doc's own content — this doc's `incremental_skip` was `True` this run, meaning a prior audit marker already
covers it as unchanged). Per findings-triage, filed here rather than either (a) blindly flipping a stale-checkbox
doc to `active` (which would let AO backlog-regen re-derive already-done work as fresh tasks) or (b) silently
leaving the operator's 2026-08-07 "flip all 8" ruling permanently unexecuted for these last 2.

## Todos

- [ ] [BACKEND] P2. **Reconcile all 13 open checkboxes in `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`
      against `tradfi_satellite_ao_dispatch_batch13_2026_08_13.md`'s dispatched/completed todos** — close the (at
      least 4) confirmed-done items citing batch13's evidence directly (mirroring each item's real disposition:
      DONE with a commit/verify citation, or NOT ACTIONABLE with the blocking reason), leave genuinely still-open
      items as-is. Done when: every checkbox's state matches live reality, with citations.
- [ ] [PM] P2. **Once the reconciliation above lands, flip `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`
      + its `_finalize` from `status: draft`/`assigned_vm: NA` to `status: active`/`assigned_vm: planning`**, per
      the operator's 2026-08-07 ruling (`tradfi_autonomous_session_operator_decisions_2026_07_25.md` item 5,
      "Option A, flip all 8... unqualified"). This closes out the last 2 of the original 8. Done when: both docs'
      frontmatter reflects the flip and the remaining genuinely-open todos are live in the AO backlog.

## Progress Log

- **2026-08-18 (na-eligibility-audit, tradfi tranche, dispatch agt-31bfcb)**: filed while resolving
  `tradfi_autonomous_session_operator_decisions_2026_07_25.md`'s item-5 propagation todo; did not execute either
  todo above directly (out of scope for the audit run that found it — this doc's own content was outside this
  run's incremental-diff scope).
- **plan_reconciler 2026-08-19** (epic-scoped `tradfi_master` pass) — **Todo 1 PARTIALLY DONE**: flipped the 3
  specifically-named checkboxes (KRX equities registry-vs-adapter verify, line ~142; distinct-values/axis-value
  census, line ~232; both `[x]` with batch13 evidence citations) plus corrected the 4th (Databento `by_date`
  re-feed, line ~296) with a stale-premise annotation matching batch13's own NOT ACTIONABLE disposition (not a
  flip — the work itself is still gated on the billing block). **Not done**: full reconciliation of the remaining
  ~9 open checkboxes in `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` against fresh live state (only
  the 4 batch13-cited items were checked this pass) — Todo 1 stays open for that remainder. Todo 2 (flip
  `status: draft`→`active`) NOT executed — still gated on Todo 1's full completion, per this doc's own explicit
  ordering ("once the reconciliation above lands").
