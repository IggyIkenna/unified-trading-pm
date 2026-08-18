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
assigned_vm: NA
execution_scope: local-only
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

- [ ] [BACKEND] P2. Find and fix the `plan_reconciler` (and likely every sharded `plan_health`-family role's) boot
      prompt template's `$PM_REPO_PATH` population to resolve to the dispatched slot's own clone, not the root PM
      clone. Done when: a fresh sharded dispatch's boot message shows `$PM_REPO_PATH` under `.tabs/<slot>/`, verified
      against a live dispatch.
- [ ] [BACKEND] P3. Decide + implement one of: (a) actually export the boot-message session variables into the spawned
      shell environment, or (b) correct `agents/plan_reconciler.md`/`agents/RULES.md` wording to stop presenting them
      as real env vars. Done when: the doc and the runtime behavior agree.
