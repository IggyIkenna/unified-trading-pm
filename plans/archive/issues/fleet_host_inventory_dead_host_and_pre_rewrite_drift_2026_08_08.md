---
doc_type: issue
title:
  "Fleet host inventory: 1 dead AWS host (11-14d stale, needs decommission) + 1 pre-history-rewrite repo drift (5 repos,
  never FF-pullable)"
summary: >-
  Review fleet health sweep (2026-08-08 ~12:58Z, msg 4113), main independently confirmed via /api/state before filing.
  Two distinct operator-decision findings: (1) host ip-172-31-0-185 — all 3 slots reporter-stale since 2026-07-25/28
  (11-14 days), slot 0 dirty/detached repos since 2026-07-22/24, consistent with a terminated/offline AWS instance with
  no active workers — needs operator decommission-or-recover decision. (2) host ip-172-31-5-118 slot 0 — 5 repos
  (e2e-testing, instruments-service, unified-trading-library, execution-service, market-data-processing-service) show
  large ahead/behind drift-violations, all timestamped 2026-08-05T11:12Z, coinciding with the Aug-5 history-rewrite
  event (matches the `.stale-pre-history-rewrite-20260805T112618Z` backup markers seen elsewhere in the fleet) — this
  slot's clones predate the rewrite and were never updated, so they can never fast-forward-pull correctly until reset.
  No committed work sits on the wrong branch (nothing to rescue), so this is a clean reset, not a recovery.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, fleet-health, host-inventory, decommission, history-rewrite, drift-violation]
related:
  [
    /plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-08
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
assigned_role: devops
drift_direction: advance-process
resolved_by:
  "Finding 1: /plans/archive/issues/fleet_git_health_ip_185_known_human_planning_vm_2026_08_03.md (already resolved,
  discovered as a stale duplicate). Finding 2: extracted into
  /plans/active/ao_satellite_ao_dispatch_batch12_2026_08_09.md for AO dispatch."
locked_by:
source:
  "review (agent-orchestrator loop tick, msg 4113, ~2026-08-08T12:58:58Z); main independently corroborated slot 3 state
  via /api/state before filing"
depends_on: []
context_scope:
  [
    /plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
---

# Fleet host inventory gaps — dead host + pre-rewrite repo drift

## Finding 1 — dead host ip-172-31-0-185 (operator decommission decision)

All 3 slots on this host are reporter-stale since 2026-07-25/28 (11-14 days at filing time):

- Slot 0: dirty/detached repos since 2026-07-22/24.
- Slot 1 + Slot 2: last reported 2026-07-28.

No active workers report from this host. Pattern is consistent with a terminated or offline AWS instance rather than a
live host with a reporting bug (11-14 days of total silence across all 3 slots, not an intermittent gap).

## Finding 2 — pre-history-rewrite drift on ip-172-31-5-118 slot 0 (needs a clean reset)

5 repos on this slot show large ahead/behind drift-violations, all since `2026-08-05T11:12Z`:

| repo                           | behind | ahead |
| ------------------------------ | ------ | ----- |
| e2e-testing                    | 1094   | 1050  |
| instruments-service            | 3785   | 3699  |
| unified-trading-library        | 2516   | 2456  |
| execution-service              | 51     | 15    |
| market-data-processing-service | 30     | 104   |

This timestamp coincides with the Aug-5 history-rewrite event (see related doc
`provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`) and matches the
`.stale-pre-history-rewrite-20260805T112618Z` backup-repo markers observed elsewhere in the fleet — this slot's clones
predate the rewrite and were never updated onto the new history, so their ahead/behind counters are comparing against an
obsolete base and will never resolve via a normal FF-pull. No committed work sits on the wrong branch here (nothing
unique to lose), so the fix is a clean re-clone/reset of these 5 repos on this slot, not a rescue-and-merge.

## Todos

- [x] ✅ [OPERATOR] P2. **CLOSED as a stale duplicate 2026-08-09 (`/ag-closeout-audit ao`)** — host ip-172-31-0-185 /
      instance `i-0dd9812a96cdda5dc` was already independently AWS-verified TERMINATED 2026-08-03 (operator-approved
      retirement via `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`), 3+ prior re-flags already resolved, no
      snapshot/volume survives to attempt recovery. See
      `/plans/archive/issues/fleet_git_health_ip_185_known_human_planning_vm_2026_08_03.md` (`status: resolved`, final
      2026-08-05 Progress Log entry) for the full resolution trail. This finding (filed 2026-08-08, 5 days later)
      re-discovered the identical stale-host signature without cross-referencing that resolution — no new decision
      needed, decommission is already the executed outcome.
- [x] ✅ [DEVOPS] P2. **Clean-reset the 5 drift-violating repos on ip-172-31-5-118 slot 0** (`e2e-testing`,
      `instruments-service`, `unified-trading-library`, `execution-service`, `market-data-processing-service`) onto
      current post-history-rewrite `live-defi-rollout`. — **DONE 2026-08-10 via batch12 todo 8**: confirmed clean
      working trees on all 5 (no uncommitted work lost), tagged each old `HEAD` as `archive/pre-reset-20260810T015655Z`
      for reversibility, then
      `git fetch origin live-defi-rollout && git switch -C     live-defi-rollout origin/live-defi-rollout` per repo
      (branch-ref-only move; never `reset --hard`/`rm -rf`; the `alternates` object stores untouched). All 5 now
      ahead=0/behind=0 against `origin/live-defi-rollout`; `git fsck` clean. Re-verified in the batch12-finalize review
      (same host): all 5 on `live-defi-rollout` at ahead=0/behind=0 + archive tags present.

## Progress Log

- **context-scout 2026-08-09**: populated context_scope (3 entries).
- **2026-08-09 (`/ag-closeout-audit ao`, dispatch `agt-41d860`, slot 10)**: Finding 1 closed as a stale duplicate of an
  already-resolved doc (see todo 1 above) — editorial dedup, not new work. Finding 2 (todo 2) is a clean, conflict-free
  AO-dispatch candidate; extracted into `ao_satellite_ao_dispatch_batch12_2026_08_09.md` todo (pending operator approval
  to flip that batch `draft` → `active`).
