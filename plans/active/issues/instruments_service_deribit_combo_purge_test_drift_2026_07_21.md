---
doc_type: issue
title: "instruments-service tests/goldens stale vs UAC DERIBIT-COMBO deregistration (cefi manifest canonicalization v2)"
summary: >-
  UAC commit 11adf279 (2026-07-21, operator decision) deregistered the legacy DERIBIT-COMBO venue from
  VENUE_TO_ADAPTER_KEY and registered OKX-FUTURES/OKX-SWAP. instruments-service's own tests/golden files (factory
  routing tests, enumeration-completeness tests, the cefi expected-universe golden, and the CEFI per-AG dedup target
  count) still assume the old venue set and now fail deterministically. Discovered as a side-effect while fixing an
  unrelated ldr_qg_failure escalation (agt-9df557) for instruments-service#886.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [cefi, deribit-combo, test-drift, cross-repo]
related: []
created: 2026-07-21
assigned_vm: NA
source: [cicd-escalation-agt-9df557]
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
parent_epic: cefi_master
resolved_by:
---

## What I found

While resolving `ldr_qg_failure` escalation `agt-9df557` (instruments-service#886, `quality-gates-v2` red on
`live-defi-rollout` due to an unrelated `TimestampAlignmentError` on `available_at`), a full local `quality-gates.sh`
run on instruments-service surfaced **8 deterministic, pre-existing test failures** unrelated to my fix:

```
FAILED tests/unit/scripts/test_check_enumeration_completeness.py::TestCompletenessMetrics::test_completeness_pct_is_correct_fraction
FAILED tests/unit/scripts/test_check_enumeration_completeness.py::TestCompletenessMetrics::test_missing_instrument_type_column_yields_empty_enumerated
FAILED tests/unit/scripts/test_expected_universe_golden.py::TestGoldenByteIdentical::test_expected_matches_golden[cefi]
FAILED tests/unit/test_cefi_tradfi_comprehensive.py::TestDeribitComboAdapter::test_factory_contains_deribit_combo
FAILED tests/unit/test_factory_comprehensive.py::TestFactoryTardisRouting::test_deribit_combo_batch_routes_to_tardis
FAILED tests/unit/test_factory_comprehensive.py::TestFactoryTardisRouting::test_deribit_combo_live_routes_to_rest_adapter
FAILED tests/unit/test_factory_comprehensive.py::TestFactoryTardisRouting::test_deribit_combo_live_pool_reuse
FAILED tests/unit/test_pipeline_e2e_prediction.py::test_rule11_per_ag_dedup_target_counts_byte_unchanged
```

Root cause: `unified-api-contracts` commit `11adf279` ("fix(registry): register OKX-FUTURES/OKX-SWAP cefi venues,
deregister legacy DERIBIT-COMBO", 2026-07-21 17:24:44+0100) removed `DERIBIT-COMBO` from `VENUE_TO_ADAPTER_KEY`
(comment: "operator decision: legacy venue... own internal factory entry") and added 2 new venues. instruments-service
depends on UAC via an **unpinned, editable path dependency**
(`[tool.uv.sources.unified-api-contracts] path = "../unified-api-contracts"`, range
`unified-api-contracts>=0.33.0,<1.0.0` in `pyproject.toml`), so any local dev clone that has fast-forwarded its sibling
UAC checkout past `11adf279` picks up the new registry immediately — while instruments-service's own factory-routing
tests, the `test_expected_universe_golden.py` cefi golden file, and the
`test_rule11_per_ag_dedup_target_counts_byte_unchanged` magic count (`25`, now actually `26` — net +1 from
OKX-FUTURES/OKX-SWAP minus DERIBIT-COMBO) were never updated to match.

Confirmed pre-existing (not caused by the `available_at` fix): reproduced byte-identical on a clean `git stash`'d tree
at instruments-service HEAD `639591f6`. Reproduced deterministically in isolation (not test-order/xdist flaky) —
`python -m pytest <the 8 tests> -p no:xdist` fails the same 8, every time.

**Why this hasn't shown up in actual CI yet**: `quality-gates-v2` resolves sibling `path = "../<repo>"` dependencies by
cloning each dep repo's `main` branch fresh at CI runtime (see
`instruments-service/.github/workflows/quality-gates-v2.yml` → `python-quality-gates-v2.yml` →
`BRANCH="${DEP_BRANCH:-main}"`), NOT `live-defi-rollout`. UAC commit `11adf279` was only on `live-defi-rollout` at time
of writing; it will hit UAC's `main` (and therefore every future instruments-service CI run) once the standing LDR→main
promote PR merges (~15 min cadence). This is a ticking cross-repo break: once that promotion lands, **every future
`quality-gates-v2` run on instruments-service will fail these same 8 tests** until this issue is closed.

