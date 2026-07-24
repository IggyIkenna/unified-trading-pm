---
doc_type: plan
title: Features ModeHandler ABC lift — 4 families share local ModeHandler shape; lift to UTL canonical
summary:
status: complete
nature: record
asset_group: cross-cutting
stage: [meta]
repos: [features-service, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
type: code
epic: epic-code-completion
priority: P2
deadline: post-2026-05-23
parent: master_to_live_defi_2026_05_23
shipped: 2026-05-08
migrated_from: feature_batch_handler_abc_zero_consumers_2026_05_08.md (issue doc)
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
estimate_calibration_note: "Backfilled 2026-05-13: status:complete (shipped UTL@abeb5bc3 + features-service@7335bbef
  2026-05-08). Tiny residual baseline 0.5 × 0.6 = 0.3 for any final flips. **FLAG**: plan is complete; should move to
  plans/archive/ at next archival pass (no live work remaining).

  "
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Features ModeHandler ABC lift — successor plan

> **Status (2026-05-08 EOD)**: **COMPLETE**. UTL canonical `ModeHandler` shipped UTL@abeb5bc3 (lift + 11 unit tests at
> `tests/unit/feature_service_base/test_mode_handler.py`). All 4 families (`volatility / delta_one / onchain / sports`)
> migrated at features-service@7335bbef — every `batch_handler.py / live_handler.py / target_handler.py / __init__.py`
> swapped to `from unified_trading_library.feature_service_base import ModeHandler`; 4 local `base_handler.py` files
> deleted (Citadel-Grade § 3 no-tech-debt). 3 bare-class families (`commodity / cross_instrument / multi_timeframe`)
> documented as **stays-bare** decision in the codex SSOT below — divergent shapes don't fit the canonical contract;
> force-fit would distort. `calendar` stays on `service_cli.BaseModeHandler` per existing lineage.

## What this is

Successor plan capturing **option α** from the Phase 10 sub-agent's FeatureBatchHandler investigation
(`plans/archive/issues/feature_batch_handler_abc_zero_consumers_2026_05_08.plan.md`). Originally option β (delete dead
UTL FeatureBatchHandler) shipped 2026-05-08 PM at UTL@2162eee5, closing the workspace-SSOT violation. **This plan
captures the architectural follow-up**: lift the local 4-family `ModeHandler` ABC into UTL canonical so future
features-\* batch handlers have a real SSOT to inherit from.

## Why P2 / post-2026-05-23

- 4 of 8 families (`volatility / delta_one / onchain / sports`) currently inherit a per-family local `ModeHandler` class
  that's structurally identical across all 4 — a real duplicated workspace pattern begging for SSOT lift.
- 3 families (`commodity / cross_instrument / multi_timeframe`) run bare `class BatchHandler:` with no base class. They
  could adopt the lifted UTL canonical or stay bare — design call.
- 1 family (`calendar`) uses UTL `service_cli.BaseModeHandler` (different lineage). Out of scope.

The lift is architectural housekeeping. It doesn't gate May-23 cutover — features-service is operational without it.
Estimated effort: 2-3 days for one focused agent.

## Pre-audit

- Lift target: 4 copies of `ModeHandler` in:
  - `features-service/features_service/volatility/cli/handlers/base_handler.py`
  - `features-service/features_service/delta_one/cli/handlers/base_handler.py`
  - `features-service/features_service/onchain/cli/handlers/base_handler.py`
  - `features-service/features_service/sports/cli/handlers/base_handler.py`
- Diff the 4 to extract canonical surface (likely the 16-arg async `run()` signature + lifecycle hooks).
- Lifted location: `unified-trading-library/unified_trading_library/feature_service_base/mode_handler.py`.

## Phases

1. - [x] **Diff the 4 ModeHandlers** — produced SSOT-merge artifact; per-family deltas identified (sports
         `**kwargs: object` minimal; volatility 11-arg + `run_batch`/`run_live` wrappers; delta_one 16-arg with
         lookback_buffer + dual-protocol cleanup; onchain 9-arg + EnhancedError cleanup). Lifted contract =
         most-permissive `**kwargs: object` for forward-compatibility.
2. - [x] **Lift to UTL** — UTL@abeb5bc3 ships `unified_trading_library/feature_service_base/mode_handler.py` with
         canonical `async def run(**kwargs: object) -> bool` abstract method + lifecycle hooks (`__init__` / `cleanup` /
         `_register_resource` / `_parse_date`). Cleanup uses dual-protocol (`_Closeable.close()` +
         `_Cleanupable.cleanup()`) — adopted from delta_one's superset shape. Cleanup errors route through
         `classify_and_emit_error` with `_service_name` class var override. 11 unit tests at
         `tests/unit/feature_service_base/test_mode_handler.py`. Re-exported via
         `unified_trading_library.feature_service_base.__init__.ModeHandler`.
