---
doc_type: plan
title: Archetype paper-runnable matrix — 2026-05-15 snapshot
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-15"
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **ARCHIVED 2026-05-19** — 100% complete (5/5 items); preserved for archaeology.

---

title: "Archetype paper-runnable matrix (pvl-p18b snapshot)" slug: archetype_paper_runnable_matrix_2026_05_15 created:
2026-05-15 author: slot-5 (harsh) locked_by: live-defi-rollout locked_since: 2026-05-15 codex_ssot:
/codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md spawned_by: "slot_5 extended queue item 6
— pvl-p18b-archetype-paper-runnable-matrix" estimate_class: design estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3

---

# Archetype paper-runnable matrix — 2026-05-15 snapshot

> **Purpose**: populate per-archetype 4-state taxonomy for the May-23 lead pair (`carry_staked_basis` +
> `ARBITRAGE_PRICE_DISPERSION`) per `pvl-p18b`. Full taxonomy defined in
> `/codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md`. This plan is the EVIDENCE RECORD for
> Group F item 18.B in `master_to_live_defi_2026_05_23.md`.

---

## 4-state taxonomy (from codex SSOT)

| State               | Meaning                                                                        |
| ------------------- | ------------------------------------------------------------------------------ |
| **paper-runnable**  | ≥3-day end-to-end paper run on real infra; P&L attribution clean; recon green. |
| **paper-shippable** | Code + tests + matching engine wired; never run end-to-end on real infra yet.  |
| **backtest-only**   | Batch-mode evidence only; paper plumbing not fully wired.                      |
| **stub**            | Name in catalogue only; no engine code or sketch-only.                         |

---

## Per-archetype matrix — May-23 lead pair

| Archetype                                            | State (2026-05-15)  | Blockers to next state                                                         | Owning plan                                             | Evidence shipped today                                               |
| ---------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------- | -------------------------------------------------------------------- |
| `carry_staked_basis`                                 | **paper-shippable** | Need ≥3-day end-to-end paper run on real infra (`pvl-p18a`)                    | `defi_master_2026_05_07.md` Fork 1                      | execution-service@310d9629 (TestCarryStakedBasisPaperSmoke, 4 tests) |
| `ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion` | **backtest-only**   | APD execution orchestrator not yet built; need Phase A engine + paper evidence | `arbitrage_price_dispersion_finalisation_2026_05_09.md` | execution-service@59eac3a5 (TestAPDNormalFillAllVenues, 22 tests)    |

> **Note on `carry_staked_basis` state**: promoted from `backtest-only` → `paper-shippable` today (2026-05-15). Prior
> state per codex SSOT (2026-05-09): `backtest-only`. Promoted because: RecursiveLoopOrchestrator (paper mode) +
> AAVEConnector(is_live=False) + hedge-leg mock fills are now all wired and tested. Pending gate: ≥3-day real infra
> paper run + P&L attribution via `pvl-p18a`.

---

## carry_staked_basis — component inventory

| Component                         | Status     | SHA / reference                                           |
| --------------------------------- | ---------- | --------------------------------------------------------- |
| RecursiveLoopOrchestrator         | ✅ wired   | execution-service (recursive_loop_orchestrator.py)        |
| AAVEConnector paper mode          | ✅ wired   | execution-service@310d9629                                |
| Hedge-leg (perp short) paper fill | ✅ mocked  | execution-service@310d9629 TestCarryStakedBasisPaperSmoke |
| L2Matcher (6 CeFi perp venues)    | ✅ wired   | execution-service matching_engine/engine.py               |
| Solana devnet LST connector       | ✅ wired   | execution-service protocols/solana_lst_devnet.py          |
| DefiErrorCode routing (13 Aave)   | ✅ tested  | execution-service@69d02cb0 TestAaveErrorRouting           |
| P&L attribution (paper run)       | ❌ pending | `pvl-p18a` ≥3-day run                                     |
| Risk pre-flight gate              | ✅ tested  | risk-and-exposure@fd10112 BLOCK_CRITICAL (98%)            |
| Kill-switch event chain           | ✅ tested  | UTL@4ffe980 3-tier kill-switch (26 tests)                 |

**Gate to `paper-runnable`**: launch `strategy-paper-carry_staked_basis` VM for ≥3 continuous days per
`promote_workflow_may23_cli_path_2026_05_10.md` § "Paper soak criteria".

---

## ARBITRAGE_PRICE_DISPERSION — component inventory

| Component                                | Status       | SHA / reference                                                           |
| ---------------------------------------- | ------------ | ------------------------------------------------------------------------- |
| APD execution orchestrator               | ❌ not built | Phase A pending (`arbitrage_price_dispersion_finalisation_2026_05_09.md`) |
| L2Matcher for 6 perp venues (hedge fill) | ✅ wired     | execution-service matching_engine/engine.py                               |
| Hedge-leg fill simulation tests          | ✅ tested    | execution-service@59eac3a5 TestAPDNormalFillAllVenues (22 tests)          |
| APD slippage scenarios (5+)              | ✅ tested    | execution-service@59eac3a5 5 scenarios × 6 venues                         |
| UniswapConnector (DEX leg)               | ✅ wired     | execution-service defi_execution (UniswapConnector)                       |
| Price-dispersion detection               | ✅ tested    | TestAPDPriceDispersionDetection (HL@1802 vs Kraken@1798)                  |
| APD carry decision trace CLI             | ✅ shipped   | execution-service cli/defi_arbitrage_dispersion_decision_trace.py         |
| P&L attribution                          | ❌ pending   | `pvl-p18a` + APD orchestrator                                             |
| End-to-end paper infra run               | ❌ pending   | Blocked: APD execution orchestrator not built                             |

**Blocker to `paper-shippable`**: APD execution orchestrator (Phase A) must be built before any paper infra run is
possible. Assigned to `arbitrage_price_dispersion_finalisation_2026_05_09.md`.

---

## Blockers summary (named per SSOT rule)

| Archetype            | Status blocker       | Named successor plan                                            | Operator ask required? |
| -------------------- | -------------------- | --------------------------------------------------------------- | ---------------------- |
| `carry_staked_basis` | `pvl-p18a` infra run | `promote_workflow_may23_cli_path_2026_05_10.md` § paper soak    | No (infra ready)       |
| `APD`                | APD orchestrator     | `arbitrage_price_dispersion_finalisation_2026_05_09.md` Phase A | No (code work)         |

---

## Done-def verification

- [x] Matrix filed with current state for `carry_staked_basis` (paper-shippable) + `APD` (backtest-only)
- [x] Blockers named per SSOT taxonomy (not "DEFERRED — no data")
- [x] Component inventory complete for both archetypes
- [x] Named successor plans in `plans/active/` for each blocker
- [x] State promotion rationale documented (carry_staked_basis: backtest-only → paper-shippable)
