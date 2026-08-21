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
- [x] [BACKEND] P1. ✅ Add or run testnet smoke coverage where credentials are available or provisionable and record an honest unavailable result for the remainder; file an operator credential request when a credential gap is confirmed. Gate: every attempted path has a measured terminal result. — Evidence: live per-venue smoke run in the Progress Log entry below; `execution-service@a5b248491d` (`scripts/run_cefi_testnet_connectivity_smoke.py`), `unified-api-contracts@b2f54822b3` (Aster dead-DNS registry fix found while running it).
- [x] [BACKEND] P1. ✅ Track every failed or absent CeFi row with its source and data type; Gate: no failure is hidden behind a declared-absence or expected-unattempted status. — Evidence: `market-tick-data-service@27f4087273` (verified ancestor of `origin/live-defi-rollout`); see Progress Log entry below for the full reconciliation.
- [ ] [BACKEND] P2. Register `bitfinex`, `okx_swap`, and `coinbase_cde` as their own `SourceCapability` entries in `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_cefi.py` (domains/operations/base_urls derived from the real adapters, e.g. `bitfinex_native.py` for Bitfinex — not fabricated); `supports_testnet` per the 2026-08-21 verdict table below (Bitfinex: False; OKX-SWAP: True, same demo-trading infra as `okx`; Coinbase-CDE: True, certification/UAT environment provisioned on request, not self-serve). (repo: unified-api-contracts)
- [x] [BACKEND] P0. ✅ Verified source-scoped exemptions and canonical oracle/manifest checks with negative controls. UAC `03c79c82` resolves source per `(venue, data_type)` and excludes only source-first Databento cells; its quality-gate tests passed. MTDS `f90bf09a` routes CEFI/DEFI object paths through `canonical_path_violations(..., require_pipeline_mode=True)` and its tests reject missing `pipeline_mode`, raw wire-symbol filenames, and missing captures. — Evidence: `unified-api-contracts` QG `tests` slice passed; `market-tick-data-service` QG `tests` slice passed (`11113 passed, 28 skipped, 1 xpassed`).

## Progress Log

