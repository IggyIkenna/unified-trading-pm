---
doc_type: audit-instruction
title: strategy_master_audit_instructions
summary:
  Weekly audit checklist for strategy-service post-consolidation — 8 checks (53 archetypes registered,
  portfolio_allocator determinism, zero stale strategy-and-dart-service refs, batch=live signal identity, shard-level
  no-raise) plus CF-1/2/5/8/9/12 canonical-form checks on the strategy-output _index and batch→paper→live e2e goal
  posts.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [audit, strategy, reconciliation, data-correctness, ssot-audit, quality-gates]
related:
  [
    /plans/audit/instructions/canonical_form_cross_service_audit_checklist.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    ../../../codex/09-strategy/architecture-v2/archetypes/,
  ]
created: 2026-05-22
tier: L2
parent_epic: strategy_master
cadence: Weekly
verifier:
lifespan:
type: audit-instructions
epic: strategy_master
assigned_vm: vm-trading-core
last_updated: 2026-05-22
---

# Strategy Master — Audit Instructions

## Epic Scope

strategy-service post-consolidation: 53 archetypes across all asset_groups, `portfolio_allocator`, risk manager,
position tracker, PnL calculator, and batch=live code path identity. Shard-level failure isolation required.

Codex SSOTs: `codex/09-strategy/architecture-v2/archetypes/`, `/codex/04-architecture/shard-level-failure-isolation.md`,
`plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`

## Triggers

- Weekly (minimum cadence)
- After each new archetype is added or removed from the registry
- After any repo consolidation phase completes (verify no stale import references)
- When `execution_master` audit surfaces strategy→execution contract violations

## Checklist

- [ ] (a) **53 archetypes registered**: all 53 archetypes present in the archetype registry (no orphans). Grep:
      `rg "class.*Archetype\|register_archetype" strategy-service/ --include="*.py"` — count and verify

- [ ] (b) **strategy_archetype_logic_audit findings GREEN**: all findings from the Opus 1M logic audit are in code.
      Check: `plans/audit/results/strategy_archetype_logic_audit_2026_05_20.md` — verify all RED items have commit SHAs

- [ ] (c) **portfolio_allocator determinism**: same input → same allocation output (no time-dependent randomness). Run:
      unit test for `portfolio_allocator` with fixed seed if applicable

- [ ] (d) **QG passes clean**: zero new violations introduced by consolidation phases. Run:
      `bash scripts/quality-gates.sh` in strategy-service — exit 0 required

- [ ] (e) **Zero stale repo references**: consolidation Phase 11 stale ref cleanup fully shipped. Grep:
      `rg "strategy-and-dart-service|strategy_and_dart_service" --include="*.py"` across all service repos — should be 0
      hits (old consolidated repo name) Check: `strategy_consolidation_phase11_stale_ref_cleanup_2026_05_21.md` — all 6
      sub-phases `- [x]`

- [ ] (f) **Batch=live code path identity**: strategy produces identical signals for same tick sequence regardless of
      `--mode batch` vs `--mode live`. Verify: no `if mode == "live"` branching in signal computation logic Grep:
      `rg "mode.*live\|live.*mode" strategy-service/ --include="*.py"` — review any hits for correctness

- [ ] (g) **dYdX venue token regression resolved**: dYdX venue token issue has an operator-acked decision (Option A:
      re-add to UAC, B: remove from catalog, or C: xfail markers). Check:
      `strategy_dydx_venue_token_regression_2026_05_20.md` status — must not be indefinitely BLOCKED-OPERATOR

- [ ] (h) **Shard-level failure isolation**: no `raise` inside per-venue or per-shard loops in strategy computation.
      Grep: `rg "^\s+raise " strategy-service/ --include="*.py"` — review each hit; raises inside loops are violations

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

## Canonical-form cross-service audit coverage (CF-1…CF-12)

