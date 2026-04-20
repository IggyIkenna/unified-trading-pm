---
name: institutional-smoke-matrix
overview:
  Build a daily-runnable smoke matrix for every (service × category × data_type × venue) cell using TEST buckets +
  --max-results 1, in service-dependency order.
type: mixed
epic: epic-data-platform-honest-coverage
status: active

locked_by: live-defi-rollout
locked_since: 2026-04-20

completion_gates:
  code: C5
  deployment: D2
  business: B3

depends_on:
  - honest_coverage_metrics_2026_04_19
  - proper_coverage_roadmap_2026_04_20

todos:
  # ─── Phase 1 — TEST bucket plumbing across all services ─────────────────
  - id: phase-1-audit-is-test-run
    content: |
      - [ ] [AGENT] P0. Audit every service config for IS_TEST_RUN handling.
        Today only market-tick-data-service honours IS_TEST_RUN=true (routes writes
        to `-test-{project_id}` buckets). Audit all 9 services that write category-
        partitioned data: instruments-service, MTDS, MDPS, features-sports,
        features-calendar, features-onchain, features-delta-one, features-volatility,
        features-cross-instrument, features-multi-timeframe, features-commodity,
        ml-training-service, ml-inference-service. Per-service report:
        (a) does it read IS_TEST_RUN? (b) which bucket helper resolves the suffix?
    status: todo

  - id: phase-1-propagate-is-test-run
    content: |
      - [ ] [AGENT] P0. Propagate IS_TEST_RUN=true → `-test-` bucket suffix in every
        service config (per Phase 1 audit). Pattern: `MarketDataProcessingServiceConfig.is_test_run()`
        already exists — mirror that pattern in MarketTickDataServiceConfig (which
        does it differently today), InstrumentsServiceConfig, every features-*
        config, ml-* configs. Single SSOT: env var `IS_TEST_RUN=true` swaps the
        bucket suffix.
    status: todo

  - id: phase-1-create-test-buckets
    content: |
      - [ ] [SCRIPT] P0. Create `-test-` buckets for every category × service that
        doesn't have one yet. Use `gsutil mb -l asia-northeast1` per missing bucket.
        Naming convention: `{service-prefix}-test-{project_id}` (e.g.
        `market-data-tick-test-cefi-central-element-323112`,
        `instruments-store-test-sports-central-element-323112`). Required buckets
        listed in `dependencies.yaml`. Idempotent: skip if exists.
    status: todo

  - id: phase-1-gcs-lifecycle
    content: |
      - [ ] [SCRIPT] P0. GCS lifecycle policy on every `-test-` bucket:
        delete-after-7-days. Prevents test data from accumulating cost. Use
        `gsutil lifecycle set test-bucket-lifecycle.json gs://<bucket>` per bucket.
        Lifecycle config lives in `deployment-service/configs/test-bucket-lifecycle.json`
        (NEW). Add a verification CLI: `bash deployment-service/scripts/verify-test-bucket-lifecycle.sh`.
    status: todo

  - id: phase-1-dep-checker-test-mode
    content: |
      - [ ] [AGENT] P0. MDPS dependency_checker.py + every other service's dep-checker
        must honour IS_TEST_RUN=true → read from `-test-` buckets. The
        `UPSTREAM_DEPS_TEST` map in MDPS dependency_checker.py already exists for
        this purpose; just needs to be wired through (today it's only used when
        `test_mode=True` is passed to the constructor). Make `IS_TEST_RUN=true`
        env var auto-trigger test_mode.
    status: todo

  # ─── Phase 2 — per-service smoke matrix scripts ─────────────────────────
  - id: phase-2-instruments-smoke
    content: |
      - [ ] [AGENT] P1. instruments-service: `scripts/smoke_matrix.py`. Iterates
        every (category × venue × data_type) cell defined in UAC capability
        declarations. For each cell: invokes the service CLI with `--max-results 1`
        + `IS_TEST_RUN=true`. Asserts each cell wrote a manifest row with
        `capture_status=captured` OR `empty_confirmed`. Sub-CLI:
        `python -m instruments_service.smoke [--category X] [--venue Y] [--data-type Z]`.
        Returns rc=0 with per-cell pass/fail summary.
    status: todo

  - id: phase-2-mtds-smoke
    content: |
      - [ ] [AGENT] P1. market-tick-data-service: `scripts/smoke_matrix.py`. Same
        pattern as instruments. The existing `smoke_canonical_writes.sh` is a
        starting template (already uses IS_TEST_RUN=true) — extend to cover all
        categories + all data_types + cap to 1 instrument per venue.
    status: todo

  - id: phase-2-mdps-smoke
    content: |
      - [ ] [AGENT] P1. market-data-processing-service: `scripts/smoke_matrix.py`.
        Iterates every (category × data_type × timeframe) cell. Already supports
        `--max-results 1` (in cli/parser.py). Pre-flight: consume the smoke artefacts
        from MTDS + instruments-service smokes (test buckets). Asserts each cell
        produces a manifest row.
    status: todo

  - id: phase-2-features-smokes
    content: |
      - [ ] [AGENT] P1. features-* services (sports, calendar, onchain, delta-one,
        volatility, cross-instrument, multi-timeframe, commodity): each gets
        `scripts/smoke_matrix.py`. Pattern matches the per-(feature_service ×
        category) cells from `launch-features-backfill-vm.sh` (already documented
        the matrix in its header). features-sports smoke_test_single_day.py +
        features-delta-one smoke_test_single_day.py are starting templates.
    status: todo

  - id: phase-2-ml-smokes
    content: |
      - [ ] [AGENT] P2. ml-training-service + ml-inference-service: `scripts/smoke_matrix.py`.
        Pattern: train one model per (model_family × training_period) on minimal
        data + run inference on 1 instrument. Asserts manifest entries.
    status: todo

  # ─── Phase 3 — API Football dependency + sports ordering ────────────────
  - id: phase-3-api-football-dep-enforcement
    content: |
      - [ ] [AGENT] P0. instruments-service sports adapters MUST throw a clear
        error if api-football reference data hasn't been fetched yet for the date.
        Today the dep is silent — sports adapters that depend on api-football
        (footystats, SFI, etc.) read from instruments-store-sports/.../entity=
        ASSUMING the data is there. Add a pre-flight check + DependencyError with
        actionable message: "api-football reference data missing for date X.
        Run: python -m instruments_service --operation instruments --mode batch
        --category SPORTS --sports-provider API_FOOTBALL --start-date X --end-date X".
        Document in `codex/02-data/sports-adapter-dependency-order.md` (NEW).
    status: todo

  - id: phase-3-sports-internal-ordering
    content: |
      - [ ] [AGENT] P1. Document the sports-internal adapter dependency order:
        api-football (canonical fixtures + leagues) MUST run FIRST, then
        footystats/SFI/Understat/odds-api can run in any order (they depend on
        api-football's canonical fixture IDs). Codify in
        `codex/02-data/sports-adapter-dependency-order.md`. Add unit test that
        verifies the ordering invariant.
    status: todo

  # ─── Phase 4 — service dependency ordering for the smoke orchestrator ───
  - id: phase-4-orchestrator-dep-graph
    content: |
      - [ ] [AGENT] P0. deployment-service/scripts/run-smoke-matrix.sh — workspace
        orchestrator. Reads dependency DAG from `deployment-service/configs/dependencies.yaml`
        (already exists for prod batch ordering). Runs smokes in dep order:
        instruments-service FIRST → MTDS → MDPS → features-*. Per-service: parallel
        within a tier, sequential across tiers. Pass IS_TEST_RUN=true through the
        whole chain. Collects per-service pass/fail summaries → writes
        `playwright-artifacts/smoke-matrix-{date}.md`.
    status: todo

  - id: phase-4-cli-flags
    content: |
      - [ ] [AGENT] P0. Smoke orchestrator CLI:
        - `--service X` — smoke only one service (skips deps if their TEST buckets
          have valid data from a prior run, else prompts the operator)
        - `--category Y` — limit to one category (CEFI/TRADFI/DEFI/SPORTS/PREDICTION)
        - `--venue Z` — limit to one venue
        - `--data-type W` — limit to one data type
        - `--no-deps` — skip the dep cascade (assumes prior state in TEST buckets)
        - `--cleanup` — delete TEST bucket data after the run (overrides 7-day lifecycle)
        Default: full matrix in dep order.
    status: todo

  # ─── Phase 5 — codex playbook + CI integration ──────────────────────────
  - id: phase-5-codex-playbook
    content: |
      - [ ] [DOC] P0. codex/14-playbooks/smoke-testing-playbook.md (NEW): operational
        runbook for the smoke matrix. Covers: when to run (daily, pre-release,
        post-incident), how to read the per-cell summary, common failure modes
        (TEST bucket not provisioned, IS_TEST_RUN not propagated, dep order broken,
        api-football missing), how to retry a single cell, how to cleanup TEST data.
    status: todo

  - id: phase-5-gha-workflow
    content: |
      - [ ] [AGENT] P1. GHA workflow `.github/workflows/nightly-smoke-matrix.yml`
        in PM. Runs `bash deployment-service/scripts/run-smoke-matrix.sh --all` at
        02:00 UTC daily. Posts result summary to Slack #data-platform-ops. Gates
        production deployment workflows: a deployment to main can only proceed if
        the most recent smoke matrix is green.
    status: todo

  - id: phase-5-coverage-floor
    content: |
      - [ ] [SCRIPT] P2. Add per-(service × category) smoke coverage floor in
        `deployment-service/configs/smoke-coverage-floor.yaml`. Blocks merges that
        would lower the count of green smoke cells below the historical baseline.
        Pattern: same as coverage_ratchet_policy_2026_04_19 plan.
    status: todo

  # ─── Phase 6 — verification + handover ──────────────────────────────────
  - id: phase-6-end-to-end-validation
    content: |
      - [ ] [SCRIPT] P0. End-to-end validation: run `bash deployment-service/scripts/run-smoke-matrix.sh
        --all` from a clean state. Expected: every (service × category) cell
        produces a manifest row in its TEST bucket; final summary shows 100% green.
        Document the actual cell count + any deferred cells (e.g. ml-* if not yet
        ready) in this plan's note: field.
    status: todo

  - id: phase-6-archival
    content: |
      - [ ] [DOC] P1. Once Phase 6 validates green: archive this plan to
        `plans/archive/`. Update MEMORY.md with the smoke matrix invariants.
        Update CLAUDE.md Key Rules with the smoke matrix expectation.
    status: todo

isProject: true
---

## Context + motivation

Discovered 2026-04-20 during the SPORTS smoke incident: there is **no institutional smoke test matrix** across the
platform. Existing smoke coverage is fragmented:

| Service                           | Has smoke?                                    | TEST bucket support?                                  | `--max-results 1` support?    |
| --------------------------------- | --------------------------------------------- | ----------------------------------------------------- | ----------------------------- |
| instruments-service               | ❌                                            | ❌                                                    | ❌                            |
| market-tick-data-service          | ✅ (`smoke_canonical_writes.sh`, 3 cats only) | ✅ (`IS_TEST_RUN=true`)                               | partial (`--max-instruments`) |
| market-data-processing-service    | ❌                                            | partial (`UPSTREAM_DEPS_TEST` exists, not auto-wired) | ✅                            |
| features-sports-service           | ✅ (`smoke_test_single_day.py`, in-process)   | ❌                                                    | ❌                            |
| features-calendar-service         | ❌                                            | ❌                                                    | ✅                            |
| features-onchain-service          | ❌                                            | ❌                                                    | ✅                            |
| features-delta-one-service        | ✅ (`smoke_test_single_day.py`, in-process)   | ❌                                                    | ✅                            |
| features-volatility-service       | ❌                                            | ❌                                                    | ✅                            |
| features-cross-instrument-service | ❌                                            | ❌                                                    | ✅                            |
| features-multi-timeframe-service  | ❌                                            | ❌                                                    | ✅                            |
| features-commodity-service        | ❌                                            | ❌                                                    | ✅                            |
| ml-training-service               | ❌                                            | ❌                                                    | ❌                            |
| ml-inference-service              | ❌                                            | ❌                                                    | ❌                            |

**The blocker for `--max-results 1` everywhere**: writing to PROD buckets with partial shards corrupts the manifest
(row_count=1 when the real shard would have N rows) and breaks downstream features. The fix is to route smokes to
`-test-` buckets via `IS_TEST_RUN=true` — only MTDS does this today. Phase 1 of this plan propagates the convention to
every service.

**Service dependency order matters**: a meaningful smoke for MDPS requires MTDS smoke output to exist in TEST buckets. A
meaningful smoke for features-\* requires MDPS smoke output. The orchestrator (Phase 4) runs in dep order so each tier
consumes the prior tier's TEST artefacts.

**Sports has additional internal ordering**: api-football provides canonical fixture IDs that footystats / SFI /
Understat / odds-api adapters depend on. Today this dep is silent — adapters that read missing api-football data produce
empty results without explaining why. Phase 3 enforces it explicitly.

## Phased DAG

```
Phase 1 (TEST bucket plumbing — PARALLEL across services)
  ├── audit IS_TEST_RUN
  ├── propagate IS_TEST_RUN
  ├── create -test- buckets
  ├── GCS lifecycle (7d auto-delete)
  └── dep-checker test-mode wiring
       │
       │  every service writes to -test- when IS_TEST_RUN=true
       ▼
Phase 2 (per-service smoke matrix — PARALLEL)
  ├── instruments-service smoke
  ├── MTDS smoke
  ├── MDPS smoke
  ├── features-* smokes (8 services)
  └── ml-* smokes (2 services)
       │
       │  each service has a sub-CLI to run its own smoke
       ▼
Phase 3 (sports dependency enforcement — SEQUENTIAL with Phase 2)
  ├── api-football missing-data error
  └── sports-internal ordering doc
       │
       ▼
Phase 4 (workspace orchestrator — SEQUENTIAL with Phase 2+3)
  ├── dep-graph reader
  └── CLI flags (--service, --category, --venue, --data-type)
       │
       │  one command runs the full matrix or a slice
       ▼
Phase 5 (codex playbook + CI — PARALLEL after Phase 4)
  ├── playbook doc
  ├── GHA nightly workflow
  └── coverage floor
       │
       ▼
Phase 6 (end-to-end validation + archive)
```

## Success criteria

| Criterion                                 | Target                                                                   | Verification                      |
| ----------------------------------------- | ------------------------------------------------------------------------ | --------------------------------- |
| Every service honours `IS_TEST_RUN=true`  | 13/13 services route writes to `-test-` buckets                          | manual test per service           |
| Every `-test-` bucket has 7-day lifecycle | 100%                                                                     | `gsutil lifecycle get` per bucket |
| Per-service smoke matrix script           | 13/13 services have `scripts/smoke_matrix.py` (or `.sh`)                 | file exists                       |
| Workspace orchestrator                    | `bash deployment-service/scripts/run-smoke-matrix.sh --all` returns rc=0 | E2E run                           |
| API Football dep enforcement              | sports adapters throw `DependencyError` when api-football data missing   | unit test                         |
| GHA nightly smoke matrix                  | passes daily, posts to Slack                                             | GHA history                       |
| Coverage floor in CI                      | blocks merges that lower the green-cell count                            | CI history                        |

## Estimated effort + cost

| Phase                               | Sessions                            | Cost                                                               |
| ----------------------------------- | ----------------------------------- | ------------------------------------------------------------------ |
| Phase 1 (TEST bucket plumbing)      | 1 mega-agent (parallel per service) | $0 (local QG)                                                      |
| Phase 2 (per-service smoke scripts) | 2-3 agents (one per service tier)   | $0                                                                 |
| Phase 3 (sports dep enforcement)    | 1 agent                             | $0                                                                 |
| Phase 4 (orchestrator + CLI)        | 1 agent                             | $0                                                                 |
| Phase 5 (codex playbook + GHA)      | 1 agent                             | $0                                                                 |
| Phase 6 (E2E validation)            | 1 session                           | ~$5 GCE (one-time matrix run)                                      |
| **Daily ongoing cost**              | —                                   | ~$0.50/day GCE × 13 services × `--max-results 1` ≈ **~$1.5k/year** |

Total: **~5-7 focused agent sessions** + ~$1.5k/year ongoing matrix cost.

## Non-goals

- **No production smoke matrix.** This plan builds TEST-bucket smokes only. Production smokes (writes to PROD buckets,
  full shards, real adapters) remain a separate concern handled by the existing backfill infrastructure
  (launch-cefi-sharded-backfill.sh etc.) and the `proper_coverage_roadmap_2026_04_20` plan.
- **No new mocking infrastructure.** TEST buckets get real data from real adapter calls, just capped to 1 instrument per
  shard. The `--max-results 1` flag uses the same code path as production.
- **No unit-test additions.** This plan is about end-to-end smoke tests, not unit tests. Unit tests are owned by each
  service's `tests/unit/` and `quality-gates.sh`.
- **No replacement of existing smoke scripts.** The 3 existing smokes (MTDS canonical, features-sports single-day,
  features-delta-one single-day) remain. Phase 2 supersedes them with the new uniform pattern; the old ones get deleted
  after the new ones are proven.

## SSOT references

- Per-category bucket layouts: `codex/02-data/per-category-bucket-layouts.md` (defines what a smoke needs to write)
- Honest-coverage manifest schema: `codex/02-data/availability-manifest-and-data-status.md`
- VM tarball deployment: `codex/05-infrastructure/vm-tarball-deployment.md`
- Coverage roadmap (the broader operational sequence): `plans/active/proper_coverage_roadmap_2026_04_20.plan.md`
- Service dependency DAG: `deployment-service/configs/dependencies.yaml`
- CLI convention: `codex/06-coding-standards/cli-convention.md`

## Handover prompt for the next agent (copy verbatim)

```
Read this plan first: unified-trading-pm/plans/active/institutional_smoke_matrix_2026_04_20.plan.md

Pick the next undone P0 todo (in order: phase-1-audit-is-test-run,
phase-1-propagate-is-test-run, phase-1-create-test-buckets,
phase-1-gcs-lifecycle, phase-1-dep-checker-test-mode, then Phase 3 sports
ordering, then Phase 4 orchestrator).

Phase 1 todos can be one mega-agent that touches every service config in
parallel. Phase 2 smoke scripts can be 2-3 parallel agents (one per service
tier: T0 instruments, T1 MTDS+MDPS, T2 features-*).

Hard rules: live-defi-rollout branch, never --dep-branch, IS_TEST_RUN env
var honoured by every service config that writes data, --max-results 1
safe-by-default in all CLIs. Document each completion with the commit SHA in
the plan todo's note: field.
```
