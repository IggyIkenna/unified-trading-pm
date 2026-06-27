---
title: "Sports P1a — golden-window API-Football to 100% (fixtures + enrichment + core)"
parent_epic: sports_master
priority: P0
status: active
assigned_vm: NA
assigned_vm: human-planning
assigned_role: data_engineering
drift_direction: advance-code
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - sports_p0_spot_vm_launchers_2026_06_27
  - sports_p0_sourcing_and_honest_coverage_correctness_2026_06_27
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
  - plans/active/data_completion_to_100_all_ag_2026_06_21.md
  - plans/active/sports_manifest_canonicalisation_2026_06_01.md
---

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 1). Golden window = **2025-09-01
> .. 2025-11-30**, 94-league universe. This plan drives ALL **API-Football** `data_types` to 100% honest coverage on the
> window — fixtures (verify), enrichment (the open gap), and core. **PREREQ: P0 shipped** (else honest-absence is
> mislabelled). One agent, `data_engineering` (Sonnet/high). Smart-skip + season-aware: fetch only not-honest-complete
> cells; off-season/no-fixture → typed `EXPECTED_*`.

# Sports P1a — golden-window API-Football to 100%

## Scope (API-Football data_types on the golden window)

`FIXTURES` (already ~100% post-canonicalize — VERIFY), and the open enrichment + core gap (numbers per
`data_completion_to_100_all_ag` 2026-06-24 measure): `FIXTURE_LINEUPS` (~5,690 blank-reason empty + 18 failed),
`FIXTURE_EVENTS` (~541 blank-reason), `FIXTURE_STATS` (~370 blank-reason + 16 failed), `PLAYER_STATS` (~2 failed),
`INJURIES` (~90 real `ApiFootballResponseError` — retry), `STANDINGS` + `TEAMS` (verify). ODDS is NOT api-football (→
P1c, MTDS). XG/XG_SHOTS are understat (→ P1b).

> **SPOT VMs (HARD)** — launch every VM in this plan as **spot/preemptible** (the cloud can reclaim + kill it at any
> moment) per [`sports_p0_spot_vm_launchers_2026_06_27`](sports_p0_spot_vm_launchers_2026_06_27.md); the sports
> launchers default to SPOT. Backfills are idempotent/skip-existing, so a reclaimed VM relaunches + resumes — and a
> preemption must NOT raise a false `DP_VM_GONE_NO_CAPTURE` (R5).

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — 4-state `capture_status`, the
  `expected_unattempted_pending_fetch == 0` target
- `codex/02-data/honest-absence-downstream-handling.md` — typed `EXPECTED_*`; the golden-window effect
- `codex/02-data/sports-gcs-path-ssot.md` — sports layouts + `candidate_parquet_paths()`

## Mechanics (real CLIs / scripts / launchers)

- **Backfill**:
  `bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh --entity <ENTITY> 2025-09-01 2025-11-30`
  (singleton-locked — one `af-backfill-*` at a time; `--force` only to bypass). Per-entity: `FIXTURES`,
  `FIXTURE_LINEUPS`, `FIXTURE_EVENTS`, `FIXTURE_STATS`, `PLAYER_STATS`, `INJURIES`, `STANDINGS`, `TEAMS`.
  `skip-existing` ON (gap-fill, not re-fetch).
- **Audit/verify**: `instruments-service/scripts/run_fixture_completeness_audit_2026_06_25.py` (golden-window scan) + a
  `read_availability_index` window query for `expected_unattempted_pending_fetch == 0`.
- Rate budget allocated at VM launch (`allocate_rate_budget("api_football", n_vms)`); honour the AF singleton lock.

## Todos

- [ ] [VERIFY] P0. **Confirm FIXTURES = 100% on the window** for all 94 leagues. Run the completeness audit; any
      residual no-match cell must carry `EXPECTED_NO_FIXTURE` (not blank/`SOURCE_RETURNED_ZERO`). **Gate**:
      `read_availability_index` window-scoped query → `(api_football, FIXTURES)` has 0
      `expected_unattempted_pending_fetch` and 0 blank-reason empties across the 94 leagues × 91 days.
- [ ] [DATA] P0. **Backfill the enrichment gap** (`FIXTURE_LINEUPS`, `FIXTURE_EVENTS`, `FIXTURE_STATS`, `PLAYER_STATS`)
      for the window, gap-fill only (skip-existing). Relabel residual blank-reason empties to the correct typed reason
      via the season/coverage calendar (`EXPECTED_NO_FIXTURE` / `EXPECTED_NO_PROVIDER_COVERAGE` / `EXPECTED_PRE_*`);
      these enrichment `data_types` start `2020-06-06` (`DATA_TYPE_COVERAGE_START`) so the whole window is in-coverage.
      Use the AF backfill launcher per entity (singleton-serialised). **Gate**: window query → each enrichment
      `data_type` has 0 `expected_unattempted_pending_fetch` AND 0 blank-reason empty; every non-captured cell carries a
      typed `EXPECTED_*` reason; VM run.log `exit_code=0` + STARTED/STOPPED events.
- [ ] [DATA] P0. **Re-fetch the ~90 INJURIES real failures** (`ApiFootballResponseError`) on the window via
      `--recovery-fixture-ids` or an entity-scoped re-run; genuine post-retry failures stay `attempted_failed` only with
      a `FetchEvidence`-backed error, never masked as empty. **Gate**: window `INJURIES` `attempted_failed` → 0 (or each
      residual carries proven `FetchEvidence`); no placeholder `record_captured`.
- [ ] [VERIFY] P0. **Verify STANDINGS + TEAMS = 100%** on the window (core entities; date-invariant TEAMS via the FLAT
      layout). **Gate**: window query → both at 100% honest coverage; phantom dry-run ≈ 0 (P0 #5 unblocked it).
- [ ] [DATA] P1. **No-blank-reason invariant** across ALL AF data_types on the window. **Gate**: the canonical sports
      `_index` window slice has ZERO `capture_status=empty_confirmed` rows with blank/null `error_reason` for any
      api_football data_type.

**Full-execution criterion**:

- ✅ Every API-Football data_type reads 100% honest coverage on 2025-09-01..2025-11-30 for the 94 leagues,
  manifest-verified.
  - **What ran**: per-entity `af-backfill-*` VMs (launcher above) on the window; the completeness audit +
    `read_availability_index` query on `instruments-store-sports-prd-central-element-323112`.
  - **Verification**: window query output pasted into the Progress Log — `pending_fetch=0`, `blank_reason=0`,
    `attempted_failed=0` (or evidence-backed) per data_type.

## Success criteria

- 0 `expected_unattempted_pending_fetch`, 0 blank-reason empties, 0 un-evidenced `attempted_failed` for every
  api-football data_type on the golden window across the 94 leagues.
- Every VM run honoured the singleton lock + emitted STARTED/progress/STOPPED (no fire-and-forget).

## Dependencies

- **Upstream (prereq)**: P0 (sourcing + honest-coverage correctness).
- **Feeds**: P1d (features), P1e (golden-window e2e gate). Runs concurrently with P1b, P1c.

## References

- `data_completion_to_100_all_ag_2026_06_21.md` — the golden-window gap maps (NA/local-only; re-homed here)
- `sports_manifest_canonicalisation_2026_06_01.md` — the typed-reason contract
