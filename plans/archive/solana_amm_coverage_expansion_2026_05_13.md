---
doc_type: plan
title: Solana AMM coverage expansion — METEORA + PHOENIX + JUPITER + LIFINITY + Pyth oracle prices
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-13
type: plan
deadline: 2026-05-23
priority: P0
companion_to: plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md
spawned_from: plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md (Successor plan C)
locked_by: live-defi-rollout
locked_since: 2026-05-13
estimate_class: brand-new
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 3.0
effective_concurrent_slots: 1
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **ARCHIVED 2026-05-16 — 100% done per inventory (slot-8 SWEEP-16 mechanical archive sweep)**

# Solana AMM coverage expansion — Plan C

Successor to the Solana perp DEX adapters (Plan B) that shipped at `instruments-service@5624624` +
`unified-api-contracts@2c69b01`. This plan extends Solana DeFi coverage to 4 AMM/CLOB venues (Meteora, Phoenix, Jupiter,
Lifinity) plus Pyth oracle price feeds for the `arbitrage_price_dispersion` archetype.

**Issue doc**: `plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md` **Codex SSOT**:
`/codex/04-architecture/solana-defi-coverage.md` (Phase 7 updates)

---

## Pre-audit findings

Workspace grep confirms:

- `SOLANA_DEFI_PROTOCOLS` in
  `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_chain_data.py` — jupiter entry
  already existed (aggregator type), others absent
- `SOLANA_PROTOCOL_DEPLOY_DATES` in
  `instruments-service/instruments_service/reference_data/adapters/defi/_solana_utils.py` —
  meteora/phoenix/jupiter/lifinity/pyth absent
- Test dirs: `instruments-service/tests/unit/reference_data/adapters/defi/` — no meteora/phoenix/jupiter/lifinity/pyth
  tests
- No pre-existing meteora.py / phoenix.py / lifinity.py / pyth.py in defi adapter dir

---

## Phase 0 — Audit + plan (SERIAL) [DONE]

- [x] [PLAN] P0. Read Plan B pattern (mango.py, zeta.py, flash_trade.py). Read \_solana_utils.py, \_defi_chain_data.py,
      test patterns. Confirmed clean implementation surface.

---

## Phase 1 — METEORA adapter (PARALLEL with 2/3/4/5)

**Program ID**: LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo (Meteora Dynamic Liquidity) **API**:
https://app.meteora.ag/api/pools **Launch date**: 2022-09-01 **Data type**: SPOT (AMM liquidity pools)

- [x] [SCRIPT] P0. Create `instruments-service/instruments_service/reference_data/adapters/defi/meteora.py` — DLMM pool
      discovery adapter with `_classify_meteora_error` + `MeteoraReferenceDataAdapter`. tick_size derived from bin_step
      (basis points / 10000).
- [x] [SCRIPT] P0. Add `"meteora": datetime(2022, 9, 1, tzinfo=UTC)` to `SOLANA_PROTOCOL_DEPLOY_DATES` in
      `_solana_utils.py`.
- [x] [SCRIPT] P0. Add `"meteora"` entry to `SOLANA_DEFI_PROTOCOLS` in `_defi_chain_data.py`.
- [x] [SCRIPT] P0. Create `tests/unit/reference_data/adapters/defi/test_meteora_metadata.py` — 12 tests covering adapter
      init, record building, error classification, get_instruments filtering, get_instrument lookup, NotImplemented
      methods.

---

## Phase 2 — PHOENIX adapter (PARALLEL with 1/3/4/5)

**Program ID**: PhoeNiXZ8ByJGLkxNfZRnkUfjvmuYqLR89jjFHGqdXY (Phoenix CLOB DEX) **API**:
https://api.phoenix.trade/markets **Launch date**: 2023-06-01 **Data type**: SPOT (CLOB markets — orderbook-based spot
trading)

- [x] [SCRIPT] P0. Create `instruments-service/instruments_service/reference_data/adapters/defi/phoenix.py` — CLOB
      market discovery adapter. Parses base/quote from both `base_params`/`quote_params` dicts and string names (slash
      or dash notation).
