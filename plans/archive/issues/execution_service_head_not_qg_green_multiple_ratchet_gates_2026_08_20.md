---
doc_type: issue
title: >-
  execution-service `live-defi-rollout` HEAD (fb50f7296) fails multiple pre-existing hard QG gates — broad-except
  baseline (deribit.py, fixed in this session) and function-size cap (bridge.py/cctp.py, unfixed — out of scope) —
  blocking the two-pass quickmerge sentinel for EVERY agent, not just this session
summary: >-
  While trying to ship a completed, tested change to `execution_service/api/external_instruction_api.py` (wiring
  TRANSFER/CANCEL — see the sibling issue docs for that work), `bash scripts/quality-gates.sh --no-fix` could not
  produce a clean, sentinel-writing run despite the shipped code itself being fully green (all new/existing tests
  passing). Root cause is NOT this session's change — it is TWO separate pre-existing hard-gate violations already
  on `origin/live-defi-rollout` HEAD:

  1. **STEP 5.5 broad-except baseline** (`execution_service/venues/deribit.py:176`): a real `except Exception as e:`
     site pushed the repo's count to 161 against a tracked baseline of 160
     (`unified-trading-pm/scripts/quality_gates/broad_except_baseline.yaml`). Confirmed on `origin` via
     `git merge-base --is-ancestor dd9e75d04 origin/live-defi-rollout` (introduced by
     `dd9e75d04 "fix: load Deribit tick_size from IS InstrumentRecord at startup..."`). The site is a genuinely
     intentional best-effort startup-cache loader (parquet I/O + per-row processing, degrading to a live-API
     fallback on ANY failure) — exactly the case the checker's own guidance describes ("For a genuinely-intentional
     broad catch... add `# noqa: broad-except` on the except line with a one-line reason"). **Fixed in this
     session** (execution-service, uncommitted at time of filing — see the companion TRANSFER/CANCEL change for
     shipping status) by adding that sanctioned noqa comment; this did not touch business logic and carries
     negligible risk, so it was treated as an in-scope "small+clear ≤30min" finding per the findings-triage rule
     rather than filed as a pure blocker.

  2. **Function/class/method size cap** (NOT prefixed "STEP" in the gate output — a separate hard gate): THREE
     methods on `origin/live-defi-rollout` HEAD (commit `fb50f7296`, the literal branch tip at time of writing —
     "fix(defi): persist bridge transfer security state") exceed the 50-line method cap:
     `execution_service/defi_execution/protocols/bridge.py:356 SocketBridgeConnector.bridge()` (85L),
     `execution_service/defi_execution/protocols/bridge.py:560 SocketBridgeConnector._execute_bridge_tx()` (59L),
     `execution_service/defi_execution/protocols/cctp.py:236 CCTPBridgeConnector.bridge()` (79L). **NOT fixed in
     this session** — deliberately left alone: these are security-sensitive, real-fund-movement bridge-execution
     methods with zero prior context available to this session, under heavy, very recent, active churn (5+
     "fix(bridge):"/"refactor(bridge):" commits landed within the hour preceding this discovery, per `git log`).
     Splitting them safely requires real understanding of the bridge security-state/tx-execution flow — genuine
     refactoring work, not a mechanical fix, and carries real risk of a fund-safety regression if done carelessly
     by someone unfamiliar with the code. Left for whoever owns that domain.

  **Practical impact**: `scripts/quickmerge.sh --agent`'s Pass-1 sentinel (`.qg_last_passed_sha`) can only be
  written by a fully green `quality-gates.sh` run. With gate #2 unfixed, NO agent — this session or any other —
  can currently produce that sentinel for execution-service, meaning the two-pass ship mechanism is structurally
  blocked for the whole repo until gate #2 is resolved (fix the 3 methods, or a sanctioned baseline/cap exemption
  if one exists for this gate — not verified in this session).

  **Separately observed** (worth the operator's awareness, not itself a QG blocker): during this investigation a
  SECOND live Claude Code session (distinct `--resume=` id from this one, confirmed via `ps aux`) was found
  actively editing `execution_service/engine/routing/instruction_router.py`,
  `execution_service/engine/handlers/transfer_handler.py`, `scripts/capture_golden_swaps.py`, and
  `scripts/validate_uniswap_fills.py` in this SAME slot-6 `execution-service` checkout, concurrently with this
  session's work -- the documented "two operators/sessions sharing ONE slot's checkout" failure mode
  (`/codex/05-infrastructure/per-tab-worktrees.md`). Their `instruction_router.py`/`transfer_handler.py` edits were
  read (not touched, not staged, not committed by this session) and appear to independently, correctly fix the
  exact TRANSFER/CeFi venue_category registry gap this session's own investigation found and documented in
  `external_instruction_transfer_cefi_venue_category_registry_gap_2026_08_20.md` -- worth reconciling directly with
  that session/operator rather than both efforts landing independently.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-trading-pm]
