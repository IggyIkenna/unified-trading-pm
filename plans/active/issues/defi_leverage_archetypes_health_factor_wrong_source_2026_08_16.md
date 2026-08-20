---
doc_type: issue
title: >-
  Every health-factor-shaped liquidation gate reads an ad-hoc source — 4 archetypes across 3 families, plus a
  purpose-built circuit breaker that's completely unused
summary: >-
  Two related use-cases of the same field, both broken the same way. Own-leverage risk gating — `CARRY_STAKED_BASIS`
  and `CARRY_RECURSIVE_STAKED`, the only two DeFi archetypes that take on-chain leverage — gate liquidation risk on
  `features.get("health_factor")`, a generic features-service value that carries no wallet-specific meaning and has
  never been populated with real data. Third-party liquidation-candidate monitoring — `arbitrage_structural`'s
  `liquidation_capture.py` and `mev`'s `liquidation_bundle.py` — independently reimplement the identical
  "health-factor < threshold" pattern to spot OTHER wallets' liquidatable positions, each with its own inline gate.
  The correct centralized module (`DeFiHealthAggregator` / `positions_health.py`, already client_id-scoped) exists
  but is never called from the strategy engine — it's HTTP-only, execution-service-facing — and a purpose-built
  `liquidation_proximity_circuit.py` circuit breaker exists with zero callers anywhere outside its own package
  `__init__.py`. Also found: the centralized module itself isn't fed by any live source (only tests call its update
  path), a stub on-chain Aave adapter in strategy-service returns `NotImplementedError`, and the data model is
  missing LTV/borrow-capacity/liquidation-price fields an archetype would need. A broader sweep across all other
  strategy families (kill-switch handling, vol_trading's risk gates) found those correctly centralized — this
  pattern is confined to health-factor-shaped liquidation gates specifically, not a systemic failure. Filed per
  operator direction to establish a strategy-agnostic, venue-agnostic centralized pattern for private on-chain
  position/risk reads, after three rounds of investigation surfaced and then precisely scoped this while scoping
  the Elysium carve-out's excluded `health_factor` field.
status: open
nature: issue
asset_group: [defi]
stage: [execution]
repos: [strategy-service, execution-service, unified-api-contracts]
scope: [engineer]
tags: [defi, risk, health-factor, liquidation, architecture, centralization, strategy-agnostic]
related:
  [
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
    /codex/04-architecture/defi-execution-overview.md,
  ]
created: 2026-08-16
author: interactive-session
parent_epic: security_and_cross_cutting_master
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6.4
assigned_role:
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
archive_exempt: true # 0-open-todos 2026-08-18 (all 8 closed by citation) — underlying fix still in-progress in strategy_service_centralization_fixes_2026_08_16.md, this doc stays as the living evidence record (see Progress Log)
context_scope:
  [
    /codex/04-architecture/defi-execution-overview.md,
    /codex/04-architecture/position-risk-centralization.md,
    /plans/active/strategy_service_centralization_fixes_2026_08_16.md,
    strategy-service/strategy_service/position/core/defi_health_aggregator.py,
    strategy-service/strategy_service/position/core/margin_event_emitter.py,
    strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py,
  ]
source: >-
  Interactive session 2026-08-16, surfaced while scoping which DeFi feature fields the Elysium carve-out owes the
  client. Two agent-dispatched investigations traced the actual wiring rather than trusting docstrings: the first
  found features-service's `_process_health_factor()` docstring falsely claims per-wallet Aave polling (it actually
  reads generic protocol-level rate-index data); the second enumerated every DeFi-leverage-capable archetype and
  traced their real risk-data sourcing end to end.
---

# DeFi-leverage archetypes' liquidation kill-gate reads the wrong data source

## Finding

Exactly two archetypes take genuine on-chain DeFi leverage (post collateral, borrow against it) — everything else
(`rotation_lending.py`, all three `defi_lp/*.py` engines, every non-DeFi archetype) is supply-side/LP-only or
CEX-margin, confirmed by an exhaustive search for borrow/collateral/lend logic. **Two more archetypes, in two other
families, independently reimplement the identical gate for a related but distinct purpose — spotting OTHER
wallets' liquidatable positions rather than gating our own leverage:**

