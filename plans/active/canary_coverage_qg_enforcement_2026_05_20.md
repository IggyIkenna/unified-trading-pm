---
name: canary_coverage_qg_enforcement_2026_05_20
locked_by: live-defi-rollout
locked_since: 2026-05-20
priority: P1
status: open
target_slot: ikenna-slot-1
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
deadline: 2026-06-04
parent_plan: master_to_live_defi_2026_05_23.md
parent_epic: data_correctness
related_plans:
  - defunct_uac_provider_dirs_cleanup_2026_05_20.md
  - kalshi_api_migration_to_elections_subdomain_2026_05_20.md
  - mega_audit_and_plan_beefup_progression_2026_05_20.md
codex_ssots:
  - codex/06-coding-standards/quality-gates.md
  - codex/02-data/contracts-scope-and-layout.md
  - codex/02-data/data-pipeline-correctness-hard-rule.md
---

# Canary coverage QG enforcement — close the 3 cassette↔prod blind spots

> **Surfaced 2026-05-20** by orphan-check audit during weekly-validation canary shipping. The headline gap from the
> audit: "the canary is documentation, not a gate." Three compounding blind spots: ~50% of live adapters have NO
> cassette (incl. every May-23 DeFi protocol), ~25% of cassettes are PROD-ORPHANS (canary green on endpoints prod
> doesn't read), and the cassettes that exist are almost entirely REST GETs while production live ticks come from 20
> WebSocket connectors with 1 WS cassette between them. **The "Batch = Live" SSOT (CLAUDE.md CRITICAL section) is
> unenforced at the canary layer.**

## Why this plan exists

Per CLAUDE.md "Data Pipeline Correctness Is The Heartbeat — No Exceptions, No Cutbacks (HARD RULE — codified
2026-05-20)":

> Every issue is fixed in full — every missing venue × data_type × time range backfilled, every silent empty diagnosed,
> every schema-version row migrated, **every batch adapter paired with a live equivalent.**

The canary as shipped 2026-05-20 (`unified-api-contracts@18c74a56` + `@a408925c`) walks 91 cassettes (~57 venues) and
structurally diffs them against live API responses. But it has zero teeth: no QG step enforces that cassettes correspond
to actual production code paths, no QG step asserts that production HTTP/WebSocket call-sites have cassette coverage,
and no QG step enforces batch-cassette ↔ live-WS-cassette coexistence for venues that support both.

## Audit-confirmed blind spots (numbers from 2026-05-20 orphan-check)

| Category                                                            | Count                     | Example                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------------------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cassettes with ZERO production consumers                            | ~16 of 65 non-stub (~25%) | `gateio`, `mexc`, `bitstamp`, `huobi`, `hyblock` full venues + per-cassette orphans in `alchemy/aave_*`, `databento/batch_*`, `tardis/datasets_*`, `yahoo_finance/earnings_*`                                                                                                                                                                                                                                                                                                                                                       |
| Production HTTP hosts WITHOUT cassettes                             | ~140 unique hosts         | **DeFi (P0 May-23)**: aave-api-v2.aave.com, api-v3.balancer.fi, api.beefy.finance, app.compound.finance, app.spark.fi, app.euler.finance, app.venus.io, api.curve.finance, api-v2.pendle.finance, blue-api.morpho.org, karak.network, app.solayer.org, solblaze.org, lifinity.io, lido.fi, rocketpool.net, marinade.finance, jito.network, restaking.jito.network, ethena.fi, puffer.fi, ether.fi, picasso.network, sanctum.so, symbiotic.fi, yearn.fi, idle.finance, convexfinance.com, cambrian.network — **none have cassettes** |
| Production WebSocket connectors without WS cassettes                | 19 of 20                  | binance/bybit/coinbase/deribit/hyperliquid/aster/kalshi/kraken/databento_tradfi etc. — only `alchemy/alchemy_ws_eth_subscription.yaml` exists workspace-wide                                                                                                                                                                                                                                                                                                                                                                        |
| Venues with BOTH batch + live adapter but missing one cassette side | ~10                       | hyperliquid (REST ✓, WS ✗), kraken (neither), aster (neither), kalshi (REST ✓, WS ✗)                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `tests/test_cassette_orphan_checker.py` assertion strictness        | informational only        | `assert isinstance(orphans, list)` — does NOT assert zero orphans                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |

## Goals

1. Wire 3 new QG STEPs into `unified-api-contracts/scripts/quality-gates.sh` that turn the canary from documentation
   into an enforced gate.
2. Land minimal new cassettes for the May-23 critical-path DeFi protocols (so they CAN drift-fail rather than silently
   being missing).
3. Land WS cassettes for the 19 missing WebSocket connectors, enforcing the "Batch = Live" SSOT at the cassette layer.
4. Make `tests/test_cassette_orphan_checker.py` actually assert zero orphans (currently informational).
5. Wire the canary into per-PR CI for `live-defi-rollout` pushes (offline sub-step — cassette structural diff without
   live network calls).

## Phased execution

### Phase 1 — Strengthen existing assertions (~0.5 day)

- [ ] [SCRIPT] P1. Make `tests/test_cassette_orphan_checker.py::TestIntegrationOrphanCheck` assert `len(orphans) == 0`
      (currently `assert isinstance(orphans, list)` — informational only). Allowlist confirmed-OK orphans explicitly.