**2026-08-21 — slot 4 reconciliation flip (todo #4, failed/absent row tracking + anti-hiding gate).**
Verified — did not re-run the smoke driver — that this todo's underlying work was already shipped by a
peer session against the sibling blocker issue
[/plans/active/issues/cefi_venue_smoke_batch1_missing_catalog_and_driver_teardown_2026_08_20.md]'s matching P1 todo,
whose wording ("classify every `no_captured_data_for_cell`/`tardis_guard_busy` result against the production source
listing... no row may remain represented only by a skipped aggregate result") is the same work this plan's todo
names. Verification performed this session (not trusted from the issue doc's own copy of the evidence):
- `market-tick-data-service@27f4087273` confirmed a live ancestor of `origin/live-defi-rollout` via
  `git merge-base --is-ancestor`, and its diff read in full: it adds
  `market_tick_data_service/scripts/classify_cefi_skips_against_source_listing_2026_08_21.py` +
  `tests/unit/scripts/test_classify_cefi_skips_against_source_listing_2026_08_21.py`.
- The script's `classify_pair()` checks every (venue, data_type) pair behind a `no_captured_data_for_cell`/
  `tardis_guard_busy` row against the vendor's REAL production listing (Tardis's public
  `GET /v1/exchanges/{exchange}` dataset-types, or the on-chain-perp launcher's fixed
  trades/book_snapshot_5/derivative_ticker triple for the 5 native-REST venues) — never guesses: a fetch failure or
  unmapped venue/data_type resolves `unresolved_source_check`, not a fabricated verdict. 87 distinct pairs classified:
  31 `confirmed_absent_at_source`, 45 `confirmed_available_needs_capture` (real gaps, left untouched — not converted
  to a declared absence), 11 `unresolved_source_check`.
- `apply_reclass()` is the gate this todo names: it only ever moves a pair's PROD manifest `attempted_failed` rows to
  `empty_confirmed/EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE` when that pair is in the confirmed-absent set, gated on a
  row-count-preserving / captured-count-invariant / delta-consistent check (`gate_ok`) computed via DuckDB
  out-of-core (never a full-frame pandas decode of the ~30.8M-row PROD manifest). Unit tests
  (`test_apply_reclass_dry_run_computes_gate_without_writing`,
  `test_apply_reclass_apply_writes_snapshot_and_reclassed_manifest`) prove both the dry-run gate math and that an
  untouched (non-absent) pair's `attempted_failed` row survives a real apply run unchanged. The issue doc's own
  Progress Log records the live `--apply` result against the PROD cefi manifest: `gate_ok=true`, `reclassed=0`,
  `applied=false` — none of the 31 confirmed-absent pairs currently sit in `attempted_failed`, i.e. no failure is
  presently hidden behind a declared absence for the classified pairs.
- Independently checked (not assumed) whether this todo's Gate also needs to cover the OTHER failure reasons seen in
  the terminal reports above (`canonical_no_matching_objects_in_test_bucket`, `vm_self_deleted_no_exit_status`,
  `no_parquet_under`): read `market-tick-data-service/scripts/pipeline_e2e_check.py` directly. These are
  driver-report-level diagnostic strings explaining why the SMOKE CHECK itself failed (canonical path mismatch, VM
  teardown, no object under the test-bucket prefix) — the driver only READS manifest `capture_status` (via
  `read_prod_capture_status`/`verify_manifest_row`) to decide its own pass/fail/skip verdict, it never writes it, so
  these reasons cannot themselves cause a manifest-level hide-behind-absence. The driver already carries a general
  "honest-empty pass" branch (`pipeline_e2e_check.py` ~line 1888): a manifest row that is genuinely
  `empty_confirmed[EXPECTED_*]` is treated as PASS, while an unexplained zero-row result (`SOURCE_RETURNED_ZERO`)
  deliberately stays FAIL for force legs — the exact anti-hiding behavior this todo's Gate requires, already
  structural for every data_type/reason, not just the classified subset.
- Every failed/absent row remains traceable to its `data_type` (the driver's `shard_label` is
  `asset_group:venue:data_type`) and its source: either the manifest's own `source` column (schema v9,
  write-stamped by the capturing adapter) for rows that were actually attempted, or the classify script's
  `verdict.detail` naming the checked vendor/listing for the 87 skip-reason pairs.

Scope note for the next reader: the 45 `confirmed_available_needs_capture` pairs and the 3 venues still
`unresolved_source_check` are real open follow-up, already tracked as their own todos in the linked issue doc — not
duplicated here, per this doc's `related:` cross-reference.

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

### 2026-08-21 — slot 21 live testnet connectivity smoke (todo #3)

Shipped `execution-service/scripts/run_cefi_testnet_connectivity_smoke.py` (permanent,
re-runnable) and ran it live against the 17-venue denominator the prior verdict table above
already settled — one credential-free HTTP request per venue, honest two-tier verdict so a
wrong endpoint guess degrades to "unconfirmed" rather than a false negative. Full JSON
evidence + stdout captured this session (not committed — a live network snapshot, not
canonical data). Result: **15/16 attempted venues `host_reachable_endpoint_ok`** (2xx from
the specific well-known public endpoint) — BINANCE-FUTURES, BINANCE-SPOT, BITGET-FUTURES,
BITGET-SPOT, BYBIT, BYBIT-SPOT, COINBASE-FUTURES, COINBASE-SPOT, DERIBIT, EXTENDED-STARKNET,
HYPERLIQUID, KRAKEN-FUTURES, OKX-FUTURES, OKX-SPOT, OKX-SWAP. **1/16 `host_unreachable`**:
ASTER — the UAC-declared testnet host `testnet-api.aster.finance` is dead DNS (confirmed via
independent `getent`/`curl` checks, not transient); found the real, already-shipped execution
adapter uses `fapi.asterdex.com` instead and never referenced `aster.finance`. Fixed the
evidenced mainnet URL in the same session (`unified-api-contracts@b2f54822b3`, `_cefi.py` +
`endpoints.py`); no verified testnet host was found for Aster, tracked as open follow-up in
[/plans/active/issues/aster_testnet_endpoint_unresolved_2026_08_21.md]. Two BITGET rows and
three OKX rows share their mainnet domain (demo trading is account/header-scoped, not
URL-scoped) — their `host_reachable_endpoint_ok` result proves shared-domain reachability
only, called out explicitly in the script rather than silently equated with a testnet-distinct
signal. COINBASE-CDE recorded as `credential_required_no_endpoint` (no live attempt — no UAC
declaration and no publicly known base_url exist to attempt); operator credential/access
request filed at
[/plans/active/issues/coinbase_cde_testnet_credential_ask_2026_08_21.md]. The 7 simulate-only
venues (BITFINEX-FUTURES, BITFINEX-SPOT, KALSHI-PERP, KRAKEN-SPOT, LIGHTER-ZKSYNC,
PACIFICA-SOLANA, POLYMARKET-PERP) recorded as `not_applicable_simulated` per the already-settled
prior verdict, no attempt made (structural absence, not a gap). Every one of the 24 venues now
has a measured terminal result — the gate this todo names. Full quality gates passed both repos
(unified-api-contracts 314s, execution-service 363s); both SHAs verified ancestors of
`origin/live-defi-rollout` via `git merge-base --is-ancestor`.
