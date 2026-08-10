---
doc_type: plan
title: AO satellite AO batch 10 — finalize
summary: >-
  Gated closeout for `ao_satellite_ao_dispatch_batch10_2026_08_09.md` — machine-held via `depends_on` +
  `gate_on_depends` until all 6 of that batch's todos are done. Reconciles each verified todo's evidence back into its
  TRUE source doc's own checkbox (`ao_satellite_ao_dispatch_batch2_2026_07_30.md` ×2,
  `ao_open_issues_consolidated_close_out_2026_07_17.md` ×3,
  `dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md` ×1) — replacing each source checkbox's redirect-pointer
  with the real evidence, not just re-flipping it blind — then checks whether any source doc is now fully closed
  (unlikely given each retains other open, non-extracted items) and archives it if so, before archiving the batch plan
  itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator, strategy-service]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-10, finalize, satellite-extraction]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch10_2026_08_09.md,
    /plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/active/issues/dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: review
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch10_2026_08_09]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch10_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch, 2026-08-09, per the satellite-batch-extraction pattern's mandatory finalize-twin rule.
---

# AO satellite AO batch 10 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch10_2026_08_09.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until all 6 of that batch's todos are `done`. The batch itself stays
> `status: draft` until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [x] ✅ [REVIEW] P0. **Re-verify all 6 of batch10's done-claims against reality, not against their checkboxes** — for
      each: re-run/re-check the cited evidence (a live query re-run for the read-only items, `git show --stat <sha>` for
      any code change, the named regression check where one exists). **Done when**: each of the 6 claims is
      independently confirmed, and any discrepancy is re-opened as a new tracked todo here with the discrepancy stated.
      **VERIFIED 2026-08-10 (slot 24, review)** — all 6 claims confirmed against reality: (1) na-eligibility timer:
      `agent-orchestrator@17939c3` (TimeoutStartSec 2450→21600) present in
      `scripts/install-na-eligibility-auditor-timer.sh`; live `state.db` shows `na_eligibility_auditor`
      `exit_reason=lifecycle-complete` rows (cited `agt-b831d5` + fresh 2026-08-10 `agt-ffd0db`/`agt-a70469`). (2)
      wip-preserve ref: `git ls-remote origin 'refs/wip-preserve/*'` empty (never a real remote ref); preserved commit
      `a77eb6d1`'s `staging-lock-check.yml` byte-identical to superseding `400d3773` (verified LDR ancestor). (3) ao
      archive sweep: 0 genuine orphans held as-of the 2026-08-09 sweep (check_archive_candidates 0, inventory 0/297),
      but the corpus-wide gates have since drifted — re-opened as new todo 5 below. (4) plan_reconciler: activity rows
      396415 (dispatch `agt-a398c9` @03:02:46) + 397344 (result @04:43:25: contradiction_count=5, doc_drift_count=5,
      fixes_count=12, filed=4, commit_sha=40ad77233, pr_url=pull/2653) match the claim exactly; PR 2653 (head
      `plan_reconciler/agt-a398c9`) CLOSED; R1 `_reclaim_exited_slot` (`worker_liveness_watchdog.py:1311`, gated on
      `has_session()==False` → `reset_slot_worker_state(...,"idle")`); R2 `watchdog_heartbeat_timeout=900` /
      `watchdog_scheduled_heartbeat_timeout=3600` (`config.py:489/499`) + `_heartbeat_timeout_for`
      (`worker_liveness_watchdog.py:715`). (5) role lifecycle: all 5 craft role files declare `lifecycle: persistent`;
      AO commits c72daaa+4421129, PM commit 14f1dcd. (6) prettier: `agent-orchestrator@fcbc736` exists;
      `dashboard/package.json:28` = `"prettier": "^3.9.5"`.
