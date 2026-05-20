---
name: canary_coverage_qg_enforcement_2026_05_20
locked_by: live-defi-rollout
locked_since: 2026-05-20
priority: P0
status: open
target_slot: multi-slot-fanout
estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6.4
deadline: 2026-05-23
deadline_change_reason: "Operator pulled deadline 2026-05-20 from June-4 to May-23: 140 prod blind spots are inside live-DeFi cutover gate per Data Pipeline Correctness HARD RULE. Heavy slot fan-out required (~7 cal AI-days into 3 cal days = ~2.3x parallelism)."
slot_allocation:
  - "slot 1 main (Phase 1: assertions + 3 QG STEPs + canary CI wire-in)"
  - "slot 2 (Phase 3 DeFi cassettes: Aave/Compound/Spark/Euler/Venus/Curve cluster ~6 protocols)"
  - "slot 3 (Phase 3 DeFi cassettes: LST cluster Lido/RocketPool/cbETH/JitoSOL/mSOL/Jito/Marinade/Sanctum ~8 protocols)"
  - "slot 4 (Phase 3 DeFi cassettes: yield/restaking cluster Ethena/Puffer/EtherFi/Pendle/Morpho/Beefy/Yearn/Convex/Karak/Solayer/Solblaze/Cambrian/Symbiotic/Idle/Picasso/Sky ~16 protocols)"
  - "slot 5 (Phase 3 DEX cassettes: Uniswap/Curve/Balancer/Sushi/PancakeSwap/Phoenix/Orca/Raydium/Drift/Lifinity ~10 venues)"
  - "slot 6 (Phase 3 CeFi blind + Sports/Execution cassettes: kraken-spot/futures/pacifica/extended + sportsbook scrapers + Copper/Tenderly/Socket/CCTP ~25 cassettes)"
  - "slot 7 (Phase 4 WS recorder + 19 WS cassettes via MTDS scripts/record_ws_cassettes.py)"
  - "slot 8 (Phase 5 orphan decisions + validate_schemas.py WS-handling + Phase 2 STEP wiring)"
operator_directive: "Headline gap from the orphan-check audit should ALL be fixed — no deferrals (per Data Pipeline Correctness HARD RULE)."
no_deferral_scope:
  - "Every cassette that has zero production consumer: either wire it to a consumer or delete it (no orphans)"
  - "Every production HTTP/WS host: must have a cassette + entry in capability declarations (no blind spots)"
  - "Every venue with both batch + live adapters: must have BOTH a batch cassette and a WS cassette"
  - "Every QG STEP wiring change: must be in scripts/quality-gates.sh (not informational tests)"
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

## Operator directive (2026-05-20)

> "Headline gap from the orphan-check audit shoudl all be fixed"
> "enforcemnet for caanary coverage shodl be enforced codcumented in pan etc"

Per CLAUDE.md "Data Pipeline Correctness Is The Heartbeat — No Exceptions, No Cutbacks (HARD RULE — codified 2026-05-20)":
**every** missing cassette is recorded, **every** orphan is resolved, **every** WS connector gets a frame cassette, **every** batch source is paired with its live equivalent. No "we'll skip this for the deadline." No "most cells captured, backfill rest later." Only legitimate deferral path is `BLOCKED-CREDENTIALS` (operator-acked) — and only for the SPECIFIC venue × endpoint blocked, not the whole class.

The plan reviewer SHALL reject any partial-scope PR claiming this plan is "done with the rest deferred." Status field stays `in_progress` until **every** cell is either captured or operator-acked `BLOCKED-*`.



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

### Phase 3 — Record missing cassettes for ALL ~140 prod hosts (~3 days, NO DEFERRALS)

Per operator directive "Headline gap should ALL be fixed" — every prod-host blind spot is in-scope. ~140 unique
hosts surfaced by audit; below grouped by track. PARTIAL COMPLETION REJECTED — status stays `in_progress` until
**every** entry has either a cassette OR an operator-acked `BLOCKED-CREDENTIALS` ping.

**DeFi `carry_staked_basis`** (~28 protocols):

- [ ] [SCRIPT] P1. REST cassette per: Aave, Compound, Spark, Euler, Venus, Curve, Lido (stETH), RocketPool (rETH),
      Coinbase cbETH, JitoSOL, mSOL (Marinade), Jito, Sanctum, Ethena (USDe/sUSDe), Puffer, EtherFi (eETH/weETH),
      Pendle, Morpho, Beefy, Yearn, Convex, Karak, Solayer, Solblaze, Cambrian, Symbiotic, Idle, Picasso, Sky.
      For protocols with only on-chain reads (no REST): document with `<protocol>/mocks/onchain_<call>.yaml`
      capturing the canonical contract call + decoded response.

**DeFi `arbitrage_price_dispersion`** (~9 DEXes):

- [ ] [SCRIPT] P1. REST/GraphQL cassette per: Uniswap V3, Curve (pools), Balancer, Sushi, PancakeSwap (via thegraph),
      Phoenix, Orca, Raydium, Drift, Lifinity (Solana).

**CeFi venues lacking cassette**:

- [ ] [SCRIPT] P1. REST cassette per: kraken-spot, kraken-futures (in CLAUDE.md perp-funding list), pacifica,
      extended (api.starknet.extended.exchange — Cayman venue).

**Sports / Prediction**:

- [ ] [SCRIPT] P1. Polymarket sports markets cassettes (see [[polymarket]] follow-up — sports-tag endpoint must be
      live-recorded, not hand-crafted).
