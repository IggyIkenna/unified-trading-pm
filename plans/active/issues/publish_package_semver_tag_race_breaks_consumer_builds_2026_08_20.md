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
  - /plans/active/issues/cloud_build_uac_publish_ordering_race_recurrence_strategy_service_2026_08_20.md
created: 2026-08-20
author: /ci-reconcile (cicd escalation agt-18cf35, slot-7·planning)
parent_epic: ci_master
priority: P2
source: >-
  Cloud Build FAILURE escalation for instruments-service (env prod, branch main) — cloud_build_router_failure,
  agt-18cf35, 2026-08-20.
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
effort: low
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

- [x] ✅ [BACKEND] P2. **Add `tags: ["v*"]` to the per-repo `publish-package.yml` trigger** — unified-api-contracts@42e319f5,
      unified-trading-pm@template-fix (see Progress Log). Correction: `rollout-workflow-templates.sh`'s `TEMPLATE_DIR`
      (`scripts/workflow-templates/`) does NOT include a `publish-package.yml.tmpl` — this workflow is manually
      `cp`'d per repo per its own header comment, not rolled out by that script. The canonical source-of-truth copy
      is `unified-trading-pm/scripts/propagation/templates/publish-package.yml` (also fixed).
- [ ] [BACKEND] P2. **Propagate the `tags: ["v*"]` fix to every OTHER wheel-publishing repo's own
      `.github/workflows/publish-package.yml` copy** (e.g. unified-trading-library, unified-cloud-interface) — only
      `unified-api-contracts` was fixed live (2026-08-21, it was the repo causing this instance's failure). No
      automated rollout script covers this file (confirmed: not in `rollout-workflow-templates.sh`'s
      `TEMPLATE_DIR`), so this is manual per-repo `cp` from the now-fixed
      `scripts/propagation/templates/publish-package.yml`.

## Progress Log

- **2026-08-21 (cicd escalation agt-0efe8e, slot-32·planning)** — Recurrence for strategy-service (build
  17377c02 FAILURE, then re-queued build 541345c5 also FAILURE, both on `unified-api-contracts>=0.159.0` vs
  GAR's `0.158.1.dev1+gae56a4f9f`). Confirmed same race: UAC tag `v0.159.0` existed (`ae56a4f9f`) but the wheel
  never published. Immediate unblock: manually re-dispatched `publish-package` repository_dispatch for
  `unified-api-contracts@ae56a4f9f` → `0.159.0` published to AR (`2026-08-21T12:36:34Z`); re-triggered
  `strategy-service-build` trigger (`9caa93b0-bb1d-4052-a928-c262e76ff7ef`) →
  **`Evidence: cloudbuild=97f20649-1503-4dec-9120-3d3b3060a612` — SUCCESS**, fresh `strategy-service:latest`
  digest pushed. Root-cause fix (this doc's sole todo, previously unimplemented) applied and shipped:
  added `tags: ["v*"]` to `unified-api-contracts/.github/workflows/publish-package.yml`
  (`Evidence: unified-api-contracts@42e319f5` via quickmerge) and to the canonical template
  `unified-trading-pm/scripts/propagation/templates/publish-package.yml`. No open repo-blockers found
  (`GET /api/repo-blockers` → `{"open": []}`). Fleet-wide propagation to every other wheel-publishing repo's
  own copy remains open — see corrected todo above.

- **2026-08-20 (cicd escalation agt-18cf35, slot-7·planning)** — Diagnosed, fixed, verified. Root-caused the
  instruments-service prod build failure to the publish/semver tag race above; re-published
  `unified-api-contracts` 0.149.0 to AR; re-triggered `instruments-service-prod` → SUCCESS
  (`cloudbuild=a29956a9-06de-4d65-a6cc-3c4fa6693167`). The recurrence fix (tag-triggered publish) is a follow-up todo;
  the immediate wall is green.

- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries); all paths re-verified on disk,
  unchanged.
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, batch 3/3): RECLASSIFY (whole-doc), `assigned_vm: NA
  → planning`. Sole open todo is a single, fully-specified `.github/**` workflow-trigger fix (add `tags: ["v*"]` to
  `publish-package.yml`, roll out via `rollout-workflow-templates.sh`, verify on the next breaking release) — no
  design/judgment call, outcome worker-determinable alone. Conflict-check: grepped active `assigned_vm: planning`
  docs for overlapping scope; found `cloud_build_uac_publish_ordering_race_recurrence_strategy_service_2026_08_20.md`
  (also `NA`) independently diagnosing an adjacent variant of the SAME semver-agent/publish-package race (its own P3
  "longer-term option" proposes sequencing semver-agent's dispatch behind `publish-package.yml`'s AR-confirmation —
  a different remedy for overlapping root-cause territory) with no prior cross-reference between the two docs —
  added the missing `related:` link both directions so a worker landing either fix does so aware of the other.
  Not a blocking conflict (neither doc is `planning`-dispatched, and the two P2 fixes are independent workstreams:
  producer-side tag-triggered republish here vs. consumer-side retry-budget widening there), but flagging per the
  "flag rather than guess which doc should win" instruction.
