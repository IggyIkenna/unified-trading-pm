---
title: "Solana LST + native staking adapters — Successor Plan A"
created: 2026-05-14
author: slot-3-ikenna
type: active-plan
status: active
migrated_from: plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md § "Successor plan A"
locked_by: live-defi-rollout
locked_since: 2026-05-14
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
deadline: 2026-05-23
---

> **MIGRATED FROM**: `plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md` § "Recommended decision — Successor
> plan A — Solana LST + native staking adapters" (filed 2026-05-13 by slot 3 audit).

## Context

Two May-23 DeFi archetypes require Solana LST data:

- **`carry_staked_basis`** (lead archetype): needs JITO-SOLANA + MARINADE-SOLANA LST rates + native SOL staking yield as
  the base carry. Currently 0% captured for both venues. The hedge leg (`DRIFT/JitoSOL+mSOL`) is non-operational until
  LST oracle prices land.
- **`arbitrage_price_dispersion`**: needs `staked_token_oracle_prices` for cross-venue price-dispersion computation (LST
  depeg detection).

### Existing infrastructure (already shipped — do NOT re-implement)

| Component                         | Location                                          | Status                                      |
| --------------------------------- | ------------------------------------------------- | ------------------------------------------- |
| Pyth Hermes historical batch      | MTDS `oracle_prices_handler.py:375,708`           | ✅ wired                                    |
| Pyth Hermes source priority       | UAC `source_priority.py:162,269`                  | ✅ declared                                 |
| `_SANCTUM_RULES` risk rules       | UAC `registry/risk_rules/venue.py:318`            | ✅ exists                                   |
| `solblaze.py` connector           | execution-service `protocols/solblaze.py`         | ✅ exists                                   |
| JITO/mSOL Pyth feed IDs           | MTDS `oracle_prices_handler.py` `_PYTH_FEEDS`     | ✅ exists (added 2026-05-14 slot-3 session) |
| `native_staking_apr` schema field | UAC `internal/domain/defi/sim_schemas.py:101-103` | ✅ schema-only; no capture adapter          |

### What is missing

1. **SANCTUM instruments-service adapter** — instruments-service has no `sanctum.py`; UAC capability declarations need
   `SANCTUM-SOLANA` entry.
2. **SOLBLAZE MTDS flow** — `solblaze.py` connector exists in execution-service but no instruments-service reference
   data adapter → no manifest rows → MTDS won't schedule it.
3. **`staked_token_oracle_prices` MTDS run** — Pyth Hermes feeds for JITOSOL/mSOL/bSOL/INF are declared in MTDS but no
   scheduled VM captures these LST feeds specifically.
4. **`native_staking_rates` adapter** — no instruments-service adapter + no MTDS handler exists. Source: Solana RPC
   `getInflationRate`/`getEpochInfo`/`getValidators` + Helius APY aggregation.
5. **JITO-SOLANA / MARINADE-SOLANA backfill** — 0% capture despite adapters existing. Need VM launch to pull historical
   data from 2022-08 (JITO) and 2021-02 (MARINADE) launch dates.

---

## Phase 1 — UAC capability declarations (P0)

- [x] [UAC] P0. Add `SANCTUM-SOLANA` to `DEFI_VENUE_LAUNCH_DATES` in `unified_api_contracts/registry/chain_env.py`.
      Launch date: `"2023-06-01"` (Sanctum v1 mainnet launch, conservative). Chain = SOLANA. Asset class = LST.
      (UAC@75ee9c4 — chain_env.py PROTOCOL_LAUNCH_DATES entry added)
- [x] [UAC] P0. Add `SANCTUM-SOLANA` to `DEFI_INSTRUMENTS_NOT_YET_COLLECTED` in
      `unified_api_contracts/registry/capability_declarations/_defi_coverage.py` so data-status does not flag historical
      days as missing until first parquet write lands.
      (UAC@75ee9c4 — added with Phase 2 removal note)