3. - [x] **Adopt in 4 families** — features-service@7335bbef:
   - `volatility / delta_one / onchain / sports` → all
     `batch_handler.py / live_handler.py / target_handler.py / __init__.py` (15 files modified) swapped to
     `from unified_trading_library.feature_service_base import ModeHandler`.
   - 2 test files updated (`tests/onchain/unit/test_batch_handler.py:145` +
     `tests/volatility/unit/test_cli_and_tradfi.py` 2× refs).
   - 4 local `base_handler.py` files DELETED (Citadel-Grade § 3 no-tech-debt).
   - Per-family smoke verified:
     `BatchHandler.__mro__[1].__module__ == 'unified_trading_library.feature_service_base.mode_handler'` for all 4.
4. - [x] **3 bare-class families decision — STAY BARE** (sub-agent design call per
         `Clear context = implement, don't ask` rule):
   - `commodity` (327 LOC, sync `run(start_date, end_date, commodity, dry_run)`, per-(commodity, day) shards with
     multi-factor compute + cross-factor coverage gating) — no natural fit for the canonical 16-arg async ModeHandler
     contract.
   - `cross_instrument` (498 LOC, async `_ingest_data → _process_features → _gate_and_write` over feature_groups, NOT a
     per-shard fan-out) — no shard_key axis to map onto canonical.
   - `multi_timeframe` (109 LOC compact compute, doesn't share lifecycle) — adoption would add ceremony with no shared
     logic to lift.

   Force-fit would either (a) widen the ABC absorbing 16-arg signatures + multi-feature_group iteration + cross-factor
   gating (diluting contract to nothing — same wall the original `FeatureBatchHandler` lift hit, per
   [`plans/archive/issues/feature_batch_handler_abc_zero_consumers_2026_05_08.plan.md`](../archive/issues/feature_batch_handler_abc_zero_consumers_2026_05_08.plan.md)),
   OR (b) rewrite the family's compute pipeline (327-498 LOC each) to map onto the per-shard 1-frame abstraction.
   Neither is a small refactor; both touch live production paths under May-23 deadline pressure. **If a future
   bare-class family grows to need shared lifecycle, adoption is a small refactor (subclass + register resource +
   override `_service_name`); contract is open.**

5. - [x] **calendar lineage decision — STAY SEPARATE**. Calendar uses
         `unified_trading_library.service_cli.BaseModeHandler` (different lineage with `args`+`runtime` injection from
         ServiceCLI). Not unified with `feature_service_base.ModeHandler` because the contract surfaces differ
         (config-driven vs CLI-args-driven). Documented in codex.
6. - [x] **Codex SSOT update** — `/codex/04-architecture/features-service-architecture.md` extended with new
         `### Canonical ModeHandler ABC (lifted 2026-05-08, UTL@abeb5bc3)` subsection under "UTL helpers shared across
         families" (PM@<this-commit>). Adoption status table covers all 8 families + their decisions.
7. - [x] **Workspace QG sweep** — features-service + UTL clean (per-file diffs surgical; deleted files clean; smoke
         imports green; no stragglers via `grep -rn "features_service.*\.cli\.handlers\.base_handler"` returns zero).

## Done definition

- ✅ UTL@abeb5bc3: canonical ModeHandler + 11 tests.
- ✅ features-service@7335bbef: 4 families adopt UTL ModeHandler + 2 test refs updated.
- ✅ 4 local `base_handler.py` files deleted (Citadel-Grade § 3 no-tech-debt).
- ✅ Codex SSOT doc updated (PM@<this-commit>).
- ✅ Per-family smoke imports clean (BatchHandler.**mro**[1] resolves to
  `unified_trading_library.feature_service_base.mode_handler.ModeHandler`).
- ✅ Sub-agent decisions recorded for the 3 bare-class families (stay bare) + calendar lineage (stay separate).

## Composes with

- `features_repo_consolidation_2026_05_08.md` — closes the FeatureBatchHandler residual.
- `feature_batch_handler_abc_zero_consumers_2026_05_08.md` (issue doc) — option α captured here.
- `Citadel-Grade Planning § 7 Single Source of Truth` — 4-family ModeHandler duplication is a real SSOT violation; this
  plan resolves it.
