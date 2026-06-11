---
title: "instruments-service version phantom — manifest/main 0.30.0 vs tag v0.2.1 (needs reconciliation)"
created: 2026-06-11
author: slot-1 (CI firefight)
locked_by: live-defi-rollout
priority: P2
status: active
---

# instruments-service version phantom

## What I found

`instruments-service` has inconsistent version data:

- `workspace-manifest.json` `versions{}` = **0.30.0** (both LDR + main)
- latest git **tag** = **v0.2.1**
- the SIT QG version-alignment check reads `main=0.30.0`

So `versions{}=0.30.0` is a **phantom** — well ahead of the real released tag (v0.2.1). Effects:

1. A consumer floor `>=0.30.0` (system-integration-tests had this) is **unsatisfiable by tag** — the version-aware clone
   fallback seeks a nonexistent `v0.30.0` tag.
2. It shows as a VERSION_SPLIT / VESTIGIAL_SCALAR_DRIFT in `assert_version_coherence` (warn-only).

## Why a one-liner doesn't work

Lowering `versions{}` 0.30.0→0.2.1 on LDR (attempted 2026-06-11, reverted) creates a **downgrade-drift**: LDR (0.2.1)
reads as BEHIND main (0.30.0), which the SIT version-alignment gate blocks. Determining the TRUE version + aligning
source `pyproject` / `versions{}` (main+LDR) / tags consistently is a version-reconciliation task.

## Recommended decision

Reconcile via `run-version-alignment.sh --fix` (the sanctioned tool) OR have semver-agent re-stamp instruments-service
to its true version, so source `pyproject.version`, `versions{}` (main+LDR), and the release tag all agree. Then the SIT
floor `>=0.2.1` lands cleanly. NOT blocking today (the content-first clone + non-blocking dep-range mean SIT's
`>=0.30.0` floor no longer hard-fails CI — it warns).
