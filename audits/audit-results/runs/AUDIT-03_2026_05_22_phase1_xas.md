---
title: "AUDIT-03 — Phase 1 READ results: §2.13 XAS (cross-archetype / cross-asset-class regression safety)"
audit_id: AUDIT-03
run_phase: "Phase 1 — static drift, READ checkpoints"
section: "§2.13 cross-archetype / cross-asset-class regression safety (XAS-*)"
date: 2026-05-22
method: "sonnet sub-agent first-pass (evidence-required) → Opus reviewer consolidation"
auditor: Harsh + Claude Opus 4.7 (reviewer)
checklist: audits/audit-files/audit_03_defi_archetypes_e2e.md
code_audited:
  - strategy-service@b303a358 — engine/strategies/v2/factory.py, portfolio_allocator/archetypes.py, target_universe/catalog.py, *_handler.py, hedge_ratio_writer.py, decision_context_writer.py, gcs_storage_service.py, grid_generator.py
  - unified-api-contracts@c3f7a45 — internal/{enums,execution}.py, canonical/crosscutting/errors/defi.py, transfer_events.py
  - execution-service@a848ef61 — transfer_coordinator.py
oracle: codex/04-architecture/{client-funds-isolation,shard-level-failure-isolation}.md + CLAUDE.md (53-archetype safety, bucket-name SSOT, asset_group vocab)
---

# AUDIT-03 — Phase 1 READ — §2.13 XAS

Sub-agent first pass, Opus-reviewed. **4 findings (F-34…F-37)**, plus confirmations that two of my own EXE/ALC findings
generalize cross-archetype (XAS-06↔F-27, XAS-08↔F-23). XAS-00 meta-rule reminder: any shared-layer fix from this audit
needs cross-archetype regression evidence before close.

## Per-checkpoint verdicts

| ID | Verdict | Evidence |
| -- | ------- | -------- |
| XAS-01 | **CODE-DRIFT** | `ARCHETYPE_ENGINE_REGISTRY` (factory.py:55-84) = **28 entries**; `StrategyArchetype` enum = **55 members** (docstring says "53" — also stale). 29 enum values have no engine (all VOL_* except VOL_TRADING_OPTIONS, 5 granular MM variants, ARBITRAGE_MEV_SANDWICH, ARBITRAGE_CROSS_DOMAIN_EVENT, 4 PORTFOLIO_*). `get_archetype_engine_class()` raises `KeyError` if any dispatched → **F-34** |
| XAS-02 | PASS | 0 `if mode=="live"` signal/decision branches in strategy-service source; `batch_handler.py:426` hit is comment-only; `live_handler.py:33` is a docstring example. batch=live holds for signal logic |
| XAS-03 | PASS | `available_at=datetime.now(UTC)` in staked_basis.py:561 + price_dispersion.py:178 are write-time (inside instruction-emit blocks); batch_handler.py:1320 uses record-write-time `now_utc`. No read-time derivation in strategy/execution |
| XAS-04 | PHASE2-DEFERRED | manifest divergence (MISSING_EXPECTED + DIVERGENT_EMPTY × 5 asset_groups) needs GCS query at runtime |
| XAS-05 | PHASE2-DEFERRED | schema_version ≥95% v8 × asset_group needs manifest parquet query |
| XAS-06 | **CODEX-DRIFT** | `DefiErrorCode` is a plain class (not StrEnum), **35** constants (CCTP +5 not in the "30" claim) — confirms **F-27**. `AtomicInstruction` absent from UAC (only e2e-testing imports); `PnLFactor` not in UAC (aligns with F-17); `execution_mode`↦`ManualExecutionMode` (StrEnum, internal/execution.py:47). Invariant partly drafted against UAC shapes that don't all exist → **F-35-adjacent** (see reviewer note) |
| XAS-07 | PASS | 0 `: Any` type annotations in `unified_api_contracts/internal/` or `/canonical/` (only docstring prose) |
| XAS-08 | **CODE-DRIFT / CODEX-DRIFT** | `CrossClientTransferForbiddenError` defined in execution-service `transfer_coordinator.py:49` (not UAC); 1 actual raise (coordinator:241); 0 in UAC, 0 in strategy-emit; `TransferIntent` has no `model_validator`. The CLAUDE.md "3 layers" claim is aspirational → **F-36**. Generalizes F-23 (ALC-05) cross-asset-class |
| XAS-09 | PASS (count stale) | `BaseRankAllocator` (archetypes.py:381) has **7** direct subclasses (audit says 6 — `ArbitragePriceDispersionRankAllocator` added Phase 8); base contract (`_eligible`/`_score`/`weight`) uniform across all. Minor: update XAS-09 text to 7 |
| XAS-10 | PASS | catalog.py generates slots per-archetype via isolated `_build_<archetype>()` fns; `VENUE_COLLATERAL_MATRIX` referenced only by `accepted_perp_collateral()` inside the staked-basis builder — a matrix change for our slots leaves sibling archetype slot counts untouched |
| XAS-11 | **CODE-DRIFT** | `category=` leakage: `hedge_ratio_writer.py:142` + `decision_context_writer.py:155` pass `category="defi"` to `record_captured()` (should be `asset_group=`); `live_handler.py:33` docstring example; `batch_handler.py` deprecation alias emitting both keys; legacy `category=cefi` read-path in a decision-trace → **F-37** |
| XAS-12 | PHASE2-DEFERRED | `a6_batch_live_adapter_parity.py` exists (PM plans/audit/results); execution needs live GCS |
| XAS-13 | **CODE-DRIFT** | `gcs_storage_service.py:185,251,293-302` builds `gs://` URIs via f-strings passed to `polars.write_parquet` (actual writes, `# noqa: gs-uri`); `grid_generator.py:100` write-path f-string; `catalogue_bucket=f"strategy-store-{project_id}"` (hedge_ratio_writer:136, decision_context_writer:149) bypasses `resolve_bucket_name` → **F-37-adjacent** (folded into bucket-SSOT finding) |
| XAS-14 | PASS | 0 stale `strategy_and_dart_service` / `strategy_and_dart` import refs outside PM migration-doc references |

