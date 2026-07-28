---
doc_type: issue
title:
  Service Dockerfiles are inconsistent + fragile — normalize the 9 Pattern-B services to the clean base-image form
  (Pattern A)
summary:
  "A local `docker build` of all 15 cloned Python service images (current code, amd64, against the current UTL base
  digest) split cleanly into **two build contracts**:"
status: open
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [
    alerting-service,
    execution-service,
    greeks-service,
    strategy-service,
    batch-live-reconciliation-service,
    fund-administration-service,
    market-data-processing-service,
    ml-service,
    trading-agent-service,
  ] # corrected 2026-07-14, was: [agent-orchestrator, alerting-service, client-reporting-api, deployment-service, features-service, instruments-service] (didn't match this doc's own body — the 9 real Pattern-B target repos named in the "Fan out the normalization" todo, line ~87 — verify-rerun-2 finding 57)
scope: [engineer, admin]
tags: [infrastructure, execution, refactor, consolidation, uac, verification]
related: [/plans/archive/2026_07/test_fleet_image_builds_from_current_code_2026_06_17.md]
created: 2026-06-17
parent_epic: deployment_and_user_management_master
priority: P2
source:
  [
    2026-06-17 fleet image-build validation
    (/plans/archive/2026_07/test_fleet_image_builds_from_current_code_2026_06_17.md) — local amd64 sweep of all 15
    Python service images surfaced two divergent Dockerfile build contracts,
  ]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
---

# Service Dockerfiles inconsistent — normalize Pattern B → Pattern A

> **For Ikenna** — surfaced while test-building every service image locally from current code. Not blocking anything
> live (the bespoke builds DO work on GCP via per-service cloudbuild staging) — it's a reproducibility/maintainability +
> image-size cleanup. A fleet Dockerfile normalization decision.

## What I found

A local `docker build` of all 15 cloned Python service images (current code, amd64, against the current UTL base digest)
split cleanly into **two build contracts**:

- **Pattern A — clean base-image (6 services):** `FROM unified-trading-library@<digest>` + `COPY . .` +
  `uv pip install --system --no-deps -e .`. Self-contained; all shared deps come from the base image. **Builds from a
  single-repo context with zero extra staging.** Repos: `instruments-service`, `client-reporting-api`,
  `deployment-service`, `features-service`, `market-tick-data-service`, `agent-orchestrator`. Image size **~3 GB**.

- **Pattern B — vendored-sibling (9 services):** also `FROM` the base, but then **re-vendors sibling repo SOURCES into
  the build context** (`COPY unified-api-contracts/ unified-trading-library/ …`) and runs `uv sync --frozen` against
  local path sources. Requires a **multi-repo build context** that cloudbuild assembles via a per-service
  `stage-siblings` step. And the staging is **per-service-bespoke**:
  - `alerting`, `execution`, `greeks` — vendor exactly **UAC + UTL** (build locally once those 2 are staged). ✅ proved.
  - `strategy` — vendors a **third** sibling: `COPY market-tick-data-service/`.
  - `batch-live-reconciliation` — `COPY configs/cloud-providers.yaml` (a file **not in the repo** — cloudbuild stages it
    from deployment-service/UAC).
  - `fund-administration`, `market-data-processing`, `ml`, `trading-agent` — `uv.lock` pins UAC at the **absolute path
    `file:///unified-api-contracts`** (filesystem root), so `uv sync --frozen` fails unless the sibling is at exactly
    `/unified-api-contracts`. Build-machine-absolute lock paths. Image size **~5.5–7 GB** (≈2× Pattern A, because the
    sibling sources are re-vendored + re-synced on top of a base that already contains them).

**Local-build result:** 9/15 build cleanly here (6 Pattern-A + alerting/execution/greeks); the other 6 each need their
own bespoke context replicated and were left GCP-authoritative.

## Why it matters

- **Fragility / reproducibility:** every Pattern-B service has its own implicit context contract (which siblings, which
  configs, which absolute lock paths). It only builds where that exact staging is reproduced (cloudbuild + the AWS
  buildspec) — local builds and any new CI path break until each service's staging is hand-replicated.
- **Image bloat:** Pattern-B images are ~2× the size for no benefit (the base already contains UTL+UAC; re-vendoring +
  `uv sync` just duplicates them). Bigger images = slower pulls, more registry storage, larger attack surface.
- **Maintenance tax:** the `uv.lock` absolute path pins (`file:///unified-api-contracts`) are especially brittle — they
  encode a build-machine filesystem layout into the lock.
- **Not a live outage** — they build + deploy today via GCP. This is debt, hence **P2**, not P0/P1.

## Recommended decision

