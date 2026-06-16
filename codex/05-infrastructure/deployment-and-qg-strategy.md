---
scope: [engineer, admin]
title: Deployment + QG strategy SSOT
type: infrastructure
status: living
last_reviewed: 2026-05-17
owner: workspace-platform
---

# Deployment + QG strategy SSOT

**Created**: 2026-05-13 per operator + Ikenna + Harsh design discussion 2026-05-13 17:05-17:18 UTC. **Status**: SSOT for
deployment-method choice + QG-enforcement layering through 2026-05-23 cutover and beyond.

## Decision matrix — env × deployment method (HARD RULE)

**Tarball is a dev escape valve, NOT a production path.** Env-locked at the deployment-api + UI guard layer; not
operator-pickable in non-dev.

| Env         | Tarball                                    | Image (Docker via cloud-build) | Notes                                                                                                                                                                             |
| ----------- | ------------------------------------------ | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **dev**     | ✅ allowed (default for rapid iteration)   | ✅ allowed                     | tarball requires local QG green via `bash scripts/quality-gates.sh` + `act` pre-flight pass; image build runs async on tarball write so promoting dev→staging doesn't wait 20 min |
| **staging** | ❌ BLOCKED (UI guard + deployment-api 400) | ✅ REQUIRED                    | Tarball selection in staging requires explicit `--override-tarball-block` flag + audit log entry; default UI prevents it                                                          |
| **prod**    | ❌ BLOCKED (UI guard + deployment-api 400) | ✅ REQUIRED                    | Live trading on real wallets — no tarball ever; no override flag accepted                                                                                                         |

**Enforcement points**:

1. `deployment-api/.../deploy_endpoint.py` — env-aware deploy validation rejects tarball method for staging/prod with
   explicit error (P0 wire-in pending — see plan).
2. `deployment-ui/.../DeploymentForm.tsx` — env-aware UI guard greys out tarball toggle for staging/prod (per Ikenna's
   "2x2 matrix toggle" design).
3. Audit log on every tarball deploy attempt (success or rejection) for post-incident review.

## The 4-tier QG enforcement stack

QG runs at 4 points in the developer → production pipeline, each catching different failure classes:

### Tier 1 — Local pre-commit (fast, mandatory)

- `bash scripts/quality-gates.sh` on the repo (existing two-pass model per CLAUDE.md)
- Catches: lint, typecheck, codex provenance, missing-symbol, ruff
- Latency: 30s-3min depending on repo
- Discipline: developer/agent runs before every commit; CLAUDE.md "Pass 1" rule
- Enforced via prek hooks where configured

### Tier 2 — `act + docker` pre-push (medium-fast, recommended)

- Run GHA workflow locally via `act` in same Docker container that would push
- Catches: workflow-level integration failures, dependency resolution differences from local dev env,
  environment-variable wiring gaps
- Latency: 3-8 min depending on workflow
- Command pattern: `act -j quality-gates --container-architecture linux/amd64 -W .github/workflows/quality-gates.yml`
- **Known limitations** (verify per repo before relying on):
  - OIDC / WIF tokens don't work the same as GHA runners (test before using act for deploy-auth-dependent workflows)
  - Matrix builds sometimes flake
  - Some secrets unavailable in act runtime
  - **`act` pass ≠ CI pass guarantee** — treat as fast pre-flight, not certainty
- Discipline: run before push when changes affect deploy path; not strictly required for plan-doc commits

### Tier 3 — CI (canonical, mandatory)

- GitHub Actions runs on push to `main` / PR-to-main
- Catches: clean-runner integration, cross-repo coordination, semver-bump triggering, downstream dispatch
- Latency: 5-20 min per repo
- **The canonical QG status** — what `bash scripts/quality-gates.sh` should match
- Telegram bot reports CRITICAL on failure (CLAUDE.md "CI Verification After Every Push" rule)

### Tier 4 — Image build (cloud-build, gated)

- Triggers on merge to `staging` (and on `main` for release tags)
- Builds Dockerfile with pinned base image digest (NOT `:latest` tag — drift risk)
- Pushes to Artifact Registry:
  `asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/<service>:<version>` + `:<commit-sha>`
- **Image SHA = the cutover-window truth** — VMs run pinned image, not branch-following
- Verifies: full QG pass + integration tests + linting against final container
- Latency: 8-20 min per image (varies by service base size)

## The tarball flow (dev only)

