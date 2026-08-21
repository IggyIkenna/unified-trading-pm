---
doc_type: issue
title:
  agent-orchestrator's workflow-template-parity gate drifted + blocked EVERY unified-trading-pm commit 3 times within ~1
  hour during the Phase-7 self-hosted-runner rollout — multiple slots independently pushing direct per-repo commits to
  the same workflow files, racing each other and the SSOT rollout
summary: >-
  While shipping unrelated plan-doc updates, the `workflow-template-parity` QG (fleet-shared, blocks every commit to
  unified-trading-pm) failed on `agent-orchestrator`'s workflow copies THREE separate times between ~19:29 and ~20:09
  UTC on 2026-07-27. Each time the sanctioned remedy (`rollout-workflow-templates.sh --repo agent-orchestrator`) fixed
  it, but it re-drifted again within ~10-30 minutes. Root cause (confirmed via `git log --oneline -15 --
  .github/workflows/main-backmerge-to-ldr.yml` in agent-orchestrator): during this window, at least 2 DIFFERENT actors
  landed their OWN direct commits to agent-orchestrator's per-repo workflow copies as part of the active "Phase 7 — flip
  glue workflows to self-hosted runners" rollout (a canary commit `f570c16` + another slot's own `91dfaa7 fix(ci): sync
  backmerge/version-bump workflow copies to self-hosted glue-runner template`), interleaved with the PM-side SSOT
  template itself changing (`137b3d7e6`) and a slot's baseline commit (`b6c4d0fb1 docs(ci): baseline the Phase-7
  canary's expected workflow-template drift`). Multiple slots were touching the SAME set of files during an in-flight
  migration without a single owner driving it to a stable end-state, so each fix landed against a moving target and got
  stepped on again before it could settle.
status: open
nature: issue
asset_group:
  [ci] # corrected 2026-08-02 (/ag-closeout-audit cross-cutting, operator-ruled) -- was [cross-cutting]; content is
  # workflow-template-parity QG drift during the Phase-7 self-hosted-runner rollout, squarely ci-tranche (CI/CD
  # pipeline mechanics), not generic cross-AG content.
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci-cd, workflow-templates, drift, phase-7, self-hosted-runners, coordination]
related: [/codex/08-workflows/ci-cd-flow.md, /plans/active/ci_consolidated_closeout_2026_07_25.md]
created: 2026-07-27
author: unknown
priority: P2
parent_epic: ci_master
source: "slot-3, infra, discovered while shipping unrelated plan-doc updates, 2026-07-27"
execution_scope: local-only
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    scripts/workflow-templates/rollout-workflow-templates.sh,
    scripts/quality_gates/detect_template_drift.py,
    /plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md,
  ]
---

# workflow-template-parity drifted + blocked all PM commits 3x in ~1hr during Phase-7 rollout

## What I found

Shipping unrelated `docs(plans):` commits to `unified-trading-pm` (todo-10 benchmark findings, unrelated to CI/CD), the
fleet-shared `workflow-template-parity` QG check failed 3 separate times within roughly one hour (2026-07-27,
~19:29-20:09 UTC), each time citing `agent-orchestrator`'s per-repo workflow copies as newly drifted vs. the PM SSOT
(`scripts/workflow-templates/`):

1. **~19:29 UTC**: 8 files drifted (`main-backmerge-to-ldr.yml`, `major-bump-issue-handler.yml`,
   `request-major-bump.yml`, `staging-backmerge-to-ldr.yml`, `update-dependency-version.yml`,
   `version-registry-notify.yml`, `quality-gates-v2.yml`, `semver-agent.yml`). Fixed via
   `rollout-workflow-templates.sh --repo agent-orchestrator` → `agent-orchestrator@9b24a9f`.
2. **~19:40 UTC** (~11 min later): the SAME 8 files drifted again. Fixed again → `agent-orchestrator@55ddf82`.
3. **~20:09 UTC** (~29 min later): 5 of the same files drifted a third time. Fixed again → `agent-orchestrator@3721ef4`.

