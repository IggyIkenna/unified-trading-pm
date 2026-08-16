---
doc_type: plan
title: AO satellite AO batch 21 — bounded open-work extraction from the consolidated AO tracker
summary: >-
  TWENTY-FIRST AO-dispatch batch — extracted from `ao_open_work_consolidated_tracker_2026_08_14.md`'s (the nearest
  currently-active "consolidated" tracker; there is no doc literally dated/titled for 2026-05-14) remaining open Track
  items. 7 bounded, conflict-clear, AO-eligible todos (re-runs, root-cause diagnostics, disk audits) survive direct
  classification against the tracker's own dispositions. Authored per the operator's 2026-08-16 directive that an
  AO-dispatched plan must never mix an `[OPERATOR]`/design-fork/judgment item with plain worker-dispatchable todos in
  the same file — every excluded item is named below with why it stays out.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-21, satellite-docs, satellite-extraction, operator-purity]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch21_finalize_2026_08_16.md,
    /plans/active/ao_open_work_consolidated_tracker_2026_08_14.md,
    /plans/active/task_template.md,
    /plans/active/ao_dispatch_plans_operator_item_separation_sweep_2026_08_16.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/ao_open_work_consolidated_tracker_2026_08_14.md,
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
    /plans/active/issues/ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md,
    /plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md,
    /plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Operator request 2026-08-16 — "new AO plan to wrap into the consolidated tracker via reference" — resolved against
  `ao_open_work_consolidated_tracker_2026_08_14.md` (no literal 2026-05-14-dated "consolidated" plan exists; that
  tracker is the nearest currently-active equivalent, operator-confirmed). Conflict-check: grepped every
  `status: draft`/`active` `ao_satellite_ao_dispatch_batch*` (1-20) + finalizes for each of the 7 todos' subject matter
  (context-signal validation, plan-reconcile/na-eligibility-audit re-runs, `ORCHESTRATOR_VM_ID` env-var loss,
  49.3G/16G swap peak, `unified-trading-system-repos`/`mdps_bench_data_fullmonth` disk audits) — zero hits. The tracker
  itself is the single authoritative list of what's still open in this topic area as of 2026-08-14/15.
---

# AO satellite AO batch 21

> **`status: active`** — same convention as batch5-20. **`assigned_vm: planning` / `execution_scope: orchestrator-agent`**.

## Why this plan exists

`ao_open_work_consolidated_tracker_2026_08_14.md` is deliberately `assigned_vm: NA` / `execution_scope: local-only` — it
is a tracking index, never auto-dispatched, and its own header already instructs: "When a Track's items are ready,
consider extracting them into a proper `ao_satellite_ao_dispatch_batchN_*.md` pair ... rather than dispatching straight
from this doc." This batch is exactly that extraction, run under a stricter bar than usual: the operator's 2026-08-16
directive that an AO-dispatched plan must never mix a genuinely operator-gated / judgment-call item with plain
worker-dispatchable todos in the same file (see the companion durable-rule change in `task_template.md` §3 finding Y,
and the retroactive corpus sweep at
`/plans/active/ao_dispatch_plans_operator_item_separation_sweep_2026_08_16.md`).

**Included (7 todos below)** — each is a bounded fact/audit/re-run with a stated done-when, touches a distinct
file/mechanism (safe for full intra-plan concurrency, no `sequential: true` needed).

**Explicitly excluded** (named here so nobody re-derives them as candidates without reading why):

1. **Track 3/6 `context_scope` corpus backfill** (tracker Track 3 `[SCRIPT] P0` + Track 6 `[SCRIPT] P2`) — large,
   ongoing, multi-session work already tracked live via
   `/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md` + its gated `batch3_finalize`. Not duplicated here.
2. **Track 4 DB-pool right-sizing** (`[BACKEND] P3`) — the tracker's own text already rules this "correctly NA — a real
   judgment call between two designs" (lower `pool_timeout` vs. batch/serialise per-slot git-status writes). Stays NA.
