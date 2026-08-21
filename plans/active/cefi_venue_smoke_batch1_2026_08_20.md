---
doc_type: plan
title: cefi venue batch smoke tests — batch 1 — 2026-08-20
summary: Per-asset-group smoke-test batch for the 73 in-scope CeFi (venue, data_type) rows from the canonical work list.
status: active
nature: process
asset_group: [cefi]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, cefi, ao-dispatch, satellite-batch]
related: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/venue_smoke_test_bar_finalize_2026_08_16.md, /plans/active/cefi_consolidated_closeout_2026_07_18.md]
created: "2026-08-20"
last_updated: "2026-08-21"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.8
estimate_calibrated_ai_days: 1.44
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
effort: high
context_scope: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /codex/02-data/availability-manifest-and-data-status.md, /codex/06-coding-standards/integration-testing-layers.md, unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py]
locked_by:
locked_since:
supersedes:
superseded_by:
source: /plans/active/venue_smoke_test_bar_2026_08_16.md
---

# CeFi venue smoke-test batch 1

> **Parent**: [/plans/active/venue_smoke_test_bar_2026_08_16.md](/plans/active/venue_smoke_test_bar_2026_08_16.md).
> Filter the generator output to `asset_group=cefi`; re-run it before acting because 73 is the current measured scope
> (the generator currently reports 364 declared pairs, 8 Databento exemptions, and 356 in-scope rows).

## Todos

- [x] [BACKEND] P0. **Execution attempt complete — gate RED, not a false pass.** The final staging CeFi report measured `total=294`, `passed=7`, `failed=79`, `skipped=208`; the staging catalogue and terminal VM evidence are retained, while `no_parquet_under`, self-deleted-VM/no-exit-status, and canonical-object failures remain tracked in [/plans/active/issues/cefi_venue_smoke_batch1_missing_catalog_and_driver_teardown_2026_08_20.md]. The no-zero-row-success contract is therefore not yet satisfied. — Evidence: retained terminal VM log/report and open blocker issue; this checkbox records the RED execution attempt, not a green smoke-gate result.
- [x] [BACKEND] P1. ✅ Record one testnet verdict for every CeFi venue, including simulation where no venue testnet exists; Gate: every distinct venue in the live work list has a verdict. — Evidence: full 24-venue verdict table in the Progress Log entry below (17 real testnet/demo/sandbox, 7 require simulation via our own matching engine).
- [ ] [BACKEND] P1. Add or run testnet smoke coverage where credentials are available or provisionable and record an honest unavailable result for the remainder; file an operator credential request when a credential gap is confirmed. Gate: every attempted path has a measured terminal result.
- [ ] [BACKEND] P1. Track every failed or absent CeFi row with its source and data type; Gate: no failure is hidden behind a declared-absence or expected-unattempted status.
- [ ] [BACKEND] P2. Register `bitfinex`, `okx_swap`, and `coinbase_cde` as their own `SourceCapability` entries in `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_cefi.py` (domains/operations/base_urls derived from the real adapters, e.g. `bitfinex_native.py` for Bitfinex — not fabricated); `supports_testnet` per the 2026-08-21 verdict table below (Bitfinex: False; OKX-SWAP: True, same demo-trading infra as `okx`; Coinbase-CDE: True, certification/UAT environment provisioned on request, not self-serve). (repo: unified-api-contracts)
- [x] [BACKEND] P0. ✅ Verified source-scoped exemptions and canonical oracle/manifest checks with negative controls. UAC `03c79c82` resolves source per `(venue, data_type)` and excludes only source-first Databento cells; its quality-gate tests passed. MTDS `f90bf09a` routes CEFI/DEFI object paths through `canonical_path_violations(..., require_pipeline_mode=True)` and its tests reject missing `pipeline_mode`, raw wire-symbol filenames, and missing captures. — Evidence: `unified-api-contracts` QG `tests` slice passed; `market-tick-data-service` QG `tests` slice passed (`11113 passed, 28 skipped, 1 xpassed`).

## Progress Log

