---
doc_type: codex-ssot
title: operational-modes
summary:
  "The workspace SSOT for the operating-mode taxonomy — ONE OperationalMode enum {LIVE, MANUAL, BACKTEST, PAPER} plus
  additive (ExecutionTarget, ExecutionTrigger) axes via a pure decompose() helper; composes orthogonally with
  RuntimeMode. Deletes the anti-patterns paper_trade:bool, _PAPER_VENUE_KEYS, and the parallel
  TestingStage.LIVE_TESTNET."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [execution, pipeline-mode, uac, live-trading, ssot]
related:
  [
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/paper-vs-live-execution-seam.md,
    /codex/04-architecture/matching-engine-mode-dispatch.md,
    /codex/05-infrastructure/per-venue-paper-policy.md,
  ]
created: 2026-05-09
authoritative_for:
  [
    operational-mode taxonomy,
    OperationalMode enum SSOT,
    ExecutionTarget and ExecutionTrigger axes,
    operational-mode decompose helper,
  ]
referenced_by:
  [
    /codex/04-architecture/manual-trade-booking.md,
    /codex/04-architecture/matching-engine-mode-dispatch.md,
    /codex/04-architecture/multi-mode-wallet-isolation.md,
    /codex/04-architecture/paper-vs-live-execution-seam.md,
    /codex/05-infrastructure/per-venue-paper-policy.md,
    /codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md,
    /codex/14-customer-journeys/dart/mode-toggle.md,
  ]
owner:
last_reviewed: 2026-05-10
code_refs:
overview:
  SSOT for the workspace's operating-mode taxonomy — single canonical `OperationalMode` enum + additive
  `(ExecutionTarget, ExecutionTrigger)` two-axis decomposition + composability with `RuntimeMode`. Resolves drift across
  UAC + execution-service + sports-routing + UI.
type: codex-ssot
locked_by: live-defi-rollout
locked_since: 2026-05-09
spawned_from: plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md
implements_in: plans/active/master_to_live_defi_2026_05_23.md
---

# Operational modes — single SSOT

> **Canonical 2026-05-10.** This doc is the workspace SSOT for the operating-mode taxonomy; consumer-site migration of
> the deleted anti-patterns is owned by `master_to_live_defi_2026_05_23.md` Group F sub-items `pvl-p17a` / `pvl-p17b` /
> `pvl-p17c` / `pvl-p17d`. Plan continues to own the implementation phasing; this doc owns the contract.

## TL;DR

The workspace has ONE operating-mode SSOT:
`unified_api_contracts.internal.modes.OperationalMode { LIVE, MANUAL, BACKTEST, PAPER }`. Everything else (the additive
`ExecutionTarget` / `ExecutionTrigger` enums, the `decompose()` helper, the `paper_target_registry`) is derived from or
composes with this single enum. Anti-patterns (`paper_trade: bool` field in execution-service, `_PAPER_VENUE_KEYS`
string-set in sports routing, parallel `TestingStage.LIVE_TESTNET` enum) are deleted.

## Closed-set 4-cell mode matrix

| Named mode | ExecutionTarget           | ExecutionTrigger | Notes                                                                     |
| ---------- | ------------------------- | ---------------- | ------------------------------------------------------------------------- |
| Backtest   | `simulation` only         | automated        | Historical replay forces simulation — no testnet for past dates.          |
| Paper      | `simulation` OR `testnet` | automated        | Real-time data + simulated/testnet matching. Live data, no real money.    |
| Live       | `live_venue`              | automated        | Real venue + real capital + automated execution.                          |
| Manual     | `live_venue`              | **manual**       | Real trades + real endpoints; only the trigger differs (operator-driven). |

**Strategy / risk / P&L / position-balance / alerting / instructions are identical across all four cells.** The
execution-target axis selects fill source; the trigger axis selects who pulls the trigger. Anything else branching on
these axes is an anti-pattern.

## UAC schema (additive)

