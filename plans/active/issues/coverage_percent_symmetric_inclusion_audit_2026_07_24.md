---
doc_type: issue
title:
  Audit every coverage-percent computation across repos against the symmetric-inclusion invariant (empty_confirmed in
  numerator+denominator together, or neither)
summary: >-
  `/codex/02-data/honest-coverage-model.md` now states the symmetric-inclusion invariant explicitly (added 2026-07-24
  per `data_pipeline_e2e_milestones_gate_2026_07_24.md` §10) — the 2 SSOT formulas (`reachable_coverage`,
  `all_shards_coverage`) satisfy it by construction, but a 3rd, undocumented coverage-percent formula was found live in
  deployment-api during this same audit. This doc tracks the corpus-wide grep + classification needed to find any other
  asymmetric violation.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-api, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [honest-coverage, empty_confirmed, coverage-percent, audit, invariant]
related: [/codex/02-data/honest-coverage-model.md, /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md]
created: "2026-07-24"
last_updated: "2026-07-26"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: correct-codex
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §10
depends_on: []
---

# Symmetric-inclusion invariant audit — every coverage-percent formula

## Todos

- [x] ✅ [AUDIT] P2. Grep every repo (start with deployment-api, given a 3rd undocumented formula site was already found
      there) for coverage-percent computations referencing `empty_confirmed`; classify each against the
      symmetric-inclusion invariant stated in `/codex/02-data/honest-coverage-model.md` § "Coverage formula". — DONE
      2026-07-26 (grepped all 24 repo clones for `empty_confirmed`/`coverage_pct`/`all_shards_coverage`/
      `reachable_coverage`/`coverage_ratio`; read every production, non-test formula site found).

      **Result: NO VIOLATION found anywhere in the corpus.** Every site found:

                          1. `compute_honest_coverage()` — `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_honest_coverage_logic.py:96-186`.
                             `captured / (captured+attempted_failed+expected_unattempted_known_empty+expected_unattempted_pending_fetch)`;
                             `empty_confirmed` excluded from both. **PASS** — the `reachable_coverage` SSOT.
                          2. `_count_statuses()` — `instruments-service/scripts/measure_honest_coverage.py:603-613`. `coverage_pct` excludes
                             `empty_confirmed` both sides; `all_shards_coverage_pct` includes it denominator-only. **PASS** — the
                             `all_shards_coverage` SSOT.
                          3. `attempt_coverage_pct` — `deployment-api/deployment_api/services/data_status/coverage_metrics.py:406-414`
                             (`derive_capture_status_rates`), mirrored in `manifest.py:490-511` (`overall_attempt_coverage_pct`),
                             `rollup_cache.py:180-202`, `data_status_mock.py:60-78,95-99`. Formula:
                             `numerator = captured+empty_confirmed+attempted_failed`; `denominator = total_expected_cells` — an
                             independently-derived calendar/shard-universe count (not a sum of `CaptureStatusCounts` fields), which is
                             structurally inclusive of `empty_confirmed` cells. **PASS** — this IS the previously-flagged "3rd undocumented
                             formula"; it satisfies the invariant, it just isn't named in the codex doc yet (see follow-up todo below).
                          4. `_coverage_per_calc_league()` — `deployment-api/deployment_api/services/coverage_drift.py:55-82`.
                             `ok = isin(["captured","empty_confirmed"]).sum(); pct = 100*ok/len(group)` — denominator is the raw row count,
                             inclusive of `empty_confirmed` rows. **PASS**.
                          5. `mtds_honest_coverage_for_venue`/`_for_bookmaker` — `deployment-api/deployment_api/services/data_status/mtds.py:822-834,987-1001`.
                             Numerator credits `captured`+`empty_confirmed` (+`expected_unattempted`); denominator is a schedule/calendar-derived
                             `expected_dates` count, structurally inclusive of the same cells. **PASS**.
                          6. `read_capture_status_counts` — `unified-trading-library/unified_trading_library/manifest_writer/_queries.py:407-447` —
                             pure count materialization feeding formula #1, no independent ratio. **PASS** (delegates to SSOT).

                          Ruled out as unrelated (no `empty_confirmed` involvement): features-service's `coverage_ratio`
                          (`replacement_model_calculator.py`, `sports_validity_engine.py` — bench-depth/prior-coverage, unrelated concept),
                          strategy-service's `data_certification.py` `coverage_pct` (bars/lookback ratio), client-reporting-api (pure
                          passthrough consumer), batch-live-reconciliation-service (no `empty_confirmed` references at all).

- [ ] [DOC] P3. `/codex/02-data/honest-coverage-model.md` § "Coverage formula" names only `reachable_coverage`/
      `all_shards_coverage` — add `attempt_coverage_pct` (numerator=`captured+empty_confirmed+attempted_failed`,
      denominator=an independently-derived calendar/shard-universe cell count, NOT a `CaptureStatusCounts` field-sum) as
      a third sanctioned pattern, since it's proven live and widespread (deployment-api's primary
      `coverage_metrics.py`/`manifest.py`/`rollup_cache.py` path + the MTDS-style venue/bookmaker rollups in `mtds.py` +
      the `coverage_drift.py` detector). Doc-only change, no code fix needed. Source: this doc's audit finding 3
      (audited 2026-07-26).
