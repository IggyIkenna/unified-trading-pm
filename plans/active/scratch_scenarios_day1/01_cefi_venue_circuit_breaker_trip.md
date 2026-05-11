## Scenario `cefi_venue_circuit_breaker_trip` — Per-venue trading halt (CeFi)

| Field | Value |
|---|---|
| `scenario_id` | `cefi_venue_circuit_breaker_trip` |
| Category | `VENUE_OUTAGE` |
| Layer | `EVENT` primary (WS feed close / REST 503 synthesised at the ingress boundary); `ORDER` secondary (matching-engine `RejectFills` after halt window opens). `RAW_TICK` is optional (`StaleHold` on the venue's tick stream to mirror feed-staleness). Three taps total. |
| Asset groups | `frozenset({MarketAssetGroup.CEFI})` |
| Applies-to | per-venue (one CeFi perp venue at a time; closed-set: `bybit` / `deribit` / `binance` / `okx` / `hyperliquid` / `aster`) |
| Targets archetype(s) | `ARBITRAGE_PRICE_DISPERSION` (primary — hedge leg of the funding-arb pair runs on the halted venue); `CARRY_STAKED_BASIS` (secondary — if the LST-leverage hedge leg uses the halted perp venue for delta neutralisation) |

### Real-world referent

Models four recurring failure modes from 2024-2025: (1) **Binance 2024-04 BTCUSDT-perp matching-engine pause** during a high-volatility CPI print (REST 503 for ~8 min, WS feed froze, hedge-arb books one-sided for the duration); (2) **Bybit 2024-12 unscheduled spot+derivatives halt** announced as "maintenance" mid-session, ~20 min, while open positions accumulated funding cost and could not be unwound; (3) **OKX 2025-02 partial outage** where REST stayed live but WS subscriptions disconnected (silent staleness — orders accepted but no fill confirmation); (4) **Hyperliquid 2024-10 BSC RPC cascade** where the venue's own infra failed but hedge venues stayed up — created cross-venue divergence + asymmetric inventory. The scenario must exercise both REST-503 and WS-only-down sub-shapes because they trigger different breakers.

### Trigger condition (synthetic injection)

At wall-clock `T+0` (start-of-day fixture or scenario runner kick-off), for the chosen venue `V ∈ {bybit, deribit, binance, okx, hyperliquid, aster}` the harness simultaneously:

1. Emits a synthetic `connection_close(reason="maintenance", code=1001)` event into the WS feed stream for ALL subscribed instruments on `V`.
2. Routes all `V`-bound REST adapter calls through a fault-injector returning HTTP 503 with `Retry-After: 120`.
3. Holds last-known mid (`StaleHold` mutation on RAW_TICK layer) for `V`'s instruments for `outage_duration_seconds` (parameterised, default 300s; matrix variants 90s / 300s / 900s).
4. After `outage_duration_seconds`, restores WS + REST in a single step (`recovery_curve="step"`) or over a 120s ramp (`recovery_curve="ramp_120s"`) — both variants run.

The injection is correlation-id-tagged `synthetic=true` per UAC scenario contract (Phase 1.B). No real venue traffic is touched; this is an in-process mutation on the EVENT and ORDER taps registered by Phase 3.E + 3.F.

### Observable signature (in event stream + dashboards)

- WS-feed-staleness event: `CONNECTIVITY_GAP_DETECTED` fires from MTDS `LiveConnectivityWatchdog` within ~5s of the synthetic `connection_close` (per `codes.py:204-211`).
- `TICK_STALENESS` from MDPS write-gate within ~15s as the inter-tick gap on `V` crosses the per-venue baseline (per `codes.py:196-203`).
- Order-rejection rate spike on `V`: `ORDER_REJECTION_SPIKE` (`codes.py:77`) fires once the 5min rolling window crosses the `REJECT_RATE_BPS` threshold of 500bps (per `registry/circuit_breakers/arbitrage_price_dispersion.py:127-140`).
- Position-balance-monitor diff with venue REST: PBM cannot reconcile (REST 503), emits `RECON_DEGRADED` (`codes.py:70`) for `V` after `recon_degraded_seconds` default 60s.
- Autonomous-recovery state transitions: `CIRCUIT_BREAKER_DEGRADED` (post-`REJECT_RATE_BPS`) → `CIRCUIT_BREAKER_OPEN` (post-`VENUE_OUTAGE_SECONDS`), per `codes.py:42-45`.
- Cross-venue divergence as the other 5 perp venues continue trading: `CROSS_VENUE_DIVERGENCE_BPS` breaker fires after 120s window if same-instrument mid diverges ≥40bps (per `registry/circuit_breakers/arbitrage_price_dispersion.py:80-93`).
- Hedge-gap alert: `UNHEDGED_POSITION_ALERT` (`codes.py:84`) fires if the existing position on `V` cannot be unwound and the cross-venue hedge drifts > $100k notional (`HEDGE_GAP_NOTIONAL_USD` breaker, `arbitrage_price_dispersion.py:158-172`).
- Kill-switch arming: `KILL_SWITCH_VENUE_DISCONNECT` (`codes.py:34`) fires with `provenance=BREAKER_AUTO`, `switch_id=KILL_PER_VENUE_<V>` (per `kill_switch.py:83-88`).

### Mutation spec (UAC `ScenarioMutationSpec` discriminated-union member)

- Mutation types (composite — three taps): `LatencyInject + RejectFills` (ORDER layer) + `StaleHold` (RAW_TICK layer) + custom `VenueConnectionClose` synthesized event on EVENT layer. **Phase 4 follow-up**: `VenueConnectionClose` is NOT yet a member of the Phase 1.B closed-union (`DropRows | StaleHold | PriceShift | BookSpoof | LatencyInject | RejectFills | OracleDeviate | GasSurge | ManifestPhantom | EventDrop | EventDuplicate` per plan body lines 343-345). **Decision**: model the venue-halt as `RejectFills(reason="VENUE_HALTED", rest_status_code=503, ws_close_code=1001)` on ORDER layer + `StaleHold(hold_duration_seconds=outage_duration_seconds)` on RAW_TICK layer + `EventDrop(stream="ws_heartbeat")` on EVENT layer. No new mutation member needed for the pre-cutover 6-scenario subset; post-cutover plan should add a dedicated `VenueOutage` mutation for cleaner semantics.
- Parameters:
  - `venue: Literal["bybit", "deribit", "binance", "okx", "hyperliquid", "aster"]`
  - `data_types: frozenset({"trades", "orderbook", "funding_rate", "position", "order_status"})`
  - `outage_duration_seconds: int` (matrix: 90 / 300 / 900)
  - `recovery_curve: Literal["step", "ramp_120s"]`
  - `rest_status_code: int = 503`
  - `ws_close_code: int = 1001`
  - `rest_retry_after_seconds: int = 120`
- Pipeline tap layer: primary `ScenarioOverlayLayer.EVENT` (ingress synthetic events) + secondary `ScenarioOverlayLayer.ORDER` (`RejectFills` on matching-engine adversarial mode per Phase 3.E) + tertiary `ScenarioOverlayLayer.RAW_TICK` (`StaleHold` per Phase 3.A). Three-layer scenario.
- `available_at` discipline: `StaleHold` SHIFTS `available_at` for the held window (last-known tick reused with newer `available_at` stamps). Per Phase 2.E (plan lines 397-401), the applier MUST stamp `_synthetic_available_at_shift: bool = True` on affected rows so UTL `lookahead_bias_check(scenario_overlay_active=True)` downgrades to a structured warning rather than raising `LookaheadBiasError`. Strict mode stays ON for all non-overlay paths.

### Expected outcomes (per archetype × per layer)

| Archetype | `RiskRuleConsequence` | Breaker(s) tripped (cite by `breaker_id` from UAC registry) | `BreakerAction` | `KillSwitchId` armed (if any) | `AlertCode` fired | `expected_within` |
|---|---|---|---|---|---|---|
| `ARBITRAGE_PRICE_DISPERSION` (primary) | `BLOCK` on new `V`-bound orders via `MAX_POSITION_SIZE_PER_VENUE` (`registry/risk_rules/venue.py:80`) re-evaluating against stale state; pre-flight rejects | `VENUE_OUTAGE_SECONDS` (`registry/circuit_breakers/carry_staked_basis.py:126-138`, scope=PER_VENUE, applies_to="*", 90s threshold) + `REJECT_RATE_BPS` (`arbitrage_price_dispersion.py:127-140`) + `CROSS_VENUE_DIVERGENCE_BPS` if window > 120s (`arbitrage_price_dispersion.py:80-93`) | `BLOCK_NEW` (VENUE_OUTAGE_SECONDS) + `BLOCK_NEW` (REJECT_RATE_BPS) + `BLOCK_NEW` (CROSS_VENUE_DIVERGENCE_BPS); ESCALATES to `CANCEL_OPEN` via `INVENTORY_IMBALANCE_RATIO` (`arbitrage_price_dispersion.py:95-109`) if cross-venue inventory imbalance > 20% during the halt | `KILL_PER_VENUE_<V>` (e.g. `KILL_PER_VENUE_BYBIT`, `kill_switch.py:83`); ESCALATES to `KILL_ALL_LIVE` (`kill_switch.py:74`) only if `HEDGE_GAP_NOTIONAL_USD` breaker also fires (>$100k unhedged) | `CONNECTIVITY_GAP_DETECTED` (≤5s) → `TICK_STALENESS` (≤15s) → `ORDER_REJECTION_SPIKE` (≤30s) → `CIRCUIT_BREAKER_DEGRADED` (≤60s) → `CIRCUIT_BREAKER_OPEN` (≤90s) → `KILL_SWITCH_VENUE_DISCONNECT` (≤95s) → `UNHEDGED_POSITION_ALERT` (≤120s if hedge gap accrues) | 120s end-to-end for full breaker-trip + kill-switch arm; 5s for first connectivity alert |
| `CARRY_STAKED_BASIS` (hedge-leg secondary) | `BLOCK` on rebalance instructions targeting `V` (pre-flight via `MAX_OI_PER_VENUE`, `venue.py:60`) | `VENUE_OUTAGE_SECONDS` (shared with primary, scope=PER_VENUE applies_to="*"); secondary trip if rebalance failure cascades into `LIQUIDATION_CASCADE_RISK` (`carry_staked_basis.py:110-124`) on the DeFi leg because hedge can't refresh | `BLOCK_NEW` (VENUE_OUTAGE_SECONDS); ESCALATES to `KILL_ALL` if `LIQUIDATION_CASCADE_RISK` fires | `KILL_PER_VENUE_<V>` + potentially `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` (`kill_switch.py:79`) if liquidation-cascade trips | `CONNECTIVITY_GAP_DETECTED` + `CIRCUIT_BREAKER_OPEN`; `DEFI_HEALTH_FACTOR_CRITICAL` (`codes.py:48`) only if hedge-failure propagates to LST leverage; `KILL_SWITCH_DEFI_LIQUIDATION_RISK` (`codes.py:32`) only at full escalation | 120s for venue-level breaker; 600s for cascade-into-DeFi-leg escalation (slower because depends on real on-chain HF refresh) |

### Auto-recovery contract (per DR plan `BreakerRecoveryRule`)

The primary breaker for this scenario is `CircuitBreakerId.VENUE_OUTAGE_SECONDS`. Its `BreakerRecoveryRule` (per `registry/circuit_breakers/carry_staked_basis.py:220-225`) is:

```
BreakerRecoveryRule(
    breaker_id=CircuitBreakerId.VENUE_OUTAGE_SECONDS,
    guard_description="Venue REST + WS heartbeats green for >= 5min.",
    retry_policy="exponential",
    auto_disarm_after_seconds=300,
)
```

Because the breaker's `action=BLOCK_NEW`, `BREAKER_RECOVERY_DEFAULTS[BLOCK_NEW] = AUTO_COOLDOWN` (per `circuit_breaker.py:235-240`). So after the venue's REST + WS heartbeats stay green for 5min sustained, the breaker auto-disarms and `KILL_SWITCH_AUTO_RECOVERED` (`codes.py:171`) fires with `cooldown_seconds_elapsed` reflecting actual elapsed time. The scenario MUST assert the auto-disarm path completes when `recovery_curve="step"` AND the post-recovery quiet window exceeds 300s; for `recovery_curve="ramp_120s"` with `outage_duration_seconds=900`, the assertion is auto-disarm within 600s of recovery start.

**Escalation paths that REQUIRE manual unkill**: if `INVENTORY_IMBALANCE_RATIO` (CANCEL_OPEN, MANUAL_UNKILL per defaults) or `HEDGE_GAP_NOTIONAL_USD` (KILL_ALL, MANUAL_UNKILL) trip during the outage, those breakers stay armed until operator action. Scenario asserts `KILL_SWITCH_MANUAL_UNKILLED` is the ONLY exit path for those, and that the auto-disarm of `VENUE_OUTAGE_SECONDS` does NOT cascade-disarm the escalated breakers (orthogonal recovery).

### Cross-references / prior art

- UAC `BreakerConfig` entry: `unified-api-contracts/unified_api_contracts/registry/circuit_breakers/carry_staked_basis.py:126-138` (VENUE_OUTAGE_SECONDS, PER_VENUE, applies_to="*"). Shared across archetypes; no archetype-specific override needed.
- UAC `BreakerRecoveryRule`: same file, `:220-225`.
- DR plan `disaster_recovery_circuit_breakers_2026_05_10.md` § Phase 1.B (BreakerAction closed-set) + Phase 1.C-D (KillSwitchId / KillSwitchProvenance / KillSwitchArmRequest+ArmedEvent+DisarmEvent) — all shipped per `unified-api-contracts/unified_api_contracts/canonical/crosscutting/kill_switch.py:74-93`.
- Risk plan `risk_simulations_limits_alerting_2026_05_10.md` § Phase 2.B VenueRules: `unified-api-contracts/unified_api_contracts/registry/risk_rules/venue.py:55-246` (6 perp venues × 3 rules = 18 rules; this scenario exercises the BLOCK consequence on `MAX_POSITION_SIZE_PER_VENUE` + `MAX_OI_PER_VENUE` for `applies_to=<V>`).
- Existing matching-engine adversarial mode hooks: `execution-service/execution_service/matching_engine/{engine,trade_matcher}.py` — Phase 3.E of THIS plan (`simulation_scenarios_topology_price_shocks_2026_05_09.md:432-436`) extends those with `RejectFills` mutation. Scenario consumes the extension.
- Connectivity-gap alerting taxonomy: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/codes.py:186-227` (TICK_STALENESS / CONNECTIVITY_GAP_DETECTED / CONNECTIVITY_RECOVERED / CONNECTIVITY_GAP_BACKFILLED — 4-event lifecycle, all 4 fire in this scenario's full timeline).
- Historical incidents modelled: Binance 2024-04 BTCUSDT-perp halt, Bybit 2024-12 unscheduled maintenance, OKX 2025-02 WS-only outage, Hyperliquid 2024-10 BSC RPC cascade (citations in § Real-world referent above).

**Phase 4 follow-up (deferred — captured per Capture-Discoveries HARD RULE)**:
- Add `VenueOutage` as a first-class member of `ScenarioMutationSpec` closed-union (plan body line 343-345) so this scenario can stop composing three primitive mutations and use a single typed spec. Owner: successor plan `simulation_scenarios_post_cutover_2026_06_01.md` Phase 1.B extension.
- No literal `VENUE_HALTED` AlertCode in current closed-set — the scenario currently maps to `CIRCUIT_BREAKER_OPEN` + `KILL_SWITCH_VENUE_DISCONNECT`. If operator UX wants a distinct "venue halted" label in dashboards, add `VENUE_HALTED = "VENUE_HALTED"` to `AlertCode` enum (`codes.py`) in successor plan Phase 1.E.
