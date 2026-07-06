---
doc_type: issue
title:
  WSFeedConnector Phase-3.5 rollout gap — 73 unregistered venues account for the blocked-not-registered smoke-matrix
  cells
summary: |
  Per-venue WSFeedConnector registration audit surfaced by
  `foundation_gates_and_capture_to_100_2026_07_06` task 010. **Finding**: 0 built-but-unregistered venues (the C5
  handler-audit class of bug does NOT recur at the venue level); **73 genuinely-not-built venues** — Phase-3.5 rollout
  is complete for 31/(31+73) canonical batch venues (~30%). The 73 map cleanly to the smoke-matrix
  `blocked-not-registered` cell counts (cefi 104 · defi 1225 · sports 70 · tradfi 40). Filed as an ordered follow-up
  so each remaining venue is either wired to a WSFeedConnector (with a regression test) or classified
  `BLOCKED-CREDENTIALS` / `BLOCKED-OPERATOR-DECISION` / `BATCH-ONLY-BY-DESIGN`.
status: open
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [live-pipeline, wsfeedconnector, phase-3-5, per-venue-rollout, handler-audit-followup]
related:
  [
    foundation_gates_and_capture_to_100_2026_07_06.md,
    instruments_completion_tracker_2026_07_06.md,
    live_pipeline_mtds_mdps_features_2026_05_08.md,
    ../../codex/02-data/live-data-persistence-and-event-log.md,
    ../../codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-06
last_updated: 2026-07-06
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role: data_engineering
drift_direction: advance-code
source:
  [
    e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py#L280,
    market-tick-data-service/market_tick_data_service/live/connectors/__init__.py#L34,
    market-tick-data-service/market_tick_data_service/cli/handlers/websocket_streaming_handler.py#L54,
  ]
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

# WSFeedConnector Phase-3.5 rollout gap — 73 unregistered venues

> Filed as the audit output of `foundation_gates_and_capture_to_100_2026_07_06` task 010 (venue-level `WSFeedConnector`
> registration audit — a DIFFERENT bug class from the operations-dispatcher C5 handler audit). **The C5 audit closed 2
> gaps; this per-VENUE audit shows the residual is entirely Phase-3.5 rollout gap (0 built-but- unregistered venues; 73
> genuinely-not-built venues).** Feeds Plan 4's Layer-1 re-measure so `blocked-not-registered` counts are correctly
> interpreted as a live-transport gap, not a wiring bug.

## What I found

**Registered venue keys after `register_all()` (2026-07-06):** 31 keys —
`ASTER · BINANCE-FUTURES · BINANCE-SPOT · BYBIT-FUTURES · BYBIT-SPOT · CBOE · CME · COINBASE-SPOT · DERIBIT · DRIFT-SOLANA · HYPERLIQUID · KALSHI · KALSHI-PERP · KRAKEN-FUTURES · KRAKEN-SPOT · NASDAQ · NYSE · OKX-FUTURES · OKX-SPOT · POLYMARKET · POLYMARKET-PERP · UPBIT · curve · jito · kalshi · morpho · odds_api · orca · phoenix · polymarket · raydium`.

**Batch expected venues (UAC `VENUES_BY_ASSET_GROUP`) — resolver output** using `resolve_live_venue_key` from
`e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py:201` (strips chain suffixes then case-folds against
`WS_FEED_CONNECTOR_FACTORIES`):

| AG         | resolved (has factory) | unresolved (missing) | cells (venues × data_types) that read `blocked-not-registered` |
| ---------- | ---------------------- | -------------------- | -------------------------------------------------------------- |
| cefi       | 11                     | **13**               | 104 (matches QG roll-up)                                       |
| defi       | 6                      | **49**               | 1225 (matches QG roll-up)                                      |
| tradfi     | 4                      | **4**                | 40 (matches QG roll-up)                                        |
| sports     | 1                      | **7**                | 70 (matches QG roll-up)                                        |
| prediction | 2                      | **0**                | 0                                                              |
| **TOTAL**  | 24                     | **73**               | 1439                                                           |

**Built-but-unregistered vs genuinely-not-built** (per the task's classifier):

- **BUILT-BUT-UNREGISTERED = 0.** Diff between all `connectors/*_ws.py` modules on disk (39) and the modules imported by
  `register_all()` (28) yielded 11 candidates, but every one is a **data-type-specific helper** imported by an
  already-registered base module and dispatched inside its factory:
  - `binance_futures_book_ticker_ws` — imported by `binance_futures_ws.py` L253-266 for `book_snapshot_5` +
    `derivative_ticker` dispatch (also imported by `aster_book_liq_ws.py` for the ASTER book helper).
  - `bybit_futures_book_ticker_ws` — imported by `bybit_ws.py` L244-257.
  - `coinbase_book_ws` — imported by `coinbase_spot_ws.py`.
  - `deribit_book_ticker_ws` — imported by `deribit_ws.py`.
  - `hyperliquid_l2book_ws` + `hyperliquid_ticker_ws` — imported by `hyperliquid_ws.py`.
  - `kalshi_trades_ws` — imported by `kalshi_clob_ws.py`.
  - `kraken_futures_book_ticker_ws` — imported by `kraken_futures_ws.py`.
  - `okx_futures_book_ticker_ws` — imported by `okx_ws.py`.
  - `polymarket_trades_ws` — imported by `polymarket_clob_ws.py`.
  - `tardis_machine_ws` — intentionally NOT registered (opt-in `live_source == "tardis-machine"` fallback per
    `websocket_streaming_handler.py:128-136`).

  Conclusion: the C5-class bug (built + unit-tested but missing from the dispatcher) does NOT recur at the WS connector
  layer. Nothing to inline-fix.

- **GENUINELY-NOT-BUILT = 73.** The 73 unregistered venues have NO `WSFeedConnector` implementation anywhere in
  `market_tick_data_service/live/connectors/`; they are the remaining Phase-3.5 rollout backlog.

## Why it matters

Plan 4 (`layer1_remeasure_and_certify_2026_07_06`) task 001 called out "the unregistered-handler audit (Plan 5) — run it
BEFORE this re-measure so a built-but-unwired handler … is not mislabelled as a real coverage gap in the certified
numbers." **This audit closes the loop cleanly**: the 1,439 cells that read `blocked-not-registered` in the QG
batch+live smoke matrix are a **live-transport gap, not a wiring bug**. Task 001's re-measure can now interpret them as
honest-live-absence for the 73 venues without re-scoping them as capture bugs.

**Impact on Layer-1 certification (mine, task 002 of Plan 4):** none — Layer-1 is denominator-only (batch capture);
`blocked-not-registered` is a LIVE-dimension verdict. The certified cefi Layer-1 73.61% stands.

**Impact on Plan 4's Layer-2 rollup interpretation:** the `blocked-not-registered` cells belong to venues without a LIVE
feed — batch-only capture (REST) may still be present for many (BITFINEX/BITGET REST, ICE via Databento batch), which is
distinct from the LIVE Phase-3.5 rollout. Layer-2 capture % should NOT be dragged down by these cells if the underlying
batch REST capture is honest-complete.

## Recommended decision

Adopt the ordered Phase-3.5 rollout as the standing follow-up plan. The de-risk order (from
`live_pipeline_mtds_mdps_features_2026_05_08` Phase 3.5 + the `register_all()` docstring) is **cefi spot/perp → tradfi →
sports → defi (bulk-remainder) → prediction (already done)**. Group the 73 into six categories so the operator can
approve / defer per category rather than per-venue.

## Actionable todos (per-venue rollout, grouped for tractable dispatch)

### CeFi — 13 venues

- [x] [DESIGN] P1. **CeFi bare-venue triage: BYBIT · COINBASE · OKX · DERIBIT-COMBO** ✅ — Operator ruling landed
      (BLK-31951ebc + BLK-f7372dd9, 2026-07-06). Resolutions: **BYBIT** bare → alias-register to `_bybit_factory`
      shipped (mtds@9d3c1aa1); **OKX** bare → alias-register to `_okx_factory` shipped (mtds@9d3c1aa1);
      **DERIBIT-COMBO** → confirmed manifest/reference-only (no live tick feed — combos derive from bare DERIBIT
      `options_chain`); **COINBASE** bare → **DEFERRED** as a follow-on [CODE] task (25 downstream callers — needs a
      migration, not a drop). Regression tests added: `test_bybit_bare_alias_registered` +
      `test_okx_bare_alias_registered`. Closes ~26 of 104 cefi `blocked-not-registered` smoke-matrix cells (BYBIT ~13
      + OKX ~13).
- [ ] [CODE] P2. **COINBASE bare-name UAC removal + downstream migration** — bare `COINBASE` entry in
      `unified_api_contracts/.../market_data_categories.py:242` is a legacy pre-2026-06-23 tag (before the perp-gate
      pair). Slot-6 initial grep suggested `COINBASE` was orphan; operator ruling (2026-07-06) found ~25 downstream
      callers that still key off bare `COINBASE`. Migrate those callers to `COINBASE-SPOT` (or the perp-gate pair
      `COINBASE ↔ COINBASE-SPOT` if MVP requires it), THEN drop the bare entry from UAC. Gate: 0 downstream call
      sites reference bare `COINBASE`; the entry is removed from `VENUES_BY_ASSET_GROUP["cefi"]`; smoke-matrix
      `blocked-not-registered` count for `COINBASE` drops to 0 (repo: unified-api-contracts + fan-out).
- [ ] [CODE] P1. **BITFINEX-SPOT + BITFINEX-FUTURES WSFeedConnector build** — public WS APIs; BitFinex REST batch
      already captures. Register under `BITFINEX-SPOT` / `BITFINEX-FUTURES` (repo: market-tick-data-service). Gate: both
      venues resolve in `resolve_live_venue_key`; regression tests mirror
      `test_deribit_options_chain_operation_registered`.
- [ ] [CODE] P1. **BITGET-SPOT + BITGET-FUTURES WSFeedConnector build** — public WS APIs (repo:
      market-tick-data-service). Gate: both venues resolve; regression tests added.
- [ ] [CODE] P1. **COINBASE-FUTURES WSFeedConnector build** — public WS on `wss://advanced-trade-ws.coinbase.com` (repo:
      market-tick-data-service). Gate: COINBASE-FUTURES resolves; regression test.
- [ ] [CODE] P1. **BINANCE-DELIVERY WSFeedConnector build** — Binance COIN-M dated futures (public WS
      `wss://dstream.binance.com`). NOTE: per tracker 06-27 decision, COIN-M is explicitly NOT MVP for perps, but
      DELIVERY (dated futures) is separate. Confirm MVP scope before building (repo: market-tick-data-service). Gate:
      BINANCE-DELIVERY resolves (or filed as BLOCKED-OPERATOR-DECISION honest-absence). **BLOCKED-OPERATOR-DECISION**
      (Ikenna — MVP inclusion).
- [ ] [CODE] P2. **On-chain CeFi perps: EXTENDED-STARKNET + LIGHTER-ZKSYNC + PACIFICA-SOLANA WSFeedConnector build**
      (repo: market-tick-data-service). These are the on-chain-CeFi-perp venues from foundation-completeness §G1.3.
      **Currently BLOCKED-CREDENTIALS** for the paid-RPC endpoints per tracker Blocked/waiting register; build the
      scaffold anyway per External-data-always-available rule. Gate: 3 venues resolve OR carry `BLOCKED-CREDENTIALS`
      scaffolds with `_placeholder_factory` that raises the credential-required error.

### TradFi — 4 venues

- [ ] [CODE] P1. **FX WSFeedConnector build** — FX not a Databento code; likely needs another provider (repo:
      market-tick-data-service). **BLOCKED-OPERATOR-DECISION** — pick provider (OANDA / TrueFX / bank-feed); currently
      no candidate connector class. Filing as honest-absence in the meantime.
- [ ] [CODE] P1. **ICE WSFeedConnector build** — Databento supports ICE datasets but is BLOCKED-CREDENTIALS on the
      Real-Time key (per Databento connector docstring). Once credential arrives, wire ICE under the existing
      `databento_tradfi_ws.py` factory pattern (venue map = `_VENUE_TO_DATASET`) (repo: market-tick-data-service).
      **BLOCKED-CREDENTIALS**.
- [ ] [CODE] P2. **KRX + YAHOO_FINANCE WSFeedConnector build** — KRX Korea; YAHOO_FINANCE is batch-only by design (no
      live WS). File YAHOO_FINANCE as `BATCH-ONLY-BY-DESIGN` honest-absence; KRX depends on provider selection (repo:
      market-tick-data-service). **BLOCKED-OPERATOR-DECISION** (Ikenna — KRX MVP scope).

### Sports — 7 venues

- [ ] [CODE] P1. **BETFAIR (+ 3 sub-variants: EX_EU / EX_UK / SB_UK) WSFeedConnector build** — Betfair Exchange +
      Sportsbook streaming APIs (repo: market-tick-data-service). **BLOCKED-CREDENTIALS** for the Betfair API app key
      (subscription; see tracker Blocked/waiting register `SFI + Transfermarkt sports keys`). Gate: 4 Betfair venue keys
      resolve OR carry `BLOCKED-CREDENTIALS` scaffold.
- [ ] [CODE] P2. **DRAFTKINGS + FANDUEL + PINNACLE WSFeedConnector build** — US Sportsbook public odds pages (typically
      HTTP polling, not WS; may not have public WS) (repo: market-tick-data-service). **BLOCKED-OPERATOR-DECISION**
      (odds_api already covers these via the aggregator — decide whether direct Sportsbook is in scope or if `ODDS_API`
      capture is sufficient for MVP).

### DeFi — 49 venues (the bulk)

- [x] [DESIGN] P0. **DeFi live-connector strategy call: chain-agnostic base OR per-(protocol × chain)?** ✅ — **DECISION
      (Ikenna, 2026-07-06): Option B — per-(protocol×chain) registration.** Each canonical UAC venue key
      (`PROTOCOL-CHAIN` form, e.g. `UNISWAP_V3-ETHEREUM`, `CURVE-ETHEREUM`, `AAVE_V3-ARBITRUM`) gets its own
      `register_ws_feed_connector` entry. Rationale: execution routing requires per-chain keys (Uniswap V3 exists on
      Ethereum/Arbitrum/Base/Optimism/Polygon simultaneously; chain-agnostic keys are ambiguous for gas, liquidity, and
      alerting). Base classes parameterized by `chain` are fine for code-reuse. Consistent with IS as SSOT — venue_key
      encodes (protocol × chain) uniquely. Full analysis + policy in Progress Log. The 3 Solana naming mismatches
      (orca/raydium/jito → ORCA-SOLANA/RAYDIUM-SOLANA/JITO-SOLANA) and existing curve/morpho renames are separate
      follow-on fixes (CODE tasks below).
- [ ] [CODE] P1. **DeFi lending: AAVE_V3 + COMPOUND_V3 + MORPHO-BASE per-chain WSFeedConnector build** (repo:
      market-tick-data-service). Once the naming policy above lands. Gate: AAVE_V3 + COMPOUND_V3 canonical keys resolve;
      MORPHO-BASE resolves against the existing MORPHO base or a chain-specific override.
- [ ] [CODE] P1. **DeFi DEX-swap: UNISWAP_V3 + UNISWAP_V2 + UNISWAP_V4 + SUSHISWAP + BALANCER + PANCAKESWAP_V3 +
      CAMELOT_V3 + AERODROME_V3 + TRADER_JOE_V2 + VELODROME_V2 WSFeedConnector build** (repo: market-tick-data-service).
      Depends on the naming policy above. Gate: each protocol canonical key resolves.
- [ ] [CODE] P1. **DeFi LST + perp + specialty: LIDO + ETHERFI + ETHENA + EIGENLAYER + FLUID + SPARK + GMX + KAMINO +
      MARINADE + JITO-SOLANA WSFeedConnector build** — some (JITO) already have polling connectors but under a different
      key (`jito` vs `JITO-SOLANA`); reconcile the key naming (repo: market-tick-data-service). Gate: each protocol
      canonical key resolves.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-06** — **gap-001 shipped** by slot-6. Operator ruling on slot-4's 2026-07-06 recommendation received via
  main (BLK-31951ebc + BLK-f7372dd9): APPROVE items 1-3, DEFER item 4. Shipped MTDS bare-venue aliases + regression
  tests at `mtds@9d3c1aa1`:
  1. `bybit_ws.py` — bare `BYBIT` → `_bybit_factory` alias (wiring-only, MVP scope already includes bare BYBIT as
     the canonical perp namespace of the perp-gate pair);
  2. `okx_ws.py` — bare `OKX` → `_okx_factory` alias (wiring-only, bare OKX is in `_CEFI_SUB_VENUE_BASES`);
  3. `test_bybit_ws_connector.py` + `test_okx_ws_connector.py` — regression tests
     (`test_bybit_bare_alias_registered` / `test_okx_bare_alias_registered`) asserting each bare key resolves to
     the same factory object as the `-FUTURES` key + produces a valid connector.

  The DERIBIT-COMBO stance (manifest/reference-only, no live tick feed — combos derive from bare DERIBIT
  `options_chain`) is CONFIRMED by the operator; no MTDS code change (there is no WS feed to build). COINBASE bare
  removal is DEFERRED under a new [CODE] P2 todo (operator surfaced ~25 downstream callers requiring migration
  before the UAC drop). Impact: ~26 of 104 cefi `blocked-not-registered` smoke-matrix cells resolved by items 1+2
  (BYBIT ~13 + OKX ~13); DERIBIT-COMBO ~13 reclassified as honest-absence; ~52 residual on the P1/P2 CODE follow-ons.

- **2026-07-06** — **Design analysis (task gap-001, CeFi bare-venue triage)** by slot-4. Investigated the 4 bare CeFi
  venue tags (BYBIT · OKX · COINBASE · DERIBIT-COMBO) that fail `resolve_live_venue_key` against the current
  `WS_FEED_CONNECTOR_FACTORIES` set. Findings + per-venue recommendation:

  **1. `BYBIT` (bare) — RECOMMENDATION: register alias to `BYBIT-FUTURES` factory.**
  - MVP scope INCLUDES bare `BYBIT` (`mvp_scope.py:372`) — it is the canonical perp namespace for the perp-gate pair
    `BYBIT ↔ BYBIT-SPOT` per `cefi_universe_capture_rule_2026_06_23`.
  - `symbol_rules._VENUE_INSTRUMENT_TYPE["BYBIT"] = "perpetual"` (mtds engine).
  - MTDS registers `BYBIT-FUTURES` (`bybit_ws.py:266`); no bare `BYBIT` registration exists → smoke matrix
    `blocked-not-registered`.
  - This is a wiring-only gap, NOT a scope question: the MVP rule already says bare BYBIT is in-scope.
  - Fix: add `register_ws_feed_connector(venue="BYBIT", factory=_bybit_factory, overwrite=True)` in `bybit_ws.py`
    (identical factory served under both keys — matches the OKX-SPOT/OKX-FUTURES symmetric-shape precedent).
  - No MVP-rule change needed. Regression test: `resolve_live_venue_key("BYBIT", …)` returns `"BYBIT"`.

  **2. `OKX` (bare) — RECOMMENDATION: register alias to `OKX-FUTURES` factory.**
  - MVP scope uses sub-venues `OKX-SPOT` / `OKX-SWAP` / `OKX-FUTURES` (`mvp_scope.py:381-383`); bare `OKX` is in
    `_CEFI_SUB_VENUE_BASES = frozenset({"OKX"})` as a legacy caller-convenience alias (`mvp_scope.py:89`) — the
    `is_mvp("cefi", "OKX", …)` predicate base-normalises bare `OKX` to match any `OKX-*` sub-venue.
  - MTDS registers `OKX-FUTURES` (`okx_ws.py:268`) + `OKX-SPOT` (`okx_spot_ws.py:59`); no bare `OKX` → smoke matrix
    `blocked-not-registered`.
  - Same wiring-only gap as BYBIT. `OKX-FUTURES` is the perp/swap primary (per
    `_VENUE_INSTRUMENT_TYPE["OKX-SWAP"]="perpetual"`; `tardis_machine_ws.py:85` maps `OKX-FUTURES` → `okex-swap`).
  - Fix: add `register_ws_feed_connector(venue="OKX", factory=_okx_factory, overwrite=True)` in `okx_ws.py`.
  - No MVP-rule change needed.

  **3. `COINBASE` (bare) — RECOMMENDATION: remove from `VENUES_BY_ASSET_GROUP["cefi"]` (legacy tag; no MVP semantics).**
  - MVP scope declares `COINBASE-SPOT` + `COINBASE-FUTURES` (`mvp_scope.py:396-397`); bare `COINBASE` is NOT in the
    MVP venues frozenset and NOT in `_CEFI_SUB_VENUE_BASES`.
  - UAC `VENUES_BY_ASSET_GROUP["cefi"]` still carries bare `COINBASE` alongside `COINBASE-SPOT` +
    `COINBASE-FUTURES` (`market_data_categories.py:242-247`) — legacy pre-2026-06-23 shape (before the perp-gate
    pair was introduced).
  - No downstream MVP/pipeline code references bare `COINBASE` (unlike bare BYBIT/OKX which the MVP rule does).
  - The 5 · 5 = 25 `blocked-not-registered` cells attributed to bare `COINBASE` are a UAC-registry artifact, not a
    real gap.
  - Fix: remove the `"COINBASE",` entry from `market_data_categories.py:242`. The COINBASE-FUTURES live
    connector build is already tracked as a separate P1 CODE todo (line 144 of this issue doc).
  - Alt (if any downstream code still keys off bare `COINBASE`): register `COINBASE` → `COINBASE-SPOT` factory alias
    instead of removing. Grep is clean; recommend the remove.

  **4. `DERIBIT-COMBO` — RECOMMENDATION: confirm manifest-only / batch-only-by-design; no WS feed exists or is needed.**
  - `DERIBIT-COMBO` is a REFERENCE-DATA venue (instruments-service adapter
    `deribit_combo_adapter.py`, `VENUE_TO_ADAPTER["DERIBIT-COMBO"]="deribit_combo"`) that fetches multi-leg combo
    instrument DEFINITIONS from Deribit's public REST `/get_instruments?kind=combo`. It has its own manifest shard
    to preserve venue-tag integrity (per `market_data_categories.py:234-240`, the venue had 0 captured days
    2026-05-23→06-18 before the kind-split fix).
  - There is NO market-tick data feed for combos independent of bare `DERIBIT`: `grep -rn 'DERIBIT-COMBO'
    market-tick-data-service/` returns 0 hits. Combo pricing derives from bare DERIBIT's `options_chain` (marks +
    IVs of the constituent legs); the D2a `{OPTION}` → `options_chain`-only cut already handles it.
  - Not in MVP scope (`mvp_scope.py` CeFi venues frozenset does not include `DERIBIT-COMBO`); historical is
    unbackfillable (Deribit REST does not offer historical combos —
    `relabel_deribit_combo_historical_to_empty_2026_06_27.py`).
  - Fix: no WSFeedConnector to build. The `blocked-not-registered` cells for DERIBIT-COMBO are honest-absence
    (BATCH-ONLY-BY-DESIGN for the reference-data side; no live tick equivalent). Confirm this stance so downstream
    can classify these cells `expected_unattempted` with reason "reference-data-only venue".
  - Optional cleanup: keep DERIBIT-COMBO in `VENUES_BY_ASSET_GROUP["cefi"]` (needed for URDI's venue-tag filter);
    add a `NON_LIVE_VENUES` allow-list or equivalent so `resolve_live_venue_key` returns a sentinel
    ("reference-data-only") rather than `None` for these venues, distinguishing them from real live gaps.

  **Summary table:**

  | Venue          | Verdict                          | Change                                           | Repo(s) |
  | -------------- | -------------------------------- | ------------------------------------------------ | ------- |
  | BYBIT          | add-live-factory (alias)         | `register(BYBIT, _bybit_factory)`                | mtds    |
  | OKX            | add-live-factory (alias)         | `register(OKX, _okx_factory)`                    | mtds    |
  | COINBASE       | remove-from-scope (legacy tag)   | drop `"COINBASE",` in `market_data_categories`   | UAC     |
  | DERIBIT-COMBO  | confirm-manifest/reference-only  | classify honest-absence; optional NON_LIVE tag   | UAC/e2e |

  **Impact on the `blocked-not-registered` cell count**: 4 venues × ~13 avg data_types = ~52 of the 104 `cefi`
  blocked-not-registered cells resolved by these fixes alone (BYBIT ~13 + OKX ~13 + COINBASE ~13 remove +
  DERIBIT-COMBO ~13 reclassify = ~52). The remaining ~52 cells are the 9 other unbuilt CeFi venues (BITFINEX ×2,
  BITGET ×2, COINBASE-FUTURES, BINANCE-DELIVERY, LIGHTER/EXTENDED/PACIFICA) tracked as separate P1/P2 CODE todos.

  Posting **BLOCKED-OPERATOR-DECISION** (Ikenna) for the 4-venue recommendation before shipping the register-alias +
  remove-from-scope code changes. The 3 rename-only cases (BYBIT / OKX alias, COINBASE removal) are wiring/registry
  edits with no scope shift; DERIBIT-COMBO is a pure classification confirm.

- **2026-07-06** — **Operator decision (gap-011)**: Ikenna confirmed **Option B — per-(protocol×chain)** via main agent.
  Policy: each canonical UAC `PROTOCOL-CHAIN` venue key gets its own `register_ws_feed_connector` entry in MTDS. Base
  classes with chain parameter OK for code reuse. Solana naming mismatches (orca/raydium/jito) and curve/morpho renames
  are separate follow-on CODE tasks. Checkbox flipped; policy documented. CODE items below are now unblocked on naming
  direction.

- **2026-07-06** — **Design analysis (task gap-011)** by slot-4. Researched the chain-agnostic vs per-(protocol×chain)
  question. Key findings:

  **49-venue breakdown (precise):**
  - 3 are a **Solana naming mismatch**: `orca`/`raydium`/`jito` are registered under bare names but the smoke matrix's
    `_normalize_venue_for_match` deliberately does NOT strip `-SOLANA` (only EVM chain suffixes are stripped). So
    `ORCA-SOLANA`, `RAYDIUM-SOLANA`, `JITO-SOLANA` each fail to resolve to their connector. Fix: rename the three
    `register_ws_feed_connector(venue=...)` calls from bare names to canonical UAC names. **Does not require the
    architectural call — can proceed unilaterally.**
  - 46 are genuinely-not-built (no connector exists). These need the architectural decision.

  **Existing multi-chain honesty gap**: The 6 DeFi venues the smoke matrix shows as "resolved" include `CURVE-OPTIMISM`,
  `CURVE-AVALANCHE` (matching the `curve` key via chain-strip), and `MORPHO-BASE` (matching `morpho`). BUT:
  `CurveWSFeedConnector` hardcodes `api.curve.finance/v1/getPools/all/ethereum` (Ethereum only). `MorphoWSFeedConnector`
  hardcodes `chainId_in: [1]` (Ethereum only). So the smoke matrix says these 3 venues are "registered" but the actual
  connector does not serve their chain data. This is a correctness gap under Option A (chain-agnostic): the connector
  claims a chain it doesn't cover.

  **Option A — chain-agnostic (one venue key spans all chains)**:
  - Pros: fewer registry keys; `curve` key resolves for all CURVE-\* chains automatically.
  - Cons: connectors must actually serve ALL chains simultaneously (Curve has per-chain REST endpoints:
    `/v1/getPools/all/optimism`, `/v1/getPools/all/avalanche`). Current connectors are Ethereum-only despite "resolving"
    for multi-chain — violates honest-absence principle. Hard to express in smoke matrix: `CURVE-OPTIMISM` shows
    "registered" but actual data is Ethereum only.

  **Option B — per-(protocol×chain) registration (RECOMMENDED)**:
  - Pros: registry key = UAC canonical `PROTOCOL-CHAIN` form 1:1; smoke matrix is honest; correctness is verifiable.
  - Cons: 46 separate factory registrations needed vs a smaller number of base classes.
  - Implementation: base classes with `chain` parameter are fine for code-reuse (e.g., `CurveWSFeedConnector(chain=...)`
    fetches the right endpoint); each chain gets its own `register_ws_feed_connector(venue="CURVE-OPTIMISM", ...)`.
  - Existing connectors: `curve` → re-register as `CURVE-ETHEREUM`; `morpho` → `MORPHO-ETHEREUM`. Backward-compat: add
    alias `curve` → `CURVE-ETHEREUM` in the registry if needed for existing test coverage.

  **Recommendation to Ikenna**: Option B (per-chain). Plus, regardless of Option A/B:
  1. Immediately rename Solana bare keys → canonical: `orca`→`ORCA-SOLANA`, `raydium`→`RAYDIUM-SOLANA`,
     `jito`→`JITO-SOLANA`. This fixes 3 of the 49 unresolved without touching the architectural question.
  2. Rename `curve`→`CURVE-ETHEREUM`, `morpho`→`MORPHO-ETHEREUM` to close the multi-chain honesty gap.

  Posting BLOCKED-OPERATOR-DECISION for Ikenna to approve Option B before building the 46 remaining venues.

- **2026-07-06** — **Issue filed** by `foundation_gates_and_capture_to_100-010` (venue-level WSFeedConnector audit). Ran
  `register_all()` on `mtds@HEAD` post the C5 handler fix: **31 registered venue keys**. Cross-referenced against UAC
  `VENUES_BY_ASSET_GROUP` via the smoke-matrix's own `resolve_live_venue_key` resolver → **73 unregistered venues**
  (cefi 13 · tradfi 4 · defi 49 · sports 7 · prediction 0). Verified all 73 are **genuinely-not-built** (no
  `WSFeedConnector` class exists in `connectors/`); the 11 "unregistered" `_ws.py` modules are ALL data-type-specific
  helpers imported by their base venue's factory (no C5-class bug at the WS layer). Cell counts match the QG
  batch+live-smoke roll-up exactly: cefi 104 · defi 1225 · sports 70 · tradfi 40 = 1,439 `blocked-not-registered` cells.
  This closes the interpretation loop for Plan 4's Layer-1 re-measure: the residual counts are a live-transport gap
  (Phase-3.5 rollout backlog), not a wiring bug — Layer-2 capture % should not be dragged down by them if the underlying
  batch REST capture is honest-complete.
