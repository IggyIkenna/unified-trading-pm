---
doc_type: issue
title: >-
  `deployed_versions`/`deployed_versions_aws` manifest provenance RETIRED — cross-repo follow-ups in deployment-api
  (dead `deployed_version_for` read), deployment-ui mock, and openapi spec
summary: >-
  infra_satellite_ao_dispatch_batch9_2026_08_09.md todo 4 chose option (b) — retire the never-working
  `deployed_versions`/`deployed_versions_aws` manifest provenance: removed the write steps from both router workflows,
  the manifest field, and the reconcile_manifest_backmerge entry. The manifest no longer carries deploy provenance (read
  Firestore `ci_status` instead, per the workspace `ci_status`-is-SSOT rule). Several CROSS-REPO consumers still
  reference the removed field; they degrade gracefully (return None/empty today — the field was already empty) but are
  now dead reads and should be cleaned up in their own repos. This doc tracks those.
created: "2026-08-10"
last_updated: "2026-08-10"
author: "slot-17-infra"
parent_epic: infrastructure_master
assigned_vm: planning
source:
  - /plans/archive/2026_08/infra_satellite_ao_dispatch_batch9_2026_08_09.md (todo 4)
related:
  - /plans/active/issues/codex_drift_followups_dual_cloud_image_builds_2026_08_08.md
  - /plans/active/infra_consolidated_closeout_2026_07_25.md
status: resolved
---

<!-- ARCHIVED 2026-08-10: all 3 todos done — deployed_versions phrase removed from all 4 openapi/docstring locations across deployment-api + unified-api-contracts; prior todos (dead read removal, UI mock update) already shipped. No remaining work. -->

# `deployed_versions` retirement — cross-repo follow-ups

## What I found

`infra_satellite_ao_dispatch_batch9_2026_08_09.md` todo 4 (2026-08-10) removed the `deployed_versions` /
`deployed_versions_aws` manifest-provenance write path and the manifest field itself (option b — it was dead code: the
write step never fired, `permissions: contents: read` blocked the push, and the field was empty for 5 months). The
retirement is complete in unified-trading-pm. But cross-repo consumers still reference the removed field:

1. **deployment-api** `deployment_api/routes/_repo_ci_manifest.py::deployed_version_for` reads
   `workspace-manifest.json.deployed_versions["prod"][repo]["version"]` and returns it as
   `RepoOverview.deployed_version` (`routes/repo_ci.py`). After the field removal this returns `None` unconditionally
   (already did — the field was empty — but now it's a permanently-dead read of a removed key). The method + its
   docstring describe the retired write path as live ("committed to the manifest by the cloudbuild post-build step").
2. **deployment-api** `deployment_api/routes/deployment_diff.py::_deployed_versions_at_sha` reads
   `.deployed_versions.production` at two SHAs for the `/api/deployments/diff` endpoint — already always `{}` today (the
   manifest key is `prod`, not `production`), now permanently dead.
3. **deployment-ui** `public/design-mocks/artifact-pipeline.html` mock narrative references the field being empty/absent
   — a design mock, cosmetic only.
4. **unified-api-contracts** `openapi/unified-trading-system.openapi.{json,yaml}` (and deployment-api's own
   `docs/specs/openapi.json`) document a mock-mode fallback "falls back to deployed_versions from the PM manifest" for
   the build-list endpoint — the fallback source no longer exists.

## Why it matters

None of these break at runtime (all degrade gracefully to None/empty, exactly the pre-retirement behavior since the
field was empty). They are dead reads and stale documentation that reference a removed manifest field — exactly the
"present the manifest as a build-provenance source" pattern the retirement was meant to end. A future reader of
`deployed_version_for`'s docstring will be misled into believing the manifest records deployed image tags.

## Recommended decision

Clean up each in its own repo (all small, bounded, deterministic):

- **deployment-api**: delete `deployed_version_for` (and its `repo_ci.py` call sites' `deployed_version` field wiring,
  or return a documented constant) since the manifest no longer records deployed versions; the dashboard's "deployed
  version" column should read Firestore `ci_status` / released-version registry instead, consistent with the
  `ci_status`-is-SSOT rule. Either remove the dead read or repoint it. `deployment_diff.py`'s
  `_deployed_versions_at_sha` either needs a live source or removal (it was already broken — reads `production`).
- **deployment-ui**: update the design mock narrative (cosmetic).
- **unified-api-contracts** + **deployment-api openapi spec**: drop the "falls back to deployed_versions" phrase from
  the mock-mode docstring (the fallback source is gone).

## Todos

- [x] ✅ [INFRA] P3. Remove the dead `deployed_versions` read in deployment-api
      `_repo_ci_manifest.deployed_version_for` + `repo_ci.py` call sites (or repoint to Firestore `ci_status` /
      released-version registry); remove `deployment_diff._deployed_versions_at_sha` or wire it to a live source. (repo:
      deployment-api) — deployment-api@fff55c6
- [x] ✅ [INFRA] P3. Update the deployment-ui artifact-pipeline design mock to drop the `deployed_versions` narrative.
      (repo: deployment-ui) — deployment-ui@32a99e5. Rewrote the "Build provenance never recorded" health item: the
      manifest no longer carries `deployed_versions`/`deployed_versions_aws` (RETIRED 2026-08-10); provenance now read
      from Firestore `ci_status` / released-version registry, matching the deployment-api fix (fff55c6). QG green.
- [x] ✅ [INFRA] P3. Remove the "falls back to deployed_versions from the PM manifest" mock-mode phrase from the
      build-list endpoint docstring in unified-api-contracts openapi + deployment-api openapi spec. —
      unified-api-contracts@ea9ca78b8f, deployment-api@c6267286be

## Progress Log

- **2026-08-10 (slot-3, infra)**: Flipped todo 2 — deployment-ui design mock updated.
  `public/design-mocks/artifact-pipeline.html` health item "Build provenance never recorded" no longer describes
  `deployed_versions`/`deployed_versions_aws` as live manifest fields; now states the fields were RETIRED 2026-08-10 and
  provenance is sourced from Firestore `ci_status` / released-version registry (consistent with deployment-api fix
  `fff55c6`). Shipped `deployment-ui@32a99e5` via quickmerge (QG green, 51s, sentinel verified); verified on origin.
- **2026-08-10 (slot-25, infra)**: Flipped todo 3 — removed "falls back to deployed_versions from the PM manifest"
  phrase from build-list endpoint docstring in 4 files across 2 repos: `deployment-api` (`builds.py` docstring +
  `docs/specs/openapi.json`) and `unified-api-contracts` (`openapi/unified-trading-system.openapi.{yaml,json}`).
  Replaced with "returns mock build entries" since the `deployed_versions` manifest field no longer exists. Shipped
  `unified-api-contracts@ea9ca78b8f` + `deployment-api@c6267286be` (both QG green, verified on origin).
