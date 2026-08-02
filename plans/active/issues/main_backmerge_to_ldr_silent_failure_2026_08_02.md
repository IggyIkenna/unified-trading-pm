---
doc_type: issue
title: >-
  main-backmerge-to-ldr.yml has failed on every run since 2026-07-29T15:48:27Z (~3 days, 0/100 successes) — the
  main->live-defi-rollout bridge is down and its own conflict-escalation safety net never fires
summary: >
  Found as a side effect of the 2026-08-02 fleet version/tag-state census (`ci_satellite_ao_dispatch_batch1-020`).
  `workspace-manifest.json`'s `versions{}` cache appeared to lag the git-tag SSOT for 15/24 repos on `live-defi-rollout`
  — but `origin/main`'s copy of the same file is CURRENT (exact match to tags for the repos spot-checked), proving the
  writer (`update-repo-version.yml`, triggered by each repo's `semver-agent.yml` `version-bump` dispatch) is healthy.
  The actual break is `main-backmerge-to-ldr.yml`, the job that is supposed to project `main` back onto
  `live-defi-rollout` (the branch every AO slot worker's `.tabs/<N>/unified-trading-pm` clone tracks). Live-queried via
  `gh run list --workflow=main-backmerge-to-ldr.yml`: 0 successes in the most recent 100 runs (2026-07-30T18:38Z →
  2026-08-02T14:33Z), last success 2026-07-29T15:48:27Z. `origin/live-defi-rollout` is now 210 commits behind
  `origin/main` on `workspace-manifest.json` alone (221 behind in general). A representative failed run (id 30752363942,
  2026-08-02T14:33Z) exits with code 1 in ~0.6s and prints ZERO of the job's own `[backmerge:...]` decision lines
  (`noop`/`merged`/`conflict`/`error`) — it dies before the `git fetch origin main live-defi-rollout --quiet` step's
  surrounding logic can even set `DECISION`, so the job's own conflict-escalation path (open a visible PR +
  `escalate-to-orchestrator` dispatch) never triggers. This has been silently invisible: no PR opened, no escalation
  fired, and the only externally-visible signal is a plain GitHub Actions red X on a job most humans do not watch
  directly.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    ci-cd,
    backmerge,
    main-ldr-sync,
    silent-failure,
    versions-consolidator,
    workspace-manifest,
    git-tag,
    live-defi-rollout,
  ]
related:
  [
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
    /plans/archive/issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-08-02
parent_epic: infrastructure_master
priority: P1
source:
  ci_satellite_ao_dispatch_batch1-020 (Fleet version/tag-state census, slot 6, 2026-08-02) — found while re-deriving
  manifest `versions{}` vs git-tag drift; the census itself stayed read-only per its HARD CONSTRAINT, this finding is
  filed as required follow-up work per the Findings Closure rule (RULES.md § 4.5) rather than fixed inline (out of the
  census todo's scope, and a live CI workflow needs its own investigation budget).
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
last_updated: 2026-08-02
locked_by:
resolved_by:
depends_on: []
---

# `main-backmerge-to-ldr.yml` down since 2026-07-29 — the fleet's `main`→LDR sync bridge is silently broken

## What I found

The `main-backmerge-to-ldr.yml` workflow (PM repo) is supposed to fast-forward-or-merge `origin/main` into
`origin/live-defi-rollout` on a schedule, keeping LDR (the branch every AO worker slot clones and reads) current with
`main` (the projection every consolidator/reconciler/version-bump writer actually commits to). It has run and FAILED
continuously since **2026-07-29T15:48:27Z** (last confirmed success) — 0 successes across the most recent 100 runs as of
2026-08-02T14:33Z, spanning back to 2026-07-30T18:38Z. This is corroborated by
`ao_slot_capacity_policy_ci_scheduled_split_2026_07_29.md`, which independently observed the
`quality-gates-v2 → main-backmerge-to-ldr → Semver Agent` chain running clean on 2026-07-29 — so this is a genuine
regression introduced sometime after that, not a pre-existing condition.

**Impact confirmed live**: `origin/main`'s `workspace-manifest.json` has `unified-trading-library=0.70.0` and
`unified-trading-pm=1.2.697` — both exact matches to their highest git tags (i.e. `update-repo-version.yml`, the actual
`versions{}` writer, is healthy and current). `origin/live-defi-rollout`'s copy of the same file has
`unified-trading-library=0.65.0` and `unified-trading-pm=1.2.655` — 5 minor / 42 patch behind respectively. LDR is 210
commits behind main on `workspace-manifest.json` alone, 221 in general.

**The escalation safety net does not fire**: a representative failed run (`30752363942`, 2026-08-02T14:33:49Z,
`gh run view 30752363942 --log`) exits with code 1 after ~0.6 seconds and prints none of the job's own runtime decision
lines (no `[backmerge:noop]`, `[backmerge:merged]`, or the conflict-path's `[backmerge] opened conflict PR` /
`[backmerge] escalated conflict to orchestrator`) — meaning the failure happens before `DECISION` is ever set (almost
certainly inside or immediately after `git fetch origin main live-defi-rollout --quiet`, the first real command in the
step). Because the job's own `if [ "${DECISION}" = "conflict" ]` branch (which opens a visible PR and dispatches
`escalate-to-orchestrator`) is never reached, this specific failure mode is **completely silent** beyond the bare
workflow run's red X — no PR, no Slack page via that path, no orchestrator escalation. (Whether a `notify-slack.yml`
call elsewhere in the same workflow file fires on failure was not checked in this pass — see the fix todo below.)

