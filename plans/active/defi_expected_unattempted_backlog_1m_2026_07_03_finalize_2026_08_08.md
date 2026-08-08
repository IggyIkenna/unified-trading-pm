---
doc_type: plan
title: Finalize — defi A_TOKEN/DEBT_TOKEN instrument_type-alias + oracle_prices validity fix close-out
summary: >-
  Gated finalize companion for issues/defi_expected_unattempted_backlog_1m_2026_07_03.md (reclassified NA→planning,
  na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08) — re-verifies the `_INSTRUMENT_TYPE_ALIASES` +
  `PROTOCOL_CAPABILITIES` widening build's evidence, confirms the dead `venue_mapping.DataTypeConfig` cleanup landed,
  then archives both docs per plan-completion-and-archival-discipline once every todo is done.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, manifest, expected-unattempted, instrument-type-alias, finalize, archival, ao-build]
related:
  [
    /plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: advance-code
depends_on: [defi_expected_unattempted_backlog_1m_2026_07_03]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep) — every AO-dispatched plan/reclassified issue doc needs a
  gated finalize companion (/plans/active/task_template.md §4).
context_scope:
  [
    /plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    unified-api-contracts/unified_api_contracts/registry/possible_manifest.py,
  ]
---

# Finalize — defi A_TOKEN/DEBT_TOKEN instrument_type-alias + oracle_prices validity fix close-out

Machine-held (`gate_on_depends: true`) until every todo in `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`
is done. Do not start manually before then.

## Todos

- [ ] [REVIEW] P2. Re-verify the build's evidence: (1) `market_data_categories._INSTRUMENT_TYPE_ALIASES` gained the two
      named entries (`"a_token": "lending"`, `"debt_token": "lending"`) — confirm via `git log`/`git show` against a
      fresh `git pull --ff-only origin live-defi-rollout` on `unified-api-contracts` (don't trust the build todo's own
      evidence line uncritically); (2) the AAVE_V3/FLUID/SOLEND/SPARK/VENUS lending protocols' declared `data_types` in
      `capability_declarations/_defi.py` were widened to include `oracle_prices`; (3) a live check confirms
      `valid_data_types_for_instrument_type("defi", "A_TOKEN")` and `("defi", "DEBT_TOKEN")` both return a non-`None`
      frozenset containing `oracle_prices`; (4) a new regression test asserts the previous unmapped-fallback bug
      (`--data-types perp_trades` over-fanning A_TOKEN/DEBT_TOKEN venues, the 2026-07-16 finding) no longer reproduces;
      (5) the now-confirmed-dead `venue_mapping.DataTypeConfig` + its one unit test were deleted per the source doc's
      own follow-up note (only if that deletion sub-step was actually attempted — the source todo scopes it as a "do not
      do in this todo" follow-up, so its absence is not itself a finding). Done-when: all applicable points
      independently re-verified with cited evidence; any mis-citation found is corrected in the source doc directly.
- [ ] [DOC] P2. Run the standard 6-step plan-completion-and-archival-discipline ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` and this finalize doc itself: archive both to
      `plans/archive/2026_08/issues/` (this finalize doc to `plans/archive/2026_08/`), and fix every corpus referrer
      path (grep the repo for the old paths — `defi_satellite_ao_dispatch_batch6_2026_07_30.md`,
      `defi_satellite_ao_dispatch_batch9_2026_08_06.md`, `defi_satellite_ao_dispatch_batch10_2026_08_06.md`,
      `defi_consolidated_closeout_2026_07_18.md`, `instruments_completion_tracker_2026_07_06.md`, and
      `instruments_remaining_work_audit_2026_07_10.md` all cite the source doc — update each hit). Done-when:
      `regenerate_active_plan_inventory.py` shows zero orphan referrers to the archived paths.

## Progress Log

- **2026-08-08 (na-eligibility-audit round7 RECLASSIFY sweep)**: finalize plan authored alongside the RECLASSIFY flip of
  the source issue doc, per `task_template.md`'s finalize-plan-coverage rule.