- [ ] [SCRIPT] P1. Sportsbooks scraped via execution-service (1xbet, bet365, betvictor, 888sport, bwin, boylesports,
      coral, ladbrokes, paddypower, sbobet, skybet, unibet, williamhill, betway) — record at least one cassette per
      scraper to detect HTML structure drift.
- [ ] [SCRIPT] P1. `api.oddspapi.io` (e2e-testing/scripts/sports/oddspapi_historical_backfill.py).

**Execution / infra**:

- [ ] [SCRIPT] P1. Copper (`api.copper.co`, `api.sandbox.copper.co`), Tenderly (`api.tenderly.co`), Socket
      (`api.socket.tech`), Circle CCTP (`iris-api.circle.com`) — at least 1 read-only endpoint cassette each.

### Phase 4 — WS cassettes for the 19+ missing live connectors (~1.5 days, NO DEFERRALS)

The "Batch = Live" SSOT (CLAUDE.md CRITICAL) requires identical schemas batch vs live. Without WS frame cassettes
the canary cannot detect when a venue silently renames a WS field — the highest-frequency drift mode for
trade-frames. **No deferrals; every connector gets a cassette.**

- [ ] [SCRIPT] P1. Build `MTDS scripts/record_ws_cassettes.py` helper that subscribes to each WS connector,
      records the first 3 frames per channel/type, writes YAML to
      `unified-api-contracts/external/<venue>/mocks/<channel>_ws.yaml`.
- [ ] [SCRIPT] P1. Record WS cassettes for ALL connectors in `market-tick-data-service/market_tick_data_service/live/connectors/`:
      binance-spot, binance-futures, bybit-spot, bybit-futures, coinbase-spot, deribit, hyperliquid-info,
      hyperliquid-exchange, aster-futures, kalshi (post-URL-migration), kraken-spot, kraken-futures,
      databento-tradfi-live, polymarket-clob, upbit, and any others discovered during recording. One frame per
      subscription channel (trade / orderbook / ticker / funding etc.).
- [ ] [SCRIPT] P1. Update `unified-api-contracts/scripts/validate_schemas.py` to handle WS cassettes — separate
      replay path that connects, samples first N frames, structurally diffs.
- [ ] [SCRIPT] P1. New `STEP 5.7X batch_live_cassette_coexistence.sh` (Phase 2) enforces no missing WS cassette
      for any venue with a `live/connectors/<venue>_ws.py`. Once Phase 4 lands, this STEP guards regression.

### Phase 5 — Resolve all 25% prod-orphan cassettes (~0.5 day, NO DEFERRALS)

For each prod-orphan cassette (from 2026-05-20 audit list): WIRE-TO-CONSUMER or DELETE-CASSETTE. Document each
decision in `unified-api-contracts/scripts/canary/orphan-decisions.yaml`. The orphan-check STEP (Phase 2) then
asserts zero orphans = zero post-decision-log entries needing action.

- [ ] [SCRIPT] P1. Decide + execute per orphan: `gateio`, `mexc`, `bitstamp`, `huobi` venues (full-orphan), and
      per-cassette orphans in `alchemy/aave_get_reserve_data`, `alchemy/aave_get_user_account_data`,
      `barchart/get_quote_es1`, `databento/batch_*` (3 cassettes), `databento/timeseries_get_range_*` (2),
      `open_meteo/forecast_current_weather`, `tardis/datasets_csv_download`, `tardis/datasets_warmup`,
      `yahoo_finance/earnings_msft`.

### Phase 5 — Wire canary into per-PR CI (~0.5 day)

- [ ] [SCRIPT] P2. Add `canary_offline_check` step to UAC `quality-gates.sh`: cassette YAML parse + schema-validate
      against cassette baseline (no live network call). This catches cassette corruption / schema-cassette mismatch on
      every PR, not just weekly.
- [ ] [SCRIPT] P2. Optional weekly-validation also runs on every push to `live-defi-rollout` (matrix-build with
      schedule-trigger guarded so it doesn't fire 20× per day).

## Success criteria — NO PARTIAL COMPLETION

- All 3 new QG STEPs (`cassette_prod_consumer_linkage.sh`, `prod_url_has_cassette.sh`,
  `batch_live_cassette_coexistence.sh`) are wired into UAC `quality-gates.sh` + green on tab branch
- `tests/test_cassette_orphan_checker.py` asserts `len(orphans) == 0` (currently informational)
- Every ~140 prod HTTP/WS host has either a cassette OR an operator-acked `BLOCKED-CREDENTIALS` ping
- Every live WS connector in MTDS has at least 1 frame cassette
- Every prod-orphan cassette has a recorded decision (wire-or-delete) in `orphan-decisions.yaml` AND
  the corresponding action has been executed
- Weekly canary surface count: 140+ cassettes (vs current 91)
- Per CLAUDE.md "Data Pipeline Correctness Is The Heartbeat" — every cell in scope, no exceptions
- `canary_offline_check` runs on every PR to `live-defi-rollout`
- Per CLAUDE.md "Data Pipeline Correctness Is The Heartbeat" — no cells silently missing

## Cross-references

- Audit surfaced this gap: 2026-05-20 orphan-check sub-agent (run during defunct-dirs-cleanup session)
- Canary shipped: `unified-api-contracts@18c74a56` + `@a408925c`
- Companion plan: [[kalshi_api_migration_to_elections_subdomain_2026_05_20]] (the canary already caught this)
- Composes with the HARD RULE: CLAUDE.md "Data Pipeline Correctness Is The Heartbeat"
- Composes with foundation-completion-gate discipline: any layer-N+1 PR that touches a venue with NO cassette is
  layer-N+1 work on an unaudited foundation, review-blocking.
