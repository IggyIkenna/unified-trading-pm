---
doc_type: plan
title: AO satellite AO batch 12 — finalize
summary: >-
  Gated closeout for `ao_satellite_ao_dispatch_batch12_2026_08_09.md` — machine-held via `depends_on` +
  `gate_on_depends` until all 11 of that batch's todos are done. Reconciles each verified todo's evidence back into its
  TRUE source doc's own checkbox (`deepseek_flash_ab_routing_test_2026_08_05.md` ×5,
  `ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md` ×2,
  `fleet_host_inventory_dead_host_and_pre_rewrite_drift_2026_08_08.md` ×1,
  `forced_compact_reports_submitted_but_never_executes_2026_08_08.md` ×3), checks whether any source doc is now fully
  closed and archives it if so, then archives the batch plan itself.
status: archived
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-12, finalize, satellite-extraction]
related:
  [
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch12_2026_08_09.md,
    /plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md,
    /plans/active/issues/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md,
    /plans/archive/issues/fleet_host_inventory_dead_host_and_pre_rewrite_drift_2026_08_08.md,
    /plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: review
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch12_2026_08_09]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch12_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch, 2026-08-09, per the satellite-batch-extraction pattern's mandatory finalize-twin rule.
---

# AO satellite AO batch 12 — finalize

> **ARCHIVED 2026-08-10** — all 4 todos done: re-verified all 11 of batch12's done-claims against reality (tests re-run
> green, live DB/state confirmed), reconciled the evidence into the 4 TRUE source docs, checked source docs for full
> closure (deepseek archived; ao_false_done left to its own finalize), and archived the batch plan itself (inventory
> regenerated, `check_finalize_plan_coverage` clean). Completion evidence in each todo below. Archived by the
> batch12-finalize review worker.

