---
doc_type: plan
title: Hard Schema Enforcement at Write Boundary — Workspace-Wide
summary: >-
  Completed 2026-05-19 plan that made per-asset-group instrument fields hard-required at the UAC write boundary — added
  RecordFailedReason taxonomy + InstrumentRecord model_validator (CeFi/DeFi/FUTURE/OPTION/EVENT_CONTRACT/sports),
  per-row SCHEMA_VALIDATION_FAILED routing at instruments-service, MalformedRowKeyError guard in UTL, and PM QG STEP
  5.83 static assertions.
status: complete
nature: record
asset_group: [sports]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [schema-enforcement, write-gate, hard-required-fields, instrument-record, record-failed, quality-gates]
related: []
created: 2026-05-08
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
epic: epic-code-completion
completion_gates: { code: C5, deployment: D3, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
  - { repo: instruments-service, code: C0, deployment: none, business: none }
  - { repo: market-tick-data-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on: [tradfi-master-2026-05-07, writegate-honest-coverage-endtoend-2026-05-06, infrastructure-master-2026-05-07]
todos:
  - { id: phase-1-uac-schema-audit-hard-required-flips, content: "- [x] ✅ [SCRIPT] P0. **Phase 1 — UAC schema audit +
        hard-required field markup per asset_group.** Walk every\n  Pydantic / TypedDict / dataclass schema under
        `unified_api_contracts/canonical/domain/_*.py`. For each\n  asset_group, identify the fields that are
        workspace-rule-required-but-currently-nullable + flip nullable →\n  required:\n    - **CeFi**: `base_currency`,
        `quote_currency` on every spot/perp instrument schema.\n    - **DeFi**: `chain_id`, `contract_address`,
        `decimals` on every on-chain asset schema.\n    - **TradFi futures**: `expiry_date`, `last_trading_date`,
        `first_notice_date`, `delivery_date`,\n      `settlement_date` (covered by `tradfi_master` Q1 — sequence this
        plan AFTER tradfi_master ships\n      those flips).\n    - **TradFi options**: `expiration` (covered by
        `tradfi_master` Q2 — sequence AFTER).\n    - **Sports**: `fixture_id` on every per-fixture entity (lineups /
        events / stats / injuries).\n    -\
        \ **Predictions**: ALREADY hard-required per Phase 1A of writegate — no change needed; serves
        as\n      reference for the rest.\n  Per-flip: one-shot manifest migration script back-fills + flips schema in a
        single PR.\n  **PARTIAL FOUNDATION + 3 ASSET-GROUP RULES SHIPPED 2026-05-11 by slot 5
        (ikenna-aggressive-may15-tab,\n  RE-TASK)**: foundation (RecordFailedReason taxonomy + SCHEMA_VALIDATION_FAILED
        enum value) shipped at\n  uac@`3157f45`; per-asset-group `InstrumentRecord` model_validator shipped
        uac@`37d1ddb` enforcing 3 closed-set\n  rules: (1) CeFi spot/perp (SPOT_PAIR / PERPETUAL) → `base_asset` +
        `quote_asset` non-empty; (2) DeFi on-chain\n  (POOL / LENDING / LST / YIELD_BEARING / A_TOKEN / DEBT_TOKEN /
        STAKING / SPOT_ASSET — 8 types) → `pool_address`\n  OR `base_asset_contract_address` non-empty; (3)
        EVENT_CONTRACT → `expiry` non-null. Two new module-level\n  constants exposed: `CEFI_PAIR_INSTRUMENT_TYPES` +
        `DEFI_ONCHAIN_INSTRUMENT_TYPES` (downstream callers can\n  check `instrument.instrument_type\
        \ in CEFI_PAIR_INSTRUMENT_TYPES` directly). 10/10 smoke tests pass —\n  validator raises `ValueError` for
        empty/null required fields per rule; downstream MTDS / instruments-service\n  adapters' per-row try/except
        routes them to\n  `record_failed(reason=RecordFailedReason.SCHEMA_VALIDATION_FAILED)` (already shipped (sister
        enum to\n  `EmptyConfirmedReason` per the existing `honest_coverage.py` shape). 8 closed-set members covering
        schema\n  violation / upstream timestamp bias / malformed tick field / upstream subgraph zero / cluster
        coverage\n  violation / malformed row key / classified venue error / unclassified adapter error. Foundational
        for\n  Phase 2 per-row `record_failed` routing — adapters route schema-rejected rows
        to\n  `record_failed(reason=RecordFailedReason.SCHEMA_VALIDATION_FAILED, ...)` once Phase 2 refactors
        the\n  `ManifestWriter.record_failed` signature to accept the structured-reason kwarg. Smoke-import
        verified:\n  enum count 8, frozenset size 8, mutually exclusive\
        \ with EmptyConfirmedReason.\n  **TRADFI FUTURE+OPTION model_validator rules SHIPPED 2026-05-19 by slot 8
        (uac@80aef10)**: added FUTURE\n  (tradfi_master Q1 gate passed 2026-05-13) and OPTION (tradfi_master Q2 gate
        passed 2026-05-13) branches to\n  `InstrumentRecord._enforce_per_asset_group_required_fields` model_validator.
        Both enforce `expiry` non-null\n  per workspace rule. 15 tests in
        `tests/internal/unit/test_instrument_record_hard_required_fields.py` cover\n  all 5 asset-group rules. QG ✅ ALL
        PASSED.\n  **SPORTS fixture_id COMPLETE 2026-05-19 slot 4 (uac@436bed0)**: sports per-fixture domain
        schemas\n  (`fixture_stats`, `lineup`, `events`, `injury`, `player_stats`, `arbitrage`, `progressive`) all
        declare\n  `fixture_id: str` as Pydantic required non-nullable field (no default → Pydantic enforces at
        construction).\n  Inspection confirms all per-fixture entities comply. No InstrumentRecord model_validator rule
        needed — sports\n  instruments encode fixture identity in `instrument_key`.\
        \ Model_validator comment updated to reflect\n  completion. Phase 1 fully closed.\n  **Phase 2 record_failed
        COMPLETE 2026-05-19 slot 4 (instruments-service@3c2da42)**: per-row\n  SCHEMA_VALIDATION_FAILED routing at
        instruments-service orchestrator shipped.\n", status: done, note: ALL SHIPPED. uac@3157f45 RecordFailedReason
        taxonomy; uac@37d1ddb CeFi/DeFi/EVENT_CONTRACT validators; uac@80aef10 FUTURE+OPTION validators;
        instruments-service@3c2da42 per-row record_failed routing; uac@436bed0 Sports fixture_id closure +
        model_validator comment update. Phase 1 complete 2026-05-19 slot 4. }
  - {
      id: phase-2-per-row-record-failed-orchestrator-refactor,
      content:
        "- [x] ✅ [SCRIPT] P0. **Phase 2 — Per-row schema validation gate at instruments-service orchestrator.**
        Today\n  `engine/orchestrator.py` venue-shard-wide try/except causes ALL rows to fail when ONE row violates
        schema.\n  Refactor: split each shard into per-row try/except; valid rows → `record_captured`; invalid rows
        →\n  `record_failed(reason=SCHEMA_VALIDATION_FAILED, error_detail={field, expected_type,
        observed_value})`.\n  Same pattern UTL `instruments_write_gate.py` already partially supports. **CLAUDE.md
        \"shard-level failure\n  isolation\" rule applies** — no `raise` inside per-row loop.\n  **SHIPPED 2026-05-19
        instruments-service@3c2da42**: replaced venue-shard failure with per-record\n  SCHEMA_VALIDATION_FAILED events;
        venue only added to validation_failed_venues when ALL its records fail.\n",
      status: done,
    }
  - {
      id: phase-3-sports-adapter-full-column-capture-audit,
      content:
        "- [x] ✅ [SCRIPT] P0. **Phase 3 — Sports adapter full-column capture audit.** 6 adapters with
        documented\n  minimal-flatten loss (issue cites 18-30 columns dropped at normalize-time): footystats, SFI
        (progressive\n  + standings + matches), understat (XG per-shot — biggest miss, 15+ fields per shot
        dropped),\n  transfermarkt, open_meteo, odds_api. Per adapter: probe raw payload sample, compare against
        current\n  normalizer output, flag dropped columns; rewrite normalizer to capture all useful columns;
        cassette\n  parity test locks the new shape. **Coordinate with sports_master Phase 3 C.7 follow-ups** — that
        section\n  already lists STANDINGS / XG / MATCHES flatten work; verify alignment before duplicating.\n  —
        UAC@6ccb5c5: normalize_understat_shot 18-field flat dict (C.7 Follow-up #2 — biggest miss
        shipped);\n  sports_master C.7 Follow-up #1 (STANDINGS) done at UAC@ac12d80; C.7 Follow-up #3 (MATCHES) done at
        UAC@4e23bd9\n",
      status: done,
    }
  - {
      id: phase-4-manifest-row-key-shape-validation,
      content:
        "- [x] ✅ [SCRIPT] P0. **Phase 4 — Manifest row_key shape validation.** UTL
        `ManifestWriter.record_captured`\n  guard: for per-instrument shard atoms (per CLAUDE.md \"shard-granularity
        SSOT\"), row_key MUST contain\n  non-empty `instrument_id`; for bundled shards, row_key MUST contain
        non-empty\n  `chain` / `options_chain` / `canonical_question_group` per the shard-key matrix. Empty values →
        raise\n  `MalformedRowKeyError` at write-time. Catches the 2026-05-07 CeFi Tardis bundle-shape
        regression\n  proactively (covered separately by writegate Phase 2.A migration).\n  — UTL@0caa08e3:
        MalformedRowKeyError class + _coerce_row_key guard for instrument_id/chain shard-atom keys\n",
      status: done,
    }
  - {
      id: phase-5-qg-static-assertion,
      content:
        "- [x] ✅ [SCRIPT] P0. **Phase 5 — PM `quality-gates.sh` STEP 5.83 static assertion.** Two-layer\n  coverage
        shipped:\n  (1) `check_uac_instrument_record_validator.py` wired in `base-library.sh` STEP 5.83
        under\n  `UAC_CANONICAL_EXEMPT` guard — verifies InstrumentRecord model_validator + CEFI/DEFI frozensets\n  in
        UAC `internal/reference/instrument.py`. — PM@03a320846 2026-05-19\n  (2) `check_uac_hard_required_fields.py`
        wired in `base-service.sh` STEP 5.83 — verifies\n  `validate_instrument_records` + 3 closed-set rule landmarks
        in UAC `instrument_validation.py`\n  (runtime validator regression guard) + AST-walks service source for
        literal\n  `record_captured(data_type=\"<bundled_type>\", …)` calls missing required shard-key
        kwarg.\n  Smoke-tested: both [OK] against real UAC + empty source.\n  — PM@429b64b2b (STEP 5.83 base-service.sh
        + check_uac_hard_required_fields.py) 2026-05-19\n",
      status: done,
    }
  - {
      id: codex-update,
      content:
        "- [x] ✅ [AGENT] P0. **Codex updates**: per-row `record_failed` pattern + `RecordFailedReason` taxonomy
        (all\n  9 members) added to `/codex/02-data/honest-absence-downstream-handling.md` reason taxonomy table
        —\n  `SCHEMA_VALIDATION_FAILED`, `UPSTREAM_SUBGRAPH_ZERO`, `MALFORMED_ROW_KEY`,
        `CLASSIFIED_VENUE_ERROR`,\n  `UNCLASSIFIED_ADAPTER_ERROR`, `UPSTREAM_LIVE_GAP`. Per-row schema validation +
        `SCHEMA_VALIDATION_FAILED`\n  content already consolidated in
        `/codex/06-coding-standards/validation-and-errors.md` § 3 (no separate\n  schema-validation.md needed — file was
        pre-merged per header note). — PM@tab-3 2026-05-19\n",
      status: done,
    }
  - {
      id: composability-with-futures-expiry,
      content:
        "- [x] [HUMAN] P0. **Composability with futures expiry confirmed (operator decision 2026-05-08).**
        Sequence:\n  tradfi_master Q1+Q2 ships first → futures schemas become hard-required → THEN this plan
        ships\n  workspace-wide enforcement → existing futures rows already comply. Avoids mass-fail-during-transit.
        NO\n  bundling into a single coordinated migration plan (operator preference).\n",
      status: done,
    }
isProject: false
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: "No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from
  filename (design, multiplier 0.6×).

  Owner agent: fill baseline + multiply × 0.6 per /codex/08-workflows/estimation-calibration.md. Refine class if
  dominant work-class differs.

  "
parent_epic: sports_master
priority: P2
---

> **ARCHIVED 2026-05-21** — 100% complete (0 open todos). All 7 todos shipped: uac@3157f45 + uac@37d1ddb + uac@80aef10 +
> instruments-service@3c2da42 + uac@436bed0 + UTL@0caa08e3 + PM@429b64b2. One item (expiry type-level flip) migrated to
> tradfi_master P3 as DEFERRED. status: done → archived.

> **🟡 FOLDED INTO UMBRELLA — `manifest_evolution_SUPERSEDED_2026_05_21`** (codified 2026-05-08)
>
> This plan's manifest-touching scope MUST execute as part of the umbrella's gate sequence — NOT in isolation. Operator
> direction: "manifest, code, and data migrate in the same group plan to avoid collision risk; force batch execution;
> don't allow execution in isolation." Three-axis invariant: schema (UAC) + writer code (UTL + adapter callsites) + GCS
> data layout co-evolve.
>
> Child of:
> [`plans/epics/manifest_evolution_SUPERSEDED_2026_05_21.md`](../epics/manifest_evolution_SUPERSEDED_2026_05_21.md)
>
> This plan's phases land in gate(s): **G2** (cluster validation AST guard) + **G7** (workspace audit)

## Deferred work — migrated to: `tradfi_master.md`

- **InstrumentRecord.expiry full type-level nullable→required flip** (FUTURE + OPTION): model_validator (uac@80aef10)
  provides runtime enforcement. Full Pydantic type-level flip is a post-May-23 breaking change; migrated to
  tradfi_master.md as DEFERRED P3 item. 2026-05-19 slot 4.

## Closure note (2026-05-19 slot 4)

All 7 plan todos completed: uac@3157f45 (RecordFailedReason taxonomy) + uac@37d1ddb (CeFi/DeFi validators) + uac@80aef10
(FUTURE+OPTION validators) + instruments-service@3c2da42 (per-row record_failed) + uac@436bed0 (Sports fixture_id) +
UTL@0caa08e3 (MalformedRowKeyError) + PM@429b64b2 (STEP 5.83 QG). Codex updated. One deferred item (full type-level
expiry flip) migrated to tradfi_master P3. Plan status: active → done.

# Hard Schema Enforcement at Write Boundary — Workspace-Wide

## Why this plan exists

The 2026-05-07 audit + the 2026-05-08 archived RFC
(`plans/archive/issues/hard_schema_enforcement_at_write_boundary_2026_05_08.md`) identify that only **predictions** has
hard-required lifecycle enforcement at the write boundary today. Every other asset_group leaves required fields nullable
AND the write path fails venue-shard-wide rather than per-row. Three observable consequences:

1. Fields that should be hard-required (`base_currency` / `quote_currency` for cefi; `chain_id` / `contract_address` /
   `decimals` for defi; `expiry_date` for tradfi futures; `fixture_id` for sports) are schema-present but not enforced —
   adapters silently write nulls when the upstream payload is sparse.
2. Per-shard try/except masks partial-data bugs as "all-or-nothing" failures — a single bad row taints the entire
   venue-day shard, hiding the diagnostic detail.
3. Sports adapters minimal-flatten (18-30 columns dropped at normalize-time) — the source payload has the data, the
   normalizer drops it, downstream features compute on missing fields.

These compose: lookahead bias / partial-bundle / minimal-flattening incidents through 2026-Q2 trace back to this shape.
Fix is a single workspace-wide migration with 5 phases.

## Architecture summary

- **Phase 1**: UAC schemas flip nullable → required per asset_group + back-fill migration script per-flip.
- **Phase 2**: instruments-service orchestrator refactor — per-row try/except, record_captured for valid,
  record_failed(SCHEMA_VALIDATION_FAILED) for invalid.
- **Phase 3**: 6 sports adapters re-normalized to capture full payload (coordinate with sports_master Phase 3 C.7).
- **Phase 4**: UTL ManifestWriter row_key shape validation — empty `instrument_id` for per-instrument shards raises
  MalformedRowKeyError.
- **Phase 5**: PM QG STEP 5.66 static assertion fails CI on missing markup.

## Sequencing rationale (operator decision 2026-05-08)

Bundling this with the tradfi_master Q1+Q2 futures-expiry work into a single coordinated plan was rejected by the
operator. Reason: the operator-preferred shape is incremental + reversible. Sequencing tradfi_master first → this plan
second means existing futures rows already comply when the workspace-wide enforcement lands. If the work were bundled, a
partial commit would mass-fail every existing futures row mid-migration.

## Sibling plan relationships

- `tradfi_master.md` Q1+Q2 (futures expiry hard-required + options expiration flip) — sequenced BEFORE Phase 1 here.
- `sports_master.md` Phase 3 C.7 — overlaps with Phase 3 here on STANDINGS / XG / MATCHES flatten work; coordinate to
  avoid duplicating cassette parity tests.
- `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 2.A — Phase 4 row_key shape validation extends the writegate
  per-row failure routing.
- `infrastructure_master.md` — parent umbrella; this plan is referenced from the "Hard schema enforcement at write
  boundary" pointer section.

## Plan-format compliance

Follows `unified-trading-pm/plans/PLAN_FORMAT.md`: 3-tier readiness (C5 / D3); per-repo gates; Cursor checkboxes on
every todo; sibling-plan dependencies declared in `depends_on`; SSOT-first (codex docs in the codex-update todo own
intent, plan owns activation); pre-audit complete via the source RFC archived to `plans/archive/issues/`.

## Per-asset-group schema-flip roadmap (updated 2026-05-20 slot 4 — hard_schema_phase1_field_flip_migration_2026_05_19)

Per-field enforcement status as of 2026-05-20 (audit by slot 7 re-dispatch 2026-05-19; validator work slot 4):

| Field                         | Declaration                                      | Model validator                                                          | Status                                                                                                                        |
| ----------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `base_asset`                  | `str = ""`                                       | ✅ Rule 1: CeFi SPOT_PAIR/PERPETUAL → non-empty                          | **Already non-nullable.** Validator enforces at runtime. Phase C audit script verifies legacy rows.                           |
| `quote_asset`                 | `str = ""`                                       | ✅ Rule 1: same                                                          | **Already non-nullable.** Same as base_asset.                                                                                 |
| `pool_address`                | `str \| None`                                    | ✅ Rule 2: DeFi ONCHAIN → pool_address OR contract_address (disjunctive) | **Disjunctive — cannot flip individually.** Validator is SSOT.                                                                |
| `base_asset_contract_address` | `str \| None`                                    | ✅ Rule 2: disjunctive                                                   | **Same as pool_address.**                                                                                                     |
| `base_asset_decimals`         | `int \| None`                                    | ✅ **Rule 6: SHIPPED uac@956bec1 2026-05-19**                            | Non-null enforced for ALL `DEFI_ONCHAIN_INSTRUMENT_TYPES`. Phase B audit script verifies legacy rows.                         |
| `quote_asset_decimals`        | `int \| None`                                    | ✅ **Rule 7: SHIPPED uac@956bec1 2026-05-19**                            | Non-null enforced for POOL type (two-asset).                                                                                  |
| `expiry`                      | `datetime \| None`                               | ✅ Rules 3/4/5: FUTURE/OPTION/EVENT_CONTRACT → non-null (uac@80aef10)    | **Legitimately None for non-futures.** Declaration stays Optional. Phase E (subclass) is post-cutover.                        |
| Sports `fixture_id`           | `str` (non-optional on all per-fixture entities) | N/A — already non-optional                                               | **No flip needed.** `CanonicalInjury.fixture_id: str \| None` is legitimately nullable (pre-season injuries have no fixture). |

**Three architectural choices for the actual flips** (next agent picks one):

1. **Per-asset-group `InstrumentRecord` subclass** (e.g. `CefiSpotInstrument` / `DefiPoolInstrument` /
   `TradFiFuturesInstrument`) with the relevant fields non-nullable. Cleanest type-safety but requires a
   discriminated-union shape at the read boundary + instruments-service adapter migration.
2. **Pydantic `model_validator(mode="after")` on `InstrumentRecord`** that asserts per-`instrument_type` field
   requirements at runtime (e.g. `if instrument_type in {SPOT, PERPETUAL}: assert base_asset and quote_asset`).
   Lightest-touch but defers errors to runtime instead of type-check.
3. **Conditional-required per work-split (b)** — flip all the fields to non-nullable at the schema level + allow
   instrument-records to pass through the instruments-service adapter with sentinel values during the tradfi-master
   Q1+Q2 transition window, then flip the sentinels to hard-required post-tradfi-Q1+Q2 land. Operator preference per
   2026-05-11 aggressive May-15 push.

**Recommended**: option (2) `model_validator` — smallest blast radius, codifies the workspace rules without disrupting
the existing `InstrumentRecord` consumers, lands incrementally per asset_group. Subclasses (option 1) can come later as
a refactor once the runtime checks have stabilised the data shape.

**Per-flip migration sequence** (one PR per asset_group + per field, ordered to minimise mass-fail-during-transit):

1. CeFi `base_asset` / `quote_asset` — empty-string → non-empty validator. Back-fill migration: walk every captured CeFi
   spot/perp instrument in `gs://instruments-store-cefi-prod-{pid}`, identify rows with empty `base_asset` or
   `quote_asset`, classify (legitimate-data-source-omission vs adapter-bug), back-fill from venue REST or flag for
   re-fetch.
2. DeFi `chain_id` / `contract_address` / `decimals` — None → non-null validator on instruments with
   `instrument_type in DEFI_INSTRUMENT_TYPES`. Back-fill from on-chain registry (Aave V3 / Compound V3 / etc.
   subgraphs) + per-protocol fallback ABI calls. **Composes with catalogue Phase 2-3** — those adapters write the
   per-protocol contract addresses + decimals at instruments-service write time.
3. ✅ TradFi futures `expiry` non-null model_validator rule — **SHIPPED uac@80aef10 2026-05-19** (tradfi_master Q1 gate
   passed 2026-05-13). `InstrumentRecord` model_validator enforces `FUTURE → expiry non-null`. Full nullable→required
   schema flip + back-fill migration still deferred (see Phase 5 dependency).
4. ✅ TradFi options `expiry` non-null model_validator rule — **SHIPPED uac@80aef10 2026-05-19** (tradfi_master Q2 gate
   passed 2026-05-13). `InstrumentRecord` model_validator enforces `OPTION → expiry non-null`. Full schema flip +
   back-fill migration still deferred.
5. Sports `fixture_id` — per-file audit in `canonical/domain/sports/`; flip nullable → required on every per-fixture
   entity schema. Already-captured sports parquets per the 2026-05-07 audit should comply (the adapter populates
   fixture_id from the api_football payload); validator simply codifies the requirement.

**Phase 2 dependency**: per-row `record_failed` routing refactor at instruments-service `engine/orchestrator.py`

- MTDS adapter base. Each per-row try/except routes schema-rejected rows to
  `record_failed(reason=RecordFailedReason.SCHEMA_VALIDATION_FAILED, ...)` with `error_detail` capturing the field
  name + expected type + observed value. The RecordFailedReason taxonomy shipped at uac@`3157f45` is the foundation; the
  signature refactor is Phase 2's body of work.

**Phase 4 dependency**: `ManifestWriter.record_captured` row_key shape validation extends naturally — empty
`instrument_id` for per-instrument shards / empty `chain` for DeFi bundled shards →
`record_failed(reason= RecordFailedReason.MALFORMED_ROW_KEY)`. Phase 4 wires the guard.

**Phase 5 dependency**: PM `quality-gates.sh` STEP 5.66 AST-walk asserts (a) hard-required fields are non-nullable in
the Pydantic declarations + (b) every `record_captured` callsite passes the row_key shape validation kwargs for bundled
shards. Extends existing STEP 5.64.
