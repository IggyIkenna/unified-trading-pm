## Scenario `defi_oracle_deviation_30sigma` — Chainlink/Pyth oracle stale-or-wild

| Field                | Value                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scenario_id`        | `defi_oracle_deviation_30sigma`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Category             | `PRICE_SHOCK` (wild-print variant — 30σ deviation against realized) + `STALENESS` (heartbeat-stall variant) + `DATA_CORRUPTION` (zero-print / publisher-collusion sub-shape of wild-print). Three sub-categories run as one scenario with two declared variants (a) `wild_print` and (b) `stale_hold`.                                                                                                                                                                                                                                               |
| Layer                | `RAW_TICK` (oracle feed at ingress: Pyth Hermes batch + PythNet live for Solana; Chainlink `AggregatorV3.latestRoundData()` for Ethereum/L2) + `FEATURE` (downstream oracle-derived features: LST yield curves, USDC/USDT/USDE peg deviation, perp-basis reference mid). Two-layer scenario per Phase 3.A + 3.C wire-ins.                                                                                                                                                                                                                            |
| Asset groups         | `frozenset({MarketAssetGroup.DEFI})`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Applies-to           | per-chain × per-asset (closed-set per `CHAIN_RPC_TEMPLATES` UAC `registry/capability_declarations/_defi.py` + 2026-05-06 Pyth-unban directive): **Solana → Pyth** (`USDC/USD`, `SOL/USD`, `JITO-SOL/SOL`, `MARINADE-SOL/SOL`, `SANCTUM-LST/SOL`); **Ethereum + L2 → Chainlink** (`USDC/USD`, `USDT/USD`, `ETH/USD`, `BTC/USD`, `WEETH/ETH`, `RETH/ETH`, `WSTETH/ETH`). Each oracle ID maps to a concrete aggregator address (Chainlink) or feed account pubkey (Pyth) — pulled from `config/testnet_contracts.yaml` validated by `PROTOCOL_SCHEMAS`. |
| Targets archetype(s) | `CARRY_STAKED_BASIS` (primary — LST yield-leverage strategy directly consumes Pyth LST/SOL prices for sizing + Chainlink USDC/USD peg for collateral haircut + Aave health-factor refresh; cannot rebalance or deleverage without a fresh, in-band oracle); `ARBITRAGE_PRICE_DISPERSION` (secondary — perp-vs-spot basis derived using spot oracle as reference; wild-print produces a synthetic basis blowout, stale-print produces a frozen reference that diverges from realized perp mid)                                                        |

### Real-world referent

Models four canonical oracle-failure precedents. (1) **Chainlink GMX-V1 AVAX-USD wild-print 2022-09-18** — a
co-ordinated thin-book pump on a Chainlink aggregator's source DEX moved the median print ~12% off realized; GMX V1
priced liquidations off the wild aggregator value and $565k of solvent positions were liquidated before the keeper bot
caught up. Wild-print sub-shape: single-update spike, reverts on next heartbeat. (2) **Chainlink LUNA depeg zero-print
2022-05-12** — during the UST depeg cascade, LUNA's Chainlink aggregator emitted `0` for ~25 minutes when source DEXes
halted and the aggregator's `minAnswer` floor was hit (the now-deprecated `minAnswer`/`maxAnswer` clamp returned
`minAnswer` instead of `revert`). Zero-print sub-shape of wild-print — covered by `OracleDeviate` mutation with
`target_price=0`. (3) **Pyth Solana SHIB / DOGE wild-print 2024-03-08** — Hermes publisher-aggregation logic surfaced a
single mis-quoting publisher's outlier as the canonical price for ~400ms before the aggregator's confidence-interval
filter caught it; downstream Solana DeFi protocols (Drift, Mango, Kamino) all paused liquidations. (4) **Pyth heartbeat
stall 2024-Q1 Solana congestion** — during a Jito-bundle MEV storm, Pyth's per-feed heartbeat (nominal 400ms) silently
lapsed 5-15s for ~7 minutes; the canonical `is_valid` flag stayed true (publishers were still online) but the staleness
was unrepresented. Stale-print sub-shape — heartbeat skipped without an `is_valid=false` signal.

### Trigger condition (synthetic injection)

Two variants run as separate sub-scenarios under the same `scenario_id`, parameterised via `variant` field:

(a) **`wild_print`** — at wall-clock `T+0` the harness publishes a single oracle update with
`price = realized_mid * (1 + sign * deviation_sigma * rolling_sigma_60s)` for `deviation_duration_heartbeats=1`
heartbeat, then reverts. For Pyth (400ms heartbeat) this is a ~400ms spike; for Chainlink (per-feed heartbeat, typically
60min for ETH/USD, 24h for stablecoin pegs, 1hr for LSTs) this is one full heartbeat at the wild value.
`deviation_sigma=30` default; matrix variants 10σ / 30σ / 100σ (`100σ` covers the zero-print shape). Sign matrix: ±1
(positive + negative); for stablecoin oracles, negative spike (depeg-down) is the operative correctness test. Wild-print
update carries a synthetic `confidence_interval` consistent with the wild value so downstream `min_confidence_interval`
filters don't trivially reject — the test is whether deviation-vs-canonical-mid trips correctly, not whether
confidence-filtering trips.

(b) **`stale_hold`** — at `T+0` the harness skips `stale_duration_heartbeats=3` consecutive heartbeats (or
`stale_duration_seconds` absolute for chains with very-long Chainlink heartbeats). For Pyth (400ms heartbeat): minimum
stale duration 1.2s, matrix variants 1.2s / 10s / 60s. For Chainlink AggregatorV3 ETH/USD (60min heartbeat): minimum 3hr
(3 missed heartbeats), matrix variants 3hr / 12hr / 25hr (the last crosses the 24hr `maxAge` safety check most consuming
protocols apply). After `stale_duration`, the harness emits one good heartbeat with `available_at = real_arrival_time`
(no synthetic shift on recovery).

Both variants are `synthetic=true` correlation-tagged per Phase 1.B scenario contract; both layer-tap at RAW_TICK before
features-onchain reads. Both emit `synthetic_provenance=defi_oracle_deviation_30sigma` row metadata so downstream
readers can attribute the perturbation.

### Observable signature (in event stream + dashboards)

- **MTDS RAW_TICK manifest row** — for `stale_hold` variant:
  `record_failed(error=OracleStaleError, attempted_at=<real_now>)` on the (chain, oracle*id, heartbeat-window) shard.
  **FOLLOW-UP**: grep workspace for `OracleStaleError` / `OracleDeviationError` exception classes — if not present in
  UTL `unified_trading_library/errors/` or features-onchain, add to honest-coverage taxonomy under writegate plan Phase
  2.A four-category mapping (currently the canonical names per CLAUDE.md "Reason taxonomy" closed set are
  `EXPECTED*\*`for empty-confirmed, not`OracleStale`— staleness past heartbeat = unexpected upstream gap →`record_failed`, not `record_empty`).
- **features-onchain manifest** — for `wild_print` variant: features that depend on the wild oracle (LST yield,
  peg-deviation, perp-basis-ref) emit `record_failed(error=OracleDeviationError)` for the affected feature-window;
  `available_at` reflects real heartbeat time, not synthetic.
- **Oracle-deviation metric** — `oracle_deviation_bps_<oracle_id>` time-series crosses 100bps threshold (Pyth wild) /
  `oracle_age_seconds_<oracle_id>` time-series crosses heartbeat × 1.5 threshold (Chainlink stale).
- **Peg-deviation feature spike** — for USDC/USDT/USDE wild-prints: `peg_deviation_bps_<stable>` feature spikes beyond
  its 99.5pct historical band within one feature window.
- **Autonomous-recovery state transition** — `oracle_health` state machine in features-onchain transitions
  `green → degraded → red`, mirroring `CIRCUIT_BREAKER_DEGRADED` → `CIRCUIT_BREAKER_OPEN` lifecycle.
- **Deleverage planner back-off** — strategy-service `carry_staked_basis` signal generator emits
  `signal_suppressed(reason="oracle_stale")` / `signal_suppressed(reason="oracle_deviation")` events instead of new
  rebalance instructions for the affected oracle's coverage radius.
- **Alert with provenance** — `DEFI_FEATURE_STALE` (per `codes.py:52`) carries `oracle_id` + `chain` +
  `heartbeat_age_s` + `deviation_bps` + `synthetic=true` + `scenario_id=defi_oracle_deviation_30sigma` in payload.
  (Closer fit than `TICK_STALENESS` because the latter is keyed on `(venue, instrument)` per MDPS; oracle feeds are
  keyed on `(chain, oracle_id)`.)
- **Kill-switch arming** (only at escalation thresholds — see Auto-recovery contract) — `KILL_PER_ASSET_GROUP_DEFI` per
  `kill_switch.py:92` if breaker stays armed > 5min OR if two correlated oracles (e.g. Pyth-SOL/USD + Pyth-JITO-SOL/SOL)
  fail simultaneously.

### Mutation spec (UAC `ScenarioMutationSpec` discriminated-union member)

- Mutation types — composite per variant. `wild_print`: `OracleDeviate` (existing closed-union member per plan body line
  344). `stale_hold`: `StaleHold` (existing member, line 343). No new mutation member needed for the pre-cutover
  6-scenario subset.
- Parameters (`wild_print`):
  - `oracle_id: str` — e.g. `"pyth_solana_jito_sol_sol"` (Pyth feed account pubkey) or
    `"chainlink_ethereum_usdc_usd_0x8fffffd4afb6115b954bd326cbe7b4ba576818f6"` (Chainlink aggregator address).
    Closed-set candidate values enumerated in scenario applicability filter.
  - `chain: Literal["solana", "ethereum", "arbitrum", "base", "polygon"]` (`solana` → Pyth; everything else → Chainlink,
    per CLAUDE.md DeFi pointer chain).
  - `deviation_sigma: Decimal` (matrix: `10` / `30` / `100`).
  - `deviation_sign: Literal[-1, 1]` (matrix: both).
  - `deviation_duration_heartbeats: int = 1`.
  - `confidence_interval_mode: Literal["consistent_with_wild", "honest_realized"]` — `consistent_with_wild` is the
    operative test; `honest_realized` checks the confidence-interval filter path.
- Parameters (`stale_hold`):
  - `oracle_id: str` (same closed set).
  - `chain: Literal[...]` (same).
  - `stale_duration_heartbeats: int` (Pyth matrix: `3` / `25` / `150` = ~1.2s / ~10s / ~60s).
  - `stale_duration_seconds_absolute: int | None` — REQUIRED for Chainlink (variable heartbeat per feed); matrix `10800`
    / `43200` / `90000` = 3hr / 12hr / 25hr.
- Pipeline tap layer: primary `ScenarioOverlayLayer.RAW_TICK` (Pyth Hermes + Chainlink `latestRoundData` ingress in MTDS
  DeFi adapter); secondary `ScenarioOverlayLayer.FEATURE` (features-onchain `_compute_oracle_health` +
  `_compute_lst_yield` + `_compute_peg_deviation` exit, before `record_captured`).
- `available_at` discipline: this mutation does **NOT** synthetically shift `available_at` for downstream rows. The
  whole correctness point of the scenario is that the staleness gap remains honest in the manifest: features-onchain
  emits `record_failed(OracleStaleError, attempted_at=<real_now>)` per honest-absence rule (CLAUDE.md "Honest absence"
  category 2 = unexpected upstream-pipeline gap → STOP, fail-fast, manifest reflects truth), NOT `record_captured` with
  a stale value carrying a fresh `available_at`. Per Phase 2.E, the applier stamps `_synthetic_provenance` but does NOT
  stamp `_synthetic_available_at_shift=True` (no shift to declare). UTL `lookahead_bias_check` stays strict on this
  scenario — the test asserts NO lookahead bias is introduced by the injection itself.

### Expected outcomes (per archetype × per variant)

| Archetype                                          | Variant                                                  | `RiskRuleConsequence`                                                                                                                                                        | Breaker(s) tripped (cite by `breaker_id` from UAC registry)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | `BreakerAction`                                                                                                                                                                                                                                                                            | `KillSwitchId` armed                                                                                                                                                                                                                         | `AlertCode` fired                                                                                                                                                                                                                                                                 | `expected_within`                                                                                                                                                                |
| -------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CARRY_STAKED_BASIS` (primary)                     | `wild_print` 30σ on Pyth JITO-SOL/SOL                    | `BLOCK` via `GLOBAL_DATA_STALENESS_HALT` (`registry/risk_rules/global_rules.py:73-85`) re-evaluating at signal pre-flight (LST yield invalid → no new rebalance instruction) | `ORACLE_DEVIATION_BPS` (`registry/circuit_breakers/carry_staked_basis.py:35-50`, scope=PER_ARCHETYPE, threshold=100bps, window=60s, consecutive=3); ESCALATES to `LIQUIDATION_CASCADE_RISK` (`carry_staked_basis.py:109-124`) only if wild-print is `deviation_sign=-1` AND propagates into HF refresh that crosses 1.10                                                                                                                                                                                                                                                                                  | `BLOCK_NEW` (ORACLE_DEVIATION_BPS); ESCALATES to `KILL_ALL` (LIQUIDATION_CASCADE_RISK) at the secondary trip                                                                                                                                                                               | none initially (`BLOCK_NEW` is local); ESCALATES to `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` (`kill_switch.py:79`) if breaker stays armed > 5min, then `KILL_PER_ASSET_GROUP_DEFI` (`kill_switch.py:92`) only if correlated oracles also fail | `DEFI_FEATURE_STALE` (≤5s) → `DEFI_RATE_DEVIATION` (`codes.py:54`, ≤30s if peg-deviation feature also spikes) → `CIRCUIT_BREAKER_DEGRADED` (≤60s, after 1 of 3 consecutive windows) → `CIRCUIT_BREAKER_OPEN` (≤180s, after 3 consecutive 60s windows)                             | 60s for first DEGRADED; 180s for OPEN; 600s for kill-switch arming                                                                                                               |
| `CARRY_STAKED_BASIS`                               | `stale_hold` 25hr on Chainlink USDC/USD                  | `BLOCK` via `GLOBAL_DATA_STALENESS_HALT` (peg unverifiable → no deleverage instruction can proceed; collateral haircut undefined)                                            | `ORACLE_DEVIATION_BPS` (re-used — `oracle_deviation_bps` metric defined as max(deviation, heartbeat_age_bps_equivalent) so a stale feed reads as a divergent feed); secondary trip `RPC_OUTAGE_SECONDS` (`carry_staked_basis.py:51-64`) if the staleness is sourced from RPC failure (closed-set chain-RPC failure mode for L1/L2). **FOLLOW-UP** — `ORACLE_DEVIATION_BPS` is closest existing breaker; a dedicated `ORACLE_STALENESS_SECONDS` breaker would be cleaner (covers age-not-deviation semantics). Add to successor plan `simulation_scenarios_post_cutover_2026_06_01.md` + DR plan Phase 1.A | `BLOCK_NEW` initially; ESCALATES to `SCALE_DOWN` if `stale_duration` crosses 6hr AND existing position size > $500k (i.e. unwind some leverage before HF refresh stalls compound) — wired via Phase 2 archetype risk rule (see archetype.py:97 reference to "oracle / depeg blast radius") | `KILL_PER_ASSET_GROUP_DEFI` (`kill_switch.py:92`) if stale > 30min absolute OR stale > 3 × heartbeat AND any DeFi position has open HF < 1.30                                                                                                | `DEFI_FEATURE_STALE` (≤30s, slower than wild-print because Chainlink heartbeat is minutes-to-hours) → `CIRCUIT_BREAKER_DEGRADED` (≤90s) → `CIRCUIT_BREAKER_OPEN` (≤heartbeat × 3 + 60s) → `KILL_SWITCH_DEFI_LIQUIDATION_RISK` (`codes.py:32`, only at the HF-crossing escalation) | 60s for FEATURE_STALE; full breaker trip = `heartbeat × 3 + 60s` (3hr 1min for ETH/USD, 25hr 1min for stablecoin pegs); kill-switch arming bounded by HF re-check cadence (5min) |
| `ARBITRAGE_PRICE_DISPERSION` (hedge-leg secondary) | `wild_print` 30σ on Pyth SOL/USD (used as perp-spot ref) | `BLOCK` on new arb-leg instructions referencing the wild oracle's covered instrument (spot leg pre-flight rejects)                                                           | `CROSS_VENUE_DIVERGENCE_BPS` (`registry/circuit_breakers/arbitrage_price_dispersion.py:80-93` per scenario 01 cite) — wild-print on the spot oracle synthesises a >40bps divergence vs realized perp mid; secondary `BASIS_INVERSION_BPS` if the wild value flips perp-spot basis sign                                                                                                                                                                                                                                                                                                                    | `BLOCK_NEW`; ESCALATES to `CANCEL_OPEN` if `INVENTORY_IMBALANCE_RATIO` > 20% accumulates during the wild window                                                                                                                                                                            | `KILL_PER_ARCHETYPE_ARBITRAGE_PRICE_DISPERSION` (`kill_switch.py:80`) only if `BASIS_INVERSION_BPS` ALSO trips (correlated double-trip)                                                                                                      | `DEFI_RATE_DEVIATION` (`codes.py:54`, ≤5s) → `CIRCUIT_BREAKER_DEGRADED` (≤30s)                                                                                                                                                                                                    | 30s for first DEGRADED                                                                                                                                                           |
| `ARBITRAGE_PRICE_DISPERSION`                       | `stale_hold` 60s on Pyth (sub-minute heartbeat stall)    | `BLOCK` on new arb-leg instructions for the affected instrument (spot ref undefined)                                                                                         | `CROSS_VENUE_DIVERGENCE_BPS` (stale-vs-realized divergence as the perp mid keeps moving and the held oracle stays put)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | `BLOCK_NEW`; auto-disarms on first fresh heartbeat                                                                                                                                                                                                                                         | none (60s Pyth stall is short of asset-group kill threshold)                                                                                                                                                                                 | `DEFI_FEATURE_STALE` (≤5s) → `CIRCUIT_BREAKER_DEGRADED` (≤30s) → `CIRCUIT_BREAKER_CLOSED` on recovery                                                                                                                                                                             | 30s for DEGRADED; 30s post-recovery for CLOSED                                                                                                                                   |

