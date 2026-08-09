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
context_scope:
  [
    agent-orchestrator/server/dispatch_visibility_report.py,
    agent-orchestrator/server/regen_backlog_from_plan.py,
    /plans/archive/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md,
    /plans/active/issues/ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md,
  ]
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
- `plans/archive/2026_08/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md` (disk_open=1)
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
- `plans/archive/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md` (disk_open=1)

Most of these are explained by one of the 27 findings below (their sole open todo IS the accidental exclusion); a few
are genuinely, correctly all-DEFERRED/all-BLOCKED docs and need no action.

## Why it matters

Same as the parent issue: a plan renders a live `- [ ]`, `regenerate_active_plan_inventory.py` counts it, the operator
reading the plan sees tracked work — AO never dispatches it, and until this gate existed nothing said so. A
`RULED 2026-08-06 (operator): proceed now` todo that still silently excludes itself is the worst version of this: the
human already made the call and the fleet still never executes it.

## Recommended decision

- [x] ✅ [SCRIPT] P2. **Triage accidental exclusion in `plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md`.**
      Not genuinely blocked — the todo's own prose merely NAMES two marker families as documentation subject matter
      (`BLOCKED-CREDENTIALS` as an example ingestion-gate token, `DEFERRED-BY-DESIGN` as a sibling convention it
      cross-references), and both literal ASCII-hyphen spellings independently matched `_BLOCKED_TOKEN_RE` and
      `_PERMANENT_NON_DISPATCHABLE_RE` respectively — two separate accidental triggers in the same block, not one.
      Rewrote all four occurrences to the non-breaking-hyphen spelling (`BLOCKED‑CREDENTIALS`, `BLOCKED‑marker`,
      `BLOCKED‑ON:<ref>`, `BLOCKED‑<TOKEN>`, `DEFERRED‑BY‑DESIGN`) — the same convention this issue doc's own
      recommended-decision prose already uses for this exact reason. Verified:
      `dispatch_visibility_report --pm-path ../unified-trading-pm --json` for
      `ao_satellite_ao_dispatch_batch6_2026_08_04.md` now shows `excluded: []` (was 1 accidental) and `backlog_open`
      rose 2→3 matching `disk_open=3`.
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-09 (slot-24, infra).** Triage accidental exclusion in
      `plans/active/cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12_finalize_2026_08_08.md`. Moot, not
      accidental: the flagged todo (the `[REVIEW] P2. Reconcile — ... re-launch LIGHTER-ZKSYNC` item) was independently
      completed and checked off `[x] ✅ "DONE 2026-08-09 (slot 28, review craft)"` by another session before this triage
      dispatched. The doc now has a different sole open todo (`[DOC] P2. Archive.`, line 77) which is correctly
      dispatchable — no exclusion, nothing to rewrite. Verified:
      `cd agent-orchestrator && uv run python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`:
      `cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12_finalize_2026_08_08.md` now reports
      `disk_open=1, backlog_open=1, excluded=[]`. (repo: unified-trading-pm)
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-09 (slot-32).** Triage accidental exclusion in
      `plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md`. The flagged todo (the HYPERLIQUID/ASTER
      wire-vs-canonical investigate item) was independently completed and checked off `[x]` by another session on
      2026-08-09 (before this triage dispatched) — it's no longer an open todo, so the accidental-exclusion
      classification no longer applies. Verified via
      `cd agent-orchestrator && uv run python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`:
      `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` now reports `disk_open=3, backlog_open=3, excluded=[]` — no
      rewrite needed. (repo: unified-trading-pm)
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-09 (slot-23).** Triage accidental exclusion in
      `plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md`. Moot, not accidental: the flagged todo
      (`[VERIFY]     P1. Re-measure the billed notify/glue cost`) was independently completed and checked off `[x]` by
      slot 31 on 2026-08-09, and the whole doc — every todo now done — was archived to
      `plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md` (`status: complete`, 0 remaining `- [ ]`).
      No open todo remains on disk for the gate to misclassify, so no rewrite needed. Verified:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists `plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md` at all (doc no longer has any open
      todos to report on). (repo: unified-trading-pm)
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-09 (slot-12, infra).** Triage accidental exclusion in
      `plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md`. Moot, not accidental: the doc's flagged todo (the
      `[VERIFY] P0` 4-item billing/capacity re-measurement sweep) was independently completed by slot-28 on 2026-08-09
      (see that doc's own Progress Log), and with all 9 of the plan's todos now done it was archived to
      `plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md` (`status: complete`) the same day. No open
      todo remains on disk for the gate to misclassify, so no rewrite needed. Verified:
      `cd agent-orchestrator && uv run python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists `ci_satellite_ao_dispatch_batch4_2026_07_31.md` at all (0 hits — doc has no open todos to report
      on). (repo: unified-trading-pm)
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-09 (slot-23).** Triage accidental exclusion in
      `plans/active/ci_satellite_ao_dispatch_batch6_2026_08_08.md` (todo 1, `[INFRA] P0` re-measure fleet CI
      job-minutes). Moot, not accidental: the flagged todo is checked `[x] ✅` in the archived doc
      (`plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_2026_08_08.md`, `status: complete`, 0 remaining `- [ ]`),
      and the doc no longer exists at the `plans/active/` path the finding cited. No open todo remains on disk for the
      gate to misclassify. Verified:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists `ci_satellite_ao_dispatch_batch6_2026_08_08.md` at all. (repo: unified-trading-pm)
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-09 (slot-23).** Triage accidental exclusion in
      `plans/active/ci_satellite_ao_dispatch_batch6_2026_08_08.md` (todo 12, `[VERIFY] P3` skip-tests/skip-<X> per-phase
      delta measurement). Same moot cause as the sibling finding above (same target doc, now archived with every todo —
      including this one — checked `[x] ✅`). Verified via the same `dispatch_visibility_report --json` run: zero hits
      for this doc. (repo: unified-trading-pm)
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
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-09 (slot-24, infra).** Triage accidental exclusion in
      `plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md`. Already fixed by another session, not hand-fixed
      here: the flagged todo's trigger phrase (`...batch5_2026_07_27.md`'s earlier BLOCKED-OPERATOR-DECISION
      classification of this same...`) was rewritten to `...previously operator-decision-gated classification of this
      same...`in`unified-trading-pm@84f363ff6`(slot-2, laptop, 2026-08-09 10:07 UTC+1) — an incidental fix bundled     inside an unrelated 20-file sweep titled "reclassify prek_stash_restore_race NA->planning". No live    `BLOCKED-<TOKEN>`/permanent-deferral marker remains anywhere in the block; the todo was never actually re-blocked     after the 2026-07-28 operator ruling this doc itself describes. Verified:     `cd
      agent-orchestrator && uv run python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm
      --json`    shows`defi_satellite_ao_dispatch_batch6_2026_07_30.md`with`disk_open=1, backlog_open=1, excluded=[]` —
      the todo is correctly dispatchable, no rewrite needed. (repo: unified-trading-pm)
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
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-09 (slot-3, infra).** Triage accidental exclusion in
      `plans/active/infra_capture_and_devops_leftovers_2026_07_06.md`. Genuinely still blocked, AND a live gap worse
      than "accidental" — the checkbox's actual current blocker (a 2026-08-09 slot-9 finding,
      `BLOCKED-DESIGN-SPEC,     checked 2026-08-09 (slot 9, infra)` at line 348) used a token not in
      `_BLOCKED_TOKEN_RE`'s alternation (`DESIGN-SPEC` is not
      `CREDENTIALS|OPERATOR(-DECISION)?|BILLING|UPSTREAM-(OUTAGE|DESIGN)|PLAYWRIGHT|JURISDICTION`) — so this todo was
      not merely mis-classified as accidental, it was **fully dispatchable to AO right now** (`excluded: []`) despite
      the operator's own 2026-08-09 ruling to "leave this checkbox open, do NOT invent a probe design." Fix: retagged
      the checkbox's own head (right after `[INFRA] P1.`) with `BLOCKED-UPSTREAM-DESIGN` — an ALREADY-recognized token
      whose documented shape ("blocked until an upstream design decision lands") is exactly this situation (the probe's
      target/request-pattern/provisioning/teardown spec is missing, not an operator sign-off) — rather than proposing a
      new token unilaterally (the parent issue's own precedent,
      `blocked_     prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md`, explicitly reserves adding new
      tokens for a real decision, not a mechanical retag). Also reworded the stale "AO-dispatchable now" head-banner
      claim and the line-348 continuation note to point back at the new head marker instead of restating an unrecognized
      one. Verified end-to-end via
      `cd agent-orchestrator && uv run python3 -m server.dispatch_visibility_report --pm-path     ../unified-trading-pm --json`:
      this doc now shows `disk_open=1, backlog_open=0, excluded=[{"declared": true}]` (was `backlog_open=1, excluded=[]`
      — i.e. genuinely dispatchable moments earlier). Also ran the actual QG gate,
      `uv run python3 scripts/quality_gates/check_ao_dispatch_visibility_gate.py`: exit 0,
      `1 accidental exclusions     (baseline 0, buffer 5)` — within the existing ratchet buffer, no `--update-baseline`
      needed. (repo: unified-trading-pm)
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
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-09 (slot-27, infra).** Triage accidental exclusion in
      `plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md`. Moot, not accidental: the flagged todo (the
      `[TEST] P2` E2E login helper contract repair) was independently completed and checked off
      `[x] ✅ DONE     2026-08-09 (slot-28, infra), unified-trading-system-ui@15e4b4bc` by another session, and with all
      25 of the plan's todos now done it was archived to
      `plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md` (`status: archived`, superseded_by
      `infra_satellite_ao_dispatch_batch12_2026_08_09`). No open todo remains on disk at the `plans/active/` path for
      the gate to misclassify. Verified:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      no longer lists `infra_satellite_ao_dispatch_batch1_2026_07_26.md` at all under either the active or archive path
      (0 hits — only the distinct `batch10`-`batch14` docs appear). (repo: unified-trading-pm)
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
      `plans/archive/2026_08/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`.** Its checkbox reads
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
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-09 (slot-3, infra).** Triage accidental exclusion in
      `plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`. Already fixed by another
      session, not hand-fixed here: the flagged todo's trigger phrase
      (`AF-classification decision     (BLOCKED-OPERATOR-DECISION, filed 2026-08-06 slot 13)`) was rewritten to
      non-marker prose
      (`AF-classification     decision (an operator-decision question filed 2026-08-06 slot 13, RULED per the note above the same day —     option C, "vendor-verify first," chosen)`)
      in `unified-trading-pm@84f363ff6` (slot-2, laptop, 2026-08-09 10:07 UTC+1) — the same incidental fix bundled
      inside the unrelated 20-file "reclassify prek_stash_restore_race NA->planning" sweep already noted above for the
      `defi_satellite_ao_dispatch_batch6` todo. No live `BLOCKED-<TOKEN>`/permanent-deferral marker remains anywhere in
      the block; the todo was never actually re-blocked after the operator's 2026-08-06 RULED decision this doc itself
      describes. Verified:
      `cd agent-orchestrator && .venv/bin/python3 -m server.dispatch_visibility_report --pm-path ../unified-trading-pm --json`
      shows `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` with
      `disk_open=4, backlog_open=4,     excluded=[]` — all 4 open todos in that doc (incl. this one) are correctly
      dispatchable, no rewrite needed. (repo: unified-trading-pm)
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
- [x] ✅ [SCRIPT] P2. **Triage accidental exclusion in
      `plans/active/issues/sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md`.**
      Genuinely still blocked, not accidental: the target doc's own DECISION/DISCRIMINATOR sections (lines 153-322) show
      the RETIRE recommendation is only a recommendation — "operator sign-off requested via /blocked (slot 5,
      2026-07-24)... **Why sign-off is still required before execution**" — with no Progress Log entry showing the
      operator ever answered. Retagged the checkbox line's own `[CODE] P2.` prefix with an explicit
      `BLOCKED-OPERATOR-DECISION.` marker (matches `_BLOCKED_TOKEN_RE`'s `OPERATOR(-DECISION)?` alternative) so it opens
      its own line instead of being buried inside "scaffold-with-BLOCKED-CREDENTIALS" prose; also converted the two
      other inline `BLOCKED-CREDENTIALS` mentions in that same todo block to the non-breaking-hyphen spelling
      (`BLOCKED‑CREDENTIALS`) so they stay documentation-only and don't independently trip the live-token check.
      Verified: `dispatch_visibility_report --pm-path ../unified-trading-pm --json` for this doc now shows
      `"declared": true` (was `false`); still correctly excluded (`disk_open=1, backlog_open=0` — genuinely blocked, not
      dispatchable) since the operator decision remains outstanding. Fleet-wide accidental count: 26→25 (repo:
      unified-trading-pm).
- [ ] [SCRIPT] P2. **Triage accidental exclusion in
      `plans/archive/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md`.** Its checkbox reads
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
- **2026-08-08 (slot 3, infra)** — Fixed todo 1 (`ao_satellite_ao_dispatch_batch6_2026_08_04.md`'s `[DOC] P3`
  task_template.md-documentation todo). Two independent accidental triggers in the same block, not one: the todo's own
  prose named `BLOCKED-CREDENTIALS` (an example token) and `DEFERRED-BY-DESIGN` (a sibling convention) purely as
  documentation subject matter, and each literal ASCII-hyphen spelling matched a different gate regex
  (`_BLOCKED_TOKEN_RE` and `_PERMANENT_NON_DISPATCHABLE_RE` respectively). Rewrote both plus the doc's other two
  `BLOCKED-` mentions to the non-breaking-hyphen spelling already used elsewhere in this issue doc. Verified via
  `dispatch_visibility_report --json`: the doc's `excluded` list is now empty, `backlog_open` 2→3.
- **2026-08-08 (slot 29, infra)** — Fixed the
  `sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md` todo. Unlike the
  two prior fixes, this one is a GENUINE, still-open block (operator sign-off on the retire-vs-scaffold decision was
  requested via `/blocked` 2026-07-24 and never answered), so the fix declares the hold rather than removing it:
  retagged the checkbox's own `[CODE] P2.` prefix with `BLOCKED-OPERATOR-DECISION.` (opens its own line, matches
  `_BLOCKED_TOKEN_RE`'s `OPERATOR(-DECISION)?` alternative) and converted the two incidental `BLOCKED-CREDENTIALS`
  mentions later in the same block to the non-breaking-hyphen spelling so they stay documentation-only. Verified via
  `dispatch_visibility_report --json`: the doc's todo now shows `"declared": true` (still correctly excluded — genuinely
  blocked, not a false negative). Fleet-wide accidental count 26→25.

