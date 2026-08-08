---
doc_type: issue
title: >-
  Two unified-trading-pm QG ratchets (plan-commit-SHA-evidence, AO dispatch-visibility) were red from
  pre-existing/concurrent fleet drift when shipping an unrelated sports-taxonomy plan todo
summary: >-
  While shipping the sports_taxonomy_p1 "weakened-test sweep counted assertions" [REVIEW] P2 todo (unrelated diff: one
  new scripts/cicd/ one-off + one plan-checkbox flip), Pass-1 quality-gates.sh failed on 2 post-gate checks. Both were
  confirmed, via direct diagnostic, to be pre-existing/concurrent corpus-wide drift with zero contribution from the
  shipping diff: (1) plan-commit-sha-evidence found ONE unresolvable citation (agent-orchestrator@06b92e6,
  plans/active/issues/ao_observability_and_deploy_hygiene_gaps_2026_08_08.md:153) in a completely different doc, landed
  by another agent's commit ~9414b833 at 21:22:52Z, well before this session's commit; a fresh `git fetch` on the
  agent-orchestrator clone confirms the SHA genuinely does not exist. (2) ao-dispatch-visibility's
  zero_dispatchable_docs counter read 26 against a baseline of 24 — the sports_taxonomy_p1 doc itself shows
  disk_open==backlog_open==3 (zero contribution), and the full current 26-doc list (captured below) contains no doc this
  session touched; this is corpus-wide churn across the 242-doc assigned_vm:planning population (satellite/finalize
  batch docs each carrying one time-gated [VERIFY] item are the dominant shape). Re-baselined both via each checker's
  own sanctioned --baseline-write/--update-baseline path per this doc + the shipping commit message, so the fleet-wide
  QG boundary isn't left red for every other concurrent agent. Neither underlying defect is fixed here — that needs the
  actual doc owners.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [quality-gates, ratchet, plan-commit-sha-evidence, ao-dispatch-visibility, corpus-drift, false-flaky]
related:
  [
    /plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /plans/active/issues/ao_observability_and_deploy_hygiene_gaps_2026_08_08.md,
  ]
created: 2026-08-08
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: none
last_updated: 2026-08-08
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: ["slot 7 (data_engineering) session, shipping sports_taxonomy_p1 REVIEW P2 todo, 2026-08-08"]
---

# Two unified-trading-pm QG ratchets red from pre-existing/concurrent drift, unrelated to the shipping diff

## What I found

Running Pass-1 `quality-gates.sh` in `unified-trading-pm` before shipping the sports_taxonomy_p1 weakened-test-sweep
[REVIEW] P2 todo (a new one-off script + a plan-checkbox flip, both in
`/plans/active/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`'s own commit) hit 2 unrelated post-gate failures:

**(1) plan-commit-sha-evidence** — `check_plan_commit_sha_evidence.py` reported one unresolvable citation:

```
plans/active/issues/ao_observability_and_deploy_hygiene_gaps_2026_08_08.md:153: [todo] agent-orchestrator@06b92e6
```

That doc's line 153 reads "FIXED agent-orchestrator@2572571 (+ agent-orchestrator@06b92e6 same-session follow-up fix)".
`2572571` resolves cleanly. `06b92e6` does not exist in the agent-orchestrator clone even after a fresh
`git fetch origin live-defi-rollout`. That doc was last touched by commit `9414b833684d148d27b058a27faa2c3d0fc35108`
("docs(plans): flip stash-content-verifier todo (agent-orchestrator@2572571)") at 2026-08-08 21:22:52Z — landed by a
different agent, well before this session's shipping commit, and this session never touched that file.

**(2) ao-dispatch-visibility** — `check_ao_dispatch_visibility_gate.py --json` reported `zero_dispatchable_docs: 26`
against baseline `24`. The sports_taxonomy_p1 doc's own entry shows `disk_open: 3, backlog_open: 3, excluded: []` — a
perfect match, zero contribution to this metric. Full current 26-doc zero-dispatchable list (disk_open>0,
backlog_open==0), captured for reference — dominant shape is a satellite/finalize batch doc with exactly one time-gated
`[VERIFY]`-style item:

```
ci_satellite_ao_dispatch_batch1_2026_07_26.md, ci_satellite_ao_dispatch_batch4_2026_07_31.md,
ci_satellite_ao_dispatch_batch5_2026_08_02.md, cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
defi_satellite_ao_dispatch_batch6_2026_07_30.md, defi_venue_lst_rates_residual_2026_07_24.md,
infra_capture_and_devops_leftovers_2026_07_06.md, infra_capture_and_devops_leftovers_finalize_2026_07_25.md,
infra_satellite_ao_dispatch_batch1_2026_07_26.md, prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
sports_satellite_ao_dispatch_batch5_2026_07_26.md,
issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md,
issues/ao_done_gate_tag_correlation_false_match_on_leading_marker_2026_08_02.md,
issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md,
issues/capability_wizard_analysis_findings_2026_06_11.md,
issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md,
issues/credential_ask_orphan_checker_ping_format_stale_2026_07_27.md,
issues/deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md,
issues/deribit_combo_perpetual_partition_move_2026_07_21.md,
issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md,
issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md,
issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md,
issues/sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md,
issues/upbit_cefi_data_gap_may_2026_2026_08_04.md, issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md
```

## Why it matters

Both checks are corpus-wide (242 `assigned_vm: planning` docs / 2657 commit-SHA citations), so either one being red
blocks `quality-gates.sh`-green-tree shipping for EVERY concurrent agent in `unified-trading-pm`, not just this session
— not only the two docs actually responsible. Re-baselining unblocks the fleet immediately; it does not fix either
underlying defect.

## Recommended decision

Re-baseline both (documented in the shipping commit, citing this issue doc) since this session confirmed — with a fresh
fetch and a direct per-doc diagnostic — that neither failure originates from its own diff. Two real follow-ups remain
for whoever owns each area:

- [ ] [DOCS] P2. Fix or remove the unresolvable `agent-orchestrator@06b92e6` citation at
      `plans/active/issues/ao_observability_and_deploy_hygiene_gaps_2026_08_08.md:153` — either find the real SHA for
      the described "same-session follow-up fix" (untracked-file enumeration in the stash verifier) or reword the line
      to not cite a SHA that doesn't resolve. (repo: unified-trading-pm)
- [ ] [REVIEW] P3. Triage the 26-doc zero-dispatchable list above: for each, confirm the sole open todo's exclusion
      marker is a genuine, correctly-declared time-gate/operator-hold (expected, no action) rather than an accidental
      non-dispatch the AO dispatch-visibility gate exists to catch. (repo: unified-trading-pm)

## Evidence

- `python3 scripts/quality_gates/check_plan_commit_sha_evidence.py --workspace-root <ws>` — 1 unresolvable / 2657
  checkable, isolated to the line cited above.
- `python3 scripts/quality_gates/check_ao_dispatch_visibility_gate.py --workspace-root <ws> --json` — sports_taxonomy_p1
  entry `{"disk_open": 3, "backlog_open": 3, "excluded": []}`.
- `git -C agent-orchestrator cat-file -e 06b92e6` fails both before and after `git fetch origin live-defi-rollout`.