Per `codex/05-infrastructure/vm-tarball-deployment.md` existing SSOT + operator clarifications 2026-05-13:

1. **Generation**: `bash deployment-service/scripts/vm/create-code-tarballs.sh <flag>` — refresh per code change
   (CLAUDE.md HARD RULE).
2. **Naming + manifest**:
   - Tarball name: `<repo>@<commit-sha>.tar.gz` (commit SHA in name, not just hash; pin tarball to git state)
   - Sibling manifest: `<repo>@<commit-sha>.manifest.json` containing
     `{repo, commit_sha, pyproject_version, git_status_clean: true/false, created_at, created_by}`
   - VM launcher reads manifest at start, asserts commit_sha matches expected, fails loud on drift
3. **GCS location**: `gs://${PROJECT_ID}-deployment-tarballs/<env>/<repo>/<commit-sha>.tar.gz` — env in path, not bucket
   name
4. **Local QG required before upload** — `bash scripts/quality-gates.sh` must pass; upload script refuses if local QG
   dirty
5. **Async image build trigger** — tarball write fires `cloud-build` async on same commit-sha. When tarball promoted
   dev→staging, image already exists. No 20-min wait.

## The act + docker pre-flight workflow (NEW design)

**Goal**: catch QG failures BEFORE the slow image push.

**Approach**:

1. Each repo's `.github/workflows/quality-gates.yml` is the SAME workflow CI runs.
2. `bash scripts/dev/act-preflight.sh <repo>` (NEW, to be authored) — runs `act` against the QG workflow in the repo's
   docker container, using a pinned `act-runner-image`.
3. Pre-push git hook (optional, opt-in): run `act-preflight.sh` and refuse push on fail.
4. Manual invocation: developer runs `act-preflight.sh <repo>` before push when uncertain.

**Discipline boundary**: `act + docker` is a productivity tool, NOT a replacement for Tier 3 CI. CI remains the
canonical status; `act` reduces the false-positive push count.

## Image base-pinning (audit + ratchet)

Per CLAUDE.md Dockerfile rules + this SSOT codification:

- **Banned**: `FROM python:3.13-slim` — base image drifts under tag
- **Banned**: `FROM gcr.io/.../base:latest` — same drift problem
- **Required**:
  `FROM asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest` — but pin
  to SHA digest in cutover-window

**Cutover-window discipline** (2026-05-15 → 2026-05-23): pin all production Dockerfiles to a digest, not a tag. Audit
script: `bash deployment-service/scripts/audit/dockerfile-base-pin.sh` (NEW) walks all Dockerfiles + flags any using
`:tag` instead of `@sha256:digest` for production-bound services.

## Artifact Registry retention policy

Image storage grows fast. Without a retention policy: ~50 services × ~5 commits/day × 14 days = ~3,500 images at ~200 MB
each = ~700 GB on Artifact Registry. At $0.10/GB-month = ~$70/month and growing. Set policy now:

- **Keep forever**: every release tag (`v1.0.0`, `v1.0.1`, etc.) — operator can roll back to any release
- **Keep 14 days**: every `:<commit-sha>` image — recent dev iteration
- **Keep 3 days**: every `:branch-<branch>` image — feature-branch builds
- **Delete immediately on PR close**: PR-specific images

Implementation: `deployment-service/scripts/audit/artifact-registry-retention.sh` (NEW) or use Artifact Registry's
built-in cleanup policies. Set as a Cloud Scheduler weekly cron.

## Version-bump frequency model

Per CLAUDE.md "Version Graduation" + semver-agent:

- Every merge to `staging` bumps PATCH (semver-agent auto)
- Every `feat!` on 0.x.x bumps MINOR (pre-1.0.0 override)
- Every `feat!` on 1.0.x+ bumps MAJOR (requires `/approve` issue)
- **Bump → image build**: yes, every staging-branch merge fires cloud-build
- **Tarball flow**: dev iteration uses tarballs (no image churn); staging-merge fires image
- **Cost**: ~5 deploys/day during cutover × ~50 services = ~250 builds/day worst case. At $0.003/build-min × 10 min =
  ~$7.50/day. Trivial vs live-trading capital at risk.

## 99%-repo identification (per Harsh's suggestion)

**Goal**: don't gate the whole pipeline on the slowest repo. Identify repos that are deployment-ready NOW + pipeline
them while laggards catch up.

**Method**:

1. Daily QG-status snapshot: `bash unified-trading-pm/scripts/quality_gates/snapshot.sh` (NEW) walks all repos + runs
   `bash scripts/quality-gates.sh` per repo with `--quick` flag (skip slow integration tests if any) + writes
   `quality_gates_snapshot_YYYY_MM_DD.parquet` to GCS.
2. Inventory table: `Repo | Pull SHA | QG status | Failing step | First-error-line | Last-green-date`
3. **99%-repo criterion**: 5+ consecutive days of QG green + zero P0 issue docs open + no in-flight refactor banner on
   the repo's plans.
4. Pipeline: identified repos go on the image-build path TODAY; laggards stay on tarball until they hit the criterion.
5. Tracking surface: deployment-ui dashboard surfaces per-repo readiness (extend
   `deployment_ui_lifecycle_tabs_2026_05_08.md`).

## Cutover-window sequence (codifies the 2026-05-13 → 2026-05-23 plan)

| Day | Date                    | QG/Deployment action                                                                                                                   | Owner                                           |
| --- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| 1-3 | 2026-05-13 → 2026-05-15 | All repos to QG-green on LDR; parallel coverage-raise; identify 99%-repos; wire `act + docker` pre-flight                              | per-repo slot (root deps serial, leaf parallel) |
| 4   | 2026-05-16              | Cloud-build async image build per commit-to-main on 99%-repos; tarball stays as dev escape valve                                       | deployment-service slot                         |
| 5-6 | 2026-05-17 → 2026-05-18 | Rest of repos hit QG-green; CI/CD on main fully passing; image builds caught up for all services; UI env-locking shipped               | governance + deployment-ui slots                |
| 7-8 | 2026-05-19 → 2026-05-20 | Staging deploys go image-only; tarball blocked in staging via UI guard; dress rehearsal uses image path end-to-end                     | governance + deployment-api slots               |
| 9   | 2026-05-22              | Prod deploys go image-only; pre-cutover sign-off includes "all production VMs running pinned image SHA" check in `credential-probe.sh` | slot 1 main + operator                          |
| 10  | 2026-05-23              | Cutover on image-only prod path; tarball available in dev for hotfix iteration only                                                    | operator                                        |

## Parallelization model — root vs leaf

Per operator clarification 2026-05-13: PM + UAC + deployment-service are root dependencies that all leaf services touch.
**Per-repo parallelism is NOT independent**.

**Serial slots** (one slot at a time, never fan out):

- `unified-trading-pm` — plan + codex edits; index contention
- `unified-api-contracts` — schemas + UAC registries; downstream consumer breaks if wrong
- `deployment-service` — VM launchers + scripts; affects every cutover VM

**Parallelizable across leaf services** (one slot per service, no cross-service shared files):

- `mtds`, `mdps`, `execution-service`, `instruments-service`, `strategy-service`
- `position-balance-monitor-service`, `risk-and-exposure-service`, `pnl-attribution-service`, `alerting-service`
- `client-reporting-service`, `batch-live-reconciliation-service`
- `features-onchain`, `features-sports`, `features-volatility`, `features-cross-instrument`, `features-delta-one`,
  `features-commodity`, `features-calendar`, `features-multi-timeframe`
- `ml-training`, `ml-inference`
- `deployment-api`, `deployment-ui`, `unified-trading-system-ui`, `user-management-ui`

