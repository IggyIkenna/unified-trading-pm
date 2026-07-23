---
doc_type: plan
title: Hard Schema Phase 1 — Field-Flip Migration Plan
summary:
status: complete
nature: record
asset_group: [defi]
stage: [meta]
repos: [instruments-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-19
parent_epic: defi_master
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-05-19
last_updated: 2026-05-19
completion_gates: { code: C3, deployment: D1, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C2, deployment: none, business: none }
  - { repo: instruments-service, code: C1, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on: [hard-schema-enforcement-2026-05-08, defi-catalogue-chain-primitives-2026-05-10]
todos:
  - { id: phase-a-defi-decimals-validator, content: "- [x] ✅ [CODE] P0. **Phase A — DeFi decimals model_validator
        rule.** — uac@956bec1. Rules 6+7 added to _enforce_per_asset_group_required_fields; 10 new tests; all QG green.
        (slot 4 2026-05-19)\n  `InstrumentRecord._enforce_per_asset_group_required_fields` currently enforces:\n    (1)
        CeFi SPOT_PAIR/PERPETUAL → base_asset + quote_asset non-empty\n    (2) DeFi ONCHAIN → pool_address OR
        base_asset_contract_address non-empty\n    (3) EVENT_CONTRACT → expiry non-null\n    (4) FUTURE → expiry
        non-null\n    (5) OPTION → expiry non-null\n  **Gap**: no rule for `base_asset_decimals` or
        `quote_asset_decimals`. These are\n  required for on-chain price calculation in MTDS DeFi handlers (dex_pools
        reads\n  token0/token1 decimals for price; A_TOKEN/DEBT_TOKEN reads base decimals for\n  normalization). Add two
        rules:\n    6. DeFi `base_asset_decimals` non-null for ALL `DEFI_ONCHAIN_INSTRUMENT_TYPES`\n       (POOL /
        LENDING / LST / YIELD_BEARING / A_TOKEN\
        \ / DEBT_TOKEN / STAKING / SPOT_ASSET).\n       Rationale: every DeFi instrument has a primary token with a
        decimals value (18 for\n       most ERC-20s, 6 for USDC, 8 for WBTC). Null decimals = silent price normalization
        bug.\n    7. DeFi `quote_asset_decimals` non-null for TWO-ASSET DeFi types: `{POOL}`
        only.\n       LENDING/LST/STAKING/A_TOKEN/DEBT_TOKEN/SPOT_ASSET are single-asset → quote
        decimals\n       legitimately None. POOL (Uniswap V3 / Curve / Balancer) requires both token0 and\n       token1
        decimals for price computation.\n  Implementation: extend `_enforce_per_asset_group_required_fields` with two
        `elif`\n  branches OR fold into the existing DeFi on-chain branch as additional checks.\n  Unit tests: extend
        `tests/internal/unit/test_instrument_record_hard_required_fields.py`.\n", status: todo }
  - { id: phase-b-null-decimals-gcs-audit-script, content: "- [x] ✅ [SCRIPT] P0. **Phase B — Null-decimals GCS audit
        script.** — instruments-service@1f807c9. `scripts/audit_defi_null_decimals_2026_05_19.py` — scans DeFi parquets
        for null base/quote decimals; read-only; per-venue/per-type report; JSON output. (slot 4 2026-05-19)\n  Write
        `instruments-service/scripts/audit_defi_null_decimals_2026_05_19.py`:\n  ```python\n  # Usage: python
        audit_defi_null_decimals_2026_05_19.py --asset-group defi --dry-run\n  # Scans
        gs://instruments-store-defi-prod-{PROJECT_ID}/.../*.parquet\n  # Reads base_asset_decimals +
        quote_asset_decimals columns\n  # For each row where instrument_type in DEFI_ONCHAIN_INSTRUMENT_TYPES:\n  #   -
        null base_asset_decimals → record to audit report (pool_address, venue, date)\n  # For POOL rows: null
        quote_asset_decimals → same\n  # Output: JSON summary + sample rows for manual classification\n  ```\n  The
        script must respect CLAUDE.md \"Plans Run To Actual Completion\":\n \
        \ - Reads from GCS via `unified_trading_library.cloud_interface`\n  - Prints null-count summary by venue +
        instrument_type\n  - Outputs `audit_defi_null_decimals_{date}.json` to local path\n  - Does NOT write to GCS
        (read-only audit)\n  Pre-condition: Phase A model_validator shipped so new rows won't add to null count.\n", status: todo }
  - { id: phase-c-cefi-empty-string-audit, content: "- [x] ✅ [SCRIPT] P1. **Phase C — CeFi empty-string base/quote
        audit (verification only).** — instruments-service@46bea40. `scripts/audit_cefi_empty_base_quote_2026_05_19.py`
        — scans CeFi parquets for empty base_asset/quote_asset in SPOT_PAIR/PERPETUAL rows; read-only; per-venue count
        table; JSON output. (slot 4 2026-05-19)\n  `InstrumentRecord.base_asset` and `quote_asset` are already `str =
        \"\"` (non-nullable\n  at declaration level). Model_validator Rule 1 enforces non-empty at write-time.
        This\n  phase is a verification that the existing constraint is working:\n  Scan
        `gs://instruments-store-cefi-prod-{PROJECT_ID}/.../*.parquet` for rows where\n  `base_asset == \"\"` or
        `quote_asset == \"\"` AND `instrument_type` is in\n  `CEFI_PAIR_INSTRUMENT_TYPES`. Expected count: 0 (any
        non-zero is a bug in the adapter\n  or a pre-Phase-1 legacy row). Output: count per venue + sample rows if
        any.\n  If count > 0: file separate issue doc with adapter\
        \ fix required.\n  Note: this is a DEFENSIVE verification, not a migration. The declaration already\n  enforces
        `str`; the model_validator enforces non-empty. Nothing to flip.\n", status: todo }
  - {
      id: phase-d-per-field-declaration-status-table,
      content:
        "- [x] ✅ [DOCS] P1. **Phase D — Per-field declaration status table in plan body.** — unified-trading-pm (this
        commit). `plans/active/hard_schema_enforcement_2026_05_08.md` \"Per-asset-group schema-flip roadmap\" section
        updated with corrected per-field status table showing Rules 6+7 shipped at uac@956bec1. (slot 4
        2026-05-19)\n  Update the \"Per-asset-group schema-flip roadmap\" section
        in\n  `hard_schema_enforcement_2026_05_08.md` with the corrected per-field status:\n  | Field | Current type |
        Model validator | Declaration flip needed? |\n  |\n",
    }
---

> **ARCHIVED 2026-05-21** — Phases A-D complete (field-flip validators for CeFi/DeFi + InstrumentRecord validators + QG
> STEP). Phase E (subclass design for expiry declaration-level enforcement) DEFERRED-POST-CUTOVER → successor:
> `uac_venue_metadata_gap_fill_2026_06_xx.md`. status: active → archived.

|---|---|---| | `base_asset` | `str = ""` | ✅ Rule 1 (CeFi) | No — already str; add Field(min_length=1) if desired | |
`quote_asset` | `str = ""` | ✅ Rule 1 (CeFi) | No — already str | | `pool_address` | `str \| None` | ✅ Rule 2
(disjunctive) | No — disjunctive can't express in type alone | | `base_asset_contract_address` | `str \| None` | ✅ Rule
2 (disjunctive) | No — same | | `base_asset_decimals` | `int \| None` | ❌ NOT YET (Phase A this plan) | Phase A ships
validator; declaration stays Optional | | `quote_asset_decimals` | `int \| None` | ❌ NOT YET for POOL (Phase A) | Phase
A ships validator for POOL type | | `expiry` | `datetime \| None` | ✅ Rules 3/4/5 (FUTURE/OPTION/EVENT_CONTRACT) | No —
legitimately None for non-futures | | Sports `fixture_id` | `str` on all per-fixture entities | Already non-optional |
None needed | | `CanonicalInjury.fixture_id` | `str \| None` | N/A — legitimate optional | Pre-season injuries don't
have a fixture_id | status: todo

- id: phase-e-subclass-design-deferred content: |
  - [x] ✅ **DEFERRED-POST-CUTOVER — stays in this archived plan; activates post-May-23. DO NOT move without operator
        ack.** [DESIGN] P2. **Phase E — Subclass design for declaration-level enforcement (DEFERRED post-cutover).** For
        fields where the declaration flip would add real type-safety value but can't be expressed without subclasses
        (primarily `expiry` for FUTURE/OPTION): The subclass approach (e.g. `FuturesInstrumentRecord(InstrumentRecord)`
        with `expiry: datetime` non-optional) requires: (a) instruments-service adapters return typed subclasses (not
        base InstrumentRecord) (b) consumers narrow the type at read boundaries (c) parquet read path infers the subtype
        from `instrument_type` column This is a significant refactor. Defer until after May-23 cutover. Named successor:
        this plan itself (`hard_schema_phase1_field_flip_migration_2026_05_19.md`). **DO NOT move this to a different
        post-cutover plan without operator ack.** status: todo

- id: phase-f-codex-update content: |
  - [x] ✅ [DOCS] P1. **Phase F — Codex update: per-field enforcement status table.** — unified-trading-pm (this
        commit). `/codex/06-coding-standards/validation-and-errors.md` new §7 "InstrumentRecord hard-required field
        enforcement" with full 7-rule table, DEFI_ONCHAIN_INSTRUMENT_TYPES, audit script pointers, SSOT cross-ref. (slot
        4 2026-05-19) Update `/codex/06-coding-standards/validation-and-errors.md` § "InstrumentRecord hard-required
        field enforcement" with the corrected scope table (same as Phase D but in the codex SSOT). Cross-reference this
        plan + `hard_schema_enforcement_2026_05_08.md`. status: todo

isProject: false estimate_class: refactor estimate_baseline_ai_days: 5 estimate_calibrated_ai_days: 2.0
estimate_calibration_note: | Design+audit phase completed 2026-05-19 slot 7 re-dispatch (work_split item 10). Remaining
work: Phase A (1 validator rule extension, ~1 AI-day), Phase B (1 audit script, ~0.5 AI-day), Phase C (1 audit script,
~0.3 AI-day), Phases D/F (docs, ~0.2 AI-day). Total ~2 cal AI-days. refactor class (0.4× multiplier) because majority of
work is extending existing Phase 1 model_validator + writing audit scripts with existing tooling pattern. priority: P2
priority: P0 estimate_class: infra estimate_baseline_ai_days: 3.0 estimate_calibrated_ai_days: 2.4

---

> **Successor to**: [`hard_schema_enforcement_2026_05_08.md`](hard_schema_enforcement_2026_05_08.md) Phase 1 (status:
> `helper-shipped` — foundation shipped, field flips pending).
>
> **Do NOT archive `hard_schema_enforcement_2026_05_08.md`** — it is locked and contains Phases 2-5 context. This plan
> is the granular action plan for Phase 1's outstanding work only.

# Hard Schema Phase 1 — Field-Flip Migration Plan

## Design + audit output (slot 7 re-dispatch 2026-05-19)

This plan documents the findings from the Phase 1 design+audit pass assigned to slot 7 (work_split_2026_05_19_ikenna.md
item 10). The audit was intentionally design-only with no field flips; this plan is the required output.

---

## Task 1: Field inventory — Optional→required candidates with model_validator cross-ref

### InstrumentRecord fields audited

| Field                         | Current declaration       | Model validator rule                                                  | Audit finding                                                                                            |
| ----------------------------- | ------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `base_asset`                  | `str = ""` (NOT nullable) | ✅ Rule 1: CeFi SPOT_PAIR/PERPETUAL → non-empty                       | **Already non-nullable.** Plan's "flip" = constraint hardening. Validator covers runtime.                |
| `quote_asset`                 | `str = ""` (NOT nullable) | ✅ Rule 1: same                                                       | **Already non-nullable.** Same as base_asset.                                                            |
| `pool_address`                | `str \| None = None`      | ✅ Rule 2: DeFi ONCHAIN → pool_address OR base_asset_contract_address | **Disjunctive — cannot flip individually.** Declaration stays Optional. Validator is SSOT.               |
| `base_asset_contract_address` | `str \| None = None`      | ✅ Rule 2: disjunctive                                                | **Same as pool_address.**                                                                                |
| `base_asset_decimals`         | `int \| None = None`      | ❌ **NOT YET ENFORCED**                                               | **Phase A gap.** Required for all DEFI_ONCHAIN types (price normalisation).                              |
| `quote_asset_decimals`        | `int \| None = None`      | ❌ **NOT YET ENFORCED**                                               | **Phase A gap.** Required for POOL type only (two-asset; single-asset types legitimately have no quote). |
| `expiry`                      | `datetime \| None = None` | ✅ Rules 3/4/5: FUTURE/OPTION/EVENT_CONTRACT → non-null               | **Legitimately None for non-futures.** Declaration stays Optional. Validator covers required types.      |
| `atoken_address`              | `str \| None = None`      | None                                                                  | A_TOKEN instruments should have this; currently no validator. Phase A can add if needed.                 |
| `debt_token_address`          | `str \| None = None`      | None                                                                  | DEBT_TOKEN instruments should have this; currently no validator. Phase A can add if needed.              |

### Sports per-fixture schemas audited (fixture_id nullability)

| Schema                    | File                    | `fixture_id` type | Finding                                                                                 |
| ------------------------- | ----------------------- | ----------------- | --------------------------------------------------------------------------------------- |
| `CanonicalFixtureStats`   | `fixture_stats.py:20`   | `str`             | ✅ Already non-optional                                                                 |
| `CanonicalEvent`          | `events.py:29`          | `str`             | ✅ Already non-optional                                                                 |
| `CanonicalLineup`         | `lineup.py:48`          | `str`             | ✅ Already non-optional                                                                 |
| `CanonicalPlayerStats`    | `player_stats.py:21`    | `str`             | ✅ Already non-optional                                                                 |
| `CanonicalInjury`         | `__init__.py:596`       | `str \| None`     | ✅ **Legitimately optional** — injuries can be pre-season/training (no fixture context) |
| `arbitrage.py` classes    | `arbitrage.py:46,67`    | `str`             | ✅ Already non-optional                                                                 |
| `betting.py` classes      | `betting.py:61,82`      | `str`             | ✅ Already non-optional                                                                 |
| `ProgressiveFixtureStats` | `progressive.py:22,109` | `str`             | ✅ Already non-optional                                                                 |
| `ProcessedOdds`           | `processed_odds.py:21`  | `str`             | ✅ Already non-optional                                                                 |

**Sports verdict**: `fixture_id` is already non-optional on all per-fixture entities. `CanonicalInjury.fixture_id` is
legitimately nullable (pre-season/training injuries have no fixture). **No flip needed.**

---

## Task 2: Consumer-sweep classification

### CeFi `base_asset` / `quote_asset`

| File                                                 | Line     | Pattern                                                         | Classification                                                 |
| ---------------------------------------------------- | -------- | --------------------------------------------------------------- | -------------------------------------------------------------- |
| `instruments-service/cefi/tardis.py`                 | 500, 532 | `inst.base_asset or ""`                                         | 🟡 DEFENSIVE — redundant after model_validator; harmless no-op |
| `instruments-service/cefi/ccxt_adapter.py`           | 203, 234 | `inst.base_asset != X` / `inst.base_asset == X and inst.expiry` | 🟢 SAFE — direct comparison works fine                         |
| `instruments-service/catalogue/catalogue_builder.py` | 70       | `record.raw_symbol or record.base_asset`                        | 🟡 DEFENSIVE — raw_symbol fallback; no impact                  |

**No 🔴 BREAKS for CeFi fields.**

### DeFi `pool_address` / `base_asset_contract_address`

Direct reads from `InstrumentRecord.pool_address` in service code are NOT in strategy-service (that code reads from a
`position.pool_address` which is a different schema). No InstrumentRecord pool_address consumers found in services that
would break on a declaration change.

| Asset                                          | Classification                                            |
| ---------------------------------------------- | --------------------------------------------------------- |
| `pool_address` declaration flip                | N/A — disjunctive rule prevents solo flip; stays Optional |
| `base_asset_contract_address` declaration flip | N/A — same                                                |

### TradFi `expiry`

| File                                                 | Line     | Pattern                                                       | Classification                                                                                |
| ---------------------------------------------------- | -------- | ------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `instruments-service/catalogue/catalogue_builder.py` | 86       | `record.expiry.date() if record.expiry is not None else None` | 🟡 DEFENSIVE — correct for non-futures; would break if expiry flipped to non-null universally |
| `instruments-service/catalogue/catalogue_builder.py` | 108      | `if record.expiry is not None:`                               | 🟡 DEFENSIVE — same                                                                           |
| `instruments-service/tradfi/futures_factory.py`      | 267      | `if not record.expiry: return early`                          | 🟡 DEFENSIVE — explicit None handling for "skip non-expiry instruments" logic                 |
| `instruments-service/tradfi/futures_factory.py`      | 287      | `record.expiry.date() if isinstance(record.expiry, datetime)` | 🟡 DEFENSIVE — correct                                                                        |
| `strategy-service/portfolio_allocator/archetypes.py` | 602, 716 | `bool(s.expiry)` / `not s.expiry`                             | 🟡 DEFENSIVE — "dated mode requires expiry" check; would become no-op for FUTURE instruments  |

**All consumers are 🟡 DEFENSIVE** — they handle None correctly for non-futures instrument types. A universal
`expiry: datetime` declaration flip would require updating these consumers to remove None checks (or they'd generate
basedpyright `reportUnnecessaryComparison` errors). The correct fix is the **subclass approach** (Phase E) not a global
declaration flip.

**No 🔴 BREAKS found.** All defensive consumers would degrade to no-ops after validator.

---

## Task 3: Sports `fixture_id` phantom verification

**Verdict**: No phantom. All per-fixture entities already have `fixture_id: str` (non-optional).
`CanonicalInjury.fixture_id: str | None` is justified (pre-season/training injury records not associated with a
fixture).

**Action**: NONE. Document in Phase D table. Remove "Sports fixture_id" from the "pending" list in
`hard_schema_enforcement_2026_05_08.md` Phase 1 roadmap section.

---

## Task 4: Back-fill migration scope per field

| Field(s)                                                 | Migration needed?                                                                                              | Tooling to use                                                                                      | When                                                               |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `base_asset` / `quote_asset` empty rows                  | **Audit only** (Phase C)                                                                                       | New `audit_cefi_empty_base_quote.py` using instruments GCS reader pattern                           | Before Phase A                                                     |
| `pool_address` / `base_asset_contract_address` null rows | **None** — model_validator already ensures new rows comply; historical null rows are from pre-Phase-1 adapters | N/A                                                                                                 | After catalogue Phase 2-3 completes the protocol address backfills |
| `base_asset_decimals` null rows (Phase A gap)            | **Audit + targeted re-fetch** (Phase B)                                                                        | New `audit_defi_null_decimals_2026_05_19.py` → re-fetch from catalogue adapter or on-chain registry | After Phase A validator ships                                      |
| `quote_asset_decimals` null rows for POOL type           | Same as base_asset_decimals                                                                                    | Same script, filter for POOL instrument_type                                                        | Same as above                                                      |
| `expiry` null rows for FUTURE/OPTION                     | **Existing script** `migrate_tradfi_expiry_schema.py` handles this                                             | Run `migrate_tradfi_expiry_schema.py --dry-run` to identify residual null-expiry futures rows       | Not blocking — model_validator catches new writes                  |
| Sports `fixture_id`                                      | **None** — already non-optional everywhere relevant                                                            | N/A                                                                                                 | N/A                                                                |

### Existing migration tooling inventory (instruments-service/scripts/)

- `migrate_tradfi_expiry_schema.py` — handles null expiry back-fill for TradFi futures; already run per tradfi_master Q1
- `audit_fixtures_via_api_football.py` — pattern for sports per-fixture audit
- `reconcile_phantom_manifest_rows.py` / `reconcile_phantom_manifest_rows_all.py` — manifest phantom identification
  pattern
- `canonicalize_defi_manifest_data_types_2026_05_16.py` — DeFi parquet migration pattern (SSOT for new DeFi scripts)
- `backfill_sports_fixture_stats_manifest.py` — sports entity backfill pattern

**Phase A + Phase B new scripts** follow the `canonicalize_defi_manifest_data_types_2026_05_16.py` pattern: GCS reader →
null-field filter → JSON audit report → optional targeted re-fetch.

---

## Phased DAG

```
Phase A: DeFi decimals model_validator rules (UAC)
    └── deps: DEFI_ONCHAIN_INSTRUMENT_TYPES constants (already defined); catalogue Phase 2-3 adapter writes
    └── output: 2 new validator rules + unit tests

Phase B: Null-decimals GCS audit script (instruments-service)
    └── deps: Phase A (model_validator ships so new rows comply before audit runs)
    └── output: JSON audit report of historical null decimals

Phase C: CeFi empty-string audit (instruments-service)
    └── deps: None (read-only verification)
    └── output: count of empty base_asset/quote_asset rows per venue

Phase D: Update hard_schema_enforcement plan body — corrected scope table
    └── deps: Phases A/B/C findings (to fill in audit results)
    └── output: plan body "Per-asset-group schema-flip roadmap" updated with current status

Phase F: Codex update — validation-and-errors.md
    └── deps: Phase D (same content)
    └── output: codex doc updated

Phase E: Subclass design (DEFERRED — post-cutover)
    └── deps: May-23 cutover shipped; instruments-service Type narrowing refactor scheduled
    └── named successor: this plan (not a new plan)
```

Phases A + C are parallelisable (no dependency between them). Phases D + F are parallelisable and follow A/B/C.

---

## Deferred work — migrated to:

| Deferred item                                                                                                | Successor                                                 |
| ------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| Phase E — subclass design for declaration-level expiry enforcement (FUTURE/OPTION/EVENT_CONTRACT subclasses) | This plan post-cutover (DO NOT move without operator ack) |

## Temporary states + their canonical follow-up plans

| Temporary state                                                                   | Follow-up plan                       | ETA                                            |
| --------------------------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------- |
| `base_asset_decimals` / `quote_asset_decimals` not enforced (model_validator gap) | Phase A of this plan                 | Next session after operator write-pause window |
| Subclass approach for declaration-level `expiry` enforcement                      | Phase E of this plan                 | Post-cutover (after May-23)                    |
| CeFi empty-string rows (if any found in Phase C)                                  | Issue doc + adapter fix per findings | Same session as Phase C                        |

</content>