**Root cause (confirmed via `git log --oneline -15 -- .github/workflows/main-backmerge-to-ldr.yml` in
agent-orchestrator, cross-referenced with commit timestamps)**: this was NOT one stale fix going stale once — it was
multiple actors independently landing DIRECT commits to agent-orchestrator's per-repo workflow copies during an active,
uncoordinated in-flight migration ("Phase 7 — flip fleet-template glue workflows to self-hosted runners"):

- `f570c16 feat(ci): Phase 7 canary — flip 8 glue workflows to self-hosted runners` — a canary commit directly to
  agent-orchestrator's own copies, landing between my 1st and 2nd fix.
- `91dfaa7 fix(ci): sync backmerge/version-bump workflow copies to self-hosted glue-runner template (workflow-template-parity)`
  — ANOTHER slot's own independent fix attempt for the same drift, landing around the same window.
- On the PM side: `137b3d7e6 feat(ci): Phase 7 — flip 7 fleet-template glue workflows to self-hosted runners` (the SSOT
  template change itself) and `b6c4d0fb1 docs(ci): baseline the Phase-7 canary's expected workflow-template drift` (a
  baseline commit acknowledging SOME expected drift, but not covering agent-orchestrator's specific files that kept
  re-drifting).

Each of my 3 fixes was landing against a target that another actor was simultaneously moving —
`rollout-workflow- templates.sh --repo agent-orchestrator` re-syncs from whatever the SSOT looks like AT THAT MOMENT,
but if the SSOT or agent-orchestrator's own copies change again seconds/minutes later (from a different slot's
concurrent commit, or the canary's own direct push), the fix doesn't hold. **Confirmed stable as of my 3rd fix**
(`agent-orchestrator@3721ef4`, `detect_template_drift.py --workflows` → `NEW drift (blocking): 0`), but there is no
guarantee this doesn't recur if the Phase-7 rollout is still in flight when another slot next touches these files.

## Why it matters

- **This QG check is fleet-shared** — a drift in ONE repo (agent-orchestrator) blocks EVERY commit to
  `unified-trading-pm`, regardless of what that commit actually touches. During this ~1hr window, at least my own
  session burned 3 separate full-QG re-run cycles (each several minutes) purely to unblock unrelated plan-doc ships —
  pure overhead with zero relation to the actual work. A genuinely uncoordinated multi-slot migration on a
  shared-blocking-gate file set is a real cost multiplier: N slots independently "fixing" the same drift means N times
  the wasted QG cycles, and the fix doesn't converge until every actor stops touching the files.
- **No single owner was visibly driving the Phase-7 rollout to a stable end-state** during this window — from my vantage
  point (one slot reacting to gate failures), I could not tell whether the rollout was done, still landing canaries, or
  had another slot mid-fix at the same time I was. A `docs(ci):` baseline commit (`b6c4d0fb1`) suggests SOME awareness
  the rollout causes expected drift, but it didn't prevent the 2nd/3rd recurrence.
- Not a data-correctness or trading-critical-path issue, but a genuine cross-repo coordination gap that cost real
  wall-clock time across at least 2 slots (mine + whoever landed `91dfaa7`) during an in-flight migration.

## Recommended fix path

- [x] ✅ [DATA] P2. **Confirmed via direct measurement (2026-07-28), not an operator ask — this was a checkable fact.**
      Ran `detect_template_drift.py --workflows --json` fleet-wide: `new_drift` = 1 entry
      (`market-tick-data-service/staging-lock-check.yml`, unrelated to Phase 7/agent-orchestrator), `current_drift` = 7
      entries including `agent-orchestrator/update-dependency-version.yml` — but that entry is already present in the
      accepted `workflow_template_drift_baseline.json` (140 entries), not fresh drift. Traced the baseline's own
      history: commit `b6c4d0fb1` ("docs(ci): baseline the Phase-7 canary's expected workflow-template drift",
      2026-07-27 20:17:49+0100) explicitly grandfathers this as intentional, documented, TEMPORARY canary-phase state —
      its own message confirms agent-orchestrator "got the real rollout" (the 7 files this issue's 3 drift incidents
      were about) while "the other 23 repos' copies are deliberately NOT re-rolled-out yet (no self-hosted runner
      registered for them...)." **Verdict: the Phase 7 rollout for agent-orchestrator itself is COMPLETE and STABLE** (0
      new drift measured today against its own files) — the earlier "still in flight" uncertainty is resolved. The wider
      "Phase 7 fan-out" to the remaining 23 repos is a SEPARATE, deliberately-deferred future work item (each repo needs
      its own self-hosted runner registered first), not an uncoordinated in-flight race — tracked by the ratchet
      baseline itself, which shrinks as each repo is rolled out. No single-owner assignment is needed for the
      already-stable agent-orchestrator canary; a future owner is only relevant if/when the fan-out to the other 23
      repos is scheduled.