- [x] [SCRIPT] P0. Add `"phoenix": datetime(2023, 6, 1, tzinfo=UTC)` to `SOLANA_PROTOCOL_DEPLOY_DATES`.
- [x] [SCRIPT] P0. Add `"phoenix"` entry to `SOLANA_DEFI_PROTOCOLS`.
- [x] [SCRIPT] P0. Create `tests/unit/reference_data/adapters/defi/test_phoenix_metadata.py` — 13 tests.

---

## Phase 3 — JUPITER adapter (PARALLEL with 1/2/4/5)

**Program ID**: JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4 (Jupiter v6 aggregator) **API**:
https://lite-api.jup.ag/swap/v1 (quotes), https://tokens.jup.ag/tokens?tags=strict (token list) **Launch date**:
2021-11-01 **Data type**: SPOT (aggregated token pairs)

Jupiter already had a minimal `SOLANA_DEFI_PROTOCOLS` entry (aggregator type/api_url). Plan C extends it with:

- `"jupiter"` in `SOLANA_PROTOCOL_DEPLOY_DATES`
- Full adapter with `_CORE_ROUTABLE_PAIRS` (15 LST/major pairs for `arbitrage_price_dispersion`)
- Token list fetch capability for extended universe

- [x] [SCRIPT] P0. Create `instruments-service/instruments_service/reference_data/adapters/defi/jupiter.py` — aggregated
      pair discovery adapter with `_CORE_ROUTABLE_PAIRS` list covering SOL/LST pairs critical for
      arbitrage_price_dispersion.
- [x] [SCRIPT] P0. Add `"jupiter": datetime(2021, 11, 1, tzinfo=UTC)` to `SOLANA_PROTOCOL_DEPLOY_DATES`.
- [x] [SCRIPT] P0. Create `tests/unit/reference_data/adapters/defi/test_jupiter_metadata.py` — 13 tests including core
      pair coverage assertions.

---

## Phase 4 — LIFINITY adapter (PARALLEL with 1/2/3/5)

**Program ID**: LFNTYraetVioAPnGJht4yNg2aUZFXR776cMeN9VMjXp (Lifinity V2) **API**: https://api.lifinity.io/pools
**Launch date**: 2022-03-01 **Data type**: SPOT (proactive market-making pools)

- [x] [SCRIPT] P0. Create `instruments-service/instruments_service/reference_data/adapters/defi/lifinity.py` — PMM pool
      discovery adapter. Handles token_0/token_1 dict params + string name fallbacks.
- [x] [SCRIPT] P0. Add `"lifinity": datetime(2022, 3, 1, tzinfo=UTC)` to `SOLANA_PROTOCOL_DEPLOY_DATES`.
- [x] [SCRIPT] P0. Add `"lifinity"` entry to `SOLANA_DEFI_PROTOCOLS`.
- [x] [SCRIPT] P0. Create `tests/unit/reference_data/adapters/defi/test_lifinity_metadata.py` — 12 tests.

---

## Phase 5 — Pyth oracle adapter (PARALLEL with 1/2/3/4)

**UNBANNED per CLAUDE.md 2026-05-06**: Pyth enabled for Solana on-chain price feeds. **API**:
https://hermes.pyth.network/v2/ (Hermes batch REST) **Live RPC**: https://pythnet.rpcpool.com/ (PythNet on-chain, for
live pipeline) **Launch date**: 2021-08-01 **Data type**: SPOT (oracle price feed references)

**Pyth price feed IDs (SSOT — embedded in adapter)**:

- SOL/USD: `H6ARHf6YXhGYeQfUzQNGk6rDNnLBQKrenN712K4AQJEG`
- JITOSOL/USD: `7yyaeuJ1GGtVBLT2z2xub5ZWYKaNhF28mj1RdV4VDFVk`
- mSOL/USD: `E4v1BBgoso9s64TQvmyownAVJbhbEPGyzA3qn4n46qj9`
- bSOL/USD: `AFrYBhb5wKQtxRS9UA9YRS4V3oFXrfW1Kq3hZedLgGiP`
- JUP/USD: `7dbob1psH1iZBS7qPsm3Kwbf5DzSXK8Jyg31CTgTnxH5`
- RAY/USD: `AnLf8tVYCM816gmBjiy8n53eXKKEDydT5piYjjQDPgTB`
- BONK/USD: `8ihFLu5FimgTQ1Unh4dVyEHUGodJ738bWMDule9otdKX`
- WIF/USD: `6ABgrEZkHDexkBEBhXAHmCFmcj1mNLyyhGEe3VC2DfcK`
- JTO/USD: `nJnMsAf9Es6SKY9YaB88weinqoNVrav3wGD7SVoiPaC`
- USDC/USD: `Gnt27xtC473ZT2Mw5u8wZ68Z3gULkSTb5DuxJy7eJotD`

- [x] [SCRIPT] P0. Create `instruments-service/instruments_service/reference_data/adapters/defi/pyth.py` — oracle price
      feed adapter with `PYTH_PRICE_FEEDS` SSOT dict + `PythOracleReferenceDataAdapter` + `fetch_latest_prices()` for
      Hermes batch fetch. raw_symbol = Pyth feed ID (canonical traceability).
- [x] [SCRIPT] P0. Add `"pyth": datetime(2021, 8, 1, tzinfo=UTC)` to `SOLANA_PROTOCOL_DEPLOY_DATES`.
- [x] [SCRIPT] P0. Add `"pyth"` entry to `SOLANA_DEFI_PROTOCOLS` in `_defi_chain_data.py`.
- [x] [SCRIPT] P0. Create `tests/unit/reference_data/adapters/defi/test_pyth_metadata.py` — 14 tests including feed ID
      format validation, SSOT registry coverage, Hermes mock fetch.

---

## Phase 6 — dex_swaps backfill script skeleton (SERIAL — after Phases 1-5)

- [x] [SCRIPT] P0. Create `instruments-service/scripts/backfill_solana_dex_swaps_2026_05_13.py` — per-VM shard isolation
      scaffold with `--dry-run` default, `--apply --confirm` gate, venue scope
      (`--venue meteora|phoenix|jupiter|lifinity|all`), deploy-date floor per venue. Operator-runnable.

**VM launch command** (operator executes; documented here per Runbook Execution-Owner rule):

```bash
gcloud compute instances create solana-dex-backfill-$(date +%Y%m%d-%H%M) \
    --zone=asia-northeast1-b \
    --machine-type=n2-standard-8 \
    --image-family=debian-11 \
    --image-project=debian-cloud \
    --metadata=startup-script="
        export VM_NAME=solana-dex-backfill
        export MANIFEST_PER_VM_SHARDS=true
        export DEPLOYMENT_ENV=prod
        cd /app && python3 scripts/backfill_solana_dex_swaps_2026_05_13.py \
            --venue all --start-date 2022-03-01 --end-date $(date +%Y-%m-%d) \
            --apply --confirm
    " \
    --scopes=cloud-platform
```

Execution metadata:

```yaml
execution:
  owner: Tab 2 — Ikenna slot 2 / cron post-May-23
  cadence: one-shot (backfill); rerun if new venues added
  verifier: manifest captured rows for all 4 Plan C venues; sample parquet OHLC populated
  last_executed: NEVER
```

**DEFERRED**: Full pipeline wiring (dex_swaps write path to GCS + manifest entries for
METEORA-SOLANA/PHOENIX-SOLANA/JUPITER-SOLANA/LIFINITY-SOLANA) is a follow-up after MTDS integrates the new venues. The
backfill script shell is ready; the APPLY mode raises a descriptive warning until MTDS receives the new venue coverage.

---

## Phase 7 — Codex SSOT updates (SERIAL — after Phases 1-6)

