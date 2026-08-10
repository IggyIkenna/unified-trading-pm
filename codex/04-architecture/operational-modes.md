---
doc_type: codex-ssot
title: operational-modes
summary:
  "The workspace SSOT for the operating-mode taxonomy — ONE OperationalMode enum {LIVE, MANUAL, BACKTEST, PAPER} plus
  additive (ExecutionTarget, ExecutionTrigger) axes via a pure decompose() helper; composes orthogonally with
  RuntimeMode. Deletes the anti-pattern paper_trade:bool; the parallel TestingStage.LIVE_TESTNET enum is NOT deleted —
  still live and more entangled than before, see Anti-patterns section; sports _PAPER_VENUE_KEYS relocated to
  adapters/sports_factory.py as a legitimate per-adapter venue-key allowlist (mode dispatch itself already reads
  OperationalMode.PAPER directly)."
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
last_reviewed: 2026-08-09
code_refs:
overview:
  SSOT for the workspace's operating-mode taxonomy — single canonical `OperationalMode` enum + additive
  `(ExecutionTarget, ExecutionTrigger)` two-axis decomposition + composability with `RuntimeMode`. Resolves drift across
  UAC + execution-service + sports-routing + UI.
type: codex-ssot
locked_by: live-defi-rollout
locked_since: 2026-05-09
spawned_from: plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md
implements_in: plans/archive/2026_07/master_to_live_defi_2026_05_23.md
---

# Operational modes — single SSOT

> **Canonical 2026-05-10.** This doc is the workspace SSOT for the operating-mode taxonomy; consumer-site migration of
> the deleted anti-patterns is owned by `master_to_live_defi_2026_05_23.md` Group F sub-items `pvl-p17a` / `pvl-p17b` /
> `pvl-p17c` / `pvl-p17d`. Plan continues to own the implementation phasing; this doc owns the contract.

## TL;DR

The workspace has ONE operating-mode SSOT:
`unified_api_contracts.internal.modes.OperationalMode { LIVE, MANUAL, BACKTEST, PAPER }`. Everything else (the additive
`ExecutionTarget` / `ExecutionTrigger` enums, the `decompose()` helper, `PAPER_EXECUTION_TARGETS`/`get_paper_target()`)
is derived from or composes with this single enum. Anti-pattern `paper_trade: bool` field in execution-service is
deleted; the parallel `TestingStage.LIVE_TESTNET` enum is **NOT deleted** (still live, more entangled than before — see
Anti-patterns section); sports `_PAPER_VENUE_KEYS` was relocated (not deleted) — see item 2 below.

## Closed-set 4-cell mode matrix

| Named mode | ExecutionTarget                   | ExecutionTrigger  | Notes                                                                     |
| ---------- | --------------------------------- | ----------------- | ------------------------------------------------------------------------- |
| Backtest   | `simulation` only                 | `automated`       | Historical replay forces simulation — no testnet for past dates.          |
| Paper      | `simulation` / `testnet` / `fork` | `automated`       | Real-time data, no real money. Per-venue target via `get_paper_target()`. |
| Live       | `mainnet`                         | `automated`       | Real venue + real capital + automated execution.                          |
| Manual     | `mainnet`                         | `manual_operator` | Real trades + real endpoints; only the trigger differs (operator-driven). |

_(Target/trigger values corrected 2026-08-09 to the real enum members — this table previously said `live_venue` and
`manual`, neither of which exists, and omitted `fork` as a paper target.)_

**Strategy / risk / P&L / position-balance / alerting / instructions are identical across all four cells.** The
execution-target axis selects fill source; the trigger axis selects who pulls the trigger. Anything else branching on
these axes is an anti-pattern.

## UAC schema — TRANSCRIBED FROM CODE 2026-08-09 (the previous block was wrong in 4 ways)

> The block below is copied from `unified_api_contracts/internal/modes.py` as it actually stands. The version this doc
> carried from 2026-05-10 until 2026-08-09 named enum members that do not exist and gave `decompose()` a signature it
> has never had — code written against it would not have compiled. Corrections are called out inline.

```python
# unified_api_contracts/internal/modes.py

class OperationalMode(StrEnum):  # CANONICAL — single SSOT, no rename. Unchanged, doc was correct.
    LIVE = "live"
    MANUAL = "manual"
    BACKTEST = "backtest"
    PAPER = "paper"

class ExecutionTarget(StrEnum):
    MAINNET = "mainnet"        # doc previously said LIVE_VENUE — WRONG, no such member
    TESTNET = "testnet"
    FORK = "fork"              # doc previously OMITTED this member entirely
    SIMULATION = "simulation"

class ExecutionTrigger(StrEnum):
    AUTOMATED = "automated"
    MANUAL_OPERATOR = "manual_operator"   # doc previously said MANUAL — WRONG, no such member

def decompose(
    stage: TestingStage,                  # <- takes a TestingStage, NOT an OperationalMode
) -> tuple[OperationalMode, ExecutionTarget, ExecutionTrigger]:   # <- 3-tuple, not 2
    """Decompose a (deprecated) TestingStage into canonical 3-tuple.
    Use this when migrating consumers off TestingStage to the finer-grained enums."""
```