- **2026-08-09 (slot 3, interactive)** — **The accidental count moves 25 → 34, and none of the increase is new debt.**
  Read this before triaging further, or the jump looks like a regression.

  Two implementations of this gate shipped in parallel on 2026-08-08 (slot 3 and slot 4 both worked
  `ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md`; the operator was shown the collision and
  chose to let both run). They were merged into one 2026-08-09 — `agent-orchestrator@03e1809`, plus the redundant second
  PM script deleted — keeping this module's `_plan_contributes_briefs` scope filter and folding in three changes from
  the other implementation. Two of them change the numbers in this doc:

  1. **The declaration rule tightened to the checkbox line's head only.** It previously also honoured a marker at the
     head of a CONTINUATION line. Measured against the live corpus, that absolved the wrong todos: of 9 exclusions
     declared on that basis, **7 were prettier 120-char soft-wraps landing mid-sentence** (e.g.
     `BLOCKED-OPERATOR-DECISION item)? (b) has ...`), and **2 of those 7 were RESOLUTION notes** saying the marker no
     longer applied (`` `BLOCKED-CREDENTIALS` is now STALE, clearing it ``). Prose wrapping is a formatting artifact, so
     a rule keyed on "starts a line" is satisfiable by accident — which rebuilds the false-absolution this gate exists
     to catch, inside the gate. So ~10 todos previously counted DECLARED are now correctly ACCIDENTAL. **They were
     always accidental; the detector just could not see them.** That is the whole of the 25 → 34 move, and it is the
     opposite of a baseline raise absorbing debt (contrast
     `/plans/archive/issues/operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md`, which is the bad kind).
  2. **A third finding exists now: ineffective declarations**, with its own `max_ineffective_declarations` baseline
     (currently **4**, all `BLOCKED-PREREQUISITES`). These are the INVERSE failure and are NOT in this doc's 25 — a
     marker in the correct structural position whose token is absent from `_BLOCKED_TOKEN_RE`, so nothing excludes the
     todo and AO dispatches it while every human reads it as held. That is
     `/plans/active/issues/blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md`, still live. Any
     check that only inspects EXCLUDED todos is structurally blind to it, which is why it survived three prior fixes.
     They need a decision, not a rewording: add the token to the dispatcher's vocabulary, or retag to an existing one.
     Note `/plans/active/sports_closeout_track_s2_foldin_2026_07_25.md` argues its `BLOCKED-PREREQUISITES` items are not
     accurately described by any existing token — an argument for adding it upstream.

  Also: `_raw_open_todos` (a hand-mirrored copy of `_parse_open_todos`'s frontmatter/fence/strikethrough walk) was
  deleted in favour of a recording spy on `_is_non_dispatchable`, so the real walk now reports every block it evaluates.
  ~70 lines of duplicated oracle gone — a second copy of the parser was the exact drift risk the source issue warned
  about. Tests 9 → 14, covering the soft-wrap and resolution-note regressions and all three ineffective-declaration
  cases.

  **Triage impact**: the ~10 newly-visible accidental exclusions are not yet enumerated as todos in this doc. Re-run
  `python -m server.dispatch_visibility_report --pm-path <pm> --json` for the current per-doc list before continuing —
  do not work from this doc's existing 25-item enumeration alone, it predates the rule change.

- **context-scout 2026-08-09**: populated context_scope (4 entries).
- **2026-08-09 (slot 23, infra)** — Fixed the `ci_satellite_ao_dispatch_batch1_2026_07_26.md` todo. Moot, not
  accidental: its sole flagged todo was already checked off by slot 31 on 2026-08-09, and with every todo in the doc now
  done it was archived to `plans/archive/2026_08/` (`status: complete`). Confirmed via
  `dispatch_visibility_report --json`: the doc no longer appears in the report at all (zero open todos left to
  misclassify).
- **2026-08-09 (slot 12, infra)** — Fixed the `ci_satellite_ao_dispatch_batch4_2026_07_31.md` todo. Same "moot, not
  accidental" pattern as the batch1/batch10 fixes above: the flagged `[VERIFY] P0` billing sweep todo was completed by
  slot-28 on 2026-08-09, and with all 9 of that plan's todos done it archived to `plans/archive/2026_08/` the same day.
  Confirmed via `dispatch_visibility_report --json`: the doc no longer appears in the report at all.
- **2026-08-09 (slot 23, infra)** — Fixed both `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todos (todo 1
  `[INFRA] P0` re-measure fleet CI job-minutes, and todo 12 `[VERIFY] P3` skip-tests/skip-<X> delta measurement). Same
  "moot, not accidental" pattern as the batch1/batch4 fixes above: both flagged todos are checked `[x] ✅` in the
  now-archived doc (`plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_2026_08_08.md`, `status: complete`, 0
  remaining `- [ ]`), so no open todo remains on disk for the gate to misclassify. Followed the note above the
  2026-08-09 (slot 3) entry to re-run the live report rather than trust this doc's stale 25-item enumeration —
  re-running `dispatch_visibility_report --json` confirmed `ci_satellite_ao_dispatch_batch6_2026_08_08.md` no longer
  appears at all (zero hits, both under its old active path and the new archive path). Fixed both todos in one commit
  since they target the identical already-resolved doc with identical evidence.
- **2026-08-09 (slot 24, infra)** — Fixed the
  `cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12_finalize_2026_08_08.md` todo. Same "moot, not accidental"
  pattern as the batch1/batch4/batch6/cefi_batch10 fixes above: the flagged `[REVIEW] P2` reconcile/re-launch item was
  already checked off `[x]` by slot-28 (review craft) before this triage dispatched. Followed the 2026-08-09 (slot 3)
  note to re-run the live report rather than trust the stale enumeration — confirmed
  `disk_open=1, backlog_open=1, excluded=[]` for that doc (its remaining open todo, `[DOC] P2. Archive.`, is correctly
  dispatchable, not excluded).
- **2026-08-09 (slot 24, infra)** — Fixed the `defi_satellite_ao_dispatch_batch6_2026_07_30.md` todo. A different flavor
  of "already resolved elsewhere": not a checked-off todo this time, but the trigger phrase itself
  (`earlier BLOCKED-OPERATOR-DECISION classification`) was already rewritten to non-marker prose
  (`previously operator- decision-gated classification`) by `unified-trading-pm@84f363ff6` (slot-2, laptop, 2026-08-09),
  an incidental fix bundled inside an unrelated 20-file doc sweep. Confirmed via `dispatch_visibility_report --json`:
  `disk_open=1, backlog_open=1, excluded=[]` for that doc — its sole open todo is correctly dispatchable, no rewrite
  needed here.
- **2026-08-09 (slot 3, infra)** — Fixed the `infra_capture_and_devops_leftovers_2026_07_06.md` todo. Different from
  every "moot" fix above — this one was a live, worse-than-accidental gap: the doc's sole open todo (the disposable-IP
  rate-limit probe) carries a genuine, current block (slot-9's 2026-08-09 finding that the probe design spec itself is
  missing, `/plans/active/issues/rate_limit_probe_vm_authorized_no_design_spec_2026_08_09.md`), but the marker used to
  express it, `BLOCKED-DESIGN-SPEC`, is not a token `_BLOCKED_TOKEN_RE` recognizes — so the todo was not merely
  mis-classified as accidental, it was **fully dispatchable to AO** (`excluded: []`) despite the operator's explicit
  ruling to leave it open and not invent a design. Retagged the checkbox head with `BLOCKED-UPSTREAM-DESIGN` — already
  in the recognized alternation, and its documented intent ("blocked until an upstream design decision lands") is an
  exact semantic match — rather than proposing a new token unilaterally. Verified via
  `dispatch_visibility_report --json`: `disk_open=1, backlog_open=0, excluded=[{"declared": true}]` (was
  `backlog_open=1, excluded=[]`). Also ran the real QG gate (`check_ao_dispatch_visibility_gate.py`): exit 0, fleet-wide
  `1 accidental exclusion (baseline 0, buffer 5)` — comfortably within the ratchet buffer, no `--update-baseline`
  needed. unified-trading-pm@(pending).
- **2026-08-09 (slot 3, infra)** — Fixed the `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` todo. Same
  "already resolved elsewhere" flavor as the `defi_satellite_ao_dispatch_batch6` fix above and by the SAME commit: the
  flagged todo's trigger phrase (`AF-classification decision (BLOCKED-OPERATOR-DECISION, filed 2026-08-06 slot 13)`) was
  rewritten to non-marker prose by `unified-trading-pm@84f363ff6` (slot-2, laptop, 2026-08-09 10:07 UTC+1), the same
  incidental 20-file sweep. Confirmed via `dispatch_visibility_report --json`:
  `disk_open=4, backlog_open=4, excluded=[]` for that doc — all 4 open todos, including this one, are correctly
  dispatchable, no rewrite needed here.
- **2026-08-09 (slot 27, infra)** — Fixed the `infra_satellite_ao_dispatch_batch1_2026_07_26.md` todo. Same "moot, not
  accidental" pattern as the ci batch1/batch4/batch6 and cefi_batch10 fixes above: the flagged `[TEST] P2` E2E login
  helper contract todo was already checked off `[x] ✅` by slot-28 (infra) on 2026-08-09
  (`unified-trading-system-ui@15e4b4bc`), and with all 25 of that plan's todos done it was archived same-day to
  `plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md`. Confirmed via
  `dispatch_visibility_report --json`: the doc no longer appears in the report at all (zero open todos left to
  misclassify).
