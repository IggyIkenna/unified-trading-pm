---
doc_type: audit-instruction
title: execution_master_audit_instructions
summary:
  Weekly execution-service audit — venue handlers (all CeFi + DeFi venues), transfer coordinator, treasury,
  CLOUD_KMS_ENCRYPTED custody (Copper + CEFFU post-June-1), flash-loan receiver, matching engine — enforcing the HARD
  RULE that cross-client funds movement is forbidden at all 3 CrossClientTransferForbiddenError enforcement layers.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: [audit, execution, client-isolation, defi, cefi, verification]
related: []
created: 2026-05-22
tier: L2
parent_epic: execution_master
cadence: weekly (minimum)
verifier:
lifespan:
type: audit-instructions
epic: execution_master
assigned_vm: vm-trading-core
last_updated: 2026-05-22
---

# Execution Master — Audit Instructions

## Epic Scope

execution-service: venue handlers (all CeFi + DeFi venues), transfer coordinator, treasury, custody path
(`CLOUD_KMS_ENCRYPTED` for May-23; Copper + CEFFU post-June-1), flash loan receiver, matching engine. Hard rule:
cross-client funds movement FORBIDDEN at all 3 enforcement layers.

Codex SSOTs: `/codex/04-architecture/client-funds-isolation.md`, `/codex/04-architecture/flash-loan-receiver.md`,
`/codex/04-architecture/custody-providers.md`, `/codex/04-architecture/defi-execution-overview.md`

## Triggers

- Weekly (minimum cadence)
- After any new venue handler ships
- After any custody provider change or credential rotation
- After any transfer/withdraw/deposit code change
- When cross_client_funds_isolation retroactive audit shows new gaps

## Checklist

- [ ] (a) **CrossClientTransferForbiddenError at all 3 layers**: raised at UAC schema construction, strategy-service
      emit, and execution-service consume. Grep: `rg "CrossClientTransferForbiddenError" --include="*.py"` — verify 3
      distinct call sites

- [ ] (b) **client_id invariant on every fund movement**: every transfer/withdraw/deposit/bridge operation checks
      `source_account.client_id == dest_account.client_id`. Grep: `rg "client_id" execution-service/ --include="*.py"` —
      review all transfer-path usages Run: happy intra-client path test + UAC-validator-rejects-cross-client test

- [ ] (c) **CLOUD_KMS_ENCRYPTED path tested**: KMS custody path has end-to-end test (Tenderly fork or mock). Find:
      `rg "KMS|kms" execution-service/tests/ --include="*.py" -l` Verify: Copper/CEFFU June-1 timeline documented;
      May-23 ships on KMS only

- [ ] (d) **FlashLoanReceiver.sol matches codex**: contract in `deployment-service/contracts/FlashLoanReceiver.sol`
      matches description in `/codex/04-architecture/flash-loan-receiver.md`. Grep:
      `rg "FlashLoanReceiver" deployment-service/ --include="*.sol"` Read: codex doc — verify ABI, callback signature,
      and re-entrancy protection match

- [ ] (e) **SwapRouter02 address matches UAC constant**: `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45` Grep:
      `rg "68b3465833fb72A70ecDF485E0e4C7bD8665Fc45" --include="*.py"` — verify it's a UAC constant, not hardcoded in
      execution-service business logic

- [ ] (f) **All venue handlers classify errors**: every venue handler calls `classify_venue_error()` on error path.
      Grep: `rg "classify_venue_error" execution-service/ --include="*.py"` — count vs handler file count

- [ ] (g) **6 BLOCKING gaps from retroactive audit shipped**: all items from
      `cross_client_funds_isolation_retroactive_audit_2026_05_20.md` are in code. Check: the active plan absorbing those
      gaps — all `- [x]`

- [ ] (h) **Shard-level failure isolation**: no `raise` inside per-venue loops in execution-service handlers. Grep:
      `rg "^\s+raise " execution-service/ --include="*.py"` — review each hit

### E2E Pipeline Verification (Batch → Paper → Live)

- (e2e-batch) **Batch e2e audit**: run `bash scripts/quality-gates.sh` with mock upstream features data → strategy
  produces signals → execution records manifest rows. Use `CLOUD_MOCK_MODE=true` and synthetic feature fixtures. Goal:
  confirm the entire batch code path executes without real upstream data.
- (e2e-paper) **Paper trading goal post**: paper trading for ≥1 DeFi archetype runs ≥7 days without silent failures.
  Manifest shows strategy_output + execution_record rows. PnL stream emits StrategyPnlStreamEvent. Dashboard shows paper
  positions. This is the gate before live.
- (e2e-live) **Live trading goal post**: live execution for ≥1 DeFi archetype with real wallet transactions confirmed
  on-chain. PnL calculator confirms realized + unrealized PnL matches expected from strategy signals.
- (post-trade) **Post-trade audit**: after live runs ≥7 days, verify execution records match strategy signals (no
  slippage model regression), PnL attribution is correct, and no cross-client fund movement occurred.
- (mock-upstream) **Mock upstream pattern**: strategy and execution audits MUST be runnable with mock MTDS + features
  data. Document the mock fixture location and how to substitute upstream parquets for independent downstream testing.

## Canonical-form cross-service audit coverage (CF-1 … CF-12)

