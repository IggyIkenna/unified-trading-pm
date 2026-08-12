---
doc_type: issue
title: "plan_reconciler findings — ui tranche, 2026-08-07 (dispatch agt-a40e5f)"
summary: >-
  Sharded plan_reconciler run over the `ui` asset_group tranche (15 docs: 11 plans + 4 issues). 11 of 15 docs are in the
  12h grace window (read-only). Of the 4 non-grace docs, 2 are locked (`locked_by: live-defi-rollout`), blocking
  auto-fix. ZERO fixes applied this run — all findings filed for operator review. 4 verified missed-flip candidates
  (HARD evidence) blocked by lock, 1 archive candidate blocked by lock, 1 stale draft, 1 stale close-out prose, 1
  missing normative ref.
status: open
nature: process
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, findings, ui, 2026-08-07]
related:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md,
    /plans/active/ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md,
    /plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md,
    /plans/archive/2026_08/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md,
    /plans/active/deployment_registry_firestore_p5_verify_2026_07_14.md,
    /plans/active/deployment_registry_firestore_migration_2026_07_14.md,
  ]
created: "2026-08-07"
last_updated: "2026-08-07"
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: ui_developer
drift_direction: none
locked_by:
locked_since:
resolved_by:
source: "plan_reconciler dispatch agt-a40e5f — sharded ui tranche run 2026-08-07"
depends_on: []
---

# plan_reconciler findings — ui tranche, 2026-08-07

> **Run**: dispatch `agt-a40e5f`, sharded to `tranche=ui`. 15 docs in scope (11 plans + 4 issues). **Outcome**: zero
> fixes applied (11/15 grace-protected, 2/4 non-grace locked). All findings filed below.

## Coverage

- **Docs in tranche**: 15 (11 plans + 4 issues)
- **Grace-protected (read-only)**: 11 (all <12h old)
- **Non-grace (writable)**: 4 — of these, 2 locked (`locked_by: live-defi-rollout`), 1 stale draft, 1 overview with
  active children
- **Checked**: all 15 docs read, checkbox counts measured, grace/lock status determined
- **Skipped (grace)**: 11 docs — freshly touched (2026-08-06/07), active work in flight

## Flips verified (HARD evidence — blocked by lock)

All 4 are in `data_status_tab_and_downloads_remediation_2026_06_16.md` (75h old, non-grace, but **locked**:
`locked_by: live-defi-rollout` since 2026-06-16). **CORRECTED 2026-08-12 (/plan-reconcile)**: only items 1-3's own text
cites CODE-SHIPPED `deployment-ui@80c547d` — item 4 does not (see its entry below), so treat items 1-3 as the verified
missed-flip candidates and item 4 as a separate, genuinely-unshipped todo. SHA verified reachable on
`origin/live-defi-rollout` this run:

- `git merge-base --is-ancestor 80c547d origin/live-defi-rollout` → ✅ confirmed
- Commit: `80c547d fix(data-status): venue re-fetch + de-dupe data-type panels + pagination size selector; pin Node>=22`

1. **`- [ ] [UI] P1. Venue filter — frontend`** (line: "CODE-SHIPPED deployment-ui@`80c547d` (re-fetch `useEffect` on
   venue change)") — SHA verified, not flipped.
2. **`- [ ] [UI] P2. Collapse duplicate "available" vs "available dates"`** (line: "CODE-SHIPPED deployment-ui@`80c547d`
   (legacy date-range panel removed)") — SHA verified, not flipped.
3. **`- [ ] [UI] P2. Pagination visible-count selector`** (line: "CODE-SHIPPED deployment-ui@`80c547d` (`DateList` size
   selector)") — SHA verified, not flipped.
4. **`- [ ] [UI] P3. Rollup-difference clarity`** — ~~(line: "CODE-SHIPPED deployment-ui@`80c547d`") — SHA verified, not
   flipped.~~ **CORRECTED 2026-08-12 (/plan-reconcile)**: false attribution. Checked
   `data_status_tab_and_downloads_remediation_2026_06_16.md`'s actual "Rollup-difference clarity" todo (and its full git
   history via `git log -p --follow`) — it has never carried a `CODE-SHIPPED deployment-ui@80c547d` citation; it reads
   "(audit §F, by-design): optional small UI note/tooltip … — deployment-ui" with no commit citation at all, i.e. it is
   a distinct, genuinely-unshipped todo. The `80c547d` SHA belongs only to items 1-3 above (venue filter,
   duplicate-panel collapse, pagination selector). This item should never have been listed alongside the 3 genuine
   missed-flip candidates.

**Action blocked**: `locked_by: live-defi-rollout` on the parent doc prevents autonomous flip. Operator should either
confirm the lock is genuine (and flip these manually) or unlock the doc so the next reconciler run can auto-flip.

## Archive candidates (operator review)

### `issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` — RESOLVED 2026-08-10

- **Status (at filing)**: `status: open`, 0 open todos, 3 done (`[x]`)
- **Lock (at filing)**: `locked_by: live-defi-rollout`, `locked_since: 2026-05-21`
- **Finding**: The lock timestamp (`2026-05-21`) **predates the doc's own `created: 2026-07-21` by 2 months** —
  impossible for a genuine exclusive claim. Strongly suggests a stale placeholder value.
- **Previously flagged**: `ui_satellite_ao_dispatch_batch1_2026_08_06.md` § "Findings" (2026-08-06) flagged this same
  doc with the same observation.
- **Action**: Operator should verify the lock is stale, `[unlock-plan]`, then archive via the 6-step ritual. All 3 todos
  are verified done (fresh re-verification through 2026-08-06 context-scout entry, no reopening).