## Findings

| ID | Checkpoint | Class | Finding | Sev | Status |
| -- | --------- | ----- | ------- | --- | ------ |
| F-34 | XAS-01 | CODE-DRIFT | `ARCHETYPE_ENGINE_REGISTRY` registers 28 of 55 `StrategyArchetype` enum members; 29 archetypes (VOL family, granular MM, 2 ARBITRAGE_*, 4 PORTFOLIO_*) have no engine → `KeyError` at dispatch. Enum docstring says "53" (also stale). No guard comment marks the registry as an intentional rollout-subset. `factory.py:55-84` + `enums.py:31-137` | P1 | NEEDS-DECISION (rollout-subset vs oversight — operator/Opus call) |
| F-35 | XAS-06 | CODEX-DRIFT | XAS-06 invariant references shared UAC types not all present: `AtomicInstruction` (only in e2e-testing, not UAC source), `PnLFactor` (absent — aligns with F-17). `DefiErrorCode` is a plain string-constant class (additive but no StrEnum exhaustiveness). Confirm canonical locations / whether these were planned-but-unshipped. [DefiErrorCode count = F-27] | P2 | NEEDS-CONFIRM |
| F-36 | XAS-08 | CODEX-DRIFT | CLAUDE.md client-funds-isolation "3 layers (UAC schema construction, strategy-emit, execution-consume)" is aspirational: `CrossClientTransferForbiddenError` lives in execution-service (not UAC), 1 raise (coordinator:241), 0 in UAC/strategy; `TransferIntent` has no validator. Generalizes F-23. Fix: add a UAC `TransferIntent` `model_validator` OR reconcile the doc to "structural single-client_id + 1 coordinator raise" | P1 | CONFIRMED (extends F-23) |
| F-37 | XAS-11 + XAS-13 | CODE-DRIFT | (a) `category="defi"` passed to `record_captured()` in `hedge_ratio_writer.py:142` + `decision_context_writer.py:155` (should be `asset_group=`) + `batch_handler` deprecation alias; (b) inline `gs://` write-path f-strings in `gcs_storage_service.py:185/251/293` + `grid_generator.py:100` + `catalogue_bucket` f-string — both bypass workspace SSOT (`asset_group=` + `resolve_bucket_name`) | P1 | CONFIRMED |

## Reviewer notes

- **F-34 is the headline cross-cutting finding**: a 28-of-55 factory means 29 archetypes raise `KeyError` if dispatched.
  Needs an architecture decision — is the registry intentionally the cutover-rollout subset (then add a guard comment +
  a clear `NotYetImplementedArchetypeError`), or an oversight (then add stubs)? The enum docstring "53" vs 55 members is
  itself a minor count drift. **Not a May-23 blocker** for our 2 archetypes (both registered) but a real 53-archetype
  safety gap.
- **XAS-08/F-36 generalizes F-23**: the cross-client invariant HOLDS structurally (TransferIntent single client_id +
  coordinator raise) but the codex "3-layer + UAC validator" wording is wrong on all 3 counts. The cleanest fix is a UAC
  `model_validator` (belt-and-suspenders + satisfies the required-test), which would also make the doc accurate.
- **F-37 (bucket-SSOT + category= leakage)** is XAS's confirmation that the bucket-name + asset_group vocab rules have
  drift in strategy-service writers — composes the workspace bucket-SSOT HARD RULE; the `# noqa: gs-uri` suppressions
  flag these as known-but-unresolved.
- XAS-04/05/12 are Phase-2 RUN (manifest/parquet queries) — deferred.