- [ ] [SCRIPT] P3. Consider whether `rollout-workflow-templates.sh` (or a wrapping CI job) could roll out to EVERY repo
      in one atomic pass when the SSOT changes, rather than relying on individual slots to notice + fix per-repo drift
      reactively when their own unrelated commit trips the gate. This would remove the "N slots independently re-fixing
      the same drift" failure mode entirely. **NOTE added 2026-08-16 (plan_reconciler Phase -1):** the blast radius this
      question was written against has shrunk substantially since — `plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`
      (status: active, last_updated 2026-08-14) is 10 of 11 todos done, converting most of the fleet's byte-identical,
      full-copy-propagated workflow files into thin `workflow_call` stubs hosted once in `unified-trading-ci` — the
      exact class of file whose N-repos-drift-simultaneously failure mode motivated this question. With most of that
      content now centrally hosted and callers thin, re-assess whether this P3 item is still worth pursuing at its
      original fleet-wide-rollout scope, or should close/downgrade — not a mechanical fix, left open for that
      reassessment rather than force-closed.
- [ ] [DATA] P3. If another workflow-template-parity failure recurs on `agent-orchestrator` (or any other repo) during a
      future rollout, check `git log --oneline -15 -- .github/workflows/<file>.yml` in the affected repo FIRST to
      distinguish "stale SSOT drift" (one clean fix suffices) from "an active multi-actor migration is still landing
      direct commits" (a fix will not hold; escalate per this doc rather than blind-retrying).

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **na-eligibility-audit 2026-08-01**: KEEP-NA, valid -- Full audit rationale: Both remaining open items are genuinely
  judgment-gated, not bounded-outcome work a worker could execute unilaterally. Item 1 ("Consider whether
  rollout-workflow-templates.sh ... could roll out to EVERY repo in one atomic pass") is an open-ended design question
  -- whether to build a new atomic fleet-...
- **na-eligibility-audit 2026-08-02**: **CONFIRMS KEEP-NA, valid — unchanged** (tranche `ci`, autonomous). This doc
  entered the `ci` tranche only today: the sole post-marker commit is the 2026-08-02 `/ag-closeout-audit cross-cutting`
  operator-ruled retag `asset_group: [cross-cutting]` → `[ci]`. No content moved. Re-read end-to-end and both open items
  re-tested against the bounded-outcome bar: the `[SCRIPT] P3` is an open-ended design question by its own first word
  ("**Consider whether** … could roll out to EVERY repo in one atomic pass"), with no decided target mechanism; the
  `[DATA] P3` is a conditional runbook step that is not startable at all until a future drift recurrence triggers it
  ("**If** another workflow-template-parity failure recurs … check `git log` FIRST"). Neither outcome is determinable by
  a worker today. Correctly NA.
- **context-scout 2026-08-03**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — open-ended design questions, conditional runbook, prior verdicts
stand

- **2026-08-06 (na-eligibility-auditor, tradfi tranche — this doc's P3 runbook fired as designed)**: a docs-only
  `docs(plans):` flip on unified-trading-pm tripped `workflow-template-parity` with **6 NEW drifted copies** in sibling
  repos — `batch-live-reconciliation-service`, `deployment-ui`, `e2e-testing`, `execution-service`, `greeks-service`,
  `strategy-service`, all `image-build-gate.yml`. Applied this doc's own P3 first-step:
  `git log --format='%h %cs %s' -2 -- .github/workflows/image-build-gate.yml` in each affected repo → every last-touch
  is a 2026-08-06
  `chore(ci): point at unified-trading-ci instead of unified-trading-pm for reusable QG + image-build workflows` — the
  **active multi-actor migration class, not stale SSOT drift** (per this doc's taxonomy, "a fix will not hold; escalate
  rather than blind-retrying" — and a re-rollout or baseline re-write would fight the migration owner mid-flight). The
  2026-07-27 phase-7 note's "wide fan-out to remaining repos is a separate deliberately-deferred future item, tracked by
  the ratchet baseline" now has a concrete instance: the unified-trading-ci re-point is landing repo-by-repo via direct
  commits today, and each repo's copy will read as NEW drift until the rollout owner re-baselines
  (`detect_template_drift.py --baseline-write` after rollout completion per its own header). Workaround used this
  recurrence: pure `docs(plans):`/plan-flip commits are the CLAUDE.md carve-out #2 (direct push, no quickmerge) — the
  pre-push `check-strict-quickmerge` hook accepts `plans/**`-only commits, so the docs flip shipped directly without
  touching any workflow copy. Next recurrence with docs-only content: same carve-out. With CODE content: must wait for
  the rollout owner to re-baseline or coordinate per this doc.

**na-eligibility-audit 2026-08-07** (tranche `ci`, autonomous, `agt-cbbd1f`): KEEP-NA, valid — re-verified both open
items. Item 1 is an open-ended design question ("consider whether... could roll out in one atomic pass"), no decided
mechanism. Item 2 is a standing conditional runbook, not a pending action — confirmed still being actively exercised
live (a 2026-08-06 tradfi-tranche auditor hit the same drift gate, followed this doc's own step-3 diagnostic, and
correctly used the docs-only carve-out rather than fixing code). No `assigned_vm` change.

- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:699f5e63a376d900]: KEEP-NA,
valid — confirms the 2026-08-07 verdict, unchanged. Item 1 remains an open-ended design question with no decided
mechanism; item 2 remains a standing conditional runbook (last actually exercised 2026-08-06 by a tradfi-tranche
auditor, per its own documented usage). No `assigned_vm` change.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:79fe015bf644fd6a]: KEEP-NA,
valid — Full read confirms 2 open items, with 6 independent prior audit passes (2026-08-01, 2026-08-02, 2026-08-06 x2,
2026-08-07, 2026-08-09) all agreeing KEEP-NA, most recently yesterday. Item 1 (P3 SCRIPT, atomic fleet-wide rollout
mechanism): an open-ended design question by its own first word ('Consider whether rollout-workflow-templates.sh...
could roll out to EVERY repo in one atomic pass'), no decided target mechanism -- correctly not bounded. Item 2 (P3
DATA, git-log-first diagnostic runbook for future recurrences): a standing conditional procedure, not itself a startable
one-off task -- and it is demonstrably still live and correct: the 2026-08-06 Progress Log entry documents a DIFFERENT
(tradfi-tranche) auditor actually following this exact step during a real recurrence of the underlying
stale-drift-vs-active-migration pattern, and correctly used the doc's own prescribed carve-out.

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).