- [ ] [REVIEW] P0. **Reconcile each verified todo's evidence into its TRUE source doc's own checkbox** — replace the
      redirect-pointer text batch10 left behind with the real completion evidence (commit sha / query result / recorded
      verdict), per source: `ao_satellite_ao_dispatch_batch2_2026_07_30.md` (its `[SCRIPT] P3` line ~199 and `[DATA] P2`
      line ~242), `ao_open_issues_consolidated_close_out_2026_07_17.md` (its `[REVIEW] P0` line ~479, `[BACKEND] P0`
      line ~806, `[BACKEND] P0` line ~828), `dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md` (its 2nd
      `[INFRA] P3`, line ~81). **Done when**: all 6 source checkboxes carry real evidence, not a bare redirect pointer.
- [ ] [REVIEW] P1. **Check whether any of the 3 source docs is now fully closed** (every remaining open todo done, not
      just the extracted ones) — if so, run the standard 6-step archival ritual on it (banner, codex-alignment check,
      corpus-wide referrer fixup, lock check). Each source doc is expected to retain other open, non-extracted items
      (see batch10's own Progress Log for what was deliberately left behind in each), so this is a check, not an assumed
      action — do not force an archival if real work remains. **Done when**: each of the 3 source docs' current
      open-todo count is confirmed, and any doc found fully closed is archived with evidence cited here.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch10_2026_08_09.md`, move to `plans/archive/2026_08/`, fix every
      corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then re-run the active-plan
      inventory generator. **Done when**: the batch plan is archived with a banner, the inventory regenerates cleanly,
      and `check_finalize_plan_coverage.py` no longer names this pair.
- [ ] [REVIEW] P1. **Corpus-wide plan-hygiene gates drifted since batch10's sweep — archive the 2 new
      `check_archive_candidates.sh` candidates + epic-wire the orphaned 2026-08-10 satellite plans.** Re-opened by P0's
      re-verification (claim 3 held as-of the 2026-08-09 sweep, but both gates are now RED against baseline). (1)
      `check_archive_candidates.sh` now reports **2 candidates vs baseline 0**:
      `plans/active/issues/mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md`
      (`asset_group: [defi, prediction]`, `parent_epic: infrastructure_master` — out of batch10's
      `ao`/`orchestrator_master` scope; its done `[x]` was wrapped in a code-span and invisible to the checker until the
      2026-08-10 prose-formalization reformat; genuinely all-done + unlocked → archive-eligible via the 6-step ritual)
      and `plans/active/issues/plan_reconciler_unexplained_tmux_session_loss_2026_08_10.md` (filed 2026-08-10 by batch10
      todo 4's own evidence; its single `[BACKEND] P2` todo is done → archive-eligible, but FIRST capture its
      `tmux_session_lost` rate-canary monitoring recommendation as a tracked `- [ ]` todo per the todos-not-prose rule,
      then archive). (2) `regenerate_active_plan_inventory.py` now reports **3 orphans / 313 plans** (was 0/297 at the
      sweep) — the newly-created 2026-08-10 satellite batch/finalize plans (`tradfi_satellite_ao_dispatch_batch12_*`,
      `ao_satellite_ao_dispatch_batch19_*`, `cefi_satellite_ao_dispatch_batch17_*`) aren't yet referenced by
      master/epics. **Done when**: both candidates archived + the rate-canary todo captured, the orphaned plans are
      epic-wired, and the inventory regenerates clean.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips).

## Progress Log

- **2026-08-09** — Authored in the same turn as batch10, per the mandatory finalize-twin rule (task_template.md §4).
  `sequential: true` since the 4 todos are a genuine chain (verify → reconcile → check-and-archive sources → archive
  self). Ships `status: active` (not `draft`) — `gate_on_depends` already machine-holds every task until batch10's own
  todos are all done, matching the batch7-9 finalize precedent.
- **2026-08-10 (slot 24, review)** — P0 done: re-verified all 6 of batch10's done-claims against reality (see todo 1's
  evidence). 5 claims confirmed cleanly; claim 3 (ao archive sweep) confirmed as-of its 2026-08-09 sweep but the
  corpus-wide gates have since drifted: `check_archive_candidates.sh` is RED (2 candidates vs baseline 0 —
  `mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md` +
  `plan_reconciler_unexplained_tmux_session_loss_2026_08_10.md`) and the inventory reports 3 orphans / 313 plans (was
  0/297). Re-opened as new todo 5 (P1).
