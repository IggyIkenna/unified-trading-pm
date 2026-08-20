---
doc_type: issue
title: True native staking return -- build-ready spec (Option B, NOT YET reviewed/approved)
summary: >-
  Split out of pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md (line-cap remediation, that doc hit
  1066/1000 lines). Build-ready implementation spec for the remaining open [CODE] P1 todo there (Option B, operator-
  ruled WHAT on 2026-07-29) -- a FX-noise-isolated "true native staking return" metric. SPEC ONLY, no code written;
  stays under the parent doc's standing OPERATOR GATE (3-lens money-path review required before any accrual/NAV
  change ships).
status: open
nature: issue
asset_group: [defi]
stage: [strategy]
repos: [strategy-service]
scope: [engineer, admin]
tags: [pnl-correctness, interest-accrual, determinism-spine, money-path, defi, operator-gate, spec]
related:
  [
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
  ]
created: 2026-08-20
author: unknown
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend
drift_direction: advance-code
depends_on: [pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21]
source: >-
  Split from pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md 2026-08-20, line-cap remediation.
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    strategy-service/strategy_service/engine/backtest/paper_run_passive.py,
    strategy-service/strategy_service/engine/backtest/paper_run_attribution.py,
  ]
---

# True native staking return -- build-ready spec (Option B, NOT YET reviewed/approved)

Build-ready implementation spec for the remaining open `[CODE] P1` todo (Option B, "true native staking return" —
operator-ruled WHAT on 2026-07-29). **This section is a SPEC ONLY** — no strategy-service code was written or
modified to produce it, and the todo above stays unchecked. It exists so the standing `## OPERATOR GATE`'s 3-lens
money-path review has a concrete, code-grounded artefact to review instead of starting from the todo's one-line
description. Written by reading the real determinism-spine producers (`paper_run_passive.py`,
`paper_run_attribution.py`, `benchmark_fills.py`, `paper_run_transfers.py`, `canonical_lst_yields_index_provider.py`)
and the codex Hard Rule this metric must match — nothing below is invented shape.

### 1. The exact formula

Codex Hard Rule #5 (`/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md:113-121`, "Staking yield:
wrapped (price-delta) vs rebasing (balance-delta)"), wrapped/non-rebasing row:

```
CARRY_BASE = holding × (exchange_rate_now / exchange_rate_prev - 1)
```

`holding` is explicitly the **native LST/underlying quantity** (a fixed token count), not a USD notional. This is
the metric Option B asks for. It is a genuinely different NUMBER from the codex's own adjacent "Share Class P&L"
section (`pnl-attribution.md:704-717`), which this doc's own E2 investigation (§ "Q3 — storage vs display", "One
real economic caveat") already worked out algebraically:

```
# already-shipped, currently-dead convert_settlement_to_share_class (view A — currency preference)
pnl_eth_at_settlement = pnl_usd / eth_price_at_SETTLEMENT      # today's/read-time spot rate

# Option B (view B — true native return, Hard Rule #5's literal form)
fx_factor       = pnl_usd × (1/eth_price_settlement - 1/eth_price_trade)
trading_factor  = pnl_usd / eth_price_TRADE                    # = holding × (exchange_rate_now/prev - 1)
total_pnl_eth   = trading_factor + fx_factor                   # = pnl_usd / eth_price_settlement  (reconciles to view A)
```

`trading_factor` (divide by the ENTRY/trade-day price) is algebraically identical to `holding × ratio` because
`holding = staked_notional_usd_at_entry / eth_price_trade` is a fixed quantity for the life of the position — so
`holding × ratio = (staked_notional_usd / eth_price_trade) × ratio = (staked_notional_usd × ratio) / eth_price_trade
= quote_yield / eth_price_trade`. The build below computes it via `quote_yield / entry_price` (dividing the
already-shipped quote-denominated CARRY/STAKING_REWARD accrual by one fixed per-position entry price), which is the
exact same number as the literal `holding`-based form, without needing to carry a separate native-quantity field —
consistent with this doc's own E4/Q3 rulings against inventing new stored quantities where an existing one derives
it. `fx_factor` is the residual — the part `total_pnl_eth` (view A) picks up that `trading_factor` (view B)
deliberately excludes.