| Archetype | File | Use case |
| --- | --- | --- |
| `CARRY_STAKED_BASIS` | `strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py:419` | Own-leverage risk: `LST_AS_MARGIN` mode posts the LST as real on-chain-derived perp margin |
| `CARRY_RECURSIVE_STAKED` | `strategy_service/engine/strategies/v2/carry_and_yield/recursive_staked.py:115,447` | Own-leverage risk: genuine `STAKE→LEND→BORROW→STAKE...` recursive loop |
| (arbitrage_structural) | `strategy_service/engine/strategies/v2/arbitrage_structural/liquidation_capture.py:81-97` | Third-party monitoring: own `max_health_factor` param gate, identical "HF < threshold → act" logic to capture others' liquidations |
| (mev) | `strategy_service/engine/strategies/v2/mev/liquidation_bundle.py:153,266-283` | Third-party monitoring: `features.get(f"liq_candidate_health_factor_{cid}")`, inline `candidate.health_factor >= 1` gate |

**All four read from the generic per-tick features pipeline, ad hoc.** For the first two, that's literally
`features.get("health_factor")` — `staked_basis.py:419`, `recursive_staked.py:115` (entry gate) and `:447`
(exit/unwind gate, `_check_family2_health_kill`). A separate investigation this session found the pipeline
function that was believed to populate it (`_process_health_factor()` in
`features-service/features_service/onchain/engine/orchestrator.py`) has a **false docstring** — it claims to poll
Aave's `getUserAccountData()` per wallet, but actually reads the same generic MTDS `rate_indices` data every
sibling Aave feature calculator uses, with no wallet parameter anywhere. The value has never carried real
per-position meaning, and the corpus has never had it populated (confirmed: paper-run substitutes a hardcoded
safe constant because "the dedicated health_factor feature group carries no numeric column yet in this corpus,"
`strategy_service/cli/handlers/paper_run_handler.py:26-28,343`).

**`recursive_staked.py` copied the pattern deliberately, not accidentally** — its own docstring (lines 436-439)
says it reuses "the same `health_factor` feature / `min_health_factor`" as `staked_basis.py`. `liquidation_capture.py`
and `liquidation_bundle.py` show the same instinct independently arising a second and third time, for a different
purpose, in different families — this is a precedent problem, not a one-off bug.

**A purpose-built fix already exists and sits completely unused**: `strategy_service/circuit_breakers/liquidation_proximity_circuit.py`
looks purpose-built for exactly this gate, but `grep -rln "liquidation_proximity_circuit" strategy_service` returns
nothing outside its own package `__init__.py` — zero archetypes call it, including the four above.

**What's confirmed NOT broken — this is a scoped pattern, not systemic.** A broader sweep across every other
strategy family found risk-gating done correctly elsewhere: kill-switch handling is centralized in
`BaseArchetypeEngineV2` (`engine/strategies/v2/base.py:40-43,249-284`) and every archetype inherits it uniformly;
`vol_trading`'s `RiskGates`/`PortfolioRiskGate` (`vol_trading/portfolio_risk_gate.py`) are shared, single-instance
objects threaded through the family's allocators, not reimplemented per-archetype. Several other archetype-specific
gates checked (stat_arb_pairs' stop-loss z-score, defi_lp/vault.py's drawdown gate) are genuinely archetype-specific
with no duplicate elsewhere — correctly left alone.

## The correct centralized module exists — but nothing calls it, and nothing feeds it

- `strategy_service/position/core/defi_health_aggregator.py` (`DeFiHealthAggregator`) is genuinely venue/protocol-
  agnostic by construction (iterates whatever `DeFiLendingPosition` objects it's given, keyed by protocol/chain, no
  protocol-specific branching) and already `client_id`-scoped. **But it's only instantiated in
  `position/api/routes/risk.py:248,271` (HTTP routes) — never imported by any `engine/strategies/v2/**` file.**
- `positions_health.py`'s own docstring names its real consumer as execution-service's `run_wallet_preflight_checks`
  Layer-4, not strategy-service archetypes.
- **Neither is fed by a live source today.** Grep found only test-file callers of `update_wallet_health_from_lending`
  — no production code path pushes real lending-position data into `DeFiHealthAggregator`'s state.