scope: [engineer]
tags: [execution-service, quality-gates, broad-except, function-size-cap, bridge, quickmerge, sentinel, shared-checkout-collision]
related:
  [
    /plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md,
    /plans/archive/issues/external_instruction_transfer_cefi_venue_category_registry_gap_2026_08_20.md,
    /plans/archive/issues/external_instruction_defi_handlers_simulation_only_2026_08_20.md,
    /plans/active/issues/external_instruction_bridge_atomic_not_wired_2026_08_20.md,
  ]
created: 2026-08-20
source: >-
  Sub-agent dispatch wiring TRANSFER/CANCEL onto external_instruction_api.py (2026-08-20) -- discovered while
  attempting the mandated `bash scripts/quality-gates.sh --no-fix` pre-ship gate, 5 consecutive real (non-cached)
  full-suite runs, root-caused via git blame/merge-base against origin, not guessed.
author: agent
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
resolved_by: >-
  Independently resolved by the domain owner mid-session, per operator authorization ("just fix the pre-existing
  issues, that's fine"): `execution-service@8b87a17a5` split all 3 flagged methods under the 50-line cap
  (`3f54ca206` trimmed `bridge()` further), landing on `origin/live-defi-rollout` within the hour. This session's
  own earlier stopgap refactor of the same 3 methods (done directly, before the domain owner's fix landed, also
  under operator authorization) was superseded and discarded via `git checkout HEAD -- <file>` during
  reconciliation rather than kept — the domain owner's version is authoritative. A fresh
  `bash scripts/quality-gates.sh --no-fix` run on the reconciled tree wrote `.qg_last_passed_sha` cleanly
  (8841 passed), confirming the ship mechanism is unblocked; `execution-service@3af76e1a01` (the TRANSFER/CANCEL
  work this issue was blocking) shipped immediately after, verified ancestor of origin.
locked_by:
locked_since:
context_scope:
  [
    execution-service/execution_service/defi_execution/protocols/bridge.py,
    execution-service/execution_service/defi_execution/protocols/cctp.py,
    execution-service/execution_service/venues/deribit.py,
    unified-trading-pm/scripts/quality_gates/broad_except_baseline.yaml,
  ]
drift_direction: advance-code
---

# execution-service HEAD fails hard QG gates -- the two-pass ship mechanism is currently blocked repo-wide

> **RESOLVED + ARCHIVED 2026-08-20.** Domain owner split the 3 flagged bridge.py/cctp.py methods under the
> 50-line cap (`execution-service@8b87a17a5`+`3f54ca206`); ship mechanism confirmed unblocked (fresh
> `quality-gates.sh` wrote `.qg_last_passed_sha` cleanly, 8841 passed); the TRANSFER/CANCEL work this issue was
> blocking shipped immediately after (`execution-service@3af76e1a01`). See `resolved_by` frontmatter for the
> full record.

## Why P0

Every future `quickmerge.sh --agent` ship attempt for execution-service needs a real, fully-green
`quality-gates.sh` run to write the Pass-1 sentinel. Gate #2 (function-size cap on `bridge.py`/`cctp.py`) is
unresolved and already on HEAD -- this is not a "my change caused it" problem, it blocks EVERYONE shipping to this
repo until fixed. Flagging P0 for visibility even though the fix itself is bounded (3 methods, one file's worth of
refactoring).

## What's already resolved

`execution_service/venues/deribit.py:176`'s broad-except-baseline overage -- fixed via a sanctioned `# noqa:
broad-except` comment (checker's own suggested remedy for an intentional best-effort catch), zero business-logic
change. See the companion TRANSFER/CANCEL change for exact commit status.

## What's NOT resolved (needs a bridge/CCTP domain owner)

- `execution_service/defi_execution/protocols/bridge.py:356 SocketBridgeConnector.bridge()` -- 85 lines, cap 50.
- `execution_service/defi_execution/protocols/bridge.py:560 SocketBridgeConnector._execute_bridge_tx()` -- 59 lines, cap 50.
- `execution_service/defi_execution/protocols/cctp.py:236 CCTPBridgeConnector.bridge()` -- 79 lines, cap 50.

All three need extracting helper methods (validation, tx-construction, submission, confirmation-polling -- whatever
the actual internal seams are) to get under the 50-line cap, without changing behavior in a fund-movement path.
Given the very recent, active churn on these exact files (5+ bridge-related commits in the hour preceding this
finding), coordinate with whoever is currently working that area before touching them.

## Follow-ups

- [x] ✅ [BACKEND] P0. Split `SocketBridgeConnector.bridge()`, `SocketBridgeConnector._execute_bridge_tx()`, and
      `CCTPBridgeConnector.bridge()` under the 50-line method cap — done by the domain owner,
      `execution-service@8b87a17a5`+`3f54ca206`. See `resolved_by` above.
- [x] ✅ [AGENT] P1. Verified a fresh `bash scripts/quality-gates.sh` run on execution-service writes
      `.qg_last_passed_sha` cleanly — `32ad0cfa4a2b5bf469d816008919ce855295b4f9` (8841 passed, 0 failed). Ship
      mechanism confirmed unblocked; `execution-service@3af76e1a01` shipped immediately after.
