---
doc_type: issue
title: B23 determination — the 51/85-column instruments schema is not locked or versioned; 4-part fix
summary: >-
  B23 (data_pipeline_completion_2026_08_21.md) asks whether INSTRUMENTS_PARQUET_SCHEMA is locked and versioned.
  Determination: NO — no version field exists on the schema or its SchemaContract wrapper, the per-asset-group
  contracts synthesised from it are never consulted by any writer/reader, and no golden/hash test would catch a
  silent column change. This doc carries the 4-part fix as tracked, AO-dispatchable todos.
status: resolved # 2026-08-22 -- all 4 parts [x], last part (schema-contract gate wiring) landed
  # instruments-service@a1fa51a0b9 + @a74de357f0
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-api-contracts, instruments-service]
scope: [engineer]
tags: [schema, versioning, data-pipeline-completion, b23]
related:
  [
    /plans/active/data_pipeline_completion_2026_08_21.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md,
  ]
context_scope:
  [
    unified-api-contracts/unified_api_contracts/internal/domain/instruments/_instruments_parquet_schema.py,
    unified-api-contracts/scripts/check_schema_versions.py,
    unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py,
    unified-api-contracts/unified_api_contracts/internal/schemas/_instrument_catalogue_contract.py,
    instruments-service/instruments_service/engine/orchestrator/sink.py,
    /plans/active/data_pipeline_completion_2026_08_21.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-18"
parent_epic: uac_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: T2 session 2026-08-22 -- part 4 wired + shipped (instruments-service@a1fa51a0b9, @a74de357f0)
depends_on: []
author: data_engineering (slot 9)
source: [/plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md item 3]
---

> **📦 ARCHIVED 2026-08-22** — all 4 parts of the fix [x]; part 4 (schema-contract gate wiring at
> `promote_catalogue`) landed as `instruments-service@a1fa51a0b9` (gate code, byproduct of a sibling agent's
> monthly-rollup commit sharing the same function) + `@a74de357f0` (regression test + dedup-guard test fix).
> Kept as a historical record of the reconciliation decision (writer-authoritative,
> `INSTRUMENTS_CATALOGUE_SCHEMA_VERSION`) and the dtype-normalization gap found while wiring the gate.

# B23 determination — instruments schema is not locked/versioned; 4-part fix

## What I found

`INSTRUMENTS_PARQUET_SCHEMA` (`unified-api-contracts/unified_api_contracts/internal/domain/instruments/_instruments_parquet_schema.py`)
is a bare `list[dict]` literal, currently 85 columns (grown silently from the "51-column" figure B23's own title still
carries — no changelog entry or version bump marks when or why). Full evidence trail is recorded in
`data_pipeline_completion_2026_08_21.md`'s B23 blockquote (updated 2026-08-18). In short: the schema has no version
field, the framework that versions OTHER UAC schemas (`CANONICAL_*_VERSION` + `check_schema_versions.py`) explicitly
excludes it, the per-asset-group `SchemaContract`s synthesised from it are registered but never consulted by any
consumer, and no test would catch a silent column add/remove/retype.

## Why it matters

B23 exists because of a real incident (2026-04-14: 85 `entity=fixtures_schedule` shards silently carried an
instrument-catalogue shape instead of fixtures data, undetected until a downstream column-projection read failed).
The one guard that exists for that incident class (`sink.py::_assert_not_cross_domain_contamination`) is narrow and
reactive — it would not catch an in-place change to the instrument-catalogue schema itself, which is exactly what
"locked and versioned" is meant to prevent.

## Recommended decision

Implement the 4-part fix below, in order (each part is independently useful; later parts depend on earlier ones
landing in the same repo so they are NOT concurrent-dispatchable against each other — sequential within this doc).

- [x] ✅ [DATA] P1. Add `INSTRUMENTS_SCHEMA_VERSION: str = "1.0.0"` as a module-level constant in
      `unified-api-contracts/unified_api_contracts/internal/domain/instruments/_instruments_parquet_schema.py`,
      following the same pattern as UAC's existing `CANONICAL_*_VERSION` constants elsewhere in the repo. Repo:
      unified-api-contracts. Done-when: the constant exists, is exported, and a unit test asserts its value.
      — unified-api-contracts@88a62935 (2026-08-19): `INSTRUMENTS_SCHEMA_VERSION: str = "1.0.0"` added to
      `_instruments_parquet_schema.py` + exported via its `__all__` and the `internal.domain.instruments` package
      re-export; unit test `tests/unit/test_instruments_parquet_schema_version.py` asserts the value. QG green
      (294s), quickmerge landed + ancestry-verified on LDR.
- [x] ✅ [DATA] P1. Extend `unified-api-contracts/scripts/check_schema_versions.py` (or add a sibling script) to also
      cover `internal/domain/instruments/` — its current `_get_files()` only walks `canonical/domain/` +
      `canonical/execution.py`. Pair with a checked-in golden file (column name+type+order, or a content hash of
      `INSTRUMENTS_PARQUET_SCHEMA`) compared on every test run; a mismatch fails UNLESS `INSTRUMENTS_SCHEMA_VERSION`
      was also bumped in the same change. Depends on the todo above (needs the version constant to exist). Repo:
      unified-api-contracts. Done-when: a deliberate schema-list edit without a version bump fails CI locally
      (`quality-gates.sh`), and the same edit WITH a version bump passes.
      — unified-api-contracts@d384e840b7: added `check_instruments_schema_lock.py`, a checked-in SHA-256 golden
      snapshot, and falsifier tests covering both unchanged-version failure and bumped-version success; quickmerge quality gates passed; commit is
      ancestry-verified on `origin/live-defi-rollout`.
- [x] ✅ [DATA] P2. Add a schema_version field to SchemaContract — unified-api-contracts@553c8e5f01 + Evidence: quality-gates.sh PASS; five catalogue contracts assert INSTRUMENTS_SCHEMA_VERSION
      (`unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py`, currently has none) and populate
      it from `INSTRUMENTS_SCHEMA_VERSION` in `_make_catalogue_contract()`
      (`unified-api-contracts/unified_api_contracts/internal/schemas/_instrument_catalogue_contract.py`). Depends on
      the first todo. Repo: unified-api-contracts. Done-when: `CEFI_INSTRUMENT_CATALOGUE.schema_version` (and the
      other 4 asset-group contracts) resolve to the same value as `INSTRUMENTS_SCHEMA_VERSION`.
- [x] ✅ [DATA] P0. **Reconcile `INSTRUMENTS_PARQUET_SCHEMA` with what the catalogue writer actually emits — this
      now gates part 4.** Measured 2026-08-20: writer emits 41 columns, contract declares 85, and 4 of the 6
      required columns (`instrument_key`, `symbol`, `available_from_datetime`, `timestamp`) are emitted by NO asset
      group. Decide which side is authoritative — the schema's `instrument_key`/`*_datetime` naming, or the
      writer's `instrument_id`/`available_from` — then align the other. Repo: unified-api-contracts (+ a follow-up
      writer change in instruments-service if the schema wins). Done-when: a real catalogue frame from
      `build_instrument_catalogue.py` produces ZERO violations from `validate_dataframe` against its own
      asset_group's contract.
      — unified-api-contracts@910d35da (2026-08-20): writer authoritative. `_instrument_catalogue_contract.py` now
      declares the 41 rolled-up catalogue columns (CATALOG_COLUMNS) explicitly under
      `INSTRUMENTS_CATALOGUE_SCHEMA_VERSION`, keyed on `instrument_id`; new `test_instrument_catalogue_contract.py`
      asserts a writer-shaped frame validates with zero violations. QG green (301s), quickmerge landed +
      ancestry-verified on LDR.
