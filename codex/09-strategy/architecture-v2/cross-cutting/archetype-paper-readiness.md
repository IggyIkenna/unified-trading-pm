---
name: archetype-paper-readiness
overview:
  Per-archetype 4-state taxonomy (paper-runnable / paper-shippable / backtest-only / stub) for every entry in
  the canonical strategy archetype catalogue (UAC `StrategyArchetype` enum = 55 archetypes; full coverage
  matrix at `codex/09-strategy/architecture-v2/category-instrument-coverage.md`). Pins the closed-set gate set
  every strategy archetype must clear before being eligible for `OperationalMode.PAPER`.
type: codex-ssot
status: stub
created: 2026-05-09
last_verified: 2026-05-12
locked_by: live-defi-rollout
locked_since: 2026-05-09
spawned_from: plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md
implements_in: plans/active/master_to_live_defi_2026_05_23.md # Group F items 18.A / 18.B
---

# Archetype paper-mode readiness

> **Stub doc.** Full content fills in as `master_to_live_defi_2026_05_23.md` Group F sub-items `pvl-p18a` / `pvl-p18b`
> ship.

> **Source file note (corrected 2026-05-12 per `codex_audit_strategy_2026_05_12.md` ST-4)**: the 4-state taxonomy is
> for **strategy archetypes** per UAC `StrategyArchetype` (55 members) — the same set documented in
> `codex/09-strategy/architecture-v2/README.md` "55 Archetypes" + the matrix in `category-instrument-coverage.md`. It
> is NOT a taxonomy of `strategy_service/portfolio_allocator/archetypes.py`, which holds the 8
> **PortfolioAllocator archetype engines** (risk-parity / factor / tactical-overlay / multi-strategy / etc.) — those
> are allocator engines, a different concept. An earlier version of this doc pointed at the allocator file by mistake.

## 4-state taxonomy

Every archetype lands in exactly one of four states for `OperationalMode.PAPER` readiness:

| State                  | Meaning                                                                                                                                                        |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **paper-runnable**     | Has run paper-mode end-to-end against real venues + real data, P&L attribution clean, recon green. **The only state that counts as ready for live promotion.** |
| **paper-shippable**    | Code exists + tests exist + matching engine wired; never executed paper end-to-end on real infra. Plumbing ready; evidence pending.                            |
| **backtest-only**      | Only batch-mode evidence exists; paper plumbing not wired. Most archetypes today.                                                                              |
| **stub / placeholder** | Archetype name exists in catalogue but no engine code, or engine code is sketch-only. Not eligible for paper-mode.                                             |

## Paper-runnable gate set (closed set)

An archetype graduates from `paper-shippable` → `paper-runnable` only when ALL of the following are met:

1. **End-to-end run completed** for ≥3 continuous days against real venues + real data + matching engine (or testnet per
   `paper_target_registry`).
2. **Event stream verified** per CLAUDE.md "no fire-and-forget VM launches" rule — STARTED / per-instrument progress /
   STOPPED with non-empty metadata.
3. **P&L attribution decomposed** by source (strategy alpha vs execution alpha vs financing) per
   `09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`.
4. **Recon green** for paper-vs-live (where live coverage exists) and batch-vs-paper for the run window per
   `pvl-p21a-three-way-recon`.
5. **Lookahead-bias clean** — `LookaheadBiasError` not raised over the run window; `available_at` semantics correct per
   `02-data/availability-manifest-and-data-status.md`.
6. **Risk + alerting wired** — risk-and-exposure pre-flight checks fired correctly; alerting-service rules consumed the
   mode-tagged events per `pvl-p22a`.
7. **Position-balance reconciled** — PBM dual projection matches actual venue/chain state after each fill.

Archetypes that fail ANY gate stay in `paper-shippable` until the gap closes.

## Per-archetype matrix (TBD — populated by `pvl-p18b`)

The full matrix populates as `master_to_live_defi_2026_05_23.md` `pvl-p18b` ships. Initial state for May-23 lead pair:

| Archetype                                            | State (initial 2026-05-09) | Owning plan                                             | Paper-mode evidence run                              |
| ---------------------------------------------------- | -------------------------- | ------------------------------------------------------- | ---------------------------------------------------- |
| `carry_staked_basis`                                 | backtest-only              | `defi_master_2026_05_07.md` Fork 1                      | `pvl-p18a` ≥3-day run pre-cutover                    |
| `ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion` | stub (Phase A pending)     | `arbitrage_price_dispersion_finalisation_2026_05_09.md` | `pvl-p18a` ≥3-day run pre-cutover (pairs with above) |
| Other archetypes in `archetypes.py`                  | TBD                        | various                                                 | post-cutover                                         |

## Solana-specific addendum

`carry_staked_basis` has Solana legs (jitoSOL / mSOL / bSOL); per
[`../../../05-infrastructure/per-venue-paper-policy.md`](../../../05-infrastructure/per-venue-paper-policy.md), Solana
paper-mode uses devnet (or localnet / surfnet) — picked by `pvl-p20c`. `carry_staked_basis` graduating to
`paper-runnable` requires the Solana paper wiring to ship.

## Composes with

- [`../../../04-architecture/operational-modes.md`](../../../04-architecture/operational-modes.md) — the canonical mode
  SSOT.
- [`../../../04-architecture/paper-vs-live-execution-seam.md`](../../../04-architecture/paper-vs-live-execution-seam.md)
  — execution-only seam principle.
- [`../../../05-infrastructure/per-venue-paper-policy.md`](../../../05-infrastructure/per-venue-paper-policy.md) —
  `paper_target_registry`.
- [`pnl-attribution.md`](pnl-attribution.md) — P&L decomposition per source.
- [`../../../14-customer-journeys/dart/mode-toggle.md`](../../../14-customer-journeys/dart/mode-toggle.md) — DART
  visualization of paper-runnable archetypes.