### Auto-recovery contract (per DR plan `BreakerRecoveryRule`)

Primary breaker is `CircuitBreakerId.ORACLE_DEVIATION_BPS`. Its existing rule (per
`registry/circuit_breakers/carry_staked_basis.py:184-189`):

```
BreakerRecoveryRule(
    breaker_id=CircuitBreakerId.ORACLE_DEVIATION_BPS,
    guard_description="Oracle deviation < 50bps for 5min (sustained recovery).",
    retry_policy="exponential",
    auto_disarm_after_seconds=300,
)
```

Because `action=BLOCK_NEW`, `BREAKER_RECOVERY_DEFAULTS[BLOCK_NEW] = AUTO_COOLDOWN` (per `circuit_breaker.py:235-240`).
The scenario asserts:

- **`wild_print` recovery** — after the single-heartbeat wild update reverts, deviation drops back into band
  immediately. 5-min sustained-green guard then passes, breaker auto-disarms, `KILL_SWITCH_AUTO_RECOVERED`
  (`codes.py:171`) fires with `recovered_after_seconds ≈ 300` + guard-evaluation trail. Assertion SLA: auto-disarm
  within 360s of the wild-update reversion.
- **`stale_hold` recovery** — Pyth variants (1.2s / 10s / 60s stalls): heartbeat resumes → oracle age drops below
  `heartbeat × 1.5` → 5-min sustained-green → auto-disarm within 360s of recovery. Chainlink variants (3hr / 12hr / 25hr
  stalls): heartbeat resumes → next-round read succeeds → 5-min sustained-green → auto-disarm; same SLA.