**Coverage-raise spawn pattern** (Harsh's "mechanical parallel sonnets"):

- 1 sub-agent per leaf service (not per-folder within a service; index contention)
- Root-dep coverage raises happen in dedicated single-slot session
- Per-tab worktrees (CLAUDE.md per-tab-worktrees infra) for any case where multiple agents must touch the same repo
- Pre-commit check (CLAUDE.md `Commit + Push + Flip` Half 1 mandatory pre-commit check) catches accidental cross-agent
  bundling

## QG complexity (C901) policy — UAC carveout (operator decision 2026-05-13)

**Closed-set decision** locked 2026-05-13 — encoded here as workspace SSOT for the C901 lint rule:

| Layer                                                                                                                                      | Policy                                                                                                                                                                                                                                                      | Rationale                                                                                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **UAC** (`unified-api-contracts/**`) — registry + capability_declarations + internal/architecture_v2 + canonical/crosscutting enumerations | **Blanket C901 ignore via `[tool.ruff.lint.per-file-ignores]`** in UAC `pyproject.toml`. Per-file rationale comment required at top of any file added to the ignore list.                                                                                   | UAC is registry/declarative, not algorithmic. `KNOWN_VENUE_TOKENS`, `STRATEGY_FAMILY_REGISTRY`, `paired_dispersion_catalog`, `capability_declarations/*`, `ARCHETYPE_CONFIG_SEED`, `VENUE_DATA_TYPE_CAPABILITIES` enumerate closed sets. Lowering complexity = artificial extraction that fragments registry view + harms grep-ability. |
| **UTL** (`unified-trading-library/**`)                                                                                                     | Mixed — extract-method where genuine; `# noqa: C901` with per-line rationale where legitimate orchestrator (e.g., `ManifestWriter._check_cluster_coverage` orchestrating bundled-shard validation gates is legitimately complex).                           | UTL is library + orchestration boundary; some functions are pipeline-stages that must stay linear for audit clarity.                                                                                                                                                                                                                    |
| **Service code** (`*-service/**`, `deployment-api/**`, `deployment-ui/**`, etc.)                                                           | Mixed — extract-method where the function does multiple concerns; `# noqa: C901` with rationale where genuine orchestrator (e.g., `submit_manual_instruction`, `_build_leaf_parquet_candidates` — both legitimately need linear audit-trail readable flow). | Most C901 in service code is real complexity that should be decomposed; some are genuine orchestrators.                                                                                                                                                                                                                                 |
| **Test code** (`tests/**`)                                                                                                                 | `noqa: C901` permitted freely; test setup often has linear setup-then-act-then-assert that mirrors the unit under test.                                                                                                                                     | Tests measure code, they're not the code.                                                                                                                                                                                                                                                                                               |

**Threshold itself**: current C901 threshold is 7 in some repos (very tight) and 10 in others (default). Operator may
consider raising back to 10 in a future cycle if mixed-approach leaves too many legitimate orchestrators carrying `noqa`
comments. **Action item**: harmonize threshold to 10 workspace-wide via QG STEP base-service.sh (deferred — not blocking
May-23).

**Long-term direction**: complexity is a structural-coupling proxy, not a correctness check. The real correctness gate
is test coverage on the function (Phase 8 target = 100% on validation + orchestrator surfaces). A C901 orchestrator at
95% test coverage is safer than an extract-method-split orchestrator at 60% test coverage.

## Open risks

| Risk                                                                                                                  | Likelihood                                 | Mitigation                                                                                             |
| --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| `act + docker` doesn't cover OIDC/WIF for deploy-auth workflows                                                       | HIGH                                       | Test per workflow before relying on act; document workflow-by-workflow coverage; treat as 80% solution |
| Image storage costs balloon without retention policy                                                                  | MEDIUM                                     | Ship retention policy in cutover-window Phase 4 (Day 5-6)                                              |
| CI/CD bot attribution race (Foot-gun #1) — semver-rollout[bot] hijacks author when prek + parallel-agent push collide | HIGH (already observed twice 2026-05-13)   | Track commit SHA, not author; expect bot attribution; don't escalate over author drift alone           |
| Tarball SHA drift (what's on GCS vs what's expected)                                                                  | MEDIUM                                     | Sibling `manifest.json` + VM launcher SHA assertion; fail loud                                         |
| `:latest` tag drift in production base images                                                                         | LOW (banned per CLAUDE.md but worth audit) | `dockerfile-base-pin.sh` audit script; ratchet via QG STEP                                             |

## Cross-references

- **Cutover-window timeline** (companion):
  [`codex/08-workflows/cutover-window-dependency-order.md`](../08-workflows/cutover-window-dependency-order.md)
- **VM tarball deployment SSOT** (existing):
  [`codex/05-infrastructure/vm-tarball-deployment.md`](vm-tarball-deployment.md)
- **VM launcher script SSOT** (existing): [`codex/05-infrastructure/launcher-script-ssot.md`](launcher-script-ssot.md)
- **Runtime tiers + deployment** (existing):
  [`codex/05-infrastructure/runtime-tiers-and-deployment.md`](runtime-tiers-and-deployment.md)
- **Promote workflow May-23 CLI plan**:
  [`plans/active/promote_workflow_may23_cli_path_2026_05_10.md`](../../plans/active/promote_workflow_may23_cli_path_2026_05_10.md)
  — wires in the env-locking enforcement + 99%-repo identification
- **Promote workflow post-cutover UI plan**:
  [`plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`](../../plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md)
  — full UI pipeline build
- **Governance HARD RULE automation + QG ratchet** (pulled-forward to May-23):
  [`plans/active/governance_qg_automation_gaps_post_cutover_2026_05_12.md`](../../plans/archive/governance_qg_automation_gaps_post_cutover_2026_05_12.md)
  — wires audit scripts (`dockerfile-base-pin.sh`, `artifact-registry-retention.sh`, `snapshot.sh`)
- **MVP universe**:
  [`codex/09-strategy/mvp-universe-per-asset-group.md`](../09-strategy/mvp-universe-per-asset-group.md)

## Phase 8.A — VM infrastructure hardening (shipped 2026-05-15)

Four patterns shipped in the B-011 / Phase 8.A slot sweep that are now canonical:

### VM launcher DRY library (`launcher_common.sh`)

`deployment-service/scripts/vm/lib/launcher_common.sh` — 6 shared functions: `lc_validate_env`, `lc_singleton_check`,
`lc_gcloud_create`, `lc_code_bucket`, `lc_run_ts`, `lc_write_startup_file`.

**Rule**: every new launcher MUST source `lib/launcher_common.sh` and use these functions instead of inline boilerplate.
New launchers that inline `gcloud compute instances create` without `lc_gcloud_create` are QG-blocking (review enforced,
no automated gate yet — future QG STEP candidate).

Template reference: `scripts/vm/templates/startup-gcs-url.sh.tmpl` (GCS-URL pattern, ~61 launchers) and
`scripts/vm/templates/startup-inline-heredoc.sh.tmpl` (inline HEREDOC, ~31 launchers).

### VM security hardening audit

Shellcheck sweep at `--severity=error` on all 83 `launch-*.sh` launchers (see
`codex/05-infrastructure/vm-security-audit.md`):

- **P0 hardcoded credentials**: 0 found (clean)
- **P0 curl-pipe-bash**: 0 found (clean)
- **P1 SC2046 (flag injection)**: fixed `launch-amm-golden-fixture-validation-vm.sh` (3 vectors → `EXTRA_FLAGS=()`
  array)
- **P2 SC2034 (unused vars)**: 11 removals across 9 launchers

New launchers must pass `shellcheck --severity=warning` before merge. QG `TestShellcheckClean` enforces at
`--severity=error` (warning-level is informational).

### VM deployment-events pubsub gap

Audit completed; findings in `codex/05-infrastructure/vm-deployment-events-audit.md`:

- `vm-heartbeat-daemon` uses `PubSubEventSink` (7-day TTL) — all other services use `GCSEventSink` for permanent
  archival.
- No GCS export subscription on `deployment-events` topic → heartbeat events expire after 7 days.
- **Recommended action** (non-blocking May-23, P2): switch `heartbeat_cli.py` to `GCSEventSink` or add a GCS export
  subscription on the `deployment-events` Pub/Sub topic.

### VM zombie watchdog per-prefix thresholds + notification

`vm_zombie_watchdog.py` now supports:

- `PREFIX_IDLE_THRESHOLDS`: per-prefix `(heartbeat_stale_min, shard_stale_min)` overrides (longest-prefix match).
  Live-service VMs tolerate longer idle periods (30/240 min); backfill VMs use shorter thresholds (10/60 min).
- `--notify-url`: webhook POST (Slack-compatible) on zombie detection. Best-effort — never blocks kill loop.
- Both features wired: thresholds applied per-VM in `_evaluate_vm()`; notification fires before kill loop (even under
  `--dry-run`).

### GCS lifecycle gap (operator action required)

`vm-logs/` prefix: 4,130 dirs, no lifecycle purge, growing ~1,800/year. Watchdog `gsutil ls` latency grows with this.
See `plans/active/issues/deployment_events_lifecycle_audit_2026_05_15.md` for the 3 `gsutil lifecycle set` commands
needed (14d vm-logs, 30d QG snapshots, 90d events). Non-blocking May-23 (P2) but recommended before cutover.

## Continuous verification

This SSOT is read at slot 1 main morning ledger sweep daily through 2026-05-23. Updated on:

- New deployment method discovered or evaluated
- act/docker workflow limits hit in practice
- Image-build / tarball cost or speed observed beyond planned
- Production incident post-mortem

Last reviewed: 2026-05-15. Next review: 2026-05-17 (post 99%-repo image-build + honest-coverage cron verification).

**2026-05-15 additions**:

- Honest-coverage cron VM: Cloud Scheduler → Cloud Run Job → GCE VM pattern canonised. SSOT: `launcher-script-ssot.md` §
  "Honest-coverage cron VM". Terraform: `deployment-service/terraform/gcp/honest_coverage_scheduler.tf`.
  BLOCKED-OPERATOR-DECISION: Cloud Scheduler creation pending Ikenna (cloudscheduler.jobs.create IAM).
- B-011 blindspot audit complete: 8 VM_PREFIX_TO_BUCKET entries registered; 0 known watchdog blindspots. Watchdog
  relaunched: `vm-zombie-watchdog-20260515-110711`. SSOT: `launcher-script-ssot.md` § "B-011 blindspot audit".
- **B-014 Phase 3 QG ratchet rollout** (2026-05-13 → 2026-05-15): All 15 service repos received
  `scripts/quality-gates.sh` with `MIN_COVERAGE=70` floor + SSOT path
  `unified-trading-pm/codex/06-coding-standards/quality-gates-service-template.sh` + lifecycle enforcement block. STEP
  5.79-5.82 (dockerfile-base-pin, tarball-manifest-present, tarball-env-block, image-build-on-staging-merge) are
  `PENDING_RATCHET` — they run post-compliance-check and show ❌ cosmetically but do NOT block the
  `✅ ALL QUALITY GATES PASSED` verdict.

  > **[DELTA 2026-05-22]** Phase 5 target date was 2026-05-17 (5 days ago). Actual status of PENDING_RATCHET steps
  > (5.79-5.82) has NOT been verified as of 2026-05-22 — verify per-repo QG output before assuming advisory-only.
  > Tracked under `plans/epics/infrastructure_master.md`.

  Plan: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md`. STEP SSOT:
  `codex/06-coding-standards/quality-gates.md` §§ 5.79-5.82.

- **B-018 Phase 4.A QG snapshot cron** (2026-05-15): Daily QG-status snapshot (described at § "99%-repo identification"
  above) implemented as `unified-trading-pm/scripts/quality_gates/snapshot.sh` + `check_snapshot_staleness.py`. VM
  prefix: `qg-snapshot` (registered in `vm_zombie_watchdog.py:VM_PREFIX_TO_BUCKET`). GCS output:
  `quality_gates_snapshot/` prefix in deployment bucket. Launcher:
  `deployment-service/scripts/vm/launch-qg-snapshot-vm.sh`. Scheduler: BLOCKED-OPERATOR-DECISION (Cloud Scheduler IAM
  same as honest-coverage cron above). Plan: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` §
  Phase 4.A.

## Phase 9 — Deployment API endpoint extensions (shipped 2026-05-15)

Phase 9 added 10 deployment-api endpoints + 5 deployment-ui routes that are now canonical workspace surfaces. Full
endpoint table in `codex/05-infrastructure/deployment-ui-architecture.md` § "Phase 9 shipped patterns".

**Key additions**:

- 4 VM-launch endpoints (`/api/backfill/launch`, `/api/ml/experiment/launch`, `/api/strategy/backtest/launch`,
  `/api/execution/backtest/launch`) — each fires the canonical launcher in `deployment-service/scripts/vm/` and returns
  VM name + launch metadata.
- WebSocket VM event streaming (`/ws/vm/{vm_name}/events`) — polls GCS events bucket every 5s; used by
  `/ops/live-deployments` real-time panel.
- Prometheus telemetry (`/metrics`) — 5+ counters; standard exposition format; Grafana-compatible.
- Firebase ID token auth middleware on all endpoints (deployment-api@299908f); per-IP rate limit 60 req/min
  (deployment-api@e968719).
- `/research/*` routes (ml-experiments, strategy-backtests, execution-backtests) and DART terminal stub.

**Implication for new endpoints**: any new `deployment-api` endpoint MUST (a) accept Firebase ID token, (b) be covered
by the rate-limit middleware, (c) appear in `/api/openapi.json`, (d) have a unit test for auth valid/expired/missing.
These are now workspace defaults — not optional add-ons.

**Phase 10 venue admission** (strategy-service): codex updated by slot 3/11 at `codex/09-strategy/` —
`batch-live-architecture.md` + `carry-recursive-borrow-perp-hedged.md`; drift findings in
`plans/active/issues/strategy_service_phase10_codex_drift_2026_05_15.md`. No `codex/05-infrastructure/*` gaps found for
venue admission (infra surfaces are neutral to venue admission logic).
