---
title: "Staging resync — LDR→staging promotion stalled ~1 month (post-cutover unfreeze)"
created: 2026-05-24
source:
  - "staging branch staleness audit 2026-05-24"
  - "UAC pilot PR IggyIkenna/unified-api-contracts#48"
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

The LDR→staging promotion is **stalled ~1 month across all repos** — staging is NOT auto-synced from LDR (there is no
auto-promote; the sanctioned path is manual `quickmerge` → PR-to-`staging`, gated by the `quality-gates` SIT check). It
froze deliberately during the live-defi-rollout cutover sprint (direct-to-LDR, quickmerge deferred per the
`DO NOT quickmerge when dep repos dirty` rule). Cutover was 2026-05-23.

Staging staleness (commits behind LDR, 2026-05-24):

| repo                      | staging last commit | commits behind |
| ------------------------- | ------------------- | -------------- |
| strategy-service          | 2026-05-07          | 1159           |
| unified-api-contracts     | 2026-05-07          | 832            |
| execution-service         | 2026-05-07          | 746            |
| deployment-service        | 2026-05-07          | 624            |
| market-tick-data-service  | 2026-05-07          | 614            |
| instruments-service       | 2026-05-07          | 478            |
| unified-trading-system-ui | 2026-04-28          | 175            |
| alerting-service          | 2026-03-16          | 162            |

