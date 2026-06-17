---
title: E2E defi-strategy run surfaced funding / APR / gas / rate correctness bugs — fix in the MAIN codebase before backfill + live
created: 2026-06-17
author: ikennaigboaka
source:
  - operator 2026-06-17 (recent e2e-testing repo defi-strategy work — ran staked_basis + other light trades to test APRs)
  - e2e-testing/scripts/defi/staked_basis_funding_scan.py + colocated_engine.py
locked_by: live-defi-rollout
---

## What I found

Running the recent **e2e-testing defi-strategy** harness (`scripts/defi/` — staked_basis + light trades, testing APRs) surfaced a cluster of **funding / APR / gas / lending-rate correctness bugs**. These were found in the e2e harness but the ROOT CAUSES are in the **main codebase** (the funding/APR computation the production strategy + the backfill both consume) — so they MUST be fixed in main, not just patched in the harness, or the backfill + live strategies hit the same wrong numbers. The canonical APR/funding-annualisation logic should be ONE SSOT (features-service), consumed everywhere (no divergent copies).

## Why it matters

`carry_staked_basis` net carry = perp-funding APY (± per venue) + staking/LST APY (where the venue accepts the LST as collateral). If funding annualisation, APY, gas, or Aave rates are wrong, the strategy ranks the wrong coins/venues and the backfilled feature/strategy data is poisoned → wrong live decisions. Data-pipeline-correctness is the heartbeat: fix every issue in full before backfill resumes.

## The bugs (each a MAIN-codebase fix)

- [ ] [BUG] P1. **Aster perp-funding acquisition is "weird"** — diagnose how Aster funding is fetched + normalised (mtds Aster perp_funding adapter + UAC `registry.perp_funding_cadence` Aster entry). Confirm the rate sign, interval, and units match the other venues' canonical shape. Repo: market-tick-data-service (+ UAC if cadence/registry).
- [ ] [BUG] P0. **Deribit funding bug** — the Deribit perp-funding path produced wrong values. Root-cause (sign / interval / endpoint / normalisation) + fix + unit test against a recorded Deribit funding sample. Repo: market-tick-data-service (Deribit adapter) + UAC if the cadence/annualisation is wrong.
- [ ] [BUG] P0. **Per-venue funding interval annualisation (1h vs 8h vs 24h)** — funding APY must annualise using each venue's ACTUAL funding interval (Hyperliquid/Aster ~1h, Binance/OKX/Bybit ~8h, some 24h), not a single assumed cadence. Audit `unified_api_contracts.registry.perp_funding_cadence.annualise_funding_rate_bps` (+ every per-venue cadence entry) and every caller; one canonical annualiser, correct per-venue periods/year. Repo: UAC + consumers (mtds, features-service, strategy-service).
- [ ] [BUG] P0. **APY zeros — align to the features-service canonical logic** — the e2e harness/strategy computed APY and got ZEROS where features-service computes them correctly using the same inputs. Make the funding→APY (and LST/staking-APY) computation a SINGLE canonical implementation (features-service / UAC SSOT) consumed by the strategy + the harness — delete the divergent zero-producing path (delete-deprecated-code). Repo: features-service (SSOT) + strategy-service + mtds; align UAC if the annualiser lives there.
- [ ] [BUG] P1. **Gas-cost handling** — possible bug in DeFi gas-cost fetch/normalisation + the net-of-gas consumption in net-carry. Verify the gas_fees adapter + that the strategy subtracts gas from net carry correctly (composes with the audit's "gas NET-COST consumer" + "gas_fees in manifest" items). Repo: market-tick-data-service (gas adapter) + strategy/execution-service (net-cost consumer) + UAC.
- [ ] [BUG] P1. **Aave lending-rate (APY) correctness** — possible bug in the Aave supply/borrow rate fetch + APY conversion (RAY → APY, per-second compounding). Verify against an on-chain reference. Repo: market-tick-data-service (Aave/lending adapter) + UAC if the conversion lives there.

## Recommended decision

Dispatch as a focused correctness workstream (see the dispatch prompt, operator 2026-06-17). **Coordinate the mtds items with the Half-A agent (which owns market-tick-data-service)** — either fold these into that agent or run after its mtds work lands; the features-service / strategy-service / UAC parts are collision-free. Land BEFORE the migration `--apply` + backfill resume so the backfilled funding/APR/gas/rate data is correct from the start.