**na-eligibility-audit 2026-08-18** (ci tranche): KEEP-NA, valid -- unchanged, 7th consecutive confirmation. NOT
re-litigating: `plan_reconciler_findings_ci_2026_08_16.md` already annotated (not force-closed) that the design
question's blast radius has shrunk since `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` went
10/11 done (independently re-checked today -- still 10/11, todo 10 remains genuinely undecided), and
`ag_closeout_audit_ci_parked_2026_08_16.md` already filed the operator-ruling ask for this doc as its own Todos item 2
rather than let it be reconfirmed a 7th time with no decision. Not duplicating that escalation here -- see that doc
for the standing ask.
- **context-scout 2026-08-20**: refreshed context_scope (4 entries)

**na-eligibility-audit 2026-08-21** (ci tranche wave 2): KEEP-NA, valid — unchanged, 8th consecutive confirmation.
Item 1 (P3 SCRIPT, atomic fleet-wide rollout mechanism) remains an open-ended design question by its own first word
("Consider whether..."), no decided target mechanism. Item 2 (P3 DATA, git-log-first diagnostic runbook for future
recurrences) remains a standing conditional procedure, not itself a startable one-off task, and stays demonstrably
live/correct (last exercised by a real recurrence 2026-08-06). `ag_closeout_audit_ci_parked_2026_08_16.md` already
filed the operator-ruling ask for item 1 rather than re-litigating it here again. No `assigned_vm` change.
