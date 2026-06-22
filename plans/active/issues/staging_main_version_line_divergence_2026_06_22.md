---
title:
  staging→main promote PRs recur as version-line (pyproject) conflicts — dual-path version divergence; the LDR→main
  fallback drains them but they regenerate every cycle (structural cure = single-lineage version stamping)
created: 2026-06-22
author: harshkantariya [slot-4·laptop]
source:
  - 2026-06-22 triage-queue investigation (deployment-ui /repos "Stuck — triage queue")
  - instruments-service git history (merge-base 9c0d29b / main tip "Merge PR #511 from live-defi-rollout")
  - .github/workflows/staging-conflict-ldr-main-fallback.yml (the live Class-D mitigation)
  - .github/workflows/conflict-resolution-agent.yml (dup-env outage, fixed 2026-06-22)
  - .github/workflows/semver-agent.yml.tmpl (bump fires on push:[staging], not LDR)
locked_by: live-defi-rollout
parent_epic: infrastructure_master
estimate_class: design
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.2
priority: P2
status: active
---

## What I found

`staging→main` promote PRs across the fleet recur as CONFLICTING on a single deterministic thing: `pyproject.toml`'s
`version =` line. On 2026-06-22 the triage queue showed 6 such PRs; after they drained, **7 new ones appeared within the
hour** (UAC#412, instruments#514, fund-admin#219, greeks#238, unified-trading-api#429, e2e-testing#366, SIT#257). It is
a **treadmill** — drained reactively, regenerated every promote cycle.

### Root cause — dual-path version-line divergence (verified on instruments-service)

The version is **not** bumped on LDR. `semver-agent` fires on `push:[staging]` (the staging gate: "feature → staging →
bump → SIT → main") and commits `chore(release): bump version to X` **on staging**; the bump then backmerges down to LDR
(so all three branches end up carrying the bump commit). So versions are not missing — every branch gets them.

The conflict comes from `main` having **two inbound lineages** that both touch the `version =` line:

1. the gated `staging→main` release promote (carries the bumped version), and
2. the `LDR→main` drift/fallback merge (carries LDR content).

Traced on instruments-service: merge-base(staging,main) = `9c0d29b` (`version 0.25.0`); main's tip =
`6c91953 "Merge pull request #511 from live-defi-rollout"`. LDR carried the staging-bumped `0.27.0`, but that LDR→main
merge **kept main at `0.25.0`** (main must not jump to an un-released version outside the gated promote) — i.e. it
**re-resolved the `version =` line on main's side**. That re-resolution diverges main's version-line history from
staging's, so the next `staging→main` promote sees "both sides changed the version region" → textual conflict that never
self-heals. It is NOT a missing/misplaced bump; it is a hot line edited by two lineages into `main`.

## Why it matters

- Recurring triage churn: every promote cycle regenerates a batch of version-line conflict PRs across ~the whole fleet.
- Latency: the live mitigation runs hourly with a 30-min staleness floor, so a conflicted promote can sit "conflict
  wall" for up to ~90 min before draining — that is the "Stuck — triage queue" the operator sees.
- It masks real conflicts: a genuine (non-version) staging→main conflict is harder to spot in the noise.

## Live mitigations (already shipped — do NOT duplicate)

1. **`staging-conflict-ldr-main-fallback.yml` (Class D, hourly `47 * * * *`, STALE_MIN=30)** — the architecturally
   correct workaround: instead of resolving the version line, it **routes the promotion through an `LDR→main` PR**.
   Because LDR is the SSOT and carries BOTH back-merges (LDR ⊇ main AND LDR ⊇ staging), `LDR→main` is a CLEAN merge that
   lands the same+newer content; it verifies `main...LDR behind_by==0`, arms v2-gated auto-merge (`--merge`, non-admin),
   and closes the dammed `staging→main` PR as superseded. SAFETY: skips `breaking_pending` repos; never
   force/admin-merge.
2. **`conflict-resolution-agent.yml`** — the worker-escalation path for non-trivial conflicts. **Was a silent outage**
   2026-06-22: a duplicate `env:` block in the dispatch step (Max-plan-worker cutover regression) made the workflow
   invalid YAML → every `repository_dispatch` failed to start → escalated conflicts went nowhere. **FIXED**
   (`fix(cicd): conflict-resolution-agent — merge duplicate env: blocks`, PR #490 → main); dispatch verified working.

## A dedicated version-line auto-resolver was considered and REJECTED as redundant

A "promoter auto-resolves the version-line-only conflict (take higher semver + `uv lock`)" fix was proposed + approved
in principle, but on reading the existing workflows it duplicates the Class-D fallback (which already drains exactly
this conflict class, more cleanly, via LDR→main). Adding a second resolver would be a competing parallel path (violates
delete-deprecated / no-parallel-paths). **Decision: do not build it.** The fallback + the now-fixed agent cover the
reactive drain.

## Recommended decision

1. **Structural cure (this issue) — single-lineage version stamping.** Make the `version =` line have ONE history so it
   cannot diverge:
   - Bump on a single lineage consistent with LDR-is-SSOT (stamp once; staging + main are byte-identical projections),
     OR
   - keep the staging bump but make the `LDR→main` path **version-line-neutral** (never re-resolve `version =` on main —
     main only ever takes the version via the gated `staging→main`/`LDR→main` promote, never via a drift merge). Either
     removes the dual-lineage edit of the version line → no recurring conflict → the Class-D fallback becomes rarely
     needed. Touches `semver-agent` bump location + the backmerge + promote topology → needs a careful pre-audited plan
     (Citadel-grade: grep every consumer of the version-bump/backmerge flow before changing it).

2. **Cheap latency win (optional, decide separately):** tighten `staging-conflict-ldr-main-fallback` from hourly to
   `*/20`–`*/30` so the conflict-wall dwell time drops from ~90 min toward ~30 min. Tradeoff: more Actions runs; the
   comment deliberately set it hourly as "low-urgency". Operator call — does NOT fix recurrence, only latency.

## ⚠️ Paths to explore more (not yet verified)

- **Confirm the `LDR→main` drift merge is the ONLY second writer of `version =` on main** (vs e.g. a backmerge bot or a
  ci_status commit also touching it). Trace 2–3 more repos' main version-line history before designing the cure.
- **Whether bumping on LDR would prematurely leak un-released versions to main** via the LDR→main drift path — the cure
  must keep main's version advancing ONLY through the gated promote, even if the stamp lineage moves to LDR.
- **Interaction with the Mode-A/Mode-B findings** in `staging_to_main_promotion_starvation_2026_06_19.md` (the manifest
  version-bump desync + the squash-fallback semver-label loss) — all three touch the same version/promote machinery; the
  cure plan should reconcile them so fixes don't fight.