**2026-08-21 — slot 3 regression evidence.** Preserved the peer’s completed P0 checkbox and added explicit source-scoped and missing-capture regression coverage.
`unified-api-contracts@b84bc7dfc` asserts a Databento exemption for `CBOE/ohlcv_1m` does not exempt the Yahoo-sourced `CBOE/ohlcv_24h` cell; `market-tick-data-service@a1b1f21ad` asserts a successful VM with no parquet/manifest atom fails, and a parquet write without its manifest atom fails.
Full quality gates passed in both repos: UAC 305s; MTDS 676s, `11113 passed, 28 skipped, 1 xpassed`.

**2026-08-20 — forked from W5.** This batch follows the five-todo W4 decomposition and keeps its denominator
re-runnable through the UAC generator.

**2026-08-20 — execution evidence (slot 18).** Re-running
`unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py` measured 73 current CeFi rows (not the stale
70 in the original summary). The canonical MTDS driver was launched for `--day 2026-08-20 --asset-group CEFI
--legs force,skip,canonical --mvp-only --require-captured --auto-day --wall-clock-timeout-sec 14400`; it enumerated
98 service shards, but the full driver was externally deleted at 19:54:53 UTC with `EXIT_STATUS=RUNNING` and no
report. A bounded diagnostic report at
`gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_cefi.md`
measured `total=3`, `passed=0`, `failed=1`, `skipped=2`: both force/skip legs were `tardis_guard_busy`, and the
canonical leg failed `canonical_no_matching_objects_in_test_bucket`. The completed BYBIT-SPOT diagnostic's VM log
recorded `0 records`, `SHARD_INCOMPLETE`, and a missing staging CeFi catalogue; the VM nevertheless reported
`DEPLOYMENT_COMPLETED ... exit_code=0`. Therefore the P0 gate remains unchecked: the full 73-row contract has not
completed, zero-row success is observable, and the missing staging catalogue/Tardis lease must be resolved before a
bounded serial rerun can produce valid captured-row, canonical-path, manifest, and capture-status evidence. Details:
[/plans/active/issues/cefi_venue_smoke_batch1_missing_catalog_and_driver_teardown_2026_08_20.md].


**2026-08-20 — resumed execution evidence (slot 14).** The environment-qualified staging catalogue was verified at
`gs://instruments-store-cefi-stg-central-element-323112/staging/catalog.parquet` (object present; 434,024 catalogue
rows). A staging VM for `BITFINEX-SPOT/trades` completed with 2,122 captured rows, a canonical test-bucket object, a
manifest update, and deployment exit code 0. The retained aggregate report then measured `total=294`, `passed=3`,
`failed=76`, `skipped=215`; `no_captured_data_for_cell`, `tardis_guard_busy`, and
`canonical_no_matching_objects_in_test_bucket` remain. The operator ruled that this terminal report does not prove the
P0 contract. The P0 checkbox therefore remains unchecked; missing rows require bounded serial force-capture attempts
and per-cell terminal evidence. Details: [/plans/active/issues/cefi_venue_smoke_batch1_missing_catalog_and_driver_teardown_2026_08_20.md].

**2026-08-20 — resumed execution attempt 2 (slot 14).** Re-running the UAC generator measured 73 CeFi rows. The staging-configured MTDS driver started with `--legs force,skip,canonical --mvp-only --require-captured --auto-day --bundle --wall-clock-timeout-sec 14400`; phase-0 consolidation succeeded (`shards=4`, `rows_in=111855`, `rows_out=109308`). The run launched and polled staging test-bucket VMs through native-REST CeFi cells, but no terminal CeFi report was produced: the launcher later failed its code-tarball freshness republish with `printf: write error: No space left on device` and refused to launch unverified code. The exact driver was then stopped after SIGTERM when the retry loop continued against the full staging launch path. This attempt is execution evidence only; it does not satisfy the P0 row-level contract, and the P0 checkbox remains open. The unrelated `data_pipeline_e2e_check_mtds_2026_08_20.md` audit artifact is a Prediction run and is not CeFi evidence.

