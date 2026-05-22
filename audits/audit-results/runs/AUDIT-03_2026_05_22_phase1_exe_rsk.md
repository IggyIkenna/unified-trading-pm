---
title: "AUDIT-03 — Phase 1 READ results: §2.3 EXE + §2.5 RSK (safety-critical, main pass)"
audit_id: AUDIT-03
run_phase: "Phase 1 — static drift, READ checkpoints (safety-critical sections kept back for main)"
section: "§2.3 execution path (EXE-*) + §2.5 risk/kill-switch/breaker (RSK-*) + §2.1 deferred closure (CSB-05/15/17/20)"
date: 2026-05-22
method: "Opus 4.7 main — direct read (no sub-agent; safety-critical)"
auditor: Harsh + Claude Opus 4.7
checklist: audits/audit-files/audit_03_defi_archetypes_e2e.md
code_audited:
  - execution-service@a848ef61 (live-defi-rollout) — defi_execution/{protocols/aave.py,protocols/uniswap.py,mev/*}, v2/{mev_router.py,execution_policies.py}, engine/{circuit_breaker.py,venue_cascade_monitor.py,risk/preflight_gate.py,preprocessors/wrap_preprocessor.py,handlers/{claim,sell}_reward_handler.py}, matching_engine/defi/cost_aggregator.py, providers/rpc_fallback.py, config/chain_config.yaml
  - unified-api-contracts@c3f7a45 — canonical/crosscutting/{errors/defi.py,kill_switch.py,circuit_breaker.py}, registry/{risk_rules/archetype.py,scenarios/defi.py,dex_router_addresses.py}, internal/execution.py
  - strategy-service@b303a358 — risk/v2/preflight.py, position/core/reconciler_breaker_bridge.py, portfolio_allocator/archetypes.py, target_universe/catalog.py, config_reloaders.py
  - unified-trading-library — events/event_types.py, risk_preflight/wallet_preflight.py
oracle: codex/04-architecture/{defi-execution-overview,mev-protection,flash-loan-receiver,interface-credential-convention,kill-switch-circuit-breaker,custody-providers}.md + codex/09-strategy/architecture-v2/cross-cutting/{execution-policies,risk-gates}.md
---

# AUDIT-03 — Phase 1 READ — §2.3 EXE + §2.5 RSK (safety-critical main pass)

Done as **main (Opus, direct read)** per the audit plan — these are the kept-back safety-critical sections. Also closes
the §2.1 deferred carry checkpoints (CSB-05/15/17/20). **9 findings (F-27…F-33 numbered; +2 sub-notes)**, incl. **2 P0**
(EXE-07 wrap discipline, RSK-05 LST-depeg scenario). The risk/kill-switch infrastructure is otherwise **solid** — kill-
switch hierarchy, breaker thresholds, multi-venue cascade, 4-layer preflight all PASS.

## §2.3 EXE — per-checkpoint verdicts

| ID | Verdict | Evidence |
| -- | ------- | -------- |
| EXE-01 | PASS + **CODEX-DRIFT** | `classify_venue_error()` wired at the orchestration call sites (`engine/orchestrator.py:252,348`, `multi_leg_orchestrator.py:334,470`, `engine/routing/instruction_router.py:281`, `adapters/defi_adapter.py:185`) — routing is via the `ErrorAction` field on `VenueErrorClassification`, not per-connector. **F-27**: `DefiErrorCode` has **35** codes (13 base/Aave + 7 RECURSIVE_LOOP + 8 HL + 2 ORACLE + **5 CCTP added 2026-05-19**), but the audit/codex/CLAUDE.md say "30"; and routing is on `ErrorAction` (FAIL/RETRY/SKIP + **RECONNECT** = 4) not a literal code-name prefix |
| EXE-02 | **NEEDS-CONFIRM (likely GAP)** | `MevRouter._DEFAULT_POLICIES` (v2/mev_router.py) maps `FLASHBOTS_PROTECT`→ethereum-only, `PUBLIC_MEMPOOL`→multi-chain ✓ + BLOXROUTE excluded ✓ — but the **$10k-notional → FLASHBOTS_PROTECT mode-SELECTION** logic was not found anywhere; the router maps mode→policy + validates chain, nothing selects the mode by USD size → **F-32** |
| EXE-03 | PASS | `JITO_BUNDLE` policy is solana-only (mev_router.py:73-80); `jito_bundle.py:111 assert_jito_mode` guards; `route()` rejects mode↔chain mismatch (mev_router.py:99-102) |
| EXE-04 | PASS | `_DEFAULT_POLICIES` runtime registry in `MevRouter`; resolution via `.route(mode, chain)` — not hardcoded per-strategy (mev_router.py:32-103) |
| EXE-05 | PASS (docstring stale) | `aave.py:801 _validate_flash_loan_receiver` calls `eth.get_code(addr)` and **raises `ValueError`** on empty bytecode (818-825); `connect()` (845-852) raises if receiver unconfigured then validates on-chain; receiver resolved config→UAC testnet registry (681-708). Behavior matches codex flash-loan-receiver.md:81. **Sub-note**: docstring (805) says "Logs a warning" but code raises — fix docstring |
| EXE-06 | PASS | `uniswap.py` quotes via QuoterV2 (839,1189) → `minAmountOut` w/ `slippage_factor=(10000−max_slippage_bps)/10000` (702-704) → revert `if amount_out < min_amount_out` (1034); `DEFAULT_MAX_SLIPPAGE_BPS` is code SSOT (894) |
| EXE-07 | **CODE-DRIFT (P0)** | **F-28** — `wrap_preprocessor.py` `_WRAP_RULES` (40-50) only covers ETH→WETH + eETH→weETH for **DeFi protocols** (AAVE/MORPHO/UNISWAP/CURVE/BALANCER). **No `stETH→wstETH` rule, no CeFi perp venue (OKX/Bybit/Deribit)**; `preprocess()` (195-228) only fires on DeFi op-types (LEND/BORROW/STAKE/SWAP/REPAY/WITHDRAW/UNSTAKE) — the CeFi collateral-transfer leg bypasses it entirely. Posting rebasing stETH to OKX is **not prevented** at this layer (nor at strategy `_build_legs` per F-11). Composes/elevates F-11 |
| EXE-08 | **CODE-DRIFT (P1)** | **F-29** — DeFi connectors store the wallet PK as `self._private_key` instance attr (aave.py:165, uniswap.py:404, base.py:380, eigenlayer.py:168, hyperliquid.py:159/188); codex interface-credential-convention.md:187 says "Connectors MUST NOT store config['wallet_private_key'] as an instance attribute beyond the connect() method". Mitigant: cleared at `disconnect()` (aave.py:864, uniswap.py:943). The strict fetch-per-request-and-discard pattern is not followed |
| EXE-09 | PASS (naming drift) | `execution_policies.py:236 resolve_algo` evaluates rules document-order first-match; raises `NoMatchingRule` on no match (257, default-deny) ✓; version-pin via `get_by_ref("policy_id@v{N}")` (148-159) ✓. **Sub-note**: codex/checkpoint names `select_algo`/`NoRuleMatched`; actual `resolve_algo`/`NoMatchingRule` |
| EXE-10 | PASS-static (RUN deferred) | `matching_engine/defi/cost_aggregator.py:11-12` docstring: "used by both batch backtest replay and live pre-trade cost gating … Batch: callers pass per-day median gas_price_gwei from MTDS gas_fee_data". Mode-agnostic; gas source caller-injected. Zero-divergence assertion = Phase 2 RUN |
| EXE-11 | NEEDS-CONFIRM (Phase 2) | Directive contract is `internal/strategy_directives.py`; per-leg execution validation exists. ⚠ XAS-06 reports `AtomicInstruction` not present in UAC (only e2e-testing imports) — verify the emitted directive type name + UAC location before claiming validation. Cross-ref XAS-06/F-27 |
| EXE-12 | PASS-static (RUN deferred) | `VENUE_COLLATERAL_MATRIX` (UAC registry/venue_collateral.py) exists; ALC-01 confirmed eligibility delegates to the UAC matrix (no hardcoded allowlist). Execution-preflight enforcement = Phase 2 RUN |
| EXE-13 | PARTIAL | `engine/handlers/{claim,sell}_reward_handler.py` exist + execute on-chain claims/sells (gas-only cost). The **auto-trigger thresholds ($50 accrued / max 1×24h / $100 sell)** were not located in execution-service — they belong to reward-decision logic (strategy/features); verify there |
| EXE-14 | **CODE-DRIFT (P1/P2)** | **F-30** — `infura` (a removed provider per CLAUDE.md DeFi Execution Architecture) is wired as a resolvable RPC provider: `config/chain_config.yaml` `fallbacks: [infura, …]` + `providers/rpc_fallback.py:9` provider-id resolution |
| EXE-15 | PASS | Pyth confined to Solana — `defi_execution/protocols/solana_lst_devnet.py` (Pyth Hermes API) + `drift.py` (Solana oracle); no EVM-chain Pyth usage |
| EXE-16 | PASS-mostly | RPC URLs are config-driven (`chain_config.yaml` + `rpc_fallback.py` resolver). **Sub-note**: hardcoded Pyth Hermes URL `https://hermes.pyth.network/v2` in `solana_lst_devnet.py` (devnet helper). The `no_hardcoded_venue_urls.sh` QG step is IS/MTDS-scoped, not in execution-service/scripts |
| EXE-17 | PASS-static (RUN deferred) | `TestnetContractRegistry` (UTL config_interface) used via `get_testnet_contract_registry()` (aave.py:716) + validates `config/testnet_contracts.yaml` at load. Import-without-KeyError RUN check = Phase 2 |
| EXE-18 | **CODE-DRIFT (P1)** | **F-31** — `SWAP_ROUTER_ADDRESS = "0x68b3…Fc45"` hardcoded as a class constant in `protocols/uniswap.py:848` AND `venues/uniswap.py`; QuoterV2 `0x61fFE…` likewise. UAC `registry/dex_router_addresses.py` is the canonical home — should be imported, not hardcoded in execution business logic |

**EXE tally:** PASS 9 · CODE-DRIFT 4 (EXE-07 P0, EXE-08/14/18) · CODEX-DRIFT 1 (EXE-01) · NEEDS-CONFIRM/GAP 2 (EXE-02,11) · partial 1 (EXE-13).

## §2.5 RSK — per-checkpoint verdicts

| ID | Verdict | Evidence |
| -- | ------- | -------- |
| RSK-01 | PASS | `KillSwitchId` (UAC kill_switch.py:52) has all 5 levels: `KILL_ALL_LIVE` → `KILL_PER_ASSET_GROUP_{CEFI,DEFI}` → `KILL_PER_ARCHETYPE_{CARRY_STAKED_BASIS,ARBITRAGE_PRICE_DISPERSION}` → `KILL_PER_VENUE_{BYBIT,DERIBIT,BINANCE,OKX,HYPERLIQUID,ASTER}` → `KILL_PER_WALLET` (+ 6 treasury halts). `KillSwitchArmRequest.target_wallet_id` "Required when KILL_PER_WALLET; rejected otherwise" (192-197). **Sub-note**: that conditional-required rule is documented in the field docstring — confirm a `model_validator` enforces it (none seen) |
| RSK-02 | PASS-static (RUN deferred) | 4-set on-kill behaviour (`STOP_NEW_ONLY`/`FAST_UNWIND`/`SLOW_UNWIND`/`DELTA_HEDGE`) defined (kill_switch.py:216-218 + archetype.py:36-39). Strategy on-kill re-entry behaviour = Phase 2 RUN |
| RSK-03 | PASS | `circuit_breaker.py` exact thresholds: `_DEGRADED_FAILURE_RATE_THRESHOLD=0.30` (56), `_OPEN_FAILURE_RATE_THRESHOLD=0.60` (57), `_FAILURE_RATE_WINDOW=20` (58), `_FAILURE_RATE_MIN_SAMPLES=5` (59); CLOSED→DEGRADED@≥0.30 (287), DEGRADED→OPEN@≥0.60 (294); `should_count_as_failure` returns False for `CanonicalRateLimitError` (464) — 429 not counted ✓ |
| RSK-04 | PASS-static | `WalletSpendingPreCheckResult` (UAC internal/execution) + `unified_trading_library/risk_preflight/wallet_preflight.py` produce layer-by-layer pre-check results. Audit-log-row write = verify in Phase 2 |
| RSK-05 | **CODE-DRIFT / GAP (P0)** | **F-33** — UAC `registry/scenarios/defi.py` defines 6 scenarios: `defi_chain_rpc_outage_solana`, `defi_liquidity_drain_lending_pool`, `defi_oracle_deviation_30sigma`, `defi_gas_surge_50x`, `defi_mempool_congestion_inclusion_delay`, `defi_stablecoin_depeg`. There is **NO `DEFI_LST_DEPEG_STETH_5PCT`** (LST-depeg) scenario — only stablecoin-depeg. Codex (kill-switch-circuit-breaker.md, autonomous-recovery-matrix.md, backtest-groups.md) specifies it as the carry archetype's signature kill trigger → `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS`. The carry depeg kill-switch (CSB-12) is unverifiable by scenario. Composes CUT-05 (no scenario-matrix cron either). `ScenarioOutcomeAssertion` structure incl. `expected_within_seconds` exists |
| RSK-06 | PASS-static (RUN deferred) | 4-layer model: L1/L2 in `strategy-service/risk/v2/preflight.py` (UAC rule registry = rule SSOT; `_CONSEQUENCE_TO_DECISION` maps L2 RiskRuleConsequence→RiskGateDecision); L3 execution `engine/risk/preflight_gate.py` (BLOCK→reject+emit). L2-veto-prevents-L3+L4 ordering = Phase 2 RUN |
| RSK-07 | PASS-static | `DUAL_FAILURE_DETECTED` + `RECON_DEGRADED_CLOSE` exist as AlertCodes (UAC alerting/codes.py) + event patterns (alerting/rules.py) + UTL events. Recon-gate behaviour (L2∧L3 freshness) = Phase 2 RUN |
| RSK-08 | PASS-static (**caveat — composes F-24**) | Per-archetype breaker registry exists (UAC `registry/circuit_breakers/carry_staked_basis.py`); CUSTODY breaker config present. **Caveat**: F-24 found `CustodyProvider.health_check()→CustodyHealth` is ABSENT from the protocol + all impls — so the `CUSTODY_DISCONNECT_SECONDS` breaker has no health-ping signal to act on. Breaker defined, input missing |
| RSK-09 | NEEDS-VERIFY (Phase 2) | On-chain reconciler (wallet vs PBMS per-chain drift → POSITION_LIMIT_EXCEEDED → CANCEL_OPEN) is in-depth·RUN; confirm reconciler exists in Phase 2 |
| RSK-10 | PASS | `engine/venue_cascade_monitor.py`: `_CASCADE_THRESHOLD_PCT` (>50%); `cascade_pct = len(open)/total·100` (56); `is_cascade = pct > threshold` (57); all-OPEN → `_activate_firm_wide_kill_switch` (70); is_cascade → scoped STOP_NEW_ONLY (71-72); `_emit_cascade_detected` at CRITICAL (78-79) ✓ |
| RSK-11 | PASS-static (count = RUN) | Per-archetype rule registry (`registry/risk_rules/archetype.py`) has **24** `RiskRule()` instances across CARRY_STAKED_BASIS + ARBITRAGE_PRICE_DISPERSION (docstring: "≥10 rules each"); L2 preflight wired (risk/v2/preflight.py). The master "15/15 fire" likely aggregates across multiple registry layers (global/asset_group/strategy_family/archetype) — exact firing count = Phase 2 RUN. **Sub-note**: archetype.py docstring says "≥10" vs master L1348 "15/15" — reconcile expected count |
| RSK-12 | PASS | `KILL_SWITCH_ACTIVATED` (UTL event_types.py:210) + `KILL_SWITCH_DEACTIVATED` (211, the "explicit deactivation") + `CIRCUIT_BREAKER_OPEN` emitted (circuit_breaker.py:387) — all required events present |

**RSK tally:** PASS 8 (incl. all P0 kill-switch/breaker/cascade/preflight static checks) · CODE-DRIFT/GAP 1 (RSK-05 P0) · NEEDS-VERIFY 1 (RSK-09) · static-pass-with-caveat 2 (RSK-08 composes F-24, RSK-11 count).

## §2.1 deferred closure — CSB-05/15/17/20

| ID | Verdict | Evidence |
| -- | ------- | -------- |
| CSB-05 | PASS | `features-service/.../onchain/engine/staking_apy_total.py` derives **base** from on-chain `lst_rates` rate-ratio between consecutive days (docstring 7-9); **no DefiLlama/vendor** reference. Aggregates base + EIGEN + seasonal − dust (also confirms PNL-03 3-layer decomposition) |
| CSB-15 | PASS | `CarryStakedBasisRankAllocator` (portfolio_allocator/archetypes.py): `DEFAULT_MIN_APY_BPS=Decimal("250")` (402); survivor filter `score > self.min_apy_bps` (442); `_score` (417); 2-stage weights normalized, "sum ≤ 1.0; remainder stays in cash" (docstring 5-6) |
| CSB-17 | PASS | `catalog.py:959 _build_carry_staked_basis` emits exactly the 4 slots from the collateral matrix: lido-deribit (USDC), jito-drift + marinade-drift (USDC, Solana), lido-bybit (USDT) (docstring 967-969). The catalog is correct — F-08's stale "zero slots" claim was the *engine* docstring, not the catalog |
| CSB-20 | PASS | `StrategyPnlStreamEvent` emitted by the carry engine (staked_basis.py) for trading-agent-service; `StrategyDirectiveReloader` exists (config_reloaders.py) with per-archetype directive injection + `get_directive_reloader()` singleton |

## Findings (new this run)

| ID | Checkpoint | Class | Finding | Sev | Status |
| -- | --------- | ----- | ------- | --- | ------ |
| F-27 | EXE-01 | CODEX-DRIFT | `DefiErrorCode` = **35 codes** (CCTP +5 added 2026-05-19), not "30" as codex defi-execution-overview + CLAUDE.md state (last updated 2026-05-15). Routing is via `ErrorAction` (FAIL/RETRY/SKIP/**RECONNECT** = 4) not a literal code-name "prefix". Update codex count + wording. [overlaps XAS-06] | P2 | CONFIRMED |
| F-28 | EXE-07 | CODE-DRIFT | Wrap preprocessor lacks `stETH→wstETH` and any CeFi perp venue; only fires on DeFi op-types → the OKX/Bybit/Deribit collateral-transfer leg bypasses it. Posting rebasing stETH to a CeFi perp venue is **not prevented** at either the strategy (F-11) or execution (EXE-07) layer. `execution-service/.../engine/preprocessors/wrap_preprocessor.py` | **P0** | CONFIRMED |
| F-29 | EXE-08 | CODE-DRIFT | DeFi wallet PK stored as `self._private_key` instance attr beyond `connect()` (aave/uniswap/base/eigenlayer/hyperliquid), contra codex Key-Lifetime §L187 ("MUST NOT store … beyond the connect() method"). Cleared at `disconnect()` (mitigant); per-request-fetch-and-discard not implemented | P1 | CONFIRMED |
| F-30 | EXE-14 | CODE-DRIFT | `infura` (removed provider) wired as a resolvable RPC fallback in `config/chain_config.yaml` + `providers/rpc_fallback.py` | P2 | CONFIRMED |
| F-31 | EXE-18 | CODE-DRIFT | SwapRouter02 + QuoterV2 addresses hardcoded in `protocols/uniswap.py:848` + `venues/uniswap.py` despite UAC `registry/dex_router_addresses.py` being canonical | P1 | CONFIRMED |
| F-32 | EXE-02 | GAP (needs-confirm) | $10k-notional → `FLASHBOTS_PROTECT` MEV mode-**selection** not located; `MevRouter` only maps mode→policy + validates chain. BLOXROUTE correctly excluded + policies correct, but nothing chooses the private-mempool mode by trade size on ETH mainnet | P1 | NEEDS-CONFIRM |
| F-33 | RSK-05 | CODE-DRIFT/GAP | `DEFI_LST_DEPEG_STETH_5PCT` scenario (carry's signature depeg kill trigger) is **not implemented** — UAC `registry/scenarios/defi.py` has stablecoin-depeg + oracle-deviation but no LST-depeg. Carry depeg kill-switch (CSB-12) unverifiable by scenario; composes CUT-05 (no scenario-matrix cron) | **P0** | CONFIRMED |

**Sub-notes (P3, not separately numbered):** EXE-05 `_validate_flash_loan_receiver` docstring says "logs a warning" but code raises ValueError (fix docstring); EXE-09 codex names `select_algo`/`NoRuleMatched` vs actual `resolve_algo`/`NoMatchingRule`; RSK-01 KILL_PER_WALLET `target_wallet_id` conditional-required documented but a `model_validator` enforcing it was not seen; RSK-11 archetype.py says "≥10 rules" vs master "15/15".

## Reviewer notes

- **Two P0 safety findings drive remediation**: F-28 (wrap discipline — a rebasing-stETH-to-OKX transfer would post a
  rebasing token to a CeFi perp venue that requires non-rebasing wstETH; affects 2 of the 4 carry slots: lido-deribit +
  lido-bybit) and F-33 (no LST-depeg scenario — the single most important carry scenario can't be run; doubly blocked by
  CUT-05's missing scenario-matrix cron). Both should land in a carry-execution-safety remediation plan.
- **The risk infrastructure is otherwise strong**: kill-switch 5-level hierarchy, breaker thresholds (exact), 429-not-
  counted, multi-venue cascade (>50%/all), 4-layer preflight, DUAL_FAILURE/RECON_DEGRADED codes, KILL_SWITCH_ACTIVATED +
  CIRCUIT_BREAKER_OPEN all present. RSK is mostly PASS.
- **F-29 (key lifetime)** needs an operator/architecture call: is `disconnect()`-clearing sufficient, or must connectors
  fetch-per-request-and-discard? The codex wording is strict (no instance-attr storage beyond connect()).
- **EXE-02 (F-32)** is the one I most want a second pair of eyes on — the policies + chain-validation are correct, but I
  could not find the by-notional mode selector for ETH-mainnet ≥$10k. If it lives in an upstream signal/dispatch path I
  didn't reach, downgrade to PASS; if absent, it's a P1 MEV-protection gap.
- **EXE-11** cross-refs XAS-06: confirm the emitted directive type (`AtomicInstruction` reportedly not in UAC) before
  Phase-2 validation testing.
- Phase-2 RUN items not executed this pass: EXE-10/11/12/17, RSK-02/05/06/07/09/11 (full behaviour), per §0.2.