### 2. The new per-position entry-price anchor

**What it is**: the ONE spot/pool price of the native asset (ETH, SOL, …) in the position's quote currency, at the
moment the `carry_staked_basis` position's stablecoin→native SWAP fills — i.e. the entry price the position's
`holding` is established at. Per-position, per-strategy-instance, computed exactly ONCE (not per day).

**Where it already exists, uncaptured**: `strategy_service/engine/backtest/benchmark_fills.py::_resolve_swap_benchmark`
(line 262) resolves this exact price for the SWAP instruction — `snapshot.pool_mid_at_block` when available, else
`snapshot.mid_price` — and `_compute_swap_fill` (line 305) stamps it onto the returned `BenchmarkFillRecord.fill_price`
(line 321). That record lands in `GroupBBacktestResult.fills` (`strategy_service/engine/backtest/runner.py:91`), part
of `StrategyReplay.result` — so **the number already exists in the replay's own output on every paper AND batch run**;
today it is read (line 321) and then never extracted for this purpose. No new price feed, no new provider class (unlike
the FUNDING/STAKING legs, which each needed a new `Canonical*Provider`) — this is pure plumbing of an already-computed,
already-deterministic value.

**How it gets threaded (mirrors the FUNDING/STAKING leg pattern exactly — additive, `None`-default, scoped)**:

1. New field on `StrategyReplay` (`strategy_service/cli/handlers/paper_run_handler.py:963`):
   `entry_native_spot_price: Decimal | None = None` — same shape/doc-comment convention as the existing
   `funding_rates_by_day`/`staking_index_by_day` fields immediately above it.
2. Resolved ONCE inside `replay_carry_strategy` (`paper_run_handler.py:2090`), scoped to
   `CARRY_STAKED_BASIS`/`CARRY_STAKED_BASIS_DATED` (the same two archetypes `staking_index_by_day` is already scoped
   to, `paper_run_handler.py:2465`): filter `result.fills` for the `InstructionActionV2.SWAP` fill whose
   `instrument_key` matches the deploy leg (`spot_venue:SWAP:<in_asset>-><out_asset>`, per
   `_canonical_instrument_key` in `benchmark_fills.py`), take its `fill_price`. Because this reads the SAME
   `GroupBBacktestResult` a batch rerun independently re-derives from the SAME immutable GCS partition, paper and
   batch resolve the IDENTICAL price — ε=0 holds by construction, no new determinism proof mechanism needed beyond
   what already covers `fills`.
