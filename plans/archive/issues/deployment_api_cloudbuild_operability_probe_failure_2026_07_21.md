---
doc_type: issue
title: deployment-api Cloud Build broken since 14:19 UTC — stale vendored unified-trading-library blocks deploy
summary: >-
  9 consecutive deployment-api Cloud Build runs have FAILED at the operability-probe step since 2026-07-21 14:19 UTC
  (last SUCCESS 14:18:35 UTC, image tag a557471, still the live Cloud Run revision). The probe's `import
  deployment_api.main` fails with `ImportError: cannot import name 'gcs_read_object_range' from
  'unified_trading_library'` — a symbol that exists in the current unified-trading-library source but not in whatever
  snapshot the Docker build vendored. Suspected root cause: cloudbuild.yaml's `vendor-deps` step skips re-cloning a
  sibling repo if its destination directory already exists in the build cache (`if [ -d "$$dest" ]; then ... skip; fi`),
  so a cached, stale unified-trading-library checkout never picks up new commits. Blocks 5 of 6 deployment-api fixes in
  deployment_alerts_ingestion_completeness_2026_07_20.md (todos 4/5/6/8/9) from reaching production despite being merged
  to `main` — discovered while measuring real post-ingestion coverage for that plan's todo 11.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: [ci-cd, cloud-build, deploy, blocker, p0]
related: []
created: "2026-07-21"
parent_epic: observability_master
priority: P0
assigned_vm: planning
resolved_by: slot-3, review, 2026-07-21
locked_by:
source: [deployment_alerts_ingestion_completeness_2026_07_20.md]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# What I found

While measuring real production coverage for `deployment_alerts_ingestion_completeness_2026_07_20.md` todo 11
("Post-ingestion coverage re-measure"), I found deployment-api's live Cloud Run revision
(`uts-shared-deployment-api-00232-sbm`, image `deployment-api:a557471`, ready since `2026-07-21T14:27:34Z`) is running
an OLDER build than what's on `main` — confirmed by diffing `a557471`'s content directly: it has todo 3
(`_read_alerting_service_sync`) but NOT todo 4 (`subject_repo`), todo 5 (`resolve_bucket_name()` for the
cicd-events/alerting-service buckets), todo 6 (one-object-per-write), todo 8 (30-day retention/pagination), or todo 9
(`_read_kill_switch_audit_log_sync`) — even though `git show origin/main:...` proves all of that code IS on `main` as of
commit `11fce38` (2026-07-21 17:41:19 UTC).

**Cloud Build history** (queried directly via the `cloudbuild_v1` Python client,
`projects/central-element-323112/locations/asia-northeast1`, filtered to `deployment-api` images, verified independently
— not just taking a sub-agent's word for it):

| build (UTC)  | image                            | result                                         |
| ------------ | -------------------------------- | ---------------------------------------------- |
| 14:18:35     | `deployment-api:latest`          | **SUCCESS** (`d666ef15-ec5`) — last good build |
| 14:19:32     |                                  | FAILURE (`6291e79a-649`)                       |
| 15:06, 15:09 |                                  | FAILURE                                        |
| 15:51, 15:50 |                                  | FAILURE                                        |
| 16:24, 16:26 |                                  | FAILURE                                        |
| **17:41:24** | (contains todo 9, latest `main`) | **FAILURE** (`12eb1e3f-3bc`)                   |

Every failure is at the `operability-probe` step; `push`/`scan-check`/`deploy` never even run (stay `QUEUED`). **Root
cause, pulled directly from the build's Cloud Logging entries**
(`resource.type="build" resource.labels.build_id="12eb1e3f-3bc8-4f1b-b294-3cde58f54d45"`):

```
=== Operability probe: IMPORT deployment_api.main (the gunicorn app_uri) ===
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import deployment_api.main; print('IMPORT OK: deployment_api.main')
  File ".../deployment_api/main.py", line 45, in <module>
    from .routes import (
  File ".../deployment_api/routes/deployment_digest.py", line 47, in <module>
    from deployment_api.routes.deployments_inventory import (
  File ".../deployment_api/routes/deployments_inventory.py", line 110, in <module>
    from deployment_api.routes._run_log_tail import read_run_log_tail
  File ".../deployment_api/routes/_run_log_tail.py", line 15, in <module>
    from unified_trading_library import gcs_read_object_range
ImportError: cannot import name 'gcs_read_object_range' from 'unified_trading_library' (/app/unified_trading_library/__init__.py)
```

`gcs_read_object_range` DOES exist in the current `unified-trading-library` source
(`unified_trading_library/__init__.py:160,2241`) and deployment-api's `pyproject.toml` declares
`unified-trading-library>=0.12.0,<1.0.0` with `path = "../unified-trading-library", editable = true` in `uv.lock` — a
normal sibling-repo editable install, not a version-range problem.

**Suspected mechanism**: `deployment-api/cloudbuild.yaml`'s `vendor-deps` step (~line 79-121) clones sibling repos into
the Docker build context, but guards each clone with:

```
if [ -d "$$dest" ]; then echo "vendor-deps: $$dest present — skipping"; return 0; fi
echo "vendor-deps: cloning $$repo @ live-defi-rollout → $$dest"
```

If `$$dest` (the vendored `unified-trading-library` checkout) survives across builds via a cached Docker
layer/build-cache, this SKIPS re-cloning even when the real `unified-trading-library` repo has new commits upstream — so
the vendored snapshot silently goes stale. I did NOT confirm this is the exact trigger (didn't inspect the build's
cache-hit/miss behavior directly — that needs someone with deeper Cloud Build cache visibility than I pulled here), but
it's the most plausible explanation given `gcs_read_object_range` is a real, present symbol in the actual repo.

# Why it matters

This is a **live production deploy blocker**, not just a test failure — deployment-api has been stuck on an hours-stale
image since 14:18 UTC, silently failing every subsequent merge's deploy attempt (9 in a row as of this writing).
Concretely for `deployment_alerts_ingestion_completeness`: todos 4 (subject_repo correctness), 5 (bucket-resolution QG
fix), 6 (row-drop race fix), 8 (30-day retention), and 9 (kill-switch ingestion) are all merged to `main` but **not
running against real traffic** — anyone reading the `/alerts` page right now is seeing the OLD behavior for those 5
fixes despite the plan showing them `[x]` shipped. Any other repo's next deploy attempt will hit the same wall until
this is fixed.

# Recommended decision

1. Confirm the `vendor-deps` stale-cache hypothesis: check whether Cloud Build's build cache (or a Docker layer cache)
   is preserving the vendored `unified-trading-library` directory across builds, and whether the cache key includes the
   sibling repo's current HEAD SHA. If not, that's the fix — key the vendor-deps cache (or skip the cache) on the
   sibling repo's live SHA so a stale snapshot can never survive past its source updating.
2. Once fixed, re-run the build for at least commit `11fce38` (or later) and confirm `deploy` reaches `SUCCESS` + the
   new Cloud Run revision is `latestReadyRevision`.
3. Re-run `deployment_alerts_ingestion_completeness_2026_07_20.md` todo 11's coverage re-measure for todos 4/5/6/8/9
   ONLY after that deploy confirms live (don't trust "code on main" as a proxy for "running in prod" — this incident is
   exactly why).

## Todos

- [x] ✅ [INFRA] P0. **Original `vendor-deps` hypothesis was WRONG — corrected root cause found + confirmed already
      fixed by an automated pin-refresh commit, not agent code.** `vendor-deps` (`cloudbuild.yaml` ~79-121) does NOT
      even handle `unified-trading-library` — that dep is baked into a PRE-BUILT base Docker image
      (`asia-northeast1-docker.pkg.dev/.../unified-trading-library/unified-trading-library@${BASE_IMAGE_DIGEST}`,
      `Dockerfile:45`), not cloned per-build. Real root cause: the `ARG BASE_IMAGE_DIGEST` pin in `Dockerfile` was stale
      — it pointed at a UTL base image published BEFORE `gcs_read_object_range` was added to unified-trading-library
      (`unified-trading-library@e22e40f1`, 2026-07-21 13:12:57 UTC), so every build baked in an image lacking the symbol
      regardless of the deployment-api source itself. Fixed by `deployment-api@e8679a3`
      (`chore(deps): refresh base-image digest pin`, part of the automated base-image-digest-drift-detector this
      workspace already runs) bumping `sha256:17738961...` → `sha256:748604b6...`. **This is a RECURRING failure class**
      — `strategy-service@b15c73c` (2026-07-17) fixed the identical bug 4 days earlier (a different stale pin); the
      automated refresh doesn't run fast/synchronously enough after UTL publishes new symbols to prevent hours-long
      deploy outages. Not filing a new issue for that — flagging here since `b15c73c`'s own fix already improved the
      probe (imports `deployment_api.main`, the real `app_uri`, not the near-empty package `__init__`) so this class of
      bug now fails FAST at build time (not 5 steps later at `deploy`), which is the containment this workspace already
      has. **Verified live** (3 independent signals, not self-report): (1) Cloud Build history —
      `040eabcd`/`609584cf`/`d21cb9aa` all `SUCCESS` incl. the `deploy` step, 18:43/18:46/19:19 UTC, all 13 steps green;
      (2) `git merge-base --is-ancestor 11fce38 7f505a7c060...` confirms the built commit descends from the target; (3)
      Cloud Run API — `uts-shared-deployment-api`'s `latestReadyRevision` is `...-00235-9dl`, image tag `7f505a7`, all 6
      revision conditions `CONDITION_SUCCEEDED` (container healthy in 43.8s). (repo: deployment-api)
- [x] ✅ [REVIEW] P1. Re-measured `deployment_alerts_ingestion_completeness_2026_07_20.md` todo 11's coverage for todos
      4 (subject_repo)/5 (bucket resolution)/6 (row-drop race)/8→7 (retention)/9 (kill-switch, `deployment-api`'s own
      `_read_kill_switch_audit_log_sync`) now that the deploy above is confirmed live. All 5 fix commits
      (`04b19bd5`/`36db2e858`/`7e7fa5a`/`dbeb5c9`/`cda7a89`/`105ffb3`) are confirmed ANCESTORS of the deployed `7f505a7`
      via `git merge-base --is-ancestor`, so the running container has the code. **Direct prod-data proof for
      subject_repo (todo 4, the writer side)**: read `gs://unified-trading-cicd-events/cicd/alerts/2026-07-21/` directly
      — a row written at `19:19:58Z` (36 min after the 18:43 deploy) carries `"subject_repo":"unified-trading-pm"`
      distinct-but-correct (self-reporting workflow), proving the `notify-slack.yml` writer-side fix
      (`unified-trading-pm@36db2e858`) is live and producing correctly-shaped data. **Limitation, stated honestly rather
      than skipped**: could NOT get authenticated HTTP access to
      `https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app` itself to exercise `/api/repo-ci/alerts` /
      `/api/alerts` end-to-end (repo-filter correctness, retention `days`/`capped` response shape, kill-switch-audit
      read results) — this sandbox's ADC is an interactive user OAuth2 credential
      (`google.oauth2.credentials.Credentials`), not a service account, and `google.oauth2.id_token.fetch_id_token`
      requires one to mint a Cloud-Run-invoker ID token. Todos 5/6/8/9's LIVE-DATA behavior (as opposed to
      code-is-deployed) is therefore confirmed by ancestry + deploy-health, not by direct API exercise — a follow-up
      re-check with service-account creds (or from inside the VPC / via an authorized human) would close that gap if it
      matters enough to chase further. Given the class of risk here (read-path correctness on already-tested code, not a
      data-correctness/live-trading path), this is a reasonable stopping point. (repo: deployment-api)
