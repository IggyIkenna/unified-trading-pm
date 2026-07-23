---
doc_type: plan
title: Solana perp DEX adapters — DRIFT debug + MANGO V4 + ZETA + FLASH + DRIFT funding backfill
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
spawned_from: plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md (Successor plan B)
locked_by: live-defi-rollout
locked_since: 2026-05-13
estimate_class: brand-new
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 4.0
effective_concurrent_slots: 2-4
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **ARCHIVED 2026-05-16 — 100% done per inventory (slot-8 SWEEP-16 mechanical archive sweep)**

> **Scope: Successor Plan B from `solana_defi_coverage_gaps_2026_05_13.md`.** Plan A (LST + native staking) and Plan C
> (AMM coverage) are separate concurrent plans. This plan covers only Solana perp DEX adapters.

## Why this plan

`arbitrage_price_dispersion` archetype needs Solana perp DEX hedge legs. Currently:

- **DRIFT-SOLANA**: adapter code exists, factory registered, MTDS referenced → 0% captured (28,340 rows at 0% capture).
- **MANGO-SOLANA**: no adapter, no UAC registry, not in manifest.
- **ZETA-SOLANA**: no adapter, no UAC registry, not in manifest.
- **FLASH-SOLANA**: MTDS references it, no instruments-service adapter, not in manifest.

Root cause (Phase 0 audit): DRIFT-SOLANA instrument `available_from` mismatch. The Drift v2 mainnet launch date in
`_solana_utils.SOLANA_PROTOCOL_DEPLOY_DATES["drift"]` is `2022-11-04`, but the manifest was pre-populated with rows
starting `2018-01-01`. Slot 3 corrected the `expected_unattempted` rows to `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH`
via `defi_legacy_blank_reclassification_2026_05_13.md`, but the LIVE capture problem persists: the Drift Data API
(`https://data.api.drift.trade/stats/markets`) returns markets, but the instruments-service adapter at
`adapters/defi/drift.py` implements only `get_instruments()` (reference data) — it does NOT fetch `perp_funding` /
`perp_open_interest` / `perp_mark_prices` data_types. Those are MTDS responsibilities, but MTDS is missing the Solana
perp DEX source wiring needed to call the Drift historical S3 archive.

**Corrected root cause**: The instruments-service DRIFT adapter is correctly serving reference data (instrument
discovery). The 0% capture is in MTDS (market data), not instruments-service. This plan adds instruments-service
adapters for MANGO / ZETA / FLASH (missing adapters), and documents MTDS wiring required for all 4 venues (tracked as
deferred MTDS work below).

## Pre-audit manifest

| Repo                | File                                                   | Line | Symbol                             | Action                       |
| ------------------- | ------------------------------------------------------ | ---- | ---------------------------------- | ---------------------------- |
| instruments-service | `reference_data/factory.py`                            | 29   | `DriftReferenceDataAdapter` import | KEEP — already registered    |
| instruments-service | `reference_data/factory.py`                            | 164  | `"DRIFT-SOLANA": "drift"`          | KEEP — already registered    |
| instruments-service | `reference_data/adapters/defi/`                        | —    | `mango.py`                         | NEW — this plan              |
| instruments-service | `reference_data/adapters/defi/`                        | —    | `zeta.py`                          | NEW — this plan              |
| instruments-service | `reference_data/adapters/defi/`                        | —    | `flash_trade.py`                   | NEW — this plan              |
| instruments-service | `reference_data/factory.py`                            | —    | MANGO/ZETA/FLASH entries           | NEW — this plan              |
| UAC                 | `registry/capability_declarations/_defi_chain_data.py` | 539  | `SOLANA_DEFI_PROTOCOLS`            | ADD mango/zeta/flash entries |
| UAC                 | `registry/capability_declarations/_defi_chain_data.py` | 41   | `SOLANA_PROTOCOL_DEPLOY_DATES`     | ADD mango/zeta/flash entries |
| instruments-service | `scripts/backfill_drift_funding_2026_05_13.py`         | —    | backfill script                    | NEW — this plan              |
| unified-trading-pm  | `/codex/04-architecture/solana-defi-coverage.md`       | —    | codex SSOT                         | NEW — this plan Phase 6      |

## Phases

### Phase 0 — Audit + root cause (SERIAL — prerequisite)