## Why it matters

Every downstream consumer of `workspace-manifest.json` that reads from `live-defi-rollout` (every AO slot worker's PM
clone, this census included) has been seeing a stale, silently-diverging view of fleet version state, `ci_status`
projections, and any other `main`-only commit for ~3 days. This is the exact same failure SHAPE as the archived
`ldr_main_backmerge_silently_resurrects_reverted_commit_2026_07_29.md` incident that this same workflow file already has
defensive logic for (the `Promoted-From-LDR` trailer / silent-revert-loss safety net) — but that logic can only protect
against a MERGE producing wrong content; it does nothing when the job dies before reaching a merge attempt at all.

## Recommended decision

This is a live, bounded, worker-determinable investigation + fix — not an operator judgment call (the failure is a
concrete git/CI defect, not a design question) — so it is dispatched here rather than filed `NA`.

- [ ] [INFRA] P1. **Diagnose the exact failure point in `main-backmerge-to-ldr.yml`'s "Back-merge main into LDR" step**
      (likely `git fetch origin main live-defi-rollout --quiet`,
      `git ls-remote --exit-code --heads origin     live-defi-rollout`, or the `git config`/checkout steps immediately
      before it — the job dies in <1s with zero `[backmerge:...]` output, before `DECISION` is ever set). Pull a full
      `gh run view <id> --log` for a recent failed run and identify the first non-zero exit. Repo: unified-trading-pm.
- [ ] [INFRA] P1. **Fix the root cause** (auth/token scope regression, a changed default branch/ref assumption, a GH API
      rate-limit/outage during the fetch, or similar) and confirm 3 consecutive scheduled runs succeed
      (`decision=merged` or `decision=noop`) before considering this closed. Repo: unified-trading-pm.
- [ ] [INFRA] P2. **Close the silent-failure gap**: whatever the root cause turns out to be, ensure a failure at or
      before the `git fetch`/`git ls-remote` step ALSO reaches a visible alert (either wrap those early commands so a
      failure still sets `DECISION=error` and hits the existing `exit 1` + (if a Slack step exists on this workflow)
      notify path, or add a dedicated failure notifier) — the current design's only safety net is the conflict-PR path,
      which this incident proved is unreachable when the failure happens earlier than that. Repo: unified-trading-pm.
- [ ] [INFRA] P1. **Once fixed, drain the backlog**: confirm `live-defi-rollout` catches up to `origin/main` (verify
      `git rev-list --count origin/live-defi-rollout..origin/main` reaches 0, or explain any remaining gap), then
      re-verify the 2026-08-02 census's LAG table in
      `/plans/archive/issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md` — most of the 15 LAGGING
      repos should resolve to `sync` once the backmerge catches up (a handful may still genuinely lag if `main` itself
      hasn't been bumped for them). Repo: unified-trading-pm.
