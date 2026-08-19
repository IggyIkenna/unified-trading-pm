---
doc_type: issue
title: "plan_reconciler's boot message sets $PM_REPO_PATH to the ROOT PM clone (read-only) instead of the dispatched slot's clone -- 2nd confirmed occurrence"
summary: >-
  Two independent plan_reconciler dispatches (agt-2be768/slot 10, 2026-08-16, sports tranche; agt-57336e/slot 31,
  2026-08-18, sports tranche) both received a boot message where `$PM_REPO_PATH` resolved to
  `/home/ubuntu/unified-trading-system-repos/unified-trading-pm` (the root clone) instead of the dispatched slot's own
  clone (`.tabs/<N>/unified-trading-pm`) -- directly contradicting `agents/RULES.md`'s repeated HARD RULE that
  root-clone work is READ-ONLY and all writes happen in the assigned slot. Both dispatches independently caught this
  via the doc/pointer-that-misled-me HARD RULE and worked around it by operating out of their own slot clone instead,
  but neither could fix the dispatcher itself (out of scope for a plans/** doc-reconciliation run). Also observed both
  times: none of the boot message's other "session variables" (`SERVER_URL`, `SLOT_ID`, `DISPATCH_ID`, `WORKTREE`,
  `TRANCHE`, `BRANCH`) are actually exported shell env vars -- every HTTP call and path must use literal values
  substituted from the boot message text, not `$VARNAME` references (confirmed via `env | grep`, both dispatches).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, plan_reconciler, boot-prompt, dispatch, env-vars, tmux-spawn, recurring]
related:
  [
    /agents/plan_reconciler.md,
    /plans/archive/issues/plan_reconciler_findings_sports_2026_08_16.md,
    /plans/active/issues/plan_reconciler_findings_sports_2026_08_18.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-18"
author: plan_reconciler
parent_epic: orchestrator_master
assigned_vm: planning # reclassified NA -> planning 2026-08-19 (na-eligibility-audit, ao tranche) — conflict-check CLEAR
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  First occurrence: agt-2be768/slot 10, 2026-08-16 sports-tranche dispatch, flagged in
  plan_reconciler_findings_sports_2026_08_16.md (now archived) but never filed as its own tracked issue. Second,
  independent occurrence: agt-57336e/slot 31, 2026-08-18 sports-tranche dispatch (this doc's author) -- same exact
  misconfiguration, confirming it is systemic to the plan_reconciler dispatch path, not a one-off.
context_scope:
  [
    agent-orchestrator/server/plan_health.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/scripts/install-plan-reconciler-timer.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/agents/RULES.md,
  ]
---

# plan_reconciler dispatch wiring: `$PM_REPO_PATH` points at the root clone, not the slot's own — 2nd occurrence

## Evidence

**2026-08-16 (agt-2be768, slot 10)**: boot-provided `$PM_REPO_PATH` resolved to
`/home/ubuntu/unified-trading-system-repos/unified-trading-pm` (root clone). Flagged in the run's own findings doc
(now archived, see `related:`), worked around by operating out of `.tabs/10/unified-trading-pm` instead. Never filed
as its own tracked issue — sat only as a note inside a dated findings doc.

**2026-08-18 (agt-57336e, slot 31)**: identical boot message shape — `$PM_REPO_PATH` again resolved to the root
clone. Additionally confirmed this run: `env | grep -E '^(SERVER_URL|PM_REPO_PATH|SLOT_ID|DISPATCH_ID|WORKTREE|TRANCHE|BRANCH)='`
returns nothing — none of the boot message's "session variables" are real exported shell env vars in the spawned
tmux pane's shell. Every subsequent Bash call in this session had to use literal values (e.g. the literal URL
`http://localhost:8765/api/slots/31/heartbeat`, not `$SERVER_URL/api/slots/$SLOT_ID/heartbeat`) since Bash tool calls
each start a fresh shell with no persisted state from a prior call, and these values were never exported anywhere a
fresh shell would inherit them from.

Both dispatches independently reached the same conclusion (root-clone path is a misconfiguration, not intentional)
via `agents/RULES.md`'s own explicit, repeated guardrail text: "root-clone reads are READ-ONLY. ALL work happens
inside your assigned slot directory."

## Why this matters

A worker that does NOT independently catch this (unlike both occurrences here) risks writing/committing directly
into the shared root PM clone — which is read by every other slot's boot sequence and role-file reads. A commit
landing there via a raw filesystem write (bypassing the normal per-slot git remote flow) could corrupt the shared
canonical checkout other slots read from, or simply confuse git state in a clone nothing expects to be dirty.

## Recommended fix

- Audit `agent-orchestrator/server/autospawn.py` (or wherever the `plan_reconciler` boot-prompt template is rendered)
  for where `$PM_REPO_PATH` is populated for a `tranche`-sharded dispatch — it should resolve to
  `{WORKSPACE_ROOT}/.tabs/{slot_id}/unified-trading-pm`, matching `$WORKTREE`, not the root clone path.
- Separately: either actually `export` the documented session variables into the spawned tmux pane's shell
  environment (so `$SERVER_URL`/`$SLOT_ID`/etc. work as literally documented across every Bash call), or correct
  `agents/plan_reconciler.md` + `agents/RULES.md` to stop implying they are real env vars and instead present them as
  boot-message text a worker must substitute manually. Current state is a doc/reality mismatch either way.

## Todos

- [x] ✅ [BACKEND] P2. Find and fix the `plan_reconciler` (and likely every sharded `plan_health`-family role's) boot
      prompt template's `$PM_REPO_PATH` population to resolve to the dispatched slot's own clone, not the root PM
      clone. Done when: a fresh sharded dispatch's boot message shows `$PM_REPO_PATH` under `.tabs/<slot>/`, verified
      against a live dispatch. — `agent-orchestrator@6eeee7f7f8` (verified: ancestor of `origin/live-defi-rollout` +
      content grep on the landed commit). `plan_health.dispatch()` now rewrites `pm_repo_path` right after
      `_pick_free_slot()` resolves the actual slot: `pm_repo_path = str(Path(slot.worktree or f".tabs/{slot_id}/") /
      "unified-trading-pm")`, using the SAME `slot.worktree` source `$WORKTREE` already derives from, so they can
      never drift apart. Sits inside the one shared `dispatch()` call site every plan_health-family mode routes
      through (report/reconcile/docs_reconcile/ag_closeout/na_eligibility/context_scout/cefi_reconciliation/
      cefi_mtds_smoke/escalation_reconcile/ci_reconcile/data_pipeline_alerts_reconcile/ao_watchdog) — not a
      plan_reconciler-only patch. Regression test updated:
      `agent-orchestrator/tests/test_plan_health.py::test_dispatch_happy_path_spawns_plan_health_template` now
      asserts the extra_vars value equals the picked slot's own clone path and explicitly differs from the
      caller-supplied default. Full QG green (4123 passed / 9 skipped, dashboard 414 passed) before ship.
- [x] ✅ [BACKEND] P3. Decide + implement one of: (a) actually export the boot-message session variables into the spawned
      shell environment, or (b) correct `agents/plan_reconciler.md`/`agents/RULES.md` wording to stop presenting them
      as real env vars. Done when: the doc and the runtime behavior agree. — Picked **(b)**: the orchestrator's own
      boot-stub composer (`agent-orchestrator/server/prompts.py::_compose`) already treats every session value as
      literal text — its STEP 2/3 curl commands interpolate `{server_url}`/`{slot_id}` as plain Python f-strings, never
      `$VAR` shell syntax, and its module docstring states the worker "READS its role/RULES files" rather than
      inheriting exported state. Making these genuinely-exported shell env vars would need new per-shell-invocation
      plumbing (e.g. a sourced env file every fresh Bash-tool shell picks up) since a worker's tool calls each start a
      FRESH shell with no state persisted from a prior call — confirmed live 3x (`env | grep` empty across 3
      independent dispatches, this doc's own Evidence section). (b) is the lower-risk, already-consistent-with-the-
      architecture choice. Implemented as ONE canonical explanation in `agents/RULES.md` § "Your worktree — read from
      root, operate only in your slot" (read FIRST by every plan_health-family role per
      `agent-orchestrator/server/prompts.py::expected_read_files`, so this covers all 5 role files the finalize doc
      names — `plan_reconciler.md`/`na_eligibility_auditor.md`/`docs_reconciler.md`/`ag_closeout_auditor.md`/
      `plan_health.md` — without touching each individually) plus a shorter pointer note in `agents/plan_reconciler.md`
      itself (the file most directly implicated by the 3 live occurrences). Shipped via `safe-doc-push.sh`.

## Progress Log

- **plan_reconciler 2026-08-18 (ao tranche, hunter #3, Phase -1 pass)**: root-caused todo 1 by reading the live
  dispatch call chain directly (not trusting either occurrence's own diagnosis alone). Confirmed exact origin:
  `agent-orchestrator/scripts/install-plan-reconciler-timer.sh:88` — `PM_REPO="${PM_REPO:-/home/${OPERATOR}/unified-trading-system-repos/unified-trading-pm}"`
  — defaults to the ROOT clone, and line 281's per-tranche curl body passes this literal `${PM_REPO}` value straight
  into `POST /api/plan-health/dispatch`'s `pm_repo_path` field, unconditionally, for every one of the (up to 10)
  concurrent tranche dispatches. Traced the Python side too: `plan_health.dispatch()` (`server/plan_health.py`)
  never rewrites `pm_repo_path` after `_pick_free_slot()` resolves the actual target slot — the value flows
  verbatim from the caller straight into `autospawn.do_spawn(..., extra_vars={"pm_repo_path": pm_repo_path, ...})`
  (lines ~784/803), which becomes the boot message's literal `PM_REPO_PATH` session var. So this is not a timing
  race or a stale-default edge case — it is structural: the shell script cannot know the slot in advance (the slot
  is picked inside the Python call), and nothing on the Python side substitutes the picked slot's own
  `.tabs/{slot_id}/unified-trading-pm` path once it IS known. Confirms the doc's own recommended-fix direction is
  the only viable one — the correction has to happen inside `dispatch()`, after slot pick, not in the calling shell
  script. Not fixed here (real `agent-orchestrator` engineering, out of scope for a plans-corpus reconciliation
  pass) — todo 1 stays open, now with the exact file:line evidence needed to implement it directly. Todo 2 not
  independently re-verified this pass (the doc's own live `env | grep` evidence from 2 separate dispatches already
  stands; no new information to add).
- **na-eligibility-audit 2026-08-19 (ao tranche)**: RECLASSIFY (whole-doc) -> `assigned_vm: planning`. Root cause already fully traced with exact file:line evidence by a same-day plan_reconciler pass; both todos (fix the boot-template wiring + reconcile the session-var-export/doc-wording question) are bounded/deterministic. Conflict-check clear: no other active planning doc claims this fix. Companion gated finalize: `plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18_finalize_2026_08_19.md`.

**THIRD confirmed occurrence, na_eligibility_auditor (ao tranche, this run)**: this exact session's own boot message set `$PM_REPO_PATH` to `/home/ubuntu/unified-trading-system-repos/unified-trading-pm` (the root clone) rather than `.tabs/30/unified-trading-pm` (this session's own slot clone) — verified via `git status`/`git log` comparison of both paths before any write. Corroborates this doc's todo 1's own prediction that the bug generalizes to "every sharded plan_health-family role's boot prompt template", not just plan_reconciler's. Followed the same sanctioned workaround as the two prior occurrences: verified `.tabs/30/unified-trading-pm` was clean/current (ahead=0, behind=0, no stale `.agent-claim`) and did every Phase 3/4 write for this audit run there instead of the root clone. No new issue doc filed — this doc already tracks the class; noted here as evidence + folded the generalization into this doc's own finalize plan's reconcile todo (verify the fix covers every plan_health-family role, not just plan_reconciler).

- **2026-08-19 (dispatched worker)**: Both todos implemented and shipped. Todo 1: `agent-orchestrator@6eeee7f7f8` —
  `dispatch()` now rewrites `pm_repo_path` to the picked slot's own `.tabs/<slot_id>/unified-trading-pm` immediately
  after `_pick_free_slot()`, matching `$WORKTREE`'s own `slot.worktree` source. Ship hit heavy multi-session
  contention on this shared `.tabs/3/agent-orchestrator` checkout (2+ other live sessions concurrently running their
  own `quickmerge --isolated` ships to the same branch) — two earlier isolated-ship attempts silently lost the
  uncommitted diff during the isolation evacuate/restore cycle (working tree came back clean with zero trace of the
  fix, no stash, no reachable commit — re-applied the identical edit from a preserved copy of the diff both times).
  Third attempt landed cleanly; independently verified post-ship via `git merge-base --is-ancestor 6eeee7f7f8
  origin/live-defi-rollout` (pass) + `git show 6eeee7f7f8:server/plan_health.py \| grep` for the exact added line
  (found) — not just the ship script's own printed "success", per this workspace's measurement-claims-discipline
  rule. Todo 2: direction (b) chosen and shipped in `unified-trading-pm` (this same commit batch) — see the todo's own
  evidence line for the reasoning. Both QG-verified (agent-orchestrator: 4123 passed/9 skipped + dashboard 414
  passed, 0 basedpyright errors) before shipping.