**Normalize all 9 Pattern-B services to Pattern A** — `FROM base@digest` + `COPY . .` + `uv pip install --no-deps -e .`,
dropping the sibling `COPY`s, the `uv sync --frozen` against path sources, and the per-service `stage-siblings`
cloudbuild steps. The base image already carries UTL+UAC, so the service only needs its own code installed `--no-deps`.
Pattern A is proven (6 services) and yields self-contained, single-context, ~3 GB builds that work identically
local/GCP/AWS.

Open questions for the owner:

- Any Pattern-B service that genuinely needs a sibling NOT in the base (e.g. strategy ↔ market-tick-data-service)? If a
  service imports another _service's_ code, that's a separate tier violation to resolve (services integrate by contract,
  not import) — flag, don't paper over with vendoring.
- Sequencing: normalize one canary (e.g. `alerting`) end-to-end (Dockerfile + cloudbuild `stage-siblings` removal +
  green GCP build), then fan out.

## Follow-up todos

- [x] ✅ [DESIGN] P2. Decide + own the Pattern-A normalization (this doc). **DONE 2026-07-28** — operator ruling
      2026-07-27 (`june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED item 39): no more Ikenna/Harsh
      human-owner split, this is agent work. Agent owns it; decision = normalize to Pattern A exactly as this doc's own
      "Recommended decision" already specified (no design change needed, just execution).
- [x] ✅ [INFRA] P2. Canary-normalize `alerting-service` Dockerfile + cloudbuild to Pattern A; confirm green GCP build +
      ~3GB image. **DONE (pre-existing, verified 2026-07-28)** — alerting-service was ALREADY normalized to Pattern A by
      an earlier session (no separate canary commit found in this session; the repo's live `Dockerfile` +
      `cloudbuild.yaml` were read in full and confirmed Pattern-A shaped: `FROM base@digest` + `COPY . .` +
      `uv pip install --system --no-sources -e .`, zero `stage-siblings` step, zero vendored sibling `COPY`, zero
      `uv sync --frozen`/`file:///` absolute-path lock references). **Repo:** alerting-service.
- [x] ✅ [INFRA] P2. Fan out the normalization to the remaining 8 Pattern-B services. **6/8 already done pre-session,
      verified 2026-07-28; 2/8 (greeks, strategy) normalized + shipped this session; execution-service explicitly OUT OF
      SCOPE (being handled by a different concurrent agent, delta_proxy wire-in task — do not re-touch).** Verification
      method for all 8: read the live `Dockerfile` + `cloudbuild.yaml`/`cloudbuild.yml` in full and confirm (a) no
      `stage-siblings` cloudbuild step, (b) no `COPY unified-api-contracts/` / `COPY unified-trading-library/` / any
      other sibling-repo `COPY` into the build context, (c) no `uv sync --frozen` against local path sources / no
      `file:///` absolute lock-path references, (d) install is `uv pip install --system --no-deps|--no-sources -e .`
      relying on the base image for UTL+UAC. - **Already normalized, confirmed (no code change needed):**
      `alerting-service` (see canary todo above), `batch-live-reconciliation-service`, `fund-administration-service`,
      `market-data-processing-service`, `ml-service`, `trading-agent-service` — all 6 read in full, all 6 structurally
      Pattern-A per criteria (a)-(d) above. All 6 also show recent (2026-07-28, same-day)
      `chore(deps): refresh base-image digest pin` commits from the fleet's own digest-drift-sweep automation,
      confirming they are live/current, not stale reads. - **Normalized + shipped this session:** `greeks-service`
      (Dockerfile + cloudbuild.yaml, greeks-service@b82340ad) and `strategy-service` (Dockerfile + cloudbuild.yaml +
      buildspec.aws.yaml, strategy-service@7be73520) — both confirmed still Pattern-B at session start (`stage-siblings`
      step + `COPY unified-api-contracts/`/`COPY unified-trading-library/` +
      `uv sync --frozen --no-dev --no-install-project` against local path sources; strategy-service additionally
      vendored `market-tick-data-service/`, see the BUG todo below). Rewrote both Dockerfiles to the Pattern-A shape
      (`COPY . .` + `uv pip install --system       --no-sources -e .`, no sibling `COPY`s), removed the `stage-siblings`
      cloudbuild step from both `cloudbuild.yaml`s, and removed the dead `market-tick-data-service` clone from
      strategy-service's `buildspec.aws.yaml` pre_build. **Verification (real, not just structural read):** ran a
      genuine local
      `DOCKER_BUILDKIT=1 docker build --platform linux/amd64 --build-arg PROJECT_ID=central-element-323112` for both —
      both built clean (greeks-service 5.58GB, strategy-service 3.81GB — the latter down from the Pattern-B ~5.5-7GB
      class the parent validation doc measured, confirming the image-bloat fix). Ran the `import <pkg>` smoke + the
      credential-free mock-mode run check mirroring each repo's own cloudbuild operability-probe
      (`CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`) — both passed on the SECOND pass. **Found + fixed a real regression
      on the first pass**: strategy-service's mock pipeline crashed
      `PermissionError: [Errno 13] Permission denied: '/.local-dev-cache'` —
      `unified_trading_library.dev_paths       .get_workspace_root()` falls back to a `parents[2]`-from-`__file__`
      heuristic when `WORKSPACE_ROOT` is unset, which is install-layout-dependent: under the OLD Pattern-B venv install
      (`uv sync` into `/app/strategy-service/.venv/...`) it happened to resolve to a path still under `/app` (owned by
      `appuser`, writable); under the NEW Pattern-A `--system` install (UTL lives at `/app/unified_trading_library/`,
      baked into the base image) the same heuristic resolves to `/` (root, not owned by `appuser`) — confirmed this was
      genuinely masked-not-absent by checking recent real GCP Cloud Build history for strategy-service
      (`gcloud builds list`: repeated SUCCESS through 2026-07-28T05:26Z on the still-live Pattern-B Dockerfile,
      including its REQUIRED operability-probe step that exercises this exact mock-pipeline path). Fixed by pinning
      `ENV WORKSPACE_ROOT=/app/strategy-service` explicitly in the Dockerfile (decouples from the fragile heuristic
      entirely) — confirmed no other Pattern-A repo already sets this (none do; a latent cross-fleet gap that happens to
      only bite strategy-service today because it's the only cloudbuild operability-probe that actually invokes the full
      mock pipeline via `-m strategy_service` rather than a `--help` short-circuit; greeks-service has zero
      `WORKSPACE_ROOT`/`get_workspace_root` references in its own source, confirmed unaffected). Both `quality-gates.sh`
      green (greeks-service 74s, strategy-service 172s incl. 5629 tests passed) before shipping. - **Explicitly out of
      scope:** `execution-service` — a different concurrent agent owns it (delta_proxy wire-in task); not touched this
      session.
- [x] ✅ [BUG] P3. Investigate `strategy-service` vendoring `market-tick-data-service/` — confirm it's not a
      service↔service import (tier violation). **DENIED / FALSE ALARM — already resolved before this doc was even filed,
      confirmed 2026-07-28.** Three independent checks, all consistent: (1) `strategy_service/` source has ZERO
      `import market_tick_data_service` / `from market_tick_data_service` anywhere (grep across `.py` files in source +
      tests) — the only hit workspace-wide is a docstring comment in
      `strategy_service/engine/core/canonical_aave_borrow_index_provider.py` referencing the file path as documentation,
      not an import. (2) `pyproject.toml` `dependencies = [...]` has no `market-tick-data-service` entry, and `uv.lock`
      has no `market-tick-data-service` package entry at all. (3) `git log -p pyproject.toml` shows the actual
      dependency WAS removed on **2026-06-10** (commit `d1f5a6a8`, "refactor(deps): drop market-tick-data-service
      service-dep from strategy-service" — commit message: "strategy_service source never imports
      market_tick_data_service (verified 0 imports). The sole coupling was
      tests/position/integration/test_split_libraries.py::test_market_interface_import[...]"), which is BEFORE this
      issue doc was filed (2026-06-17). So at the time this doc's own investigation was written, the tier-violation
      concern was already moot — only the Dockerfile/cloudbuild's vendoring of the `market-tick-data-service/` SOURCE (a
      `COPY` + `stage-siblings` clone that was then immediately `rm -rf`'d post-`uv sync`, since `uv.lock` no longer
      referenced it) survived as vestigial dead weight, never cleaned up until this session's Pattern-A normalization
      removed it. **No separate issue doc filed** (per the findings-triage rule, only a CONFIRMED cross-repo bug gets
      its own doc; this is a confirmed non-issue with the fix already landed as a side effect of the normalization
      commit above) — verdict + evidence trail recorded here instead.

## Composes with

- Parent validation: `/plans/archive/2026_07/test_fleet_image_builds_from_current_code_2026_06_17.md` (findings log).
  (Was `plans/active/…` — repointed 2026-07-26, `/plan-reconcile` infra shard: the parent plan was archived; verified
  `ls plans/active/test_fleet_image_builds_from_current_code_2026_06_17.md` → no such file, and
  `find plans -name 'test_fleet_image_builds*'` → the single hit under `plans/archive/2026_07/`.)
- Tier/import architecture (no service↔service imports): `/codex/04-architecture/tier-and-import-architecture.md`.
- Canonical service cloudbuild template + STEP 5.22: `unified-trading-pm/scripts/...` / service `cloudbuild.yaml`.
