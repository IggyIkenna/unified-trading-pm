---
doc_type: issue
title:
  "digest-drift-sweep.yml never dispatches (cross-repo Contents API authed with repo-scoped GITHUB_TOKEN) → 11 service
  repos pinned to a stale UTL base-image digest → EVERY service Cloud Build is RED on setuptools PYSEC-2026-3447"
summary: >-
  The PM workflow .github/workflows/digest-drift-sweep.yml (cron 0 */6 * * *) is meant to bump each service's Dockerfile
  BASE_IMAGE_DIGEST pin when the UTL base image republishes. It has NEVER dispatched: it authenticates cross-repo GitHub
  Contents-API reads with secrets.GITHUB_TOKEN (the ambient, repo-scoped token), which cannot read another repo's
  contents, so every one of its 16 IMAGE_REPOS logs "Dockerfile not found — skipping" (verified across 4 runs
  07-14→07-18: No ARG found 16 / Dispatched 0 every time). Consequence: 11 service repos are still pinned to UTL base
  digest sha256:b7e391f8… (uploaded 2026-07-13T18:44 UTC, BEFORE the fleet pip-audit fix landed 07-14), so their
  in-image quality-gates.sh runs a stale qg-common.sh whose pip-audit ignore-list lacks PYSEC-2026-3447 → the in-image
  QG (STEP 5 codex compliance) fails on "setuptools 82.0.1: PYSEC-2026-3447" → the Cloud Build push step never runs →
  the service cannot deploy a fresh image. This blocks the deploy leg of ALL affected services (found while trying to
  redeploy ml-service for bucket_fold_ml Phase D). The fresh UTL base :latest sha256:76a15429… (v0.55.0, 07-18T10:36)
  correctly carries the ignore (grep count 2). ml-service was unblocked with a manual pin bump (this session); the other
  10 repos + the broken sweep remain.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-trading-pm,
    ml-service,
    execution-service,
    strategy-service,
    deployment-service,
    agent-orchestrator,
    alerting-service,
    client-reporting-api,
    fund-administration-service,
    greeks-service,
    market-data-processing-service,
    trading-agent-service,
  ]
scope: [engineer, admin]
tags: [ci, cloudbuild, base-image, digest, pip-audit, fleet, p1, deploy-blocker]
related: [bucket_fold_ml_2026_07_17.md]
created: 2026-07-18
parent_epic: infrastructure_master
priority: P1
assigned_vm:
resolved_by:
locked_by:
source:
  "Found 2026-07-18 during /autonomous execution of bucket_fold_ml_2026_07_17 Phase D (redeploy ml-service + cite
  cloudbuild=SUCCESS). The redeploy was blocked by a red ml-service Cloud Build; root-cause investigation (read-only
  sub-agent) traced it to this fleet-wide, silently-broken digest-drift-sweep automation."
---

# digest-drift-sweep.yml broken → 11 service repos stale-pinned → all service Cloud Builds RED (PYSEC-2026-3447)

> **P1 fleet deploy-blocker. NOT a bucket-fold bug** — surfaced because bucket_fold_ml Phase D needs a green ml-service
> build. ml-service was unblocked in-session (manual pin bump `b7e391f8`→`76a15429`, ml-service@5d05c4c); this doc
> tracks the root cause + the 10 other affected repos so the operator can decide on the fleet fix.

## Root cause (evidence)

1. **The QG base scripts are baked into the UTL base Docker image**, not vendored per-repo. UTL `cloudbuild.yaml`
   `clone-pm-scripts` step (`:161-177`) does
   `git clone --depth=1 --branch live-defi-rollout … unified-trading-pm … /workspace/unified-trading-pm` on every
   base-image bake; `unified-trading-library/Dockerfile:84` `COPY . .` bakes it to `/app/unified-trading-pm/…`. Each
   service's thin `scripts/quality-gates.sh` sources
   `${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh` → resolves to that baked copy
   in-image. So a service's in-image QG runs **whatever qg-common.sh was in the base image it is pinned to**.
2. **The fix landed in PM but not in the pinned base image.** PM `qg-common.sh:106` gained
   `--ignore-vuln PYSEC-2026-3447` in commit `3f4fad383` (2026-07-14 11:32 UTC, on main + live-defi-rollout). The fresh
   UTL base `:latest` = `sha256:76a15429…` (07-18T10:36) carries it (proven:
   `docker run … grep -c PYSEC-2026-3447 /app/unified-trading-pm/scripts/quality-gates-base/qg-common.sh` → **2**). But
   11 repos still pin `sha256:b7e391f8…` (07-13T18:44, pre-fix) → their in-image QG lacks the ignore → pip-audit fails.
3. **The automation that should have bumped the pins is broken.** PM `.github/workflows/digest-drift-sweep.yml` (cron
   `0 */6 * * *`) authenticates its cross-repo Contents-API reads with `secrets.GITHUB_TOKEN` (`:77`), the ambient
   repo-scoped token, which **cannot read another repo's contents**. Every run (checked 07-14→07-18, incl. 07-18 06:38
   UTC) logs `No ARG found: 16 / Already fresh: 0 / Dispatched: 0` — all 16 `IMAGE_REPOS` hit "Dockerfile not found —
   skipping" at the always-failing fetch (`:138-151`). Its last real dispatch to ml-service was 2026-06-28; nothing
   since. Every other cross-repo call in this codebase (UTL `clone-pm-scripts`, `update-repo-version.yml`) uses a real
   cross-repo `GH_PAT`.

## Blast radius (11 repos pinned to stale `b7e391f8`, all will fail identically)

`agent-orchestrator`, `alerting-service`, `client-reporting-api`, `deployment-service`, `execution-service`,
`fund-administration-service`, `greeks-service`, `market-data-processing-service`, `ml-service` (now unblocked),
`strategy-service`, `trading-agent-service`. (`deployment-api` `e5de3b29` and `batch-live-reconciliation-service`
`9594091a` are on post-fix digests → likely unaffected; `features-service`/`instruments-service`/`mtds` on distinct
digests — re-verify at their next deploy.)

**Bucket-fold impact**: Folds C+D (execution-service + strategy-service) and any deployment-service redeploy will hit
the SAME wall at their Phase-D redeploy. Mitigation for each: bump that repo's `BASE_IMAGE_DIGEST` to `sha256:76a15429…`
(or the then-current fresh base) and ship via quickmerge → promote, exactly as done for ml-service.

## Recommended fix (operator decision — options)

A: **Fix the sweep token + backfill the 10 stale pins** — swap `secrets.GITHUB_TOKEN` → a cross-repo `GH_PAT` in
`digest-drift-sweep.yml:77` (matches `update-repo-version.yml`), re-run the sweep; it then auto-bumps every stale pin.
One-line workflow fix + one sweep run fixes the whole fleet and prevents recurrence. **[REC]** B: Manually bump each of
the 10 stale repos' `BASE_IMAGE_DIGEST` (as done for ml-service) — unblocks them now but leaves the sweep broken →
recurs on the next base-image republish. C: Both — A for durability + B for the repos needing a deploy before the next
sweep cycle.

Not fixed autonomously in this session: the token fix is a fleet CI-workflow change outside the bucket-fold dispatch
(rule-11 blast-radius: a shared-workflow change wants its own verify pass across the fleet). Bucket-fold Phase-D
redeploys handle their own repo's pin inline as they are reached.
