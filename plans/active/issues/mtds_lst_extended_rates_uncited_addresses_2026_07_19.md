---
doc_type: issue
title:
  MTDS quality-gates-v2 STEP 5.97 red on live-defi-rollout — 19 uncited Ethereum contract addresses in
  _lst_extended_rates.py
summary:
  "Re-running quality-gates-v2 on market-tick-data-service@live-defi-rollout (as part of clearing escalation agt-e7639b,
  the InstrumentType.LENDING retirement wall) surfaced an INDEPENDENT, unrelated gate failure: STEP 5.97
  (`check_defi_address_citations.py`, baseline
  `unified-trading-pm/scripts/quality_gates/defi_address_citation_baseline.yaml`) fails with 19 uncited contract
  addresses > baseline 0, all in `market_tick_data_service/cli/handlers/_lst_extended_rates.py` (lines 52-289) —
  introduced by `market-tick-data-service@8746708c` ('feat(defi): acquire lst_rates for new staking/restaking/vault
  venues ... verified via live Alchemy RPC'), a commit that predates my session and is unrelated to the
  LENDING/900-line-cap wall I was dispatched to fix. The commit message claims live Alchemy RPC verification, but none
  of the 19 addresses carry the required `# DERIVED <YYYY-MM-DD> from <chain> <source>` citation comment (a couple have
  a bare protocol-name comment, e.g. `# KelpDAO LRTOracle`, `# Renzo ezETH rate provider`, most have none). This is
  currently the ONLY remaining red leg blocking `quality-gates-v2` on live-defi-rollout (verified via a direct
  workflow_dispatch re-run, 29669216186, after my LENDING+900L fix landed at faf4fafa — tests-leg and everything else in
  checks-leg now pass). I did NOT attempt to fix this myself: fabricating a `# DERIVED` citation without re-verifying
  each address on-chain would defeat the purpose of the check (data-correctness on real onchain contract addresses
  feeding live financial data collection) — this needs someone to actually re-run/spot-check the Alchemy verification
  8746708c claims, or add `# QG-allow: defi-citation` only if these are genuinely factory-deployed pool addresses (they
  don't look like it — wBETH/KelpDAO/Renzo/etc. read as protocol-level rate-provider constants, not auto-deployed
  pools)."
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, citation, defi, data-correctness, lst-rates, ci-cd]
related: [defi_consolidated_closeout_2026_07_18.md]
created: 2026-07-19
parent_epic: defi_master
severity: P2
priority: P2
source: cicd escalation agt-e7639b, quality-gates-v2 workflow_dispatch re-run 29669216186
assigned_vm:
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# MTDS quality-gates-v2 STEP 5.97 red — uncited addresses in `_lst_extended_rates.py`

## Discovery context

Dispatched as CICD escalation `agt-e7639b` for `market-tick-data-service#632` (LDR→main promotion PR),
`wall_type=ldr_qg_failure`. Root-caused and fixed the actual assigned wall (two independent causes):

1. `solana_lst_archival.py` at 905L over the 900-line file cap — split into `_solana_lst_archival_tier1.py`.
2. 9 pre-existing test failures from `unified-api-contracts@e319864f` (operator ruling 2026-07-18) retiring
   `InstrumentType.LENDING` as `UNSUPPORTED_BY_DESIGN` — `risk_params_handler.py`, `liquidations_handler.py`, and
   `lending_indices_handler.py` still minted `LENDING` canonical ids. Swapped to `InstrumentType.A_TOKEN` (the reserve's
   canonical representative id) — a deliberately conservative fix that preserves the existing 1-record-per-market shard
   atom the honest-coverage EU-reconciliation depends on (NOT the full A_TOKEN+DEBT_TOKEN per-leg split
   `codex/02-data/cross-asset-canonical-target-ssot.md:160` targets long-term, which would double cardinality and needs
   IS-side EU-seed coordination). Also needed one additive UAC schema-contract entry `(defi, a_token, liquidations)` —
   another agent (slot-4) had already shipped the identical fix concurrently; discarded my duplicate.

Shipped both at `market-tick-data-service@faf4fafa`. Re-ran `quality-gates-v2` directly on `live-defi-rollout`
(`gh workflow run quality-gates-v2.yml --ref live-defi-rollout`, run `29669216186`) to verify — tests-leg passed clean
(6330 passed), but checks-leg failed on **STEP 5.97**, a check unrelated to either of the above two fixes.

## The finding

```
[FAIL] market-tick-data-service: 19 uncited contract address(es) > baseline 0. New/over-baseline site(s):
  market_tick_data_service/cli/handlers/_lst_extended_rates.py:52,64,79,96,112,124,136,148,162,174,186,200,212,224,241,253,265,277,289
```

`scripts/quality_gates/check_defi_address_citations.py` requires every raw `0x...` contract address literal to carry
either `# DERIVED <YYYY-MM-DD> from <chain> <source>` (protocol-level SSOT constant) or
`# QG-allow: defi-citation — <reason>` (factory-deployed pool/pair address). None of the 19 addresses in
`_lst_extended_rates.py` carry either. The baseline (`defi_address_citation_baseline.yaml`) has zero tolerance and must
never be raised.

The file was added whole by `market-tick-data-service@8746708c` (before my session), whose commit message asserts
"verified via live Alchemy RPC" — so the underlying diligence plausibly happened, it just was never captured as the
required inline citation comment. This is why the gate did not previously show red on this file: nothing had re-run the
full unsliced `quality-gates.sh` (or CI's `quality-gates-v2`) against `live-defi-rollout` HEAD since 8746708c landed
until my re-trigger.

## Why I didn't fix it myself

Bounded CICD one-shot scope (agt-e7639b was specifically the LENDING+900L wall, already resolved and shipped). More
importantly: I cannot respons­ibly author 19 `# DERIVED` citations without actually re-verifying each address against a
real source (etherscan/alchemy/protocol docs) — writing a citation I haven't personally checked would be exactly the
kind of unverified claim this gate exists to prevent, on live financial-data-collection contract addresses.

## Recommended next step

A short, targeted task (not a big investigation): pull the 19 `(token, address, chain)` tuples from
`_EVM_EXTENDED_RATE_CONFIGS` in `_lst_extended_rates.py`, spot-check each against etherscan/the protocol's own docs
(most are well-known LST/LRT protocols — wBETH, KelpDAO, Renzo, etc.), then add the
`# DERIVED <date> from ethereum <source>` comment per line. Est. 30-60 min including verification. This is currently the
ONLY thing blocking `quality-gates-v2` on `market-tick-data-service` LDR→main promotion.