```python
# unified_api_contracts/internal/modes.py — additive change, no breaking modifications

class OperationalMode(StrEnum):  # CANONICAL — single SSOT, no rename
    LIVE = "live"
    MANUAL = "manual"
    BACKTEST = "backtest"
    PAPER = "paper"

class ExecutionTarget(StrEnum):  # NEW — derived axis
    SIMULATION = "simulation"
    TESTNET = "testnet"
    LIVE_VENUE = "live_venue"

class ExecutionTrigger(StrEnum):  # NEW — derived axis
    AUTOMATED = "automated"
    MANUAL = "manual"

def decompose(mode: OperationalMode) -> tuple[ExecutionTarget, ExecutionTrigger]:
    """Pure function — single SSOT for the (mode → target, trigger) mapping."""
    return {
        OperationalMode.BACKTEST: (ExecutionTarget.SIMULATION, ExecutionTrigger.AUTOMATED),
        OperationalMode.PAPER:    (ExecutionTarget.SIMULATION, ExecutionTrigger.AUTOMATED),  # default; see paper_target_registry for upgrade
        OperationalMode.LIVE:     (ExecutionTarget.LIVE_VENUE, ExecutionTrigger.AUTOMATED),
        OperationalMode.MANUAL:   (ExecutionTarget.LIVE_VENUE, ExecutionTrigger.MANUAL),
    }[mode]
```

**Routing / recon / UI code uses `decompose(mode)` to switch on `target` or `trigger` independently.** The on-disk +
on-wire surface stays the single `OperationalMode` enum.

## Composability with `RuntimeMode`

`RuntimeMode { LIVE, BATCH }` is service-transport (streaming Pub/Sub vs batch GCS). It composes orthogonally with
`OperationalMode`:

- A `RuntimeMode.LIVE` streaming service can run `OperationalMode.PAPER` against a Tenderly fork (paper-mode against
  real-time data).
- A `RuntimeMode.BATCH` service can run `OperationalMode.BACKTEST` (historical replay).
- A `RuntimeMode.BATCH` service running `OperationalMode.PAPER` is conceptually possible but operationally rare (paper
  mode is real-time by definition; batch transport defeats the purpose).

No consumer should conflate the two enums. They live on different fields.

## `TestingStage` deprecation

`TestingStage { MOCK, HISTORICAL, LIVE_MOCK, LIVE_TESTNET, STAGING, LIVE_REAL }` was a parallel progression-ladder enum
that overlapped with `OperationalMode`. Deprecated 2026-05-09:

- `TestingStage.LIVE_TESTNET` collapses to `(target=TESTNET, trigger=AUTOMATED)` — derived view.
- `TestingStage.LIVE_REAL` collapses to `OperationalMode.LIVE` or `OperationalMode.MANUAL` (depending on trigger).
- Other values (`MOCK`, `HISTORICAL`, `LIVE_MOCK`, `STAGING`) re-expressed via `OperationalMode` + a separate
  `progression_stage` field if still needed (likely UI-only).

## Anti-patterns (deleted)

1. **execution-service `paper_trade: bool` field** (`service_config.py` with alias `PAPER_TRADE | DEFI_PAPER_TRADE`) —
   competing surface to `OperationalMode.PAPER`. **Deleted** by `pvl-p17b`. 4 consumer call-sites migrated.
2. **sports `_PAPER_VENUE_KEYS = ("paper", "betfair", "matchbook")`** in
   `execution-service/execution_service/sports_execution/routing.py:16-25` — string-set rather than enum. **Deleted** by
   `pvl-p17c`. Routing logic migrated to read `OperationalMode.PAPER` directly.
3. **Parallel `TestingStage` enum** — see deprecation above.

## Composes with

- [`batch-live-architecture.md`](batch-live-architecture.md) — batch ⊂ paper ⊂ live in code-path; only fill source
  differs.
- [`paper-vs-live-execution-seam.md`](paper-vs-live-execution-seam.md) — execution layer is the only seam.
- [`/codex/05-infrastructure/per-venue-paper-policy.md`](/codex/05-infrastructure/per-venue-paper-policy.md) — the
  `paper_target_registry` SSOT.
- [`/codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md`](/codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md)
  — per-archetype 4-state taxonomy.
- [`/codex/14-customer-journeys/dart/mode-toggle.md`](/codex/14-customer-journeys/dart/mode-toggle.md) — DART operator
  surface for the modes.