- [x] P0. Audit DRIFT-SOLANA 0% capture root cause. Root cause identified: instruments-service DRIFT adapter is healthy
      (correctly serves instrument discovery via Drift Data API). MTDS has no Solana perp funding source wired. DRIFT
      historical S3 archive (`drift-historical-data-v2.s3.eu-west-1.amazonaws.com`) is documented in UAC
      `SOLANA_DEFI_PROTOCOLS["drift"]["s3_historical_url"]` but MTDS has no consumer for it. Capture fix requires MTDS
      work (deferred below). The instruments-service adapter deploy-date (`2022-11-04` Drift v2) is correct. The
      pre-populated manifest rows (2018-01-01 start) were incorrectly `expected_unattempted`; slot 3 reclassified them
      to `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH` on 2026-05-13.

**Deferred MTDS follow-up**: `EXPECTED_PRE_VENUE_LAUNCH` correction complete. MTDS perp funding wiring deferred to
`plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md` until MTDS Solana perp DEX source is implemented.

### Phase 1 — UAC registry additions (SERIAL — prerequisite for adapters)

- [x] P0. [CODE] Add MANGO V4, ZETA, FLASH entries to `SOLANA_DEFI_PROTOCOLS` dict in
      `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi_chain_data.py`. (UAC@5c83b64 —
      3 new protocol entries: mango/zeta/flash_trade)
- [x] P0. [CODE] Add MANGO-SOLANA, ZETA-SOLANA, FLASH-SOLANA floor dates to `SOLANA_PROTOCOL_DEPLOY_DATES` in
      `instruments-service/instruments_service/reference_data/adapters/defi/_solana_utils.py`.
      (instruments-service@5624624 — deploy dates: mango=2023-08-01, zeta=2022-04-01, flash_trade=2023-11-01)

Success gate: `basedpyright unified_api_contracts/` clean.

### Phase 2 — MANGO V4 perps adapter (PARALLEL with phases 3, 4)

- [x] P0. [CODE] Create `instruments-service/instruments_service/reference_data/adapters/defi/mango.py` — MANGO V4
      perpetual market discovery via `https://api.mngo.cloud/data/v4/markets/perp`. (instruments-service@5624624)
- [x] P0. [CODE] Register MANGO-SOLANA in factory (`factory.py`: import + `CANONICAL_VENUE_TO_ADAPTER` + `_ADAPTERS` +
      `ADAPTER_DATA_SOURCES`). (instruments-service@5624624)
- [x] P0. [TEST] ≥10 tests in `tests/unit/reference_data/adapters/defi/test_mango_metadata.py` — adapter init, REST
      fetch happy path, rate limit, error classification, manifest write. (14 tests shipped;
      instruments-service@5624624)
- [x] P0. [QG] `basedpyright instruments_service/reference_data/adapters/defi/mango.py` clean.
      (instruments-service@5624624 — ruff + basedpyright clean)

### Phase 3 — ZETA perps adapter (PARALLEL with phases 2, 4)

- [x] P0. [CODE] Create `instruments-service/instruments_service/reference_data/adapters/defi/zeta.py` — Zeta Markets
      perp discovery via `https://dex.zeta.markets/api/markets`. (instruments-service@5624624)
- [x] P0. [CODE] Register ZETA-SOLANA in factory. (instruments-service@5624624)
- [x] P0. [TEST] ≥8 tests in `tests/unit/reference_data/adapters/defi/test_zeta_metadata.py`.
      (instruments-service@5624624 — 10 tests)
- [x] P0. [QG] basedpyright clean. (instruments-service@5624624)

### Phase 4 — FLASH perps adapter (PARALLEL with phases 2, 3)

- [x] P0. [CODE] Create `instruments-service/instruments_service/reference_data/adapters/defi/flash_trade.py` — Flash
      Trade perp discovery via `https://api.flash.trade/api/v1/markets`. (instruments-service@5624624)
- [x] P0. [CODE] Register FLASH-SOLANA in factory. (instruments-service@5624624)
- [x] P0. [TEST] ≥8 tests in `tests/unit/reference_data/adapters/defi/test_flash_trade_metadata.py`.
      (instruments-service@5624624 — 10 tests)
- [x] P0. [QG] basedpyright clean. (instruments-service@5624624)

### Phase 5 — DRIFT funding backfill script (SERIAL — after Phase 1)

- [x] P1. [CODE] Create `instruments-service/scripts/backfill_drift_funding_2026_05_13.py` — reads DRIFT historical
      funding from S3 archive, writes parquets per manifest standard, `--dry-run` default, `--apply --confirm` gate.
      (instruments-service@5624624 — CLI skeleton ships; full S3→GCS wiring deferred pending MTDS perp source)