- **RESOLVED 2026-08-10**: operator asked directly and approved a targeted `[unlock-plan]` for this doc. Unlocked +
  archived to `/plans/archive/2026_08/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` per the
  6-step ritual; see `/plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md` todo 3 for
  the fuller evidence trail.
- **Broader pattern**: `locked_by: live-defi-rollout` appears on **62 docs corpus-wide** (per batch1's own grep) —
  whether this is a genuine mechanism or stale template default affecting archival eligibility across the corpus is
  unclear from a ui-scoped run. Worth a dedicated corpus-wide check.

## Stale draft

### `deployment_registry_firestore_p5_verify_2026_07_14.md`

- **Status**: `status: draft` for ~184h (7.7 days), `assigned_vm: NA`
- **Open**: 3 todos (post-phase codex audit, CLAUDE.md update, ship-and-mark-master)
- **Context**: Correctly sequenced behind `deployment_registry_firestore_p3_cutover_2026_07_14.md`'s GO/NO-GO checklist
  (item 7 in batch1's Deferred: "explicitly sequenced behind item 6 above landing in prod"). The draft status is
  intentional gating, not neglect — but at 184h it's worth re-checking whether the P3 gate has moved.
- **Action**: No immediate fix — re-check when P3 cutover converges. Flagged for visibility.

## Stale close-out prose (already flagged, re-confirmed)

### `ui_consolidated_closeout_2026_07_30.md` Track 3 and Track 4

- Track 3 still reads "alerts N+1 read pattern fixed at root, not just the two stopgaps" as if open — both already
  resolved and archived (`issues/alerts_endpoint_per_object_gcs_read_performance_2026_07_23.md`).
- Track 4 still reads "mock/live contract parity restored on all 12 drifted endpoints" as if open — already resolved and
  archived (`issues/deployment_api_live_mock_parity_2026_07_17.md`).
- Previously flagged by `ui_satellite_ao_dispatch_batch1_2026_08_06.md` § "Findings" and by
  `ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md` todo 4 (which explicitly plans to trim these).
- **Action**: Will be fixed when batch1_finalize todo 4 runs (gated on batch1 completion). No independent fix needed.

## Missing normative ref

### `plans/active/ACTIVE_INDEX.md`

- Referenced in plan_reconciler SKILL.md as a normative ref ("ACTIVE_INDEX.md — stay in scope for EVERY shard")
- File does not exist (`ls: cannot access 'plans/active/ACTIVE_INDEX.md': No such file or directory`)
- `plans/active/INDEX.md` DOES exist (7h old, grace-protected)
- **Action**: Determine whether ACTIVE_INDEX.md should exist (and regenerate if so) or whether the SKILL.md reference is
  stale and should be removed. Low priority — the file has been absent for some time with no apparent breakage.
- **Re-flagged, still unfixed, 2026-08-10** (plan_reconciler dispatch `agt-ec1688`, ui tranche re-run): re-confirmed the
  file still doesn't exist and `cursor-configs/skills/plan-reconcile/SKILL.md` (lines 5, 59, 425) and
  `agents/plan_reconciler.md` (line 114) still cite it. This item has now sat as prose-only for 3 days across 2 runs
  without becoming a tracked todo — converting it below per this workspace's "every follow-up is a `- [ ]` todo, never
  prose" rule. Both citing files are outside `plans/**` (plan_reconciler's own write-scope), so no worker running this
  skill can fix them directly — an operator or a human session must.

- [ ] [DOC] P3. Resolve the `ACTIVE_INDEX.md` dangling normative-ref: either regenerate the file (if a real artifact was
      intended, distinct from the existing `INDEX.md`) or edit `cursor-configs/skills/plan-reconcile/SKILL.md` (lines 5,
      59, 425) + `agents/plan_reconciler.md` (line 114) to drop the stale name and cite only `INDEX.md`. Requires a
      human/operator session (both target files are outside every plan_reconciler dispatch's `plans/**` write-scope).
      Done when: `grep -rn ACTIVE_INDEX cursor-configs/skills/plan-reconcile/SKILL.md     agents/plan_reconciler.md`
      returns 0 hits, or the file exists and is wired into the regen tooling.

## Hygiene sweep (corpus-wide, not tranche-specific)

The STEP 1 hygiene sweep (`run_hygiene_sweep.sh --ci --no-regen`) reported 4 hard failures:

1. Reference path convention (ratchet)
2. AG-closeout linkage (ratchet)
3. Terminal-status-archived (ratchet)
4. Archive candidates (ratchet)

All 4 are ratchet-gated — the corpus-wide baseline has slack, and current counts exceed it. Not fixable within a
single-tranche run. These are pre-existing corpus conditions, not regressions introduced by ui-tranche work.

## Docs not reached

None — all 15 ui-tranche docs were identified and their grace/lock/open-todo status measured this run. The 11 grace docs
were not read end-to-end (active work in flight, <12h old — reading them for context is safe but modifying them is not).

## Progress Log

- **2026-08-07** — plan_reconciler dispatch agt-a40e5f, sharded to `tranche=ui`. 15 docs in scope, 11 grace-protected, 2
  locked, 1 stale draft, 1 overview-with-active-children. 4 verified missed-flip candidates (HARD evidence, blocked by
  lock), 1 archive candidate (blocked by suspicious lock), 1 stale close-out prose (already tracked by batch1_finalize),
  1 missing normative ref (ACTIVE_INDEX.md). Zero fixes applied. All findings filed here.
