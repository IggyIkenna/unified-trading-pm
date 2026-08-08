---
doc_type: issue
title: "27 accidental (undeclared) exclusions found by check_ao_dispatch_visibility_gate.py — per-doc triage"
summary: >-
  Follow-up from ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md's own "Done when": a MEASURED
  run of the new check_ao_dispatch_visibility_gate.py (agent-orchestrator/server/dispatch_visibility_report.py) against
  the live corpus (2026-08-08) found 45 total disk-vs-backlog excluded todos across 246 assigned_vm:planning docs, split
  18 declared (a live BLOCKED-<token>/DEFERRED-BY-DESIGN/stretch marker that correctly opens its own line -- the parser
  working as intended) vs 27 accidental (the marker is merely present inside a longer sentence -- the same
  regex-widening bug class the parent issue found via the sports Betfair todo, now surfaced structurally instead of one
  incident at a time). Also found 24 zero-dispatchable docs (an assigned_vm:planning doc with open todos on disk but
  none reaching the backlog at all). The parent issue's own scope note ("the other 46 are... deliberately left for the
  gate to classify rather than hand-triaged now") applies here too: this doc lists every accidental finding as its own
  todo rather than hand-fixing 27 across 26 docs in the same session as building the gate itself. The gate's baseline
  (ao_dispatch_visibility_baseline.yaml) is seeded at today's measured 27/24 so it ratchets from here -- fixing (or
  genuinely re-declaring) items below should lower the baseline via --update-baseline as they land.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, plan-hygiene, dispatch, false-progress, quality-gates]
related:
  [
    /plans/archive/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md,
    /plans/active/issues/ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md,
  ]
created: 2026-08-08
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
source: "slot-21 infra worker, 2026-08-08 -- building/wiring check_ao_dispatch_visibility_gate.py"
depends_on: [ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08]
---

# AO dispatch-visibility gate — 27 accidental exclusions, per-doc triage

## What I found

Running the new gate's oracle directly against the live corpus (2026-08-08):

```
docs=246 disk_open=642 backlog_open=597 excluded=45 accidental=27 zero_dispatchable_docs=24
```