3. **Persisted** (not just held in-memory) onto the existing, currently-always-`None` `LedgerRow.price` field
   (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/ledger/_ledger_row.py:265-267`, "Quote-currency
   price per unit at execution time") on the STAKE leg row `paper_run_transfers.py::build_paper_run_transfers` emits
   (line 88, STAKE leg at line 153) — `transfer_ledger_row()`
   (`unified_trading_library/ledger/materialize.py:287`) already accepts an optional `price` kwarg that this call site
   simply never passes today. This gives every downstream reader (client-reporting-api, an audit script, a future
   batch rerun that only has the transfer ledger and not a live `StrategyReplay`) a durable, queryable anchor per
   position — no new column, no new ledger type.
4. `entry_native_spot_price` is ALSO threaded directly into `build_paper_run_passive`/`build_paper_run_attribution`
   (or a new sibling read-path — see § "Files to change" below) alongside the existing `staking_index_by_day` param,
   so the native-return number can be computed/exposed without a second GCS/ledger read.

### 3. How this diverges from `convert_settlement_to_share_class`, and why both coexist

Two different QUESTIONS, both legitimate, both already named as distinct in this doc's own E2 investigation
(§ "One real economic caveat", lines 688-702) — repeated here as the spec's explicit framing so a reviewer does not
conflate them:

| | `convert_settlement_to_share_class` (shipped, currently dead code) | Option B (this spec) |
| --- | --- | --- |
| Question answered | "What's my already-computed USD PnL worth in ETH terms **today**?" | "What did the staking position **actually earn**, isolated from ETH's own USD price movement?" |
| Divisor | `eth_price_at_settlement` (current/read-time spot) | `eth_price_at_trade` (fixed, position-entry spot) |
| Changes on every read as ETH/USD moves | Yes — a currency-preference VIEW, recomputed live | No — anchored once at entry, stable per position |
| Mixes in ETH's own FX/price drift | Yes (that's the point — "what's my number worth in ETH right now") | No — deliberately isolates it out |
| Where it lives | `strategy-service/strategy_service/engine/core/settlement_service.py:633-696`, orphaned (zero callers) | New — see § "Files to change" |
| Storage model | DISPLAY / derive-on-read over the existing USD `PnLAttributionRow`/`LedgerRow` amount — **no schema change** | Same DISPLAY / derive-on-read model, **plus** the one new persisted `LedgerRow.price` anchor (§2) |

Both coexist because they are different, both-correct answers to different client questions — a client asking "show
me my ETH-share-class NAV today" wants view A; a client (or an internal correctness audit) asking "how much did the
staking leg itself yield, in real ETH terms, over this window" wants view B. Per this doc's own already-ruled Q3/Q4
(storage-vs-display verdict, lines 673-719): **neither view gets a new column on `PnLAttributionRow` or the passive
`LedgerRow`** — both are computed at read time over the existing canonical USD amount. View A's divisor is a live FX
rate feed (`fx_rate_eth_usd` from MDPS `DefiFxRateAdapter`); view B's divisor is the ONE persisted `LedgerRow.price`
value from §2. They can ship independently, in either order, without touching each other's code path.

### 4. Files to change (function-level — no line-level diff, this is a spec)

Repo: `strategy-service` only, except the client-reporting-api item at the bottom (optional for a first increment —
see § "Definition of done").

1. **`strategy_service/cli/handlers/paper_run_handler.py`**
   - `StrategyReplay` (dataclass, ~line 963): add `entry_native_spot_price: Decimal | None = None` field, doc-commented
     like the sibling `staking_index_by_day` field immediately above it.
   - `replay_carry_strategy` (~line 2090): after the existing `staking_index_by_day` resolution block (~line 2465,
     scoped to `CARRY_STAKED_BASIS`/`CARRY_STAKED_BASIS_DATED`), add a small helper call that extracts the deploy
     SWAP fill's `fill_price` from `result.fills` (see §2 step 2) and sets `entry_native_spot_price` on the returned
     `StrategyReplay`. Honest-absence: no matching SWAP fill in `result.fills` (e.g. an archetype config variant with
     no swap leg) → `None`, logged — never a fabricated/estimated price.
   - The `build_paper_run_transfers(...)` call site (~line 3268): add `price=r.entry_native_spot_price` to the STAKE
     leg's row-building call (the existing function already threads a single `price` per call — check whether the
     STAKE leg needs its own dedicated call or whether `build_paper_run_transfers` needs a per-leg price param; today
     it takes one `price`-less call for all 4 legs, so this likely needs a signature change — a new optional
     `stake_price: Decimal | None = None` kwarg specifically for the STAKE leg's `transfer_ledger_row(..., price=...)`
     call, leaving the other 3 legs' `price=None` unchanged).
   - The `emit_paper_run_attribution(...)` / passive call sites (~lines 3254, and the mirrored db_spec path ~3142):
     thread `entry_native_spot_price=r.entry_native_spot_price` alongside the existing `staking_index_by_day=r.staking_index_by_day`
     kwarg, IF the native-return number is computed inside the producer (see next item) rather than purely at the
     reporting layer.
2. **`strategy_service/engine/backtest/paper_run_passive.py`** / **`paper_run_attribution.py`**
   - Decision point for the reviewer (flagging, not picking — mirrors this doc's own pattern of flagging real forks):
     compute the native-return number INSIDE these producers (a new optional output alongside the existing quote
     `accrued_amount`/`carry_amount`, e.g. a sibling `PnLAttributionRow`-adjacent value or a parallel lightweight
     record), OR keep these producers untouched and do the division purely at the reporting layer (§3's DISPLAY
     model) using the already-quote-denominated `STAKING_REWARD`/`CARRY` rows these producers already emit, joined
     against the `entry_native_spot_price` persisted on the STAKE `LedgerRow` (§2 step 3). **The reporting-layer-only
     option requires ZERO changes to `paper_run_passive.py`/`paper_run_attribution.py`** — recommended smallest
     increment, consistent with Q3/Q4's "no schema change" ruling and item 4 of this doc's own earlier "Smallest
     correct increment" list.
3. **`strategy_service/engine/backtest/paper_run_transfers.py`**
   - `build_paper_run_transfers` (line 88): add the `stake_price: Decimal | None = None` kwarg (see item 1 above),
     pass it through to the STAKE leg's `transfer_ledger_row(..., price=stake_price)` call (line 153's leg tuple
     needs a price slot added to its per-leg tuple shape, or a small post-loop patch for just that one leg).
4. **`strategy_service/cli/handlers/batch_rerun.py`**
   - Verify (not yet confirmed in this spec pass) whether batch_rerun re-derives the TRANSFER ledger at all — this
     doc's own STAKING-leg progress note (line ~458) states batch_rerun "does not call the attribution producer at
     all — only the passive tape", and makes no mention of calling `build_paper_run_transfers`. If batch never
     rebuilds transfers, `entry_native_spot_price` only needs threading into whatever batch DOES call (the passive
     re-derivation, if item 2 above puts the computation there) — confirm this before assuming a transfer-ledger
     parity test is even applicable.
5. **New read-time helper (recommended location, TBD by reviewer)**: a small, pure function —
   `native_staking_return(quote_amount: Decimal, entry_native_spot_price: Decimal) -> Decimal` — living either
   alongside `index_ratio_accrual` (`strategy_service/engine/backtest/index_ratio_accrual.py`, the existing pure-math
   module this whole doc's accrual fixes have used as the shared primitive home) or in a new small module if the
   reviewer prefers keeping accrual math and reporting-conversion math separate. Guard `entry_native_spot_price > 0`
   → `None`/honest-absence, never a divide-by-zero or a silent zero.
6. **`client-reporting-api/client_reporting_api/api/routes/attribution.py`** (optional for a first increment; needed
   for a client-visible number) — a NEW route or field alongside the existing `_nav_from_rows` (line 130,
   `nav_in_share_class` at line 149, the currently-a-no-op share-class stub view A already occupies) — do NOT reuse
   or overload `nav_in_share_class` for view B's number, they are different questions (§3) and conflating them in one
   field would be exactly the "subtly-wrong client-facing number" this doc's OPERATOR GATE exists to prevent.

### 5. Money-path / NAV-correctness risks a reviewer should scrutinize

- **Wrong SWAP fill picked as the entry price.** A position may have more than one SWAP-shaped fill over its life
  (e.g. a rebalance, a partial top-up) — the extraction in §2 step 2 MUST anchor to the FIRST/deploy-day swap only
  (matching `holding`'s "fixed at entry" semantics), never the most-recent or a re-resolved one. Picking a later
  price silently converts this into a rolling-window view (indistinguishable from a subtly-broken view A) rather
  than the fixed-anchor view B Hard Rule #5 specifies.
- **`entry_native_spot_price` is `None` (honest absence) for a real position** (e.g. no matching SWAP fill found —
  config variance, or a partial-fill edge case) — the reporting layer MUST render this as an explicit gap (matching
  this doc's own house style for `lst_yields`/`aave_borrow_index` gaps: a visible log/flag), never silently fall back
  to view A's number under the view-B label. Two economically different numbers must never share a code path that
  can silently substitute one for the other.
- **Confusing this with a currency-PREFERENCE toggle.** A UI/reporting consumer that lets a client "view in ETH" must
  not wire that toggle to view B by accident — view B answers a narrower, correctness-scoped question (isolated
  staking-yield-only economics) and will NOT reconcile to the client's actual USD NAV (by design — the whole point is
  excluding FX drift). Shipping view B where a client expects "my NAV in ETH" (view A) misstates what the client's
  wallet is actually worth today.
- **Aggregation across multiple staking positions / top-ups.** If a strategy instance stakes in tranches (multiple
  deploy events, each at a different entry price), a single scalar `entry_native_spot_price` per `StrategyReplay` is
  only correct for a single-deploy position. Confirm `carry_staked_basis`'s current catalogue/config shape is
  single-deploy-per-instance (this spec assumes it is, based on the reviewed code, but this should be an explicit
  reviewer check) before generalizing — a multi-tranche position needs a weighted-average or per-tranche entry price,
  not the naive single scalar this spec's smallest increment assumes.
- **Determinism drift if the extraction logic ever reads something OTHER than `result.fills`.** The entire ε=0
  argument in §2 rests on both paper and batch deriving `entry_native_spot_price` from the SAME
  `GroupBBacktestResult.fills` list. Any future edit that has batch resolve this price independently (e.g. a fresh
  GCS tick read at rerun time instead of reading the ALREADY-derived `result.fills`) reintroduces exactly the
  un-pinned-second-model failure mode this doc's own "Why NOT wire compute_pnl" section (lines 95-106) already
  rejected once for the LENDING leg.
- **Sign/direction correctness on `fx_factor` vs `trading_factor` if the fuller codex split (not just the bare
  `trading_factor` number) is ever surfaced to clients** — verify against the codex's own worked example
  (`pnl-attribution.md:709-717`) before shipping any UI that shows both factors side by side; a sign error here
  produces a plausible-looking but wrong number, the exact failure class this doc's "Lessons" section (line ~305)
  already flags as worse than a gated pause.

### 6. Definition of done (for a reviewer to check the eventual implementation against)

- `entry_native_spot_price` resolves to the correct entry-day SWAP fill price for a real `carry_staked_basis`
      position, verified against a real prod/paper run's actual `result.fills` (not a synthetic fixture only).
- The resolution reads ONLY `result.fills` (already-computed, already-deterministic) — no new GCS read, no new
      `Canonical*Provider` class, no new external data source.
- Paper and a same-window batch rerun of the SAME position resolve the IDENTICAL `entry_native_spot_price` — a
      parity test added at the same layer as the existing `staking_index_by_day`/`funding_rates_by_day` parity tests
      (mirroring `test_paper_run_passive.py`/`test_paper_run_attribution.py`'s existing pattern).
- A position with no matching SWAP fill resolves to `None` + a visible log — never a fabricated price, never a
      silent fallback to view A's settlement-time rate.
- `LedgerRow.price` on the STAKE transfer row is populated for `carry_staked_basis`/`carry_staked_basis_dated`
      ONLY (`price` stays `None` for every other archetype's transfer rows, and for every OTHER leg — DEPOSIT/
      TRANSFER/COLLATERAL_POSTED — of the SAME strategy's transfer rows) — zero behavior change outside this one
      leg, matching every prior leg-fix in this doc (FUNDING, STAKING, LENDING row-drop).
- The native-return number (§1's `trading_factor` / `holding × ratio`) is verified, on a real window, to
      NUMERICALLY DIVERGE from `convert_settlement_to_share_class`'s view-A number whenever ETH/SOL's own USD price
      moved during the window, and to MATCH it when the price was flat (both algebraic claims in §1 and §3 confirmed
      against real numbers, not just asserted from the formula).
- No new field added to `PnLAttributionRow` or the passive `LedgerRow` schema (per this doc's own Q3/Q4 ruling) —
      the ONE new persisted value is `LedgerRow.price` on the STAKE leg, an EXISTING field.
- View A (`convert_settlement_to_share_class`) and view B (this spec) are exposed as visibly DIFFERENT
      client-reporting-api fields/routes, never merged into or aliased against `nav_in_share_class`.
- Full `quality-gates.sh` green (not `--no-fix` skip) on the actual build, including a determinism/passive-row
      parity check per this doc's own standing requirement ("Green determinism tests do NOT prove interest
      correctness" — § "Build-ready spec for option A", item 5).
- 3-lens money-path review (correctness / determinism / honest-absence) explicitly signed off in this doc's
      Progress Log, in the same style as the FUNDING (2026-07-23) and STAKING (2026-07-23) leg entries above, BEFORE
      quickmerge — per the standing `## OPERATOR GATE`.
- This section's todo (line ~774, `[CODE] P1`, Option B) is flipped to `[x]` with the shipped commit sha(s) and
      evidence, in the SAME turn as the ship, per the workspace's commit-push-flip rule — not before.