- [x] [UAC] P0. Add `SOLBLAZE-SOLANA` to `DEFI_INSTRUMENTS_NOT_YET_COLLECTED` (same reason — adapter exists but MTDS
      hasn't scheduled capture yet).
      (UAC@75ee9c4 — added with Phase 3 removal note)
- [x] [UAC] P0. Verify `JITO-SOLANA` and `MARINADE-SOLANA` are NOT in `EMPTY_OR_DEPRECATED_DEFI_VENUES` (they are real
      venues, just have 0% capture due to VM never running). If incorrectly listed there, remove.
      (UAC@75ee9c4 — verified: only TRADER_JOEV2-AVALANCHE, UNISWAPV3-POLYGON, GMX-AVALANCHE in that set; no action needed)

**QG gate**: `bash scripts/quality-gates.sh` in UAC.

**Done definition**: UAC lint + type-check passes; no regressions in cassette parity tests.

---

## Phase 2 — SANCTUM instruments-service adapter (P0)

- [x] [instruments-service] P0. Read existing Solana LST adapter pattern (e.g., `solblaze.py` or `jito.py`) in
      instruments-service. Extend the pattern to SANCTUM. (instruments-service@346be5d)
- [x] [instruments-service] P0. Create `adapters/defi/sanctum.py`: static registry adapter returning INF + JSOL as
      YIELD_BEARING instruments. Factory wired. (instruments-service@346be5d)
- [x] [instruments-service] P0. Add unit tests: 7 tests covering happy path + instrument_type filter + get_instrument
      lookup + unsupported methods. All pass. (instruments-service@346be5d)
- [x] [instruments-service] P0. Register `SANCTUM-SOLANA` in instruments-service factory.py so MTDS scheduler picks
      it up. (instruments-service@346be5d)

**QG gate**: `bash scripts/quality-gates.sh` in instruments-service.

**Done definition**: QG pass; SANCTUM adapter fetches live data in local mock test.

---

## Phase 3 — SOLBLAZE MTDS wiring (P1)

- [ ] [instruments-service] P1. Verify `SOLBLAZE-SOLANA` (or `BLAZESTAKE-SOLANA`) has a `ReferenceDataAdapter` in
      instruments-service. If missing, create following SANCTUM pattern from Phase 2 — source: `api.blazestake.com` or
      `solblaze.org` public API.
- [ ] [MTDS] P1. Wire SOLBLAZE into MTDS `defi_lst_handler.py` (or equivalent LST rates handler): - Read
      `SOLBLAZE-SOLANA` from instruments config. - Fetch `lst_rates` via instruments-service reference data. - Emit
      manifest `record_captured()` per day per instrument. - `record_empty(reason=EXPECTED_PRE_VENUE_LAUNCH)` for dates
      before BlazeStake mainnet (`2022-11-01`, conservative).

**QG gate**: `bash scripts/quality-gates.sh` in MTDS.

**Done definition**: MTDS unit test captures a mock SOLBLAZE-SOLANA LST rate; manifest writes succeed.

---

## Phase 4 — `staked_token_oracle_prices` MTDS scheduling (P0)

The infrastructure exists (Pyth Hermes feeds for JITOSOL/mSOL/bSOL/INF landed 2026-05-14 in MTDS
`oracle_prices_handler.py`). This phase verifies configuration and schedules a backfill run.

- [ ] [MTDS] P0. Verify `_PYTH_FEEDS` in `oracle_prices_handler.py` includes all 4 LST feeds: JitoSOL/USD, mSOL/USD,
      bSOL/USD, INF/USD. Confirm feed IDs match Pyth mainnet: - JitoSOL: `67be9f519...` (32-byte hex from MTDS commit
      2026-05-14) - mSOL: verify against `https://pyth.network/price-feeds/crypto-msol-usd` - bSOL: verify against Pyth
      bSOL/USD feed page - INF: verify against Pyth INF/USD feed page
- [ ] [MTDS] P0. Confirm `oracle_prices_handler.py` `process()` dispatches `SOLANA` chain correctly for the LST venues
      (e.g., `JITO-SOLANA` or `JITO`). Add routing test if missing.
- [ ] [deployment-service] P0. Add VM launcher for `staked_token_oracle_prices` backfill covering `2023-10-01` (Pyth
      archive start) → today for JITO-SOLANA + MARINADE-SOLANA + SOLBLAZE-SOLANA. VM name prefix: `pyth-lst-backfill`
      (register in `VM_PREFIX_TO_BUCKET`). Backfill window: 7+ months → **REQUIRES operator ping before launch** per GCS
      backfill rule.

**Done definition**: VM launcher script exists; awaiting operator approval ping.

---

## Phase 5 — `native_staking_rates` adapter (P1)

This is the only phase that requires a wholly new data_type.

- [ ] [UAC] P1. Add `native_staking_rates` to `DataType` enum in UAC `canonical/crosscutting/data_types.py` (if not
      already present). Schema: `(chain, epoch, validator_vote_account, commission_pct, base_apy, mev_apy, total_apy)` —
      confirm against `sim_schemas.py:101` `native_staking_apr` field.
- [ ] [UAC] P1. Register `SchemaContract` for `native_staking_rates` in
      `unified_api_contracts/internal/schemas/contracts.py` for `defi` asset group.
- [ ] [instruments-service] P1. Create `adapters/defi/solana_native_staking.py`: - Sources: Solana RPC
      `getInflationRate` + `getEpochInfo` (no API key); Helius APY endpoint
      `https://mainnet.helius-rpc.com/v0/addresses/{validator}/staking-rewards` (requires Helius API key — file
      `BLOCKED-CREDENTIALS` ping if key not in config). - Data type: `native_staking_rates` per epoch (daily-ish, ~2.5
      day granularity). - Backfill start: 2020-03-16 (Solana mainnet genesis). -
      `record_empty(reason=EXPECTED_PRE_GENESIS_CHAIN)` for pre-genesis dates. - Unit tests with mock RPC responses.
- [ ] [MTDS] P1. Add `native_staking_handler.py` (or extend existing Solana handler) for `native_staking_rates`
      data_type. Follow writegate Phase 6 emission policy.

**QG gate**: `bash scripts/quality-gates.sh` in UAC + instruments-service + MTDS.

**Done definition**: `native_staking_rates` UAC schema registered; instruments-service adapter fetches mock epoch data;
MTDS handler writes 1 row per epoch per validator to manifest.

---

## Phase 6 — JITO-SOLANA + MARINADE-SOLANA backfill (P0, infra)

> **GCS backfill rule**: both venues have ≥ 2 years of data → **OPERATOR APPROVAL REQUIRED** before launching. Add ping
> to `ikenna_orchestrator/pings/slot_3.md` and HOLD until `[ack]`.

- [ ] [deployment-service] P0. Verify JITO-SOLANA adapter is functional against current Jito API endpoint (check
      `jito.py` base URL is still live — similar to ASTER URL migration). Run quick test fetch.
- [ ] [deployment-service] P0. Verify MARINADE-SOLANA adapter is functional against current Marinade API endpoint (check
      `marinade.py` base URL).
- [ ] [deployment-service] P0. **[BLOCKED-CREDENTIALS — pinging operator]** Add VM launchers: - `jito-solana-backfill` —
      JITO-SOLANA `lst_rates` from 2022-08-01 → 2026-05-14. - `marinade-backfill` — MARINADE-SOLANA `lst_rates` from
      2021-02-01 → 2026-05-14. - Both: `VM_NAME=<prefix>` + `MANIFEST_PER_VM_SHARDS=true` + singleton-locked. - Register
      both VM prefixes in `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py`.

**CREDENTIAL APPROVAL REQUEST — JITO-SOLANA/MARINADE-SOLANA Backfill**

```
Action: GCS backfill write of ≥2 years of historical LST rates data
Venues: JITO-SOLANA (2022-08 → present), MARINADE-SOLANA (2021-02 → present)
Data type: lst_rates
Cost estimate: ~80-150 VM-hours across 2 VMs; GCS write ~50-200 MB
Why: 0% capture despite adapters existing; critical for carry_staked_basis archetype
Without it: carry_staked_basis archetype has no historical performance baseline
```

**Done definition**: Operator acks the backfill ping; VM launchers exist in deployment-service; backfill VMs complete
with manifest captured rows ≥ 90% of expected date range.

---

## Codex SSOT updates

- [ ] [codex] P1. Update `codex/02-data/defi-data-type-taxonomy.md` when Phase 5 ships: add `native_staking_rates` to
      the Solana data-type table.
- [ ] [codex] P1. Update `codex/02-data/instrument-pipeline-defi.md` to add SANCTUM + SOLBLAZE to the Solana LST adapter
      table.

---

## Temporary states + their canonical follow-up plans

| State                                                     | Successor                                            |
| --------------------------------------------------------- | ---------------------------------------------------- |
| `SANCTUM-SOLANA` in `DEFI_INSTRUMENTS_NOT_YET_COLLECTED`  | Remove when Phase 2 ships + first backfill completes |
| `SOLBLAZE-SOLANA` in `DEFI_INSTRUMENTS_NOT_YET_COLLECTED` | Remove when Phase 3 ships + first backfill completes |
| `BLOCKED-CREDENTIALS` on Phase 6 backfill                 | Remove when operator acks the ping                   |

---

## Deferred items (NOT in scope of this plan)

- Successor plan B (DRIFT-SOLANA + perp DEX adapters) → `plans/active/solana_perp_dex_adapters_*.md`
- Successor plan C (METEORA + PHOENIX + JUPITER AMM) → `plans/active/solana_amm_coverage_*.md`
- Successor plan D (naming convention reconciliation `MARINADE` vs `MARINADE-SOLANA`) → operator decision gate first
- Successor plan E (restaking rewards — Jito VRT + Solayer + Picasso + Cambrian) →
  `plans/active/solana_restaking_rewards_*.md`
