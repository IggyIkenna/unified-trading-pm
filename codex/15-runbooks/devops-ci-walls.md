---
doc_type: codex-runbook
title: DevOps CI walls — recovery recipes for the common deploy/CI walls (cicd role)
summary:
  The DevOps (cicd) role's per-wall recovery runbook — v2-never-reported deadlock, behind-remote rebase, stuck LDR→main
  promotion, SIT/QG wall. Triage entry point is the /ci-status skill; every recipe cross-links its ci-cd-flow.md SSOT
  section instead of duplicating it.
status: current
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
tags: [runbook, devops, cicd, escalation, walls, quality-gates-v2, promotion]
related:
  [
    codex/08-workflows/ci-cd-flow.md,
    unified-trading-pm/agents/cicd.md,
    agent-orchestrator/server/ci_status.py,
    agent-orchestrator/server/escalation.py,
  ]
created: 2026-07-02
scope: [engineer, admin]
audience: dev / operator / the cicd one-shot worker
owner: "the dispatched cicd one-shot worker (operator when the wall escalates to main)"
cadence: "per-wall (event-driven — a wall dispatch IS the execution; no scheduled run)"
verifier:
  "python -m server.ci_status <repo> returns blocked=false for the walled repo after the fix (and the wall's escalation
  row closes with exit_reason=lifecycle-complete)"
last_executed: 2026-07-02
last_updated: 2026-07-21
code_refs:
  [
    agent-orchestrator/server/ci_status.py,
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/ci_reconcile.py,
  ]
execution:
  {
    owner: "the dispatched cicd one-shot worker (operator when the wall is escalated to main)",
    cadence: "per-wall (event-driven — a wall dispatch IS the execution; no scheduled run)",
    verifier:
      "python -m server.ci_status <repo> returns blocked=false for the walled repo after the fix (and the wall's
      escalation row closes with exit_reason=lifecycle-complete)",
    last_executed: 2026-07-02,
  }
---

# DevOps CI walls — recovery recipes (cicd role)

The **DevOps role = the `cicd` one-shot worker** (`unified-trading-pm/agents/cicd.md`): dispatched per wall via
`POST /api/escalate`, fixes the wall on the integration branch, exits. Wall routing: `merge_conflict` +
`stuck_promotion_pr` → the **conflict_resolver** prompt; `data_pipeline_failure` → its own prompt; everything else
(`ldr_qg_failure`, `sit_failure`, `main_ci_red`, `label_mismatch`) → the generic **cicd** prompt (`server/escalation.py`
`_prompt_template_for`; regression-tested in `tests/test_escalation.py`).

**Triage entry point — ALWAYS first**: from the agent-orchestrator repo root,

```bash
python -m server.ci_status <repo>            # → {repo, branch, latest_run, conclusion, qg_v2_state, blocked}
python -m server.ci_status <repo> --branch main
```

`blocked=true` covers BOTH a red v2 and a **never-reported** v2 (they need different recipes — below). This reuses the
reconcile loop's own read path, so its verdict matches the dashboard by construction.

> **The `CIReconcileLoop` only escalates a `failure` whose run tested the CURRENT branch HEAD (head-staleness gate,
> `server/ci_reconcile.py` `failing_run_is_current`, 2026-07-21).** LDR never runs server QG on push — the
> `quality-gates-v2` runs on `live-defi-rollout` are hourly `workflow_dispatch` runs — so a fix pushed to LDR leaves
> HEAD green-but-untested until the next dispatch, and the latest _completed_ run is still the OLD failure. The loop
> compares the failing run's `head_sha` to the current branch HEAD and **drops a stale/superseded failure** (logged, not
> escalated); a genuine red is caught the moment a run against the live head confirms it. So a just-fixed repo not
> escalating for a few minutes is EXPECTED, not a miss. (Prior false-red: the loop was head-blind and escalated
> already-fixed repos, spawning cicd workers that resolved `qg_v2_green` — wasted credits.)

> **This runbook cross-links, it does not duplicate.** The mechanics SSOT is
> [`codex/08-workflows/ci-cd-flow.md`](../08-workflows/ci-cd-flow.md); each recipe cites its section. If a recipe here
> ever disagrees with ci-cd-flow.md, ci-cd-flow.md wins — fix this doc.

## Recipe 1 — `quality-gates-v2` never-reported deadlock (MISSING required check)

