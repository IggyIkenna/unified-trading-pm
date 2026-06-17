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
- [x] ✅ [BUG] P0. **Deribit funding bug** — ROOT CAUSE: UAC `FUNDING_CADENCE_SECONDS["deribit"]` was `1*3600` (annualise ×8760) but the canonical stored `derivative_ticker.funding_rate` is the **8h figure** (Deribit charges hourly but publishes/stores an 8h figure; `external/deribit/normalize.py` maps `funding_8h`). Annualising the 8h figure at 1h over-stated Deribit funding APY by **8×**. FIX: set `deribit = 8*3600` (annualise at the figure's period, 1095/yr) + documented the figure-vs-charge distinction in the module docstring + added `test_deribit_annualises_at_eight_hour_figure` regression guard. No separate mtds Deribit funding adapter exists (Deribit funding flows via the Tardis ticker → UAC normalize, value preserved + matches the exchange API). unified-api-contracts@7fade10 | unit: `tests/unit/test_perp_funding_cadence.py::test_deribit_annualises_at_eight_hour_figure`.
- [ ] [BUG] P0. **Per-venue funding interval annualisation (1h vs 8h vs 24h)** — funding APY must annualise using each venue's ACTUAL funding interval (Hyperliquid/Aster ~1h, Binance/OKX/Bybit ~8h, some 24h), not a single assumed cadence. Audit `unified_api_contracts.registry.perp_funding_cadence.annualise_funding_rate_bps` (+ every per-venue cadence entry) and every caller; one canonical annualiser, correct per-venue periods/year. Repo: UAC + consumers (mtds, features-service, strategy-service).
- [ ] [BUG] P0. **APY zeros — align to the features-service canonical logic** — the e2e harness/strategy computed APY and got ZEROS where features-service computes them correctly using the same inputs. Make the funding→APY (and LST/staking-APY) computation a SINGLE canonical implementation (features-service / UAC SSOT) consumed by the strategy + the harness — delete the divergent zero-producing path (delete-deprecated-code). Repo: features-service (SSOT) + strategy-service + mtds; align UAC if the annualiser lives there.
- [ ] [BUG] P1. **Gas-cost handling** — possible bug in DeFi gas-cost fetch/normalisation + the net-of-gas consumption in net-carry. Verify the gas_fees adapter + that the strategy subtracts gas from net carry correctly (composes with the audit's "gas NET-COST consumer" + "gas_fees in manifest" items). Repo: market-tick-data-service (gas adapter) + strategy/execution-service (net-cost consumer) + UAC.
- [ ] [BUG] P1. **Aave lending-rate (APY) correctness** — possible bug in the Aave supply/borrow rate fetch + APY conversion (RAY → APY, per-second compounding). Verify against an on-chain reference. Repo: market-tick-data-service (Aave/lending adapter) + UAC if the conversion lives there.

## Recommended decision

Dispatch as a focused correctness workstream (see the dispatch prompt, operator 2026-06-17). **Coordinate the mtds items with the Half-A agent (which owns market-tick-data-service)** — either fold these into that agent or run after its mtds work lands; the features-service / strategy-service / UAC parts are collision-free. Land BEFORE the migration `--apply` + backfill resume so the backfilled funding/APR/gas/rate data is correct from the start.

## Progress Log (autonomous — 2026-06-17)

> Handoff doc for this loop (rule 6). Append-only. mtds checked clean (no Half-A in-flight) at start → mtds adapter
> fixes done here too. Dependency order: UAC (T0) → UTL (T0) → service consumers (T4).

**Design decision — Deribit annualisation period (rule 1 forced trade-off, documented):** The operator's 2026-06-16
PM issue `perp_funding_data_semantics_and_cadence_2026_06_16.md` Finding 1 initially marked UAC `deribit=1h` as ✅
(the true CHARGE cadence) but **explicitly conditioned it** on confirming the stored field is the per-hour rate
("confirm the Tardis→MTDS Deribit funding field is the per-hour rate before trusting `annualise(rate,'deribit')` at
24/day"). The e2e scan (`staked_basis_funding_scan.py`, 2026-06-16/17, the source of THIS dispatch) **empirically
confirmed the stored `derivative_ticker.funding_rate` IS the 8h figure** (≈ Deribit API `interest_8h` ~ -1e-6, not
`interest_1h` ~ -1e-8) and worked around it by annualising Deribit at 8h. Chosen resolution: set the registry
`deribit=8*3600` so the annualiser matches the stored 8h figure (preserving the "GCS funding_rate VALUES match the
exchange API exactly" invariant the operator values, and avoiding a lossy `/8` rewrite or a full Deribit re-backfill).
The registry's semantic is now documented as "the period the stored funding_rate figure represents" = the annualisation
period (= the charge interval for every venue except Deribit). If the ingest is ever switched to persist Deribit's
per-hour rate, flip the entry back to `1*3600` in the same commit (noted in the module docstring). This supersedes the
operator's pre-confirmation "assert deribit=1h" todo-line, which was conditional on the now-falsified per-hour-field
assumption.

- **[DONE] Deribit P0** — unified-api-contracts@7fade10. Cadence `deribit 1h→8h` + figure-vs-charge docstring +
  `fundings_per_day()` SSOT helper (registry re-export) + regression unit tests. QG green (208s), landed on LDR.
