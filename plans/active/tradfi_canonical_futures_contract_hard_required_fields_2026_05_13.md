---
name: tradfi-canonical-futures-contract-hard-required-fields
slug: tradfi_canonical_futures_contract_hard_required_fields_2026_05_13
date: 2026-05-13
deadline: 2026-05-23
last_updated: 2026-05-13
owner: claude-code
status: pending_approval
priority: P0
phase: phase_0_pre_audit_complete
domain: tradfi
asset_group: tradfi
type: schema-migration
locked_by: live-defi-rollout
locked_since: 2026-05-13
migrated_from: tradfi_master_2026_05_07 § "Match HT/ET/PEN ... Q1+Q2"
estimate_class: brand-new
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.5 # brand-new × 1.0
effective_concurrent_slots: 1
related_plans:
  - tradfi_master_2026_05_07
  - hard_schema_enforcement_2026_05_08
---

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

## Phase 1 — UAC schema change (BLOCKED on orchestrator approval)

- [ ] [SCRIPT] P0. Create `unified_api_contracts/canonical/domain/derivatives/futures.py` with: -
      `FuturesContractLifecyclePhase` StrEnum: `LISTED | ACTIVE | IN_FIRST_NOTICE | IN_DELIVERY | EXPIRED | SETTLED` -
      `CanonicalFuturesContract` (CanonicalBase) with 5 hard-required date/datetime fields (`expiry_date`,
      `last_trading_date`, `first_notice_date`, `delivery_date`, `settlement_date`) + `lifecycle_phase` + `venue`,
      `root`, `contract_symbol` (e.g. "ESH26"), `contract_month`, `contract_year`, `tick_size`, `contract_size`. Each
      date has explicit timezone (CME Central Time for CME products; venue-local for non-CME). - Re-export from
      `canonical/domain/derivatives/__init__.py` next to `CanonicalOptionsChainEntry`.
- [ ] [SCRIPT] P0. Flip `CanonicalOptionsChainEntry.expiration` from `AwareDatetime | None = None` to `AwareDatetime`
      (required). Update class docstring.
- [ ] [TEST] P0. Unit tests: instantiate `CanonicalFuturesContract` with all required fields; assert
      `TypeError`/`ValidationError` if any required field omitted. Same for `CanonicalOptionsChainEntry.expiration`.

## Phase 2 — Pre-audit grep manifest (✅ COMPLETE — see Phase 0)

Documented above. Composes with Phase 1 commit (no separate work).

## Phase 3 — Backfill default-or-raise logic for legacy rows

- [ ] [SCRIPT] P0. NEW error code in UAC `EmptyConfirmedReason` (or new `SchemaIncompleteReason` enum):
      `LEGACY_MIGRATION_MISSING_EXPIRY`. Used by `record_failed()` on rows where expiration/expiry can't be back-filled
      from Databento metadata.
- [ ] [SCRIPT] P0. One-shot manifest migration script `instruments-service/scripts/migrate_tradfi_expiry_schema.py`
      mirroring existing migration patterns: idempotent, dry-run + apply, per-blob CAS via `if_generation_match`,
      `2*workers` HTTP pool per workspace rules. For options-chain rows: try Databento `RDC` (reference-data) lookup by
      symbol; on miss, `record_failed(reason=     LEGACY_MIGRATION_MISSING_EXPIRY)`. For futures rows (new schema):
      write fresh per-contract rows with all 5 dates.

## Phase 4 — Cascade migration to each consumer in dependency order

Order matters: every consumer must adopt the new types BEFORE the workspace-wide hard-schema enforcement lands.

1. **instruments-service**: futures factory emits `CanonicalFuturesContract` per known root/month combo.
2. **market-tick-data-service**: Databento bridge stamps `CanonicalFuturesContract` on the write-path; reads from RDC.
3. **mtds-tradfi-staleness**: consume `CanonicalFuturesContract.expiry_date` for per-contract staleness gates.
4. **features-service**: lifecycle-phase-aware contract roll features.
5. **strategy-service**: `FuturesRollInstruction.lifecycle_phase: FuturesContractLifecyclePhase` binding.

Each consumer flip is its own commit + push + tests.

## Phase 5 — QG ratchet

- [ ] [SCRIPT] P0. NEW QG step (likely `STEP 5.7X`) in
      `unified-trading-pm/scripts/quality_gates/check_canonical_futures_construction.py`. AST-walks every
      `CanonicalFuturesContract(...)` call site; asserts all 5 required kwargs are present (not just spread from a
      dict). Same pattern as existing `check_removed_symbols.py` (STEP 5.65) + `check_chain_set_inclusion.py`.

## Coordination protocol

- ✅ Phase 0 complete (pre-audit done; documented above).
- ⏸️ Phase 1 BLOCKED — ping main before landing the breaking UAC schema commit. Main coordinates cross-plan banner cycle
  to alert downstream slots.
- Phase 3-5 sequencing handled inside `hard_schema_enforcement_2026_05_08` plan (workspace-wide rollout).

## Estimate

| Class       | Multiplier | Baseline AI-days | Calibrated AI-days |
| ----------- | ---------- | ---------------- | ------------------ |
| `brand-new` | 1.0×       | 1.5              | 1.5                |

**Wall-clock**: ~1 calendar day at slot-5 single-stream pace, OR a few hours with sub-agent fan-out for Phase 4 consumer
cascade.

## Codex SSOT updates

- Update `codex/02-data/contracts-scope-and-layout.md` — add `derivatives/futures.py` to canonical layout.
- Update `tradfi_master_2026_05_07.md` Q1+Q2 todos with commit-sha evidence on Phase 1 land.
- Cross-plan banner removal from `mdps_liquidity_baseline_and_live_tick_staleness_2026_05_08.md` once schema flip lands.

## Cross-references

- **Parent epic**: `plans/epics/tradfi_master_2026_05_07.md` § Q1+Q2
- **Sequencing partner**: `plans/active/hard_schema_enforcement_2026_05_08.md` (Phase 1 = futures expiry first)
- **Predictions reference (gold standard)**: `plans/epics/predictions_master_2026_05_07.md` § market lifecycle
- **CanonicalOptionsChainEntry def**: `unified_api_contracts/canonical/domain/derivatives/__init__.py:77`
- **Workspace import surface**: `unified_api_contracts/__init__.py:211` + `:1149`