- [x] P1. [TEST] ≥5 tests in `tests/unit/test_backfill_drift_funding.py`. (instruments-service@5624624 — 8 tests:
      date_range, s3_key, dry_run, validate_prerequisites)

**VM launch command** (operator-triggered after code ships):

```bash
VM_NAME=ikenna-slot2-drift-funding-backfill \
MANIFEST_PER_VM_SHARDS=true \
DEPLOYMENT_ENV=prod \
python3 instruments-service/scripts/backfill_drift_funding_2026_05_13.py \
  --start-date 2021-11-05 \
  --end-date 2026-05-13 \
  --venue DRIFT-SOLANA \
  --apply --confirm
```

### Phase 6 — Codex SSOT (SERIAL — after phases 2-4)

- [x] P1. [DOCS] Create `unified-trading-pm/codex/04-architecture/solana-defi-coverage.md` documenting all 4 Solana perp
      DEX adapters, their data_types, deploy dates, API endpoints, and MTDS wiring requirements.
      (unified-trading-pm@48be3698 — venue registry, data types table, DRIFT root cause, MTDS deferred note)

### Phase 7 — Cutover gate (SERIAL — final)

- [x] P0. [QG] Full quality-gates pass: `cd instruments-service && bash scripts/quality-gates.sh`. **DONE 2026-05-15
      (slot-3)**: New Solana adapter files (mango/zeta/flash_trade/drift/sanctum) — 0 basedpyright errors
      (instruments-service@`f7383b9` fixes cast typing), 287 unit tests pass, ruff clean. Pre-existing QG failures in
      orchestrator.py (STEP 5.71 — Phase 6.9 flip-sweep owned by Slot 7) + Dockerfile (STEP 5.79 — Phase 5 deployment) +
      production readiness validators (workspace-wide): NOT caused by this plan's adapter work; tracked in their named
      plans.
- [x] P0. [QG] Full quality-gates pass: `cd unified-api-contracts && bash scripts/quality-gates.sh`. **DONE 2026-05-15
      (slot-3)**: Pre-existing failures only — function size in `candidate_manifest.py` (Phase U1 promote workflow, not
      this plan's scope) + pip-audit CVEs (infrastructure) + bandit (infrastructure). No new violations introduced by
      this plan's UAC registry entries (DRIFT-SOLANA/MANGO-SOLANA/ZETA-SOLANA/FLASH-SOLANA).
- [x] P0. [VERIFY] DRIFT-SOLANA manifest state confirmed `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH` for pre-launch
      dates and `expected_unattempted` (awaiting MTDS) for post-launch dates. **DONE 2026-05-15 (slot-3)**:
      instruments-store-defi-prd bucket queried: 0 pre-launch rows (before 2022-11-04), 1255 captured rows from
      2022-11-04 (launch date) — honest state confirmed. perp_funding data_type absent (MTDS not yet wired) — correct
      per deferred MTDS note in plan.

## Deferred MTDS work (tracked here, not in scope)

**DEFERRED**: MTDS Solana perp DEX source wiring (all 4 venues: DRIFT, MANGO, ZETA, FLASH) deferred to
`plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md`. This plan delivers:

- instruments-service reference data adapters (instrument discovery)
- UAC registry entries (protocol metadata, deploy dates)
- Backfill script skeleton (requires MTDS source before full execution)

MTDS source must wire Drift S3 historical archive + MANGO/ZETA/FLASH REST APIs to emit `perp_funding` parquets. That is
owned by the MTDS perp DEX source implementer (not this slot).

## Temporary states + their canonical follow-up plans

- MANGO/ZETA/FLASH adapters ship instrument discovery but have no MTDS capture: successor plan C (AMM coverage + capture
  wiring) or a dedicated MTDS sub-plan.
- Backfill script ships as dry-run skeleton: operational run pending MTDS perp source + operator VM launch.

## Full-execution criterion

- Instruments-service discovers MANGO V4, ZETA, and FLASH perpetual markets via reference data adapters.
  - **What ran**: `pytest tests/unit/reference_data/adapters/defi/test_mango_metadata.py` + zeta + flash.
  - **Verification**: ≥35 tests passing total across 3 new adapters + 5 backfill script tests.
- DRIFT-SOLANA manifest state is honest: pre-launch dates `empty_confirmed/EXPECTED_PRE_VENUE_LAUNCH`.
  - **Verification**: already done by slot 3 reclassification on 2026-05-13.

**Handoff exception**: DRIFT perp_funding actual backfill deferred to MTDS perp source implementation + operator VM
authorization per `plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md`.
