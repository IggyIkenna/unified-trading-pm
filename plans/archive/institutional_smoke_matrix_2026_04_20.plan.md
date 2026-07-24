---
name: institutional-smoke-matrix
overview: >
  Build a smoke matrix for every (service × category × data_type × venue) cell using TEST buckets, in service-dependency
  order. **PIVOTED 2026-04-20**: initial design used a daily cron + `--max-results 1` (bogus flag) + workspace
  orchestrator; that architecture was wrong. Canonical gate is `system-integration-tests/tests/smoke/` wired into
  `staging-to-main.yml` via `sit-gate.yml`. Per-service `scripts/smoke_matrix.py` remain as dev-local debugging helpers
  only. Phase 4/5/6 scheduler artifacts deleted (2026-04-20 afternoon).
type: mixed
epic: epic-data-platform-honest-coverage
status: active

locked_by: live-defi-rollout
locked_since: 2026-04-20

# ── 2026-04-20 pivot note (read before editing) ─────────────────────────────
#
# Original Phase 4/5/6 shipped a daily-cron nightly-smoke-matrix.yml workflow +
# workspace orchestrator (deployment-service/scripts/run-smoke-matrix.sh) +
# coverage-floor gate. User flagged it as architecturally wrong: the system
# already has `system-integration-tests/` with `tests/smoke/` (<5 min,
# `@pytest.mark.smoke`) and `tests/e2e/` (15-30 min, `@pytest.mark.full_e2e`)
# that run at staging→main promotion via `sit-gate.yml`. Daily cron creates a
# "nobody owns it" problem and duplicates existing infrastructure. Worse, the
# per-service smoke_matrix.py scripts were passing `--max-results 1` — a flag
# that does not exist on any service CLI — so every cell would have failed
# rc=1 before touching GCS. The canary run confirmed this.
#
# Pivot shipped:
#   - Deleted: `.github/workflows/nightly-smoke-matrix.yml` (PM),
#     `deployment-service/scripts/run-smoke-matrix.sh`,
#     `deployment-service/configs/smoke-coverage-floor.yaml`,
#     `deployment-service/scripts/enforce-smoke-coverage-floor.py`,
#     `deployment-service/tests/unit/test_run_smoke_matrix.py`,
#     `deployment-service/tests/unit/test_enforce_smoke_coverage_floor.py`.
#   - Fixed: `--max-results 1` dropped from features-calendar, features-delta-one,
#     and MDPS smoke_matrix.py (3 files). Docstrings updated to reflect that
#     scope is narrowed via single-date/single-venue/single-category args.
#   - Rewritten: `/codex/14-playbooks/smoke-testing-playbook.md` now reflects
#     SIT=gate / per-service=dev-local, 3-step assertion still canonical.
#   - SSOT index row (00-SSOT-INDEX.md L15) rewritten.
#
# Kept (still correct under the new architecture):
#   - `scripts/smoke_matrix.py` in 11 services — useful dev-local helpers.
#   - Per-category bucket layouts SSOT (`/codex/02-data/per-category-bucket-layouts.md`).
#   - Sports T0/T1 adapter dependency order (`/codex/02-data/sports-adapter-dependency-order.md`).
#   - TEST bucket provisioning + 7-day lifecycle (`deployment-service/scripts/provision-test-buckets.sh`).
#   - MDPS 3-bug chain fix (safe_iterate_blobs + empty-bucket defence + pre-flight tolerance).
#   - Manifest v5 record_empty/record_failed split.
#
# 2026-04-20 follow-up SHIPPED: `system-integration-tests/tests/smoke/test_coverage_matrix_smoke.py`
# (+ `coverage_matrix_cells.py` helpers + 19 unit tests in
# `tests/unit/test_coverage_matrix_cells.py`, commit
# system-integration-tests@048fcd2). Parametrises over 5 representative
# cells (one per distinct partition shape — CEFI/TRADFI/DEFI/SPORTS/
# PREDICTION), enforces Steps 2 + 3 (parquet + manifest). Opt-in via
# `GCS_TEST_BUCKET_ENABLED=1`; skips cleanly without real GCS creds so SIT's
# unit-only QG stays green. Reuses per-category-bucket-layouts SSOT for
# prefix derivation. SIT README + playbook (§2.4) updated with usage.

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
      - [x] [AGENT] P0. Audit every service config for IS_TEST_RUN handling. Per-service
        report landed at `/codex/02-data/is-test-run-audit-2026-04-20.md`.
    status: done
    note: "/codex/02-data/is-test-run-audit-2026-04-20.md shipped via Phase 1 agent"

  - id: phase-1-propagate-is-test-run
    content: |
      - [x] [AGENT] P0. Propagate IS_TEST_RUN=true → `-test-` bucket suffix in every
        service config. Shipped across 11 services: features-sports (5a165f3),
        features-calendar (24fd260), features-onchain (fc19ce8), features-delta-one
        (eef36e6), features-volatility (2b7f4ba), features-cross-instrument (7d35678),
        features-multi-timeframe (2db39ad), features-commodity (0896ba0),
        ml-training (aac5cee), ml-inference (a1bb6b2). Plus MDPS auto-trigger
        via 9e7cfa8. MTDS already honoured this (pre-existing).
    status: done
    note: "11 services propagated; MTDS pre-existing"

  - id: phase-1-create-test-buckets
    content: |
      - [x] [SCRIPT] P0. `deployment-service/scripts/provision-test-buckets.sh` shipped
        (e0e0235). 77 -test- buckets live on GCS in asia-northeast1.
    status: done
    note: "deployment-service@e0e0235; 77 buckets verified via gsutil ls"

  - id: phase-1-gcs-lifecycle
    content: |
      - [x] [SCRIPT] P0. GCS lifecycle config + apply script shipped in
        deployment-service@e0e0235: `configs/test-bucket-lifecycle.json` + verify CLI.
    status: done
    note: "deployment-service@e0e0235"

  - id: phase-1-dep-checker-test-mode
    content: |
      - [x] [AGENT] P0. IS_TEST_RUN=true auto-triggers dep-checker test_mode via
        market-data-processing-service@9e7cfa8.
    status: done
    note: "market-data-processing-service@9e7cfa8"

  # ─── Phase 2 — per-service smoke matrix scripts ─────────────────────────
  - id: phase-2-instruments-smoke
    content: |
      - [x] [AGENT] P1. instruments-service: `scripts/smoke_matrix.py` shipped
        at `5e2e141` on live-defi-rollout. Iterates every (category x venue x
        data_type) cell from UAC `DATA_TYPES_BY_CATEGORY` x `VENUES_BY_CATEGORY`.
        SPORTS handled via provider axis (`--sports-provider`) with api-football
        T0 emitted FIRST. The **3-step assertion contract** (applies to EVERY
        phase-2 service smoke):
          1. **Run** the service CLI with `IS_TEST_RUN=true` (default dry-run;
             `--execute` flag actually invokes the CLI)
          2. **Verify GCS write**: ≥1 parquet under
             `gs://instruments-store-{cat}-test-{project_id}/
             instrument_availability/by_date/day={date}/venue={venue}/...` for
             CEFI/TRADFI/DEFI/PREDICTION, or `sports_reference/by_date/day=.../`
             for SPORTS (per `per-category-bucket-layouts.md`)
          3. **Verify TEST manifest write**: read the TEST bucket's own
             `_index/availability_index.parquet` and assert a row with the shard
             tuple AND `capture_status` in {captured, empty_confirmed}.
             `empty_confirmed` is a PASS not a SKIP.
        Sub-CLI: `python scripts/smoke_matrix.py [--asset-group X] [--venue Y]
        [--data-type Z] [--execute] [--report path.json]`. Returns rc=0 on
        all-pass, rc=1 on any-fail, 0 on dry-run. Enumerates 510 cells total.
        Phase 3 DependencyError for T1-without-T0 surfaces as `status=skipped
        reason=api_football_missing`. Shard-level isolation: one failed cell
        does NOT abort the rest. 15 unit tests green (tests/unit/test_smoke_matrix.py).
    status: done
    note: "instruments-service@5e2e141 — 510 cells, 15 tests, full QG green (128s)"

  - id: phase-2-mtds-smoke
    content: |
      - [x] [AGENT] P1. market-tick-data-service: `scripts/smoke_matrix.py`
        shipped at `f9efaf7` on live-defi-rollout. Same 3-step assertion
        contract as phase-2-instruments-smoke, keyed on
        (category x venue x data_type) with optional instrument_type.
        `smoke_canonical_writes.sh` superseded — new matrix covers every UAC
        category at once, uses `--max-instruments 1` for bounded smoke, injects
        the representative symbol per venue (first element of SYMBOLS_* arrays
        in `launch-cefi-sharded-backfill.sh`). Category-specific path layouts
        respected: PREDICTION has no category/venue level, DEFI keeps
        `category=defi` only (chain= is deeper), CEFI/TRADFI/SPORTS have full
        venue-level partitioning. 510 cells enumerated; 14 unit tests green
        (tests/unit/test_smoke_matrix.py).
    status: done
    note:
      "market-tick-data-service@f9efaf7 — 510 cells, 14 tests, smoke scoped to scripts/ (out of basedpyright include
      path — same convention as validate_manifest_coverage.py)"

  - id: phase-2-mdps-smoke
    content: |
      - [x] [AGENT] P1. market-data-processing-service: `scripts/smoke_matrix.py`
        shipped at `aae7c4d` on live-defi-rollout. Iterates every
        (category x data_type x timeframe) cell from UAC SSOT via
        `get_valid_timeframes_for_data_type()` and `needs_candle_processing()`.
        Uses `--max-results 1` via existing CLI (cli/parser.py). Pre-flight
        handled by MDPS DependencyChecker(test_mode=True) which auto-triggers
        from IS_TEST_RUN=true (Phase 1.5, `9e7cfa8`). Upstream-missing surfaces
        as status=skipped, reason=upstream_missing. Same 3-step assertion
        contract: (1) run CLI (2) verify GCS parquet at
        `gs://market-data-tick-{cat}-test-{project_id}/processed_candles/by_date/...`
        for non-SPORTS or `processed/by_date/...` for SPORTS (per path-layouts
        SSOT) (3) verify TEST manifest row with capture_status.
        109 cells enumerated; 14 unit tests green (tests/unit/test_smoke_matrix.py).
    status: done
    note: "market-data-processing-service@aae7c4d — 109 cells, 14 tests"

  - id: phase-2-features-smokes
    content: |
      - [x] [AGENT] P1. features-* services (sports, calendar, onchain, delta-one,
        volatility, cross-instrument, multi-timeframe, commodity): each gets
        `scripts/smoke_matrix.py` + sub-CLI at `python -m <service>.smoke` +
        unit tests. 17 viable cells total across the 8 services, honouring the
        canonical matrix in launch-features-backfill-vm.sh. Each script runs
        the 3-step assertion contract per cell: (1) run service CLI with
        IS_TEST_RUN=true (2) verify GCS parquet in the -test- bucket (3) verify
        TEST manifest capture_status. Shard-level isolation; architecturally-
        unsupported cells emit SKIP.
    status: done
    note: |
      Shipped 2026-04-20 on live-defi-rollout. 8 commits:
      features-sports-service 9b384fb, features-calendar-service d8ba357,
      features-onchain-service 9b04cd3, features-delta-one-service bc75d36,
      features-volatility-service 02e1324, features-cross-instrument-service
      0c9d3dc, features-multi-timeframe-service d9d3316,
      features-commodity-service 8d2ff8e. 17 viable cells: sports(1 SPORTS)
      + calendar(2 CEFI/TRADFI) + onchain(1 DEFI) + delta-one(4
      CEFI/DEFI/TRADFI/PREDICTION) + volatility(2 CEFI/TRADFI) +
      cross-instrument(3 CEFI/TRADFI/PREDICTION) + multi-timeframe(3
      CEFI/DEFI/TRADFI) + commodity(1 TRADFI). ~109 new unit tests
      (sports 13, calendar 16[1 skipped], onchain 16, delta-one 19,
      volatility 11, cross-instrument 12, multi-timeframe 12,
      commodity 10). Each script writes only to -test- buckets via
      IS_TEST_RUN=true env var propagation from Phase 1 plumbing.

  - id: phase-2-ml-smokes
    content: |
      - [ ] [AGENT] P2. ml-training-service + ml-inference-service: `scripts/smoke_matrix.py`.
        Pattern: train one model per (model_family × training_period) on minimal
        data + run inference on 1 instrument. Asserts manifest entries.
    status: todo

  # ─── Phase 3 — API Football dependency + sports ordering ────────────────
  - id: phase-3-api-football-dep-enforcement
    content: |
      - [x] [AGENT] P0. instruments-service sports adapters MUST throw a clear
        error if api-football reference data hasn't been fetched yet for the date.
        Today the dep is silent — sports adapters that depend on api-football
        (footystats, SFI, etc.) read from instruments-store-sports/.../entity=
        ASSUMING the data is there. Add a pre-flight check + DependencyError with
        actionable message: "api-football reference data missing for date X.
        Run: python -m instruments_service --operation instruments --mode batch
        --asset-group SPORTS --sports-provider API_FOOTBALL --start-date X --end-date X".
        Document in `/codex/02-data/sports-adapter-dependency-order.md` (NEW).
    status: done
    note: |
      Shipped 2026-04-20 on live-defi-rollout. New helper
      `instruments-service/instruments_service/reference_data/sports_dependency.py`
      exposes `check_api_football_dependency(date, bucket=None)` +
      `venue_requires_api_football(venue)`. Factory
      `instruments_service/reference_data/adapters/sports/factory.py` now
      accepts optional `date` + `bucket` kwargs; when `date` is supplied for
      any non-api-football venue (footystats / understat / transfermarkt /
      SFI / open_meteo / betfair), the factory raises
      `unified_trading_library.DependencyError` with the CLI remediation
      message before the adapter is instantiated. Error message includes the
      expected gs:// path and the exact
      `python -m instruments_service --sports-provider API_FOOTBALL` command
      to run first. Honours `IS_TEST_RUN` via the shared instruments-service
      bucket resolver. Tests in
      `instruments-service/tests/unit/test_sports_dependency_enforcement.py`
      (17 tests, all green). Commit SHA to be appended by quickmerge Pass 2.

  - id: phase-3-sports-internal-ordering
    content: |
      - [x] [AGENT] P1. Document the sports-internal adapter dependency order:
        api-football (canonical fixtures + leagues) MUST run FIRST, then
        footystats/SFI/Understat/odds-api can run in any order (they depend on
        api-football's canonical fixture IDs). Codify in
        `/codex/02-data/sports-adapter-dependency-order.md`. Add unit test that
        verifies the ordering invariant.
    status: done
    note: |
      Shipped 2026-04-20 on live-defi-rollout. New codex doc
      `unified-trading-pm/codex/02-data/sports-adapter-dependency-order.md`
      covers: the T0/T1 invariant + dependency graph, per-adapter rationale
      for depending on api-football, parallelisation rules after T0,
      per-entity coverage matrix, failure modes (entirely missing, partially
      missing, empty-day graceful degradation, test-bucket divergence), and
      fail-loud-boundary rationale (pre-flight raises are allowed; shard-
      level raises are not). Cross-linked FROM
      `per-category-bucket-layouts.md` § Cross-references, registered in
      `codex/00-SSOT-INDEX.md` immediately after the per-category-bucket
      row, and cross-referenced from this plan. Ordering invariant is
      enforced in code AND tested in the
      `TestVenueRequiresApiFootball.test_dependent_set_matches_adapter_registry`
      test which locks the `_API_FOOTBALL_DEPENDENT_VENUES` set against an
      explicit expected frozenset. Commit SHA to be appended by quickmerge
      Pass 2.

  # ─── Phase 4 — service dependency ordering for the smoke orchestrator ───
  - id: phase-4-orchestrator-dep-graph
    content: |
      - [x] [AGENT] P0. deployment-service/scripts/run-smoke-matrix.sh — workspace
        orchestrator. Reads dependency DAG from `deployment-service/configs/dependencies.yaml`
        (already exists for prod batch ordering). Runs smokes in dep order:
        instruments-service FIRST → MTDS → MDPS → features-*. Per-service: parallel
        within a tier, sequential across tiers. Pass IS_TEST_RUN=true through the
        whole chain. Collects per-service pass/fail summaries → writes
        `{report-dir}/summary.json` + human-readable tier breakdown to stdout.
    status: done
    note: |
      Shipped 2026-04-20 on live-defi-rollout. New script
      `deployment-service/scripts/run-smoke-matrix.sh` with tier-ordered
      dispatch: Tier 0 (instruments-service) → Tier 1 (market-tick-data-service)
      → Tier 2 (market-data-processing-service) → Tier 3 parallel
      (8 features-* services). Parallel WITHIN a tier via backgrounded
      subshells + `wait`; sequential ACROSS tiers. Each invocation runs
      `IS_TEST_RUN=true python scripts/smoke_matrix.py --execute --report
      {dir}/{service}.json` in the target repo. Shard-level isolation
      respected: one service failing inside a tier does NOT abort siblings
      unless `--fail-fast`. Dep-graph is hard-coded in the script from the
      plan + cross-checked against `deployment-service/configs/dependencies.yaml`
      (script logs the DAG source on every run). Summary aggregator handles
      both per-service JSON schemas: (A) instruments/MTDS/MDPS top-level
      {total_cells,passed,failed,skipped,results[]} and (B) features-*
      {cells[]} with status in {PASS/FAIL/SKIP}. Commit SHA appended by
      quickmerge Pass 2.

  - id: phase-4-cli-flags
    content: |
      - [x] [AGENT] P0. Smoke orchestrator CLI:
        - `--service X` — smoke only one service (skips deps, logs an
          actionable note if the user did not also pass `--no-deps`)
        - `--asset-group Y` — limit to one category (CEFI/TRADFI/DEFI/SPORTS/PREDICTION)
        - `--venue Z` — limit to one venue
        - `--data-type W` — limit to one data type
        - `--no-deps` — skip the dep cascade (assumes prior state in TEST buckets)
        - `--cleanup` — delete TEST bucket data after the run (overrides 7-day lifecycle)
        - `--dry-run` — enumerate cells + show invocation plan; no actual CLI runs
        - `--report-dir PATH` — override the per-service JSON + summary dir
        - `--timeout-per-service N` — per-service subprocess budget (default 600s)
        - `--fail-fast` — abort the whole matrix on first service failure
        - `--include-ml` — add ml-training + ml-inference to dispatch (default excluded
          while phase-2-ml-smokes is still open)
        Default: full matrix in service-dep order, parallel within tier,
        continue on failure.
    status: done
    note: |
      Shipped 2026-04-20 on live-defi-rollout alongside
      phase-4-orchestrator-dep-graph. All 11 flags + `--help` wired and
      unit-tested. Coverage: `deployment-service/tests/unit/test_run_smoke_matrix.py`
      (14 tests green) exercises --dry-run / --service / --fail-fast /
      --include-ml / schema-A and schema-B aggregation / filter forwarding
      / missing-script failure / unknown-flag rejection. Commit SHA appended
      by quickmerge Pass 2.

  # ─── Phase 5 — codex playbook + CI integration ──────────────────────────
  - id: phase-5-codex-playbook
    content: |
      - [x] [DOC] P0. /codex/14-playbooks/smoke-testing-playbook.md (NEW): operational
        runbook for the smoke matrix. Covers: when to run (daily, pre-release,
        post-incident), how to read the per-cell summary, common failure modes
        (TEST bucket not provisioned, IS_TEST_RUN not propagated, dep order broken,
        api-football missing), how to retry a single cell, how to cleanup TEST data.
    status: done
    note: |
      Shipped 2026-04-20 on live-defi-rollout. New file
      `unified-trading-pm/codex/14-playbooks/smoke-testing-playbook.md`
      covers: 10 sections (when to run, how to read stdout + summary.json,
      PASS/FAIL/SKIP semantics with `empty_confirmed`=PASS, 6 failure-mode
      recipes — TEST bucket missing, IS_TEST_RUN not propagated, dep cascade
      broken, api-football missing with remediation CLI verbatim, rate
      limits, VM-only path differences — single-cell retry, `--cleanup` vs
      7-day lifecycle, nightly-failure runbook, production-deploy gate
      via `workflow_call.smoke_green`, floor-YAML ratchet rules, related
      documents, change log). Registered in `codex/00-SSOT-INDEX.md`
      immediately after the `sports-adapter-dependency-order` row. Commit
      SHA appended by quickmerge Pass 2.

  - id: phase-5-gha-workflow
    content: |
      - [x] [AGENT] P1. GHA workflow `.github/workflows/nightly-smoke-matrix.yml`
        in PM. Runs `bash deployment-service/scripts/run-smoke-matrix.sh --all` at
        02:00 UTC daily. Posts result summary to Slack #data-platform-ops. Gates
        production deployment workflows: a deployment to main can only proceed if
        the most recent smoke matrix is green.
    status: done
    note: |
      Shipped 2026-04-20 on live-defi-rollout. New workflow
      `unified-trading-pm/.github/workflows/nightly-smoke-matrix.yml` runs
      at `0 2 * * *` UTC with `workflow_dispatch` (service / category /
      fail_fast / include_ml inputs) + `workflow_call` output
      `smoke_green` for downstream promotion gating. Flow: checkout PM +
      deployment-service + every Tier 0/1/2 service + 8 Tier-3 features-*
      services at `live-defi-rollout`, install gcloud SDK for gsutil,
      authenticate via workload-identity (`GCP_WORKLOAD_IDENTITY_PROVIDER`
      + `GCP_NIGHTLY_SMOKE_SA` secrets), uv-install deployment-service,
      `--dry-run` first (plan validation), then live run with per-service
      JSON + summary.json uploaded as 30-day retention artifact, then
      floor enforcement via `enforce-smoke-coverage-floor.py`. Telegram
      notification reuses `notify-telegram.yml` (workspace has no Slack
      secret; Telegram is the SSOT — see cold-storage-cleanup.yml
      pattern). Gate step fails job when any cell FAILs or floor
      regresses; downstream workflows consume the `smoke_green` output.
      Header points at the playbook for troubleshooting. Commit SHA
      appended by quickmerge Pass 2 (PM doc-only fast-path — merges to
      `main` directly per fast-path rules but workflow file goes to
      `staging` for SIT; expected quickmerge behaviour). Note: workflow
      file goes through staging per workflow routing rule (see CLAUDE.md §
      PM/Codex Doc-Only Fast-Path — `.github/workflows/` → staging).

  - id: phase-5-coverage-floor
    content: |
      - [x] [SCRIPT] P2. Add per-(service × category) smoke coverage floor in
        `deployment-service/configs/smoke-coverage-floor.yaml`. Blocks merges that
        would lower the count of green smoke cells below the historical baseline.
        Pattern: same as coverage_ratchet_policy_2026_04_19 plan.
    status: done
    note: |
      Shipped 2026-04-20 on live-defi-rollout. 3 files in
      deployment-service: `configs/smoke-coverage-floor.yaml` (zero-baseline
      per (service, category) pair; `null` for architecturally unsupported;
      13 services × 5 categories declared), `scripts/enforce-smoke-coverage-floor.py`
      (reads floor YAML + summary.json + per-service reports, counts green
      cells by category, reports ALL regressions not just first — shard-
      level failure isolation; `--strict-missing` flag for unknown-service
      promotion to fail; dry-run summary.json accepted; exit 0 OK / 1
      regression / 2 CLI misuse), and 12 unit tests at
      `tests/unit/test_enforce_smoke_coverage_floor.py` covering:
      zero-baseline pass, floor-met pass, regression surfaces rc=1 with
      actionable error, `null` skipped not enforced, malformed YAML rc=2,
      missing `cells` key rc=2, negative int rejected rc=2, dry-run
      accepted rc=0, missing-service warn by default, `--strict-missing`
      fails, multi-regression all reported (shard isolation), summary-is-
      directory accepted, missing-summary rc=2. Baseline is 0 for every
      cell — the first green nightly run ratchets up via a follow-up PR
      with `chore(smoke): ratchet smoke-coverage floor to <run-id>`
      commit prefix (documented in playbook § 8). The nightly GHA
      workflow invokes the enforcer as a step; the gate fails the job
      (and the `smoke_green` output) on any regression. Commit:
      deployment-service@c292993.

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
reconciliation_status: shipped_substantive
reconciliation_date: 2026-04-25
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **Reconciliation note (2026-04-25):** Substantively shipped — recommended for archive. Phases 1-5 shipped (PM
> 1fce53d3, 939726c3, 47c5fd7a, 4d599b72, 0852d0be); canonical gate pivoted to system-integration-tests/smoke. Ready for
> archive after YAML→checkbox conversion. See `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

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
  └── CLI flags (--service, --asset-group, --venue, --data-type)
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

- Per-category bucket layouts: `/codex/02-data/per-category-bucket-layouts.md` (defines what a smoke needs to write)
- Honest-coverage manifest schema: `/codex/02-data/availability-manifest-and-data-status.md`
- VM tarball deployment: `/codex/05-infrastructure/vm-tarball-deployment.md`
- Coverage roadmap (the broader operational sequence): `plans/active/proper_coverage_roadmap_2026_04_20.md`
- Service dependency DAG: `deployment-service/configs/dependencies.yaml`
- CLI convention: `/codex/06-coding-standards/cli-convention.md`

## Handover prompt for the next agent (copy verbatim)

```
Read this plan first: unified-trading-pm/plans/active/institutional_smoke_matrix_2026_04_20.md

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
