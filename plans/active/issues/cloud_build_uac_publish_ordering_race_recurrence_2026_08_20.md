---
doc_type: issue
title: >-
  fund-administration-service Cloud Build FAILURE 2026-08-20 — publish-ordering race recurrence (uac 0.149.0
  floor-bump build ran before unified-api-contracts 0.149.0 reached GAR); self-healed, no code fix needed
summary: >-
  cloud-build-failure-watcher escalated fund-administration-service build 930d8adf (FAILURE 2026-08-20T11:03:20Z) —
  the Dockerfile `uv pip install --system -e . --no-sources` step failed resolving `unified-api-contracts>=0.149.0`
  because GAR's `unified-libraries` index only served up to `0.148.1.dev1+gfd4391914` at build time. Root cause is the
  documented cross-repo publish-ordering race (2026-07-29 incident:
  /plans/archive/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md): the service's
  `chore(deps): re-pin unified-api-contracts to 0.149.0` floor-bump pinned a UAC release before UAC's own wheel reached
  Artifact Registry. uac 0.149.0 (+0.149.1.dev1+g2db449df4) published 2026-08-20T11:16:41Z, ~13 min after the build
  started — well beyond the Dockerfile retry-wrapper's ~45s budget (3 attempts, 15s/30s backoff). Re-ran the trigger →
  build 080f7c69 SUCCESS; fresh `:latest` digest pushed. No code change shipped (the mitigation is already present);
  the ~13-min publication gap has now exceeded the retry budget on two separate recurrences (08-16, 08-20) — the
  fleet-level retry-budget / release-ordering decision is the open follow-up.
status: open
nature: issue
scope: [engineer, admin]
asset_group: [ci] # recurrence of the 07-29 publish-ordering race; squarely ci-tranche (CI/CD pipeline mechanics)
stage: [meta]
repos:
  [
    fund-administration-service,
    unified-api-contracts,
    unified-trading-pm,
  ]
tags: [ci-cd, cloud-build, publish-ordering, artifact-registry, unified-api-contracts, race-condition]
related:
  [
    /plans/archive/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md,
    /plans/active/issues/cloud_build_router_failure_escalation_undercoverage_2026_08_16.md,
  ]
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/06-coding-standards/dockerfile-standards.md,
    fund-administration-service/Dockerfile,
    /plans/archive/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md,
  ]
created: 2026-08-20
author: claude-agent
last_updated: 2026-08-20
parent_epic: ci_master
priority: P2
source: "AO escalation agt-1497fe (wall_type=cloud_build_failure, repo=fund-administration-service)"
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# fund-administration-service Cloud Build FAILURE — publish-ordering race recurrence (2026-08-20)

## What happened (ground truth, verified live)

1. fund-administration-service carries `unified-api-contracts>=0.149.0,<1.0.0` in `pyproject.toml` on
   `live-defi-rollout`/`main` (re-pin commit `05d5b60 chore(deps): re-pin unified-api-contracts to 0.149.0
   (major/breaking floor)`).
2. The `fund-administration-service-build` trigger (fires on `main` pushes) built revision `3118cd7` at
   2026-08-20T11:03:20Z. The Dockerfile `build` step ran `uv pip install --system -e . --no-sources` against
   `UV_EXTRA_INDEX_URL=...asia-northeast1-python.pkg.dev/central-element-323112/unified-libraries/simple/` and failed
   on all 3 retry attempts:
   ```
   × No solution found when resolving dependencies:
   ╰─▶ Because only unified-api-contracts<=0.148.1.dev1+gfd4391914 is available and
       fund-administration-service==0.9.90 depends on unified-api-contracts>=0.149.0,<1.0.0, we can conclude that
       fund-administration-service==0.9.90 cannot be used.
   ```
3. Root cause: **the exact publish-ordering race documented 2026-07-29** — the service's floor-bump pinned a UAC
   release before UAC's wheel reached Artifact Registry. The `unified-libraries` GAR index only served
   `0.148.1.dev1+gfd4391914` at build time. Verified the index now (authenticated curl):
   `0.149.0` and `0.149.1.dev1+g2db449df4` are present.