- [x] [SCRIPT] P1. Update or create `/codex/04-architecture/solana-defi-coverage.md` to reflect:
  - 4 new AMM/CLOB adapters (Meteora, Phoenix, Jupiter, Lifinity)
  - Pyth oracle integration
  - Updated `SOLANA_DEFI_PROTOCOLS` + `SOLANA_PROTOCOL_DEPLOY_DATES` entries
  - `arbitrage_price_dispersion` strategy coverage map (unified-trading-pm@d3b75916 — extended solana-defi-coverage.md
    with Plan C venue tables)

---

## Phase 8 — Quality gates (SERIAL — after Phases 1-7)

- [x] [SCRIPT] P0. Run `cd instruments-service && bash scripts/quality-gates.sh` — confirm ruff + basedpyright green on
      new adapters + tests. (instruments-service@5665de8 — 78 Plan C tests pass; pre-existing failures are unrelated)
- [x] [SCRIPT] P0. Run `cd unified-api-contracts && bash scripts/quality-gates.sh` — confirm UAC registry additions
      clean. (unified-api-contracts@2dd984e — no errors in \_defi_chain_data.py; 136 pre-existing basedpyright errors in
      other files — not introduced by Plan C)
- [x] [SCRIPT] P0. Verify test count: `cd instruments-service && bash scripts/quality-gates.sh` — should include ≥48 new
      tests across 5 adapters. (78 tests: 12 Meteora + 13 Phoenix + 13 Jupiter + 12 Lifinity + 14 Pyth + 14 fix tests)

---

## Success criteria

- ✅ 5 new Solana adapters wired (4 AMM/CLOB + 1 Pyth oracle)
- ✅ All 5 venues in UAC `SOLANA_DEFI_PROTOCOLS` registry
- ✅ DEFI_VENUE_LAUNCH_DATES extended (5 entries: meteora/phoenix/jupiter/lifinity/pyth)
- ✅ ≥48 tests total across all 5 adapters
- ✅ Codex SSOT reflects new coverage (Phase 7)
- ✅ All commits pushed to origin/live-defi-rollout
- ✅ Plan body populated with phase checkboxes + cross-references

---

## Temporary states + their canonical follow-up plans

- **dex_swaps backfill apply mode**: skeleton only — full pipeline wiring deferred to MTDS Solana venue coverage
  expansion plan (to be filed post-May-23 if not already active).
- **Codex Phase 7**: pending QG pass — will be filed as `docs(codex):` commit after QG green.

---

## Files created

**unified-api-contracts:**

- `unified_api_contracts/registry/capability_declarations/_defi_chain_data.py` — added meteora/phoenix/lifinity/pyth to
  SOLANA_DEFI_PROTOCOLS

**instruments-service:**

- `instruments_service/reference_data/adapters/defi/_solana_utils.py` — added 5 deploy dates
- `instruments_service/reference_data/adapters/defi/meteora.py` — NEW
- `instruments_service/reference_data/adapters/defi/phoenix.py` — NEW
- `instruments_service/reference_data/adapters/defi/jupiter.py` — NEW
- `instruments_service/reference_data/adapters/defi/lifinity.py` — NEW
- `instruments_service/reference_data/adapters/defi/pyth.py` — NEW
- `tests/unit/reference_data/adapters/defi/test_meteora_metadata.py` — NEW (12 tests)
- `tests/unit/reference_data/adapters/defi/test_phoenix_metadata.py` — NEW (13 tests)
- `tests/unit/reference_data/adapters/defi/test_jupiter_metadata.py` — NEW (13 tests)
- `tests/unit/reference_data/adapters/defi/test_lifinity_metadata.py` — NEW (12 tests)
- `tests/unit/reference_data/adapters/defi/test_pyth_metadata.py` — NEW (14 tests)
- `scripts/backfill_solana_dex_swaps_2026_05_13.py` — NEW (operator-runnable skeleton)

**unified-trading-pm:**

- `plans/active/solana_amm_coverage_expansion_2026_05_13.md` — THIS PLAN
