---
doc_type: issue
title:
  l2_book_microstructure_capture item 3's target file (book_microstructure_compute.py) was retired 6 days before this
  plan was authored -- prerequisite todos 1+2 also unstarted
summary: |
  Dispatched todo 3 of l2_book_microstructure_capture_2026_07_13.md ("extend
  market-tick-data-service/.../derived/book_microstructure_compute.py to populate queue_position_bid/ask +
  book_depth_levels from the deeper book input when present") cannot proceed as scoped: (1) the file + its whole
  feature were DELETED on 2026-07-07 (commit a4fb3d13, also on main via 917a8ccf) when order_flow_imbalance was
  retired for "zero real consumers, zero production rows ever captured; duplicated MDPS's live implementation" --
  one week before this plan was created on 2026-07-13; (2) prerequisite todos 1 (per-venue deeper-book capability
  research) and 2 (extend live capture to pull deeper book) are genuinely unstarted -- zero references to
  L10/L20/full-L2/depth_of_book_10/deeper-book anywhere in market-tick-data-service today, confirmed by grep.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [data, features]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by: "slot-10, plan frontmatter fix -- see Resolution section"
locked_by:
source: [plans/active/l2_book_microstructure_capture_2026_07_13.md todo 3, slot-5 session 2026-07-13]
related: [plans/active/l2_book_microstructure_capture_2026_07_13.md]
tags: [strategy, market-making, orderbook, microstructure, plan-codebase-drift, retired-feature]
depends_on: []
---

# l2_book_microstructure_capture item 3 — target file retired before this plan was written

## What I found

Dispatched `l2_book_microstructure_capture-003` — todo 3 of
[`l2_book_microstructure_capture_2026_07_13.md`](../l2_book_microstructure_capture_2026_07_13.md): "Extend
`market-tick-data-service/.../derived/book_microstructure_compute.py` (`compute_book_microstructure`) to populate
`queue_position_bid`/`queue_position_ask`/`book_depth_levels` from the deeper book input when present."

Two independent blockers, verified via git history + full-repo grep (not assumed):

1. **The target file no longer exists.** `derived/book_microstructure_compute.py` (plus its handler, CLI wiring, and
   tests) was deleted entirely in market-tick-data-service commit `a4fb3d13` ("retire order_flow_imbalance feature (zero
   real consumers, zero production rows ever captured; duplicated MDPS's live implementation)"), also present on `main`
   via promote commit `917a8ccf`. This landed **2026-07-07 — six days before** this plan was authored
   (`created: 2026-07-13`). Only a stale `.pyc` remains in `__pycache__`. Deleted in that commit:
   `derived/book_microstructure_compute.py`, `derived/__init__.py` (partial),
   `cli/handlers/book_microstructure_handler.py`, `scripts/book_microstructure_connectivity_check.py`, and both
   corresponding test files.

2. **Even in its last-known state (retrieved via `git show a4fb3d13^:...`), the file never had a deeper-book code
   path.** It consumed a source-agnostic `L5BookInput` dataclass capped at `_L5_DEPTH = 5` and always emitted
   `depth_levels_bid=[]` / `depth_levels_ask=[]` / `queue_position_bid=None` / `queue_position_ask=None` with an
   explicit comment: "Deeper-book fields are honestly absent on an L5 source — never synthesised." So "extending" it per
   this plan's todo 3 was never a small addition even before it was deleted — it required a new input shape from
   scratch.

3. **Prerequisite todos 1 + 2 are genuinely unstarted, not just unchecked.** Grepped the entire market-tick-data-service
   repo for `L10|L20|full_l2|fullL2|depth_of_book_10|order_book_depth|deeper_book|book_snapshot_10|book_snapshot_20` —
   zero matches anywhere (no handler, connector, stub, TODO, or test). Every one of the 9 CeFi venues' live connectors
   (`live/connectors/binance_futures_book_ticker_ws.py` and its OKX/Bybit/Deribit/Coinbase/Upbit siblings) subscribes to
   a hardcoded 5-level depth stream (e.g. Binance's `depth5@100ms`).
   `unified_api_contracts.registry.data_type_capability` confirms `queue_position` + `depth_of_book_10` are
   `live_capable=False, batch_capable=False` for all 9 venues today, matching the plan's own stated ground truth — the
   checkboxes are accurate, nothing has been built yet.

## Why it matters

This plan's premise is that todo 3 is a mechanical "extend an existing file" step gated only on todos 1+2 landing first.
In reality the file doesn't exist, and rebuilding it means re-creating functionality that was deliberately retired 6
days earlier with a stated rationale (zero consumers, zero production rows, duplicated another service's implementation)
— the same failure mode this new plan risks repeating unless the deeper-book capture actually gets a real consumer this
time (`MarketMakingQueueMicrostructureEngine`, per the plan's own framing). It's plausible the plan author wasn't aware
of the 2026-07-07 retirement when authoring this on 2026-07-13 (6 days later) — worth confirming before any
implementation work resumes building on a foundation that was just torn out for being unused.

## Recommended decision

Two independent questions:

1. **Sequencing**: todo 3 cannot proceed until todos 1 (per-venue capability research) and 2 (live capture extension)
   actually land — should this be re-authored with `depends_on`/`gate_on_depends` (or `sequential: true`) so the
   dispatcher doesn't hand out todo 3 before its inputs exist? Currently `sequential: false` with no intra-plan
   ordering, so any worker could hit the same block I did.
2. **Premise check**: given `book_microstructure_compute.py` was retired for zero real consumers 6 days before this plan
   was written, should whoever picks up todo 1 (or before starting ANY implementation) explicitly re-confirm
   `MarketMakingQueueMicrostructureEngine` is a real, live-registered consumer that will actually use this data once
   built (the plan's own header claims it "already consumes `queue_position_bid`/`queue_position_ask` and degrades
   honestly when absent" — worth a quick verify given the sibling feature's retirement rationale was exactly "nobody
   consumes this").

## Resolution (2026-07-13, slot-10)

Both questions resolved directly (no operator escalation needed — mechanical fix + a verifiable code fact, not a
judgment call):

1. **Sequencing — fixed.** Flipped `l2_book_microstructure_capture_2026_07_13.md` frontmatter `sequential: false` →
   `true`. Confirmed via `agent-orchestrator/server/regen_backlog_from_plan.py` (`_wire_sequential_prereqs`) that
   `sequential: true` is exactly the declared mechanism for chaining each task's `completed_tasks` to its predecessor
   within one plan — `depends_on` does NOT affect dispatch (CLAUDE.md: "documents task ordering + gates archival (does
   NOT affect dispatch)"), so `sequential: true` was the correct lever, not `depends_on`. Also corrected todo 3's
   premise in-place: relabeled "Extend" → "**RE-CREATE**" with a pointer to the deleted file's last state
   (`git show a4fb3d13^:...`) so the next worker doesn't rediscover this same blocker.
2. **Premise check — verified, no change needed.** Read `strategy-service/.../market_making/queue_microstructure.py`
   directly: `MarketMakingQueueMicrostructureEngine` DOES exist, DOES read `queue_position_bid`/`queue_position_ask`
   from the features dict, and DOES degrade honestly (returns `[]`, no quote) when they're `None` — the plan's technical
   claim holds. It is explicitly NOT registered in `ARCHETYPE_ENGINE_REGISTRY` today (docstring: "no passing backtest
   AND the queue feed is absent") — but unlike the retired sibling feature, this ISN'T an oversight: the plan's own todo
   7 already explicitly defers registration to the parent plan's Phase E1, gated on this data landing AND a passing
   `GroupBRunner` backtest. So the "zero real consumers" retirement pattern does NOT apply here — there IS a real,
   code-written, unit-tested consumer with an explicit (if future-gated) registration path, not an unreferenced dead
   end.

## Todos

- [x] ✅ [SPEC] P2. Decide whether `l2_book_microstructure_capture_2026_07_13.md` needs `depends_on`/`sequential: true`
      so todo 3 isn't dispatched before todos 1+2 land; re-verify `MarketMakingQueueMicrostructureEngine` is a real live
      consumer before committing to rebuilding the retired `book_microstructure_compute.py` surface. (repo:
      unified-trading-pm — plan authoring) — RESOLVED: `sequential: true` set + todo 3 premise corrected
      (`unified-trading-pm@<pending>`); engine-consumer claim verified true, no plan change needed. See Resolution
      section above.
