## Scenario `cefi_exchange_insolvency_withdrawal_freeze` — Exchange withdrawal freeze / counterparty insolvency (CeFi)

| Field                | Value                                                                                                                                                                                                                                                                                                                                                          |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scenario_id`        | `cefi_exchange_insolvency_withdrawal_freeze`                                                                                                                                                                                                                                                                                                                   |
| Category             | `VENUE_OUTAGE` (primary — the withdrawal channel becomes permanently unavailable, the closed-set's closest fit) + `COUNTERPARTY_INSOLVENCY` (descriptive — balance-sheet / off-exchange-fund risk, NOT a connectivity fault; trading APIs can stay fully live throughout)                                                                                      |
| Layer                | `EVENT` primary (treasury balance-reconciliation state-change + withdrawal-endpoint rejection, synthesised at the treasury/custody boundary); `ORDER` secondary (new deployments blocked to the venue once frozen). `RAW_TICK` deliberately NOT held stale — see below.                                                                                        |
| Asset groups         | `frozenset({MarketAssetGroup.CEFI})`                                                                                                                                                                                                                                                                                                                           |
| Applies-to           | per-venue (one CeFi perp venue at a time; same closed-set as scenario 01: `bybit` / `deribit` / `binance` / `okx` / `hyperliquid` / `aster`), cross-referenced to `TreasurySource` where a mapping exists (`CEFFU` = Binance institutional settlement; `SUB_ACCOUNT_HYPERLIQUID` / `SUB_ACCOUNT_DYDX` = venue sub-accounts)                                    |
| Targets archetype(s) | `ARBITRAGE_PRICE_DISPERSION` (primary — margin sits on the frozen venue as one leg of the hedge pair); `CARRY_STAKED_BASIS` (secondary — perp hedge leg's margin at risk); `ML_DIRECTIONAL_CONTINUOUS` (CeFi-only archetype trading OKX + Binance + Bybit per `kill_switch.py`'s own `KILL_PER_ARCHETYPE_ML_DIRECTIONAL_CONTINUOUS` scoping — equally exposed) |

### Real-world referent

Models two of the defining CeFi-counterparty failures of the last cycle, chosen because their FAILURE SHAPES differ in a
way this scenario must exercise both of:

1. **FTX, November 2022** — the "trading stays up, withdrawals don't" shape. `Nov 6` CoinDesk reports Alameda's balance
   sheet is mostly FTT (an FTX-issued token); `Nov 7-8` a bank-run of withdrawal requests begins, FTX's Twitter still
   claims "assets are fine"; `Nov 8, ~09:00 UTC` FTX halts withdrawals while the trading UI and API stay live and
   accepting orders for several more hours; `Nov 11` Chapter 11 filing, ~$8B customer-fund shortfall revealed
   (commingling with Alameda's trading book). The critical property: **order-submission and price feeds looked
   completely healthy for ~48h after the first credible solvency signal** — a scenario harness gated only on
   connectivity (scenario 01's shape) would have seen nothing wrong until the withdrawal halt itself.
2. **Celsius Network, June 2022** — the "gradual freeze, formal pause, then bankruptcy weeks later" shape. `Jun 12`
   Celsius pauses all withdrawals/swaps/transfers citing "extreme market conditions," frames it as temporary; `Jul 13`
   files Chapter 11, by which point the pause had been continuous for a month. Models the SLOW variant: a multi-week gap
   between freeze and formal insolvency, vs. FTX's ~3-day collapse.

Both are modelled as sub-shapes of one scenario (parameterised by `freeze_to_bankruptcy_days`) rather than two separate
files, mirroring how scenario 03 parameterises `pause_mode`.

### Trigger condition (synthetic injection) — staged, NOT instantaneous

Unlike scenario 01 (an instantaneous connectivity cut), this scenario's defining property is that **each stage is
individually plausible and only becomes alarming in combination** — the harness must inject a believable earlier-stage
signal before the hard freeze, or it under-tests the "did we act on early warning" question the FTX referent raises.

For the chosen venue `V ∈ {bybit, deribit, binance, okx, hyperliquid, aster}`:

(a) **`soft_signal` at `T+0`** — harness injects one or more of: `withdrawal_processing_delay_seconds` on the venue's
withdrawal-status-check endpoint growing from baseline (~minutes) to `soft_signal_delay_minutes` (parameterised: 30 /
180 / 1440), OR a synthetic `treasury_balance_reconciliation` mismatch of `soft_signal_drift_usd` between the venue's
reported balance and the position ledger's expected balance (parameterised: $5k / $50k /
$500k — deliberately spanning
below and above the shipped `balance_drift_usd` threshold of $1000, per
`unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/thresholds.py:214-223`). Trading APIs,
price feeds, and order submission on `V` remain **fully live and unmutated** during this stage — this is the whole point
of the scenario.

(b) **`hard_freeze` at `T + freeze_delay_hours`** (parameterised: 3 / 48 / 720 — spanning FTX's ~3h public-to-halt
window through Celsius's ~30-day pause-to-filing window) — harness flips the venue's withdrawal endpoint to return a
synthetic rejection (`WithdrawalRejected(reason="venue_paused", venue=V)`) for every withdrawal attempt, regardless of
size or approval status. `RAW_TICK` (price/book/funding) and `ORDER` (new position entry) on `V` are **deliberately left
live** for `trading_continues_after_freeze_hours` (parameterised: 0 / 6 / 48 — FTX's trading-stayed-up-after-halt window
was on this order), matching the observed real-world shape before either scenario branches.

(c) **`insolvency_confirmed` at `T + freeze_delay_hours + insolvency_lag_days`** (parameterised: 3 / 30, matching FTX
vs. Celsius) — harness emits a synthetic bankruptcy-filing-equivalent event; existing balance on `V` is marked
`IMPAIRED` with `recovery_fraction` (parameterised: 0.0 / 0.15 / 0.77 — FTX's eventual creditor-recovery estimates
ranged widely over the real proceeding) rather than deleted outright, modelling the years-long, partial-recovery reality
rather than a clean full loss.

All stages `synthetic=true` per UAC scenario contract (Phase 1.B); no real venue traffic touched.

### Observable signature (in event stream + dashboards)

- **Stage (a)**: `AlertCode.BALANCE_DRIFT` (event_pattern `BALANCE_DRIFT`, severity WARN, channel TELEGRAM) fires once
  `soft_signal_drift_usd` crosses the shipped `balance_drift_usd` threshold
  (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py:628-635`). **This is the ONLY
  shipped signal this scenario's stage (a) can currently produce** — there is no shipped AlertCode for
  withdrawal-processing-delay-without-drift (the `soft_signal_delay_minutes` sub-shape), which is itself a finding this
  scenario surfaces (see Gaps below).