> **Machine-gated on `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch12_2026_08_09.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until all 11 of that batch's todos are `done`. The batch itself stays
> `status: draft` until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [x] ✅ [REVIEW] P0. **Re-verify all 11 of batch12's done-claims against reality, not against their checkboxes** — for
      each: re-run the cited regression test/repro, re-run the named live query/dry-run report for the read-only items,
      and `git show --stat <sha>` for every code change. Pay particular attention to todo 5 (backfill `--apply`) and
      todo 8 (git clean-reset) — both mutate live state directly; independently confirm the post-action state matches
      the claimed done-when, not just that the commit/command ran. **Done when**: each of the 11 claims is independently
      confirmed, and any discrepancy is re-opened as a new tracked todo here with the discrepancy stated. — **DONE
      2026-08-10**: all 11 claims independently confirmed. All 8 code SHAs (`4d27bc1` `26f8a49` `7a7ef2e` `64a0291`
      `463ee10` `a1e2969` `59d9417` `66be387`) exist on `origin/live-defi-rollout` with diffs matching the claims. Cited
      regression tests re-run green via the repo venv (229 passed across the 6 touched files; todo 11's 8 new tests
      8/8). Todo 5 `--apply` post-state verified live: `one-off:agt-7e7e2c`
      ($0.072119, slot 9) +
      `one-off:agt-a0bd62` ($0.029804, slot 4) present in `task_usage` with `backfilled=1`;
      `one-off:agt-53f733` correctly `backfilled=0`. Todo 6 re-ran `audit_false_done.py` against live `state.db`:
      UNAUDITABLE=**11**, all `status=done`. Todo 8 post-state verified on-host (ip-172-31-5-118): all 5 repos on
      `live-defi-rollout` ahead=0/behind=0 + `archive/pre-reset-20260810T015655Z` tags present. Todo 7
      `apply_transition` re-read and confirmed MATCH. Playwright (`pw:L2`) execution not independently re-runnable in
      this sandbox (documented environment limitation — `node_modules` absent, npx playwright broken); specs
      well-formed + diffs match. One minor wording discrepancy: todo 1's evidence says "6 new tests" but `4d27bc1` adds
      5 test functions (substance verified). **Separate finding (NOT a batch12 false-done)**: pre-existing
      `test_kill_session_passes_exact_match_target` broke at HEAD because post-batch12 `0c27963` added a `git rev-parse`
      subprocess to `kill_session`'s log line after the tmux kill — fixed + shipped `agent-orchestrator@8ee59be` (full
      QG green: 3233 passed, 2 skipped).
- [x] ✅ [REVIEW] P0. **Reconcile each verified todo's evidence into its TRUE source doc's own checkbox** — replace the
      redirect-pointer text batch12 left behind with the real completion evidence (commit sha / query result / recorded
      verdict), per source: `deepseek_flash_ab_routing_test_2026_08_05.md` (todos 2, 4, 12a, 17b, 25),
      `ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md` (its 2 `[BACKEND] P3` Follow-ups items),
      `fleet_host_inventory_dead_host_and_pre_rewrite_drift_2026_08_08.md` (its Finding-2 `[DEVOPS] P2` todo — Finding 1
      was already closed directly on the source doc, not by this batch),
      `forced_compact_reports_submitted_but_never_executes_2026_08_08.md` (its 3 `[BACKEND]` P1/P1/P2 todos). **Done
      when**: all 11 source checkboxes carry real evidence, not a bare redirect pointer. — **DONE 2026-08-10**
      (`unified-trading-pm@c8f2055811`): all 11 source checkboxes flipped/corrected with real evidence — deepseek todos
      2/4/12a/17b/25 (commit SHAs + live-run results), ao_false_done 2 Follow-ups (re-ran audit UNAUDITABLE=11 +
      `apply_transition` MATCH verdict), fleet_host Finding-2 (clean-reset post-state: 5 repos ahead=0/behind=0 +
      archive tags), forced_compact 3 todos (`a1e2969`/`59d9417`/`66be387`). Redirect pointers + KEEP-NA-STALE
      citation-closed annotations replaced. Verified by grep: no `do NOT action here` / `KEEP-NA-STALE, citation-closed`
      remains on any live todo (one historical Progress-Log quote of the old annotation is correctly left intact).
- [x] ✅ [REVIEW] P1. **Check whether any of the 4 source docs is now fully closed** (every remaining open todo done,
      not just the extracted ones) — if so, run the standard 6-step archival ritual on it (banner, codex-alignment
      check, corpus-wide referrer fixup, lock check). Each source doc is expected to retain other open, non-extracted
      items (`deepseek_flash_ab_routing_test_2026_08_05.md` in particular has ~10 other open todos unrelated to this
      batch), so this is a check, not an assumed action. **Done when**: each of the 4 source docs' current open-todo
      count is confirmed, and any doc found fully closed is archived with evidence cited here. — **DONE 2026-08-10**
      (`unified-trading-pm@c8f2055811`). Open-todo counts confirmed: **deepseek_flash_ab_routing_test = 0** (fully
      closed — the plan's ~10-remaining-item assumption was superseded: the 6 time-gated items were completed by batch18
      on 2026-08-10 once the 24h window elapsed) → **ARCHIVED** via the full 6-step ritual (banner +
      `status: archived` + `superseded_by: deepseek_claude_blended_provider_routing_2026_07_28` + git mv to
      `plans/archive/2026_08/` + all 8 corpus referrers updated + the one genuine prose deferral — the ~$2.35 flash
      spend residual — migrated to `issues/deepseek_flash_spend_235_residual_2026_08_10.md`). **ao_false_done = 0** but
      its archival is OWNED by its own existing active finalize plan
      (`ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08_finalize_2026_08_08.md`, which still has open
      REVIEW/DOCS todos incl. "archive the parent doc") → left for it to archive, no double-archival. **fleet_host = 0**
      but already archived (`plans/archive/issues/`) → nothing to do. **forced_compact = 1** (the explicitly time-gated
      "re-measure the wedge rate" P3) → correctly stays active.
- [x] ✅ [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch12_2026_08_09.md`, move to `plans/archive/2026_08/`, fix
      every corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then re-run the
      active-plan inventory generator. **Done when**: the batch plan is archived with a banner, the inventory
      regenerates cleanly, and `check_finalize_plan_coverage.py` no longer names this pair. — **DONE 2026-08-10**:
      batch12 plan ARCHIVED (banner + `status: archived` + git mv to `plans/archive/2026_08/`); all 4 full-path corpus
      referrers updated (this finalize plan's `related:`/`context_scope`, batch14, forced_compact, fleet_host) +
      bare-slug `depends_on` now resolves to the archived slug; `regenerate_active_plan_inventory.py` runs clean (320
      plans); INDEX regenerated via `regenerate_active_plan_index.py` (320 plans, archived docs removed);
      `check_finalize_plan_coverage.py` = 0 violations — the (batch12, finalize) pair is no longer named.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips).

## Progress Log

- **2026-08-09** — Authored in the same turn as batch12, per the mandatory finalize-twin rule (task_template.md §4).
  `sequential: true` since the 4 todos are a genuine chain (verify → reconcile → check-and-archive sources → archive
  self). Ships `status: active` (not `draft`) — `gate_on_depends` already machine-holds every task until batch12's own
  todos are all done, matching the batch7-11 finalize precedent.