**Escalation paths that REQUIRE manual unkill** — if the wild-print propagates into `LIQUIDATION_CASCADE_RISK`
(action=KILL_ALL, recovery_mode=MANUAL_UNKILL per `carry_staked_basis.py:118-124`), that breaker stays armed until
operator action. Scenario asserts `KILL_SWITCH_MANUAL_UNKILLED` (`codes.py:178`) is the ONLY exit path for the escalated
state, and that the auto-disarm of `ORACLE_DEVIATION_BPS` does NOT cascade-disarm the escalated
`LIQUIDATION_CASCADE_RISK` (orthogonal recovery — recovery composes per `BREAKER_RECOVERY_DEFAULTS` table, no implicit
cascade).

If `recovery_attempts_exceeded > 3` (per exponential retry policy on the ORACLE_DEVIATION_BPS rule), the breaker
escalates to `manual_unkill` regardless of action — the scenario covers this via a sub-variant where the stale_hold
variant is "stale → recover → stale again" repeated 4× within 1hr.

### Cross-references / prior art

- UAC `BreakerConfig` for `ORACLE_DEVIATION_BPS`:
  `unified-api-contracts/unified_api_contracts/registry/circuit_breakers/carry_staked_basis.py:35-50` (PER_ARCHETYPE,
  applies_to="CARRY_STAKED_BASIS", 100bps / 60s / consecutive=3).
