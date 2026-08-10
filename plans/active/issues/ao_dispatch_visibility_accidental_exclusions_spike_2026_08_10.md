---
doc_type: issue
title: >-
  ao-dispatch-visibility gate red — 6 accidental (undeclared) exclusions vs baseline 0 + buffer 5, blocking every
  unified-trading-pm ship
summary: >-
  `check_ao_dispatch_visibility_gate.py` FAILS on unified-trading-pm with 6 accidental (undeclared) exclusions against a
  baseline of 0 (+ buffer 5). All 6 are todos in 4 docs edited 2026-08-10 by other agents/slots (batch11, kaiko
  finalize, tradfi databento, plan_hygiene issue) — none in this doc. Verified pre-existing: the gate fails
  byte-identically at the merge-base of today's unrelated commits (`026ed5ab52`) and at HEAD, and the flagged docs are
  untouched by this task's commits. Because quality-gates.sh is the per-repo commit boundary, this red blocks every PM
  ship until the 6 todos either declare their BLOCKED-/DEFERRED-BY-DESIGN/stretch marker at the start of its own line or
  are rewritten to not trip the marker.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, dispatch-visibility, ratchet, repo-blocker, qg-red]
related:
  - /codex/12-agent-workflow/async-wait-and-poll-discipline.md
  - /plans/archive/issues/ao_dispatch_visibility_gate_regression_sports_blocked_upstream_marker_2026_08_08.md
created: "2026-08-10"
author: slot-5 (AO worker, dispatch quickmerge_isolated_worktree_missing_sibling_pm_checkout-51e7e04d12b7)
parent_epic: infrastructure_master
priority: P1
drift_direction: advance-code
depends_on: []
assigned_vm: planning
execution_scope: orchestrator-agent
source: >-
  Found while running quality-gates.sh for an unrelated quickmerge-isolation task on slot 5, 2026-08-10: the
  ao-dispatch-visibility post-gate check failed with 6 accidental exclusions vs baseline 0 + buffer 5. Verified
  pre-existing at merge-base 026ed5ab52. Repo-blocker RB-afb45a14 + escalation agt-cced28 filed.
resolved_by: ""
locked_by:
---

# ao-dispatch-visibility gate red — 6 accidental exclusions spike

## What I found

`bash scripts/quality-gates.sh` on unified-trading-pm fails at the `ao-dispatch-visibility` post-gate check:

```
check_ao_dispatch_visibility_gate: FAILED
  - accidental (undeclared) exclusions grew: 6 > baseline 0 + buffer 5
```

Baseline (`scripts/quality_gates/ao_dispatch_visibility_baseline.yaml`, `last_updated: 2026-08-09`):
`max_accidental_exclusions: 0`, `accidental_exclusions_buffer: 5`.

The 6 accidental exclusions (all `declared: false`), by doc:

| Doc                                                                                                 | Todo                                                                                                            | disk_open / backlog_open |
| --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------ |
| `plans/active/ao_satellite_ao_dispatch_batch11_2026_08_09.md`                                       | `[SCRIPT] P2. Fix fix_frontmatter.py's get_first_paragraph_after_heading() hard truncation`                     | 1 / 0                    |
| `plans/active/kaiko_provider_removal_2026_08_10_finalize.md`                                        | `[DOCS] P2. Rescope glassnode_kaiko_credential_ask_2026_08_09.md to Glassnode only`                             | 4 / 3                    |
| `plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md`                       | `[DOCS] P1. Un-gate data_completion_tradfi_2026_07_15.md's 2 billing-blocked todos`                             | 5 / 2                    |
| `plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md`                       | `[DOCS] P1. Un-gate tradfi_phase_d_terminal_gate_2026_07_24.md's 2 billing-blocked todos, PRESERVE separate...` | 5 / 2                    |
| `plans/active/tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md`                       | `[DOCS] P2. Add a Databento-access-confirmed note to tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`   | 5 / 2                    |
| `plans/active/issues/plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md` | `[OPERATOR] P1. Decide how to break the assigned_vm:NA corpus size / LDR→main promote deadlock`                 | 3 / 2                    |

## Why it matters

quality-gates.sh is the per-repo commit boundary (HARD RULE — commit only from a green tree). This red blocks **every**
unified-trading-pm ship (plan docs, codex docs, plan flips) until the 6 todos are fixed. It is blocking at least one
already-completed unrelated task (quickmerge isolation regression test + plan flip, this session).

The remedy (from the gate itself): for each newly-accidental exclusion, either DECLARE it (put the
BLOCKED-<token>/DEFERRED-BY-DESIGN/stretch marker at the start of its own line) or rewrite the todo so it no longer
trips the marker. If a reviewed/justified exception, re-run `--update-baseline` and explain in the commit message —
never hand-edit the YAML.

## Pre-existing verification

Verified the red is NOT caused by this session's work:

- This task's commits touch only `tests/test_quickmerge_isolated_sibling_pm.bats` + this issue's plan doc.
- The gate fails byte-identically at the merge-base `026ed5ab52` (before these commits) and at HEAD.
- The 6 flagged docs are all edited today by other agents/slots.

## Recommended decision

Dispatch a fix-worker to declare or rewrite the 6 accidental exclusions (each is a small marker-placement fix in its own
doc), re-run quality-gates.sh to green, then the blocker clears and PM ships resume. If any of the 6 is a genuine
justified exception, `--update-baseline` with the rationale in the commit message.

## Todos

- [ ] [SCRIPT] P1. **Fix the 6 accidental exclusions flagged by check_ao_dispatch_visibility_gate.py** — for each: put
      the BLOCKED-<token>/DEFERRED-BY-DESIGN/stretch marker at the start of its own line, or rewrite so it no longer
      trips the marker; then `bash scripts/quality-gates.sh` green. Docs:
      `ao_satellite_ao_dispatch_batch11_2026_08_09.md` (P2 fix_frontmatter truncation),
      `kaiko_provider_removal_2026_08_10_finalize.md` (P2 Rescope glassnode),
      `tradfi_databento_billing_unblock_vix_yahoo_floor_2026_08_10.md` (P1 Un-gate data_completion, P1 Un-gate
      tradfi_phase_d, P2 Databento-access-confirmed note),
      `issues/plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md` (P1 decide NA-corpus/LDR
      promote deadlock). Repo: unified-trading-pm.
