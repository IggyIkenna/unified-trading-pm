---
doc_type: plan
title: AO satellite AO batch 3 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch3_2026_07_31.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source issue doc(s)
  (the batch was an extraction, so the source docs' own checkboxes are the ones that go stale), re-checks whether either
  Deferred item's gate has since cleared, archives the source docs that reach zero open todos, and runs the standard
  6-step archival ritual on the batch plan itself.
status: resolved
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-3, finalize]
related:
  [
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch2_finalize_2026_07_30.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-31"
last_updated: "2026-08-03"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: review
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: >-
  All 6 finalize todos completed 2026-08-20; batch 3 and its zero-open-todo source docs were archived with referrers fixed.
depends_on: []
sequential: true
context_scope:
  [
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the /ag-closeout-audit ao skill run of 2026-07-31 (scheduled dispatch agt-23935a). Ships
  `status: active` (not draft) per the skill's 2026-07-30 finding: gate_on_depends already machine-holds every task
  until the batch's own todos are done, so a second draft-gate is a redundant, easy-to-forget manual flip.
---

# AO satellite AO batch 3 — finalize

> **ARCHIVED 2026-08-20.** The batch and finalize plan are both resolved; the former was archived after all three
> batch todos completed and the latter after all six finalize todos completed.

## Todos

- [x] ✅ [REVIEW] P0. **Re-verify every batch-3 done-claim against reality, not against its checkbox** — for each of the 3
      todos in `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch3_2026_07_31.md`, re-run `git show --stat <sha>` for every
      cited commit and re-run the specific named test(s) directly rather than trusting the claim, and re-run each todo's
      own stated done-when check where it is a command (the `generate_context_scope_inventory.py` zero-remaining check,
      the priority-inversion replay test, the orphan-verifier's 10-verdict reproduction + the liveness discriminator's
      slot-5/slot-15 shape checks + the 25-ref wip-preserve disposition table). **Done when**: all 3 verified, and any
      claim whose evidence does not hold up is re-opened as a new tracked todo in this doc's Progress Log with the
      discrepancy stated. **VERIFIED 2026-08-20** (slot 7, finalize worker): (1) context_scope claim holds —
      `docspec.py` `context_scope` FieldSpec confirmed `Req.R` for plan+issue doc_types (flip commit
      `unified-trading-pm@bc88604f20`, 2026-08-20), inventory at-claim-time 888/888 consistent; a fresh
      `generate_context_scope_inventory.py --json` run this session shows post-claim drift (1 NEVER_SCOUTED + 4 STALE,
      887 in-scope) — re-opened as todo 2 below, NOT a falsified claim. (2) priority-inversion claim holds —
      `agent-orchestrator@af98fcd` present on LDR with exactly the claimed files; full
      `tests/test_dispatch_priority_inversion_watchdog.py` green (20 passed, incl. the recorded-incident replay
      asserting exactly-once page fire). (3) orphan-verifier claim holds — `agent-orchestrator@623009e3` present with
      the claimed files; `tests/test_orphan_still_orphaned_verifier.py` (4 canonical verdicts + wip-preserve end-to-end)
      and `tests/test_dirty_state_resolution.py` (liveness slot-5/slot-15 triangulation + controls) green; the 29-ref
      wip-preserve disposition table is internally consistent (16 SUPERSEDED / 10 STILL-ORPHANED / 3 WOULD-REGRESS / 0
      GONE = 29 rows). Live SSM re-run of the 29-ref triage attempted but **not reproducible from this session**
      (AccessDenied on `ssm:DescribeInstanceInformation` for identity `ikenna-worker` — the original batch-3 session's
      SSM path is unavailable here); recorded-table + verifier tests stand as the evidence.
- [x] ✅ [SCRIPT] P2. **Scout the 5 post-claim context_scope-drift docs back to UP_TO_DATE** — re-opened from finalize
      todo 1's verification (2026-08-20): the batch3 todo-1 done-when (`generate_context_scope_inventory.py` zero-
      remaining check) no longer holds in the present — a fresh run reports 882 UP_TO_DATE / 4 STALE / 1 NEVER_SCOUTED
      / 887 in-scope. All 5 are post-claim churn (4 docs created 2026-08-20 by concurrent sessions; 1 pre-existing doc
      gone STALE), not a falsified backfill claim — the FieldSpec `Req.R` flip (`unified-trading-pm@bc88604f20`) and the
      888/888 at-claim-time snapshot both verified. The 1 NEVER_SCOUTED doc
      (`/plans/active/issues/dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md`) is now
      missing a REQUIRED field — a genuine `check_frontmatter_schema.py` violation. Docs to scout:
      `/plans/active/issues/dp_live_004_sports_odds_live_shard_never_captured_shared_key_quota_2026_08_20.md`
      (NEVER_SCOUTED), `/plans/active/issues/client_reporting_api_nav_aggregation_vehicle_type_blind_2026_08_20.md`,
      `/plans/active/issues/context_scope_backfill_locked_docs_residual_2026_08_20.md`,
      `/plans/active/issues/live_sports_odds_upstream_failure_masked_as_honest_absence_2026_08_20.md`, and
      `/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md` (all STALE). **Done when**: fresh
      `generate_context_scope_inventory.py --json` reports 0 NEVER_SCOUTED / 0 STALE, matching batch3 todo-1's own
      done-when. (repo: unified-trading-pm) — **DONE 2026-08-20** (slot 3): all 5 docs scouted back to UP_TO_DATE, shipped
      `unified-trading-pm@b215a78248` (on origin/live-defi-rollout). The "1 NEVER_SCOUTED" doc (dp_live_004) had already
      gained a `context_scope` field from a concurrent session by pick-up (so it was STALE, not missing) — its codex-only
      list was completed with the 3 source paths its own body names (`odds_api_ws.py`, `websocket_runner.py`,
      `odds_api_adapter.py`); the other 4 docs only needed the dated `context-scout 2026-08-20` marker. Fresh
      `generate_context_scope_inventory.py --json` confirms all 5 target docs UP_TO_DATE.
- [x] ✅ [REVIEW] P0. **Reconcile each verified todo's evidence back into its TRUE source doc's own checkbox(es)** — batch
      3 was an extraction, so the source-doc items it covers are the ones that go stale, not the batch's. Flip the
      specific todo(s) in each of: `context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md` (its `[SCRIPT] P0`
      item), `ao_dispatch_priority_inversion_starvation_has_no_page_path_2026_07_30.md` (both its `[BACKEND] P2` and
      `[SCRIPT] P3` items), `orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md` (both its `[SCRIPT] P2` items
      plus its `[DATA] P3` item), and `wip_preserve_refs_silently_unrecovered_2026_07_29.md` (its own `[DATA] P3` item —
      the duplicate this batch folded in, so it flips in lockstep with `orphaned_commit_recovery`'s `[DATA] P3`, not
      independently). **Done when**: every one of those flips is committed with the `docs(plans):` prefix and cites the
      real commit sha (or, for the read-only verification items, the reproduction evidence). — **VERIFIED 2026-08-20**
      (slot 3): all 7 named source checkboxes already `[x]` with evidence — the batch3 workers reconciled inline as they
      shipped, so no flips remained outstanding: context_scout_completion `[SCRIPT] P0` → DONE-BY-CITATION (batch3 todo 1,
      `docspec.py` Req.E→Req.R @`unified-trading-pm@bc88604f20`); ao_dispatch_priority_inversion `[BACKEND] P2` +
      `[SCRIPT] P3` → `agent-orchestrator@af98fcd` + live-backlog backfill-check; orphaned_commit_recovery `[SCRIPT] P2`
      (verifier) + `[SCRIPT] P2` (liveness) + `[DATA] P3` → `agent-orchestrator@623009e3`; wip_preserve_refs `[DATA] P3` →
      same `@623009e3` 29-ref triage.
- [x] ✅ [INFRA] P0. **Re-check both Deferred-bucket items' gates and spin any newly-cleared ones into batch 4** — for
      `orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md`'s `[REVIEW] P3` item, re-check whether it has
      since been scoped into its own dedicated plan (e.g. via `/plan-brainstorm`) — if so, mark this batch's Deferred
      entry resolved-elsewhere; if not, leave it deferred with the same reasoning. For
      `omniroute_llm_gateway_pilot_design_2026_07_30.md`, re-check whether the operator has since lifted the explicit
      NA/human-only ruling — if lifted, its 5 bounded `[INFRA]`/`[BACKEND]` todos become batch-4 material; if not, leave
      it deferred. Also re-check the data-correctness finding parked in
      `/plans/archive/issues/ag_closeout_audit_ao_parked_2026_07_31.md` (the false "backfill already done" claim in
      `context_scope_consumption_enforcement_2026_07_30.md`) — confirm whether it has been corrected; if not, escalate
      again rather than letting it go stale a second time. **Done when**: each of the 3 items is marked
      cleared-and-moved (naming the new batch-4 plan/todo or the resolving plan) or still-gated with the current reason
      — no entry left unstated. — **DONE 2026-08-20** (slot 3, infra craft): all 3 re-checked directly against the
      archived docs' live status, no batch-4 material produced by any of the three. (1)
      `orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md` — resolved DIRECTLY, not via a new dedicated
      plan: the doc itself is `status: resolved` (`resolved_by: /ag-closeout-audit ao (2026-08-16)`), its sole open
      `[REVIEW] P3` item flipped `[x]` 2026-08-16 — `agent-orchestrator@ca6603af` shipped `cgroup_memory_snapshot()`
      surfaced over `/ws/vm-resources`, satisfying the done-when (a dedicated dashboard UI tile was explicitly out of
      scope, not required). Nothing left to move into batch 4. (2) `omniroute_llm_gateway_pilot_design_2026_07_30.md` —
      the NA/human-only ruling was NOT lifted; instead the whole pilot is now `status: superseded`
      (`superseded_by: omniroute_multi_provider_routing_evaluation_2026_08_03`), archived 2026-08-06 under an explicit
      operator **no-go-for-now** ruling recorded in that evaluation plan's "Phase 3 — decision" — all 6 remaining open
      todos presupposed adopting OmniRoute and none survive the no-go; the doc's own banner confirms "nothing was
      migrated out." Same gated-on-operator reasoning class, just resolved via supersession rather than left open — no
      batch-4 material. (3) `ag_closeout_audit_ao_parked_2026_07_31.md`'s data-correctness finding — confirmed already
      corrected: `context_scope_consumption_enforcement_2026_07_30.md`'s "What's true today" section was fixed
      2026-08-01 (per that doc's own Progress Log and the parked-findings doc's own `resolved_by` field) and now states
      the accurate `Req.E`/majority-`NEVER_SCOUTED` facts; the parked doc itself carries `status: resolved`. No
      re-escalation needed.
- [x] ✅ [REVIEW] P0. **Archive every source doc that has reached zero open todos, and repoint any referrer.** At minimum
      Archived the final active source issue to `plans/archive/issues/` and migrated its watchdog contract to `/codex/04-architecture/agent-orchestrator-alerting.md`; the other three named sources were already archived and stale active-path referrers were repointed. Source verified zero open todos and unlocked; no active-path structural referrer remains — `agent-orchestrator@af98fcd` + evidence: hygiene sweep (11 pre-existing non-canonical todo warnings), frontmatter schema (2227 docs, 0 violations), active-plan inventory (381 plans, 2 orphans), and `git diff --check`.
      re-check `context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`,
      `ao_dispatch_priority_inversion_starvation_has_no_page_path_2026_07_30.md`,
      `orphaned_commit_recovery_has_no_dispatch_path_2026_07_30.md` (likely still has open non-batched items — check
      before archiving), and `wip_preserve_refs_silently_unrecovered_2026_07_29.md` (its 2 `[SCRIPT] P3` items are still
      deferred judgment calls — do not archive if so). Run the standard 6-step archival ritual (migrate any DEFERRED
      item → banner → codex-alignment check → update CLAUDE.md/codex if a contract changed → fix every referrer's path
      corpus-wide → clear the lock) on any doc that IS fully done. **Done when**: `grep -rl <slug> plans/ codex/`
      returns only the archived copy's own path for each archived doc, and
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports zero hard failures.
- [x] ✅ [INFRA] P0. **DONE 2026-08-20 — ran the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch3_2026_07_31.md`, migrate any still-Deferred item into batch 4 (never
      leave a deferral that is not already a `- [ ]` todo somewhere), move the file to `plans/archive/2026_08/`, fix
      every corpus-wide referrer including this finalize plan's own `related:`/ `depends_on:`, then run
      `.venv/bin/python scripts/plans/regenerate_active_plan_inventory.py` (CORRECTED 2026-08-18 /plan-reconcile —
      was `scripts/plan-hygiene/regenerate_active_plan_inventory.py`, which does not exist; the real script lives at
      `scripts/plans/regenerate_active_plan_inventory.py`, verified via `find`). **Evidence**: archived batch + finalize pair; `regenerate_active_plan_inventory.py` measured 379 plans and 2
      unrelated newly-created `state_fabric_*` plans without epic-body refs; `regenerate_active_plan_index.py` measured 379 active
      plans and 0 uncategorized; `check_finalize_plan_coverage.py --only` and `check_terminal_status_archived.py --only` both
      passed, and no old active-path referrer remains.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips),
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Progress Log

- **2026-07-31** — Authored in the same turn as its batch by `/ag-closeout-audit ao` (autonomous mode, scheduled
  dispatch agt-23935a). `sequential: true` is deliberate here: the five todos are a genuine chain (verify → reconcile →
  re-check gates → archive sources → archive self) and several touch the same files. Ships `status: active` per the
  skill's 2026-07-30 finding (`gate_on_depends` already holds every task; no separate draft-gate needed).
- **context-scout 2026-08-01**: verified the 3 pre-existing context_scope entries still resolve and are relevant (kept
  in place), added the gated parent batch plan as a 4th entry — refreshed (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (4 entries) — still the correct archival SSOT + batch pointer;
  no change needed. Gated finalize doc, no source path.
- **context-scout 2026-08-19**: re-verified context_scope (4 entries) — all paths confirmed resolving on disk, still
  the correct archival SSOT + batch pointer; no change needed.
- **2026-08-20 (todo 1 — VERIFIED, all 3 batch-3 claims hold)**: re-ran `git show --stat` for both cited commits
  (`agent-orchestrator@af98fcd`, `@623009e3` — file sets match the batch's claims exactly), the full
  `tests/test_dispatch_priority_inversion_watchdog.py` (20 passed, incl. the recorded-incident replay),
  `tests/test_dirty_state_resolution.py` + `tests/test_orphan_still_orphaned_verifier.py` (73 tests green across the
  three targeted files), a fresh `generate_context_scope_inventory.py --json` (882 UP_TO_DATE / 4 STALE / 1
  NEVER_SCOUTED / 887 in-scope — the 888/888 at-claim-time snapshot no longer holds ONLY due to post-claim churn; the
  FieldSpec `Req.R` flip verified live at `unified-trading-pm@bc88604f20`), and the wip-preserve disposition table
  (internally consistent: 16/10/3/0 = 29). Live SSM re-verify of the 29 wip-preserve refs attempted but
  **AccessDenied** for this session's identity (`ikenna-worker`, no `ssm:DescribeInstanceInformation`) — the original
  batch-3 session's SSM path is not reproducible from here; verifier code+tests + recorded-table consistency stand as
  the evidence. Drift re-opened as todo 2 (5 docs to re-scout).
- **2026-08-20 (todo 4 — DONE, both Deferred-bucket items re-checked, zero batch-4 material)**: read all 3 target docs
  directly rather than trusting this batch's own now-stale Deferred-section summary.
  `orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md` is now `status: resolved` — its `[REVIEW] P3`
  item shipped 2026-08-16 via `/ag-closeout-audit ao` (`agent-orchestrator@ca6603af`), resolved directly rather than via
  a new dedicated plan. `omniroute_llm_gateway_pilot_design_2026_07_30.md` is now `status: superseded` — the operator
  issued an explicit no-go-for-now ruling 2026-08-06 (`omniroute_multi_provider_routing_evaluation_2026_08_03.md` §
  "Phase 3 — decision"), so the NA/human-only gate was never lifted, it was mooted; all 6 remaining todos presupposed
  adopting OmniRoute and the doc's own banner confirms nothing was migrated out. The data-correctness finding in
  `ag_closeout_audit_ao_parked_2026_07_31.md` was corrected 2026-08-01 (that doc's own `resolved_by` field plus the
  target doc's own Progress Log both confirm the fix); the parked doc carries `status: resolved`. No new batch-4 plan
  needed — all 3 items resolved without producing AO-eligible bounded work.
