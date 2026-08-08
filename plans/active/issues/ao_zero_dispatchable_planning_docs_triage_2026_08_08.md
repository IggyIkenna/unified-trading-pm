---
doc_type: issue
title: "24 active assigned_vm:planning docs parse to ZERO dispatchable todos — need per-doc triage"
summary: >-
  MEASURED 2026-08-08 by the new `check_ao_dispatch_gap.py` QG gate
  (plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md): 24 docs with
  `assigned_vm: planning` + `status: active`/`open` currently parse to ZERO dispatchable todos via regen's real
  `_parse_open_todos` — an active AO plan the orchestrator will never touch at all. Every one of the 3 spot-checked
  (`prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s 3 open todos, verified via the new gate's per-todo
  classifier) turned out to be genuinely, declaredly blocked (BLOCKED-OPERATOR-DECISION / BLOCKED-CREDENTIALS /
  DEFERRED-BY-DESIGN) rather than a parser bug — 0 accidental exclusions found corpus-wide by the same run. This doc
  exists to close the loop the parent issue's "Done when" asked for: emit the list as its own louder finding (not
  silently baseline-absorbed) and give each doc a per-doc verdict rather than leaving 24 always-empty AO plans sitting
  `active` indefinitely.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, plan-hygiene, dispatch, zero-dispatchable, findings-triage]
related: [/plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md]
created: "2026-08-08"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
assigned_role: infra
drift_direction: fix
resolved_by:
locked_by:
source: "slot-24, filed while shipping check_ao_dispatch_gap.py (findings-closure rule, RULES.md §4.5)"
depends_on: []
---

# 24 zero-dispatchable assigned_vm:planning docs — per-doc triage

## What I found

`check_ao_dispatch_gap.py --workspace-root <ws> --update-baseline`, run 2026-08-08 against the live corpus (287
`assigned_vm: planning` + `status: active`/`open` docs checked), found 24 docs where every on-disk `- [ ]` todo is
excluded from the backlog by regen's real `_parse_open_todos` — the doc renders as tracked, live work, but AO will never
dispatch a single todo from it.

Per the parent issue's own framing: "an `active`, `assigned_vm: planning` doc with zero dispatchable todos is either
mis-tagged or finished, never correct as-is." The 24:

- `plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md`
- `plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md`
- `plans/active/ci_satellite_ao_dispatch_batch5_2026_08_02.md`
- `plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`
- `plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md`
- `plans/active/infra_capture_and_devops_leftovers_finalize_2026_07_25.md`
- `plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md`
- `plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md` (spot-checked: 3/3 declared-blocked, see below)
- `plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md`
- `plans/active/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`
- `plans/active/issues/ao_done_gate_tag_correlation_false_match_on_leading_marker_2026_08_02.md`
- `plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`
- `plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md`
- `plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`
- `plans/active/issues/credential_ask_orphan_checker_ping_format_stale_2026_07_27.md`
- `plans/active/issues/deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md`
- `plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md`
- `plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md`
- `plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md`
- `plans/active/issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`
- `plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`
- `plans/active/issues/sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md`
- `plans/active/issues/upbit_cefi_data_gap_may_2026_2026_08_04.md`
- `plans/active/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md`

**Spot-check (`prediction_satellite_ao_dispatch_batch6_2026_07_29.md`, 3 open todos, 0 dispatchable)**: read all three
directly — the Betfair two-sided-odds todo carries a live `BLOCKED-CREDENTIALS` marker (2026-07-31 progress note
confirms it's genuinely credential-gated, not a design gap), the Kalshi execution todo carries a live
`BLOCKED-OPERATOR-DECISION` marker (2026-07-31, a real unresolved conflict about what "paper order" means for a venue
with no paper mode), and the Phase-5 canonical-groups todo is marked `DEFERRED-BY-DESIGN` inline. All three are
DECLARED, not accidental — this doc is a genuine "everything remaining is blocked" case, not a parser bug or mis-tag.
This is only ONE of 24 spot-checked, not the full corpus — the other 23 need the same per-doc read before any doc gets a
verdict.

## Why it matters

Same reasoning as the parent issue: a doc that reads as tracked, active AO work but can never dispatch anything is
either stale bookkeeping (should be archived/reclassified) or correctly fully-blocked (fine to stay `active`, but worth
a dated verdict so the next sweep doesn't have to re-derive it from scratch). Left unaudited, this list only grows as
more satellite-dispatch-batch docs complete their AO-eligible todos and are left holding only blocked remainder items.

## Recommended decision

- [ ] [SCRIPT] P2. **Triage each of the 24 zero-dispatchable docs listed above.** For each: read the doc's open todos
      and classify DECLARED-BLOCKED-CORRECTLY-ACTIVE (every remaining todo carries a genuine, currently-true
      BLOCKED-<token>/DEFERRED-BY-DESIGN marker — leave `active`, no action) vs FINISHED-MIS-TAGGED (the doc is actually
      complete or all remaining work has moved elsewhere — archive per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`, or reclassify `assigned_vm` to `NA` if it's
      genuinely human-only judgment work) vs GENUINE-PARSER-GAP (an accidental exclusion `check_ao_dispatch_gap` missed
      — file it against the parent issue and fix). **Done when**: every one of the 24 has a dated verdict line in this
      doc's Progress Log (or the doc itself, whichever the triaging worker owns), and any FINISHED-MIS-TAGGED doc is
      actually archived/reclassified (not just noted). Re-run `check_ao_dispatch_gap.py --update-baseline` afterward if
      the zero-dispatchable count changed.

## Progress Log

- **2026-08-08 (slot-24)**: Filed while shipping `check_ao_dispatch_gap.py` (the parent issue's own gate). The gate's
  first live run measured 0 accidental exclusions / 24 zero-dispatchable docs, seeded as the shrinking-ratchet baseline.
  One of the 24 spot-checked directly (`prediction_satellite_ao_dispatch_batch6_2026_07_29.md`) and confirmed genuinely,
  correctly all-blocked — not a bug. The other 23 need the same read before any doc gets archived/reclassified; kept as
  one bounded audit todo per findings-closure convention (RULES.md §4.5) rather than hand-triaging all 24 now, since
  that's real per-doc judgment work outside this task's scope (shipping the gate).