- **Stage (b)**: `CircuitBreakerId.CUSTODY_DISCONNECT_SECONDS`
  (`unified-api-contracts/unified_api_contracts/registry/circuit_breakers/carry_staked_basis.py:242-254`, GLOBAL scope,
  `applies_to="*"`, described as "Copper/CEFFU unreachable >= 180[s/min — the BreakerConfig's own `threshold_value=180`
  / `threshold_unit=MINUTES` and its description's "180s" wording disagree; cite both verbatim rather than resolve the
  ambiguity here) does **NOT** fire — the venue's custody endpoint is fully reachable and returning 200s; only the
  WITHDRAWAL operation itself is rejected. **This is the scenario's central coverage-gap finding**: the one shipped
  breaker adjacent to this failure mode is keyed on endpoint unreachability, not on withdrawal-request rejection while
  reachable — FTX's "trading UI looked fine" property would not have tripped it. The withdrawal-approval quorum request
  (per `unified-api-contracts/unified_api_contracts/registry/withdrawal_approval_rules.py` — MEDIUM $10k-$100k = 2-of-M,
  LARGE > $100k = 3-of-M approvers from the `{operator:ikenna, operator:harsh, operator:system_admin}` pool) is raised
  as normal but never resolves — the scenario asserts this manifests as a **stuck-pending approval request**, not an
  error, which is itself silent unless something pages on request age.
