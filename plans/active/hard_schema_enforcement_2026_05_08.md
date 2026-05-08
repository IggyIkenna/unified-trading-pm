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
    status: blocked
    blocked_by: tradfi-master-2026-05-07
    note: "Sequenced AFTER tradfi_master Q1+Q2 futures+options expiry flips."

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

- `tradfi_master_2026_05_07.md` Q1+Q2 (futures expiry hard-required + options expiration flip) — sequenced BEFORE
  Phase 1 here.
- `sports_master_2026_05_07.md` Phase 3 C.7 — overlaps with Phase 3 here on STANDINGS / XG / MATCHES flatten work;
  coordinate to avoid duplicating cassette parity tests.
- `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 2.A — Phase 4 row_key shape validation extends the
  writegate per-row failure routing.
- `infrastructure_master_2026_05_07.md` — parent umbrella; this plan is referenced from the "Hard schema
  enforcement at write boundary" pointer section.

## Plan-format compliance

Follows `unified-trading-pm/plans/PLAN_FORMAT.md`: 3-tier readiness (C5 / D3); per-repo gates; Cursor checkboxes on
every todo; sibling-plan dependencies declared in `depends_on`; SSOT-first (codex docs in the codex-update todo own
intent, plan owns activation); pre-audit complete via the source RFC archived to `plans/archive/issues/`.