- UAC `BreakerRecoveryRule` for same: `carry_staked_basis.py:184-189`.
- UAC `BreakerConfig` for `RPC_OUTAGE_SECONDS`: `carry_staked_basis.py:51-64` (secondary trip path for
  stale_hold-via-RPC-failure sub-shape).
- UAC `BreakerConfig` for `LIQUIDATION_CASCADE_RISK`: `carry_staked_basis.py:109-124` (KILL_ALL / MANUAL_UNKILL —
  primary escalation path for wild-print negative-deviation propagating into HF crossings).
- UAC `KillSwitchId` enum: `kill_switch.py:79` (KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS), `:80`
  (KILL_PER_ARCHETYPE_ARBITRAGE_PRICE_DISPERSION), `:92` (KILL_PER_ASSET_GROUP_DEFI).
- UAC `AlertCode` mapping: `codes.py:52` (DEFI_FEATURE_STALE — best fit for oracle-derived feature staleness), `:54`
  (DEFI_RATE_DEVIATION — best fit for peg/basis deviation downstream of wild-print), `:42-45`
  (CIRCUIT_BREAKER_OPEN/DEGRADED/CLOSED/BACKOFF_ESCALATING lifecycle), `:32` (KILL_SWITCH_DEFI_LIQUIDATION_RISK at
  HF-crossing escalation), `:171` / `:178` (recovery codes).
