---
title: "AUDIT-03 — Phase 1 READ results: §2.4 P&L attribution"
audit_id: AUDIT-03
run_phase: "Phase 1 — static drift (codex+plans ↔ code), READ checkpoints"
section: "§2.4 P&L + attribution (PNL-*)"
date: 2026-05-22
method: "sonnet sub-agent first-pass (evidence-required) → Opus reviewer consolidation"
auditor: Harsh + Claude Opus 4.7 (reviewer)
checklist: audits/audit-files/audit_03_defi_archetypes_e2e.md
code_audited:
  - strategy-service@b303a358 — strategy_service/pnl/engine/{archetype_aggregator.py, reward_attribution.py, orchestrator.py, pnl_input_builder.py}
  - unified-api-contracts — internal/risk.py (PnLBreakdown, PnLAttributionRow, PnLFactor, PnLLayer)
oracle: codex/09-strategy/architecture-v2/cross-cutting/{pnl-attribution.md, restaking-reward-economics.md}
---

# AUDIT-03 — Phase 1 READ — §2.4 P&L attribution

Sub-agent first pass, Opus-reviewed. **4 findings (F-16…F-19).** Two are HIGH-impact + flagged **NEEDS-CONFIRM**
(Opus to re-verify before any remediation — they assert canonical-schema non-use across the whole P&L path).

## Per-checkpoint verdicts

| ID | Verdict | Evidence |
| -- | ------- | -------- |
| PNL-01 | PASS | `orchestrator.py:465-466` `index_growth = end_idx/start_idx - 1; interest_rate_pnl = abs(deployed)*index_growth` reads `aave_liquidity_index`; `currentLiquidityRate` not referenced. `pnl_input_builder.py:191` mirrors for LEND/STAKE ✓ |
| PNL-03 | PASS | `reward_attribution.py:36-38` maps `CARRY_BASE`/`CARRY_AVS_CONTINUOUS`/`CARRY_ISSUER_SEASONAL`; no `_eigenlayer_aggregate_apy` anywhere ✓ |
| PNL-04 | PASS | `reward_attribution.py:102` slippage = mark − realised − fees (matching-engine output, not hardcoded haircut); doc L59 confirms ✓ |
| PNL-05 | **GAP** | `reward_attribution.py:159` `if row.held or row.points_pending: continue` — pre-TGE points rows **silently skipped**, NOT emitted as `CARRY_ISSUER_SEASONAL value_eth=0 points_pending=true` per codex → F-16 |
| PNL-06 | **CODE-DRIFT** | pnl/engine writes `PnLBreakdown` (UAC risk.py:224 — `account_id: str` free-form, NO `factor`/`layer`). Canonical `PnLAttributionRow` (risk.py:943, has `factor:PnLFactor`+`layer:PnLLayer`) appears never instantiated in this path; factor identity stored as `account_id="carry_base"` string → F-17 **(NEEDS-CONFIRM)** |
| PNL-08 | **CODE-DRIFT** | primary gas path reads `gas_cost_usd` passthrough ✓ BUT `pnl_input_builder.py:142-151` hardcodes `_defaults` ETH price `"3200"` for chains 1/10/8453/42161 when parquet lacks `native_token_price_usd` → F-18 |
| PNL-10 | PASS | `archetype_aggregator.py:181-187` groups by `(archetype, config_variant)` via `_SLOT_PREFIX_RE = ^([A-Z][A-Z0-9_]+)@` ✓ |
| PNL-13 | **RE-SCOPE** | no separate `pnl-attribution-service` repo in workspace — PnL is **consolidated into strategy-service/pnl/** (per strategy-service-is-sum-of-services). `ARBITRAGE_PRICE_DISPERSION` handled generically via `archetype_aggregator` (PNL-10 PASS), not arch-specific code. GCS `by_strategy/ARBITRAGE_PRICE_DISPERSION/` reachability = Phase 2. Update checkpoint wording to drop "pnl-attribution-service". |
| PNL-02/07 | PHASE2 | borrow-sign inversion present (`orchestrator.py:467`); wrapped-vs-rebasing split + T+1 02:00 recon thresholds = behaviour/Phase 2 (recon path not in pnl/engine — separate location) |

## Findings

| ID | Checkpoint | Class | Finding | Sev | Status |
| -- | --------- | ----- | ------- | --- | ------ |
| F-16 | PNL-05 | GAP | Pre-TGE points rows silently `continue`d instead of emitting honest `CARRY_ISSUER_SEASONAL value_eth=0 points_pending=true` rows — silent-absence anti-pattern; downstream loses visibility into accruing-but-unrealised points. `reward_attribution.py:159` | P1 | AGENT-FOUND |
| F-17 | PNL-06 | CODE-DRIFT | pnl/engine emits `PnLBreakdown` (free-form `account_id` string, no `factor:PnLFactor`/`layer:PnLLayer`) rather than canonical `PnLAttributionRow`; typed dual-axis schema appears unused in the path → STRATEGY_ALPHA/EXECUTION_ALPHA absent at row level. **Affects ALL archetypes' P&L.** `reward_attribution.py:96`, `pnl_input_builder.py:169-204` | P1 | **NEEDS-CONFIRM** (Opus re-verify: check for a PnLBreakdown→PnLAttributionRow converter / emit step before accepting) |
| F-18 | PNL-08 | CODE-DRIFT | Hardcoded `"3200"` ETH-price fallback in `pnl_input_builder.py:142-151` `_defaults` (chains 1/10/8453/42161) when gas-fee parquet lacks `native_token_price_usd` — violates "no hardcoded gas/price constants". | P2 | AGENT-FOUND |
| F-19 | PNL-11/12 | CODE-DRIFT | Funding-PnL proxy `abs(net_qty)*last_price*0.0001` (synthetic 1 bps surrogate) instead of `position_qty × funding_rate × interval` from actual funding events. `pnl_input_builder.py:198` | P2 | AGENT-FOUND |

## Reviewer note

F-16 + F-17 are the high-impact ones and are sonnet-sourced; **I (Opus) re-verify both before they drive any code
change** — specifically F-17: confirm no `PnLBreakdown`→`PnLAttributionRow` conversion exists at the emit/serialize
boundary (the agent read the compute path; the canonical row may be built downstream). F-13…F-15, F-18, F-19 accepted on
cited evidence.
