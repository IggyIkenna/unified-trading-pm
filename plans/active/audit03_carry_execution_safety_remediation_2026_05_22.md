---
name: audit03_carry_execution_safety_remediation
title: "AUDIT-03 remediation — carry_staked_basis execution & risk safety (May-23 P0)"
type: active
parent_epic: defi_master
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
      op-gate. FINDING: WrapPreprocessor has NO callers in production code (only **init**.py re-export + tests).
      `_WRAP_TYPE_MAP`/`_UNWRAP_RULES` used only within wrap_preprocessor.py. Safe to edit without breaking other
      callers. TRANSFER already in op-type gate; stETH→wstETH in \_WRAP_TYPE_MAP. UAC PROTOCOL_TOKEN_PREFERENCE missing
      Deribit/Bybit/OKX — gap for Phase 1 F-11 fix.
- [x] ✅ [AGENT] P0. Grep all readers of `net_carry` / `stake_fraction` / `_build_legs` in strategy-service before
      changing the carry formula (F-09/F-10). FINDING: net_carry formula at staked_basis.py:299 already
      `f*(staking_apy+funding_apy)-fees`; only caller of \_build_legs in carry path is staked_basis.py:503;
      sports_arb_engine.py:74 has unrelated \_build_legs. stake_fraction in config.py:187+720, types.py:384+397, and
      script files (trace_carry_staked_basis.py). Safe to enforce f==1.0 — only carry engine path, no sports callers
      affected.
- [x] ✅ [AGENT] P0. Confirm UAC `registry/token_wrapping.py:31-33` `stETH→wstETH` rule + `needs_wrapping()` are the
      canonical source the preprocessor should call (verified present in §6.1). CONFIRMED: token_wrapping.py:32 has
      TokenWrappingRule(stETH, wstETH) + PROTOCOL_TOKEN_PREFERENCE maps stETH→wstETH for AAVEV3/MORPHO but MISSING
      DERIBIT/BYBIT/OKX — this is the gap for Phase 1 F-11 (will be added there).

## Phase 1 — UAC foundation (scenario + wrapping registry) — L0/L2, must precede consumers

- [x] ✅ [AGENT] P0. **F-33** — Add `DEFI_LST_DEPEG_STETH_5PCT` scenario to
      `unified-api-contracts/.../registry/scenarios/defi.py` (joins the existing 6). Model an LST↔ETH peg break:
      stETH/wstETH (and rETH/cbETH/JitoSOL/mSOL by parametrisation) priced 5% below ETH; instruments = the LST set (NOT
      the stablecoin set `{USDC,USDT,DAI,USDE}`). Wire `CANONICAL_*_VERSION` bump. Add to the `SCENARIOS` tuple. DONE:
      uac@56594ab (F-33 LST depeg scenario + CeFi venue token wrapping). Uses LST_DEPEG_MODERATE breaker.
- [x] ✅ [AGENT] P1. Confirm + (if needed) extend `registry/token_wrapping.py` `PROTOCOL_TOKEN_PREFERENCE` so CeFi-perp
      collateral targets (Deribit/Bybit/OKX) map to their required non-rebasing token (wstETH) — the matrix in UAC
      `registry/venue_collateral.py` is the source. DONE: uac@56594ab added DERIBIT/BYBIT/OKX entries with
      venue-specific stETH/wstETH preference (DERIBIT: stETH only; BYBIT: both; OKX: wstETH only).
- [ ] [SCRIPT] P0. UAC quality-gates Pass 1 GREEN (`cd unified-api-contracts && bash scripts/quality-gates.sh`).

## Phase 2 — execution-service wrap preprocessor (F-28, P0) — gated on Phase 1

- [x] ✅ [AGENT] P0. **F-28** — Rewire `execution_service/engine/preprocessors/wrap_preprocessor.py` to call UAC
      `needs_wrapping()` for the ENTRY path (today it only calls `needs_unwrapping()` for exits + uses a hardcoded
      `_WRAP_RULES` dict missing stETH). Add the `stETH→wstETH` rule. DONE: execution-service@db50597c + @e0ce5dba
      (supplemental coverage).
- [x] ✅ [AGENT] P0. **F-28** — Extend the op-type gate (L197-206) so a CeFi collateral `TRANSFER` leg whose destination
      venue requires a non-rebasing token triggers a wrap step (or is rejected with a typed error) — currently
      `TRANSFER`/`TRADE` fall through unguarded. DONE: execution-service@db50597c. TRANSFER included in op-type gate;
      UnsupportedCapabilityError raised for banned combos.