- UAC `RiskRule`: `registry/risk_rules/global_rules.py:73-85` (GLOBAL_DATA_STALENESS_HALT) — the workspace-wide BLOCK
  consequence both variants pivot on at signal pre-flight; `triggers_kill_switch=True`.
- DR plan `disaster_recovery_circuit_breakers_2026_05_10.md` § Phase 1.B (BreakerAction closed-set) + Phase 1.C-D
  (KillSwitchId / KillSwitchProvenance / KillSwitchArmRequest+ArmedEvent+DisarmEvent).
- Risk plan `risk_simulations_limits_alerting_2026_05_10.md` § GLOBAL_DATA_STALENESS_HALT semantics + § Phase 1.F
  recovery-mode wiring.
- `defi_master_2026_05_07.md` Pyth + Chainlink architecture context (Pyth-unban 2026-05-06 for Solana on-chain;
  Chainlink retained for Ethereum/L2; oracle dual-stack policy).
- UAC `CHAIN_RPC_TEMPLATES`: `registry/capability_declarations/_defi.py` — SSOT for chain→RPC mapping referenced by
  stale_hold variant when staleness is sourced from RPC layer.
- UAC `config/testnet_contracts.yaml` (validated by `unified-config-interface/testnet_contracts.py` `PROTOCOL_SCHEMAS`)
  — concrete Pyth feed pubkeys + Chainlink aggregator addresses populating `oracle_id` enumeration for applicability
  filter.
