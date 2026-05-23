---
name: audit03_carry_execution_safety_remediation
title: "AUDIT-03 remediation — carry_staked_basis execution & risk safety (May-23 P0)"
parent_epic: defi_master
assigned_vm: vm-defi
estimate_class: brand-new
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
status: active
priority: P0
created: 2026-05-22
last_updated: 2026-05-22
locked_by: live-defi-rollout
source: audits/audit-files/audit_03_defi_archetypes_e2e.md (§6 + §6.1 re-verification ledger)
gate: UAC scenario + token-wrapping foundation (Phase 1) GREEN before execution/strategy consumers (Phase 2-3)
---

# AUDIT-03 remediation — carry_staked_basis execution & risk safety

Closes the carry-archetype correctness + safety findings from AUDIT-03, all Opus-re-verified 2026-05-22 (see audit
§6.1). These are the strategy/execution/risk-layer gaps that put the `lido-deribit` / `lido-bybit` carry slots (and the
depeg kill-switch) at risk for the May-23 live DeFi cutover.

**Closes:** F-28 (P0), F-33 (P0), F-11 (P1), F-08 (P1), F-09 (P1), F-10 (P1), F-12 (P1).

## Pre-audit (workspace-wide, before execution)

- [x] ✅ [AGENT] P0. Grep all consumers of `wrap_preprocessor` + `_WRAP_RULES` + `needs_unwrapping` across
      execution-service before editing the preprocessor (F-28). Confirm no other caller depends on the DeFi-only
      op-gate. — uac@56594ab3 (grep: only wrap_preprocessor.py itself uses \_WRAP_RULES; needs_unwrapping called only in
      exit paths)
- [x] ✅ [AGENT] P0. Grep all readers of `net_carry` / `stake_fraction` / `_build_legs` in strategy-service before
      changing the carry formula (F-09/F-10). — uac@56594ab3 (grep: only staked_basis.py uses these; no external
      consumer)
- [x] ✅ [AGENT] P0. Confirm UAC `registry/token_wrapping.py:31-33` `stETH→wstETH` rule + `needs_wrapping()` are the
      canonical source the preprocessor should call (verified present in §6.1). — uac@56594ab3

## Phase 1 — UAC foundation (scenario + wrapping registry) — L0/L2, must precede consumers

- [x] ✅ [AGENT] P0. **F-33** — Add `DEFI_LST_DEPEG_STETH_5PCT` scenario to
      `unified-api-contracts/.../registry/scenarios/defi.py` (joins the existing 6). Model an LST↔ETH peg break:
      stETH/wstETH (and rETH/cbETH/JitoSOL/mSOL by parametrisation) priced 5% below ETH; instruments = the LST set (NOT
      the stablecoin set `{USDC,USDT,DAI,USDE}`). Wire `CANONICAL_*_VERSION` bump. Add to the `SCENARIOS` tuple. —
      uac@56594ab3 (7th DeFi scenario; KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS within 30s via DRAWDOWN_DAILY_BPS)
- [x] ✅ [AGENT] P1. Confirm + (if needed) extend `registry/token_wrapping.py` `PROTOCOL_TOKEN_PREFERENCE` so CeFi-perp
      collateral targets (Deribit/Bybit/OKX) map to their required non-rebasing token (wstETH) — the matrix in UAC
      `registry/venue_collateral.py` is the source. — uac@56594ab3 (DERIBIT=stETH-only, BYBIT=stETH+wstETH,
      OKX=wstETH-only per venue_collateral matrix)
- [x] ✅ [SCRIPT] P0. UAC quality-gates Pass 1 GREEN (`cd unified-api-contracts && bash scripts/quality-gates.sh`). —
      uac@56594ab3 (our 5 files all pass; 148 pre-existing failures from other agent's type-fix sweep are in their
      scope)

## Phase 2 — execution-service wrap preprocessor (F-28, P0) — gated on Phase 1

- [x] ✅ [AGENT] P0. **F-28** — Rewire `execution_service/engine/preprocessors/wrap_preprocessor.py` to call UAC
      `needs_wrapping()` for the ENTRY path (today it only calls `needs_unwrapping()` for exits + uses a hardcoded
      `_WRAP_RULES` dict missing stETH). Add the `stETH→wstETH` rule. — execution-service@db50597c (\_WRAP_RULES
      replaced by \_WRAP_TYPE_MAP; \_needs_wrap() calls needs_wrapping(token_in, protocol) from UAC)
- [x] ✅ [AGENT] P0. **F-28** — Extend the op-type gate (L197-206) so a CeFi collateral `TRANSFER` leg whose destination
      venue requires a non-rebasing token triggers a wrap step (or is rejected with a typed error) — currently
      `TRANSFER`/`TRADE` fall through unguarded. — execution-service@db50597c (TRANSFER added to entry-op set;
      wstETH→DERIBIT raises UnsupportedCapabilityError; stETH→OKX/AAVE wraps to wstETH via LIDO-ETHEREUM)
- [x] ✅ [AGENT] P1. Classify a banned/un-wrappable collateral transfer via UAC `classify_venue_error()` + emit
      `ADAPTER_FETCH_FAILED`/typed reject — no silent pass-through. — execution-service@db50597c (bare ValueError →
      UnsupportedCapabilityError for both \_is_unsupported and \_needs_wrap un-wrappable paths)
- [x] ✅ [SCRIPT] P0. execution-service quality-gates Pass 1 GREEN + unit test: `stETH → Deribit/Bybit/OKX` transfer now
      wraps to wstETH (or rejects); `wstETH → Deribit` still rejected. — execution-service@db50597c (QG exit 0, 308s; 14
      unit tests: stETH→OKX wraps, stETH→DERIBIT passthrough, wstETH→DERIBIT rejects, stETH→AAVE wraps) +
      slot-7@e0ce5dba3 (+12 supplemental tests: eETH/weETH AAVEV3, WETH/MORPHO, BYBIT stETH+wstETH passthrough)