SSOT: `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` (CF-1…CF-12 definitions + service ×
asset_group matrix). execution_master OWNS the live FORM checks against the execution-record `_index` (fills / transfers
/ global-ledger `LedgerRow` rows): CF-1, CF-2, CF-5, CF-8, CF-9, CF-12. CF-4 is **EXEMPT** — execution outputs are
computed, no vendor `source`. CF-3/6/7/10/11 are **n/a** — execution does not fetch raw market data. **Little-data
note**: execution has run almost no real volume yet, so the data-state read is quick — but the FILL/LEDGER WRITER MUST
already emit v9 + `asset_group=` + typed reasons + honest `available_at` BEFORE volume arrives, so audit the writer code
path even when the corpus is near-empty.

- [ ] (CF-1) **schema_version = v9 on execution-record + ledger rows (data-state, not constant)**: read the actual
      `schema_version` distribution from the execution-record `_index` + global-ledger `_index` (and a parquet sample),
      NOT `MANIFEST_SCHEMA_VERSION`. Then audit the writer: grep the fill/transfer/ledger emit path —
      `rg "record_captured|record_empty|LedgerRow|schema_version" execution-service/ --include="*.py"` and the
      `LedgerRow` construction sites — confirm v9 is what would be stamped on the next write. GREEN: every existing row
      is v9 AND the writer stamps v9. (Manifest-v8 lesson: a constant said v8 while 0% of rows were v8.)

- [ ] (CF-2) **`asset_group=` not `category=` on execution-record PATHS + `_index` ROWS**: grep object paths for the
      legacy key `rg "category=" execution-service/ --include="*.py"` and read `_index` rows for any `category` field;
      confirm the execution-record + ledger writers emit `asset_group=` on both the GCS path hive-key and the manifest
      row. GREEN: 0 `category=` on paths/rows; `asset_group=` canonical everywhere.

- [ ] (CF-5) **Typed `EmptyConfirmedReason` on every empty execution/ledger cell**: read the empty-reason histogram from
      the execution-record + ledger `_index`; assert 0 blank / untyped. Audit the writer:
      `rg "record_empty|EmptyConfirmedReason|EXPECTED_|SOURCE_RETURNED_ZERO" execution-service/ --include="*.py"` —
      confirm execution emits the closed-set reasons (`EXPECTED_UPSTREAM_EMPTY` for no-signal days,
      `EXPECTED_OUTSIDE_PROCESSING_SCOPE`, `SOURCE_RETURNED_ZERO` only when genuinely flat) and never a blank reason
      (would trip `LegacyBlankErrorReasonError`). GREEN: 0 blank/untyped empty cells; writer uses typed reasons only.

- [ ] (CF-8) **`available_at` per-row, honest — never lookahead / migration-time / read-time**: read `available_at` vs
      the row's day boundary on execution-record + ledger rows; assert it is the real write/fill time, never derived at
      read-time. Audit the writer: `rg "available_at" execution-service/ --include="*.py"` — confirm it is passed
      per-row at write time (UTL `record_captured` asserts presence internally) and that batch and live derive it
      identically (top `SOURCE_PRIORITY` entry's live `available_at`). GREEN: per-row honest `available_at`, batch=live
      parity.

- [ ] (CF-9) **env-split bucket `{kind}-{env}-{project}` via `resolve_bucket_name()`**: grep for inline `gs://` /
      `s3://` f-strings `rg "gs://|s3://" execution-service/ --include="*.py"` (QG STEP 5.69 ratchet) — confirm every
      execution-record / ledger bucket lookup routes through
      `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud=…, kind=…, asset_group=…, env=…)`
      and is env-tiered (`-prd`/`-test`). GREEN: 0 inline bucket f-strings; all lookups canonical + env-split.

- [ ] (CF-12) **batch = live symmetry on execution outputs**: diff the batch vs live execution-record + ledger schema /
      data_type set / field set per asset_group; confirm one code path (only execution fills differ — never schema /
      data_types / fields), and that no live-only execution data_type exists and `available_at` is not derived at
      read-time. Grep for any live-only branch: `rg "is_live|live_only|if.*live" execution-service/ --include="*.py"`
      and read each hit. GREEN: identical schema + data_types + fields batch vs live; single code path.

- **n/a (with reason)**: CF-3 (`pipeline_mode=` partition) — execution does not write hive-partitioned raw market-data
  paths; CF-4 (`source` column) — EXEMPT, execution outputs are computed (no vendor source); CF-6
  (`expected_unattempted` 4th state) — execution does not pre-flight an IS-owed universe; CF-7 (canonical
  venue/data_type names) — execution does not name raw-market data_types; CF-10 (phantom captured) — no
  pre-genesis/date-impossible object walk for execution outputs; CF-11 (fetch-failure swallow) — execution does not
  fetch raw market data (its venue-error classification is covered by checklist item (f)).

## Success Criteria

- All 8 checklist items GREEN
- Cross-client transfer impossible in all code paths (verified by tests)
- execution-service QG exits 0

- Batch e2e with mock upstream: full code path from features → strategy → execution runs without errors
- Paper trading ≥7 days: strategy_output + execution_record rows in manifest, PnL events flowing
- Live trading confirmed: ≥1 on-chain transaction verified for a real wallet

## Output Format

Result file at `plans/audit/results/execution_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