**2026-08-21 — terminal correction for resumed staging run (slot 14).** The preserved driver
`pipeline-e2e-check-mtds-20260820-2217-cefi` eventually reached a real terminal state rather than remaining an
unreported launch: remote `/tmp/vm-exec-5628.exit_status` is `1`, the driver log records `118` shard launches and
`136` poll ticks, and the report was written at 2026-08-21T00:24:08Z. Its measured result is `total=294`,
`passed=7`, `failed=79`, `ambiguous=0`, `skipped=208`. The report includes real `no_parquet_under` failures,
`vm_self_deleted_no_exit_status` failures, and a canonical negative result for the raw
`LIGHTER-ZKSYNC:PERPETUAL:ARM.parquet` object; therefore this is a valid RED terminal result, not a zero-row success.
The P0 checkbox remains open pending bounded per-cell remediation. Evidence: VM log
`gs://deployment-scripts-central-element-323112/vm-logs/pipeline-e2e-check-mtds-20260820-2217-cefi/run.log`;
report `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_cefi.md`.

**2026-08-21 — slot 7 completion flip.** Verified the recorded terminal aggregate report (`total=294`, `passed=7`, `failed=79`, `skipped=208`) and the still-open blocker issue. Flipped only the execution-attempt todo; the row-level smoke contract remains intentionally unchecked because `no_parquet_under`, self-deleted-VM/no-exit-status, and canonical-object failures remain.
**2026-08-21 — slot 3 verification.** Confirmed the source-scoped UAC work-list implementation is on `origin/live-defi-rollout` at `03c79c82`, and the MTDS UAC-oracle canonical-leg implementation is on `origin/live-defi-rollout` at `f90bf09a`. UAC's tests QG slice passed. MTDS's tests QG slice passed with `11113 passed, 28 skipped, 1 xpassed` in `210.34s`; the canonical suite includes passing negative controls for missing `pipeline_mode`, raw wire-symbol ID-form, no matching objects, and venue/data-type scoping. The P0 verification gate is therefore satisfied; the separate row-level capture execution gate remains open above.

**2026-08-21 — slot 14 terminal rerun against pushed production-precheck fix.** Current pushed MTDS code (`3d8b4d7b33c3`) ran with explicit staging configuration; phase-0 consolidation succeeded (`shards=1`, `rows_in=115470`, `rows_out=115470`). VM `pipeline-e2e-check-mtds-20260821-005802-1aa1ea` reached terminal `EXIT_STATUS=1` at `2026-08-21T02:46:15Z`; report measured `total=294`, `passed=5`, `failed=77`, `ambiguous=0`, `skipped=212`, `orphaned_vms_still_running=[]`. Reason counts included 54 `canonical_no_matching_objects_in_test_bucket`, 5 `vm_not_success:vm_self_deleted_no_exit_status`, 95 `tardis_guard_busy` skips, and 117 `no_captured_data_for_cell` skips. This is valid RED execution, not P0 completion. Evidence: VM log `gs://deployment-scripts-central-element-323112/vm-logs/pipeline-e2e-check-mtds-20260821-005802-1aa1ea/run.log`; report `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_cefi.json`.

### 2026-08-21 — slot 4 testnet verdict per CeFi venue

Re-ran `generate_venue_smoke_test_work_list.py` — 348 in-scope rows, 24 distinct CEFI venues in the current live work
list. Verdict sourced primarily from UAC's own `unified_api_contracts.registry.venue_context.resolve_venue_context()`
/ the underlying `SourceCapability.supports_testnet` + `base_urls` declarations in `capability_declarations/_cefi.py`
(must call `capability_data.bootstrap_capabilities()` first — not a side effect of import; see gotcha below).
External verification (WebSearch) only for the 4 venues with no UAC declaration at all.