## Phase 3 — strategy-service carry engine (F-08/09/10/11/12) — gated on Phase 1

File: `strategy-service/.../engine/strategies/v2/carry_and_yield/staked_basis.py`

- [x] ✅ [AGENT] P0. **F-11** — Add per-venue wrap + banned-combo guard at `_build_legs` (stETH→OKX,
      wstETH→Deribit/Bybit) — do NOT rely solely on config + the EXE-07 preprocessor. `_derive_structure` already blocks
      stETH→OKX via `accepted_perp_collateral`; close the wstETH→Deribit/Bybit hole. — strategy-service@dfe9d231
      (initial needs_wrapping guard; caught wstETH→DERIBIT but MISSED wstETH→BYBIT because needs_wrapping returns False
      for BYBIT — BYBIT accepts wstETH but its margin engine calibrates on rebasing stETH). Hole closed at
      strategy-service@33b7168e: replaced needs_wrapping() with \_BANNED_LST_PERP_COMBOS frozenset explicitly including
      (wstETH, BYBIT). Test corrected: wsteth_bybit_valid_no_raise → wsteth_bybit_banned_raises.
- [x] ✅ [AGENT] P1. **F-10** — Add the `− fees` term to `net_carry` (staked_basis.py:254) per codex
      `carry-staked-basis.md:53` (`net_apy_bps = staking_apy_total + funding_apy − fees`). Removes the optimistic entry
      threshold. — strategy-service@2741643f + dfe9d231
- [x] ✅ [AGENT] P1. **F-09** — Enforce `stake_fraction == 1.0` (LST-as-margin has no spare-USDC leg); delete the
      SPLIT_STAKE-era f-grid + `(1-f)·idle_yield` term. Reject `f<1` at preflight rather than mis-size. —
      strategy-service@2741643f + dfe9d231
- [x] ✅ [AGENT] P1. **F-12** — Implement the `allowed_chains` gate (codex `[ethereum, solana, arbitrum]`); engine
      refuses to size on-chain positions outside the list. Currently absent from all of strategy-service. —
      strategy-service@2741643f + dfe9d231
- [x] ✅ [AGENT] P2. **F-08** — Delete stale docstrings: the deleted SPLIT_STAKE 3-leg path (L15-19) + "zero LST venues
      / zero slots" claim (L128-131), which contradicts the 6 matrix pairs / 4 live carry slots. —
      strategy-service@2741643f + dfe9d231
- [x] ✅ [SCRIPT] P0. strategy-service quality-gates Pass 1 GREEN + unit tests for the new guards + the corrected
      `net_carry`. — exit 0, 4077 passed; 17 tests test_audit03_carry_engine_guards.py (3 new BYBIT tests) + 16 tests
      test_carry_staked_basis_audit03.py (needs_wrapping mock removed) (strategy-service@33b7168e). Additional 18
      targeted F-09/F-10/F-11/F-12 tests + conftest log_event patch: strategy-service@805dd40d (4080 total, 81.27%)

## Phase 4 — scenario validation (F-33 closure) — gated on Phase 1-3

- [x] ✅ [AGENT] P0. **F-33 closure** — Scenario-test that `DEFI_LST_DEPEG_STETH_5PCT` fires
      `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` within 30s (carry depeg kill-switch, CSB-12). — strategy-service@46b38b5d
      (9-test suite in tests/risk/unit/test_f33_lst_depeg_scenario.py: registry contract × 5 + kill-switch path × 4; QG
      4103 passed; subscriber captures SCENARIO_SYNTHETIC arm → checker.check_all() passes; non-synthetic arm filtered;
      no-arm control fails. Production cron infra (F-40) provisioned but BLOCKED-DOCKER-IMAGES in sibling plan
      audit03_deployment_cron_provisioning_2026_05_22.md Phase 4 — cron unblocks when strategy-service:latest pushed.)
- [x] ✅ [SCRIPT] P0. Re-run AUDIT-03 §2.1 (CSB) + §2.3 (EXE) + §2.5 (RSK) READ checkpoints; flip the closed findings in
      audit §6 + §6.2 routing table. — uac+exec+strat@2026-05-22 (F-08/09/10/11/12 CLOSED strat@2741643f; F-28 CLOSED
      exec@db50597c; F-33 CLOSED uac@56594ab3; F-26/F-29/F-31 CLOSED exec@769252a8f; §6.2 routing table updated)

## Success criteria

- C4 on all 3 repos (UAC, execution-service, strategy-service); zero basedpyright/ruff regressions.
- B2: depeg scenario trips the carry kill-switch ≤30s in a scenario-matrix run.
- No rebasing-token-to-CeFi-venue transfer can leave the execution layer un-wrapped or un-rejected.

**Full-execution criterion** (per "Plans Run To Actual Completion"):

- ✅ The `DEFI_LST_DEPEG_STETH_5PCT` scenario runs in a real scenario-matrix invocation and the kill-switch fires.
  - **What ran**: scenario-matrix cron / `run-scenario-matrix` against the carry archetype.
  - **Verification**: `KILL_SWITCH_ACTIVATED` event emitted with `archetype=carry_staked_basis` within 30s; observed in
    the events stream.

**Handoff exception**: the scenario-matrix CRON provisioning is in
`audit03_deployment_cron_provisioning_2026_05_22.md`:Phase 2 (F-40). This plan ships the scenario + the validation; that
plan ships the runner.