- [x] ✅ [DATA] P2. Wire the per-asset-group `SchemaContract`s to the instruments-service write path.
      **2026-08-22 (T2)**: re-verified the reconciliation independently before wiring — column names/order
      matched the writer's `CATALOG_COLUMNS` exactly (41/41) and `INSTRUMENTS_CATALOGUE_SCHEMA_VERSION` was
      genuinely populated, confirming T1's claim. Found one residual gap T1's own test suite missed: an
      entirely-row-absent column reindexes to `float64`/NaN (not `object`/`None`), which `validate_dataframe`
      flagged as `wrong_dtype` even though the column is legitimately all-null — broke 2 real end-to-end
      `run_rollup` tests. Fixed with a `_coerce_string_dtype_for_contract` normalizer. Wired
      `validate_dataframe(df, CONTRACT_REGISTRY[(asset_group, "instrument_catalogue", "instrument_catalogue")])`
      at `build_instrument_catalogue.py::promote_catalogue` (the correct choke point — NOT
      `sink.py::_assert_not_cross_domain_contamination`, which guards a different write path, the per-date
      `InstrumentRecord` sink, not the rolled-up catalogue promotion this todo targets), mirroring
      `CATALOGUE_SHRINK_BLOCKED` (CRITICAL `log_event` + `exit 1`, never a raise). Added
      `tests/unit/scripts/test_catalogue_schema_contract_gate.py` (valid frame promotes cleanly; missing required
      column rejected; renamed `instrument_key` id column rejected; unregistered asset_group degrades to a
      warning instead of crashing) and fixed 3 pre-existing `test_promote_catalogue_dedup_aware_guard.py` tests
      whose hand-rolled partial-column fixtures no longer satisfied the new gate. Full instruments-service test
      suite green (5476 passed, 0 failed) against the actually-landed code. Landed as two commits — a concurrent
      sibling agent's `instruments_catalogue_definitions_and_field_history_2026_08_17.md` writer work shares this
      exact function, so the gate code landed first as a byproduct of their commit
      (`instruments-service@a1fa51a0b9`), then this task's own regression coverage followed as a tightly-scoped
      fast-follow (`instruments-service@a74de357f0`) — both ancestor+content-verified on
      `origin/live-defi-rollout`.

