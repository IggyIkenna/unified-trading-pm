---
doc_type: issue
title: "Promotion lag on service repos (2026-06-29) — trigger was a flaky QG dep-clone staling unified-trading-library's tier-0 ci_status; backlog since drained. Durable fix = harden the QG dep-clone (tracked P1)."
created: 2026-06-29
source:
  - .github/workflows/ldr-to-main-promote-fleet.yml
assigned_vm: NA
status: active
priority: P1
summary: "A flaky QG dep-clone (phantom-version / stale-deps fallback) left unified-trading-library's tier-0 ci_status stuck at FAILING while the code was actually green; the dep-order gate then held UTL's dependents, surfacing as a >60m promotion-lag alert on ~8 service repos. Cleared by re-greening UTL + draining the backlog. The durable fix is hardening the flaky QG dep-clone. NOTE: an earlier draft of this doc over-attributed the stall to LABEL-CHECK / SIT-stamp / unscheduled-promoter gates — those live in the STAGED WS-L promotion machinery which is intentionally inactive and is NOT the live blocker; corrected below."
nature: process
asset_group: cross-asset
stage: [meta]
repos:
  - unified-trading-pm
  - unified-trading-library
  - instruments-service
  - market-tick-data-service
  - market-data-processing-service
  - deployment-api
  - deployment-service
  - deployment-ui
  - agent-orchestrator
scope: [engineer, admin]
tags: [cicd, promotion, ldr-main, ci-status, flaky-qg, dep-clone]
related: []
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-29
---

> **Correction (2026-06-29):** the original version of this doc named the LDR→main fleet promoter's LABEL-CHECK gate
> (and a SIT-stamp deadlock) as the root cause. That was an over-reach. Those gates live in the **WS-L promotion
> machinery that is intentionally staged on `live-defi-rollout` and NOT active in production** (operator-confirmed).
> They are NOT what caused the lag. The actual cause is below. The staged-machinery observations are retained at the
> bottom as a forward note for whenever WS-L is activated — not as an active incident.

## Symptom

Slack `#ci-failures` (2026-06-29 11:11): **PROMOTION LAG > 60m — 9 branch-pairs across 8 repos un-propagated**
(`instruments-service`, `market-tick-data-service`, `deployment-service`, `market-data-processing-service`,
`deployment-api`, …). **PM was NOT in the list** (PM's own promoter is scheduled and healthy). Earlier, the deployment
cockpit showed `deployment-api` "held behind unified-trading-library (tier 1)".

## Root cause (verified) — flaky QG staled UTL's tier-0 ci_status

`unified-trading-library`'s `ci_status` was stuck at `FAILING` (`qg_red_reason=pytest`) in Firestore **while the code was
actually green** (branch CI green; content identical across LDR/staging/main). Because UTL is tier-0, the **dep-order
gate held its dependents** out of promotion (deployment-api etc.) — which is the lag the alert reported.

Per Ikenna's agent (the deeper cause, consistent with the observed symptom): the **QG dep-clone's phantom-version /
stale-deps fallback flaked UTL's quality gate**, which set the stale `FAILING`. This class can also trip the overnight
Dead-Man-Switch and re-stale a tier-0 `ci_status`.

It cleared when UTL's `quality-gates-v2` was manually re-run (2026-06-29 04:41 → `MAIN_GREEN` 04:48), after which the
dep-order gate released the dependents.

## Durable fix (the real one) — P1

**Harden the flaky QG dep-clone (phantom-version / stale-deps fallback).** This is the root that flaked UTL and will
keep recurring (Dead-Man-Switch trips, tier-0 ci_status re-staling) until fixed. Owned by Ikenna's CI/CD agent; tracked
as the standing P1 follow-up. No further LABEL-CHECK/SIT/promoter changes are required to resolve this incident.

## Resolution status

- UTL re-greened (04:48) → dep-order block cleared.
- Remaining backlog drained 2026-06-29 ~09:09–09:20 via manual `live-defi-rollout → main` PRs (each gated by a green
  `quality-gates-v2`, merge-commits to preserve semver): `deployment-api`, `deployment-service`,
  `market-tick-data-service`, `market-data-processing-service`, `agent-orchestrator`.
- `deployment-ui` and `instruments-service` manual PRs were **closed** (not needed; backlog drains normally now).
  Note for follow-up (separate, not this incident): `instruments-service` LDR↔main have **diverged** (main 1 commit not
  back-merged into LDR), i.e. a stuck/lagging backmerge worth a look.
- Lag-alert commit counts were `compare ahead_by` (squash-inflated) — overstated; the honest measure is last-main-commit
  dates + tree equality.

## Forward note — STAGED WS-L promotion machinery (NOT active; do not treat as a live bug)

Recorded only so it isn't re-discovered as a surprise when WS-L (`cicd_consolidated_remaining_2026_06_24.md`) is
activated. **Per operator: this machinery is intentionally inactive right now — do not action.**

- `ldr-to-main-promote-fleet.yml` is a Phase-0 canary: it has **0 scheduled runs** (its schedule would only fire from a
  default branch it isn't on) and runs only on manual `workflow_dispatch`. The live promoters are PM's
  `ldr-to-main-promote.yml` (scheduled, PM-only) and the existing staging→main path.
- IF that canary is ever made the live path, two things would need fixing first: (1) its LABEL-CHECK derives `EXPECTED`
  from only the newest commit subject vs `COMPUTED` from the whole-range max bump, so a range with an earlier `feat:`
  under a newer `fix:`/`chore:` false-blocks as "mislabeled"; (2) the SIT-rehome `Stamp SIT_VALIDATED + LDR tree`
  producer exists only on `live-defi-rollout`, not on system-integration-tests' default branch, so
  `sit_validated_tree` would never be written for `repository_dispatch` SIT runs. Both are consequences of the machinery
  being staged-not-deployed; neither is causing the current lag.

## Progress Log

- 2026-06-29: Filed (originally over-attributed to LABEL-CHECK/SIT-stamp). Corrected: real trigger = flaky QG dep-clone
  staling UTL's tier-0 ci_status (per Ikenna's agent); durable fix = harden that dep-clone (P1, owned by Ikenna's
  agent). Backlog drained via gated manual LDR→main merges; deployment-ui + instruments-service PRs closed; staged WS-L
  gates demoted to a forward note.