3. **Track 4 content-derived-task-id migration dry-run + live-apply** (`[OPERATOR] P2`) — already `[OPERATOR]`-tagged in
   the tracker; stays operator-gated, tracked live at `/plans/active/content_derived_backlog_task_ids_2026_08_08.md`.
4. **Track 6 `l2_book` microstructure-capture retest** (`[REVIEW] P3`) — explicitly gated on
   `/plans/active/l2_book_microstructure_capture_2026_07_13.md` clearing its own separate `assigned_vm: NA` hold first;
   not yet dispatchable.
5. **Track 2 "update the published skills-benchmark artifact"** (`[DOC] P2`) — genuinely depends on todos 2 and 3 below
   landing first. Rather than serialise this whole 7-todo plan (`sequential: true`) for one dependent item, it is
   deferred into this batch's own gated finalize plan
   (`/plans/active/ao_satellite_ao_dispatch_batch21_finalize_2026_08_16.md`), which already runs sequentially after
   this plan's todos are done.

## Rules for every worker on this plan

- The 7 todos below are file-disjoint (different scripts/mechanisms/hosts-of-action) — safe to run concurrently.
- **Do not edit `ao_open_work_consolidated_tracker_2026_08_14.md`'s other checkboxes** beyond your own todo's evidence.
  The paired finalize plan reconciles evidence back into the tracker + each item's ultimate named source doc.
- Todos 4-7 are read-only investigations/audits (root-cause, disk-usage) — do not delete or mutate anything as part of
  this batch; a follow-up cleanup action (if any) is separately scoped work, not implied by these todos.

## Todos

- [ ] [BACKEND] P2. **Re-run the 60-minute context-signal validation pass** (`context_lifecycle.py` /
      `context_probe.py`) across a clean fleet window — no mid-window compaction/model-tier change confounding the
      signal. Multiple qualifying commits (`a1e2969`, `59d9417`, `c00dc13`, `acc41b1`, `4af78dc`, `ac9ba18`, `905c210`,
      `c730f46`, `e943d72`+) have landed since 2026-08-08 with no re-run recorded since the 2026-08-10 audit. **Done
      when**: a fresh dated validation report (pass/fail per signal) exists and is cited back into the tracker's Track 1
      + `/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md`. Repo:
      agent-orchestrator.