- [ ] [SCRIPT] P1. Move root-level cassette tests (`test_cassette_orphan_checker.py`, `test_cassette_schema_parity.py`,
      `test_batch_live_parity.py`) into UAC's QG pytest sweep — either set `PYTEST_UNIT_DIR="tests/"` in
      `scripts/quality-gates.sh` (features-service pattern) or relocate into `tests/unit/`.
- [ ] [SCRIPT] P1. Convert the existing `cassette_orphan_checker.py` to scan PRODUCTION paths (services), not test
      files. Current checker fails on test-file references — wrong target for the operator's question.

### Phase 2 — Three new QG STEPs (~1.5 days)

- [ ] [SCRIPT] P1. **STEP 5.7X `cassette_prod_consumer_linkage.sh`** — fail QG if a cassette in
      `external/<venue>/mocks/*.yaml` exists but no file in any service repo references either (a)
      `from     unified_api_contracts.<venue>` deep-path, (b) any pydantic class defined in `external/<venue>/*.py`, or
      (c) the cassette's URL host. Emit per-orphan line. Allowlist file at
      `scripts/quality-gates-allowlists/cassette-orphans.txt` for documented exceptions (test-only cassettes,
      capability-declaration-only cassettes).
- [ ] [SCRIPT] P1. **STEP 5.7X `prod_url_has_cassette.sh`** — scan production source for `https?://` and `wss?://`
      literals; fail if a referenced host has no `external/<host_to_venue>/mocks/` dir AND the venue isn't in an
      explicit `STUB-OK` allowlist. Allowlist for: `tenderly.co`, `copper.co` (operator-known no-cassette), internal
      `*-service` k8s names, etc.
- [ ] [SCRIPT] P1. **STEP 5.7X `batch_live_cassette_coexistence.sh`** — for any venue with BOTH a batch source
      registered in `_cefi.py`/`_tradfi.py`/`_defi.py` capability declarations AND a `live/connectors/<venue>_ws.py`
      file, require BOTH a REST cassette AND a WS cassette (one frame per data_type). Enforces "Batch = Live" at the
      cassette layer.

### Phase 3 — Record missing cassettes for May-23 critical-path DeFi (~2 days)

- [ ] [SCRIPT] P1. Audit + record 1 cassette per DeFi protocol used in the `carry_staked_basis` archetype: Aave,
      Compound, Spark, Euler, Venus, Curve, Lido, RocketPool, Coinbase cbETH, JitoSOL, mSOL, Jito, Marinade, Sanctum,
      Ethena, Puffer, EtherFi, Pendle, Morpho, Beefy, Yearn, Convex.
- [ ] [SCRIPT] P1. Audit + record 1 cassette per DEX used in `arbitrage_price_dispersion`: Uniswap V3, Curve, Balancer,
      Sushi, PancakeSwap (already via thegraph), Phoenix, Orca, Raydium, Drift.

### Phase 4 — WS cassettes for the 19 missing live connectors (~1 day, post-cutover OK)

- [ ] [SCRIPT] P2. Record 1 WS message cassette per live connector in MTDS: binance, bybit, coinbase, deribit,
      hyperliquid, aster, kalshi, kraken-spot, kraken-futures, databento-tradfi, polymarket-clob, gateio (if kept), and
      7 more. Use a recording mode in MTDS that emits the first 3 frames per subscription type to a YAML cassette in
      `external/<venue>/mocks/<channel>_ws.yaml`.
- [ ] [SCRIPT] P2. Update `validate_schemas.py` to handle WS cassettes (frames are JSON objects, not REST responses).

### Phase 5 — Wire canary into per-PR CI (~0.5 day)

- [ ] [SCRIPT] P2. Add `canary_offline_check` step to UAC `quality-gates.sh`: cassette YAML parse + schema-validate
      against cassette baseline (no live network call). This catches cassette corruption / schema-cassette mismatch on
      every PR, not just weekly.
- [ ] [SCRIPT] P2. Optional weekly-validation also runs on every push to `live-defi-rollout` (matrix-build with
      schedule-trigger guarded so it doesn't fire 20× per day).

## Success criteria

- All 3 new QG STEPs are wired into UAC `quality-gates.sh` + green on tab branch
- `tests/test_cassette_orphan_checker.py` asserts zero orphans (or 0 + N allowlisted)
- Every May-23 DeFi protocol in scope has at least 1 cassette in `external/<venue>/mocks/`
- Every live WS connector in MTDS has at least 1 frame cassette
- `canary_offline_check` runs on every PR to `live-defi-rollout`
- Per CLAUDE.md "Data Pipeline Correctness Is The Heartbeat" — no cells silently missing

## Cross-references

- Audit surfaced this gap: 2026-05-20 orphan-check sub-agent (run during defunct-dirs-cleanup session)
- Canary shipped: `unified-api-contracts@18c74a56` + `@a408925c`
- Companion plan: [[kalshi_api_migration_to_elections_subdomain_2026_05_20]] (the canary already caught this)
- Composes with the HARD RULE: CLAUDE.md "Data Pipeline Correctness Is The Heartbeat"
- Composes with foundation-completion-gate discipline: any layer-N+1 PR that touches a venue with NO cassette is
  layer-N+1 work on an unaudited foundation, review-blocking.
