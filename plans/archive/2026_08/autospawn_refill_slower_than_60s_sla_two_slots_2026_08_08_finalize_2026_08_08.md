---
doc_type: plan
title: AutoSpawn refill SLA gap — finalize
summary: >-
  Gated closeout for `autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until its sole todo (root-cause the AutoSpawn refill SLA gap) is done. Reconciles the
  investigation's evidence quality before archiving.
status: complete
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, autospawn, close-out, archival, plan-hygiene]
related:
  [
    /plans/archive/2026_08/issues/autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md,
    /plans/epics/orchestrator_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/autospawn_refill_sla_data_points_1_2_and_live_recheck_followup_2026_08_09.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_08/issues/autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08]
gate_on_depends: true
source: >-
  /na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08 — required companion per `plans/active/task_template.md`
  §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
---

# AutoSpawn refill SLA gap — finalize

> **🟢 ARCHIVED (2026-08-09).** Both todos done: the root-cause fix independently re-verified, and
> `autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md` archived to `/plans/archive/2026_08/issues/` per the
> 6-step ritual (the two remaining prose caveats were migrated to a tracked follow-up:
> `/plans/active/issues/autospawn_refill_sla_data_points_1_2_and_live_recheck_followup_2026_08_09.md`). This finalize
> doc itself moves alongside it in this immediately-following commit (per the never-combine-checkbox-flip-with-git-mv
> rule) to `/plans/archive/2026_08/autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08_finalize_2026_08_08.md`. No
> new durable contract — codex-alignment check: nothing to update, the fix already lives in code
> (`agent-orchestrator@dfef970`).

## Todos

- [x] ✅ [REVIEW] P3. **Verify the root-cause claim is evidence-backed, not asserted.** Confirm the parent doc's
      done-when was actually met: either a named root cause with live evidence (AutoSpawn scheduling/concurrency code
      citation + a reproduced timing gap), or a documented decision with a 10+-sample dataset showing the original 2
      data points were not representative. **Done when**: the evidence trail is independently checked, not just the
      parent doc's own claim taken at face value. Repo: unified-trading-pm. — **unified-trading-pm@(this commit)**.
      Independently verified against live `agent-orchestrator` code, not the parent doc's self-report:
      `git show --stat dfef970` confirms the commit is real, its `Quickmerge: agent` trailer + presence on
      `origin/live-defi-rollout` (`git merge-base --is-ancestor dfef970 origin/live-defi-rollout` → true) confirm it
      shipped through the gated quickmerge flow. Read the full diff directly: both `AutoSpawnLoop._run_one_tick()`'s
      queue-driven spawn section and `_resume_pass()`'s dead-worker resume section previously called `_do_spawn(...)`
      inline inside a plain sequential `for` loop (confirmed removed — no leftover unparallelized call site); both now
      route through the new `_do_spawns_concurrently()` (bounded `ThreadPoolExecutor` + `as_completed`, DB bookkeeping
      kept serial one-result-at-a-time). `python3 -m py_compile server/autospawn.py` — syntax OK. The claimed
      live-evidence timing gap (5-slot simultaneous context-wedge batch, 21s window, only 1/5 refilled within SLA) is
      corroborated by a SECOND, independent agent (main, via `journalctl` on the host) per the issue doc's own account —
      not merely self-asserted by the same worker who wrote the fix. **Caveat carried forward honestly** (already
      flagged in the parent doc, re-confirmed here, not silently dropped): no new/changed test directly asserts
      wall-clock concurrency, and the fix was not independently proven to explain data points 1/2 (lone-slot gaps) —
      only data point 3 (the 5-slot batch). Verdict: root-cause claim for data point 3 is evidence-backed, not asserted;
      the parent doc's own honest caveat about points 1/2 stands. No code change required for this verification-only
      todo.
- [x] ✅ [DOCS] P3. **Archive the parent doc per the 6-step ritual, and only then.** Confirm zero open `- [ ]` todos
      remain; add the archival banner + set `status: complete`; grep the corpus for
      `autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08` and repoint every referrer; clear any lock if set.
      Then physically move the parent doc under `plans/archive/2026_08/`. **Done when**:
      `bash     scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is 0 hard, `check_reference_paths.py` shows
      no NEW dangling reference above its baseline, and `regenerate_active_plan_inventory.py` reports 0 orphans for this
      doc. Repo: unified-trading-pm. — **unified-trading-pm@c5aa14cb9**. Confirmed zero open todos on the parent doc
      (its sole `[BACKEND]` todo already `[x]`, independently re-verified by this plan's own todo 1). Step 1 of the
      ritual (migrate deferred items, never prose) was NOT already satisfied — the parent doc carried two live caveats
      (data points 1/2 not independently explained; production live-recheck not performed) stated only in Progress Log
      prose, so filed a real tracked follow-up first:
      `/plans/active/issues/autospawn_refill_sla_data_points_1_2_and_live_recheck_followup_2026_08_09.md`
      (`unified-trading-pm@19c19c6db`). Then added the `🟢 ARCHIVED` banner + `status: resolved` + `resolved_by` to the
      parent doc and `git mv`'d it to `plans/archive/2026_08/issues/` (rename verified via `git log --stat` — both the
      delete and the add landed in one commit, not the create-only hazard). Referrer sweep: corpus-wide grep for the old
      path found only `plans/active/INDEX.md` (auto-generated, regenerated below) and this finalize plan's own
      `related:` (repointed to the archive path in this same commit); the one archived-doc referrer
      (`plans/archive/2026_07/active_plan_inventory_dashboard_2026_07_24.md`) is a frozen historical snapshot, left
      as-is by convention. No codex-alignment update needed — the durable contract (the `_do_spawns_concurrently()` fix)
      already lives in code, not in this issue doc.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside the parent doc's `na-eligibility-audit round7 RECLASSIFY` flip from
  `assigned_vm: NA` to `planning`. `status: active` immediately (not `draft`) — machine-held from actually dispatching
  via `depends_on` + `gate_on_depends: true` until the parent doc's sole todo is done.
- **2026-08-08 (slot 19)**: Todo 1 (evidence-backed verification) done. Independently checked the parent doc's
  root-cause claim against live `agent-orchestrator` code and origin history rather than accepting the self-report:
  confirmed commit `dfef970` is real, `Quickmerge: agent`-shipped, and present on `origin/live-defi-rollout`; read the
  full diff and confirmed both spawn call sites moved from an inline sequential `for`-loop `_do_spawn()` call to the new
  `_do_spawns_concurrently()` (bounded `ThreadPoolExecutor`), with no leftover unparallelized path; `py_compile`
  syntax-clean. The live-evidence timing gap (5-slot batch, only 1/5 within SLA) was corroborated by a second
  independent agent (main, via `journalctl`), not just self-asserted. Verdict: evidence-backed for data point 3; the
  parent doc's own caveat about points 1/2 (not independently explained) stands and is carried forward, not dropped.
  Todo 2 (archival) remains — the parent doc's todo is done so this finalize plan is now unblocked for it.
- **2026-08-09 (slot 25, infra)**: Todo 2 (archival) done. Filed a tracked follow-up issue doc for the two prose caveats
  first (`unified-trading-pm@19c19c6db`), then archived the parent doc per the 6-step ritual
  (`unified-trading-pm@c5aa14cb9`). Both of this finalize plan's own todos are now done and it carries no lock —
  archiving it too in the immediately following commit (`archive_exempt: true` set on THIS commit as the sanctioned
  flip-only bridge, per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s `archive_exempt` ruling
  — dropped again once the `git mv` lands).
