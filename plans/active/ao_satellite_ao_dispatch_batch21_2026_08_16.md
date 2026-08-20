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
    /plans/archive/2026_08/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md,
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
   `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch3_2026_07_31.md` + its gated `batch3_finalize`. Not duplicated here.
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

- [x] ✅ [BACKEND] P2. **Re-run the 60-minute context-signal validation pass** (`context_lifecycle.py` /
      `context_probe.py`) across a clean fleet window — no mid-window compaction/model-tier change confounding the
      signal. Multiple qualifying commits (`a1e2969`, `59d9417`, `c00dc13`, `acc41b1`, `4af78dc`, `ac9ba18`, `905c210`,
      `c730f46`, `e943d72`+) have landed since 2026-08-08 with no re-run recorded since the 2026-08-10 audit. **Done
      when**: a fresh dated validation report (pass/fail per signal) exists and is cited back into the tracker's Track 1
      + `/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md`. Repo:
      agent-orchestrator. — ✅ DONE 2026-08-17 (slot 12): confirmed fleet clean-start (all `working` slots ≤60% ctx),
      ran the full 60-min window via `GET /api/activity`. **Result: PASS on both criteria** — 21 forces, distribution
      `60×11 · 69×10` (well inside the 60-08-08 baseline's 60-85 range), **zero terminal wedges** over the full
      60 minutes (the 2026-08-08 run only partial-passed, 4 inherited wedges). Full write-up in the issue doc's new
      "2026-08-17 validation window" section + cited into the tracker's Track 1.
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
- [x] ✅ [SCRIPT] P1. **Re-run `/na-eligibility-audit` for all 9 tranches + the integrate step** — DONE 2026-08-16
      (slot 9). Ran Phase 0 (`generate_na_doc_tranche_inventory.py --tranche all --json`): 449 `assigned_vm: NA`
      docs / 1,516 open todos corpus-wide; 324 docs in-scope after incremental-skip (125 unchanged since a prior
      dated marker). Per-tranche split (docs total/in-scope, todos total/in-scope): ao 67/56 244/206; cefi 52/12
      181/33; ci 44/42 107/78; cross-cutting 115/101 492/392; defi 60/19 267/112; infra 58/53 200/165; prediction
      26/18 89/50; sports 52/42 168/118; tradfi 42/10 97/34; ui 15/14 35/34. This is the requested Phase-0
      steady-state benchmark; the full Phase-1 per-doc reclassification pass over the 324 in-scope docs was NOT
      run this session (multi-hour/multi-session scale) and remains open for the scheduled
      `na-eligibility-auditor.timer` or a dedicated future dispatch. Cited into
      `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s Progress Log + the tracker's Track 2. Repo:
      unified-trading-pm.
- [x] ✅ [DIAG] P1. **Root-cause why `planning`'s `.env.local` lost `ORCHESTRATOR_VM_ID`** between 2026-08-13 and the
      2026-08-16 08:54:18Z `orchestrator.service` restart (only patched live so far via a direct `.env.local` write +
      `systemctl restart orchestrator`, not root-caused). Check `sudo journalctl` / shell history around the restart
      window on `planning`, and confirm whether any CI/redeploy workflow calls `bootstrap_vm.sh`'s Step-5
      overwrite-from-Secret-Manager path (correct only for a FRESH VM) against the already-provisioned central VM
      instead of `refresh_env_from_sm.sh`. **Done when**: either a concrete causal mechanism is identified with a
      preventive fix proposed (or shipped), or the investigation exhausts the available evidence and states so
      explicitly — cite back into the tracker's Track 4. Repo: agent-orchestrator / infra. — ✅ DONE 2026-08-17:
      mechanism identified (forensic `.env.local.bak.*` evidence pinned it to `bootstrap_vm.sh` STEP 5b's raw
      overwrite running without reaching the identity-var re-add) and a preventive fix shipped
      (`agent-orchestrator@bc9835a38d`). Exact trigger process not identified (no root crontab/journalctl access from
      this sandboxed worker), stated explicitly — see full write-up in the tracker's Track 4.
- [x] ✅ [DIAG] P2. **Best-effort root-cause the 49.3G/16G-swap memory peak on `planning` more precisely.** The
      resource-watchdog enforcement is already shipped and live (`ReadinessWatchdog`,
      `agent-orchestrator@3b4a329`) — this is root-cause only, not new enforcement. Both previously-checked live
      candidate processes were ruled out; check for any newly-observed high-memory process across the last 3+ restarts.
      Explicitly best-effort — **done when**: either a plausible culprit is identified, or the investigation is judged
      infeasible within a bounded pass and closed as best-effort-exhausted (state which). Cite back into
      `/plans/archive/2026_08/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md` + the tracker's Track 4.
      Repo: agent-orchestrator / infra. — ✅ DONE 2026-08-17 (slot 10): the original 2026-08-02 peak itself is
      best-effort-exhausted (predates resource-watchdog, no forensic trail survives). Redirected to the fallback
      ("newly-observed high-memory process") via resource-watchdog's own kill corpus: 187 kills/7d, 25 >10GB RSS (peak
      20.2GB), concentrated on slots 6/2/25/27/14, all tracing to 4 unbounded CEFI-manifest scripts in
      `market-tick-data-service/scripts/` (`normalize_instrument_type_casing.py`,
      `audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`,
      `revert_cefi_live_corrective_migration_overreach_2026_08_16.py`, `measure_shard_duration_p95.py`). Landed a new
      `[INFRA] P2` follow-up todo in the issue doc naming these scripts for a bounded-read/streaming fix. Full write-up
      in the issue doc's new Progress Log entry + flipped `[DIAG] P2` todo.
- [x] ✅ [DATA] P2. **Audit `unified-trading-system-repos/` (157G, the dominant disk consumer on the shared host) for real
      cleanup headroom.** Enumerate the largest subtrees; distinguish live-repo working-tree bloat from stale
      worktrees/branches/build-artifacts that are safe to prune. **Audit only — do not delete anything in this todo.**
      **Done when**: a concrete, itemized cleanup manifest (path, size, safe-to-delete rationale) is written, cited back
      into `/plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md` + the tracker's Track 4. Repo: infra
      (shared host). — ✅ DONE 2026-08-17 (slot 6): itemized manifest written. Headline: ~57.2G of confirmed-dead
      one-off-script `.tmp/` scratch across 5 repo worktrees (slots 14/16/18×2/19) — same anti-pattern class as the
      already-fixed `manifest-consolidate-*` leak. Full table + rationale in the issue doc's new Progress Log entry.
- [x] ✅ [DATA] P2. **Investigate the ownership/purpose of `/home/ubuntu/mdps_bench_data_fullmonth/` (3.8G)** on the
      shared host — identify which service/plan created it, whether any live script still references it, and whether
      it's safe to archive/delete. **Done when**: ownership is identified (or confirmed genuinely orphaned) and a
      disposition recommendation is written, cited back into
      `/plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md` + the tracker's Track 4. Repo: infra
      (shared host). — ✅ DONE 2026-08-17 (slot 18): owned by
      `plans/audit/results/benchmarks/mdps_engine_comparison_2026_05_28/run_full_month.py`'s `DEFAULT_DATA_ROOT` — raw
      input for the full-month MDPS engine benchmark, whose results are already durably persisted
      (`results_full_month_binance_2026_04.md`/`.json`, `status: pass`, 2026-06-29). No other consumer found
      fleet-wide. Disposition: safe to archive/delete (re-derivable scratch, not output). Full detail in the issue
      doc's new Progress Log entry.

## Codex SSOTs (read before starting)

`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-17 (slot 18, data_engineering worker, AO-dispatched)**: Worked the `mdps_bench_data_fullmonth/` ownership
  todo (the plan's last remaining open item). Traced ownership to
  `plans/audit/results/benchmarks/mdps_engine_comparison_2026_05_28/run_full_month.py`; its benchmark is closed with
  results already persisted (`status: pass`, 2026-06-29) — disposition: safe to archive/delete. Full detail in
  `/plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md`'s new Progress Log entry; checkbox above
  flipped. This plan's 7 todos are now all complete.
- **2026-08-17 (slot 10, infra worker, AO-dispatched)**: Worked the 49.3G/16G-swap best-effort root-cause todo.
  Original 2026-08-02 peak predates resource-watchdog (shipped 2026-08-05) — no forensic trail survives, closed
  best-effort-exhausted. Redirected to the fallback: queried resource-watchdog's own kill corpus and found 187
  kills/7d, 25 >10GB RSS, all tracing to 4 unbounded CEFI-manifest scripts in `market-tick-data-service/scripts/`.
  Landed a new `[INFRA] P2` follow-up todo in
  `/plans/archive/2026_08/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md` naming the scripts. Full
  detail in that doc's Progress Log.
- **2026-08-17 (slot 12, AO-dispatched)**: Worked the 60-minute context-signal validation re-run todo. Verified the
  fleet was clean-start (all `working` slots ≤60% context) before beginning — the exact precondition the 2026-08-08
  session's own follow-up demanded. Ran a background monitor (6× 10-min checkpoints) over the live `/api/activity`
  feed for `forced_compact`/`forced_precompact`/wedge-terminal event types across the full window. Result: 21 forces,
  distribution `60×11 · 69×10` (tighter than the 2026-08-08 baseline's 60-85 range), zero terminal wedges — a clean
  PASS where the 2026-08-08 run only partial-passed (4 wedges, all inherited saturation from a dirty start). Full
  write-up appended to `slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md`'s own "2026-08-17
  validation window" section (its matching follow-up todo flipped) + a citation note appended to the tracker's
  Track 1 (checkbox itself left unflipped per this plan's own rule — `batch21_finalize` reconciles it).
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
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
- **2026-08-17 (slot 6, infra worker, AO-dispatched)**: Worked the `ORCHESTRATOR_VM_ID` root-cause todo. Found forensic
  evidence in `planning`'s own `agent-orchestrator/.env.local.bak.*` files: of 6 backups, exactly one
  (`.env.local.bak.1786877088`) carries zero `ORCHESTRATOR_*` keys — the signature of `bootstrap_vm.sh` STEP 5b's raw
  `.env.local` overwrite-from-Secret-Manager running without reaching the identity-var re-add (`_upsert_env
  ORCHESTRATOR_VM_ID`) a few lines later in the same block. Shipped a preventive fix
  (`agent-orchestrator@bc9835a38d`): STEP 5b now detects an already-provisioned host (existing `.env.local` already
  declaring `ORCHESTRATOR_VM_ID`) and upserts the Secret-Manager blob's keys in place instead of overwriting the whole
  file — mirroring `refresh_env_from_sm.sh`'s technique — so no VM-specific key can be dropped by this step again
  regardless of what triggers a partial/isolated run. The exact triggering process/redeploy path was NOT identified
  (no root crontab or full-system journalctl access from this sandboxed worker) — stated explicitly per the todo's own
  done-when. Full write-up cited into the tracker's Track 4.
- **2026-08-17 (slot 6, infra→data_engineering worker, AO-dispatched)**: Worked the `unified-trading-system-repos/`
  disk-cleanup-headroom audit todo (read-only, no deletes). Fleet-wide `find -maxdepth 3 -name .tmp` swept all 33
  `.tabs/` slots and found 5 large, confirmed-dead one-off-script scratch dirs totaling ~57.2G (slot16/
  instruments-service 17G, slot14/market-tick-data-service 14G, slot18/market-tick-data-service 11G, slot18 top-level
  8.5G, slot19/market-tick-data-service 6.7G) — each verified via contents/mtime/lsof/ps as multi-day-stale with zero
  live process, all tracing to one-off diagnostic/migration scripts (e.g.
  `purge_defi_eigenlayer_stale_spot_pair_expected_cells_2026_08_15.py`) that never clean up their own `tempfile`
  scratch. A full byte-exact `du` of all 33 slots was attempted twice and killed both times by background-task
  lifetime limits (matches the tracker's own 2026-08-15 note about the same SSM-timeout pattern); used a 15-slot
  sample (135.2G) + a complete root-level canonical-clone pass (45.2G/26 repos) instead — sufficient for the itemized
  manifest the todo asked for. Full table + recommendation in
  `/plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md`'s new Progress Log entry; citation note
  appended to the tracker's Track 4 (checkbox left unflipped per this plan's own rule — `batch21_finalize` reconciles
  it).
- **context-scout 2026-08-19**: re-scouted; context_scope unchanged (6 entries), still accurate — all 7 todos done,
  only the finalize reconciliation remains.
</content>