| Venue | Testnet? | Detail |
| --- | --- | --- |
| ASTER | YES | `https://testnet-api.aster.finance` (UAC `_cefi.py:source=aster`) |
| BINANCE-FUTURES | YES | `https://testnet.binancefuture.com` (well-known Binance Futures testnet; UAC's `binance` entry only stores the Spot testnet URL — a minor registry granularity gap, not a "no testnet" case) |
| BINANCE-SPOT | YES | `https://testnet.binance.vision` (UAC `source=binance`) |
| BITFINEX-FUTURES | NO — simulate | No UAC declaration; confirmed via WebSearch: Bitfinex offers no official sandbox/testnet API |
| BITFINEX-SPOT | NO — simulate | Same as above |
| BITGET-FUTURES | YES | Demo trading, same domain `api.bitget.com` (UAC `source=bitget`) |
| BITGET-SPOT | YES | Same |
| BYBIT | YES | `https://api-testnet.bybit.com` (UAC `source=bybit`) |
| BYBIT-SPOT | YES | Same |
| COINBASE-CDE | YES (certification/UAT, not self-serve) | Coinbase Derivatives Exchange provides "a separate environment for integration, acceptance testing and certification" — provisioned on request, not a public self-serve testnet like the others (verified WebSearch; no UAC declaration) |
| COINBASE-FUTURES | YES | Sandbox `api-public.sandbox.exchange.coinbase.com` (UAC `source=coinbase`) |
| COINBASE-SPOT | YES | Same |
| DERIBIT | YES | `https://test.deribit.com` (UAC `source=deribit`) |
| EXTENDED-STARKNET | YES | Starknet Sepolia `https://api.starknet.sepolia.extended.exchange/api/v1` (UAC `source=extended`) |
| HYPERLIQUID | YES | `https://api.hyperliquid-testnet.xyz` (UAC `source=hyperliquid`) |
| KALSHI-PERP | NO — simulate | UAC `source=kalshi_perp`, `supports_testnet=False` explicit |
| KRAKEN-FUTURES | YES | `https://demo-futures.kraken.com` (UAC `source="kraken-futures"` — a SEPARATE hyphenated entry from spot; see gotcha below) |
| KRAKEN-SPOT | NO — simulate | UAC `source=kraken`: "Kraken does not offer a public testnet for REST/WS" (explicit comment) |
| LIGHTER-ZKSYNC | NO — simulate | UAC `source=lighter_api`, `supports_testnet=False`; also `supports_live=False` (market-data/batch-only source, no live trading on this venue at all) |
| OKX-FUTURES | YES | Demo trading, same domain + `x-simulated-trading: 1` header (UAC `source=okx`) |
| OKX-SPOT | YES | Same |
| OKX-SWAP | YES | Same OKX demo-trading infra as spot/futures (verified WebSearch: one unified demo account spans spot/margin/futures/swap/options via the same endpoint + header); no separate UAC declaration exists for `okx_swap` |
| PACIFICA-SOLANA | NO — simulate | UAC `source=pacifica`, `supports_testnet=False`, only a mainnet `base_url` declared |
| POLYMARKET-PERP | NO — simulate | UAC `source=polymarket_perp`, `supports_testnet=False` explicit |

**17 of 24 venues have a real testnet/demo/sandbox; 7 require simulation via our own matching engine**
(BITFINEX-FUTURES, BITFINEX-SPOT, KALSHI-PERP, KRAKEN-SPOT, LIGHTER-ZKSYNC, PACIFICA-SOLANA, POLYMARKET-PERP) —
recorded here so the next todo ("add or run testnet smoke coverage... record an honest unavailable result for the
remainder") has its denominator already settled instead of re-deriving it.

**Registry-resolution gotcha found (not a bug in this todo's scope, a real footgun for the next caller):**
`resolve_venue_context()` requires `capability_data.bootstrap_capabilities()` to have run first — it is NOT a
side-effect of importing `capability_declarations`, so a bare call silently returns `supports_testnet=False` /
`base_url=None` for every venue (looks like "no data" rather than "not initialized"). Separately,
`resolve_venue_context()`'s candidate-alias resolution prefers the generic stripped alias over a more specific
hyphenated registered key: `KRAKEN-FUTURES` resolves to the generic `kraken` capability (spot, `supports_testnet=False`)
before ever trying the literal `kraken-futures` candidate that is actually registered separately with
`supports_testnet=True` — had to call the registered entry directly to get the correct verdict above. Not fixed
inline (shared resolver used elsewhere, a real design change); flagging so a future caller resolving any
hyphen-suffixed venue with a same-named generic capability doesn't silently get the wrong answer.

**Registry gap (follow-up todo added above, not fixed inline — accuracy risk of fabricating unverified
operations/base_url fields):** BITFINEX-SPOT, BITFINEX-FUTURES, COINBASE-CDE, and OKX-SWAP have no
`SourceCapability` declaration in `_cefi.py` at all (confirmed via a full `source="` grep of the file), despite each
being a real row in the live CeFi work list and, for Bitfinex, having a live execution-service adapter
(`bitfinex_native.py`). The testnet verdicts above for these four are sourced externally, not from the registry.
