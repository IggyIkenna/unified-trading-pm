---
doc_type: plan
title: ── 2026-04-20 canary context ───────────────────────────────────────────────
summary:
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-service,
    instruments-service,
    market-tick-data-service,
    system-integration-tests,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-21"
superseded_by: [universe_ssot_fix_2026_04_20.md]
reconciliation_status: superseded
reconciliation_date: 2026-04-25
---

> **SUPERSEDED 2026-04-25 by [universe_ssot_fix_2026_04_20.md](./universe_ssot_fix_2026_04_20.md).** Phase A
> bucket-naming fixes shipped; Phase B universe-SSOT was carved out into universe_ssot_fix Original scope retained for
> history. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

---

name: smoke-dep-chain-tactical-fixes overview: Phase A tactical fixes surfaced by 2026-04-20 institutional smoke canary.
Bucket naming convention (mostly shipped), SIT manifest filter Tier-0 vs Tier-1 semantics, path-layout SSOT
reconciliation vs actual writes, launcher extension for SPORTS + PREDICTION, stale default date, VM auto-shutdown,
SIGKILL/memory investigation. No architectural changes — that's Phase B (plans/active/universe_ssot_fix_2026_04_20.md).
type: mixed epic: epic-data-platform-honest-coverage status: active

locked_by: live-defi-rollout locked_since: 2026-04-21

completion_gates: code: C3 deployment: D2 business: B1

depends_on:

- institutional_smoke_matrix_2026_04_20

# ── 2026-04-20 canary context ───────────────────────────────────────────────

#

# CEFI dep-chain canary surfaced 11 issues. 5 bucket-naming sites fixed

# already (commits: instruments-service@e6e50c7, UTL@4ee91009, deployment-

# service@2163ec3, MTDS@1363e3f + @81b1b6f). Tier-0 → Tier-1 chain proved

# green for CEFI × BINANCE-FUTURES (131 parquet written at day=2026-04-19/

# category=cefi/venue=BINANCE-FUTURES/{data_type}). Remaining items in this

# plan are test-harness / tooling / docs. Universe-discovery drift tracked

# separately in universe_ssot_fix plan.

todos:

- id: phase-a-bucket-naming-fix content: |
  - [x] [DONE] P0. Bucket naming middle-test convention across all consumers. Shipped: instruments-service 3 sites
        (orchestrator / sports_dependency / catalogue_builder — all use get_write_bucket_name), UTL dependency_checker
        fallback fail-loud on missing -{project_id} anchor, deployment-service setup-buckets.py middle-test enforced,
        MTDS orchestrator pre-flight + Tardis/Polymarket/Kalshi/DeFi-base adapters all use get_write_bucket_name. Tests
        updated (test_new_orchestrator bucket tests: 4/4 green). Tarballs refreshed. Verified end-to-end CEFI: Tier-0
        writes to
        `instruments-store-cefi-test-central-element-323112/.../day=2026-04-19/     venue=BINANCE-FUTURES/instruments.parquet` +
        Tier-1 reads it and writes 131 tick parquet. status: done note: "Instruments e6e50c7, UTL 4ee91009, deployment
        2163ec3, MTDS 1363e3f + 81b1b6f"

- id: phase-a-sit-manifest-filter-tier-aware content: |
  - [ ] [AGENT] P0. SIT `tests/smoke/coverage_matrix_cells.py::CellSpec.manifest_filter` needs Tier-0 vs Tier-1/Tier-2
        handling. Current behaviour requires `data_type` in filter but Tier-0 instruments-service rows leave
        `data_type=''` (universe-level row spans all data types). Also filter uses `category` column which doesn't exist
        — category is bucket-level, not a manifest column. Fix: 1. Add `tier: Literal["tier0", "tier1", "tier2"]` field
        to CellSpec. 2. `manifest_filter()` omits `category` (use bucket routing instead). 3. For tier0 cells, omit
        `data_type` from filter (match any row with matching venue + empty data_type, or empty-string match). 4. For
        tier1/2 cells, include `data_type`. Update unit tests (tests/unit/test_coverage_matrix_cells.py). status:
        pending

- id: phase-a-path-layout-ssot-reconcile content: |
  - [ ] [AGENT] P0. `/codex/02-data/per-category-bucket-layouts.md` SSOT says MTDS writes under
        `raw_tick_data/by_date/day=...` but actual 2026-04-20 canary landed 131 parquet at FLAT
        `day=.../category=.../venue=.../     instrument_type=.../data_type=.../{id}.parquet` (no
        `raw_tick_data/by_date/` prefix). Either docs are wrong OR MTDS lost the prefix somewhere. Audit MTDS write path
        (StreamingParquetWriter + partition spec in orchestrator), decide canonical, update whichever is wrong. If docs
        are right, fix MTDS. If MTDS is right, fix docs + update SIT `expected_parquet_prefix` + the existing
        per-service smoke_matrix scripts that reference `raw_tick_data/by_date`. status: pending

- id: phase-a-launcher-sports-prediction content: |
  - [ ] [SCRIPT] P1. Extend `deployment-service/scripts/vm/launch-canonical-smoke-vm.sh` and
        `launch-instruments-smoke-vm.sh` case branches to cover SPORTS + PREDICTION. Current only handles
        cefi/tradfi/defi. Representative venues: _ SPORTS → ODDS_API (provider axis via --sports-provider, not --venues)
        _ PREDICTION → POLYMARKET SPORTS is tricky — it uses --sports-provider + --sports-entity, not --venues. The VM
        metadata dispatch in setup-data-pipeline-vm.sh already handles VM_SPORTS_PROVIDER, so pass that via metadata.
        status: pending

