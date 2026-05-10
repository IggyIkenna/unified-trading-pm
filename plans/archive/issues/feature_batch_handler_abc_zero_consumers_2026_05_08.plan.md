---
title:
  "UTL FeatureBatchHandler ABC has zero production consumers; 8 features-* families run 4 distinct unrelated shapes"
created: 2026-05-08
author: tab-fbh-abc-adoption-investigation
source:
  - unified-trading-library@7aba113c feat(feature_service_base):
      canonical FeatureBatchHandler ABC for per-family batch handlers
  - unified-trading-pm/plans/active/features_repo_consolidation_2026_05_08.md § Phase 5.7
  - unified-trading-pm/plans/active/features_repo_consolidation_2026_05_08.md § "deferred-work scoreboard" line 1429
  - features-service/features_service/{commodity,cross_instrument,delta_one,onchain,sports,volatility,multi_timeframe,calendar}/cli/handlers/batch_handler.py
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# UTL `FeatureBatchHandler` ABC has zero production consumers; 8 families run 4 distinct unrelated shapes

> **Severity**: P1 — not data-correctness, but a workspace-SSOT contradiction that flushes the assumed-canonical shape
> lifted in Wave 3b. The deferred-work scoreboard's "1-2 hour adoption refactor" framing materially understates the
> actual scope.
>
> **Blast radius**: `unified-trading-library/feature_service_base/batch_handler.py` (the ABC + tests, ~270 LOC) and any
> future plan phase that assumes families inherit `FeatureBatchHandler[FamilyConfigT]`. No runtime impact — every family
> currently runs without touching the ABC. May-23 cutover not directly affected.
>
> **Suggested owner**: operator triage. Likely fold into `features_repo_consolidation_2026_05_08.md` Phase 5.7 follow-up
> OR a new sub-plan for the architectural reconciliation. Spawn-prompt scope (1-2h, 3-family refactor) is not
> implementable as written.

## What I found

A sub-agent was spawned to close the deferred-work item "FeatureBatchHandler ABC adoption" (per
`features_repo_consolidation_2026_05_08.md` line 1429: `helper-shipped` → `done`). The spawn prompt's premise was that 5
of 8 families had already adopted `FeatureBatchHandler[FamilyConfigT]` and the remaining 3 (commodity / cross_instrument
/ delta_one) needed migration in 1-2 hours.

That premise is incorrect at every level. Concrete current state of the 8 batch handlers:

| Family             | Class declaration                                  | Parent                                                                                                      | Key signature                                                                                                                       | LOC |
| ------------------ | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | --- |
| `commodity`        | `class BatchHandler:`                              | none                                                                                                        | sync `run(start_date, end_date, commodity, dry_run)`                                                                                | 327 |
| `cross_instrument` | `class BatchHandler:`                              | none                                                                                                        | sync `run(...)` — internal `_ingest_data` → `_process_features` (async per feature_group) → `_gate_and_write`                       | 498 |
| `multi_timeframe`  | `class BatchHandler:`                              | none                                                                                                        | sync                                                                                                                                | 109 |
| `volatility`       | `class BatchHandler(ModeHandler):`                 | local `features_service.volatility.cli.handlers.base_handler.ModeHandler`                                   | async `run(asset_group, feature_group, start_date, end_date, timeframe, instruments, lookback_buffer_days, ...) -> bool` (16+ args) | 301 |
| `delta_one`        | `class BatchHandler(ModeHandler):`                 | local `features_service.delta_one.cli.handlers.base_handler.ModeHandler`                                    | async `run(...)` 16+ arg signature                                                                                                  | 808 |
| `onchain`          | `class BatchHandler(ModeHandler):`                 | local `features_service.onchain.cli.handlers.base_handler.ModeHandler`                                      | async `run(...)` 16+ arg signature                                                                                                  | 442 |
| `sports`           | `class BatchHandler(ModeHandler):`                 | local `features_service.sports.cli.handlers.base_handler.ModeHandler`                                       | async `run(...)` 16+ arg signature                                                                                                  | 837 |
| `calendar`         | `class CalendarBatchModeHandler(BaseModeHandler):` | UTL `unified_trading_library.service_cli.BaseModeHandler` (different class than UTL `FeatureBatchHandler`!) | async `run() -> dict[str, object]` (driven by `args` namespace + `runtime`)                                                         | 456 |

`rg "FeatureBatchHandler" --type py`-equivalent across the workspace returns hits only in:

- `unified-trading-library/unified_trading_library/feature_service_base/batch_handler.py` — the ABC itself
  (UTL@7aba113c).
- `unified-trading-library/tests/unit/feature_service_base/test_batch_handler.py` — its own self-tests, with
  `_DemoBatchHandler` / `_FailingBatchHandler` / `_EmptyHandler` / `BadHandler` test fixtures.

**Zero production consumers.** No family extends `FeatureBatchHandler`. The ABC was lifted in Wave 3b on the assumption
that adoption would follow; it didn't.

## Why the spawn-prompt's APPROACH (b) doesn't fit in 1-2 hours

`FeatureBatchHandler[FamilyConfigT]`'s required override surface is:

- `enumerate_shards(date, asset_group) -> list[str]` — return per-shard keys.
- `compute_one_shard(shard_key, date, asset_group, correlation_id) -> pl.DataFrame` — sync, single-shard compute
  returning a polars frame.
- `shard_output_path(shard_key, date, asset_group) -> str` — canonical output path.
- `record_shard_result(shard_key, date, asset_group, result, frame) -> None` — manifest verb dispatch.

The UTL ABC's mental model is "1 shard → 1 polars frame → 1 manifest write." None of the 8 families operate that way:

1. **`cross_instrument`** runs `_ingest_data` (async, reads delta-one upstream) → `_process_features` (async, iterates
   feature_groups, dispatches to `paired_price_dispersion` for one group + service.compute_features for others) →
   `_gate_and_write` (writegate + per-group persist). It's a single-day flow over feature_groups, NOT a per-shard
   fan-out. There is no natural `shard_key` axis.
2. **`commodity`** iterates per-(commodity, day) over a date range, composes signals from multiple factors per
   commodity, and writes 1 JSON blob per (commodity, day). The "shard" is really `(commodity, day)` but the compute is
   multi-factor with cross-factor coverage gating (`_has_full_factor_coverage`); doesn't decompose to a single polars
   frame.
3. **`delta_one`** runs an async preflight + parallel per-instrument compute orchestrated externally with a 16-arg
   `run()` (lookback_buffer_days, output_timeframes, max_workers, skip_dependency_check, fail_on_missing_deps,
   preflight_only, …). Forcing this through `enumerate_shards` + `compute_one_shard` discards the entire orchestration
   layer.
4. **`volatility / onchain / sports`** mirror delta-one's `ModeHandler` shape (16+ args, parallel workers, dependency
   check, async run).
5. **`calendar`** uses `BaseModeHandler` (different UTL class — `service_cli.BaseModeHandler`, not
   `feature_service_base.FeatureBatchHandler`) with `args`+`runtime` injection from `ServiceCLI`. It also doesn't fit
   `FeatureBatchHandler`.

To force-fit even one family into `FeatureBatchHandler` we'd need to either (a) widen the ABC to absorb 16-arg async run
signatures + multi-feature-group iteration + lookback buffers + parallel workers — diluting the contract to nothing — or
(b) rewrite the family's compute pipeline (498-808 LOC each on production code) to map onto the per-shard 1-frame
abstraction. Neither is 1-2 hours; both touch live production paths under May-23 deadline pressure.

The plan body itself acknowledges this — line 1429: **"Adoption blocked on shape reconciliation: either narrow UTL ABC,
widen ModeHandler, or write per-family shim. ~2-3 day work. Successor plan TBD."** The deferred-work scoreboard's
framing ("close FeatureBatchHandler ABC adoption") understates this; an "adoption refactor" is not the right verb when
zero consumers exist + the shape doesn't fit any family.

## Why it matters

- **Workspace-SSOT contradiction.** UTL ships an ABC that codex would describe as "the canonical shape per
  `FeatureBatchHandler[FamilyConfigT]`," but no consumer code matches that shape. An agent reading UTL
  `feature_service_base/batch_handler.py` and an agent reading any features-service family see different worlds.
  CLAUDE.md "Plans Run To Actual Completion" + "Citadel-Grade § 7 Single Source of Truth" both fire.
- **Deferred-work scoreboard rot.** A line-item that sat on the scoreboard for 2 days, was scheduled for 1-2 hour
  closure, and turns out to be a 2-3 day architectural call. Other deferred-work scoreboard items may have similar
  shape-mismatch — worth sweeping.
- **Wave 3b cleanup gap.** The original lift assumed 5/8 adopters; reality is 0/8. The lift was premature.
- **No technical debt rule (§ 3).** Shipping `FeatureBatchHandler` shims (APPROACH (c)) for an ABC nobody uses would be
  writing wrappers around code that has no canonical consumer to wrap. That's debt by construction.

## Recommended decision

This is a design call, not an implementation refactor. Three real options (the plan body's three are roughly accurate):

**(α) Narrow + redesign the UTL ABC** to match the actual common shape across families. The genuine commonality is
`BaseModeHandler` (calendar) and the local `ModeHandler` ABC (volatility / delta_one / onchain / sports). Lifting the
local `ModeHandler` to UTL — already mirrored 4× across families with identical 16-arg async signatures — is the right
SSOT move. This makes `FeatureBatchHandler` (current shape) obsolete; either delete it or re-purpose its dataclasses
(`BatchRunResult` / `BatchRunSummary`) into the new ABC.

**(β) Delete `FeatureBatchHandler` from UTL.** If no one will ever use it, it's dead code. UTL@7aba113c reverted,
scoreboard line removed, plan Phase 5.7 retroactively re-scoped. Simpler than (α) but loses the lift work.

**(γ) Defer permanently.** Mark the scoreboard line `deferred-permanently` with a successor plan filename
(`features_batch_handler_abc_redesign_<YYYY_MM_DD>.md`) that owns the design call post-cutover. Keep
`FeatureBatchHandler` in UTL as opt-in for any future greenfield family; don't force adoption.

**Sub-agent's actual recommendation**: (α). The 4-family `ModeHandler` overlap is a real workspace SSOT begging to be
lifted; doing so closes the original Wave 3b intent (a UTL canonical batch-handler ABC) without misshaping the families.
Estimated effort: 2-3 days for one focused sub-plan (lift `ModeHandler` to UTL → migrate 4 families to UTL `ModeHandler`
→ migrate 3 bare-class families → remove or redesign `FeatureBatchHandler`).

**Operator-triage triggers**: route this to (α) or (γ) explicitly; (β) is reversible later. Until routing, do NOT spawn
another adoption sub-agent for `FeatureBatchHandler` — it'll hit the same wall.

## Sub-agent action this session

Per Findings Triage Discipline case 5: notified operator (this issue doc) + did NOT ship code (would have been APPROACH
(c) shim adapters around an ABC nobody uses = technical debt by construction). The deferred-work scoreboard line in
`features_repo_consolidation_2026_05_08.md` line 1429 is left as `helper-shipped` — accurate. No plan-flip; the work is
bigger than this session can ship without operator architectural direction.