**Correction 4 — what `decompose()` is for.** This doc previously said "Routing / recon / UI code uses `decompose(mode)`
to switch on `target` or `trigger` independently." That is not what the function does. `decompose()` is a **TestingStage
migration shim**: it takes the deprecated `TestingStage` and returns the canonical 3-tuple. There is NO
`OperationalMode → (target, trigger)` helper in UAC. A consumer needing the paper execution target calls
`get_paper_target(chain_or_venue)` (`unified_api_contracts/internal/paper_execution_targets.py`) instead.

The on-disk + on-wire surface does stay the single `OperationalMode` enum — that part was right.

**Registry naming.** This doc and its siblings call the paper-target lookup `paper_target_registry`. **No such symbol
exists in any repo** — the name appears only in PM docs (7 doc hits, 0 code hits, verified 2026-08-09). The real symbols
are `PAPER_EXECUTION_TARGETS` (a `dict[str, ExecutionTarget]`) and the `get_paper_target()` helper, both in
`unified_api_contracts/internal/paper_execution_targets.py`.

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

## Anti-patterns — item 1 deleted, item 2 reclassified as legitimate, item 3 NOT deleted

> **Do not read this section as done.** It previously claimed all three were deleted. Two independent code-verified
> reviews on 2026-08-09 (slot 2 and slot 3, merged here) found: item 1 genuinely deleted, item 2 relocated and correctly
> reclassified as a legitimate lookup, item 3 still live and now MORE entangled. Remaining cleanup:
> `/plans/active/issues/operational_modes_antipatterns_not_actually_deleted_2026_08_09.md`.

1. **execution-service `paper_trade: bool` field** (`service_config.py` with alias `PAPER_TRADE | DEFI_PAPER_TRADE`) —
   competing surface to `OperationalMode.PAPER`. ✅ **DELETED** by `pvl-p17b`, 4 consumer call-sites migrated —
   re-confirmed 2026-08-09: no `paper_trade` remains in `service_config.py`. Note a SEPARATE, still-live
   `paper_trade: bool` constructor arg survives in
   `execution-service/execution_service/defi_execution/protocols/aave_live.py` (~line 122) — a different site this doc
   never claimed, but the same competing-surface smell (tracked as a P3 in the issue above).
2. **sports `_PAPER_VENUE_KEYS = ("paper", "betfair", "matchbook")`** — originally in
   `execution-service/execution_service/sports_execution/routing.py:16-25`, used as a string-set mode check instead of
   the enum. `pvl-p17c` migrated the actual mode dispatch to read `OperationalMode.PAPER` directly (verified still true
   — `create_sports_adapter()` branches on `mode == OperationalMode.PAPER`) and removed the tuple from `routing.py`.
   **Not deleted overall**: `_PAPER_VENUE_KEYS` now lives in
   `execution-service/execution_service/adapters/sports_factory.py:21`, with 5 entries
   (`"paper", "betfair", "matchbook", "kalshi", "polymarket"`, grown from the original 3 as venues were added). Its role
   changed from mode-detection (the anti-pattern) to a per-adapter venue-key allowlist consumed only AFTER the
   `OperationalMode.PAPER` branch is already taken — the set of venue keys the single `PaperBettingAdapter` instance
   registers itself under so any of those venues route to paper. That is a legitimate, permanent lookup, not a parallel
   mode-detection mechanism — reclassified 2026-08-09, not tracked for further deletion.
   (`plans/archive/issues/operational_modes_paper_venue_keys_anti_pattern_not_deleted_2026_08_09.md`, resolved
   2026-08-09.) _(A same-day parallel review initially read the surviving tuple as "the migration never happened". It
   did happen; the tuple's ROLE changed. Recorded because a grep for the symbol alone cannot distinguish the two, and
   the wrong reading is the intuitive one.)_
3. **Parallel `TestingStage` enum** — ❌ **NOT deleted, and now more entangled, not less.** `TestingStage` is still a
   live `StrEnum` in `unified_api_contracts/internal/modes.py` (~line 181) with `LIVE_TESTNET` intact (~line 197), and
   `decompose()` itself now maps `TestingStage.LIVE_TESTNET → (PAPER, TESTNET, AUTOMATED)` (~line 245). So the "parallel
   ladder" the deprecation note above says was removed has instead been wired INTO the canonical helper. Whether that is
   a deliberate reversal or an unfinished migration is the open question in the tracking issue — the deprecation note is
   the only record of intent, and it is 3 months stale.

## Composes with

- [`batch-live-architecture.md`](batch-live-architecture.md) — batch ⊂ paper ⊂ live in code-path; only fill source
  differs.
- [`paper-vs-live-execution-seam.md`](paper-vs-live-execution-seam.md) — execution layer is the only seam.
- [`/codex/05-infrastructure/per-venue-paper-policy.md`](/codex/05-infrastructure/per-venue-paper-policy.md) — the
  `PAPER_EXECUTION_TARGETS` / `get_paper_target()` SSOT.
- [`/codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md`](/codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md)
  — per-archetype 4-state taxonomy.
- [`/codex/14-customer-journeys/dart/mode-toggle.md`](/codex/14-customer-journeys/dart/mode-toggle.md) — DART operator
  surface for the modes.
