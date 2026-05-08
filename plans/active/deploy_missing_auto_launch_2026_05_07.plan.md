---
name: deploy_missing_auto_launch_2026_05_07
overview:
  Successor plan to data_status_drilldown_shard_atom_alignment_2026_05_07 Phase 3 -- promote the Deploy-Missing flow
  from preview-mode (operator copies + runs the gcloud command) to auto-launch (deployment-api directly invokes the
  launcher script via gcloud). Requires deployment-api->gcloud security review + paired tarball-refresh wiring + per-VM
  observability + idempotency guards.
type: code
epic: epic-deployment
completion_gates:
  code: C5
  deployment: D3
  business: none
repo_gates:
  - repo: deployment-api
    code: C2
    deployment: D3
    business: none
  - repo: deployment-service
    code: C2
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C2
    deployment: none
    business: none
depends_on:
  - data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md
todos: []
isProject: false
related:
  - data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md
---

# Deploy-Missing auto-launch (preview -> auto)

## Why

Drilldown plan Phase 3 ships Deploy-Missing in **preview mode**: the operator clicks the button on a leaf shard,
deployment-api composes the surgical bash invocation
(`bash deployment-service/scripts/vm/launch-mtds-backfill-vm.sh --shard-key='cefi|BINANCE-FUTURES|trades|PERPETUAL|btcusdt|2024-03-04'`),
and the operator copies + runs from their own authenticated terminal. Same security boundary as today's manual
backfills.

The full UX -- one-click launch from the panel without leaving the browser -- requires deployment-api to invoke
`gcloud compute instances create` directly. That crosses a security boundary that wasn't authorized in the original
plan and needs explicit review before shipping.

## Pre-audit blast radius

**Security-boundary review** (deployment-api -> gcloud):

