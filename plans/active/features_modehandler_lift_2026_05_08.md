---
title: "Features ModeHandler ABC lift — 4 families share local ModeHandler shape; lift to UTL canonical"
type: code
epic: epic-code-completion
status: planned
asset_group: cross-cutting
priority: P2
deadline: post-2026-05-23
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-08
created: 2026-05-08
migrated_from: feature_batch_handler_abc_zero_consumers_2026_05_08.md (issue doc)
---

# Features ModeHandler ABC lift — successor plan

## What this is

Successor plan capturing **option α** from the Phase 10 sub-agent's FeatureBatchHandler investigation
(`plans/active/issues/feature_batch_handler_abc_zero_consumers_2026_05_08.md`). Originally option β
(delete dead UTL FeatureBatchHandler) shipped 2026-05-08 PM at UTL@2162eee5, closing the workspace-SSOT
violation. **This plan captures the architectural follow-up**: lift the local 4-family `ModeHandler`
ABC into UTL canonical so future features-* batch handlers have a real SSOT to inherit from.

## Why P2 / post-2026-05-23

- 4 of 8 families (`volatility / delta_one / onchain / sports`) currently inherit a per-family local
  `ModeHandler` class that's structurally identical across all 4 — a real duplicated workspace pattern
  begging for SSOT lift.
- 3 families (`commodity / cross_instrument / multi_timeframe`) run bare `class BatchHandler:` with no
  base class. They could adopt the lifted UTL canonical or stay bare — design call.
- 1 family (`calendar`) uses UTL `service_cli.BaseModeHandler` (different lineage). Out of scope.

The lift is architectural housekeeping. It doesn't gate May-23 cutover — features-service is operational
without it. Estimated effort: 2-3 days for one focused agent.

## Pre-audit

- Lift target: 4 copies of `ModeHandler` in:
  - `features-service/features_service/volatility/cli/handlers/base_handler.py`
  - `features-service/features_service/delta_one/cli/handlers/base_handler.py`
  - `features-service/features_service/onchain/cli/handlers/base_handler.py`
  - `features-service/features_service/sports/cli/handlers/base_handler.py`
- Diff the 4 to extract canonical surface (likely the 16-arg async `run()` signature + lifecycle hooks).
- Lifted location: `unified-trading-library/unified_trading_library/feature_service_base/mode_handler.py`.

## Phases

1. **Diff the 4 ModeHandlers** — produce SSOT-merge artifact + identify per-family deltas (subscribe
   hooks, error classifiers, etc).
2. **Lift to UTL** — `feature_service_base/mode_handler.py` with the canonical 16-arg async `run()`
   signature + abstract hooks. Per-family deltas become subclass overrides.
3. **Adopt in 4 families** — replace local `from .base_handler import ModeHandler` with
   `from unified_trading_library.feature_service_base.mode_handler import ModeHandler`. Delete local
   `base_handler.py`.
4. **3 bare-class families decision** — operator picks: (a) adopt UTL canonical, or (b) stay bare. Per
   `Two teammates` rule, this is a design call.
5. **calendar lineage decision** — calendar uses `BaseModeHandler` from `service_cli` (different
   class). Either keep separate or unify into UTL canonical. Operator decision.
6. **Codex SSOT update** — document the canonical pattern in
   `codex/04-architecture/features-service-architecture.md` (extend the existing Phase 9 doc).
7. **Workspace QG sweep** — features-service + UTL clean.

## Done definition

- ✅ UTL@<sha>: canonical ModeHandler + tests.
- ✅ 4 features-service@<sha>: 4 families adopt UTL ModeHandler.
- ✅ Local `base_handler.py` files deleted (Citadel-Grade § 3 no-tech-debt).
- ✅ Codex SSOT doc updated.
- ✅ Operator answer recorded for the 3 bare-class families + calendar lineage.

## Composes with

- `features_repo_consolidation_2026_05_08.md` — closes the FeatureBatchHandler residual.
- `feature_batch_handler_abc_zero_consumers_2026_05_08.md` (issue doc) — option α captured here.
- `Citadel-Grade Planning § 7 Single Source of Truth` — 4-family ModeHandler duplication is a real SSOT
  violation; this plan resolves it.