- id: phase-a-stale-default-date content: |
  - [ ] [SCRIPT] P2. `launch-canonical-smoke-vm.sh` hardcodes `SMOKE_DATE="${2:-2024-06-15}"` (stale default from Phase
        2 migration). Change default to "yesterday UTC" matching `launch-instruments-smoke-vm.sh`:
        SMOKE_DATE="${2:-$(date -u -v-1d +%Y-%m-%d 2>/dev/null || date -u -d 'yesterday' +%Y-%m-%d)}" status: pending

- id: phase-a-vm-auto-shutdown content: |
  - [ ] [SCRIPT] P1. `setup-data-pipeline-vm.sh` has no auto-shutdown after the CLI task completes. VMs stay RUNNING and
        burn compute until manually deleted. Incident: canary VMs ran for 30-60+ min after task rc=0 on 2026-04-20. Add:
        when VM_TASK=canonical-smoke or instruments- smoke (smoke tasks specifically — NOT backfills), after the CLI
        subprocess exits, write the exit-code to GCS alongside the run.log, then run `sudo shutdown -h +1` so the VM
        self-terminates (1-min grace for GCS log flush). Preserve the log URI in the terminal output so the launcher
        caller knows where to look post-hoc. Add `--no-shutdown` launcher flag for debugging. status: pending

- id: phase-a-sigkill-investigation content: |
  - [ ] [AGENT] P1. CEFI canary attempt 4 (MTDS × BINANCE-FUTURES × 1 day) exited rc=137 on e2-standard-4 AFTER writing
        131 parquet. Likely OOM or oom-killer trigger. Investigate: 1. Memory watchdog log (threshold=85.0%) — was it
        triggered? 2. Check /var/log/syslog for oom-killer evidence 3. Measure peak memory via resource_profiler logs 4.
        Decide: (a) bump VM to e2-standard-8 for MTDS smoke, (b) bound MTDS per-batch memory via StreamingParquetWriter
        chunk tuning, (c) accept rc=137 as SUCCESS when preflight wrote enough data (SIGKILL after near-complete batch).
        Update `launch-canonical-smoke-vm.sh` machine-type if (a). status: pending

- id: phase-a-tier-semantic-doc content: |
  - [ ] [AGENT] P1. Update `/codex/02-data/availability-manifest-and-data-status.md` (manifest v5 SSOT) with Tier-0 vs
        Tier-1 semantic difference observed 2026-04-20: _ Tier-0 (instruments-service) rows have `data_type=''`
        (universe row spans all data_types for that (date, venue)) _ Tier-1/Tier-2 rows have `data_type` populated
        per-shard Plus: manifest has no `category` column; category is bucket-level. Update SIT
        `test_coverage_matrix_smoke.py` docstring to reference the new manifest-schema section. status: pending

- id: phase-a-qg-all-touched-repos content: |
  - [ ] [AGENT] P1. Run `bash scripts/quality-gates.sh` on every repo touched by Phase A fixes: - instruments-service -
        unified-trading-library - deployment-service - market-tick-data-service - system-integration-tests -
        unified-trading-pm (doc-only repo, runs lint only) Fix any NEW lint / typecheck / coverage regressions caused by
        this plan's changes. PRE-EXISTING failures (not caused by this plan) should be noted in a follow-up but not
        block. status: pending

- id: phase-a-verify-chain-all-categories content: |
  - [ ] [OPERATOR] P0. After Phase A items complete + Phase B universe writers shipped, verify end-to-end dep chain for
        all 5 categories on VMs (not locally). Expected: Tier-0 writes instruments.parquet for each category in `-test-`
        bucket, Tier-1 reads that universe and writes tick data. Cells to verify: _ CEFI × BINANCE-FUTURES × 2026-04-20
        (already proved 2026-04-20) _ TRADFI × CME × 2026-04-20 _ DEFI × UNISWAP × 2026-04-20 (tick download, not
        lending_indices) _ SPORTS × API_FOOTBALL × 2026-04-20 (provider axis) \* PREDICTION × POLYMARKET × 2026-04-20
        For each cell, verify: 1. Tier-0 parquet under correct prefix 2. Tier-1 parquet under correct prefix 3. Manifest
        v5 rows with capture_status in {captured, empty_confirmed} status: pending note: "Blocked on Phase B universe
        writers for TradFi/Polymarket/Kalshi/Sports-bookmakers"

# ── Success criteria ────────────────────────────────────────────────────────

# Phase A is green when:

# - SIT test_coverage_matrix_smoke.py passes its unit tests with tier-aware manifest_filter

# - per-category-bucket-layouts.md reflects actual write paths

# - Both launchers handle all 5 categories

# - VMs auto-shut down after smoke task completes

# - Manifest SSOT documents Tier-0 vs Tier-1 semantics

# - Full QG green on every touched repo

#

# End-to-end dep-chain for all 5 categories is blocked on Phase B universe

# writers — that's the gate item (phase-a-verify-chain-all-categories).
