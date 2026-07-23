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
separately-gated backfill — human-gated, not part of the code ship.

## LST exchange-rate is FOUR different numbers (operator, 2026-07-21) — audit in flight

The operator flagged that "the LST exchange rate" is not one thing. For a staking token (stETH, and same shape for
wstETH/rETH/cbETH/rsETH/weETH/ezETH/jitoSOL/mSOL/…) there are FOUR distinct rates, each for a different PnL use:

| #   | rate                                            | source                                          | which leg it serves                            |
| --- | ----------------------------------------------- | ----------------------------------------------- | ---------------------------------------------- |
| 1   | CEX spot (e.g. stETH/USDT on Binance)           | market-data-tick-cefi (if we capture LST pairs) | mark-to-market of the LST position (basis)     |
| 2   | DEX pool (e.g. stETH/ETH on Uniswap v3 / Curve) | market-data-tick-defi DEX (canonical path)      | secondary-market peg vs underlying (basis)     |
| 3   | Aave oracle rate                                | on-chain oracle Aave uses for LST collateral    | collateral value → LTV/liquidation (recursive) |
| 4   | Protocol redemption (Lido getPooledEthByShares) | the staking protocol contract (fair value)      | the TRUE staking-yield accrual                 |

Correct A2 needs: **#4** for the staking accrual, **#1/#2** for the mark-to-market of the LST vs the short, **#3** for
recursive-staking collateral/borrow. `lst_yields.exchange_rate` is exactly ONE of these (likely #4, unconfirmed) — do
NOT wire staking PnL to it until the audit confirms which, and that we have the right rate for each leg. **Audit
running:** workflow `wf_268532e0-323` builds the availability matrix (token × 4 sources × coverage + source-of-truth);
its result is NOT yet on disk — process it when it lands.

## Progress / in-flight (fresh-session resume point)

- **RULED:** engine = spine (option A), scope = A2 (LENDING + STAKING). Economics per operator recorded above.
- **PREPARED (untracked, held in strategy-service working tree, NOT shipped):**
  `strategy_service/engine/backtest/index_ratio_accrual.py` + `tests/unit/engine/backtest/test_index_ratio_accrual.py` —
  the correct pure `index_ratio_accrual(notional, prev, now) = notional*(now/prev−1)` helper (honest-absence→0) with 10
  golden tests passing. It will be shipped WITH the wiring, not orphaned.
- **IN-FLIGHT workflows (will notify a fresh session, results not yet durable):** `wf_fede40e7-098` (A2 position-
  structure understand sweep) and `wf_268532e0-323` (the 4-rate data audit above). Process both, then build A2.

## Deferred work after 2026-07-21

| item                                                                   | state          | blocked-on                                                                                                      |
| ---------------------------------------------------------------------- | -------------- | --------------------------------------------------------------------------------------------------------------- |
| A2 build (staking via #4 + borrow via aave_borrow_index)               | Not done       | the 2 in-flight sweeps landing + the 4-rate audit confirming which rate = #4                                    |
| LST rate coverage (which of #1–#4 we actually have)                    | Cannot yet     | audit `wf_268532e0-323` result                                                                                  |
| `lst_yields` sparse coverage (only 15 days)                            | Not done       | features/MTDS — file the coverage extension once the audit confirms the source                                  |
| STAKING-leg data if #4 not fully captured                              | Cannot yet     | audit result — may need a new collector (Lido redemption)                                                       |
| Onchain consolidator frozen (mark→recompute blocker)                   | Not done       | see [[onchain_manifest_dishonest_and_recompute_blocked_2026_07_21]]                                             |
| MTDS chain-field collectors (ltv/liq_threshold/…)                      | Not done       | new upstream scope (same doc)                                                                                   |
| 2 adjacent onchain vocabularies (required_inputs, \_feature_contracts) | Not done       | a dedicated UAC reconciliation pass                                                                             |
| prod-NAV historical recompute                                          | Operator-owned | human-gated; only after the A2 code is reviewed + landed                                                        |
| 2 features-service safe-survivor fixes                                 | Not done       | stashed `features-safe-survivor-fixes-2026-07-20-DEFERRED…`; reconcile against peer `features-service@9ce1f4ab` |

**Recommended next item:** process the two in-flight sweeps (`wf_268532e0-323` first — it gates WHICH rate to use), then
build A2 only for the legs whose data the audit confirms; surface any missing rate (esp. #4 protocol redemption or #3
Aave oracle) as a data gap rather than wiring on a proxy.

## Lessons (so they are not re-learned)

- **The operator's named target was dead code.** `compute_pnl` reads nothing to prod; the consumed engine is the
  determinism spine. Always confirm the CONSUMED sink before "finishing" a named function.
- **"The LST exchange rate" is four numbers** (CEX / DEX / Aave-oracle / protocol-redemption) — never wire staking PnL
  to whichever column happens to be named `exchange_rate` without confirming which of the four it is.
- **Green determinism tests do NOT prove interest correctness** — the ε=0 fill proof EXCLUDES passive/interest rows, so
  a passive-row parity test is a separate, required guard.
- **Two careful build agents refused to wire the money-path on a wrong model and escalated** — that was correct; a
  plausible NAV edit on a wrong leg-mapping is worse than a gated pause.
- **`lst_yields` is only 15 days** — a full-history staking recompute would silently book zero on missing days; make it
  a visible flag.

## A2 build is BLOCKED on 4 escalations (understand sweep `wf_fede40e7-098`, 2026-07-21)

The A2 position-structure sweep returned `buildable_now: false`. Resume-critical findings (full spec in that run's
journal; resumable via `resumeFromRunId: wf_fede40e7-098`):

- **E1 [BLOCKER — money-path]** csb SHORT-FUNDING source. The operator's "LST appreciation MINUS short funding" — but
  today `FUNDING_ACCRUAL = -basis_amount` where basis IS the Aave rate_spread; once the LENDING mismodel is zeroed, the
  funding leg collapses to 0. The "minus short funding" half has **no confirmed data source** (need real perp funding
  for the short). Must resolve before csb interest is correct.
- **E2 [confirm — sets the number]** staking BASE units. Hard Rule #5's `holding` is the LST balance in NATIVE units;
  the spine passes `staked_notional` in QUOTE units. Rec: multiply the ratio by the quote `staked_notional` (CARRY
  factor isolates staking yield in quote) — confirm.
- **E3 [scope]** RECURSIVE staking is NOT drivable in the spine today (not in `_ENGINE_DRIVABLE_ARCHETYPES`, missing
  perp/spot config keys → emits ZERO passive rows). Adding the `aave_borrow_index` borrow leg is **net-new archetype
  wiring**, not a formula swap — a tracked FOLLOW-ON, bigger than csb.
- **E4 [confirm]** A2 necessarily DROPS the csb LENDING/BASIS rows (csb does not lend) — contradicts "no schema change".
  Confirm intended csb row-set = {STAKING via LST index, FUNDING via real perp}, LENDING/BASIS explicit-zeroed.

**Smallest correct increment (when unblocked):** csb STAKING leg only — swap `STAKING_REWARD`/`CARRY` to the
`lst_yields` index ratio keyed off `cfg['lst_asset']` (threaded into the loader — TODAY both call sites pass
`lst_asset=native_asset='ETH'` for delta-netting, so the LST token is in config but NOT in the loader), explicit-zero
the LENDING mismodel, resolve FUNDING per E1. Position resolution is derivable (`cfg['lst_asset']` → UAC
`protocol_asset_for_token`); feed must widen from a `(day,bps,bps)` tuple to a typed record carrying index PAIRS
(cross-archetype change); `lst_yields` has NO dup rows (prebuilt prev/now), `lending_rates` has ~3× dup (sort+dedup+
min/max, never iloc). Recursive + compound/kamino dispatch = follow-on.

**So the A2 build is gated on: E1 (funding source) + E2/E4 (confirms) + the 4-rate audit `wf_268532e0-323` (which rate
is #4). Do NOT wire until these resolve.**

## OPERATOR RULINGS 2026-07-23 (E1/E2/E4, interactive)

- **E1 — RESOLVED.** Confirmed real perp funding rate, operator's own words: "short funding is a separate track for
  which — when we are short — we apply funding rates; net positive PnL if funding rate is positive on the short perp
  leg, and we add the LST appreciation as our long leg. Simple. That's what staked-basis trading is." I.e. this is the
  canonical basis-trade structure: LONG leg = hold the LST (spot exposure, earns the LST-appreciation/staking yield
  baked into the exchange rate); SHORT leg = short the underlying's perp (delta-hedge), which EARNS funding when the
  perp funding rate is positive (shorts receive funding when longs pay, i.e. rate > 0 → short receives). Net csb PnL =
  LST appreciation (`lst_yields` ratio) + funding earned on the short perp leg. **Still needs a concrete data-source
  identification pass** (which perp/venue is the canonical short leg per `lst_asset` — e.g. ETH-PERP on which venue —
  and whether real funding-rate history is already captured for it) before this can be wired; the STRUCTURE is now
  confirmed, the exact instrument mapping is not yet.
- **E2 — NOT resolved, operator asked for MORE investigation, not a pick.** Operator: "investigate more, what's more
  accurate — because depending on the share class, sometimes we want ETH-underlying units, sometimes USD, so we need to
  be able to figure out both, no?" This means: do NOT hardcode a single unit convention (neither the doc's own "multiply
  by quote staked_notional" recommendation nor native LST units alone) — the real requirement is **supporting BOTH
  representations** (native-underlying and quote/USD) depending on share class, not choosing one. This is an open design
  question needing its own investigation (what "share class" concretely means in this codebase's config, whether both
  units can coexist in the same feed/schema or need a per-share-class branch) before E2 can be considered closed.
- **E4 — CONFIRMED.** csb row-set = {STAKING via LST index, FUNDING via real perp}; LENDING/BASIS rows dropped entirely
  (not explicit-zeroed-but-present) — matches the actual economic structure of a staking-basis position, operator
  explicitly chose this over preserving the old schema shape.

**Updated gating**: E4 is closed. E1's STRUCTURE is closed but the concrete perp/venue data-source mapping per
`lst_asset` is a new, still-open sub-task. E2 is explicitly NOT closed — needs a dedicated investigation into
share-class-dependent dual-unit support before the STAKING leg's unit convention can be finalized. The A2 build remains
gated until E1's data-source mapping and E2's dual-unit design are both resolved — do not wire the STAKING leg with a
single hardcoded unit convention.</content>