**Symptom**: `/ci-status` shows `qg_v2_state: null` (or a promotion PR shows the required check MISSING, so the PR is
permanently BLOCKED). Classic trigger: a literal skip-ci marker (the bracketed form) anywhere in the head commit message
— including the BODY, even when merely describing it.

**Fix**:

```bash
gh workflow run quality-gates-v2.yml --repo IggyIkenna/<repo> --ref <PR_HEAD_BRANCH>
```

Then re-check `/ci-status <repo>` until `qg_v2_state: success`. The central watcher auto-recovers this class in-band
(`ci-failure-watcher --auto-recover`) — do NOT escalate to the operator for it; only act when dispatched at the wall or
when the watcher's auto-recovery itself failed.

**SSOT**: ci-cd-flow.md § "Central CI watcher — auto-recover vs escalate, and the RESOLVED bookend (codified
2026-06-09)" + § "CI Verification After Push" + § "Canonical required check name (post-Option-D, 2026-05-29)".

## Recipe 2 — behind-remote / rebase wall (push rejected, autostash conflict)

**Symptom**: an LDR push is rejected (behind remote), or a `git pull --rebase --autostash` hits a genuine same-file
conflict (quickmerge exits `QUICKMERGE_BLOCKED`).

**Fix**: `git pull --rebase --autostash` and keep the MERGED combination (quickmerge STAGE 0.4 auto-reconciles the
plain-behind case). On a genuine conflict: `rebase --abort`, recover per the autostash recipe, resolve by hand keeping
both sides' intent, re-run quickmerge. NEVER blind-overwrite, never force-push a shared branch, never `git stash drop`
foreign WIP.

**SSOT**: ci-cd-flow.md § "STAGE 0.4 Not-Behind Gate — behind-remote reconcile (multi-agent safety)".

## Recipe 3 — stuck LDR→main promotion (drain not landing)

**Symptom**: LDR is ahead of `main` by CONTENT but the standing promote PR isn't merging (v2 pending/red on the PR, or
the fleet PR stalled). Verify by CONTENT — `gh api repos/IggyIkenna/<repo>/compare/main...live-defi-rollout` — never by
squash-inflated `ahead_by`.

**Fix**: read the promote PR's v2 state first (`/ci-status <repo>` + the PR checks). v2 MISSING → Recipe 1 against the
PR head. v2 red → fix the root cause on LDR via quickmerge (the PR re-gates on the new head). PR conflicted → this is
the `stuck_promotion_pr` wall (conflict_resolver prompt): reconcile per Recipe 2, keeping the merged combination.
Promotion is `*/15` scheduled — do not hand-merge past a red gate; make the gate green instead.

**SSOT**: ci-cd-flow.md § "LDR-trunk decoupling — quickmerge lands on LDR; the drain promotes; hotfix is the only
break-glass (2026-06-10)" + § "LDR is the SSOT — clean-start force-sync + drift-tick (codified 2026-06-08)" + § "Branch
model — LDR trunk → staging → main".

## Recipe 4 — SIT / QG wall (cross-repo breaking gate red)

**Symptom**: the `sit_failure` wall — SIT (the LDR→main cross-repo breaking gate) or a server QG is red and blocks the
promotion path.

**Fix**: `gh run view --log-failed` on the failing run; determine whether the break is a REAL public-surface change
(breaking-detection is CONTENT-based — an AST diff; a 0.x-minor/docstring/refactor is NOT breaking) or a stale consumer
pin. Real break → fix forward in the consumer(s) via quickmerge, or route the producer through the staging toggle per
operator decision; false positive → fix the detector input (never relax the gate). Reproduce locally with the repo's
`bash scripts/quality-gates.sh` before pushing the fix.

**SSOT**: ci-cd-flow.md § "WS-L SIT-rehome — the LDR→main cross-repo breaking gate (full-coverage, 2026-06-28)" + §
"Breaking = public-surface change, NOT version phase (SIT scope; codified 2026-06-08)" + § "Local ↔ CI QG parity matrix
(the confidence model; codified 2026-06-08)".

## Escalation boundary (when the cicd worker stops)

Self-resolve everything above in-band. Escalate to `main` (→ operator) ONLY on: a human-only hard-stop (force-push main,
wallet keys, 1.0.0 graduation), an ambiguous product decision (which side of a conflict is intended), or a wall that
re-fires after a completed fix (loop guard). Record the wall id + evidence in the escalation row before exiting.
