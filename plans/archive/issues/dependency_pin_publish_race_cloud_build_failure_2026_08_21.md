---
doc_type: issue
title: Dependency pin bump races ahead of wheel publish — transient Cloud Build FAILUREs (instruments-service self-healed, 2026-08-21)
summary: >-
  cloud-build-failure-watcher escalated agt-2cbd97 for an instruments-service Cloud Build FAILURE. On arrival (~4.5h
  after detection, per the queue's 827-task backlog at dispatch time) the wall was ALREADY resolved: 5 consecutive
  builds since 11:06 UTC are SUCCESS, including one whose commit is a verified ancestor of current live-defi-rollout
  HEAD. Root cause (confirmed from the failing build's log): commit e66b325e ("chore(deps): re-pin unified-api-contracts
  to 0.158.0 (major/breaking floor)") landed and triggered a build before the corresponding 0.158.0 wheel had actually
  finished publishing to the asia-northeast1 Artifact Registry — `uv pip install` exhausted its own 7-attempt
  exponential-backoff retry (max ~615s total) still resolving against a registry that topped out at
  0.157.1.dev1+g615972874, and the build failed outright. The Dockerfile's built-in retry loop is a reasonable mitigation
  for short registry-propagation lag, but is NOT sufficient if the wheel publish takes longer than ~10 minutes — in that
  case the triggering build fails hard, and only a LATER-triggered build (new commit, e.g. the subsequent 0.159.0 re-pin)
  observes the now-published version and succeeds. No code fix was needed or applied — closing out per the
  already-resolved-on-arrival guidance in cicd.md's cloud_build_router_failure section, which generalizes to this wall
  type.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: [ci-cd, cloud-build, dependency-pin, uv, release-pipeline, transient, self-healed]
created: 2026-08-21
related: [/codex/08-workflows/ci-cd-flow.md]
---

# Dependency pin bump races ahead of wheel publish — transient Cloud Build FAILUREs

## What happened

`cloud-build-failure-watcher` fired escalation `agt-2cbd97` (wall_type `cloud_build_failure`) for
`instruments-service`, reporting a Cloud Build FAILURE/TIMEOUT/INTERNAL_ERROR/EXPIRED in the last ~20 minutes. By the
time a cicd worker (slot 4) was actually dispatched, the escalation queue had ~827 tasks backlogged, and the wall had
long since self-healed.

## Evidence (verified live, 2026-08-21T15:23–15:30Z)

**Build timeline for instruments-service** (`gcloud builds list`, project `central-element-323112`, region
`asia-northeast1`, trigger `c2061fd9-6d2d-4af0-8802-4ea55958984e`):

| Build | Created (UTC) | Status |
|---|---|---|
| `2e562778` | 10:47:42 | FAILURE |
| `95687259` | 10:53:53 | FAILURE |
| `3acc780a` / `97263fd0` / `424b3346` / `07a3e673` / `5974c85b` / `810048cf` / `6bee455a` / `495b9fcf` / `f89b1e0f` | 11:08:29 → 14:41:01 | SUCCESS ×9 |

**Failing build's log** (`gcloud builds log 95687259…`, step 5 "build", `uv pip install --system --no-sources -e .`):

```
No solution found when resolving dependencies:
  Because only unified-api-contracts<=0.157.1.dev1+g615972874 is available and instruments-service==0.104.0
  depends on unified-api-contracts>=0.158.0,<1.0.0, we can conclude that instruments-service==0.104.0 cannot
  be used. ... your requirements are unsatisfiable.
uv pip install failed after 7 attempts
```

The retry loop (7 attempts, exponential backoff 15s→180s, ~615s total) exhausted without the required version ever
appearing — the build failed hard rather than eventually succeeding.

**Commit that introduced the pin**: `e66b325e chore(deps): re-pin unified-api-contracts to 0.158.0 (major/breaking
floor)` — an automated re-pin following a UAC major/breaking version graduation, landed on `live-defi-rollout` shortly
before the 10:47/10:53 builds it triggered.

**Confirmed self-heal, not a live problem**:
- Current `live-defi-rollout` HEAD (`a58ac1e3`) pins `unified-api-contracts>=0.159.0,<1.0.0` (`pyproject.toml:44`,
  commit `e29699d2` "re-pin ... to 0.159.0").
- `git merge-base --is-ancestor 0f51d109… HEAD` → **yes** — the commit behind the most recent SUCCESS build
  (`f89b1e0f`, 14:41:01) is a strict ancestor of current HEAD, i.e. HEAD is at least as new as the last verified-green
  build.
- Artifact Registry (`gcloud artifacts versions list --package=unified-api-contracts …`) shows versions through
  `0.161.1` (published 14:22:14) — well above the `>=0.159.0` floor currently pinned, confirming the pin resolves.
- No FAILURE/TIMEOUT/INTERNAL_ERROR/EXPIRED for `instruments-service` on this trigger since 10:53:53 (checked through
  15:23:23, a 4.5h clean window spanning 9 consecutive successful builds).

## Root cause

The automated "major/breaking floor" re-pin sweep commits + pushes the new version constraint the moment a UAC
graduation lands, but the corresponding wheel's `publish-package` step (SSOT: `/codex/08-workflows/ci-cd-flow.md`)
runs asynchronously and can still be in flight when the re-pin's own push triggers a Cloud Build. The consuming repo's
build then races the publish and — if the wheel isn't live within the Dockerfile's own ~615s retry budget — loses,
producing a hard FAILURE rather than a delayed success. This appears to have hit a wider set of repos in the same
~10:10–10:53 UTC window (features-service, strategy-service, ml-service, trading-agent-service,
market-data-processing-service, alerting-service, client-reporting-api, greeks-service, fund-administration-service,
deployment-api all showed FAILURE entries in that window per a broad `gcloud builds list` sweep) — **not diagnosed
here** (out of this escalation's scope, which was `instruments-service` only), but flagged in case those repos'
respective CICD escalations find the same root cause and this doc saves a re-diagnosis.

## Resolution

No code change needed on `instruments-service` — self-healed once the `0.158.0` wheel (and subsequently `0.159.0`)
actually published. No `[OPERATOR]` action needed. Closing per cicd.md's already-resolved-on-arrival guidance.

## Possible future improvement (not implemented — out of scope for a one-shot wall-clear)

If this pattern recurs and causes real pain, the fix would live in the re-pin automation itself: gate the re-pin
commit/push on the target wheel version actually being resolvable in the Artifact Registry first (poll
`gcloud artifacts versions list` before pushing the pin bump), rather than relying on the consumer's own install-time
retry loop to absorb the publish lag. Not raised as a tracked todo here since a single ~13-minute self-heal is well
within the kind of transient window this workspace's other gate types (e.g. `local_ratchet_gate_breach`'s 15-minute
self-heal grace) already tolerate without escalation — worth revisiting only if a future occurrence does NOT self-heal
within a normal build-retry cycle.
