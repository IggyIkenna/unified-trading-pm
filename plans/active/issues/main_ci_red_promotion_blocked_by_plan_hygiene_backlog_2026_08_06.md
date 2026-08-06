---
doc_type: issue
title:
  "main_ci_red for unified-trading-pm: LDR→main promote PR blocked by a large plan-hygiene backlog on live-defi-rollout
  (112 archive candidates / 77 AG-closeout orphans / NA corpus over baseline) — operator decision requested"
summary: >-
  Escalation agt-80c470 (wall_type=main_ci_red, unified-trading-pm, 2026-08-06). main's quality-gates-v2 is red on 3
  lint-codex corpus checks (finalize-plan coverage, codex doc freshness, agent-rules size cap) — all 3 already FIXED on
  live-defi-rollout. But the LDR→main promote PR #2388 is blocked because the plan-hygiene hard gate
  (run_hygiene_sweep.sh --ci, folded into quality-gates-v2) fails on LDR content: 112 archive candidates (baseline 0),
  77 AG-closeout orphans (baseline 69), NA corpus over (391 vs 384 docs / 1364 vs 1347 todos). 104/112 candidates also
  exist on main. Neither main_ci_red boot remedy applies (re-firing v2 reproduces the failure; re-rolling main's stale
  quality-gates-v2.yml to the unified-trading-ci ref won't fix corpus-state checks). Only path to green main = clear the
  plan-hygiene backlog on LDR so the promote PR goes green. Operator decision requested via /blocked BLK-46fa5703
  (options A: clear backlog on LDR now, B: reclassify as plan_health / plan_reconciler, C: promotion intentionally
  paused; rec A). ALSO: this session's /done 400'd ("no active agent owns its session") — AgentRow agt-80c470 absent
  from the DB, a recurrence of cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29 (server-side fix
  agent-orchestrator@81f54a8 already shipped; see Progress Log).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci, plan-hygiene, promotion, main_ci_red, escalation, operator-decision, recurrence]
related:
  [
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md,
    /plans/archive/issues/cicd_escalation_heartbeat_steals_slot_before_done_no_agentrow_2026_07_28.md,
  ]
created: "2026-08-06"
parent_epic: infrastructure_master
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
assigned_vm: NA
execution_scope: local-only
sequential: true
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
source: "slot 2, cicd escalation agt-80c470 (wall_type=main_ci_red, repo=unified-trading-pm, 2026-08-06)"
context_scope:
  [
    unified-trading-pm/.github/workflows/quality-gates-v2.yml,
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/scripts/plan-hygiene/check_archive_candidates.sh,
    unified-trading-pm/scripts/plan-hygiene/check_ag_closeout_linkage.py,
    unified-trading-pm/scripts/plan-hygiene/check_na_corpus_ratchet.py,
    agent-orchestrator/server/ci_reconcile.py,
  ]
---

# main_ci_red: promote PR blocked by plan-hygiene backlog on LDR

## What I found (verified 2026-08-06, escalation agt-80c470)

1. **main is RED.** Last `quality-gates-v2` push run on main (head `7b5390649`, "fix: promote-provenance marker must
   verify true ancestry", 14:24Z) failed the lint-codex slice on 3 post-gate corpus checks:
   - Finalize-plan coverage regression (a new `assigned_vm: planning` plan shipped with no gated finalize plan)
   - Codex doc freshness regression
   - Agent-rules size cap violation (CLAUDE.md / SUB_AGENT_MANDATORY_RULES.md)
2. **Those 3 are already FIXED on live-defi-rollout** — they PASS on the promote PR runs (main ⊂ LDR; the corpus fixes
   are in the LDR-not-on-main commits).
3. **The LDR→main promote PR #2388 is genuinely BLOCKED**, not re-fireable. Its `quality-gates-v2` run fails the
   plan-hygiene hard gate (`run_hygiene_sweep.sh --ci`, a step in the checks leg) on LDR content:
   - **Archive candidates: 112** (baseline `candidate_count: 0` — must archive ALL to pass; a shrinking ratchet that
     refuses to raise)
   - **AG-closeout orphans: 77** (baseline 69)
   - **NA corpus: 391 docs vs 384 baseline, 1364 open todos vs 1347 baseline**
   - 104/112 archive candidates and 66/77 orphans also exist on main's own tree (main never surfaced them because its
     recent pushes were `[skip ci]` or failed the lint-codex slice before the plan-hygiene gate step ran).
4. **Promotion has been blocked on this backlog since ~2026-08-05 15:00Z** (last successful promote merge = PR #2276,
   14:18Z 08-05). Every promote-PR / LDR workflow_dispatch run since then is a FAILURE (0 successes across the last 300+
   QG runs for those triggers).
5. **The `ldr-to-main-promote.yml` bot keeps opening fresh per-SHA promote PRs** as LDR moves; each fails the same
   plan-hygiene gate. It is NOT wedged — it is correctly blocked on a red required check.

## Why neither boot remedy applies

- **(A) re-fire v2 on the PR head** → reproduces the same plan-hygiene failures.
- **(B) re-roll main's stale workflow** (main's `quality-gates-v2.yml` still calls the LOCAL
  `./.github/workflows/python-quality-gates-v2.yml`; LDR re-pointed to `IggyIkenna/unified-trading-ci/...@main` as part
  of the shared-CI-repo extraction) → doesn't change corpus-state checks; main would still fail them.

**Only path to green main = clear the plan-hygiene backlog on LDR so the promote PR goes green.** That is multi-hour,
judgment-heavy plan_health-class work (112 archival rituals + orphan links + NA shrink), so an operator decision was
requested rather than autonomously starting it.

## Operator decision (posted as /blocked BLK-46fa5703, 2026-08-06 ~14:40Z)

- **A (recommended):** a worker clears the full plan-hygiene backlog on LDR now — archive the 112 done-but-unarchived
  docs, link the AG-closeout orphans to their closeout family, shrink the NA corpus below baseline. Unblocks promotion
  permanently; main goes green after the promote PR merges.
- **B:** reclassify as plan_health / route to the plan_reconciler; main stays red until the backlog is cleared.
- **C:** operator is already handling it / wants promotion paused.

## Recommended decision

- [ ] [OPERATOR] P1. Decide BLK-46fa5703 (A/B/C). If A: dispatch a worker to clear the plan-hygiene backlog on
      live-defi-rollout (archive 112 done docs, link 77 AG-closeout orphans, shrink NA corpus), then re-fire the
      LDR→main promote PR. Evidence: /blocked BLK-46fa5703 + this doc.

## Progress Log

- **2026-08-06 (slot 2, cicd escalation agt-80c470):** Full diagnosis above. Posted /blocked BLK-46fa5703; no answer
  within the 2-min bounded wait, so the escalation stopped per the cicd one-shot contract. `/done` for this session
  400'd with `"one_shot_complete on slot 2 but no active agent owns its session 'orch-slot-2'"` —
  `GET /api/agents/agt-80c470` returns all-null (AgentRow absent). This is a RECURRENCE of
  cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29; the server-side fix (agent-orchestrator@81f54a8:
  heuristic reapers stamp `reaped-stale` instead of `lifecycle-complete`) was already shipped but does not repair
  already-broken rows. Rechecked slot 2 repos clean (ahead=0 on live-defi-rollout).