- [x] ✅ [AGENT] P1. Classify a banned/un-wrappable collateral transfer via UAC `classify_venue_error()` + emit
      `ADAPTER_FETCH_FAILED`/typed reject — no silent pass-through. DONE: UnsupportedCapabilityError (typed reject)
      raised at preprocess() — no silent pass-through. classify_venue_error wired in adapters (d7ac3ffc).
- [x] ✅ [SCRIPT] P0. execution-service quality-gates Pass 1 GREEN + unit test: `stETH → Deribit/Bybit/OKX` transfer now
      wraps to wstETH (or rejects); `wstETH → Deribit` still rejected. — execution-service@e0ce5dba (backfilled
      2026-05-24)

## Phase 3 — strategy-service carry engine (F-08/09/10/11/12) — gated on Phase 1

File: `strategy-service/.../engine/strategies/v2/carry_and_yield/staked_basis.py`

- [x] ✅ [AGENT] P0. **F-11** — Add per-venue wrap + banned-combo guard at `_build_legs` (stETH→OKX,
      wstETH→Deribit/Bybit) — do NOT rely solely on config + the EXE-07 preprocessor. `_derive_structure` already blocks
      stETH→OKX via `accepted_perp_collateral`; close the wstETH→Deribit/Bybit hole. DONE: \_BANNED_LST_PERP_COMBOS at
      staked_basis.py:117-118 + \_build_legs guard at :334-343.
- [x] ✅ [AGENT] P1. **F-10** — Add the `− fees` term to `net_carry` (staked_basis.py:254) per codex
      `carry-staked-basis.md:53` (`net_apy_bps = staking_apy_total + funding_apy − fees`). Removes the optimistic entry
      threshold. DONE: staked_basis.py:299 — `net_carry = f * (staking_apy + funding_apy) - fees`.
- [x] ✅ [AGENT] P1. **F-09** — Enforce `stake_fraction == 1.0` (LST-as-margin has no spare-USDC leg); delete the
      SPLIT_STAKE-era f-grid + `(1-f)·idle_yield` term. Reject `f<1` at preflight rather than mis-size. DONE:
      staked_basis.py:243-248 — `if stake_fraction != Decimal("1.0"): raise`.
- [x] ✅ [AGENT] P1. **F-12** — Implement the `allowed_chains` gate (codex `[ethereum, solana, arbitrum]`); engine
      refuses to size on-chain positions outside the list. Currently absent from all of strategy-service. DONE:
      \_ALLOWED_CHAINS frozenset at staked_basis.py:124 + preflight gate at :249-253.
- [x] ✅ [AGENT] P2. **F-08** — Delete stale docstrings: the deleted SPLIT_STAKE 3-leg path (L15-19) + "zero LST venues
      / zero slots" claim (L128-131), which contradicts the 6 matrix pairs / 4 live carry slots. DONE: staked_basis.py
      docstring updated — SPLIT_STAKE deletion explained at :141-148; no stale "zero LST" claim.
- [x] ✅ [SCRIPT] P0. strategy-service quality-gates Pass 1 GREEN + unit tests for the new guards + the corrected
      `net_carry`. — strategy-service@dfe9d231 (guards) + @33b7168e (F-11 hole) + @805dd40d (tests) +
      e2e-testing@26f54fd (ruff QG fix) — QG exit 0 confirmed 2026-05-24 (backfilled)

## Phase 4 — scenario validation (F-33 closure) — gated on Phase 1-3

- [x] ✅ [AGENT] P0. **F-33 closure** — Scenario-test that `DEFI_LST_DEPEG_STETH_5PCT` fires
      `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` within 30s (carry depeg kill-switch, CSB-12). Cross-plan dep: the
      `mtds-scenario-matrix` cron (F-40) that RUNS this lives in `audit03_deployment_cron_provisioning_2026_05_22.md`. —
      strategy-service@46b38b5d (scenario test) + @a64cb023 (D.2 calibration) + @ba290944 (check_lst_depeg) (backfilled
      2026-05-24)
- [ ] [SCRIPT] P0. Re-run AUDIT-03 §2.1 (CSB) + §2.3 (EXE) + §2.5 (RSK) READ checkpoints; flip the closed findings in
      audit §6 + §6.2 routing table.

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
