---
doc_type: issue
title: "Plan-reconciler findings — tradfi tranche 2026-08-07"
created: 2026-08-07
author: plan_reconciler
source: agt-ec6642
locked_by: none
asset_group: tradfi
status: open
nature: issue
tags: [plan_reconciler, tradfi, reconciliation, auto-generated]
parent_epic: plan_hygiene_master
summary:
  "Automated plan_reconciler run for the tradfi topic tranche — fan-out DETECT + adversarial VERIFY. 61 docs in scope
  (27 grace, 34 non-grace)."
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
related: []
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-07
resolved_by: ""
---

## Flips verified

(None — no open todos with HARD evidence of completion found in non-grace docs)

## Contradictions

(Pending hunter results)

## Doc-drift

(Pending hunter results)

## Hygiene fixes

1. **Zero-checkbox doc → canonical todos** (`mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md`):
   Converted 3 prose follow-up items into canonical `- [ ] [INFRA] P1.` todos (strace/py-spy reproduction, systemd
   cgroup reaper check, pkill-guard host-wide install). Commit: `bacb5ed66`.

## Filed

## Archive candidates (operator review)

4 fully-done docs identified (0 open todos, all `[x]`):

| Doc                                                      | Open | Done | Locked?                   | Cross-refs | Verdict                                                                                    |
| -------------------------------------------------------- | ---- | ---- | ------------------------- | ---------- | ------------------------------------------------------------------------------------------ |
| `instruments_satellite_ao_dispatch_batch1_2026_07_27.md` | 0    | 5    | No                        | 4          | **Deferred** — 4 cross-refs in other tranches; sharded run can't verify all referrers safe |
| `autonomous_session_operator_decisions_2026_07_25.md`    | 0    | 2    | No                        | 42         | **Deferred** — 42 cross-references; too risky in a sharded run                             |
| `tradfi_backfill_oom_remediation_2026_06_24.md`          | 0    | 12   | YES (`live-defi-rollout`) | 8          | **BLOCKED** — locked plan, never auto-archive                                              |
| `tradfi_canonical_path_migration_design_2026_07_19.md`   | 0    | 1    | YES (`live-defi-rollout`) | 9          | **BLOCKED** — locked plan, never auto-archive                                              |

## Refuted (dropped by verify)

## Coverage (hunters / batches / docs)

- Tranche: tradfi
- Docs in scope: 61 (20 active plans + 37 issues + 1 epic + 3 normative refs)
- Grace (read-only): 27
- Non-grace (editable): 34
- Normative refs: PLAN_FORMAT.md, task_template.md, INDEX.md, ACTIVE_INDEX.md
- Hunters dispatched: 2 (missed-flip + contradiction), results pending
- Direct scan: 4 archive candidates checked, 1 zero-checkbox converted

## Deferred work after 2026-08-07

| Item                                                                                         | State / why deferred                                                                                                                                                                             | Blocked on                  |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------- |
| Hunter results (missed-flip + contradiction)                                                 | Background agents dispatched but not yet returned. Their findings, if any, should be folded into the next reconciler run or this doc on the next session.                                        | Background agent completion |
| Archive: `instruments_satellite_ao_dispatch_batch1_2026_07_27.md` (0 open, 5 done, unlocked) | Deferred — 4 cross-refs in other tranches (INDEX.md, defi parked, batch1 false-completion claim, honest-coverage). Needs an `all`-tranche run or manual verification that referrers won't break. | Cross-tranche verification  |
| Archive: `autonomous_session_operator_decisions_2026_07_25.md` (0 open, 2 done, unlocked)    | Deferred — 42 cross-references. Too risky in a sharded run.                                                                                                                                      | Cross-tranche verification  |
| Archive: `tradfi_backfill_oom_remediation_2026_06_24.md` (0 open, 12 done)                   | BLOCKED — `locked_by: live-defi-rollout`. Operator must unlock before archival.                                                                                                                  | Operator `[unlock-plan]`    |
| Archive: `tradfi_canonical_path_migration_design_2026_07_19.md` (0 open, 1 done)             | BLOCKED — `locked_by: live-defi-rollout`. Operator must unlock before archival.                                                                                                                  | Operator `[unlock-plan]`    |

**Recommended next item**: Re-run `all`-tranche reconciliation on Saturday (per the weekly cadence) to handle the 2
deferred cross-tranche archives and catch any cross-tranche contradictions a single shard structurally cannot see.

## Lessons

- **Sharded run limitation**: With 27/61 docs in the grace window (<12h old), the non-grace corpus was only 34 docs —
  small enough that a direct scan was more efficient than the full 10-agent fan-out. The two background hunters
  dispatched may still return findings for the next session to fold in.
- **Archive candidates in sharded runs**: The cross-tranche archival caution check (grep other tranches' closeout docs)
  correctly blocked 2 archives that an unscoped run could have handled. The Saturday `all` run is the right place to
  clear these.
- **`locked_by: live-defi-rollout`** blocked 2 more archives. This is the most common lock value in the tradfi tranche —
  the `tradfi_master` epic and several children carry it. Archive-clearing these needs explicit operator action.