- **Stage (c)**: no shipped `AlertCode` exists for "position confirmed impaired, partial-recovery expected" — nearest
  shipped analog is `RiskType.WITHDRAWAL_DELAY`
  (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/risk_taxonomy.py:48`), which is a risk-taxonomy
  classification field, not an alert/breaker. The scenario asserts the position is marked `IMPAIRED` and removed from
  live P&L (same treatment as scenario 17's Aave-freeze `IMPAIRED` handling) rather than either continuing to mark it at
  last-known-price or zeroing it — matching the multi-year partial-recovery reality, not a clean binary loss.

### Mutation spec (UAC `ScenarioMutationSpec` discriminated-union member)

- Mutation types: stage (a) = custom `TreasuryBalanceMismatch(drift_usd=soft_signal_drift_usd)` on EVENT layer (no
  closed-union member exists for this yet — same Phase-4-follow-up gap scenario 01 hit for `VenueConnectionClose`).
  Stage (b) = custom `WithdrawalRejected(reason="venue_paused")` on EVENT layer — deliberately NOT `RejectFills` (that
  mutation, used by scenario 01, targets ORDER-layer trading rejects; this scenario needs a withdrawal-specific reject
  that does NOT also reject new orders, the opposite shape). Stage (c) = custom
  `PositionImpairment(recovery_fraction=...)` applied at the position-ledger layer. **None of the three are members of
  the Phase 1.B closed-union
  (`DropRows | StaleHold | PriceShift | BookSpoof | LatencyInject | RejectFills | OracleDeviate | GasSurge | ManifestPhantom | EventDrop | EventDuplicate`)**
  — this scenario cannot be implemented against the current mutation union without adding new members, more so than
  scenario 01's single-member gap.
- Parameters:
  - `venue: Literal["bybit", "deribit", "binance", "okx", "hyperliquid", "aster"]`
  - `soft_signal_delay_minutes: int` (matrix: 30 / 180 / 1440)
  - `soft_signal_drift_usd: Decimal` (matrix: 5000 / 50000 / 500000)
  - `freeze_delay_hours: int` (matrix: 3 / 48 / 720)
  - `trading_continues_after_freeze_hours: int` (matrix: 0 / 6 / 48)
  - `insolvency_lag_days: int` (matrix: 3 / 30)
  - `recovery_fraction: Decimal` (matrix: 0.0 / 0.15 / 0.77)
- Pipeline tap layer: primary `ScenarioOverlayLayer.EVENT` (treasury reconciliation + withdrawal-endpoint synthesis);
  secondary `ScenarioOverlayLayer.ORDER` only once `hard_freeze` fires AND `trading_continues_after_freeze_hours`
  elapses (new-order blocking starts late, not immediately — the inverse ordering of scenario 01).
- `available_at` discipline: `RAW_TICK` is UNCHANGED throughout stages (a)/(b) — no `StaleHold`, no lookahead-bias
  concern, since the whole point is that price data stays honest while custody doesn't. Only stage (c)'s position ledger
  write needs the standard `_synthetic_available_at_shift` stamp.

### Expected outcomes (per archetype × per layer)

| Archetype                                         | Stage (a) response                                                                                                                                                                                                                                                                                | Stage (b) response                                                                                                                                                                                                                                                                                                                                                                             | Stage (c) response                                                                                                                                                                                                                                               |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ARBITRAGE_PRICE_DISPERSION` (primary)            | `BALANCE_DRIFT` fires (WARN/TELEGRAM); asserted behavior is `PAUSE_NEW_ENTRIES` on `V` pending manual reconciliation — **no shipped `BreakerConfig` currently wires `BALANCE_DRIFT` to an automatic `BreakerAction`**, this is asserted as a proposed response, not verified against shipped code | Withdrawal request stuck pending quorum; margin on `V` becomes **trapped but not yet lost** — asserted: existing position held (cannot rebalance out via withdrawal), new entries to `V` blocked once `trading_continues_after_freeze_hours` elapses via a proposed `KILL_PER_TREASURY_<source>` / `KILL_PER_VENUE_<V>` arm (both real `KillSwitchId` members, `kill_switch.py:87-92,103-124`) | Position marked `IMPAIRED`, removed from live P&L at `recovery_fraction × notional`; asserted `KillSwitchProvenance=BREAKER_AUTO`, requires `MANUAL_UNKILL` (never auto-recovers — no `BreakerRecoveryRule` should exist for a confirmed-insolvent counterparty) |
| `CARRY_STAKED_BASIS` (hedge-leg secondary)        | Same `BALANCE_DRIFT` signal; hedge leg on `V` flagged at-risk                                                                                                                                                                                                                                     | Asserted: attempt to CLOSE the hedge leg on `V` (cheapest exit) BEFORE attempting withdrawal — mirrors scenario 17's "close hedge leg first, attempt withdraw second" auto-response ladder ordering, since closing a position is possible right up until `V` itself halts matching, even after withdrawals freeze                                                                              | Same `IMPAIRED` treatment; if the DeFi leg of the pair loses its hedge, asserted escalation into `LIQUIDATION_CASCADE_RISK` per scenario 17's composition                                                                                                        |
| `ML_DIRECTIONAL_CONTINUOUS` (CeFi-only, tertiary) | Same `BALANCE_DRIFT` signal on whichever of OKX/Binance/Bybit is `V`                                                                                                                                                                                                                              | Asserted `KILL_PER_ARCHETYPE_ML_DIRECTIONAL_CONTINUOUS` arms once frozen (the one `KillSwitchId` explicitly scoped to this archetype, `kill_switch.py`) — asserted NOT to cascade to DeFi strategies, per that switch's own documented isolation guarantee                                                                                                                                     | Position marked `IMPAIRED` same as above                                                                                                                                                                                                                         |

### Auto-recovery contract — deliberately asymmetric with scenario 01

Scenario 01's `VENUE_OUTAGE_SECONDS` breaker auto-disarms after 5min of green heartbeats (`AUTO_COOLDOWN`). This
scenario's escalated state must NOT behave that way: a confirmed counterparty insolvency has no "green heartbeat" signal
that means anything — the venue can stay perfectly reachable (per stage (b)'s own design) while remaining insolvent for
years. The scenario therefore asserts:

- Stage (a)'s response (if any shipped/proposed `BreakerAction` exists) may be `AUTO_COOLDOWN`-eligible — a balance
  drift can be a false positive (reconciliation lag, not insolvency).
- Stage (b) onward MUST require `KillSwitchProvenance` transition only via `MANUAL_UNKILL` — the scenario explicitly
  asserts that no combination of connectivity/heartbeat/price-feed health alone is sufficient to auto-disarm a
  withdrawal-freeze-triggered kill switch, since none of those signals distinguish "temporarily paused, coming back"
  from "insolvent, gone."

### Composes with

- **Scenario 01 `cefi_venue_circuit_breaker_trip`** — the connectivity-outage analog this scenario is deliberately the
  INVERSE of (venue down vs. venue up-but-insolvent). A harness that only implements scenario 01's shape has zero
  coverage for this one.
- **Scenario 15 `liquidation_proximity_auto_deleverage`** / **Scenario 17 `lrt_lending_meltdown_composite`** — the
  DeFi-side analogs (Aave Guardian freeze). This scenario is the CeFi-domain sibling of the same underlying failure
  class (a custodian/protocol unilaterally blocking withdrawals); the `IMPAIRED`-position treatment and the
  close-hedge-before-attempt-withdraw response ordering are deliberately copied from scenario 17 rather than
  re-invented, since the two domains converge on the same correct response shape.

### Gaps this scenario surfaces (do NOT silently assume these are covered)

1. **No shipped breaker distinguishes "endpoint reachable, operation rejected" from "endpoint unreachable."**
   `CUSTODY_DISCONNECT_SECONDS` is a pure connectivity check; this scenario's stage (b) does not trip it by design. This
   is the scenario's single most important finding — a real FTX-shaped event would sail past this breaker entirely.
2. **`BALANCE_DRIFT` has no wired `BreakerAction`** in any `BreakerConfig` found during this doc's research — it is an
   `AlertRule` (paging channel) only. Whether a drift alert alone should ever auto-block new entries (vs. paging a
   human) is an operator judgment call, not assumed here.
3. **`WithdrawalReconciler`** — referenced by name in `kill_switch.py`'s own docstrings ("Armed by WithdrawalReconciler
   on balance drift > emergency threshold") as the arming mechanism for all four `KILL_PER_TREASURY_*` switches, but no
   class or module of that name exists anywhere in `unified-api-contracts` or `execution-service` as of this doc's
   authoring — it is a **named-but-unbuilt** component. This scenario cannot be implemented until it (or an equivalent)
   ships.
4. **`TreasurySource` only explicitly names Binance (`CEFFU`) and Hyperliquid/dYdX sub-accounts** among the six CeFi
   perp venues this doc's Applies-to row lists; Bybit/Deribit/OKX/Aster custody routing has no corresponding
   `TreasurySource` member found. Either those four venues route through `DEFI_HOT_WALLET`/`COPPER` today, or the
   registry is incomplete for them — not resolved by this doc, flagged for the scenario's Phase-2 implementer to check
   before assuming per-venue treasury-kill-switch coverage exists for all six.

### Cross-references / prior art

- `ScenarioCategory` closed-set-7 enum:
  `unified-api-contracts/unified_api_contracts/canonical/crosscutting/scenario_overlay/_enums.py:12-42`.
- `KillSwitchId.KILL_PER_TREASURY_{COPPER,CEFFU,DEFI_HOT_WALLET}` + `KILL_PER_TREASURY_SUB_ACCOUNT_{HYPERLIQUID,DYDX}`,
  all "Armed by WithdrawalReconciler on balance drift > emergency threshold":
  `unified-api-contracts/unified_api_contracts/canonical/crosscutting/kill_switch.py:103-124`.
- `TreasurySource` enum: `unified-api-contracts/unified_api_contracts/internal/domain/treasury.py:23-49`.
- `withdrawal_approval_rules.py` N-of-M quorum (MEDIUM $10k-$100k = 2-of-M, LARGE > $100k = 3-of-M):
  `unified-api-contracts/unified_api_contracts/registry/withdrawal_approval_rules.py`.
- `AlertCode.BALANCE_DRIFT` + `balance_drift_usd` threshold ($1000 default, quietness-baselined 2026-05-20 to
  2026-05-22): `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py:628-635`,
  `.../alerting/thresholds.py:214-223`.
- `CircuitBreakerId.CUSTODY_DISCONNECT_SECONDS` + its `BreakerRecoveryRule`:
  `unified-api-contracts/unified_api_contracts/registry/circuit_breakers/carry_staked_basis.py:242-254,366-370`.
- `RiskType.WITHDRAWAL_DELAY`: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/risk_taxonomy.py:48`.
- `KillSwitchId.KILL_PER_ARCHETYPE_ML_DIRECTIONAL_CONTINUOUS` (CeFi-only, OKX+Binance+Bybit, isolation from DeFi
  documented on the switch itself): `unified-api-contracts/unified_api_contracts/canonical/crosscutting/kill_switch.py`.
- Historical incidents modelled: FTX Nov 2022 (trading-continues-after-freeze shape), Celsius Jun-Jul 2022
  (gradual-freeze-to-bankruptcy shape) — citations in § Real-world referent above.

**Phase 4 follow-up (deferred — captured per Capture-Discoveries HARD RULE)**:

- Build `WithdrawalReconciler` (or equivalent) — currently named-only across 4+ docstring references in `kill_switch.py`
  but zero implementation found. Blocking dependency for this scenario's stage (b)/(c) to be more than a design spec.
- Add `TreasuryBalanceMismatch` / `WithdrawalRejected` / `PositionImpairment` as first-class `ScenarioMutationSpec`
  closed-union members (Phase 1.B, same follow-up class as scenario 01's `VenueConnectionClose` gap).
- Resolve the `CUSTODY_DISCONNECT_SECONDS` `threshold_value=180`/`MINUTES` vs. description-text `"180s"` unit ambiguity
  in `carry_staked_basis.py:242-254` — found during this doc's research, not fixed here (out of scope for a
  scenario-design doc; flagged for whoever next touches that `BreakerConfig`).
- Decide whether `BALANCE_DRIFT` should gain a wired `BreakerAction` (auto-pause new entries on drift) or stay page-only
  forever — an operator risk-appetite call, not a mechanical fix.