- A third piece, `strategy_service/position/position_interface/adapters/aave.py` (`AavePositionAdapter`), looks like
  it should be that live feed — but `get_balances()` and `get_positions()` both `raise NotImplementedError`
  (lines 71-78). It's a non-functional stub, and even if implemented it returns the wrong schema
  (`CanonicalPosition`, not `DeFiLendingPosition`) to plug directly into the aggregator.
- The one genuinely working live poller is `execution-service/execution_service/defi_execution/monitors/health_factor_monitor.py`
  (real `getUserAccountData()` calls, per-wallet) — but it isn't wired to feed `DeFiHealthAggregator` either.

**So there are three unconnected pieces**: (1) execution-service's working live poller, (2) strategy-service's
non-functional stub adapter, (3) the aggregation/serving logic with no live feed. None of the three talk to each
other today.

## Data model gaps

Even once wired, the centralized data model can't yet serve everything an archetype needs:

- `DeFiAggregatedHealth`/`ProtocolHealthBreakdown` (the aggregator's output) has health factor, collateral USD,
  debt USD, weighted APY, and per-chain breakdown — **but no LTV, no borrow-capacity, no liquidation-price** field.
  `recursive_staked.py` needs LTV for loop-depth sizing (currently derives it from static/governance params instead
  of live position state, `recursive_staked.py:156,176`).
- `PositionHealthSnapshot` (`positions_health.py`) has LTV and a `liquidation_threshold` the aggregator lacks — but
  that threshold is **hardcoded to `MarginModel.AAVE_V3`** (`positions_health.py:70-72`), not resolved per the
  position's actual protocol, so it silently gives a wrong answer for a non-Aave position.

## Finding, second pass (2026-08-17) — a second centralized mechanism exists and was missed

Reconsidering this issue while generalizing the fix to be asset-group-agnostic (DeFi/CeFi/TradFi, not DeFi-only)
surfaced a mechanism this issue's original investigation never found:
`strategy_service/position/core/margin_event_emitter.py`, predating this issue's filing by 3+ months (its own
docstring: "Wave C1 — workspace audit 2026-05-01"). It states it **is** "the single canonical producer of
`MarginEvent`," built on `unified_trading_library.margin_and_liquidation` (the same generic, already CeFi-aware
core `DeFiHealthAggregator` does NOT use), and is **already live-called** from
`position/cli/handlers/monitor_handler.py` (a CLI handler, not a test) and **already consumed by
execution-service** in production (`execution_service/algo_library/deleverage_executor.py`). A dedicated test,
`tests/position/unit/test_emit_live_cefi_margin_events.py`, exercises the CeFi path specifically.

This means the premise of this issue's original fix shape — "the correct centralized module exists but nothing
calls it or feeds it" — was true for `DeFiHealthAggregator` specifically, but not the whole story: a second,
more general, already-cross-service-wired mechanism exists alongside it. Full detail:
[position-risk-centralization § Two parallel mechanisms](/codex/04-architecture/position-risk-centralization.md).

## Todos

- [x] [OPERATOR] P0. ✅ RULED 2026-08-17 — **Decide the fix shape**: neither option (a) nor (b) as originally
      framed — building either would risk a *third* parallel implementation now that `margin_event_emitter.py` is
      known. See the reconciliation todo immediately below, which must resolve first.