4. uac's `publish-package` for `main@2db449df` completed SUCCESS at 2026-08-20T11:16:41Z — **~13 minutes after** the
   fund-admin build started (11:03). The Dockerfile's retry wrapper (3 attempts, 15s/30s backoff, ~45s total budget)
   — the 2026-07-29 hardening — exhausted before the publication landed.
5. Live verification: re-ran the trigger (`gcloud builds triggers run fund-administration-service-build --branch main`)
   → build `080f7c69-7570-4efb-8d16-737931103e64` reached **SUCCESS**; `:latest` re-pointed to a fresh digest
   (`sha256:039c738098ea7df5411e1c1f784945595dcc93d2c143a845e5886ba4f74b838c`). **No bad image ever deployed** — the
   build fails before push.

## Why this is a finding, not just "already handled"

The 2026-07-29 fix's own framing was that the retry-wrapper "hardens against the exact publish-ordering-race window
this doc tracks recurring on the next cross-repo floor-bump." It has now recurred **twice with ~13-min publication
gaps that exceed the ~45s budget** — this incident and the 2026-08-16 DataTypeConfig cascade (05:05→05:19Z gap,
documented in `/plans/active/issues/cloud_build_router_failure_escalation_undercoverage_2026_08_16.md`). The
mitigation's design envelope (short window, absorb-with-retry) is narrower than the observed recurrence gaps. Each
instance self-heals (the next build after the library publishes is green) and produces no bad image, so the impact is
transient build FAILURE noise + watcher pages — but a ~13-min gap is a repeating pattern, not a one-off.

## Disposition

Not fixed this pass — this is the wall-resolution (escalation `agt-1497fe`): the incident itself self-healed via the
uac publish, verified LIVE with a real SUCCESS build, so no forced code change was made (per the documented response
to this class: "verify LIVE and close out — don't force a redundant fix"). The OPEN question — whether the fleet's
~45s retry budget should be widened (8 affected Dockerfiles, build-time cost) vs. a release-ordering guarantee
(library publishes before dependent floor-bump builds fire, e.g. via the `update-dependency-version.yml` fan-out
ordering) vs. accept-and-re-alert — is a fleet-level judgment call, tracked as the single todo below.

## Todos

- [ ] [SCRIPT] P3. Decide the fleet-level response to the publish-ordering race recurring with ~13-min publication
      gaps that exceed the Dockerfile retry-wrapper's ~45s budget (exceeded on 2026-08-16 and 2026-08-20): widen the
      retry/backoff budget across the 8 affected Dockerfiles (build-time cost), OR add a release-ordering guarantee
      (library wheel published to GAR before dependent floor-bump builds fire), OR accept the transient-failure +
      self-heal behavior and just track it. Bounded investigation + judgment — operator / future /ci-reconcile pass;
      not a mechanical fix. Reference:
      /codex/06-coding-standards/dockerfile-standards.md § "uv pip install Retry Wrapper (BuildKit-secret GAR auth)".

## Progress Log

- 2026-08-20 ~11:35Z: Filed by cicd escalation `agt-1497fe` (slot 15) after verifying LIVE the wall self-healed —
  GAR now serves uac `0.149.0`; re-run of `fund-administration-service-build` on `main` (build `080f7c69`) SUCCESS;
  fresh `:latest` digest `sha256:039c738098...`. No code change shipped. Recurrence of the 07-29 race class with a
  gap exceeding the retry budget for the 2nd time.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries).

**na-eligibility-audit 2026-08-21** (ci tranche wave 2, first audit pass — doc filed 2026-08-20): KEEP-NA, valid.
Sole open todo is an explicit fleet-level policy decision (widen the ~45s retry budget across 8 Dockerfiles vs. add
a release-ordering guarantee vs. accept-and-track) — the doc's own Disposition section frames this as a judgment
call for "operator / future /ci-reconcile pass," not a mechanical fix. No `assigned_vm` change.