## Why it matters

- Blocks any further instruments-service shipping once UAC's `main` catches up (race condition already in flight at time
  of filing).
- The dedup-count/golden drift (`test_rule11_per_ag_dedup_target_counts_byte_unchanged`,
  `test_expected_matches_golden[cefi]`) indicates the CEFI venue-universe golden baseline itself needs regenerating, not
  just a magic-number bump — do that via whatever golden-regen script the
  `master_data_canonicalisation_migration_catalogue_2026_06_07.md` / `cefi_consolidated_closeout_2026_07_18.md`
  migration already uses, not a hand-edit.
- I did NOT fix this myself: it's squarely inside an actively in-flight, coordinated migration (the same commit family
  as instruments-service `639591f6` "cefi manifest canonicalization v2" + UAC `11adf279`, both <1h old at time of
  filing) that another agent/slot is clearly already driving. Hand-editing tests / golden files mid-migration without
  that context risks colliding with in-flight work.

## Recommended decision

Whoever owns the CEFI canonicalization migration (check `cefi_consolidated_closeout_2026_07_18.md` /
`master_data_canonicalisation_migration_catalogue_2026_06_07.md` for the active owner) should:

1. Remove/update the 3 DERIBIT-COMBO-specific tests in `test_factory_comprehensive.py` +
   `test_cefi_tradfi_comprehensive.py` to match the deregistration (delete if DERIBIT-COMBO is fully retired, or assert
   the loud `ValueError` if that's now the intended behavior).
2. Regenerate the `test_expected_universe_golden.py` cefi golden fixture via its owning migration's regen script.
3. Update the `_PER_AG_TARGET_COUNTS["CEFI"]` expected count in `test_pipeline_e2e_prediction.py` from 25 to the new
   correct value (currently observes 26; confirm this is the intended steady-state, not a further symptom of drift,
   before hard-coding it).
4. Confirm `test_check_enumeration_completeness.py`'s 2 failures are the same root cause (both reference the
   enumerated-venues fraction/columns) and fix alongside.

## Todos

- [ ] [BACKEND] P1. Update instruments-service's DERIBIT-COMBO-specific factory/routing tests
      (`tests/unit/test_factory_comprehensive.py::TestFactoryTardisRouting`,
      `tests/unit/test_cefi_tradfi_comprehensive.py::TestDeribitComboAdapter`) to match UAC `11adf279`'s deregistration
      (repo: instruments-service).
- [ ] [BACKEND] P1. Regenerate the CEFI expected-universe golden fixture consumed by
      `tests/unit/scripts/test_expected_universe_golden.py::TestGoldenByteIdentical::test_expected_matches_golden[cefi]`
      via the canonicalization migration's own regen script (repo: instruments-service).
- [ ] [BACKEND] P1. Fix `_PER_AG_TARGET_COUNTS["CEFI"]` in `tests/unit/test_pipeline_e2e_prediction.py` (currently
      hard-coded `25`, observed `26` post-purge) + the 2 related `test_check_enumeration_completeness.py` failures
      (repo: instruments-service).
- [ ] [BACKEND] P2. Re-run instruments-service `quality-gates.sh` full (not `--no-fix`) after the above 3 land, to
      confirm the whole suite is green before UAC's `11adf279` promotes LDR→main and starts failing `quality-gates-v2`
      on every instruments-service PR (repo: instruments-service).

## Codex SSOTs

- `codex/08-workflows/ci-cd-flow.md` § "Local ↔ CI QG parity matrix" (this is exactly the tracked local-ahead-of-CI
  divergence class it names).
