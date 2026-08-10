---
doc_type: issue
title:
  "quality-gates.sh plan-discipline gate (A-deferred-no-banner) red on live-defi-rollout —
  codex_vs_repo_docs_ssot_audit_2026_06_01.md's in-doc DEFERRED wording trips the migration-banner rule, blocking every
  unrelated PM commit"
summary: >-
  `scripts/quality_gates/check_plan_discipline.py`'s rule (a) (A-deferred-no-banner) requires any plan body containing a
  `**DEFERRED**`/`DEFERRED — ` marker to also carry a `## Deferred work — migrated to:` banner naming a successor plan.
  `plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md` (locked_by: plan_reconciler agt-716973 since
  2026-08-10T05:24:47Z) picked up 3 `**DEFERRED — DELETE half NOT shipped**` annotations via commit `12fb7d698f`
  (2026-08-10, plan_reconciler infra-tranche run, see `plans/active/issues/plan_reconciler_findings_infra_2026_08_10.md`
  "Flips verified" #2) — a CORRECT un-checking of 3 todos that were falsely marked `[x]` while their DELETE half was
  still unshipped. The wording is accurate (work is genuinely not done yet) but semantically wrong for THIS check: the
  work was never migrated to another plan, it stays open as `- [ ]` todos in this same doc — so the "migrated to:"
  banner the checker demands doesn't actually apply, and there's no real successor plan to cite. Confirmed this is not
  something my own unrelated task introduced: reproduced byte-identical on a clean `git stash` of my own diff at the
  current `live-defi-rollout` HEAD, and confirmed live `quality-gates-v2` CI has been red on this repo since ~01:33 UTC
  today (2026-08-10) across several gates including this one (run 31358877638 and others). Declared repo-blocker
  `RB-5b82f02e` (kind `qg_red`) to unblock my own shipping without hand-editing a doc locked by a different agent's
  in-flight session.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, quality-gates, plan-discipline, false-positive, governance, ratchet]
related:
  [
    /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md,
    /plans/active/issues/plan_reconciler_findings_infra_2026_08_10.md,
    /plans/archive/governance_qg_automation_gaps_post_cutover_2026_05_12.md,
  ]
created: 2026-08-10
last_updated: "2026-08-10"
author: agent(slot-32)
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: infra
drift_direction: advance-code
source: "hit while shipping cross_cutting_satellite_ao_dispatch_batch6_2026_08_09.md todo 3 (slot-32, 2026-08-10)"
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    scripts/quality_gates/check_plan_discipline.py,
    /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md,
  ]
depends_on: []
locked_by:
---

# `check_plan_discipline.py` false-trigger on in-doc (not migrated) DEFERRED wording

## What I found

`quality-gates.sh`'s post-gate "Plan discipline check (ratchet mode)" (baseline 0) currently reports 1 violation:

```
[A-deferred-no-banner] unified-trading-pm/plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md: contains DEFERRED but no '## Deferred work — migrated to:' banner
```

The 3 triggering annotations (lines ~312, ~330, ~358 as of this writing) read `**DEFERRED — DELETE half NOT shipped**` —
introduced by `unified-trading-pm@12fb7d698f` (plan_reconciler agt-716973, 2026-08-10), which correctly un-checked 3
todos that were marked `[x]` despite their "DELETE half" genuinely not being shipped yet (verified live on disk by that
same run). This is legitimate, correct plan state — the checker's rule (a) just wasn't written to distinguish "genuinely
deferred, still an open todo in THIS SAME doc" from "deferred out of this plan entirely, migrated to a successor plan"
(the case the `## Deferred work — migrated to:` banner is actually meant for).

Live-verified this is repo-wide, not specific to my own diff: `git stash`-ed my own 2-file unrelated change
(`cross_cutting_satellite_ao_dispatch_batch6_2026_08_09.md` todo 3, workflow-template YAML lint pre-flight) and re-ran
`python3 scripts/quality_gates/check_plan_discipline.py --workspace-root <slot>` — byte-identical failure.
`gh run list --branch live-defi-rollout --workflow quality-gates-v2.yml` shows `failure` on every run since
~2026-08-10T01:33Z (multiple distinct gates failing across those runs, this one among them per run 31358877638's log).

## Why it matters

- Blocks every unrelated PM commit's local `quality-gates.sh` pass (the sentinel it writes gates `quickmerge --agent`),
  and blocks `quality-gates-v2` CI on `live-defi-rollout` — a fleet-wide "the PM repo's own gate is red" state.
- The offending doc is `locked_by: plan_reconciler (agt-716973) since 2026-08-10T05:24:47Z` — not safe for another agent
  to hand-edit mid-lock.
- Bumping `scripts/quality_gates/plan_discipline_baseline.yaml`'s `violation_count` 0→1 (the check's own suggested
  `--baseline-write` remedy) would "fix" the gate but silently ratchets UP a governance baseline that's supposed to only
  shrink — the wrong fix for what's really a rule-precision gap, not real debt to tolerate.

## Recommended decision

Two independent, non-conflicting fixes:

- [ ] [DOCS] P1. Reword `codex_vs_repo_docs_ssot_audit_2026_06_01.md`'s 3 `**DEFERRED — DELETE half NOT shipped**`
      annotations (lines ~312, ~330, ~358) to avoid the checker's DEFERRED-marker regex while keeping the same meaning —
      e.g. `**NOT YET SHIPPED — DELETE half**` or `**STILL OPEN — DELETE half not shipped**` — since the work is tracked
      as open `- [ ]` todos in this same doc, not migrated elsewhere. Wait for the doc's
      `locked_by: plan_reconciler (agt-716973)` lock to clear (or confirm it's stale via the standard liveness check)
      before editing. Repo: unified-trading-pm.
- [ ] [SCRIPT] P2. Harden `scripts/quality_gates/check_plan_discipline.py` rule (a) so a `DEFERRED — ` annotation
      immediately followed by (or co-located with) an open `- [ ]` checkbox in the SAME doc doesn't require a migration
      banner — only a `**DEFERRED**`/`DEFERRED — ` marker with NO corresponding open todo anywhere in the doc (i.e.
      genuinely deferred out of the plan, no in-doc tracking) should trip rule (a). Add a regression test fixture
      mirroring this exact doc's shape. Repo: unified-trading-pm.

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md`
- `/plans/archive/governance_qg_automation_gaps_post_cutover_2026_05_12.md` § Group A (rule origin)

## Progress Log

- **2026-08-10** (slot-32, agent(slot-32)): Filed while shipping an unrelated infra todo
  (`cross_cutting_satellite_ao_dispatch_batch6_2026_08_09.md` todo 3) — local `quality-gates.sh` red blocked the ship.
  Verified pre-existing + repo-wide (not my diff), declared repo-blocker `RB-5b82f02e` (kind `qg_red`) to resume once
  clear, did not hand-edit the locked source doc.