SSOT: `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` (CF-1…CF-12 definitions + the
service×CF ownership matrix). **strategy-service coverage**: strategy outputs are a manifest-backed `_index` (signals /
candidate manifests / `strategy_output`), so strategy OWNS the live FORM checks for the applicable invariants (CF-1,
CF-2, CF-5, CF-8, CF-9, CF-12) read against that `_index`. **CF-4 is exempt** — strategy outputs are _computed_, not
vendor-ingested, so there is no `source` column to stamp. **CF-3, CF-6, CF-7, CF-10, CF-11 are n/a** — strategy neither
fetches raw market data nor writes on-disk `pipeline_mode=` partitions / venue-named data_type corpora. **Caveat**:
strategy/execution have had LITTLE data run so far, so the data-state read is QUICK — but the audit's real job is to
confirm the **writer emits canonical form NOW**, before volume arrives. Cross-reference (don't duplicate) the per-CF
definitions in the SSOT.

- [ ] (CF-1) **schema_version = v9 on strategy `_index` rows + parquets**: read the ACTUAL `schema_version` distribution
      from the strategy-output `_index` (signals / candidate manifests / `strategy_output`) + a sample of strategy
      parquets — NOT the `MANIFEST_SCHEMA_VERSION` constant (manifest-v8 lesson). With low volume, also grep the writer
      to confirm it stamps v9: `rg "schema_version|MANIFEST_SCHEMA_VERSION" strategy-service/ --include="*.py"`. Any row
      below v9 (or NULL) is RED → fix the writer + relabel.

- [ ] (CF-2) **`asset_group=` not `category=` on PATHS and ROWS**: grep strategy-output object paths for a `category=`
      hive segment and the `_index` rows for a `category` field — both must be `asset_group=` only. Writer grep:
      `rg "category=|\"category\"|category=" strategy-service/ --include="*.py"` — review hits; confirm strategy emits
      `asset_group=` everywhere (paths + manifest rows).

- [ ] (CF-5) **Typed `EmptyConfirmedReason` on every empty strategy cell**: read the empty-reason histogram on the
      strategy `_index`; assert 0 blank / untyped. For computed/downstream outputs the right reasons are
      `EXPECTED_UPSTREAM_EMPTY` (no upstream features/MTDS for the cell) + `EXPECTED_OUTSIDE_PROCESSING_SCOPE` +
      `SOURCE_RETURNED_ZERO` only when genuinely empty. Writer grep:
      `rg "record_empty|EmptyConfirmedReason|EXPECTED_UPSTREAM_EMPTY" strategy-service/ --include="*.py"` — confirm
      every empty path passes a typed reason (no blank → `LegacyBlankErrorReasonError`).

- [ ] (CF-8) **`available_at` per-row, honest (no read-time / lookahead derivation)**: read `available_at` vs the day
      boundary on a sample of strategy `_index` rows; assert it is per-row write-time and identical under `--mode batch`
      vs `--mode live` (batch=live derivation parity). Writer grep:
      `rg "available_at" strategy-service/ --include="*.py"` — confirm it is set at write-time, never derived at read.

- [ ] (CF-9) **env-split canonical bucket via `resolve_bucket_name()`**: grep strategy-service for inline `gs://` /
      `s3://` f-strings (QG STEP 5.69 ratchet); every strategy-output bucket lookup must go through
      `resolve_bucket_name(...)` and resolve to an env-tiered `{kind}-{env}-{project}` name. Grep:
      `rg "gs://|s3://|resolve_bucket_name" strategy-service/ --include="*.py"` — any inline URI is RED.

- [ ] (CF-12) **batch = live symmetry on strategy outputs**: confirm strategy produces an identical schema / data_type
      set / field set under `--mode batch` vs `--mode live` (composes with checklist item (f)). No live-only
      strategy-output data_type; `available_at` not derived at read-time. Diff the batch vs live output schema per
      asset_group; one code path only.

n/a for strategy (cross-reference SSOT for why): **CF-3** (no on-disk `pipeline_mode=` partition written by strategy) ·
**CF-6** (`expected_unattempted` pre-flight is owned upstream by mtds/mdps/features) · **CF-7** (canonical venue /
data_type naming applies to raw-market ingest, not computed signals) · **CF-10** (phantom captured-vs-object walk is an
ingest concern) · **CF-11** (fetch-failure → `attempted_failed` is an ingesting-adapter concern; strategy fetches no raw
market data). **CF-4** is EXEMPT-computed (no vendor `source` on a computed output).

## Success Criteria

- All 8 checklist items GREEN
- strategy-service QG exits 0
- Zero stale old-repo import references workspace-wide

- Batch e2e with mock upstream: full code path from features → strategy → execution runs without errors
- Paper trading ≥7 days: strategy_output + execution_record rows in manifest, PnL events flowing
- Live trading confirmed: ≥1 on-chain transaction verified for a real wallet

## Output Format

Result file at `plans/audit/results/strategy_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
