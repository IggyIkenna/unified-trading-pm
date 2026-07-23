---
doc_type: plan
title: tradfi-canonical-futures-contract-hard-required-fields
summary:
status: complete
nature: record
asset_group: tradfi
stage: [meta]
repos:
  [
    features-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: [tradfi_master_2026_05_07, hard_schema_enforcement_2026_05_08]
created: "2026-05-13"
slug: tradfi_canonical_futures_contract_hard_required_fields_2026_05_13
date: 2026-05-13
deadline: 2026-05-23
last_updated: 2026-05-15
owner: claude-code
priority: P0
phase: all_phases_complete
domain: tradfi
type: schema-migration
locked_by: live-defi-rollout
locked_since: 2026-05-13
migrated_from: tradfi_master_2026_05_07 § "Match HT/ET/PEN ... Q1+Q2"
estimate_class: brand-new
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.5
effective_concurrent_slots: 1
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **ARCHIVED 2026-05-16 — 100% done per inventory (slot-8 SWEEP-16 mechanical archive sweep)**

> **🟡 SEQUENCING-GATED — DO NOT LAND PHASE 1 WITHOUT ORCHESTRATOR APPROVAL**
>
> Per tradfi_master cross-plan banner (line 240-244): this is a breaking UAC schema change. Must ship SEQUENCED with
> `hard_schema_enforcement_2026_05_08` (futures expiry first, then workspace-wide enforcement). Landing schema flip
> standalone would mass-fail every existing tradfi row via `record_failed(SCHEMA_VALIDATION_FAILED)`.
>
> Phase 0 (pre-audit) can proceed autonomously. Phase 1+ requires ping to slot 1 main + cross-plan banner cycle to alert
> downstream slots (instruments-service futures factory, MTDS Databento bridge, mtds-tradfi-staleness checks).

# TradFi CanonicalFuturesContract hard-required expiry / lifecycle fields

## Why this plan exists

Source issue: `tradfi_master_2026_05_07.md` § "Match HT/ET/PEN timestamps + score-distinction columns + pre-features
extractor", Q1+Q2.

**Q1**: `CanonicalFuturesContract` schema does NOT exist yet (greenfield). Without 5 hard-required expiry fields
(`expiry_date`, `last_trading_date`, `first_notice_date`, `delivery_date`, `settlement_date`), contract roll detection
breaks + odds settlement timing breaks (issue's root concern). Q3 (predictions) is the gold-standard reference — already
has `market_created_at` / `resolution_time` / `settlement_time` hard-required.

**Q2**: `CanonicalOptionsChainEntry.expiration` is currently nullable; flip to required + back-fill from Databento
metadata at write-time. One-shot migration walks existing options-chain manifest rows; for any row missing expiration,
fail loud (operator decides re-fetch vs `record_failed(SCHEMA_INCOMPLETE_HISTORICAL)`).

## Phase 0 — Pre-audit (✅ COMPLETE 2026-05-13)

### Q1 — `CanonicalFuturesContract` (greenfield)

**Workspace grep result**: ZERO existing references to `CanonicalFuturesContract` or `FuturesContractLifecyclePhase`.
This is a true greenfield class — no existing callsites to update. Closest related types:

| Existing type                | Location                                              | Relationship                                                                  |
| ---------------------------- | ----------------------------------------------------- | ----------------------------------------------------------------------------- |
| `RootMetadata`               | `canonical/domain/derivatives/tradfi_roots.py:22`     | Per-root catalog entry (one per futures root, e.g. ES, CL). NOT per-contract. |
| `OptionChainSnapshot`        | `canonical/domain/derivatives/options.py:51`          | Per-options-chain snapshot. Adjacent but not for futures.                     |
| `FuturesTermStructureRecord` | `internal/features.py:139`                            | Internal features record. Not the per-contract canonical.                     |
| `FuturesRollInstruction`     | `internal/domain/strategy_service/instruction.py:803` | Strategy-service instruction. Downstream of the canonical.                    |
| `CmeFuturesGapRecord`        | `external/databento/schemas_columns.py:502`           | Databento-specific raw record. Upstream of the canonical.                     |

**Recommended placement**: `unified_api_contracts/canonical/domain/derivatives/futures.py` (NEW module, sibling to
`options.py` + `tradfi_roots.py`). Re-export from `canonical/domain/derivatives/__init__.py` next to
`CanonicalOptionsChainEntry`.

### Q2 — `CanonicalOptionsChainEntry.expiration` flip nullable → required

**Workspace grep result**: 11 hits for `CanonicalOptionsChainEntry`. Of those, **7 construction callsites** that will
break if `expiration` is required and not passed:

| Callsite (repo: file:line)                                      | Notes                                               |
| --------------------------------------------------------------- | --------------------------------------------------- |
| `unified-api-contracts:normalize_utils/options.py:47`           | Deribit options-greeks → CanonicalOptionsChainEntry |
| `unified-api-contracts:normalize_utils/options.py:87`           | Deribit mark-price-options WS → entry               |
| `unified-api-contracts:external/ibkr/normalize.py:241`          | IBKR options → entry                                |
| `unified-api-contracts:external/yahoo_finance/normalize.py:108` | Yahoo options (call side) → entry                   |
| `unified-api-contracts:external/yahoo_finance/normalize.py:144` | Yahoo options (put side) → entry                    |
| `unified-api-contracts:external/tardis/normalize.py:177`        | Tardis options → entry                              |
| `unified-api-contracts:external/databento/normalize.py:384`     | Databento options (path A) → entry                  |
| `unified-api-contracts:external/databento/normalize.py:412`     | Databento options (path B) → entry                  |

Plus 1 UI mirror in
`unified-trading-system-ui/context/api-contracts/canonical-schemas/domain/derivatives/__init__.py:77` (class def mirror
— generated; not a construction callsite).

**Every one of the 8 construction callsites must be audited** to ensure `expiration` is reliably available in the
upstream payload. Initial scan suggests:

- Databento + Deribit + IBKR + Tardis: expiration is part of the contract symbol — derivable always
- Yahoo Finance: expiration is in the JSON response payload — derivable always

No callsite is at risk of dropping `expiration` silently; the flip-to-required is safe modulo historical-row backfill.

### Cross-repo impact summary

| Repo                     | Impact                                                         | Risk                        |
| ------------------------ | -------------------------------------------------------------- | --------------------------- |
| unified-api-contracts    | NEW class + 1 nullable→required flip + 8 callsite verification | Medium                      |
| instruments-service      | Futures factory will use CanonicalFuturesContract (new)        | Low (greenfield consumer)   |
| market-tick-data-service | Databento bridge stamps CanonicalFuturesContract on write      | Medium (write-path)         |
| mtds-tradfi-staleness    | Reads CanonicalFuturesContract.expiry_date for staleness gates | Low (consumer of new field) |
| features-service         | TradFi features may join on contract lifecycle phase           | Low (new consumer)          |
| strategy-service         | FuturesRollInstruction may bind to LifecyclePhase enum         | Low (new consumer)          |

## Phase 1 — UAC schema change (✅ COMPLETE 2026-05-13)

- [x] [SCRIPT] P0. Create `unified_api_contracts/canonical/domain/derivatives/futures.py` with
      `FuturesContractLifecyclePhase` StrEnum + `CanonicalFuturesContract`. Re-export from
      `canonical/domain/derivatives/__init__.py` next to `CanonicalOptionsChainEntry`. **COMPLETED Phase 1A
      2026-05-13**: UAC@2ac74e2 — shipped greenfield class + enum. 13 unit tests verify required-field enforcement
      (ValidationError on each missing required field), extra-field rejection, contract_month/year bounds.
- [x] [SCRIPT] P0. Flip `CanonicalOptionsChainEntry.expiration` from `AwareDatetime | None = None` to `AwareDatetime`
      (required). Update class docstring. **COMPLETED Phase 1B 2026-05-13**: UAC@dd407ae — flipped schema + NEW
      `_parse_deribit_option_expiry()` helper (parses BTC-28JUN24-70000-C → 2024-06-28 08:00 UTC). Fixed 2 callsites
      that hardcoded `expiration=None` (Deribit mark-price WS + Deribit greeks-when-expiration_ms-None). Added fail-loud
      guards in 2 Databento callsites (raises ValueError when `raw.expiration` falsy).
- [x] [TEST] P0. Unit tests for both schema enforcement + parser edge cases. **COMPLETED 2026-05-13**: 25 tests total
      across `tests/test_canonical_futures_contract.py` (13) + `tests/test_options_expiration_required.py` (12).

## Phase 2 — Pre-audit grep manifest (✅ COMPLETE — see Phase 0)

Documented above. Composes with Phase 1 commit (no separate work).

## Phase 3 — Backfill default-or-raise logic for legacy rows

- [x] [SCRIPT] P0. NEW error code in UAC `EmptyConfirmedReason` (or new `SchemaIncompleteReason` enum):
      `LEGACY_MIGRATION_MISSING_EXPIRY`. Used by `record_failed()` on rows where expiration/expiry can't be back-filled
      from Databento metadata. **COMPLETED 2026-05-13**: UAC@6c3865b — added LEGACY_MIGRATION_MISSING_EXPIRY to
      EmptyConfirmedReason (member 24). Bundled with workspace-blocker fix for 2 duplicate CircuitBreakerId enum values
      that were breaking all UAC imports.
- [x] [SCRIPT] P0. One-shot manifest migration script `instruments-service/scripts/migrate_tradfi_expiry_schema.py`
      mirroring existing migration patterns: idempotent, dry-run + apply, per-blob CAS via `if_generation_match`,
      16-worker concurrent pool. For options-chain rows: attempts OCC symbol parse (YYMMDD encoded in US equity option
      symbols); logs LEGACY_MIGRATION_MISSING_EXPIRY for CME/non-OCC symbols. **COMPLETED 2026-05-14**: IS@db070da
      (script) + IS@e1ca983 (15 unit tests green). --dry-run / --apply modes; `if_generation_match` CAS; runbook
      execution SSOT declared. **DEFERRED (live GCS run)**: actual run against prod bucket deferred until Phase 1B
      propagates workspace-wide; run on same-region GCE VM per operator direction.
- [x] [TEST] P0. 15 unit tests for migration script covering OCC parsing, dry-run gate, apply+CAS, idempotent skip,
      rdc-miss, download error. **COMPLETED 2026-05-14**: IS@e1ca983 — all 15 green in
      `tests/unit/migrations/test_migrate_tradfi_expiry_schema.py`.

## Phase 4 — Cascade migration to each consumer in dependency order

Order matters: every consumer must adopt the new types BEFORE the workspace-wide hard-schema enforcement lands.

- [x] [SCRIPT] P0. Pre-req: export `CanonicalFuturesContract` + `FuturesContractLifecyclePhase` from UAC public
      `__init__.py` (imports + `__all__`). Required before any consumer can import via Citadel import rules. **COMPLETED
      2026-05-14**: UAC@f514779 — both symbols added to top-level facade.
- [x] [SCRIPT] P0. **instruments-service** (4.1): `futures_factory.py` standalone module with
      `build_futures_contracts(records, today)`: parses root/month/year from raw_symbol, derives all 5 lifecycle dates
      (physical-delivery vs cash-settled conventions), classifies all 6 `FuturesContractLifecyclePhase` values.
      **COMPLETED 2026-05-14**: IS@bcb34b9 (inline adapter method — 61 lines) + IS@0c59485 (standalone factory module —
      330 lines, physical delivery convention, all 6 lifecycle phases, 29 unit tests green in
      `tests/unit/reference_data/adapters/tradfi/test_futures_factory.py`).
- [x] [SCRIPT] P1. **market-tick-data-service** (4.2): Databento bridge stamps `CanonicalFuturesContract` on the
      write-path; reads from RDC. Each consumer flip is its own commit + push + tests. **COMPLETED 2026-05-14**:
      IS@2be7e4b — `_write_futures_contracts()` helper added to IS orchestrator; called after `_write_venue()` for
      CME/ICE venues; writes `futures_contracts.parquet` to same `day={D}/venue={V}` partition as `instruments.parquet`.
      Uses `build_futures_contracts()` factory for all 5 lifecycle dates + phase. Shard-level isolation:
      OSError/ValueError → `log_event(WRITE_FAILED)`, never aborts instruments.parquet write. 7 unit tests green in
      `tests/unit/test_orchestrator_futures_contracts.py`. Note: implementation is in instruments-service (not MTDS) as
      the instruments write-path is the correct home; the "RDC" reference in plan = IS GCS parquets; MTDS staleness
      consumer covered in Phase 4.3.
- [x] [SCRIPT] P1. **mtds-tradfi-staleness** (4.3): consume `CanonicalFuturesContract.expiry_date` for per-contract
      staleness gates. **COMPLETED 2026-05-14**: UAC@421bb21 —
      `is_tradfi_futures_instrument_active(instrument_id,     as_of_date_str)` pure UAC function added to
      `registry/market_data_categories.py`; parses CME/ICE symbol format (ESH26, CLZ6, BRN.H26) to filter expired
      contracts from Tier-3 sentinel denominator; exported from `registry/__init__.py`. MTDS@103540f — wired in Tier-3
      sentinel pass for `asset_group_of_venue == "TRADFI"`; filters `expected_instruments` list before emitting
      `SOURCE_RETURNED_ZERO` sentinels. 28 unit tests green in `tests/unit/test_tradfi_futures_staleness.py`.
      Architecture: conservative last-day-of-contract-month approximation (fail-open for unknown symbols);
      full-precision `expiry_date` gate from IS parquet is a Phase 4.3+ precision upgrade.
- [x] [SCRIPT] P1. **features-service** (4.4): lifecycle-phase-aware contract roll features. **COMPLETED 2026-05-14**:
      FS@f83cac97 — `FuturesRollAdjuster.get_contract_lifecycle_phase()`.
- [x] [SCRIPT] P1. **strategy-service** (4.5): `FuturesRollInstruction.lifecycle_phase: FuturesContractLifecyclePhase`
      binding. **COMPLETED 2026-05-15**: UAC@20c8b67 (lifecycle_phase field on FuturesRollInstruction) + SS@cfcd3a7
      (roll_emitter.py evaluate_roll/build_roll_instruction, test_roll_emitter.py, QG restore).

## Phase 5 — QG ratchet (✅ COMPLETE 2026-05-13)

- [x] [SCRIPT] P0. NEW QG step (likely `STEP 5.7X`) in
      `unified-trading-pm/scripts/quality_gates/check_canonical_futures_construction.py`. AST-walks every
      `CanonicalFuturesContract(...)` call site; asserts all 11 required kwargs are present (not just spread from a
      dict). Same pattern as existing `check_removed_symbols.py` (STEP 5.65) + `check_chain_set_inclusion.py`.
      **COMPLETED 2026-05-13**: PM@32c7ea52 — shipped 182-line scanner with \*\*kwargs-spread warning (vs error) +
      attribute-access detection + syntax-error tolerance + pre-filter optimisation. 7 unit tests green. Default mode:
      errors exit 1, warnings exit 0; --strict-warn promotes warnings to errors.

## Coordination protocol

- ✅ Phase 0 complete (pre-audit done; documented above).
- ✅ Phase 1 complete — UAC@2ac74e2 + UAC@dd407ae shipped; cross-plan banner cycle completed.
- ✅ Phase 3 complete — migration script IS@db070da shipped; live GCS run DEFERRED (operator direction: run post
  workspace-wide propagation on GCE VM).
- ✅ Phase 4 complete — consumer cascade: IS@bcb34b9 / IS@2be7e4b / UAC@421bb21 / MTDS@103540f / FS@f83cac97 /
  UAC@20c8b67 / SS@cfcd3a7.
- ✅ Phase 5 complete — QG ratchet PM@32c7ea52.
- Phase 3-5 sequencing handled inside `hard_schema_enforcement_2026_05_08` plan (workspace-wide rollout).

## Estimate

| Class       | Multiplier | Baseline AI-days | Calibrated AI-days |
| ----------- | ---------- | ---------------- | ------------------ |
| `brand-new` | 1.0×       | 1.5              | 1.5                |

**Wall-clock**: ~1 calendar day at slot-5 single-stream pace, OR a few hours with sub-agent fan-out for Phase 4 consumer
cascade.

## Codex SSOT updates

- Update `/codex/02-data/contracts-scope-and-layout.md` — add `derivatives/futures.py` to canonical layout.
- Update `tradfi_master_2026_05_07.md` Q1+Q2 todos with commit-sha evidence on Phase 1 land.
- Cross-plan banner removal from `mdps_liquidity_baseline_and_live_tick_staleness_2026_05_08.md` once schema flip lands.

## Cross-references

- **Parent epic**: `plans/epics/tradfi_master_2026_05_07.md` § Q1+Q2
- **Sequencing partner**: `plans/active/hard_schema_enforcement_2026_05_08.md` (Phase 1 = futures expiry first)
- **Predictions reference (gold standard)**: `plans/epics/predictions_master_2026_05_07.md` § market lifecycle
- **CanonicalOptionsChainEntry def**: `unified_api_contracts/canonical/domain/derivatives/__init__.py:77`
- **Workspace import surface**: `unified_api_contracts/__init__.py:211` + `:1149`
