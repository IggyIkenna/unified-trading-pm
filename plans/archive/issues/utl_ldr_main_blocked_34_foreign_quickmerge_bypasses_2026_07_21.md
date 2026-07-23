---
doc_type: issue
title: >-
  unified-trading-library LDR→main is blocked by 34 accumulated quickmerge bypasses (many agents, direct-pushed code) —
  the provenance gate correctly refuses; needs owning-agent reprovenance or an operator ruling
summary: >-
  The UTL LDR→main promote is blocked by the provenance gate: the promote PR carries 34 code commits that reached
  live-defi-rollout WITHOUT a Quickmerge trailer (direct pushes, not carve-outs) — substantial foreign features from
  many agents (DynamoDB deployment-registry backend, Firestore dual-write, ConsolidatorLivenessMonitor, event constants,
  maintenance-window CAS marker, lifecycle daemon, pipeline-e2e shard verify, the manifest perf refactor, and more).
  This is NOT a stuck pipeline and NOT one bad commit — it is a systemic fleet-discipline accumulation. The gate is
  working as designed and explicitly warns against hand-arming auto-merge to "unblock" it (that launders the bypass and
  moves the baseline past it). Because the promote carries every main..LDR commit, this also blocks the 18 downstream
  repos that depend on UTL (bottom-up drain). Resolving it means the owning agents re-ship their commits via quickmerge,
  or an operator deliberately reprovenances the accepted set — not an autonomous mass-bless.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, provenance, quickmerge, ldr-main, promotion, fleet-discipline]
related: [/plans/active/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md]
created: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: devops
drift_direction: advance-code
depends_on: []
source:
  [
    "surfaced 2026-07-21 while clearing the UTL PR #616/#617 promote block; the perf-test red (Tier-A) masked it until
    that was fixed",
  ]
locked_by:
locked_since:
resolved_by: unified-trading-library@5879def8
---

# UTL LDR→main blocked by 34 accumulated quickmerge bypasses

## What was measured (2026-07-21)

- The alert framed it as "2 changes", but
  `check_strict_quickmerge.py --range <last-promote-marker>..origin/live-defi-rollout` reports **34 code commits that
  bypassed quickmerge** (no `Quickmerge:` trailer, not carve-outs). The alert's smaller count is a narrower monitor
  window; the promote gate refuses on the full set.
- The provenance gate has already fired on promote PR **#617**:
  `⛔ Provenance gate (LDR→main fleet bot) — this promote carries code that bypassed quickmerge … Auto-merge NOT armed.`
- The gate's own message:
  **`Do NOT hand-arm auto-merge to "unblock" this — that promotes the bypassed code AND moves the provenance baseline past it, so the violation is laundered and never flagged again (happened 2026-07-16).`**
- The 34 are foreign, substantial, and span many subsystems — a sample: `c3baaa29` DynamoDB deployment-registry backend,
  `bf56debe` Firestore deployment-registry dual-write, `fcb792d1` ConsolidatorLivenessMonitor PAUSED reason, `690a391a`
  distributed maintenance-window CAS marker, `04c72ef5` HeartbeatDaemon SIGTERM archive, `69ff7fee` pipeline-e2e shard
  verify, `80d2497e` manifest perf refactor. These are real features by multiple agents, not noise.

## Why this is not an autonomous fix

`reprovenance_bypass.sh <sha> --push` is the sanctioned, auditable remedy (each blessing names the sha) — but blessing
**34 foreign feature commits** at once asserts that all of them are correct and promote-ready, which the acting agent
cannot verify. It also normalizes a fleet-wide lapse (many agents direct-pushing UTL code) rather than correcting it.
The gate exists precisely to force this to a human decision.

## Not the perf-test red (that IS fixed)

The active Tier-A blocker until 2026-07-21 was `ci_status=FAILING` from a flaky perf-guard test, now fixed
(`unified-trading-library@9081e51c`, LDR v2 green). The provenance gate is the remaining blocker, only visible once
Tier-A cleared. UTL's own deps are on main (`✅ READY: unified-trading-library — all deps on main`).

## Options (operator / owning-agent decision)

- [x] [DEVOPS] P1. **RESOLVED via operator-authorized reprovenance sweep** (utl@5879def8): one provenanced empty commit
      re-provenances all 34 (dep-alignment PASSED, LDR green), strict-quickmerge now reports zero bypasses. Alternative
      below kept for the record.
- [ ] [DEVOPS] P1. **Owning agents re-ship their bypassed commits via quickmerge** — the correct fix. Each agent knows
      their code is intended; a content-identical `quickmerge --agent --files <paths>` re-provenances it properly. Best
      if the bypass commits are the LDR tip; mid-history ones use `reprovenance_bypass.sh <sha> --push`.
- [ ] [DEVOPS] P1. **OR an operator deliberately reprovenances the accepted set** after confirming the 34 are all
      intended — a bulk `reprovenance_bypass.sh` sweep, done knowingly, with the list reviewed. This accepts the
      accumulated debt in one auditable step.
- [ ] [DEVOPS] P2. **Prevent recurrence** — the root cause is agents direct-pushing UTL code instead of quickmerge (34
      over one marker window). Strengthen the strict-quickmerge pre-push guard's reach / add a louder per-commit nudge,
      and/or a periodic bypass-count alert so this never silently accumulates to 34 again.

## Progress Log

- **2026-07-21** — Filed while clearing the UTL promote block. Fixed the two things that WERE mine to fix (the flaky
  perf-guard red at Tier-A; the plan-discipline ratchet on PM; the dead-claim UAC WIP blocking fleet quickmerge). The
  provenance block was flagged rather than autonomously blessed, per the gate's own anti-laundering warning.
- **2026-07-21 (operator ruling: "please do clear")** — RESOLVED. Reprovenanced all 34 as one operator-authorized,
  auditable sweep (utl@5879def8, naming each sha; dep-alignment PASSED; LDR v2 green). strict-quickmerge reports zero
  bypasses. UTL LDR→main now clears both gates and drains the 18 downstream repos on the next promote tick. The P2
  recurrence-prevention todo remains open.
