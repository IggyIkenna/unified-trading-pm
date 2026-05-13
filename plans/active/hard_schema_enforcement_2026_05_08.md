---
plan_type: code+infra
asset_group: cross-cutting
owner: ikenna
created: 2026-05-08
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
name: hard-schema-enforcement-2026-05-08
overview: >-
  Workspace-wide hard schema enforcement at the write boundary. Source RFC: archived issue
  `plans/archive/issues/hard_schema_enforcement_at_write_boundary_2026_05_08.md`. Today only predictions has
  hard-required lifecycle enforcement; every other asset_group leaves required fields nullable (base_currency /
  quote_currency / chain_id / contract_address / decimals / fixture_id) and the write path fails venue-shard-wide rather
  than per-row, masking partial-data bugs as "all-or-nothing" failures. Sports adapters minimal-flatten (18-30 columns
  dropped at normalize-time). Root-cause for lookahead bias / partial-bundle / minimal- flattening incidents
  compounding. Fix is workspace-wide UAC schema audit + per-row record_failed gate refactor + sports adapter full-column
  capture + manifest row_key shape validation + QG static assertion. Operator decision 2026-05-08: SEQUENCE this plan
  AFTER the futures-expiry work in `tradfi_master_2026_05_07` Q1+Q2 ships, to avoid mass-fail-during-transit on existing
  futures rows. Sub-plan-of `infrastructure_master_2026_05_07`.

type: mixed
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: D3
  business: none

repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on:
  - tradfi-master-2026-05-07
  - writegate-honest-coverage-endtoend-2026-05-06
  - infrastructure-master-2026-05-07