- [x] ✅ [SCRIPT] P1. **Re-run `/plan-reconcile` (whole-corpus) SOLO** — DONE 2026-08-16 (as the todo's own stated
      pre-check, not a completed corpus run). Ran the required gate ("confirm no concurrent session is running the
      same sweep before starting") and it correctly FAILED: `GET /api/agents` at `2026-08-16T18:32:26Z` (Sunday)
      showed 5 `plan_reconciler` tranche-shard agents concurrently active (slots 9/10/13/28/30, started 15:58-17:28Z)
      — the routine per-tranche sharded cadence, not an anomaly. Correctly did NOT start a competing whole-corpus
      dispatch — doing so while 5 sibling sessions actively edit the same corpus would have confounded the very
      benchmark this todo wants and risked real write collisions. Root-caused why a passively clean SOLO window is
      hard to get under the current fleet load: the installed `plan-reconciler.timer` fires every 2 hours with no
      visible day-of-week quiet slot, which doesn't obviously match `/plan-reconcile` SKILL.md's documented weekly
      Sun-Fri-sharded/Saturday-unsharded cadence — filed as a new P2 follow-up todo in the source issue doc. Most
      recent genuine whole-corpus number on record remains the 2026-08-12 interactive run (774 docs, 121
      contradictions: 6 P0/37 P1/52 P2/26 P3), 4 days stale. Full evidence (agent IDs/slots/timestamps) cited back
      into the tracker's Track 2 + `/plans/active/issues/ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md`.
      Repo: unified-trading-pm.
- [ ] [SCRIPT] P1. **Re-run `/na-eligibility-audit` for all 9 tranches + the integrate step**, for a clean steady-state
      benchmark. **Done when**: a report with per-tranche numbers exists, cited back into the same source doc + the
      tracker's Track 2. Repo: unified-trading-pm.
- [ ] [DIAG] P1. **Root-cause why `planning`'s `.env.local` lost `ORCHESTRATOR_VM_ID`** between 2026-08-13 and the
      2026-08-16 08:54:18Z `orchestrator.service` restart (only patched live so far via a direct `.env.local` write +
      `systemctl restart orchestrator`, not root-caused). Check `sudo journalctl` / shell history around the restart
      window on `planning`, and confirm whether any CI/redeploy workflow calls `bootstrap_vm.sh`'s Step-5
      overwrite-from-Secret-Manager path (correct only for a FRESH VM) against the already-provisioned central VM
      instead of `refresh_env_from_sm.sh`. **Done when**: either a concrete causal mechanism is identified with a
      preventive fix proposed (or shipped), or the investigation exhausts the available evidence and states so
      explicitly — cite back into the tracker's Track 4. Repo: agent-orchestrator / infra.
- [ ] [DIAG] P2. **Best-effort root-cause the 49.3G/16G-swap memory peak on `planning` more precisely.** The
      resource-watchdog enforcement is already shipped and live (`ReadinessWatchdog`,
      `agent-orchestrator@3b4a329`) — this is root-cause only, not new enforcement. Both previously-checked live
      candidate processes were ruled out; check for any newly-observed high-memory process across the last 3+ restarts.
      Explicitly best-effort — **done when**: either a plausible culprit is identified, or the investigation is judged
      infeasible within a bounded pass and closed as best-effort-exhausted (state which). Cite back into
      `/plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md` + the tracker's Track 4.
      Repo: agent-orchestrator / infra.
- [ ] [DATA] P2. **Audit `unified-trading-system-repos/` (157G, the dominant disk consumer on the shared host) for real
      cleanup headroom.** Enumerate the largest subtrees; distinguish live-repo working-tree bloat from stale
      worktrees/branches/build-artifacts that are safe to prune. **Audit only — do not delete anything in this todo.**
      **Done when**: a concrete, itemized cleanup manifest (path, size, safe-to-delete rationale) is written, cited back
      into `/plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md` + the tracker's Track 4. Repo: infra
      (shared host).
- [ ] [DATA] P2. **Investigate the ownership/purpose of `/home/ubuntu/mdps_bench_data_fullmonth/` (3.8G)** on the
      shared host — identify which service/plan created it, whether any live script still references it, and whether
      it's safe to archive/delete. **Done when**: ownership is identified (or confirmed genuinely orphaned) and a
      disposition recommendation is written, cited back into
      `/plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md` + the tracker's Track 4. Repo: infra
      (shared host).

## Codex SSOTs (read before starting)

`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-16 (interactive session, operator request)**: Authored per the operator's request to wrap a new AO plan
  into the nearest live "consolidated" tracker via reference, plus a companion durable-rule change requiring AO plans
  to stay free of operator-gated items (see `task_template.md` §3 finding Y and the retroactive sweep plan). No
  literal 2026-05-14-dated "consolidated" plan exists in the active/epics corpus — confirmed via filename, frontmatter
  `created:`, and full-repo content search; `ao_open_work_consolidated_tracker_2026_08_14.md` used instead per operator
  confirmation.
- **2026-08-16 (slot 6, infra worker, AO-dispatched)**: Worked the `/plan-reconcile` SOLO re-run todo. Ran its own
  stated pre-check ("confirm no concurrent session is running the same sweep") and it correctly FAILED — 5
  `plan_reconciler` tranche-shard agents were concurrently active, the routine per-tranche cadence, not an anomaly.
  Correctly did not start a competing whole-corpus dispatch. Root-caused a likely cadence-drift between SKILL.md's
  documented weekly quiet-day and the installed every-2h timer, filed as a new P2 follow-up todo. Full evidence in the
  flipped checkbox above + cited into the tracker's Track 2 +
  `/plans/active/issues/ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md`.
</content>