45 open todos across 246 `assigned_vm: planning` docs are on disk but never reach the backlog. 18 of those are correctly
DECLARED (a live marker that opens its own line — the parser doing exactly what it's supposed to). The 27 below are
ACCIDENTAL: the marker is present somewhere in the block but doesn't open its own line, so
`check_ao_dispatch_visibility_gate.py` can't tell from outside the parser whether the hold is deliberate. Several carry
a dated `RULED (operator): proceed` / `DESIGN DECIDED` resolution note that doesn't match any of the four existing
`_STALE_MARKER_*_RE` escape hatches (widening a fifth time is explicitly out of scope per the parent issue — this doc is
the classify-and-file step that issue's own "Done when" calls for instead).

24 docs have zero dispatchable todos at all (disk_open > 0, backlog_open == 0):

- `plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md` (disk_open=1)
- `plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md` (disk_open=1)
- `plans/active/ci_satellite_ao_dispatch_batch5_2026_08_02.md` (disk_open=1)
- `plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` (disk_open=1)
- `plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md` (disk_open=1)
- `plans/active/infra_capture_and_devops_leftovers_finalize_2026_07_25.md` (disk_open=1)
- `plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md` (disk_open=1)
- `plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md` (disk_open=3)
- `plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md` (disk_open=1)
- `plans/active/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md` (disk_open=1)
- `plans/active/issues/ao_done_gate_tag_correlation_false_match_on_leading_marker_2026_08_02.md` (disk_open=1)
- `plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` (disk_open=1)
- `plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md` (disk_open=1)
- `plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md` (disk_open=1)
- `plans/active/issues/credential_ask_orphan_checker_ping_format_stale_2026_07_27.md` (disk_open=1)
- `plans/active/issues/deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md` (disk_open=1)
- `plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md` (disk_open=1)
- `plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` (disk_open=2)
- `plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md` (disk_open=1)
- `plans/active/issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md` (disk_open=1)
- `plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` (disk_open=2)
- `plans/active/issues/sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md`
  (disk_open=1)
- `plans/active/issues/upbit_cefi_data_gap_may_2026_2026_08_04.md` (disk_open=1)
- `plans/active/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md` (disk_open=1)

Most of these are explained by one of the 27 findings below (their sole open todo IS the accidental exclusion); a few
are genuinely, correctly all-DEFERRED/all-BLOCKED docs and need no action.

## Why it matters

Same as the parent issue: a plan renders a live `- [ ]`, `regenerate_active_plan_inventory.py` counts it, the operator
reading the plan sees tracked work — AO never dispatches it, and until this gate existed nothing said so. A
`RULED 2026-08-06 (operator): proceed now` todo that still silently excludes itself is the worst version of this: the
human already made the call and the fleet still never executes it.

## Recommended decision

- [ ] [SCRIPT] P2. **Triage accidental exclusion in `plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md`.** Its
      checkbox reads (truncated): "[DOC] P3. **Document the accepted BLOCKED‑marker `/done`-disposition convention in
      `task_template.md`.** Add a" — the marker trips `_is_non_dispatchable`
      (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own line, so
      `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely still
      blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start of its
      own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it reads
      as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note — read
      the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the block.
      Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12_finalize_2026_08_08.md`.** Its checkbox reads
      (truncated): "[REVIEW] P2. **Reconcile.** Once the source doc's sole open `[VERIFY]` P1 item lands — re-launch
      LIGHTER-ZKSYNC" — the marker trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`)
      but does not open its own line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared:
      false). If it is genuinely still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a
      permanent-deferral tag) to the start of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or
      a dedicated continuation line) so it reads as a declared hold. If it is already resolved (several of these carry a
      dated `RULED`/`DESIGN DECIDED` note — read the full todo before acting), rewrite the trigger phrase so the marker
      no longer appears anywhere in the block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in `plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md`.**
      Its checkbox reads (truncated): "[DATA] P2. **Read-only investigate the ~1104 genuine HYPERLIQUID(660)/ASTER(444)
      wire-vs-canonical filename" — the marker trips `_is_non_dispatchable`
      (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own line, so
      `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely still
      blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start of its
      own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it reads
      as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note — read
      the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the block.
      Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in `plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md`.** Its
      checkbox reads (truncated): "[VERIFY] P1. **Re-measure the billed notify/glue cost — the 3-5 day window has long
      passed.** The mover flip" — the marker trips `_is_non_dispatchable`
      (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own line, so
      `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely still
      blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start of its
      own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it reads
      as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note — read
      the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the block.
      Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in `plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md`.** Its
      checkbox reads (truncated): "[VERIFY] P0. **Time-gated billing/capacity re-measurement sweep — 4 items in" — the
      marker trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its
      own line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely
      still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start
      of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it
      reads as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note
      — read the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the
      block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in `plans/active/ci_satellite_ao_dispatch_batch6_2026_08_08.md`.** Its
      checkbox reads (truncated): "1. [INFRA] P0. **Re-measure fleet CI job-minutes 24h after the runner-checkout cache
      fix.** The 24h time-gate" — the marker trips `_is_non_dispatchable`
      (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own line, so
      `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely still
      blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start of its
      own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it reads
      as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note — read
      the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the block.
      Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in `plans/active/ci_satellite_ao_dispatch_batch6_2026_08_08.md`.** Its
      checkbox reads (truncated): "12. [VERIFY] P3. **Run the `--skip-tests`/`--skip-<X>` per-phase delta measurement**
      the source doc's own Deferred" — the marker trips `_is_non_dispatchable`
      (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own line, so
      `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely still
      blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start of its
      own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it reads
      as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note — read
      the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the block.
      Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`.** Its checkbox reads (truncated):
      "[SCRIPT] P1. **Cross-cutting data-completion prep residuals — `data_completion_to_100_all_ag_2026_06_21.md` Step"
      — the marker trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not
      open its own line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is
      genuinely still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to
      the start of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation
      line) so it reads as a declared hold. If it is already resolved (several of these carry a dated
      `RULED`/`DESIGN DECIDED` note — read the full todo before acting), rewrite the trigger phrase so the marker no
      longer appears anywhere in the block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in `plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md`.**
      Its checkbox reads (truncated): "[DIAG] P3. Delete the 916 HYPERLIQUID + 642 ASTER redundant legacy
      `defi`/`perp_funding` rows and rebuild the defi" — the marker trips `_is_non_dispatchable`
      (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own line, so
      `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely still
      blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start of its
      own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it reads
      as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note — read
      the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the block.
      Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06_finalize.md`.** Its checkbox reads (truncated): "[DOC]
      P2. **Re-check the Deferred items**: (a) the 2 conflict-parked BLOCKED‑OPERATOR-DECISION items" — the marker trips
      `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own line, so
      `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely still
      blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start of its
      own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it reads
      as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note — read
      the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the block.
      Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in `plans/active/infra_capture_and_devops_leftovers_2026_07_06.md`.**
      Its checkbox reads (truncated): "[INFRA] P1. **RULED 2026-08-06 (operator): AUTHORIZED — proceed with the
      disposable-IP probe.** The" — the marker trips `_is_non_dispatchable`
      (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own line, so
      `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely still
      blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start of its
      own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it reads
      as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note — read
      the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the block.
      Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/infra_capture_and_devops_leftovers_finalize_2026_07_25.md`.** Its checkbox reads (truncated): "[DOC]
      P2. Re-run this finalize plan's parent-reconciliation once any of the 4 remaining `BLOCKED‑*` items on" — the
      marker trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its
      own line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely
      still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start
      of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it
      reads as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note
      — read the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the
      block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in `plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md`.**
      Its checkbox reads (truncated): "[TEST] P2. **Repair the repo-wide E2E login helper contract (3-step chain,
      combined — the source doc's own todos 2" — the marker trips `_is_non_dispatchable`
      (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own line, so
      `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely still
      blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start of its
      own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it reads
      as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note — read
      the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the block.
      Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md`.** Its checkbox reads (truncated): "[SCRIPT]
      P1. **Kalshi execution credential reshape + live paper-order verify.** Todo 1: read the existing" — the marker
      trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own
      line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely
      still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start
      of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it
      reads as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note
      — read the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the
      block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/sports_satellite_ao_dispatch_batch10_2026_08_06_finalize.md`.** Its checkbox reads (truncated):
      "[DATA] P3. Reconcile `sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md` — once batch-10 todo 1" — the
      marker trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its
      own line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely
      still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start
      of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it
      reads as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note
      — read the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the
      block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md`.** Its checkbox reads (truncated):
      "[DOC] P1. **BLOCKED 2026-07-29 (slot-8, `data_engineering`) — batch5 is NOT archivable yet; premature (operator"
      — the marker trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not
      open its own line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is
      genuinely still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to
      the start of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation
      line) so it reads as a declared hold. If it is already resolved (several of these carry a dated
      `RULED`/`DESIGN DECIDED` note — read the full todo before acting), rewrite the trigger phrase so the marker no
      longer appears anywhere in the block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in `plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md`.**
      Its checkbox reads (truncated): "[DATA][BLOCKED‑UPSTREAM-OUTAGE] P2. Re-launch the instruments-service
      Transfermarkt PLAYER_VALUES backfill scoped" — the marker trips `_is_non_dispatchable`
      (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own line, so
      `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely still
      blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start of its
      own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it reads
      as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note — read
      the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the block.
      Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`.** Its checkbox reads
      (truncated): "[DOCS] P2. **RULED 2026-08-06 (operator), option A [WORKER REC]: one scoped retag pass between
      scheduled auditor" — the marker trips `_is_non_dispatchable`
      (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own line, so
      `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely still
      blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start of its
      own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it reads
      as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note — read
      the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the block.
      Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/issues/credential_ask_orphan_checker_ping_format_stale_2026_07_27.md`.** Its checkbox reads
      (truncated): "[SCRIPT] P3. Consider whether an IAM-permission gap (names the exact missing role/permission + exact
      remedy" — the marker trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`) but
      does not open its own line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false).
      If it is genuinely still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral
      tag) to the start of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated
      continuation line) so it reads as a declared hold. If it is already resolved (several of these carry a dated
      `RULED`/`DESIGN DECIDED` note — read the full todo before acting), rewrite the trigger phrase so the marker no
      longer appears anywhere in the block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/issues/deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md`.** Its checkbox reads
      (truncated): "[INFRA] P3. **Final drain confirmation on/after 2026-08-09.** Re-run `gcs_bucket_stats.py` for" —
      the marker trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open
      its own line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is
      genuinely still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to
      the start of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation
      line) so it reads as a declared hold. If it is already resolved (several of these carry a dated
      `RULED`/`DESIGN DECIDED` note — read the full todo before acting), rewrite the trigger phrase so the marker no
      longer appears anywhere in the block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md`.** Its checkbox reads (truncated):
      "[DATA] P2. **RULED 2026-08-06 (operator): proceed now.** Signed off to schedule the `--apply` against the full" —
      the marker trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open
      its own line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is
      genuinely still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to
      the start of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation
      line) so it reads as a declared hold. If it is already resolved (several of these carry a dated
      `RULED`/`DESIGN DECIDED` note — read the full todo before acting), rewrite the trigger phrase so the marker no
      longer appears anywhere in the block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md`.** Its checkbox reads (truncated):
      "[SCRIPT] P3. **D4 — `recursive_borrow_paper_smoke.py` is a non-instantiating stub** (`INFRA_GAP`/" — the marker
      trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own
      line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely
      still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start
      of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it
      reads as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note
      — read the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the
      block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md`.** Its checkbox reads
      (truncated): "[SCRIPT][BLOCKED‑UPSTREAM-OUTAGE] P2. **Retry Transfermarkt's 8 attempted_failed PLAYER_VALUES
      rows** (now the" — the marker trips `_is_non_dispatchable`
      (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own line, so
      `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely still
      blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start of its
      own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it reads
      as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note — read
      the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the block.
      Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`.** Its checkbox reads
      (truncated): "[DATA] P2. **RULED 2026-08-06: vendor-verify first (refined option C) — fix root cause if vendor CAN
      return data," — the marker trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`)
      but does not open its own line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared:
      false). If it is genuinely still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a
      permanent-deferral tag) to the start of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or
      a dedicated continuation line) so it reads as a declared hold. If it is already resolved (several of these carry a
      dated `RULED`/`DESIGN DECIDED` note — read the full todo before acting), rewrite the trigger phrase so the marker
      no longer appears anywhere in the block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`.** Its checkbox reads (truncated):
      "[VERIFY] P2. Depends on the P1 backfill above. **Census re-run 2026-07-30 (slot 3) against a snapshotted
      canonical" — the marker trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`) but
      does not open its own line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false).
      If it is genuinely still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral
      tag) to the start of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated
      continuation line) so it reads as a declared hold. If it is already resolved (several of these carry a dated
      `RULED`/`DESIGN DECIDED` note — read the full todo before acting), rewrite the trigger phrase so the marker no
      longer appears anywhere in the block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/issues/sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md`.**
      Its checkbox reads (truncated): "[CODE] P2. Execute the FINAL decided fix (retire OR
      scaffold-with-BLOCKED‑CREDENTIALS, per the operator's answer" — the marker trips `_is_non_dispatchable`
      (`agent-orchestrator/server/regen_backlog_from_plan.py`) but does not open its own line, so
      `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared: false). If it is genuinely still
      blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a permanent-deferral tag) to the start of its
      own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or a dedicated continuation line) so it reads
      as a declared hold. If it is already resolved (several of these carry a dated `RULED`/`DESIGN DECIDED` note — read
      the full todo before acting), rewrite the trigger phrase so the marker no longer appears anywhere in the block.
      Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md`.** Its checkbox reads
      (truncated): "[BACKEND] P2. **DESIGN DECIDED 2026-08-08 (operator ruling, ao round-5 apply item 17): "Let Claude
      pick based on" — the marker trips `_is_non_dispatchable` (`agent-orchestrator/server/regen_backlog_from_plan.py`)
      but does not open its own line, so `check_ao_dispatch_visibility_gate.py` classifies it accidental (declared:
      false). If it is genuinely still blocked, move the non-dispatchable marker (a live BLOCKED‑token, or a
      permanent-deferral tag) to the start of its own line (the checkbox line, right after its `[TAG] P<n>.` prefix, or
      a dedicated continuation line) so it reads as a declared hold. If it is already resolved (several of these carry a
      dated `RULED`/`DESIGN DECIDED` note — read the full todo before acting), rewrite the trigger phrase so the marker
      no longer appears anywhere in the block. Verify:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists this doc's todo with `"declared": false`. (repo: unified-trading-pm)

## Progress Log

- **2026-08-08 (slot 21, infra)** — Filed as part of shipping check_ao_dispatch_visibility_gate.py (see
  ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md). Baseline seeded at the measured 27
  accidental / 24 zero-dispatchable so the gate ratchets down as these land. Not hand-fixed in the same session, per the
  parent issue's own precedent (its Betfair fix was the exception, not the rule) — 26 docs of individual per-todo
  judgment calls is real, separate remediation work, not part of building the gate itself.