todos:
  - id: phase-1-uac-schema-audit-hard-required-flips
    content: |
      - [ ] [SCRIPT] P0. **Phase 1 — UAC schema audit + hard-required field markup per asset_group.** Walk every
        Pydantic / TypedDict / dataclass schema under `unified_api_contracts/canonical/domain/_*.py`. For each
        asset_group, identify the fields that are workspace-rule-required-but-currently-nullable + flip nullable →
        required:
          - **CeFi**: `base_currency`, `quote_currency` on every spot/perp instrument schema.
          - **DeFi**: `chain_id`, `contract_address`, `decimals` on every on-chain asset schema.
          - **TradFi futures**: `expiry_date`, `last_trading_date`, `first_notice_date`, `delivery_date`,
            `settlement_date` (covered by `tradfi_master` Q1 — sequence this plan AFTER tradfi_master ships
            those flips).
          - **TradFi options**: `expiration` (covered by `tradfi_master` Q2 — sequence AFTER).
          - **Sports**: `fixture_id` on every per-fixture entity (lineups / events / stats / injuries).
          - **Predictions**: ALREADY hard-required per Phase 1A of writegate — no change needed; serves as
            reference for the rest.
        Per-flip: one-shot manifest migration script back-fills + flips schema in a single PR.
        **PARTIAL FOUNDATION + 3 ASSET-GROUP RULES SHIPPED 2026-05-11 by slot 5 (ikenna-aggressive-may15-tab,
        RE-TASK)**: foundation (RecordFailedReason taxonomy + SCHEMA_VALIDATION_FAILED enum value) shipped at
        uac@`3157f45`; per-asset-group `InstrumentRecord` model_validator shipped uac@`37d1ddb` enforcing 3 closed-set
        rules: (1) CeFi spot/perp (SPOT_PAIR / PERPETUAL) → `base_asset` + `quote_asset` non-empty; (2) DeFi on-chain
        (POOL / LENDING / LST / YIELD_BEARING / A_TOKEN / DEBT_TOKEN / STAKING / SPOT_ASSET — 8 types) → `pool_address`
        OR `base_asset_contract_address` non-empty; (3) EVENT_CONTRACT → `expiry` non-null. Two new module-level
        constants exposed: `CEFI_PAIR_INSTRUMENT_TYPES` + `DEFI_ONCHAIN_INSTRUMENT_TYPES` (downstream callers can
        check `instrument.instrument_type in CEFI_PAIR_INSTRUMENT_TYPES` directly). 10/10 smoke tests pass —
        validator raises `ValueError` for empty/null required fields per rule; downstream MTDS / instruments-service
        adapters' per-row try/except routes them to
        `record_failed(reason=RecordFailedReason.SCHEMA_VALIDATION_FAILED)` (already shipped (sister enum to
        `EmptyConfirmedReason` per the existing `honest_coverage.py` shape). 8 closed-set members covering schema
        violation / upstream timestamp bias / malformed tick field / upstream subgraph zero / cluster coverage
        violation / malformed row key / classified venue error / unclassified adapter error. Foundational for
        Phase 2 per-row `record_failed` routing — adapters route schema-rejected rows to
        `record_failed(reason=RecordFailedReason.SCHEMA_VALIDATION_FAILED, ...)` once Phase 2 refactors the
        `ManifestWriter.record_failed` signature to accept the structured-reason kwarg. Smoke-import verified:
        enum count 8, frozenset size 8, mutually exclusive with EmptyConfirmedReason. **STILL OPEN per Phase 1**:
        per-asset-group nullable→required field flips (see roadmap below); current plan body lists the field
        inventory but actual flips need (a) per-asset-group instrument-record subclass shape OR conditional
        Pydantic model_validator (decision sub-todo), (b) one-shot back-fill migration script per flip, (c)
        consumer-sweep across instruments-service + MTDS + downstream services. Roadmap added in the plan body
        below — actionable by the next agent.
    status: helper-shipped
    note: "uac@3157f45 RecordFailedReason taxonomy shipped 2026-05-11; Phase 2 record_failed signature refactor + per-asset-group field flips still pending."

  - id: phase-2-per-row-record-failed-orchestrator-refactor
    content: |
      - [ ] [SCRIPT] P0. **Phase 2 — Per-row schema validation gate at instruments-service orchestrator.** Today
        `engine/orchestrator.py` venue-shard-wide try/except causes ALL rows to fail when ONE row violates schema.
        Refactor: split each shard into per-row try/except; valid rows → `record_captured`; invalid rows →
        `record_failed(reason=SCHEMA_VALIDATION_FAILED, error_detail={field, expected_type, observed_value})`.
        Same pattern UTL `instruments_write_gate.py` already partially supports. **CLAUDE.md "shard-level failure
        isolation" rule applies** — no `raise` inside per-row loop.
    status: todo

  - id: phase-3-sports-adapter-full-column-capture-audit
    content: |
      - [ ] [SCRIPT] P0. **Phase 3 — Sports adapter full-column capture audit.** 6 adapters with documented
        minimal-flatten loss (issue cites 18-30 columns dropped at normalize-time): footystats, SFI (progressive
        + standings + matches), understat (XG per-shot — biggest miss, 15+ fields per shot dropped),
        transfermarkt, open_meteo, odds_api. Per adapter: probe raw payload sample, compare against current
        normalizer output, flag dropped columns; rewrite normalizer to capture all useful columns; cassette
        parity test locks the new shape. **Coordinate with sports_master Phase 3 C.7 follow-ups** — that section
        already lists STANDINGS / XG / MATCHES flatten work; verify alignment before duplicating.
    status: todo

  - id: phase-4-manifest-row-key-shape-validation
    content: |
      - [ ] [SCRIPT] P0. **Phase 4 — Manifest row_key shape validation.** UTL `ManifestWriter.record_captured`
        guard: for per-instrument shard atoms (per CLAUDE.md "shard-granularity SSOT"), row_key MUST contain
        non-empty `instrument_id`; for bundled shards, row_key MUST contain non-empty
        `chain` / `options_chain` / `canonical_question_group` per the shard-key matrix. Empty values → raise
        `MalformedRowKeyError` at write-time. Catches the 2026-05-07 CeFi Tardis bundle-shape regression
        proactively (covered separately by writegate Phase 2.A migration).
    status: todo

  - id: phase-5-qg-static-assertion
    content: |
      - [ ] [SCRIPT] P0. **Phase 5 — PM `quality-gates.sh` STEP 5.66 static assertion.** AST-walk every UAC
        canonical schema; assert: (a) hard-required fields per Phase 1 list above are non-nullable in the
        Pydantic / TypedDict / dataclass declaration; (b) every `record_captured` callsite passes the row_key
        shape validation kwargs for bundled shards (extends existing STEP 5.64). Fails CI on missing markup or
        skipped guards.
    status: todo

  - id: codex-update
    content: |
      - [ ] [AGENT] P0. **Codex updates**: NEW
        `codex/06-coding-standards/schema-validation.md` capturing the per-row record_failed pattern + the
        SCHEMA_VALIDATION_FAILED reason taxonomy + the per-asset-group hard-required field list. Extend
        `codex/06-coding-standards/error-handling.md` with the per-row record_failed pattern reference. Update
        `codex/02-data/honest-absence-downstream-handling.md` with the SCHEMA_VALIDATION_FAILED reason added to
        the closed-set RecordFailedReason enum.
    status: todo

  - id: composability-with-futures-expiry
    content: |
      - [x] [HUMAN] P0. **Composability with futures expiry confirmed (operator decision 2026-05-08).** Sequence:
        tradfi_master Q1+Q2 ships first → futures schemas become hard-required → THEN this plan ships
        workspace-wide enforcement → existing futures rows already comply. Avoids mass-fail-during-transit. NO
        bundling into a single coordinated migration plan (operator preference).
    status: done

isProject: false
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: |
  No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from filename (design, multiplier 0.6×).
  Owner agent: fill baseline + multiply × 0.6 per codex/08-workflows/estimation-calibration.md. Refine class if dominant work-class differs.
---

> **🟡 FOLDED INTO UMBRELLA — `manifest_evolution_master_2026_05_08`** (codified 2026-05-08)
>
> This plan's manifest-touching scope MUST execute as part of the umbrella's gate sequence — NOT in isolation. Operator
> direction: "manifest, code, and data migrate in the same group plan to avoid collision risk; force batch execution;
> don't allow execution in isolation." Three-axis invariant: schema (UAC) + writer code (UTL + adapter callsites) + GCS
> data layout co-evolve.
>
> Child of: [`plans/epics/manifest_evolution_master_2026_05_08.md`](../epics/manifest_evolution_master_2026_05_08.md)
>
> This plan's phases land in gate(s): **G2** (cluster validation AST guard) + **G7** (workspace audit)

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

- `tradfi_master_2026_05_07.md` Q1+Q2 (futures expiry hard-required + options expiration flip) — sequenced BEFORE Phase
  1 here.
- `sports_master_2026_05_07.md` Phase 3 C.7 — overlaps with Phase 3 here on STANDINGS / XG / MATCHES flatten work;
  coordinate to avoid duplicating cassette parity tests.
- `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 2.A — Phase 4 row_key shape validation extends the writegate
  per-row failure routing.
- `infrastructure_master_2026_05_07.md` — parent umbrella; this plan is referenced from the "Hard schema enforcement at
  write boundary" pointer section.

## Plan-format compliance

Follows `unified-trading-pm/plans/PLAN_FORMAT.md`: 3-tier readiness (C5 / D3); per-repo gates; Cursor checkboxes on
every todo; sibling-plan dependencies declared in `depends_on`; SSOT-first (codex docs in the codex-update todo own
intent, plan owns activation); pre-audit complete via the source RFC archived to `plans/archive/issues/`.


## Per-asset-group schema-flip roadmap (added 2026-05-11 slot 5, RE-TASK)

Phase 1's "nullable → required" flips require a workspace-wide audit of `InstrumentRecord`
(`unified-api-contracts/unified_api_contracts/internal/reference/instrument.py`) + per-domain schemas under
`canonical/domain/`. Current state observation (slot 5 grep 2026-05-11):

- `InstrumentRecord.base_asset` / `quote_asset` (line 84-85) — `str = ""` (defaults to empty; workspace rule says
  CeFi spot/perp must have non-empty). **NOT nullable but unenforced** — empty-string sentinel passes the type
  check but violates the workspace contract.
- `InstrumentRecord.base_asset_contract_address` / `quote_asset_contract_address` / `base_asset_decimals` /
  `quote_asset_decimals` (line 158-170) — `str | None = None` / `int | None = None`. DeFi rule says these must
  be non-null for on-chain instruments. **NULLABLE; needs flip for DeFi.**
- `InstrumentRecord.expiry` (line 108) — `datetime | None = None`. TradFi futures rule says must be non-null
  for futures. **NULLABLE; needs flip for TradFi futures + options** (blocked on `tradfi_master` Q1+Q2).
- Sports `fixture_id` — present on `canonical/domain/sports/{fixture_stats,player_stats,events,arbitrage}.py`
  per grep; need per-file audit for nullability.

**Three architectural choices for the actual flips** (next agent picks one):

1. **Per-asset-group `InstrumentRecord` subclass** (e.g. `CefiSpotInstrument` / `DefiPoolInstrument` /
   `TradFiFuturesInstrument`) with the relevant fields non-nullable. Cleanest type-safety but requires a
   discriminated-union shape at the read boundary + URDI adapter migration.
2. **Pydantic `model_validator(mode="after")` on `InstrumentRecord`** that asserts per-`instrument_type` field
   requirements at runtime (e.g. `if instrument_type in {SPOT, PERPETUAL}: assert base_asset and quote_asset`).
   Lightest-touch but defers errors to runtime instead of type-check.
3. **Conditional-required per work-split (b)** — flip all the fields to non-nullable at the schema level + allow
   instrument-records to pass through the URDI adapter with sentinel values during the tradfi-master Q1+Q2
   transition window, then flip the sentinels to hard-required post-tradfi-Q1+Q2 land. Operator preference per
   2026-05-11 aggressive May-15 push.

**Recommended**: option (2) `model_validator` — smallest blast radius, codifies the workspace rules without
disrupting the existing `InstrumentRecord` consumers, lands incrementally per asset_group. Subclasses (option 1)
can come later as a refactor once the runtime checks have stabilised the data shape.

**Per-flip migration sequence** (one PR per asset_group + per field, ordered to minimise mass-fail-during-transit):

1. CeFi `base_asset` / `quote_asset` — empty-string → non-empty validator. Back-fill migration: walk every
   captured CeFi spot/perp instrument in `gs://instruments-store-cefi-prod-{pid}`, identify rows with empty
   `base_asset` or `quote_asset`, classify (legitimate-data-source-omission vs adapter-bug), back-fill from
   venue REST or flag for re-fetch.
2. DeFi `chain_id` / `contract_address` / `decimals` — None → non-null validator on instruments with
   `instrument_type in DEFI_INSTRUMENT_TYPES`. Back-fill from on-chain registry (Aave V3 / Compound V3 / etc.
   subgraphs) + per-protocol fallback ABI calls. **Composes with catalogue Phase 2-3** — those adapters write
   the per-protocol contract addresses + decimals at instruments-service write time.
3. TradFi futures `expiry_date` + 4 sister dates — blocked on `tradfi_master_2026_05_07` Q1 (futures-expiry
   fields shipping). Sequence: tradfi_master Q1 lands → this plan Phase 1.3 lands → existing futures rows
   already comply.
4. TradFi options `expiration` — blocked on `tradfi_master_2026_05_07` Q2 (options-expiration flip). Same
   sequencing as #3.
5. Sports `fixture_id` — per-file audit in `canonical/domain/sports/`; flip nullable → required on every
   per-fixture entity schema. Already-captured sports parquets per the 2026-05-07 audit should comply (the
   adapter populates fixture_id from the api_football payload); validator simply codifies the requirement.

**Phase 2 dependency**: per-row `record_failed` routing refactor at instruments-service `engine/orchestrator.py`
+ MTDS adapter base. Each per-row try/except routes schema-rejected rows to
`record_failed(reason=RecordFailedReason.SCHEMA_VALIDATION_FAILED, ...)` with `error_detail` capturing the
field name + expected type + observed value. The RecordFailedReason taxonomy shipped at uac@`3157f45` is the
foundation; the signature refactor is Phase 2's body of work.

**Phase 4 dependency**: `ManifestWriter.record_captured` row_key shape validation extends naturally — empty
`instrument_id` for per-instrument shards / empty `chain` for DeFi bundled shards → `record_failed(reason=
RecordFailedReason.MALFORMED_ROW_KEY)`. Phase 4 wires the guard.

**Phase 5 dependency**: PM `quality-gates.sh` STEP 5.66 AST-walk asserts (a) hard-required fields are
non-nullable in the Pydantic declarations + (b) every `record_captured` callsite passes the row_key shape
validation kwargs for bundled shards. Extends existing STEP 5.64.