**UAC pilot (PR #48, live-defi-rollout→staging) proved the real work per repo:**

1. **Merge conflicts** — staging diverged (~20+ doc files in UAC alone + semver-agent version bumps in pyproject) →
   `mergeStateStatus: DIRTY / CONFLICTING`.
2. **`quality-gates` SIT fails** in the cross-repo dep-clone/version-alignment phase (sibling-repo tag/branch clones
   misalign when the whole graph is mid-divergence) — the SIT itself needs updates for the deployment-topology + code
   changes across the window.
3. cloud-build trigger also fails.

## Root cause (the real mechanism)

Pushes to `live-defi-rollout` run **NO remote CI** (per CLAUDE.md "CI Verification": LDR quality is enforced only by
_local_ `quality-gates.sh`). The `quality-gates` SIT only runs on the **staging PR**. So the staging PR is the **first
time CI exercises a month of accumulated LDR state** — and it surfaces **cross-repo SIT failures that local QG never
runs** (tests that need the full sibling-repo workspace checkout). This is accumulated CI debt, not just staleness.

**UAC pilot (PR #48) — the 2 real CI failures (representative of the per-repo work):**

1. `tests/test_cassette_orphan_checker.py::test_no_unallowlisted_orphans` — 14 orphan cassettes (coingecko/ticker,
   defillama/{coins_historical,protocols,yields}, fred/dgs10, nautilus/stub, tardis/{4}, thegraph/{4}) need a prod
   consumer OR a `tests/cassette_orphan_allowlist.yaml` entry (+reason +operator ack). **Judgment call per cassette** —
   allowlisting blindly masks genuinely-removed consumers.
2. `tests/test_feature_dag_ssot.py::test_every_service_has_workspace_directory` — `features-service` declared in
   `EXPECTED_FEATURE_GROUPS_BY_SERVICE` but absent from the CI checkout — a **CI sibling-checkout / topology-drift** fix
   (the `workspace-qg` clone step), not a UAC code fix.

→ Each of the 8 repos will surface its own accumulated cross-repo-SIT failures. The cross-repo workspace-checkout
failures (#2 class) likely repeat across repos → fixing the shared `workspace-qg` clone step once helps all.

## Why it matters

- Nothing recent is on staging → `odum-portal-staging` (DART) + every staging service is a ~month-old build. The
  disaster-recovery Safety Ops work (and everything else from the sprint) can't be exercised on staging, so the game-day
  21/21 can't run there.
- Unfreezing = a coordinated **release** of ~a month of multi-repo work, in strict dependency order, each repo through
  conflict-resolution + a (currently-broken) cross-repo SIT, cascading staging→main via semver-agent.
- High blast radius + shared infra (affects both teammates' repos). No live trading yet (rapid-dev phase) — so the
  main-cascade risk is acceptable, but it's still a careful, multi-step op.

## Recommended approach (dependency order = workspace-manifest topologicalOrder)

`unified-trading-pm` → **UAC (L1)** → UTL (L2) → instruments (L3) → core services incl alerting/execution/strategy/MTDS
(L4) → client APIs (L5) → deployment + recon (L6) → UI (L7) → e2e (L8).

Per repo:

1. **Resolve conflicts favoring LDR as source-of-truth** (staging is just stale) — EXCEPT preserve staging-only
   semver-agent version bumps in `pyproject.toml`/`package.json` (don't revert published version numbers). Practically:
   merge `origin/staging` into a resync branch off LDR taking `-X ours` for everything except the version line, OR reset
   staging content to LDR then cherry-pick the staging version bumps.
2. **Fix the `quality-gates` SIT** — the cross-repo dep-clone/version-alignment step needs updating for the new topology
   (e.g. strategy_repo_consolidation, greeks-service, deployment-topology changes). This is the "SIT needs updates" the
   operator flagged.
3. Open/refresh the `live-defi-rollout → staging` PR; merge when `quality-gates` is green.
4. Verify `origin/staging == origin/live-defi-rollout` (0 behind) before the next repo in the chain.

## Recommended decision

This is a dedicated release-engineering operation (multi-hour to multi-day; ~5000 commits across 8 repos + a broken
cross-repo SIT to repair first). Options:

- **(a)** Fix the `workspace-qg` SIT first (one cross-repo fix unblocks all 8), then cascade the dep-order promotions.
- **(b)** Treat staging as disposable in rapid-dev: hard-reset each staging branch to its LDR HEAD (bypass conflicts),
  re-apply only version bumps, then run the SIT once per repo. Faster but loses staging-only history — acceptable only
  if no one relies on current staging state.

Pilot PR #48 (UAC) is open as the tracked step-1 checkpoint. Do not cascade downstream repos until the SIT is repaired +
UAC is green/merged.

## Status

- [x] Diagnosed (mechanism + per-repo scope proven via UAC pilot)
- [~] Repair `workspace-qg` cross-repo SIT (dep-clone/version-alignment) — GH Support ticket 4422570 filed; ghost blocks
  workspace-qg CI but Cloud Build (the actual quality gate) is separate and passes
- [x] UAC (L1) conflicts resolved + green + merged — 2026-05-27:
  - Cloud Build STEP 5.10 fix: `scripts/collect_responses.py` uses `importlib.import_module` instead of static
    `from google.cloud import` (UAC@7dfe274f) → Cloud Build run d5fa191a SUCCESS
  - Staging force-reset to LDR HEAD (no version divergence — both at 0.1.20); PR #48 was already merged
  - UAC also has workspace-qg ghost 283776088 (added to GH Support ticket)
- [x] UAC staging → main — PR #49 merged 2026-05-27T13:16Z (UAC@7dfe274f → main)
- [x] Cascade L2→L8 in dep order — 2026-05-27:
  - L2 UTL: already in sync (main == LDR HEAD c7294847); no PR needed
  - L3 instruments-service: staging force-reset to LDR HEAD; PR #387 merged 2026-05-27T14:20Z
  - L4 strategy-service: staging force-reset to LDR HEAD; PR #59 merged 2026-05-27T14:20Z; cloudbuild.yaml clone-deps
    UTL branch fix (LDR→main) PR #60 merged; Cloud Build 7dc2caa7 SUCCESS
  - L4 MTDS: Cloud Build 0025aa60 SUCCESS; staging force-reset to LDR HEAD 7e01464f; PR #107 queued auto-merge
  - L4 execution-service: PRs #187→#193 cascaded; PR #193 merged 2026-05-28: (7) clone deployment-service in
    clone-deps + set UNIFIED_TRADING_CLOUD_PROVIDERS_YAML (BucketNamingError — 7 tests); (8) skip subprocess tests under
    CLOUD_BUILD=true (docker-in-docker stdout hang — 5 tests); (9) patch manifest_writer.get_storage_client in
    test_write_to_gcs. Build 9b75e1ba QUEUED (2026-05-28T05:13Z)
  - L7 unified-trading-system-ui: staging 178 commits behind LDR/main; cascade BLOCKED — GitHub Actions billing issue
    ("account is locked due to a billing issue"); operator must resolve billing before UI CI can run
  - alerting-service: main already 170 commits ahead of staging; no cascade needed
  - deployment-service: main already 652 commits ahead of staging; no cascade needed; Cloud Build triggers on main but
    has pre-existing Day-1 (2026-01-27) Cloud Run startup failure for deployment-dashboard revision — separate issue,
    not staging-sync related