- [x] [AGENT] P0. ✅ RECONCILED 2026-08-18 — **Reconcile `DeFiHealthAggregator` against
      `margin_event_emitter.py`/`MarginEvent` before building or wiring anything new.** Full decision + evidence
      now lives on the corresponding todo in
      [strategy_service_centralization_fixes_2026_08_16](/plans/active/strategy_service_centralization_fixes_2026_08_16.md)
      (track completion there, per this corpus's own citation convention — see the `na-eligibility-audit`
      marker below on this doc's docstring-fix todo). Summary: A and B are NOT independent — B's DeFi path
      (`emit_margin_event_for_health`) already consumes A's `DeFiHealthAggregator.aggregate()` output via
      `risk.py::update_lending_positions()`; the genuinely redundant piece is `positions_health.py`'s separate
      `derive_snapshot_from_lending()` re-derivation (hardcoded `AAVE_V3` threshold, doesn't reuse A). `MarginEvent`'s
      schema already has `liquidation_price`/`distance_to_liquidation_pct`/`ltv_ratio` fields, but
      `_build_event()` never populates the first two for DeFi, and the DeFi snapshot is portfolio-combined, not
      per-position (`combined_health_factor`, not `ProtocolHealthBreakdown`-level) — both must be fixed before an
      archetype gate can read `MarginEvent` directly. Decision: wire archetypes onto (B)'s schema, after (b)
      populating the missing fields + per-protocol granularity, and only then retire `positions_health.py`'s
      duplicate path — not a straight "converge on B as-is."
- [x] [AGENT] P0. **(Superseded pending the reconciliation above — now resolved.)** Wire a live feed into
      `DeFiHealthAggregator`. Either finish `aave.py`'s
      `AavePositionAdapter` (fixing its schema mismatch — emit `DeFiLendingPosition`, not `CanonicalPosition`) or
      route execution-service's already-working `health_factor_monitor.py` output into the aggregator's state via
      `risk.py::update_lending_positions()` — **not** `positions_health.py::update_wallet_health_from_lending`
      (corrected 2026-08-18: that function feeds a separate, redundant cache, not `DeFiHealthAggregator` — see
      the reconciliation todo above). Do not build a third parallel poller.
      **na-eligibility-audit 2026-08-18**: KEEP-NA-STALE (already-duplicated) — this exact fix is already an open
      todo in `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` ("Route execution-service's
      HealthFactorMonitor's live per-wallet Aave data into DeFiHealthAggregator's state via
      risk.py::update_lending_positions()", [BACKEND] P0, status: active, assigned_vm: planning, sequential: true).
      Converted this checkbox to a citation marker rather than tracking a competing duplicate — track completion
      there, close this checkbox by citation once that todo lands.
- [x] [AGENT] P0. **Switch `staked_basis.py:419` and `recursive_staked.py:115,447` to the centralized source**,
      once (a) and the live feed exist. This is the actual liquidation-risk fix — until this lands, both
      archetypes' kill-gates are not protecting against real liquidation risk.
      **na-eligibility-audit 2026-08-18**: KEEP-NA-STALE (already-duplicated) — already an open todo in
      `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` ("Switch staked_basis.py's
      _validate_lst_margin_slot and recursive_staked.py's entry gate plus _check_family2_health_kill off
      features.get('health_factor')...", [BACKEND] P0, status: active, assigned_vm: planning). Converted to a
      citation marker — track completion there.
- [x] [AGENT] P1. **Switch `liquidation_capture.py:81-97` and `liquidation_bundle.py:153,266-283` to the same
      centralized source**, once it exists — these read OTHER wallets' health factor (candidates to liquidate), so
      the call shape differs from the own-position gates above (needs a candidate-wallet parameter, not
      client-scoped), but should route through the same underlying module rather than a fourth bespoke
      implementation.
      **na-eligibility-audit 2026-08-18**: KEEP-NA-STALE (already-duplicated) — already an open todo in
      `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` ("Switch
      arbitrage_structural/liquidation_capture.py's health-factor gate and mev/liquidation_bundle.py's
      liq_candidate_health_factor_* gate...", [BACKEND] P1, status: active, assigned_vm: planning). Converted to a
      citation marker — track completion there.
- [x] [AGENT] P1. **Decide `liquidation_proximity_circuit.py`'s fate.** It looks purpose-built for this exact gate
      and has zero callers. Either wire it in as the shared kill-gate all four archetypes above call, or determine
      why it was never adopted (superseded design, incomplete, wrong interface) and delete it if so — don't leave
      a working-looking, unused circuit breaker sitting alongside four bespoke reimplementations of what it does.
      **na-eligibility-audit 2026-08-18**: KEEP-NA-STALE (already-duplicated) — already an open todo in
      `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` ("Decide liquidation_proximity_circuit.py's
      fate — wire it in... or retire it", correctly re-tagged `[OPERATOR]` P1 there — this is a genuine judgment
      call, not [AGENT] as originally tagged here — status: active, assigned_vm: planning). Converted to a citation
      marker — track completion there.
- [x] [AGENT] P1. **Extend the centralized data model**: add LTV, borrow-capacity, and liquidation-price to
      `DeFiAggregatedHealth`/`ProtocolHealthBreakdown`, or unify with `PositionHealthSnapshot`'s fields. Fix the
      `AAVE_V3`-hardcoded liquidation-threshold lookup in `positions_health.py:70-72` to resolve per-position
      protocol instead.
      **na-eligibility-audit 2026-08-18**: KEEP-NA-STALE (already-duplicated) — already an open todo in
      `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` ("Extend DeFiAggregatedHealth/
      ProtocolHealthBreakdown with LTV, borrow-capacity, and liquidation-price fields...", [BACKEND] P1, status:
      active, assigned_vm: planning). Converted to a citation marker — track completion there.
- [x] [AGENT] P1. **Decide `aave.py`'s fate explicitly** — delete it in favor of the execution-service poller +
      PBMS pipeline, or finish it as the canonical feed. Don't leave a non-functional stub sitting alongside a
      working parallel path.
      **na-eligibility-audit 2026-08-18**: KEEP-NA-STALE (already-duplicated) — already an open todo in
      `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` ("Decide AavePositionAdapter (aave.py)'s
      fate...", correctly re-tagged `[OPERATOR]` P2 there — status: active, assigned_vm: planning). Converted to a
      citation marker — track completion there.
- [x] [AGENT] P2. **Fix the misleading `_process_health_factor()` docstring** in
      `features-service/features_service/onchain/engine/orchestrator.py:621-623` — it describes per-wallet Aave
      polling the function doesn't do; describe it as generic protocol-level rate-index data instead.
      **na-eligibility-audit 2026-08-17**: KEEP-NA-STALE (already-duplicated) — this exact fix is already an open
      todo in `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` line ~101 (status: active,
      assigned_vm: planning). Converted this checkbox to a citation marker rather than extracting a competing
      duplicate — track completion there, close this checkbox by citation once that todo lands.
- [x] [AGENT] P2. **Once the centralized path exists, document and enforce it as the pattern** for any future
      leverage-capable archetype, in any asset group — see the companion codex doc
      [position-risk-centralization](/codex/04-architecture/position-risk-centralization.md), authored in the
      same session and rescoped asset-group-agnostic 2026-08-17.
      **na-eligibility-audit 2026-08-18**: KEEP-NA-STALE (already-duplicated) — already an open todo in
      `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` ("Update position-risk-centralization
      from 'not yet complete' to reflect the landed state...", [BACKEND] P3, status: active, assigned_vm: planning).
      Converted to a citation marker — track completion there.
- [x] [OPERATOR] P2. **Design the mode-aware dispatch** (operator direction, 2026-08-16): batch → real historical
      data for that window; live → real-time poll against the actual wallet; paper splits into **paper-testnet**
      (poll a testnet deployment, validates wiring without touching production wallets) and **paper-live**
      (read-only poll of real mainnet data for the real wallet, no execution). Apply once the centralized path from
      the todos above exists — designing the mode dispatch before the underlying call exists would be premature.
      **na-eligibility-audit 2026-08-18**: KEEP-NA-STALE (already-duplicated) — already an open todo in
      `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` ("Design the mode-aware dispatch (batch /
      live / paper-testnet / paper-live)...", [OPERATOR] P2, status: active, assigned_vm: planning). Converted to a
      citation marker — track completion there.

## Progress Log

- **2026-08-16** — Filed from an interactive session. Two agent-dispatched investigations: the first debunked an
  initial "features-service queries private wallet data" hypothesis (it doesn't — the docstring was just wrong);
  the second enumerated every DeFi-leverage-capable archetype and traced the real gap precisely. Read-only research
  throughout — no code changed. Explicitly out of scope for the Elysium carve-out (`elysium_carveout_stubbed_strategy_service_2026_08_12.md`
  §A4 already excludes `health_factor` from that plan's data-scope, since no DeFi-side leverage is taken in the
  contracted strategies), but real production-risk-relevant for `staked_basis.py`'s live `LST_AS_MARGIN` structure
  if it's currently trading.
- **2026-08-16 (second pass)** — Operator asked whether the audit covered every strategy family, not just DeFi. A
  third agent-dispatched sweep found two more instances of the identical pattern for a related but distinct
  purpose (`liquidation_capture.py`, `liquidation_bundle.py` — third-party liquidation-candidate monitoring, not
  own-leverage gating) plus a purpose-built, completely unused circuit breaker
  (`liquidation_proximity_circuit.py`). The same sweep also checked every other family for similar duplication and
  found none — kill-switch handling and vol_trading's risk gates are correctly centralized, confirming this is a
  scoped pattern (4 files, 3 families) rather than a systemic one. Title, summary, findings and todos updated to
  the real scope in the same edit. Estimate revised from 6/4.8 AI-days to 8/6.4 to reflect the added fix surface.
- **na-eligibility-audit 2026-08-16** [body-hash:5b28bea2cce6b9c5]: KEEP-NA, valid — Freshly filed today (2026-08-16) from an interactive session; zero prior na-eligibility-audit markers, this is its first pass. 10 open todos verified via the fence-aware grep, matching Phase-0's open_todos=10 exactly.
- **context-scout 2026-08-17**: populated context_scope (4 entries) — added the correct centralized module
  (`defi_health_aggregator.py`, unused today) and `staked_basis.py` (the first archetype the P0 fix switches over)
  alongside the two companion codex architecture docs.
- **2026-08-17 (operator session, rescoped asset-group-agnostic)** — Generalizing the fix to cover CeFi/TradFi (not
  just DeFi) surfaced `margin_event_emitter.py`, a second centralized position-risk mechanism this issue's original
  investigation missed — already live-called, already cross-service, built on UTL's already-asset-group-agnostic
  `margin_and_liquidation` core. Original "decide the fix shape" todo resolved by ruling; replaced with a new P0
  reconciliation todo that must land first. Companion codex doc renamed
  `defi-position-risk-centralization.md` → `position-risk-centralization.md` and rewritten; `context_scope` updated
  to match.
- **2026-08-18 (slot 5, backend_engineer)** — Resolved the P0 reconciliation todo (mirrored, in full, on the
  corresponding todo in `strategy_service_centralization_fixes_2026_08_16.md` — this doc's checkbox is a citation
  per this corpus's convention). Also corrected the live-feed todo's wrong function name
  (`update_wallet_health_from_lending` → `risk.py::update_lending_positions()`) in the same edit, here and in the
  wrapper plan.
- **na-eligibility-audit 2026-08-18**: KEEP-NA-STALE (already-duplicated), whole-doc citation conversion — all 8
  remaining open todos (P0-P2: the live-feed wiring, both archetype switch-overs, the circuit-breaker fate
  decision, the data-model extension, the aave.py fate decision, the documentation follow-up, and the
  mode-aware-dispatch design) are verbatim or near-verbatim duplicated, several with corrected/updated framing, in
  `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` (status: active, assigned_vm: planning) —
  same pattern already applied to this doc's P2 docstring todo on 2026-08-17. Converted each to a citation marker
  rather than leaving a competing duplicate open here; doc stays `assigned_vm: NA` (zero backlog impact — this is
  pure hygiene, not a reclassification). `grep -cE '^[[:space:]]*[-*] \[ \]'` = 0 post-conversion (was 8, matching
  Phase-0's `open_todos=8` pre-conversion). Note for a future reader: this doc's own narrative (aave.py
  "non-functional stub", `HealthFactorMonitor` "already-working") is now stale relative to the sibling plan's
  2026-08-18 investigation — read the sibling plan's Progress Log for current ground truth, not this doc's
  original Finding/Data-model-gaps sections.
- **na-eligibility-audit 2026-08-18** [defi tranche]: KEEP-NA-STALE (already-duplicated) — all 8 remaining open
  todos verified against `strategy_service_centralization_fixes_2026_08_16.md` (status: active, assigned_vm:
  planning, sequential: true) and found to be verbatim/near-verbatim duplicates of that plan's own todos (the plan
  was deliberately authored by extracting this doc's findings on 2026-08-16, per its own Progress Log). Closed all
  8 by citation marker, same treatment the P2 docstring todo already received from the prior audit pass — this doc
  now carries zero independently-tracked open todos; real execution tracking lives entirely in the wrapper plan.
  Doc stays `assigned_vm: NA` (it remains the evidence/investigation record the plan's own text defers to — "Full
  findings, root cause, and evidence... live in the three source issue docs"), not archived, since the underlying
  work is still in progress. `grep -cE '^[[:space:]]*[-*] \[ \]'` = 0 post-edit, matching.
- **context-scout 2026-08-20**: refreshed context_scope (6 entries)
