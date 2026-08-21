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
  SSOT contradiction, so it is operator-gated before ship. **UPDATE 2026-08-18 (plan_reconciler)**: for the
  `carry_staked_basis` archetype specifically, the FUNDING leg (strategy-service@aa1fcdc7) and STAKING leg
  (strategy-service@e93902d8) are now shipped onto real index-ratio/funding-rate sources (shas verified reachable
  on origin/live-defi-rollout) — see body Progress Log 2026-07-23. Whether every other archetype's interest PnL is
  similarly fixed, or the banned-formula problem persists elsewhere, was NOT re-verified this pass — check the
  Todos section for current scope before assuming this summary's "unqualified banned formula" framing still applies
  fleet-wide.
status: open
nature: issue
asset_group: [defi]
stage: [strategy]
repos: [strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: [pnl-correctness, interest-accrual, determinism-spine, ssot-contradiction, money-path, defi, operator-gate]
related:
  [
    /plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md,
    /plans/archive/issues/silent_wrong_answer_audit_candidates_2026_07_20.md,
    /plans/active/issues/pnl_true_native_staking_return_spec_2026_08_20.md,
  ]
created: 2026-07-21
author: unknown
parent_epic: security_and_cross_cutting_master
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
context_scope:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    strategy-service/strategy_service/engine/backtest/paper_run_passive.py,
    strategy-service/strategy_service/engine/backtest/paper_run_attribution.py,
    strategy-service/strategy_service/engine/backtest/benchmark_fills.py,
    strategy-service/strategy_service/engine/backtest/index_ratio_accrual.py,
    /plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md,
  ]
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

### Partial resolution 2026-07-23 — code-traced which rate MTDS's `lst_rates` actually is, per chain

This does NOT replace `wf_268532e0-323` (that audit's availability matrix is broader — all 4 sources × all tokens), but
directly answers "is `lst_yields.exchange_rate` really #4?" for the tokens that matter TODAY (the only currently
perp-eligible LST is stETH, per E1) — traced by reading the actual collector code, not inferring:

- **EVM side (stETH, rETH, weETH, cbETH, mETH, swETH, ETHx, osETH, ankrETH, pufETH, wstETH) — CONFIRMED genuine #4, for
  EVERY historical date, not just "today".** `market-tick-data-service/.../lst_rates_handler.py`'s
  `_EVM_LST_ABI_METADATA` calls each token's OWN protocol contract method directly (stETH→ `getPooledEthByShares`,
  rETH→`getExchangeRate`, weETH→`getRate`, etc. — one canonical redemption/exchange-rate function per protocol).
  Critically, `_query_rate()` (line 834) takes an explicit `block_number: int` ("Historical block number to query at"),
  resolved per-date via `alchemy_client.get_block_by_timestamp(noon_ts, chain= "ETHEREUM")`, then calls
  `web3.eth.call(..., block_identifier=block_number)` — a genuine on-chain read AT THAT HISTORICAL BLOCK, confirmed live
  in this session's own backfill run.log ("Querying LST rates for 2025-04-15 at block 22274244"). This is NOT a
  current-state proxy — it's true protocol-redemption fair value, accurate for every historical day. **Confidence: high
  — the STAKING leg's data source for stETH (today's only perp-eligible LST) is genuinely #4, and E1's FUNDING-leg build
  can proceed to a STAKING-leg build on the same footing whenever that's scoped**, without waiting on the SOL-side
  caveat below.
- **Solana side (jitoSOL, mSOL, bSOL, sanctumSOL) — CONFIRMED NOT #4 for historical dates; a market-derived proxy
  instead.** `solana_lst_archival.py`'s Tier 1 (`_tier1_*_alchemy`, the genuine on-chain SPL stake-pool decode — the
  true Solana analog of `getPooledEthByShares`) is explicitly gated `if today and rpc_url:` in every fetch function
  (`_fetch_jito_rate`/`_fetch_bsol_rate`/`_fetch_sanctum_rate`) — correctly, because Solana's `getAccountInfo` JSON-RPC
  call has no historical-block parameter in this codebase's usage (always returns CURRENT state), so Tier 1 can only
  ever answer for the actual present day, never a backfill date. Tier 2 (The Graph subgraph) is a confirmed permanent
  no-op today (no Solana subgraph IDs registered in UAC). Tier 3 (each protocol's own REST API) is ALSO explicitly gated
  to `today`-only in the code (its own docstring: "Only valid for the current day... there is no per-day series").
  **This means every single historical day of Solana `lst_rates` data (i.e. all of this session's
  `2021-08-17→2026-07-22` Solana backfill except the literal last day) came from Tier 4 — `coins.llama.fi` DefiLlama
  historical price ratio (LST-USD / SOL-USD)**, which is a MARKET-DERIVED price (closer to rate #1/#2, an aggregated
  spot-price ratio) — NOT the protocol's own redemption rate. Not a bug (the code's own honest-absence/tier-gating
  design correctly prevents mislabeling current-state as historical — verified no date-mislabeling occurs), but a real,
  now-confirmed caveat: if a Solana LST ever becomes perp-eligible again (none are today per E1 — DRIFT was removed),
  its STAKING leg would need this caveat accounted for before wiring, since `lst_yields.exchange_rate` for those tokens
  is NOT rate #4 historically, unlike the EVM side.
