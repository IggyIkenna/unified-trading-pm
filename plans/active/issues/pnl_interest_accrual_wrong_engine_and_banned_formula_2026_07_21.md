---
doc_type: issue
title: >-
  DeFi interest PnL: the operator-named engine (compute_pnl) is dead code, and the engine clients actually read (the
  determinism spine) uses the codex-BANNED APY/365 accrual instead of the on-chain index-ratio form
summary: >-
  Operator directed (2026-07-21) "finish compute_pnl using the real formal rate indices for sample-to-sample PnL." A
  deep read found the brief points at the wrong file. strategy-service has THREE PnL surfaces: (A) compute_pnl
  (orchestrator.py) — dead code, zero prod callers, writes a reader-less sink, has the RIGHT index-ratio formula but
  wrong keying/schema/sink and a broken interest matcher; (B) the execution-alpha compute_handler — a third orphan
  surface, also zero readers; (C) the determinism-spine producers paper_run_passive.py + paper_run_attribution.py — the
  WIRED, client-facing engine called by BOTH paper and batch legs, writing the client-reports bucket the reporting UI
  renders. Only (C) reaches consumers, and (C) computes interest as notional*apy_bps/10000/365 — the exact pattern codex
  Hard Rule #4 lists as REVIEW-BLOCKING BANNED. So the operator's real intent (index-exact interest PnL in prod) is
  served by fixing the accrual IN THE SPINE, not by wiring compute_pnl (which would be inert AND create a second
  divergent interest model — the determinism-spine G1 failure). This is a money-path change to client NAV numbers and an
  SSOT contradiction, so it is operator-gated before ship.