- The deployment-api Cloud Run service runs under
  `${PROJECT_NUMBER}-compute@developer.gserviceaccount.com` today. Adding `roles/compute.instanceAdmin.v1` (or the
  narrower `roles/compute.instanceAdmin.v1` scoped to a specific zone + image family + subnet) lets the API spawn VMs.
  The blast radius if the API is compromised:
  - Attacker can spawn arbitrary GCE VMs in the project (cost vector).
  - Attacker can pick any image including tarball-deployed ones (code-execution vector if tarballs aren't signed).
  - Attacker can target any subnet / VPC.
- Mitigations to declare in the security review:
  - Per-shard rate limiting on the endpoint (ceiling: N VMs per operator per hour).
  - Strict allow-listing of launcher scripts (only the registered SSOT in
    `deployment_api/services/deploy_missing.py:_SERVICE_LAUNCHER_SCRIPTS`).
  - Mandatory authenticated session + audit-log record per launch.
  - Pre-flight check that the shard_key is well-formed and references a real (service, asset_group, venue, day) tuple
    in the manifest.
  - Tarball signature verification at VM boot (the setup-data-pipeline-vm.sh side).

**Tarball-refresh wiring** (deployment-service):

- Backfill VMs pull code from `gs://deployment-scripts-${PID}/code/` tarballs at boot. If the operator clicks
  Deploy-Missing on a leaf right after pushing a fix, the new VM must boot the FIXED code, not the stale tarball.
- The existing `bash deployment-service/scripts/vm/create-code-tarballs.sh --all` is the human-driven refresh; the
  auto-launch endpoint must either (a) refuse to launch when the tarball is stale (tarball mtime < latest pushed
  commit), (b) auto-trigger the tarball-refresh step before the VM boot, or (c) accept a `--branch` arg + clone the
  branch fresh on the VM (skipping the tarball entirely; ~2min slower boot).
- Decision: option (b) — auto-trigger Cloud Build job that runs `create-code-tarballs.sh` ONLY for the asset_group
  scoped to the launcher; deployment-api waits for the Cloud Build to succeed before launching the VM.

**Per-VM observability** (paired with auto-launch):

- Every auto-launched VM gets a deployment-api-emitted `DEPLOY_MISSING_VM_LAUNCHED` event keyed on the shard_key,
  so operators in the unified-events UI can see the full chain: panel-click -> preview -> launch -> STARTED ->
  PROCESSING -> STOPPED, all correlated by the shard_key as correlation_id.
- The `no fire-and-forget VM launches` rule from CLAUDE.md applies: the launch-and-monitor pair MUST be one
  endpoint call (deployment-api blocks until at least the STARTED event is observed in the per-VM events bucket
  within 90s, fails the request loud otherwise).

**Idempotency**:

- Two operators can click Deploy-Missing on the same leaf simultaneously (race). Without dedup the API fires 2 VMs;
  with the per-VM shard isolation (`MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME`) the writes don't clobber, but
  the work is wasted and the rate-limiter trips faster.
- Mitigation: deployment-api checks for an in-flight VM with `prefix=mtds-shard-key-${hash(shard_key)}` before
  launching; returns the existing VM's status if found.

## Phased execution DAG

```
Phase 0 (security review)              Phase 1 (tarball-refresh wiring)
─────────────────────────              ──────────────────────────────
Operations sign-off on:           →   create-code-tarballs.sh -> Cloud Build trigger
  - IAM scope                          deployment-api waits for Cloud Build success
  - rate limits                        Stale-tarball detection logic
  - audit-log shape
                                          ↓
                                  Phase 2 (deployment-api endpoint)
                                  ──────────────────────────────────
                                  POST /api/data-status/deploy-missing-launch
                                  invokes gcloud compute instances create
                                  with --shard-key + per-VM env vars
                                  emits DEPLOY_MISSING_VM_LAUNCHED event
                                          ↓
                                  Phase 3 (UI button update)
                                  ──────────────────────────────────
                                  DeployMissingButton: preview-mode toggle
                                  + auto-launch confirmation modal
                                  + live-event tail panel keyed by shard_key
                                          ↓
                                  Phase 4 (codex docs + plan close)
                                  ─────────────────────────────────
```

## Phase-by-phase tasks

### Phase 0 — Security review (sequential, no QG gate)

- [ ] [audit] P0. Security review with operations on the deployment-api -> gcloud IAM scope. Document the IAM role
      shape (custom role with the minimal set of permissions, not `roles/compute.instanceAdmin.v1` blanket).
- [ ] [audit] P0. Audit-log shape decision: what gets logged on every Deploy-Missing launch (operator email,
      shard_key, launch timestamp, resulting VM name).
- [ ] [audit] P0. Rate-limit ceiling decision (per-operator, per-hour, project-wide).

### Phase 1 — Tarball-refresh wiring

- [x] [deployment-service] P0. New script
      `deployment-service/scripts/vm/refresh-tarballs-for-shard-key.sh <asset_group>` that wraps
      `create-code-tarballs.sh --asset-group X` and emits a `TARBALLS_REFRESHED` event when complete.
      (deployment-service@a620e1f — accepts CEFI/TRADFI/DEFI/SPORTS/PREDICTION/ALL; emits
      TARBALLS_REFRESH_REQUESTED / TARBALLS_REFRESHED / TARBALLS_REFRESH_FAILED to
      gs://{pid}-events/events/deployment-service/...; correlation_id =
      `tarball-refresh-<asset_group>-<RUN_TS>`. Smoke-tested via `--dry-run`.)
- [x] [deployment-service] P0. Cloud Build trigger that runs the refresh script when invoked via REST. Returns the
      build_id so the deployment-api can poll for success. (deployment-service@a620e1f —
      `cloud-build/refresh-tarballs.cloudbuild.yaml` invokable via
      `cloudbuild_v1.CloudBuildClient.create_build` or `gcloud builds submit
      --config=...`. Substitutions: `_ASSET_GROUP`, `_BRANCH` (default live-defi-rollout),
      `_BUCKET` (default deployment-scripts-${PID}). 30min timeout; HIGHCPU_8 machine.)
- [x] [deployment-api] P0. Pre-launch check: read the tarball's GCS object mtime, compare to
      `git rev-parse HEAD` of `live-defi-rollout`; if stale, kick the Cloud Build and wait for completion before
      proceeding. (deployment-api@faac20a — `deployment_api/services/tarball_staleness.py`:
      `TarballStalenessChecker.{get_tarball_mtime, compute_bundle_oldest_mtime, is_stale,
      trigger_refresh, poll_build, ensure_fresh}` + `RefreshResult` dataclass + Protocol-
      based mocking for the Cloud Build invoker. Bundle membership mirrors
      create-code-tarballs.sh per-asset_group lists. 27/27 unit tests pass; QG lint+
      basedpyright clean; 70.94% coverage. **Standalone module** — Phase 2 wires it into
      the auto-launch endpoint.)

### Phase 2 — deployment-api auto-launch endpoint

- [ ] [deployment-api] P0. New endpoint `POST /api/data-status/deploy-missing-launch` accepting `{service,
      asset_group, row_key, dry_run?}`. Invokes `gcloud compute instances create` via the existing
      cloud-builds-style helper.
- [ ] [deployment-api] P0. Per-shard idempotency: `prefix=mtds-shard-key-${hash}` in-flight-VM check returns the
      running VM rather than launching a new one.
- [ ] [deployment-api] P0. `DEPLOY_MISSING_VM_LAUNCHED` event emission keyed on shard_key as correlation_id; blocks
      the response until the per-VM `STARTED` event is observed within 90s.
- [ ] [deployment-api] P0. Rate limiter middleware enforcing the Phase 0 ceiling. Returns 429 when tripped.

### Phase 3 — UI auto-launch toggle

- [ ] [deployment-ui] P0. `DeployMissingButton` gains a "Launch now" action alongside "Copy command". The Launch
      flow shows a confirmation modal (operator must explicitly opt in per click) + a live tail panel that streams
      the per-VM events keyed on shard_key.
- [ ] [deployment-ui] P0. Operator-preference setting: default to preview-mode for new operators, opt-in to
      auto-launch via the operational config UI.

### Phase 4 — Codex docs + plan close

- [ ] [unified-trading-pm] P2. Extend `codex/02-data/data-status-drilldown-hierarchy.md` with the auto-launch flow
      diagram + the IAM scope reference.
- [ ] [unified-trading-pm] P2. Plan flips closeout once Phases 0-3 ship + a 7-day operational soak (no compromise
      events fired).

## Success criteria

- **Code gates:** `bash scripts/quality-gates.sh` passes on deployment-api + deployment-service.
- **Test gates:** Phase 2 endpoint integration test against a Tenderly-equivalent fork (non-prod project) confirms
  the auto-launch fires + the VM emits STARTED + STOPPED.
- **Security gate:** Phase 0 sign-off documented in audit log.
- **Operational gate:** 7-day prod soak with the auto-launch path enabled for at least one operator + zero
  unauthorized launches.

## Temporary states + their canonical follow-up plans

- Until this plan ships, Deploy-Missing stays in **preview mode** -- operators copy the command + run from their own
  terminal. That's the documented contract and is sufficient for the live-defi-rollout MVP. No silent fix-later.

## Out of scope

- Auto-launch for non-MTDS services (instruments-service / features-* / MDPS) -- those use different launcher
  scripts; once the MTDS path is proven, the same pattern extends with one new entry per service in
  `_SERVICE_LAUNCHER_SCRIPTS` in `deploy_missing.py`.
- Auto-cancel of in-flight VMs -- if the operator clicks Deploy-Missing on a leaf, then the same leaf gets captured
  by a different VM mid-fetch, the deploy-missing VM still completes and writes (idempotently safe per
  ManifestWriter CAS, just wasteful). Cancel-on-already-captured is a future optimization.

## References

- Parent plan: `plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md` (Phase 3 ships preview;
  this plan ships the auto-launch successor).
- Existing infrastructure:
  - `deployment-service/scripts/vm/create-code-tarballs.sh` (tarball refresh).
  - `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` (VM bootstrap).
  - `deployment-service/scripts/vm/vm_zombie_watchdog.py` (zombie detection — must learn the
    `mtds-shard-key-${hash}` prefix).
  - CLAUDE.md "no fire-and-forget VM launches" rule (verification protocol per VM).
  - CLAUDE.md "VM Naming Convention" section (must register the new prefix in `VM_PREFIX_TO_BUCKET`).

## DONE-2026-05-08 — Phase 1 (tarball-refresh wiring)

Tab 4 (`deploy-missing-tarball-refresh-tab`) shipped the full Phase 1 surface in one session.

**Code commits**:

- `deployment-service@a620e1f` — `feat(deployment-service): refresh-tarballs-for-shard-key.sh +
  Cloud Build trigger config (Phase 1)`
  - `scripts/vm/refresh-tarballs-for-shard-key.sh` — accepts CEFI/TRADFI/DEFI/SPORTS/PREDICTION/ALL;
    forwards to `create-code-tarballs.sh` with the right flag form; emits structured
    `TARBALLS_REFRESH_REQUESTED` / `TARBALLS_REFRESHED` / `TARBALLS_REFRESH_FAILED` events to
    `gs://{pid}-events/events/deployment-service/...` matching `base_service.py:159` SSOT.
    Smoke-tested via `--dry-run`.
  - `cloud-build/refresh-tarballs.cloudbuild.yaml` — Cloud Build trigger invokable via REST
    (`cloudbuild_v1.CloudBuildClient.create_build`) or CLI (`gcloud builds submit
    --config=...`). Substitutions: `_ASSET_GROUP`, `_BRANCH` (default `live-defi-rollout`),
    `_BUCKET` (default `deployment-scripts-${PROJECT_ID}`). 30-min timeout; `E2_HIGHCPU_8`.

- `deployment-api@faac20a` — `feat(deployment-api): tarball staleness checker + Cloud Build
  refresh trigger (Phase 1)`
  - `deployment_api/services/tarball_staleness.py` — standalone helper module (NOT
    route-wired). `TarballStalenessChecker` exposes `get_tarball_mtime`,
    `compute_bundle_oldest_mtime`, `is_stale`, `trigger_refresh`, `poll_build`,
    `ensure_fresh`. `RefreshResult` dataclass with status `FRESH` / `STALE_NO_TRIGGER`
    / `REFRESHED` / `REFRESH_FAILED` / `POLL_TIMEOUT`. Protocol-based indirection over
    GCS Blob + Cloud Build client so unit tests inject in-memory fakes. Naive datetime
    raises loud (no silent UTC-vs-naive bugs).
  - `tests/unit/test_tarball_staleness.py` — 27/27 tests pass; covers bundle membership,
    mtime read, oldest-mtime aggregation, staleness compare, trigger-then-poll
    orchestration, FRESH-skip-trigger, STALE-no-trigger gating, REFRESHED, REFRESH_FAILED,
    POLL_TIMEOUT.
  - `tests/unit/conftest.py` — pre-registered `tarball_staleness` on the fake services
    package, mirroring the `deploy_missing` / `data_status_hierarchical` pattern.

**Plan-flip commit**: PM@<TBD-this-commit>.

**Test gates**: deployment-api QG Pass 1 — 2406/2406 in-scope tests pass; coverage 70.94%
(gate 70%); ruff format + ruff check + basedpyright clean on new files. 1 pre-existing
failure on `tests/unit/test_empty_reason_breakdown.py` (writegate Phase 4.A; semver-rollout[bot]
2026-05-07) — exempt per CLAUDE.md temporary 2026-05-07 → 2026-05-09 QG-failure exception
on others' code.

**What's next**: Phase 0 security review (operator-owned) + Phase 2 endpoint wiring, both
gated on the security review's IAM scope decision. The Phase 1 helper API is intentionally
generic (`ensure_fresh(asset_group, latest_commit_timestamp)`) so the Phase 2 endpoint
just calls it; no API churn expected.

**Bonus deferred**: Phase 0 IAM-scope proposal not drafted in this session — operator
review is the gating activity, and a unilateral IAM proposal from a sub-agent without
operator alignment risks pre-empting the security review's decisions. Tab can pick this
up after the operator names a target IAM granularity.