- **Not yet checked**: rsETH/ezETH/wBETH (the `_lst_extended_rates.py` extended-EVM roster, distinct from
  `lst_rates_handler.py`'s core roster above) and the Aave-oracle (#3) / CEX-spot (#1) / DEX-pool (#2) sourcing for any
  of these tokens — out of scope for this pass since none of them are in `_STAKED_BASIS_ETH_LSTS` today. Leave to
  `wf_268532e0-323`'s broader matrix.

## Progress / in-flight (fresh-session resume point)

- **RULED:** engine = spine (option A), scope = A2 (LENDING + STAKING). Economics per operator recorded above.
- **PREPARED (untracked, held in strategy-service working tree, NOT shipped):**
  `strategy_service/engine/backtest/index_ratio_accrual.py` + `tests/unit/engine/backtest/test_index_ratio_accrual.py` —
  the correct pure `index_ratio_accrual(notional, prev, now) = notional*(now/prev−1)` helper (honest-absence→0) with 10
  golden tests passing. It will be shipped WITH the wiring, not orphaned.
- **IN-FLIGHT workflows (will notify a fresh session, results not yet durable):** `wf_fede40e7-098` (A2 position-
  structure understand sweep) and `wf_268532e0-323` (the 4-rate data audit above). Process both, then build A2.

## Deferred work after 2026-07-21

| item                                                                   | state          | blocked-on                                                                                                                                    |
| ---------------------------------------------------------------------- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| A2 build (staking via #4 + borrow via aave_borrow_index)               | Not done       | the 2 in-flight sweeps landing + the 4-rate audit confirming which rate = #4                                                                  |
| LST rate coverage (which of #1–#4 we actually have)                    | Cannot yet     | audit `wf_268532e0-323` result                                                                                                                |
| `lst_yields` sparse coverage (only 15 days)                            | Filed          | GCS-verified + backfill scope proposed, see [[defi_lst_yields_coverage_extension_gcs_verified_2026_07_28]] (backfill itself not yet executed) |
| STAKING-leg data if #4 not fully captured                              | Cannot yet     | audit result — may need a new collector (Lido redemption)                                                                                     |
| Onchain consolidator frozen (mark→recompute blocker)                   | Not done       | see [[onchain_manifest_dishonest_and_recompute_blocked_2026_07_21]]                                                                           |
| MTDS chain-field collectors (ltv/liq_threshold/…)                      | Not done       | new upstream scope (same doc)                                                                                                                 |
| 2 adjacent onchain vocabularies (required_inputs, \_feature_contracts) | Not done       | a dedicated UAC reconciliation pass                                                                                                           |
| prod-NAV historical recompute                                          | Operator-owned | human-gated; only after the A2 code is reviewed + landed                                                                                      |
| 2 features-service safe-survivor fixes                                 | Not done       | stashed `features-safe-survivor-fixes-2026-07-20-DEFERRED…`; reconcile against peer `features-service@9ce1f4ab`                               |

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
single hardcoded unit convention.

## PROGRESS 2026-07-23 — FUNDING leg shipped (E1's data-source mapping now RESOLVED); STAKING leg still gated

**E1's data-source sub-task is now resolved** and the FUNDING leg is **SHIPPED**: `strategy-service@aa1fcdc7`
(`live-defi-rollout`, quickmerge landed, `quality-gates.sh` green — 5277 tests, Codex compliance within the pre-existing
4-violation tolerance, no new baseline-ratchet regressions).

- **Data-source mapping (confirmed against real GCS + `catalog_staked_basis.py`):** the ONLY two perp venues eligible as
  LST collateral today are **DERIBIT** (`ETH-PERPETUAL`) and **BYBIT** (`ETHUSDT`) — verified via
  `accepted_perp_collateral()` against UAC `VENUE_COLLATERAL_MATRIX` (7.5%/10% haircuts respectively). Both carry a
  real, non-null `derivative_ticker.funding_rate` column (spot-checked prod parquets directly: DERIBIT 2026-04-15 =
  113,720 ticks/day; BYBIT 2026-05-15 = 228,971 ticks/day).
- **New provider** `strategy_service/engine/core/canonical_derivative_ticker_funding_provider.py` —
  `CanonicalDerivativeTickerFundingProvider`: reads the shared `tick-data`/`cefi` bucket, day-means the `funding_rate`
  column (offset-robust, matching the prior-art `e2e-testing/scripts/defi/staked_basis_funding_scan.py` convention),
  scales to a per-day fraction via the UAC `perp_funding_cadence.fundings_per_day()` SSOT (never an inline
  periods-per-day constant). Narrow, explicit venue→symbol allowlist (DERIBIT/BYBIT only) — an unmapped venue is honest
  absence, never a guessed symbol.
- **Sign convention** (operator E1, verbatim): short perp RECEIVES when the rate is positive → `FUNDING_ACCRUAL`/
  `FUNDING` = `+notional * day_funding_fraction` (no negation) — verified consistent with the existing `staked_basis.py`
  engine docstring ("positive means longs pay shorts → adds to carry").
- **Wiring**: a purely additive `funding_rates_by_day: Mapping[str, Decimal] | None = None` parameter on
  `build_paper_run_passive` / `build_paper_run_attribution` (+ its `emit_` wrapper) and a new
  `StrategyReplay.funding_rates_by_day` field, populated in `replay_carry_strategy` ONLY for
  `spec.archetype == CARRY_STAKED_BASIS` (scoped to real config keys via direct indexing, not `.get(key, "")` —
  `_emit_staked_basis_slots` always populates both). `None` (every other archetype, every pre-existing caller) preserves
  the legacy `-basis_amount` proxy byte-for-byte — **zero behavior change outside this one leg**. Threaded into both
  `paper_run_handler.py::run_paper` and `batch_rerun.py`'s passive re-derivation, so a same-window batch rerun
  re-derives the identical mapping from the same immutable `day=` partition (ε=0 holds for the FUNDING leg too — proven
  with a paper≡batch parity test at the producer boundary, mirroring the style of the already-held
  `test_index_ratio_accrual.py` parity test).
- **STAKING_REWARD / LENDING_INTEREST are untouched** — verified via the full pre-existing test suite (unchanged, still
  green) that no other leg's computation shifted.
- **3-lens review (money-path gate) — CLEAN, shipped.** Correctness: sign + data source cross-verified against 2
  independent codebase sources + the operator's own words. Determinism: pure function of (perp_venue, native_asset,
  window) over the immutable GCS partition; parity tests added at both the new provider and the two producers.
  Honest-absence: every layer defaults to a logged zero on missing data, never a fabricated or silently-reused proxy.
- **Big finding (data-correctness, notified here per the money-path/findings-triage rule):** verified against real prod
  GCS that **`derivative_ticker` capture for EVERY CeFi venue under `pipeline_mode=batch_tardis` has NO coverage from
  ~2026-05-22 through at least 2026-07-20** (not DERIBIT/BYBIT-specific — the whole CeFi derivative_ticker collector,
  all venues, same window; `book_snapshot_5` for the same venues DOES continue into July, so this is scoped to the
  funding-rate collector specifically). This is a **pre-existing MTDS/Tardis backfill gap**, separate from and not fixed
  by this change. Practical effect: a LIVE rolling 7-day paper window today falls entirely inside this gap, so
  FUNDING_ACCRUAL will honestly book **zero** (with a visible log) until the collector backfill resumes — still strictly
  better than the current-in-prod wrong nonzero `-basis_amount` proxy, but worth a dedicated MTDS-side follow-up to
  actually restore live funding-rate capture. Historical windows before 2026-05-22 (where real data exists) will show
  real nonzero funding once a batch rerun covers them.
- **Deliberately NOT touched (out of this task's scope, confirmed correct to leave alone):** `compute_pnl` /
  `compute_handler` (dead-code surfaces per the doc's own analysis, unrelated to this fix); the STAKING leg (LST
  appreciation — still gated on the 4-rate-identity audit + E2's dual-unit design, per the standing rulings above);
  `LENDING_INTEREST`/`BASIS` for `carry_staked_basis` (E4 already ruled these DROP entirely, not index-ratio'd — a
  separate, still-open build); the already-held, still-unwired `strategy_service/engine/backtest/index_ratio_accrual.py`
  primitive — verified it is STILL PRESENT, untouched, exactly as found (not rebuilt, not committed). It is NOT the
  right tool for FUNDING (a genuine per-cycle rate, not a cumulative index — see the doc's own REFINEMENT section) and,
  per the fresh E4 ruling, is no longer needed for `carry_staked_basis`'s LENDING leg either (dropped, not fixed) — its
  remaining live use is `recursive_staking`'s borrow leg (E3), an explicit, bigger follow-on left for a dedicated
  session.

**Next open item**: process E2 (share-class dual-unit investigation) + the outstanding 4-rate-identity audit result,
then build the STAKING leg. `recursive_staking`'s borrow-leg wiring (E3) remains a separate, tracked follow-on.

## PROGRESS 2026-07-23 — STAKING leg SHIPPED (csb STAKING_REWARD/CARRY now index-ratio'd); LENDING mismodeling still open

**The STAKING leg is now wired + shipped**: `strategy-service@e93902d8` (`live-defi-rollout`, quickmerge landed,
`quality-gates.sh --no-fix` green — 5296 tests passed incl. 5 new/updated test files for this build; the two files held
unwired since the earlier pass (`index_ratio_accrual.py` + its test) are now committed as part of this change).

- **Schema confirmed (verified against the real producer, not inferred):**
  `features-service/features_service/onchain/engine/lst_features.py::compute_lst_features_for_day` joins `day` and
  `day - 1`'s `lst_rates` oracle rows per token BEFORE writing the `lst_yields` feature parquet, so a SINGLE row per
  `(day, token)` already carries both `exchange_rate` (today) and `prev_rate` (yesterday, pre-joined) — exactly the
  `(index_prev, index_now)` pair `index_ratio_accrual` needs, no separate two-day fetch required on the strategy side.
  Keying confirmed against the prior-art reader for THIS EXACT archetype
  (`scripts/trace_all_carry_archetypes.py::_resolve_carry_staked_basis`): catalog `lst_asset` (e.g. `stETH`) matches the
  parquet's `token` column directly; `staking_protocol` (e.g. `LIDO`, matching UAC
  `LST_TOKEN_TO_PROTOCOL_ASSET["stETH"] == ("LIDO", "ETH")`) is a belt-and-braces cross-check against `protocol`
  (normalised — strip underscores/hyphens — so catalog `rocketpool` matches parquet `ROCKET_POOL`).
- **New provider** `strategy_service/engine/core/canonical_lst_yields_index_provider.py` —
  `CanonicalLstYieldsIndexProvider`: composes the EXISTING `GCSFeatureProvider` (the same reader
  `_load_carry_staked_ticks` already uses for `lending_rates` — same bucket, same
  `onchain/by_date/day={D}/feature_group={group}/features.parquet` path convention) rather than reinventing raw GCS
  access, since `lst_yields` is a features-onchain output like `lending_rates`, not a raw tick-data corpus (unlike the
  FUNDING leg's `derivative_ticker`, which genuinely lives in the shared tick-data bucket). Honest absence: a day with
  no `lst_yields` row for the (protocol, token) pair returns `None` — the caller books zero + logs.
- **Wiring**: mirrors the FUNDING leg (E1) exactly — a purely additive
  `staking_index_by_day: Mapping[str, tuple[Decimal, Decimal]] | None = None` parameter on `build_paper_run_passive` /
  `build_paper_run_attribution` (+ its `emit_` wrapper) and a new `StrategyReplay.staking_index_by_day` field, populated
  in `replay_carry_strategy` ONLY for `spec.archetype == CARRY_STAKED_BASIS` (direct indexing on
  `config["staking_protocol"]`/`config["lst_asset"]` — `_emit_staked_basis_slots` always populates both). `None` (every
  other archetype, every pre-existing caller) preserves the legacy `notional * staking_bps/1e4/365` proxy byte-for-byte
  — zero behavior change outside this one leg. Threaded into `paper_run_handler.py::run_paper` and `batch_rerun.py`'s
  passive re-derivation (batch_rerun.py does not call the attribution producer at all — only the passive tape — so that
  is the one call site there).
- **What changed vs what stayed**: ONLY `STAKING_REWARD` (passive) / `CARRY` (attribution) now use
  `index_ratio_accrual(notional, index_prev, index_now)` when real data resolves. `LENDING_INTEREST`/`BASIS` are
  UNCHANGED in this build (see below — still the pre-existing `rate_spread/365` form, not yet corrected for the
  mismodeling). `FUNDING_ACCRUAL`/`FUNDING` are unaffected (E1's leg, untouched).
- **Determinism**: pure function of (staking_protocol, lst_asset, window) over the immutable GCS `day=` partition;
  parity tests added at both the new provider (`test_canonical_lst_yields_index_provider.py`) and the two producers
  (`test_paper_run_passive.py`/`test_paper_run_attribution.py`/`test_index_ratio_accrual.py`) — paper vs same-window
  batch-rerun re-derive byte-identical STAKING_REWARD/CARRY rows.
- **3-lens review (money-path gate) — CLEAN, shipped.** Correctness: schema + keying cross-verified against the real
  features-service producer AND the prior-art tracer reader (2 independent codebase sources), not inferred. Determinism:
  pure function of the immutable partition + parity tests at both layers. Honest-absence: every layer defaults to a
  logged zero on missing data (real gap — `lst_yields` coverage is sparse, ~15 days total as of 2026-07-23), never a
  fabricated or silently-reused proxy.
- **Deliberately NOT touched in this build (confirmed correct to leave alone):**
  - `LENDING_INTEREST` for `carry_staked_basis` — **STILL the banned `rate_spread/365` form, UNCHANGED.** The operator
    ruled (2026-07-21, "OPERATOR RULING") this leg is a MISMODELING — `carry_staked_basis` does not lend/borrow on Aave,
    it stakes + shorts a perp — but did NOT rule what replaces the formula: zero it, drop the row entirely (which is
    what the later E4 ruling implies for the row-SET but has not yet been implemented in code — E4 said "LENDING/ BASIS
    rows dropped entirely", but the current code still emits them, just with the old formula), or something else. **This
    is the next concrete increment**: implement E4's already-ruled row-set (drop LENDING_INTEREST/BASIS for csb
    entirely, not just leave the formula) — a smaller, already-decided change, not a new ruling needed.
  - `recursive_staking`'s borrow leg (`aave_borrow_index` wiring, E3) — separate, bigger, not-started follow-on.
  - Any Solana LST wiring — Solana `lst_yields`/`lst_rates` data is confirmed a market-derived proxy (not true
    protocol-redemption), not a true index; would need its own caveat-aware build if a Solana LST ever becomes
    perp-eligible.
  - `compute_pnl`/`compute_handler`/`settlement_service.py` — confirmed dead-code / correct-reference surfaces,
    unrelated to this fix.
- **The prod-NAV RECOMPUTE remains a separate, human-gated step** (unchanged from the FUNDING leg's note above) — this
  code change does not retroactively restate historical client NAV/PnL.

**Next open item / follow-up (tracked here since this doc has no separate active plan):**

- [x] [BACKEND] P1. E4's already-ruled row-set (csb row-set = {STAKING via LST index, FUNDING via real perp};
      LENDING/BASIS DROPPED entirely, not just left on the old formula) — **SHIPPED `strategy-service@a90e85eb`**
      (`live-defi-rollout`, quickmerge landed, `quality-gates.sh --no-fix` green — a genuine fresh run with the
      content-sentinel cleared to force real re-execution, not a cached skip: 5407 tests passed incl. 6 new/updated test
      files for this build, 0 failed, Codex compliance within the pre-existing 4-violation tolerance). - **Scope-checked
      before touching anything (per this doc's own caution):** `build_paper_run_passive`/ `build_paper_run_attribution`
      (`strategy_service/engine/backtest/paper_run_passive.py` / `paper_run_attribution.py`) are NOT
      `carry_staked_basis`-exclusive — they are the SAME shared producer the `run_paper` handler's generic branch also
      calls for `CARRY_BASIS_PERP`, `CARRY_FUNDING_DISPERSION`, and the DEX-pool/dispersion archetypes
      (`DEFI_LP_CONCENTRATED`/`DEFI_LP_POOL`/`ARBITRAGE_PRICE_DISPERSION`) — for those archetypes the
      LENDING_INTEREST/BASIS row is a GENUINE leg (fee APY / dispersion basis), not a mismodeling.
      `CARRY_RECURSIVE_STAKED` (its own dedicated `build_recursive_staked_passive`/ `_attribution` — real Aave
      borrow-index debt leg, E3, already shipped) and `CARRY_STAKED_BASIS_DATED` (its own dedicated
      `build_staked_basis_dated_passive`/`_attribution`) were confirmed UNTOUCHED — neither reuses the two functions
      this build changed. - **Fix**: added a new `emit_lending_leg: bool = True` parameter to both shared producers (+
      the `emit_paper_run_attribution` thin bridge) — default `True` preserves the exact pre-existing 3-row/3-factor
      shape for every caller that doesn't pass it (every archetype above). Wired
      `emit_lending_leg = (archetype != CARRY_STAKED_BASIS)` at the ONE call site in `paper_run_handler.py::run_paper`'s
      generic branch (shared by attribution + passive) and the equivalent passive re-derivation loop in `batch_rerun.py`
      (which does not call attribution at all — pre-existing, confirmed unrelated to this fix). The row is DROPPED
      entirely when `False` (removed from the `day_accruals`/`day_rows` list before emission) — never a zero-amount
      row. - **Row count verified**: `carry_staked_basis`'s passive tape is now 2 rows/held-day (STAKING_REWARD +
      FUNDING_ACCRUAL, not 3) and its attribution rows are CARRY + FUNDING (+ FEES), BASIS dropped — confirmed via new
      tests (`test_emit_lending_leg_false_drops_lending_interest_row_entirely` / `_drops_basis_row_entirely`) plus a
      paper↔batch parity test at both producers. Every other archetype's default-`True` row count is UNCHANGED (pinned
      by new `test_emit_lending_leg_default_true_preserves_three_row_shape`/`_factor_shape` tests alongside the
      pre-existing 3-row assertions, which needed no edits since the default is unchanged). - **Big finding (not this
      task's to fix, noted for the record):** this checkout is a SHARED working tree — mid-build, a concurrent agent's
      own WIP on `catalog_trading.py`/`test_paper_universe.py` (`ARBITRAGE_PRICE_DISPERSION` candidate-venues fix)
      landed as `strategy-service@05c0b2ed` while this build was in progress, and separately another concurrent agent
      was actively editing `strategy_service/{types.py,engine/core/config_loader.py}` + several `configs/*.yaml` + their
      test files DURING this session — confirmed those diffs are unrelated to this task and were left untouched (never
      staged, never reverted). A first quality-gate pass (run before `05c0b2ed` landed) surfaced one transient failure
      in `test_dex_pool_archetypes_are_drivable_and_selected`, isolated (single-test + isolated-diff reruns) to that
      concurrent WIP's own in-flight state, not this change — the final fresh full-suite run (after their commit landed)
      is 100% green.
- [x] [BACKEND] P2. `recursive_staking`'s borrow leg (`aave_borrow_index` wiring, E3) — **SHIPPED
      `strategy-service@23bd8b76` (2026-07-23)**, done as part of
      [[defi_archetype_universe_no_curtailment_mechanism_2026_07_23]]'s Phase 2 (also wired `CARRY_RECURSIVE_STAKED`'s
      tick loader in the same change, since the archetype had no paper-replay path at all before this). New
      `strategy_service/engine/core/canonical_aave_borrow_index_provider.py` (`CanonicalAaveBorrowIndexProvider`) reads
      real `lending_rates.aave_borrow_index`, day-over-day differenced (unlike `lst_yields`, this corpus carries only
      the current index value per row, not a pre-joined prev/now pair) — reuses the SAME `index_ratio_accrual()`
      primitive fed the debt index instead of the LST exchange-rate index, booked NEGATIVE at a
      `{lending_protocol}:DEBT_TOKEN:{native_asset}` key matching the engine's real `BORROW` `AtomicLeg` instrument_key
      exactly (verified against a real replay). **Per-reserve honest absence confirmed empirically** (5 real prod days
      spot-checked, 2026-07-23): `AAVE_V3_ETHEREUM` is 100% populated; `COMPOUND_V3_ETHEREUM` has real rows
      (DefiLlama-Yields APY-only source) but ZERO `aave_borrow_index` ever (MTDS has no on-chain Compound V3 collector)
      — its debt-cost leg honestly books zero, never a proxy from Aave's index; `KAMINO_SOLANA` never appears as a
      `protocol` value in `lending_rates` at all (MTDS's Kamino connector is a BLOCKED-CREDENTIALS scaffold) — both legs
      skip for that reserve. Full evidence + quality-gate status in the linked doc's Phase 2 entry.
- [x] [DATA] P2. `lst_yields` sparse coverage (~15 days) — file the coverage extension with features-onchain/MTDS once
      bandwidth allows; until then, STAKING_REWARD honestly books zero (with a visible log) for any day outside that
      window. — **FILED 2026-07-28 (slot-12, data_engineering)**: GCS-verified the exact gap (features-onchain
      `lst_yields` = exactly 15 day-partitions, 2026-04-03..2026-04-19 with a 2-day internal hole; MTDS raw `lst_rates`
      spans years on both sides per EVM token — LIDO confirmed 2021-08-17..2026-07-27, ETHERFI confirmed at least
      2024-01-01..2026-07-27, all 11 active EVM LST venues confirmed present on one representative in-window day) and
      proposed the concrete backfill scope (repo, date range, CLI mechanism) — confirmed a features-layer batch-compute
      lag, not raw-data absence. Backfill itself NOT executed (read-only investigation + proposal doc, per its own
      scope). See [[defi_lst_yields_coverage_extension_gcs_verified_2026_07_28]].

## E2 INVESTIGATION 2026-07-23 (sub-agent, design-only — no code changed)

Scope: the operator's "investigate more … depending on the share class, sometimes we want ETH-underlying units,
sometimes USD" ruling. Findings below are grep+read-verified across `strategy-service`, `unified-api-contracts`,
`client-reporting-api`, `market-data-processing-service`, and codex. **Recommendation up front: the codebase already has
a ruled, partially-built design for exactly this (codex § "Share Class P&L" +
`settlement_service.py::convert_settlement_to_share_class`) — it just lives in the SAME dead/unwired Surface-A code this
whole issue doc is about, and the real gap is wiring it, not inventing a new mechanism.**

### Q1 — what "share class" concretely means, and a real SSOT contradiction found along the way

**Finding (flag — not blocking, but real):** there are **two structurally-different `ShareClass` enums in UAC sharing
one name**:

- `unified_api_contracts.canonical.crosscutting.share_class.ShareClass` — `{USDT, ETH, BTC}` + `SHARE_CLASS_BASE_ASSETS`
  (stablecoin-family grouping). Consumers: `internal/reporting/client_reporting.py`
  (`ClientPosition`/`ClientPnLEntry`/`ClientNAV`), `registry/client_share_classes.py`.
- `unified_api_contracts.internal.architecture_v2.enums.ShareClass` — 9 values:
  `{USDT, USDC, FDUSD, USD, GBP, EUR, ETH, BTC, SOL}`. Consumers: essentially all of strategy-service (`catalog_*.py`,
  `specs.py`, `portfolio_allocator/*`, `position/*`), imported via the `unified_api_contracts.internal` facade. **This
  is the one relevant to `carry_staked_basis`.**

These are two different Python classes with the same name and zero interop (`ShareClass.USDC` from one is not the
other's `ShareClass.USDC` — the `canonical` one doesn't even have a `USDC` member). Worth a ruling on whether they
should converge to one canonical enum or are intentionally scoped per consumer (client-reporting contracts vs.
strategy-service internals) with a doc note explaining why — as-is it's a live wrong-import risk.

**Answering the actual question:** ShareClass (the architecture_v2 one strategy-service uses) is **NOT** a
stablecoin-only concept — native-asset values already exist as first-class members and are already used as real share
classes elsewhere in this exact codebase:

- `unified_api_contracts/internal/domain/strategy_service/catalogue.py:58-61` —
  `_DEFAULT_SHARE_CLASSES = (ShareClass.BTC, ShareClass.ETH, ShareClass.USD, ShareClass.USDT)`, the strategy-instance
  catalogue's cross-product default set, docstring noting `ShareClass` "has more members (GBP/EUR/SOL/etc.)".
- `strategy_service/portfolio_allocator/share_class_fx.py` — `SHARE_CLASS_PERF_FEE_CONFIGS["ETH_FLAGSHIP"]`, a real
  ETH-denominated share class with its own HWM/perf-fee config.
- `strategy_service/portfolio_allocator/share_class_fx.py::ShareClassFxMatrix` — pure, tested (16 tests,
  `tests/unit/portfolio_allocator/test_share_class_fx.py`), converts NAV between **any** two `ShareClass` values via
  direct / inverse / triangulated (through USDT/USD hub) rates. **Not yet instantiated anywhere in production code**
  (only in tests) — the utility is real and correct but has no live rate feed wired to it yet.
- `strategy_service/portfolio_allocator/emitter.py::build_allocation_directive` (REAL, non-test code, lines 25-100) —
  **already stores an amount in BOTH the client's `reporting_currency` and the strategy's native `share_class` side by
  side**, on `StrategyEquityDirective.target_equity` (reporting currency) + `.target_equity_share_class` (native, via
  `ShareClassFxMatrix.convert_nav()`). This is a **live, shipped precedent** for the exact "figure out both" pattern the
  operator is asking for.

So: "share class" = the currency a client's capital / NAV / PnL is **denominated and reported in** — a
client-or-client-strategy-subscription-level property, not a description of what a position technically holds.
`catalog_staked_basis.py` only emits stablecoin share classes (`_STABLE_TO_SHARE_CLASS = {USDC, USDT, FDUSD}`, lines
133-138) because the archetype economically **starts** from stablecoin capital (swap→stake) — that is a
strategy-specific restriction of one catalog generator, not a structural limit of `ShareClass` itself. **"Native
underlying" does not need to be invented as a new enum value — `ShareClass.ETH`/`.SOL` already exist and are already
used as real share classes elsewhere.** What's missing is the conversion machinery being wired for PnL rows specifically
(Q3).

### Q2 — where `staked_notional` flows: confirmed QUOTE-only, end to end, no native quantity stored anywhere

Traced the full `carry_staked_basis` chain:

1. `catalog_staked_basis.py::_emit_staked_basis_slots` (lines 281-331) — `capital_budget` + `share_class` = a
   stablecoin, on `TargetInstanceSpec`.
2. `cli/handlers/paper_run_handler.py:1404` — `staked_notional = budget * stake_fraction`, `budget = r.deployed_capital`
   (quote/stablecoin units throughout).
3. `engine/backtest/benchmark_fills.py::_compute_swap_fill` (lines 288-307) — the stablecoin→native SWAP instruction
   **does** resolve a real spot/pool price (`_resolve_swap_benchmark`, lines 245-248: `snapshot.mid_price` or
   `snapshot.pool_mid_at_block`) — but `fill_units = instruction.in_amount` (the stablecoin amount going **in**); the
   resulting native OUT quantity is never computed or stored.
4. `engine/backtest/benchmark_fills.py::_resolve_yield_benchmark` (lines 251-260) — used for STAKE/LEND/BORROW/UNSTAKE —
   `fill_price` is **hardcoded to `Decimal("1")`**, docstring: "LEND/STAKE fills are 1:1 in units … the price for
   yield-bearing deposits is 1.0; the downstream P&L uses the rate separately." I.e. `staked_notional` (quote) is booked
   as if it were already a native 1:1 quantity — no real spot price applied at the STAKE step.
5. `engine/backtest/paper_run_transfers.py::build_paper_run_transfers` (lines 88-183) — the STAKE `LedgerRow` books
   `delta=staked_notional` (quote); `price` is never populated (stays `None`). Docstring line 27: "USDC→native→LST is
   modelled as the staked notional landing in the LST position" — an explicit modeling shortcut, not a real native
   quantity.
6. `engine/backtest/paper_run_passive.py::build_paper_run_passive` (lines 70-143) — today's `notional * bps/10000/365`
   (the banned form A2 replaces) is booked as `delta=accrued_amount` via UTL's `passive_ledger_row(...)`
   (`unified_trading_library/ledger/materialize.py:247-263`, `delta=accrued_amount`) — same quote-only convention. **The
   file's own docstring already flags this as deliberate** (lines 29-32, P3.4 correctness note): "a PASSIVE row's
   `delta` is a QUOTE cash-flow, NOT a base-asset qty … these rows MUST NOT be fed to `materialize_position_ledger`."

**Conclusion:** no native-unit (ETH/SOL/LST-token) quantity is computed or stored anywhere in the current
`carry_staked_basis` pipeline — it is quote-denominated end to end, by deliberate, documented design (not an oversight).
Supporting a native-unit view therefore needs exactly **one** new deterministic input: a spot/pool price for the native
asset at entry. Notably this is **not actually a new feed to build** — `_resolve_swap_benchmark` already computes this
real price at deploy time for the SWAP leg; it is simply computed and then discarded rather than threaded forward.
`LedgerRow.price` (`unified_api_contracts/canonical/crosscutting/ledger/_ledger_row.py:277-280`, "Quote-currency price
per unit at execution time") already exists on the schema and is unused on the STAKE row today — this is the natural
place to persist it, no new column required.

### Q3 — storage vs. display, and the design already exists in codex (unwired)

**The codex already specifies this exact feature**, § "Share Class P&L"
(`/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md:704-773`):

> P&L is converted from USD to the client's share class base currency. The FX attribution factor tracks the conversion
> difference, keeping trading P&L separate from currency exposure. … For `USDT`: no FX conversion applies. For
> `ETH`/`BTC`: every attribution factor is converted to the base currency at settlement time, and the FX component is
> separated as its own factor for transparency.

Backing table (`pnl-attribution.md:726-738`): `USDT`/`ETH`/`BTC` share classes, FX rate features
`fx_rate_eth_usd`/`fx_rate_btc_usd` sourced from `DefiFxRateAdapter` in MDPS. **This adapter is real, not aspirational**
— `market-data-processing-service/market_data_processing_service/app/adapters/defi/fx_rate_adapter.py` exists in the
live codebase. Codex names the implementing function:
`strategy-service/strategy_service/engine/core/settlement_service.py::convert_settlement_to_share_class`.

**Read it** (`engine/core/settlement_service.py:633-696`, verified real, present, correct-looking): it takes a
`pnl: dict[str, Decimal]` (USD amounts), a `share_class` string, and `fx_rates: dict[str, Decimal]`, and returns the
SAME dict with `{key}_share_class` keys added alongside every original `{key}` (plus
`total_pnl_usd`/`total_pnl_share_class`/`fx_rate_used`) — dividing every USD amount by the share class's FX rate for
`ETH`/`BTC`, or copying unchanged for `USDT`. **`grep` confirms zero callers anywhere in strategy-service** — this
function is dead code, exactly like the rest of "Surface A" this whole issue doc is about (`orchestrator.py`'s
`compute_pnl` + `settlement_service.py`'s index-ratio math were already identified as the correct-but-unwired reference
for the LENDING leg; this is the SAME file's correct-but-unwired reference for share-class conversion). **Note the
shipped function is simpler than the codex prose's illustrative "ETH share class example"** (lines 709-717,
`fx_factor`/`trading_factor` split isolating FX noise from trading return) — the real code does a flat
`val / fx_rate_at_read_time` divide, not an entry-vs-settlement fx-factor decomposition. If the operator wants the
richer entry/settlement-anchored split (isolating true native-asset return from the native asset's own USD-price drift —
see caveat below), that is MORE work than wiring the function as it stands today.

**Storage-vs-display verdict: DISPLAY (derive-on-read), not new stored fields.** Every existing pattern in this codebase
for "same number, two currencies" is a computed conversion, not duplicated storage on the per-event row:
`ShareClassFxMatrix.convert_nav()`, `emitter.py::_convert_to_native`, `settlement_service.py`'s
`convert_settlement_to_share_class`, and — even where a dual-field pattern DOES exist on a stored record
(`ClientNAV.nav_usd` + `.nav_in_share_class`, `client_reporting.py:80-93`) — the conversion is applied as a computation
over an already-canonical USD number, not by storing two independently-computed amounts. (Caveat:
`client-reporting-api/api/routes/attribution.py::_nav_from_rows` currently sets `nav_in_share_class = nav_usd` verbatim
— a no-op stub; the real FX wiring isn't live yet, only the schema + the pure conversion utilities exist and are
tested.) This also matches the codebase's general philosophy of not duplicating derivable state — e.g.
`PnLAttribution.strategy_alpha_total`/`.execution_alpha_total` are explicitly commented "DERIVED — never stored"
(`unified_api_contracts/internal/risk.py:966-987`). **`PnLAttributionRow` needs NO new field for this** — no
`share_class` column, no second `amount`. Keep it storing exactly what it stores today (a single signed USD/quote
`amount`), and apply `convert_settlement_to_share_class`-equivalent logic at the reporting layer, on read, per client's
subscribed share class.

**One real economic caveat (do not conflate these two, they are different NUMBERS):**

- **(A) Currency-preference view** — the shipped `convert_settlement_to_share_class` behavior: divide the
  already-computed USD PnL by the CURRENT (settlement-time) ETH/BTC/SOL spot rate. This is what "give me my USD PnL in
  ETH terms today" means, and is what the operator's phrasing most directly maps to (a share-class reporting preference
  over an already-computed number).
- **(B) True native-asset-return view** — Hard Rule #5's literal `holding × (exchange_rate_now/exchange_rate_prev − 1)`,
  anchored to a FIXED native quantity established once at stake-entry. Over a multi-day window, (A) and (B) diverge
  whenever ETH's/SOL's own USD price moves, because (A) re-prices the USD number at TODAY's rate (mixing the LST's real
  staking yield with ETH's own FX/price drift), while (B) isolates the staking-index appreciation from the native
  asset's own price movement (economically the "clean" staking return). The codex's illustrative
  `fx_factor`/`trading_factor` split (lines 713-716) is precisely how you'd reconcile these — `trading_factor` ≈ (B),
  `fx_factor` = the residual (A)−(B) — but that split is NOT what the shipped `convert_settlement_to_share_class`
  function actually computes today (see above). Building the wrong one produces a subtly-wrong client-facing number,
  which is exactly what this doc's OPERATOR GATE exists to prevent — **flagged below for an explicit ruling.**

### Q4 — scope: this is a client-reporting-layer question, not staking-leg-specific

Every artefact above points the same way: `ClientNAV`/`ClientPnLEntry` carry `share_class` as ONE tag for the WHOLE
per-client(-period) record, not per-factor or per-leg (`client_reporting.py:37-93`);
`AllocationDirective.reporting_currency` applies at the client/allocator level
(`unified_api_contracts/internal/architecture_v2/schemas.py:390-403`); `PnLAttributionRow` carries no currency field at
all today. The operator's framing ("depending on the share class, sometimes we want ETH-underlying units, sometimes
USD") reads as a general client-reporting requirement that surfaced while reviewing the STAKING leg, not a request to
make `carry_staked_basis`'s accrual formula itself unit-switchable. **Recommend scoping the real build to the
client-reporting layer** (client-reporting-api's NAV/PnL/attribution routes, wiring
`ShareClassFxMatrix`/`convert_settlement_to_share_class`-equivalent logic for real against a live
`fx_rate_eth_usd`/`fx_rate_btc_usd`/(new `fx_rate_sol_usd`?) feed), while the STAKING leg's A2 build (this doc's main
thread) continues to emit ONE canonical quote-denominated number exactly as E4 already ruled — no accrual-formula
branching by share class inside strategy-service's engine. The FUNDING leg (E1, parallel session) is equally unaffected
— both legs feed the same canonical `PnLAttributionRow`/`LedgerRow` amount, and dual-unit viewing would apply uniformly
to the whole row-set at the reporting layer, not per-leg.

### Smallest correct increment (answers "how to build it without a wasted rebuild")

1. **No schema change** to `PnLAttributionRow` or the passive `LedgerRow` — keep the canonical stored amount in quote,
   consistent with E4's ruling and the codebase's existing single-canonical-unit convention.
2. **Wire `ShareClassFxMatrix` to a real rate feed** (MDPS `DefiFxRateAdapter`'s `fx_rate_eth_usd`/`fx_rate_btc_usd`,
   extend for `fx_rate_sol_usd` if SOL share class is ever offered) — currently a correct, tested, but production-dark
   utility.
3. **Un-orphan `convert_settlement_to_share_class`** (or a corrected reimplementation of it) as the client-reporting
   read-time conversion step, replacing the `client-reporting-api::_nav_from_rows` no-op stub
   (`nav_in_share_class = nav_usd`) with a real per-client-share-class conversion. This is the direct, minimum-diff way
   to satisfy "figure out both" — ANY client's share class (not just ETH), for ALL of NAV/PnL/attribution, with zero
   engine-side change.
4. If (B) (true native-asset-return, FX-noise-isolated) is separately wanted for the STAKING leg specifically: persist
   the ONE per-position entry-day spot price already computed and discarded in `_resolve_swap_benchmark` (step 3 of Q2)
   into the existing, currently-`None` `LedgerRow.price` field on the STAKE transfer row — a single scalar per position,
   not a new per-accrual-row field, from which `native_yield_day_d = quote_yield_day_d / entry_spot_price` is an exact,
   deterministic derivation (no per-day spot lookups needed).
5. Neither (2)/(3) nor (4) block or duplicate the A2 STAKING/FUNDING wiring (E1/E4) — they are additive, reporting/
   conversion-layer work that can land before, after, or alongside A2.

### Needs an explicit operator ruling (flagging, not picking)

1. **(A) vs (B) above** — does "ETH-underlying units" mean (A) a currency-preference view of the already-computed USD
   PnL at today's rate (matches the ALREADY-SHIPPED-but-dead `convert_settlement_to_share_class`, and "share class" as
   used everywhere else in this codebase), or (B) a genuinely different FX-noise-isolated "true native staking return"
   metric (matches Hard Rule #5's literal `holding`-based formula, needs the one new per-position entry-price anchor
   from item 4 above)? These visibly disagree over any multi-day window where ETH/SOL's own USD price moves — this is a
   genuine new fork, not an implementation detail, and shipping the wrong one is a subtly-wrong client-facing PnL
   number.
2. **The two competing `ShareClass` enums** (`canonical.crosscutting.share_class.ShareClass` `{USDT,ETH,BTC}` vs.
   `internal.architecture_v2.enums.ShareClass` — 9 values) — same class name, structurally incompatible, used by
   disjoint consumer sets. Worth a ruling on whether they should converge to one canonical enum, or are intentionally
   scoped with a doc note explaining the split (as-is, a live wrong-import risk for any future cross-cutting
   client-reporting/strategy-service work).

**This investigation does not reopen E1 (parallel session, funding-leg data-source mapping) or E4 (row-set,
CONFIRMED).**

**🟡 Timeline note (added on reconciliation-pass):** the STAKING leg's engine-side wiring actually **shipped BEFORE this
investigation ran** (`strategy-service@e93902d8`, "PROGRESS 2026-07-23 — STAKING leg SHIPPED" above, same date, earlier
in document order) — the "do not wire the STAKING leg with a single hardcoded unit convention" gate stated earlier in
this doc (`## Updated gating`) was technically crossed before E2 formally closed. This investigation's own
recommendation (§ "Smallest correct increment", item 1) **retroactively validates that choice**: keep the engine-side
stored amount single-canonical-quote-denominated, consistent with E4's ruling — no accrual-formula branching by share
class inside strategy-service's engine. So **E2 is NOT open against the already-shipped STAKING leg accrual formula** —
that part is settled, matches what shipped. What remains genuinely open (pending the operator ruling in § "Needs an
explicit operator ruling" above) is the **reporting-layer dual-unit VIEWING work** (items 2-4 of the "Smallest correct
increment" list: wiring `ShareClassFxMatrix` to a real rate feed, un-orphaning `convert_settlement_to_share_class`, and
the (A)-vs-(B) semantics ruling) — additive work that does not require touching the STAKING leg's already-shipped engine
code.

## Todos

- [ ] [CODE] P1. **RULED 2026-07-29 (operator direct answer) — Option B.** "ETH-underlying units" means a genuinely
      different, FX-noise-isolated "true native staking return" metric matching Hard Rule #5's literal `holding`-based
      formula — NOT a currency-preference view of the already-computed USD PnL. This needs the one new per-position
      entry-price anchor identified in item 4 of "Smallest correct increment" above; it disagrees with the
      already-shipped `convert_settlement_to_share_class` view over any multi-day window where ETH/SOL's own USD price
      moves, so building it is real new work, not a wiring exercise. **Not yet started.** (repo: strategy-service)
- [x] ✅ [CODE] P1. **RULED 2026-07-29 (operator direct answer) — converge to one enum. DONE 2026-07-30.** Converged
      `unified_api_contracts.canonical.crosscutting.share_class.ShareClass` (`{USDT,ETH,BTC}`) and
      `unified_api_contracts.internal.architecture_v2.enums.ShareClass` (9 values) to ONE canonical enum object —
      `unified-api-contracts@4df243f7`, `quality-gates.sh` green, shipped via quickmerge. One deliberate deviation from
      the ruling's literal module choice: kept `canonical.crosscutting.share_class.ShareClass` as the actual definition
      (expanded 3→9 values) and made `internal.architecture_v2.enums.ShareClass` a re-export
      (`from unified_api_contracts.canonical.crosscutting.share_class import ShareClass as ShareClass`) rather than the
      reverse — `canonical` is the layer other internal types already build on (the natural dependency direction), and
      this way **zero consumer files needed touching** (`client_reporting.py`, `registry/client_share_classes.py`
      already imported from `canonical.crosscutting`, so they picked up the 9 values for free). Verified live, in
      -process: `unified_api_contracts.ShareClass`, `internal.architecture_v2.enums.ShareClass`, and
      `internal.ShareClass` are now all the identical class object (`is` comparison), all 9 members present,
      `SHARE_CLASS_BASE_ASSETS` keys match. Confirmed exactly one `class ShareClass(StrEnum)` definition remains
      repo-wide (`grep`). Full completion — no partial migration, duplicate deleted. (repo: unified-api-contracts)

## Progress Log addendum

- **na-eligibility-audit 2026-08-01**: KEEP-NA valid — the sole remaining open checkbox (Option B true-native-staking-
  return metric) is a money-path change to client-facing NAV/PnL numbers in the determinism-critical spine
  (`paper_run_passive.py`/`paper_run_attribution.py`), explicitly under this doc's own OPERATOR GATE — inherently
  judgment/correctness-sensitive engineering, not a bare bounded/deterministic worker task, consistent with every prior
  accrual-formula change on this doc requiring a 3-lens money-path review. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-03**: KEEP-NA valid — re-confirmed independently, no content change since 2026-08-01.
  The sole open checkbox (Option B) is still unstarted and still explicitly under this doc's own OPERATOR GATE. Doc
  stays `assigned_vm: NA`.
- **context-scout 2026-08-03**: populated/refreshed context_scope (6 entries) — added
  `strategy-service/strategy_service/engine/backtest/benchmark_fills.py`, the file that computes and currently discards
  the entry-spot price the still-open Option B todo needs to persist for the true-native-return metric.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=defi, dispatch agt-e00d37): KEEP-NA valid — re-confirmed independently,
  no content change since 2026-08-03 (only a context-scout metadata touch). Corroborated by 3 independent sources total:
  this doc's own 2026-08-01/08-03 audits PLUS an ACTIVE `assigned_vm: planning` plan
  (`defi_satellite_ao_ dispatch_batch6_2026_07_30.md`) that explicitly names this exact doc+item under its own
  non-batchable/human-only section (money-path, needs 3-lens review + explicit go-ahead before dispatch). Sole open
  checkbox (Option B: FX-noise-isolated native-staking-return metric) remains judgment-sensitive HOW-to-build-safely
  work on live client NAV — the WHAT is operator-ruled but the HOW still needs the same money-path review every prior
  accrual-formula leg in this doc required. Incidental, not actioned: 2 untracked prose-only follow-on items (wire
  `ShareClassFxMatrix` to a real rate feed; un-orphan `convert_settlement_to_share_class`) — would also land NA if
  tracked given the same client-facing-NAV sensitivity. Doc stays `assigned_vm: NA`.
- **round11-sweep 2026-08-09** (defi tranche, satellite-extraction + RECLASSIFY re-check): re-read end to end (1 open
  `[CODE] P1` item at entry: Option B, the FX-noise-isolated true-native-staking-return metric). Checked against every
  accumulated round11 precedent (IAM self-service, D16 all-repos, S5.1 tiering, plan-destination-defaults-AO-dispatched,
  escalation-N=3-days, reversibility-qualified deletes, Option B retired, GSM secret + 5 Slack webhooks now existing) —
  none apply, and note this doc's own "Option B" (the operator-ruled true-native-staking-return metric, 2026-07-29) is a
  different "Option B" from the round11-precedent one and is NOT retired — it is operator-ruled WHAT-to-build, still
  gated on a HOW-to-build-safely money-path review (per the standing OPERATOR GATE this whole doc is filed under,
  changes to live client NAV/PnL). Not eligible for satellite-extraction — a client-facing NAV correctness change is
  inherently a judgment/3-lens-review task, not a bare mechanical build. Doc stays `assigned_vm: NA` (KEEP-NA valid,
  round11).
- **na-eligibility-audit 2026-08-16** [body-hash:1c8918d7c9daea13]: KEEP-NA, valid — This is a long-running, heavily-audited money-path issue doc (interest-PnL accrual in the determinism-critical client-reporting spine) that has already shipped three legs (FUNDING/E1, STAKING/E4/E2-partial, LENDING row-set drop) under an explicit standing '## OPERATOR GATE' requiring a 3-lens money-path review before any accrual/NAV change ships.

- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries).
- **na-eligibility-audit 2026-08-17 (defi tranche, dispatch agt-f4fef7)**: KEEP-NA, valid — re-confirmed
  independently; no substantive content change since the 2026-08-16 verdict (context-scout metadata touch only).
  Still under the standing `## OPERATOR GATE` (3-lens money-path review required before any accrual/NAV change
  ships) — not re-litigated. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries).

- **2026-08-20 (line-cap remediation)**: split the build-ready "true native staking return" (Option B) implementation
  spec out to `/plans/active/issues/pnl_true_native_staking_return_spec_2026_08_20.md` — this doc hit its 1000-line
  hard cap. Spec is SPEC ONLY, not yet reviewed/approved, stays under this doc's standing OPERATOR GATE. The open
  todo it documents (line ~774, Option B) stays tracked HERE, not in the spec doc.
- **na-eligibility-audit 2026-08-21** (defi tranche, wave 2): KEEP-NA, valid — re-confirmed; sole open item (Option B, the FX-noise-isolated true-native-staking-return metric) remains under the doc's own standing `## OPERATOR GATE` (3-lens money-path review required before any accrual/NAV change ships) — the implementation spec was split out 2026-08-20 to `pnl_true_native_staking_return_spec_2026_08_20.md` for line-cap reasons, but the open todo and its gate stay tracked here. Doc stays `assigned_vm: NA`.
