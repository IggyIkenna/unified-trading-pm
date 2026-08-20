---
doc_type: issue
title:
  "Wheel-publish races semver-agent's tag mint — a released version is tagged but never published, so consumers
  pinned to the release floor fail their image builds"
summary: >-
  instruments-service prod Cloud Build (build 1c52e823-27d7-4273-b342-0466f3b09859) FAILED at docker step 5 with
  "unified-api-contracts>=0.149.0,<1.0.0" unsatisfiable — the Artifact Registry's newest UAC wheel was
  `0.148.1.dev1+gfd4391914`, no `0.149.0`. Root cause is a cross-workflow race: UAC's per-repo `publish-package.yml`
  fires on `push: [main]` and dispatches with `git describe --tags`, which runs BEFORE semver-agent (same `push: main`
  trigger) mints and pushes the `v0.149.0` tag (~26s later). So the publish stamps a `.dev1` build and the real
  release wheel is never published — while the version-bump fan-out correctly re-pins every consumer to `>=0.149.0`
  (manifest + tag both say 0.149.0). Every consumer's prod build then breaks on a version that will never resolve.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, instruments-service, unified-trading-pm]
scope: [engineer]
tags: [ci, cloud-build, publish-package, semver-agent, artifact-registry, race, live-incident]
related:
  - /plans/active/issues/mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md
created: 2026-08-20
author: /ci-reconcile (cicd escalation agt-18cf35, slot-7·planning)
parent_epic: ci_master
priority: P2
source: >-
  Cloud Build FAILURE escalation for instruments-service (env prod, branch main) — cloud_build_router_failure,
  agt-18cf35, 2026-08-20.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-infra
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
last_updated: 2026-08-20
context_scope:
  [
    unified-api-contracts/.github/workflows/publish-package.yml,
    unified-api-contracts/.github/workflows/semver-agent.yml,
    unified-trading-pm/.github/workflows/publish-package.yml,
    unified-trading-pm/.github/workflows/update-repo-version.yml,
  ]
---

# Wheel-publish races semver-agent tag mint — released version never published

## Root cause (measured, not inferred)

`unified-api-contracts` v0.149.0 was tagged and recorded in the manifest, but the `0.149.0` wheel was never published
to Artifact Registry. The three pieces of evidence line up exactly:

- `git ls-remote origin v0.149.0` → tag exists, points at `fd439191` (= `origin/main` HEAD).
- `workspace-manifest.json` → `versions.unified-api-contracts = 0.149.0`, `ci_status: MAIN_GREEN`.
- `gcloud artifacts versions list … --package=unified-api-contracts` → newest is `0.148.1.dev1+gfd4391914`, no
  `0.149.0`.

The mechanism is a race between two workflows that both fire on `push: [main]`:

1. `publish-package.yml` (per-repo) fires immediately on the promote push and dispatches to PM with
   `VERSION=$(git describe --tags --always --match 'v*')` — which resolves to `0.148.1.dev1+gfd439191` because the
   `v0.149.0` tag does not exist YET.
2. `semver-agent.yml` (same `push: [main]` trigger) mints + pushes `v0.149.0` **~26s later** (measured: the failing
   cycle's `publish-package` run 32360286459 at 10:43:10Z vs `version-registry-notify v0.149.0` at 10:43:36Z).

The tag push (`refs/tags/v0.149.0`) does **not** re-trigger `publish-package.yml` (its trigger is
`push: branches: [main]` only), so the release wheel is simply never published. This is a FLEET-WIDE defect — every
wheel-publishing repo (unified-api-contracts, unified-trading-library, …) has this same per-repo workflow, so every
breaking (MINOR-on-0.x) release silently publishes a `.dev1` instead of the release and breaks any consumer pinned to
the release floor.

## Fix applied (this instance)

Re-dispatched `publish-package` for `unified-api-contracts` at `commit_sha=fd439191…` (the `v0.149.0` tag target,
now that the tag exists — PM's reusable workflow checks out with `fetch-depth: 0` and stamps the wheel from the
reachable tag). `0.149.0` published to AR. Then re-triggered `instruments-service-prod` Cloud Build:

- **`Evidence: cloudbuild=a29956a9-06de-4d65-a6cc-3c4fa6693167` — SUCCESS** (2026-08-20T11:26:32Z), docker step 5
  (the `uv pip install -e .` that previously failed on `unified-api-contracts>=0.149.0`) cleared.

## Recommended root-cause fix (recurrence — not yet done)

Make the release wheel publish deterministically follow the tag mint, rather than race it. Lowest-touch option: add the
tag push to the per-repo `publish-package.yml` trigger so the tag push re-fires publish with the now-correct version:

```yaml
on:
  push:
    branches: [main]
    tags: ["v*"]
```

(The `.dev1` publish on the commit push is harmless and already happens today; the tag-triggered run adds the correct
release wheel.) Alternative: have semver-agent dispatch `publish-package` with the minted version after pushing the
tag. Either way this is a `.github/**` change that must go through the workflow-template + `rollout-workflow-templates.sh`
path (never hand-edit per-repo copies).

## Todos

- [ ] [BACKEND] P2. **Add `tags: ["v*"]` to the per-repo `publish-package.yml` trigger** (or have semver-agent dispatch
      the publish with the minted version) so a release wheel is published after the tag lands. Edit the template +
      roll out via `rollout-workflow-templates.sh`; verify with the next breaking release. Repo: unified-trading-pm
      (template) + every wheel-publishing repo.

## Progress Log

- **2026-08-20 (cicd escalation agt-18cf35, slot-7·planning)** — Diagnosed, fixed, verified. Root-caused the
  instruments-service prod build failure to the publish/semver tag race above; re-published
  `unified-api-contracts` 0.149.0 to AR; re-triggered `instruments-service-prod` → SUCCESS
  (`cloudbuild=a29956a9-06de-4d65-a6cc-3c4fa6693167`). The recurrence fix (tag-triggered publish) is a follow-up todo;
  the immediate wall is green.

- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries); all paths re-verified on disk,
  unchanged.