- Historical incidents modelled: Chainlink GMX-V1 AVAX wild-print 2022-09-18; Chainlink LUNA zero-print 2022-05-12; Pyth
  SHIB/DOGE wild-print 2024-03-08; Pyth Solana heartbeat stall 2024-Q1 (citations in § Real-world referent above).

**Phase 4 follow-up (deferred — captured per Capture-Discoveries HARD RULE)**:

- **FOLLOW-UP P1**: Add `ORACLE_STALENESS_SECONDS` as a first-class `CircuitBreakerId` member distinct from
  `ORACLE_DEVIATION_BPS`. Today's mapping conflates "wild deviation" with "age-too-old"; the cleaner taxonomy separates
  deviation-bps from age-seconds. Owner: successor plan `simulation_scenarios_post_cutover_2026_06_01.md` Phase 1.B
  extension + DR plan Phase 1.A extension (UAC `circuit_breaker.py` + per-archetype seed). The pre-cutover scenario maps
  stale_hold onto `ORACLE_DEVIATION_BPS` (with `oracle_deviation_bps = max(deviation, heartbeat_age_bps_equivalent)`) —
  acceptable for the 6-scenario subset; not durable post-cutover.
- **FOLLOW-UP P1**: Grep workspace for `OracleStaleError` / `OracleDeviationError` exception classes. If absent (the
  manifest `record_failed` taxonomy in UAC + UTL today only formally lists `UpstreamTimestampBiasError` /
  `MalformedTickFieldError` / `DependencyError` per CLAUDE.md writegate Phase 2.A 4-category mapping), add the two
  oracle-typed exceptions to honest-coverage taxonomy. Owner: writegate plan
  `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 3.D.5 extension OR successor scenarios plan if the writegate
  plan archives first.
- **FOLLOW-UP P2**: No literal `ORACLE_DEVIATION` or `ORACLE_STALE` AlertCode in current closed-set (`alerting/codes.py`
  — confirmed via grep `ORACLE\|MARKET_DATA_STALE\|PRICE_FEED` returned only `DEFI_FEATURE_STALE` /
  `DEFI_RATE_DEVIATION` / `TICK_STALENESS` plus the `KILL_SWITCH_*` family). Scenario maps to `DEFI_FEATURE_STALE`
  (feature-level) + `DEFI_RATE_DEVIATION` (downstream feature spike) as the closest existing codes. If operator UX wants
  "oracle deviation" / "oracle stale" as distinct dashboard labels separate from generic feature-staleness, add to
  successor plan Phase 1.E of `simulation_scenarios_post_cutover_2026_06_01.md` (parity with the venue-outage scenario's
  `VENUE_HALTED` AlertCode follow-up captured in scenario 01).
- **FOLLOW-UP P2**: Add a dedicated `KILL_SWITCH_ORACLE_DIVERGENCE` AlertCode (parallel to
  `KILL_SWITCH_VENUE_DISCONNECT` at `codes.py:34`) so oracle-driven kill-switch arms are operator-distinguishable from
  generic DeFi-liquidation-risk arms. Owner: successor plan Phase 1.E.