## Progress Log

- **2026-08-22 (T2)**: part 4 (the last open todo) shipped — see the flipped checkbox above for full detail. All
  4 parts of the fix are now [x]. Not archived in this same edit (out of this session's scope) — flagging for a
  follow-up archival pass per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (0 open
  todos, unlocked).
- **2026-08-20 (slot 15, part 0)**: reconciled the instrument-catalogue contract with the writer. Decision: the
  writer (`build_instrument_catalogue.py::promote_catalogue`, 41-col `CATALOG_COLUMNS`) is authoritative — the
  `instrument_catalogue` SchemaContract was synthesised from the 85-col per-date `INSTRUMENTS_PARQUET_SCHEMA`, not
  the rolled-up catalogue it actually guards. `_instrument_catalogue_contract.py` now declares the 41 columns
  explicitly under `INSTRUMENTS_CATALOGUE_SCHEMA_VERSION` (decoupled from `INSTRUMENTS_SCHEMA_VERSION`), keyed on
  `instrument_id`. New `test_instrument_catalogue_contract.py` pins zero violations on a writer-shaped frame.
  Part 4 (wiring `validate_dataframe` at `promote_catalogue`) is now unblocked.
- **2026-08-20 (slot 10 completion)**: shipped the part-2 lock implementation as
  `unified-api-contracts@d384e840b7`. The standalone checker hashes the ordered schema list with sorted per-column
  keys, compares it to `scripts/instruments_parquet_schema.golden.json`, and reports drift only when the live
  `INSTRUMENTS_SCHEMA_VERSION` remains unchanged. Falsifier tests cover both no-bump failure and version-bump
  allowance. Quickmerge's re-gate passed all quality gates (284s); ancestry was verified on LDR.

- **2026-08-20 (T2 code-readiness tranche)**: **Part 4 is NOT implementable as written — the contract has never
  matched the writer.** Built the part-4 gate (`validate_dataframe` against
  `CONTRACT_REGISTRY[(ag, "instrument_catalogue", "instrument_catalogue")]` inside
  `build_instrument_catalogue.py::promote_catalogue`, which already receives `asset_group`), measured it, and
  reverted it rather than ship a change that would have blocked production promotion for all five asset groups.
  MEASURED: the writer's `CATALOG_COLUMNS` emits **41** columns against the contract's **85**, and **4 of the 6
  `required=True` columns are never emitted by the writer for ANY asset group** — `instrument_key`, `symbol`,
  `available_from_datetime`, `timestamp`. The writer's canonical identifier is `instrument_id`
  (`build_instrument_catalogue.py:279`: "`instrument_id` is written as the canonical column"), not the contract's
  `instrument_key`; the writer emits `available_from`/`available_to` where the contract declares
  `available_from_datetime`/`available_to_datetime`. Wiring the gate turned 3 existing `promote_catalogue` tests
  red with 80 violations on a cefi frame.

  **This reframes the issue.** "Registered but never consulted" is not merely an unused guard — it is why a
  never-fitting contract survived: the first real consumer fails immediately. So part 4's done-when ("a catalogue
  write with a column outside the locked+versioned contract is rejected at write time") cannot be met until the
  contract and the writer are reconciled, and that reconciliation is a UAC change with a real decision in it —
  either `INSTRUMENTS_PARQUET_SCHEMA` is wrong about the catalogue's shape, or the catalogue writer is wrong about
  its own canonical columns. Filed to T1 (`code_readiness_t1_contracts_library_externalapi_2026_08_19.md`), since
  UAC owns both the schema and the contracts. Adding a new part 0 below to carry that decision.

- **2026-08-18 (data_engineering, slot 9)**: filed from `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md`
  item 3 (B23 determination). Determination recorded in `data_pipeline_completion_2026_08_21.md`'s B23 blockquote.
  The 4-part fix is new discovered scope beyond that item's own done-when (determination + proposal only) — filed
  here per findings-triage rather than absorbed into the determination task.
- **context-scout 2026-08-19**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-20**: refreshed context_scope (6 entries).