status: open
nature: issue
asset_group: [defi]
stage: [strategy]
repos: [strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: [pnl-correctness, interest-accrual, determinism-spine, ssot-contradiction, money-path, defi, operator-gate]
related:
  [
    features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md,
    silent_wrong_answer_audit_candidates_2026_07_20.md,
  ]
created: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend
drift_direction: advance-code
depends_on: []
source:
  [
    "7-lens understanding sweep 2026-07-21 after operator directed finishing compute_pnl; the sweep found compute_pnl is
    dead code and the consumed engine (spine) carries a codex-banned accrual",
  ]
resolved_by:
locked_by:
---

# DeFi interest PnL — wrong engine named, and the real one uses a banned formula

## The three PnL surfaces (only one reaches clients)

| surface | code                                                                                    | consumers                                                                 | interest formula                                               |
| ------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------- |
| A       | `pnl/engine/orchestrator.py::compute_pnl` → `pnl-attribution-output/` (portfolio-state) | **ZERO** (grep-verified: writers/tests/docs only)                         | **correct** index-ratio, but broken keying/matcher/schema/sink |
| B       | `pnl/cli/handlers/compute_handler.py` execution-alpha → `pnl-attribution-output/`       | **ZERO**                                                                  | none (fill-vs-VWAP only; skips hold days)                      |
| C       | `engine/backtest/paper_run_passive.py` + `paper_run_attribution.py`                     | **client-reports bucket → client-reporting-api → reporting UI waterfall** | **`notional*apy_bps/10000/365` — codex-BANNED (Hard Rule #4)** |

Surface C is called by BOTH `cli/handlers/paper_run_handler.py` (paper) and `cli/handlers/batch_rerun.py:75-77,410-425`
(batch) with the same `carry_rates_by_day` feed, so paper==batch is structural. It emits canonical `PassiveLedger`
interest rows (→ NAV) and canonical UAC `PnLAttributionRow` (factor×layer) into the client-reports bucket.

## What the operator actually wants, and where it must land

The directive — "real formal form rate indices for sample-to-sample pnl" — means replace the APY/365 approximation with
the on-chain cumulative-index ratio (codex Hard Rule #4, `pnl-attribution.md:82-113`):

```
supply_yield = aToken_notional × (aave_liquidity_index_now / aave_liquidity_index_prev − 1)
borrow_cost  = debt_notional  × (aave_borrow_index_now  / aave_borrow_index_prev  − 1)   # booked NEGATIVE
```

Both indices are RAY-normalized (÷1e27 at the MTDS producer) cumulative growth factors, present in the `lending_rates`
feature group (`aave_liquidity_index` AND `aave_borrow_index`), keyed `AAVE_V3-<CHAIN>:LENDING:<ASSET>`. **Data supports
it today.** `compute_pnl` and `engine/core/settlement_service.py:245-291` already implement this ratio form correctly —
they are the reference for the math. The fix lands in the **spine producers**, not by wiring either.

## Why NOT wire compute_pnl (the literal brief)

- Its sink has zero readers → correct-but-inert.
- It reads inputs live from GCS with NO RunManifest pinning (a backward 7-day fill scan + a "current view" lending_rates
  read), so a re-materialized partition or a late-backfilled fill silently changes its interest number — an un-pinned
  second model diverging from the spine (the **G1 divergent-model failure** the determinism spine forbids).
- It carries 4 latent bugs (id-form matcher can never match `:A_TOKEN:AUSDC` vs `:LENDING:USDC`; debt computed by
  negating the supply index instead of using `aave_borrow_index`; `iloc[0]/iloc[-1]` order-dependent prev/now selection
  over ~3×-duplicated rows; `asset_group` vs `asset_class` kwarg silently dropped).

Running both the spine APY accrual AND a compute_pnl index accrual for the same position is the divergent-model failure.
Pick ONE engine.

## OPERATOR GATE (why this is not auto-shipped)

This changes **client-facing interest PnL numbers and NAV** (APY-approx → index-exact). The operator's named file was
wrong, and this is an SSOT contradiction — both per findings-triage require a notify + this doc, and per the money-path
rule I will not silently change every client's reported interest. **Structured options:**

- **A — fix the accrual IN THE SPINE producers (`paper_run_passive`/`paper_run_attribution`) [WORKER RECOMMENDATION].**
  Only path with consumers; preserves batch=live by construction; no schema/contract change (still `PnLAttributionRow`,
  factor=`CARRY`/`BASIS`/`FUNDING`); lands the directive where clients read it. Deletes/leaves A+B as dead code
  (separate call).
- **B — finish + wire compute_pnl into compute_handler and re-home its output to client-reports.** More work; fixes the
  4 latent bugs; but risks two divergent interest models and needs RunManifest pinning to be deterministic.
- **C — both engines, one designated SSOT, the other deleted.**

Plus a secondary (non-blocking): leave the `aave_rate_impact` overlay as honest-absence (rec — it's a
featureless/unproduced shard + a `rate_impact` vs `aave_rate_impact` name mismatch) vs unblock that vocabulary migration
now.

## Build-ready spec for option A (so a yes ships fast)

Smallest safe increment, one repo (strategy-service), refactor-class, in the shared producer ONLY:

1. Add an index-ratio accrual helper `amount = notional × (index_now/index_prev − 1)` (guard `index_prev > 0`).
2. Extend `paper_run_handler._carry_rates_for_day` (`paper_run_handler.py:226-244`) from a frame-mean `apy_bps` to a
   **per-reserve, per-day prev/now index pair** — `(aave_liquidity_index_prev, _now)` for supply/staked and
   `(aave_borrow_index_prev, _now)` for debt — resolved per reserve id, selected by **MIN/MAX timestamp** after
   sort+dedup (NOT `iloc`; ~3× duplicate rows per (id,timestamp)), from the **immutable day= partition** (determinism).
3. Replace ONLY the `/365` term in `build_paper_run_passive` (`paper_run_passive.py:108-109`) and the matching per-day
   accrual in `emit_paper_run_attribution` with the ratio form. Keep the EXACT same `PassiveLedger LedgerRow` +
   `PnLAttributionRow` output shape, keying, and factor set.
4. Debt uses `aave_borrow_index` (grows faster than supply on 92/109 reserves; negating the supply index understates
   debt cost).
5. **Determinism proof**: the ε=0 fill proof is TradeFillRecord-only and EXCLUDES passive/interest rows, so green
   determinism tests do NOT prove interest correctness — ADD a passive-row parity check on a fixture window (paper vs
   batch-rerun re-derive identical passive rows), and a golden-value test of the ratio math.
6. Do NOT touch `compute_handler`, `compute_pnl`, or the reader-less Surface-A sink in this increment.

## REFINEMENT after the build (2026-07-21) — option A has a leg-mapping sub-decision

The build correctly BLOCKED rather than wire the brief, and a deeper read (verified) found the spine's interest is a
**3-leg construct that does not map to the 2-index (supply/debt) model** the brief assumed:

- `LENDING_INTEREST` — a genuine Aave lending accrual. The index-ratio form applies cleanly here (codex Hard Rule #4).
- `STAKING_REWARD` — should use the **LST exchange-rate index** (`lst_rates` corpus, Hard Rule #5), NOT the Aave
  liquidity index. Different data source; a separate fix.
- `FUNDING_ACCRUAL` — perp funding, quoted as a rate (not a cumulative index) — leave on the rate form.
- `carry_staked_basis` has **no debt position** (stake-long + perp-short), so there is no `debt_notional` to apply the
  borrow-index term to. The borrow index is only relevant when a strategy actually borrows.

**Data precondition RESOLVED (verified against GCS, which the build agent could not):** `aave_liquidity_index` and
`aave_borrow_index` are 100% populated in `lending_rates`, RAY-normalized (supply 1.0→1.22, borrow 1.0→5.45), with the
expected ~3× duplicate-row noise the sort+dedup+min/max design already handles. So the "hold until data confirmed"
concern is cleared — the data is there.

**Shipped-as-prepared (unwired, correct, held):** `strategy_service/engine/backtest/index_ratio_accrual.py` — the pure
`index_ratio_accrual(notional, prev, now) = notional*(now/prev−1)` helper (guard prev>0, honest-absence→0), plus golden
math tests (10 pass, matches the `orchestrator.py`/`settlement_service.py` reference). Held (not shipped orphaned) until
the leg-mapping is confirmed, then wired.

### Leg-mapping decision (money-path, needs a ruling)

- **A1 — LENDING leg only [recommended].** Wire ONLY `LENDING_INTEREST` to the Aave index-ratio form; leave
  `STAKING_REWARD` (needs the LST index — file as follow-up), `FUNDING_ACCRUAL`, and all non-carry-staked-basis
  archetypes on their current form. Minimal, faithful, no invented debt leg, no staking mislabel. But: confirm the
  LENDING leg's economic basis in `carry_staked_basis` (supply-only yield vs net supply−borrow) and which reserve drives
  it — a strategy-semantics question that sets the number.
- **A2 — LENDING + STAKING now.** Also fix the staking leg via the LST exchange-rate index (`lst_rates`) in the same
  change. More correct-in-full, more work (new data source), larger NAV delta.
- **Hold.** Keep only the prepared helper + tests; defer wiring until the leg semantics are ratified.

## OPERATOR RULING 2026-07-21: A2 (LENDING + STAKING) + the real economic structure

The operator corrected the model (which could not be safely inferred from code):

- **`carry_staked_basis` does NOT borrow or lend on Aave.** It buys ETH/SOL → stakes → receives LST/LRT → shorts
  (spot/perp) against the LST where the LST is accepted as collateral. Its interest is therefore the **LST/LRT
  exchange-rate appreciation** (staking) minus the **short funding** — NOT an Aave `rate_spread`. The current spine's
  `LENDING_INTEREST = rate_spread/365` for this strategy is a **mismodeling** to correct.
- **`recursive_staking` is the borrow-to-stake strategy** — it stakes, uses the LST as collateral, borrows, and stakes
  again (leverage loop). This is where the Aave **`borrow_index`** (cost of the borrowed leg) genuinely applies, against
  the LST staking yield on the staked leg.

**So A2 =** staking legs (both strategies) → LST/LRT **exchange-rate index** (Hard Rule #5); borrow leg
(`recursive_staking` only) → `aave_borrow_index`; and correct the `carry_staked_basis` lending mismodeling.

**Data confirmed (verified vs GCS):**

- STAKING: `lst_yields` carries `exchange_rate` + `prev_rate` (LST redemption-rate index; e.g. 1.069→1.231) — the
  sample-to-sample ratio `exchange_rate/prev_rate − 1` is pre-built. Keyed `token`/`protocol`/`asset`. **Coverage is
  sparse — only 15 days** (a real gap: staking accrues zero on days with no `lst_yields` row → NAV under-report; file
  the coverage extension).
- BORROW: `aave_borrow_index` 100% populated in `lending_rates` (1.0→5.45).

**Build scope (A2):** per-position resolution to (a) the staked LST's `lst_yields` row for the staking leg, (b) the Aave
reserve's `aave_borrow_index` for `recursive_staking`'s borrow leg; replace the banned `/365` forms; honest-absence →
zero + visible log (esp. for the sparse LST days); deterministic prev/now from the immutable partition; real
paper-vs-batch passive-parity test; NO schema/keying/factor/sink change. Ship CODE to LDR on clean 3-lens review.

## The prod-NAV RECOMPUTE is a separate operator-gated step

Landing option A on LDR changes the code; it does NOT retroactively recompute historical client-reports. Rerunning
history with the corrected formula (which restates every client's past interest PnL/NAV) is a deliberate,
separately-gated backfill — human-gated, not part of the code ship. </content>
