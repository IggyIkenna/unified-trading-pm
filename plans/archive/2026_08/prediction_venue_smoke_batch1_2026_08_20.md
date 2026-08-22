---
doc_type: plan
title: prediction venue batch smoke tests — batch 1 — 2026-08-20
summary: Per-asset-group smoke-test batch for the 4 in-scope Prediction (venue, data_type) rows from the canonical work list.
status: complete
nature: process
asset_group: [prediction]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, prediction, ao-dispatch, satellite-batch]
related: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/venue_smoke_test_bar_finalize_2026_08_16.md, /plans/active/prediction_consolidated_closeout_2026_07_18.md]
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

# Prediction venue smoke-test batch 1

> **🗄️ ARCHIVED 2026-08-22 (slot 18, review) — all todos done, reconciled into the still-active W5 contract.** This
> batch's row/testnet-verdict findings are recorded durably in
> [`/plans/active/venue_smoke_test_bar_2026_08_16.md`](/plans/active/venue_smoke_test_bar_2026_08_16.md)'s
> 2026-08-22 (slot 18) Progress Log entry — read that doc for current state, not this archived copy.
> `superseded_by`: none (closed out, not superseded by a successor plan).

> **Parent**: [/plans/active/venue_smoke_test_bar_2026_08_16.md](/plans/active/venue_smoke_test_bar_2026_08_16.md).
> Filter the generator output to `asset_group=prediction`; the four-row count is re-measured at execution time.

## Todos

- [x] [BACKEND] P0. **Execution attempt complete — RED, not a false pass.** The canonical generator re-measured four current Prediction rows, and staging driver `pipeline-e2e-check-mtds-20260821-012839-18224b` completed with 12 leg cells: 1 passed, 7 failed, and 4 explicitly skipped. The green per-row gate remains open: both trades rows had zero parquet/capture proof, KALSHI canonical order-book had no matching rows, and the driver sampled a KALSHI instrument for the POLYMARKET trades row. Evidence: report `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_prediction.json`, finished `2026-08-21T01:47:07Z`; issue `/plans/archive/issues/prediction_smoke_checker_cross_venue_sampling_2026_08_21.md`.
- [x] [BACKEND] P1. ✅ Record one testnet verdict for every Prediction venue, including matching-engine simulation where that is the honest answer; Gate: every distinct venue has a written verdict. — Evidence: both declared Prediction venues (the complete `VENUE_TO_ASSET_GROUP["prediction"]` set — KALSHI, POLYMARKET) have a written, code-grounded verdict: KALSHI has a real, already-registered testnet with an open credential-provisioning gap (feeds todo #3 below, not a new finding); POLYMARKET has none and is already simulated via the adapter's own matching-engine-style fill simulation. Full table in the 2026-08-22 (slot 26) Progress Log entry below.
- [x] ✅ [BACKEND] P1. Add or run testnet smoke coverage for provisionable credentials and record an honest unavailable result for accounts that cannot be provisioned; file an operator credential request when a credential gap is confirmed. Gate: every attempted path has a measured terminal result. — Evidence: both attempted paths have a measured terminal result (KALSHI: HTTP 401 live-probe against demo-api.kalshi.co, 2026-08-09, recorded in `test_kalshi_adapter.py`; POLYMARKET: no testnet exists, `supports_testnet=False`, matching-engine simulation is the honest already-implemented answer — no credential to provision). KALSHI's credential gap is confirmed unprovisionable-from-session, so filed the operator credential request per `/codex/02-data/external-data-always-available-rule.md`: `BLK-3d8c3d9e` (`POST /api/slots/18/blocked`) + issue doc `/plans/active/issues/kalshi_demo_testnet_credential_request_2026_08_22.md`.
- [x] ✅ [BACKEND] P1. Track every failed or absent Prediction row with its source and data type; Gate: no expected-unattempted row is reported as captured. — market-tick-data-service@b7c523f16c.
- [x] ✅ [BACKEND] P0. Verify source-scoped exemptions, canonical checks, and manifest atom checks with a negative control; Gate: an invalid path or missing capture exits non-zero. — market-tick-data-service@e47d14527b.

## Progress Log

**2026-08-20 — forked from W5.** Prediction has its own small AG batch so its distinct market-data shape remains
visible while retaining W4's comparable five-todo structure.

- [x] ✅ [BACKEND] P0. Fix the cross-venue sampler, add the regression control, and rerun the exact four-row generator-scoped contract with force/skip/canonical, canonical-path, manifest-atom, and genuine `capture_status` evidence; Gate: every current row has a valid venue-scoped terminal result. — market-tick-data-service@4d45e5541a. Evidence: sampler regression shipped and full quality gates passed; terminal report `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_prediction.md` recorded total=12, passed=0, failed=8, ambiguous=0, skipped=4 across exactly POLYMARKET/KALSHI × trades/book_snapshot_5. Driver `pipeline-e2e-check-mtds-20260821-prediction-4d45e5` reached `EXIT_STATUS=1`; all rows had terminal force/skip/canonical results, with book_snapshot_5 force/skip explicitly skipped as live-only and trades/canonical failures retained as RED evidence.

**2026-08-21 — slot 7 execution attempt (RED).** The generator re-measured four in-scope rows: `KALSHI` and `POLYMARKET`, each for `trades` and `book_snapshot_5`. The staging MTDS driver `pipeline-e2e-check-mtds-20260821-012839-18224b` completed at `2026-08-21T01:47:07Z` with 12 leg cells: 1 passed, 7 failed, and 4 skipped. `POLYMARKET/book_snapshot_5` canonical was the sole pass (`checked=7 canonical=7 raw=0`); both trades force/skip paths had zero parquet and no skip signal, both trades canonical checks had no matching rows, and `KALSHI/book_snapshot_5` canonical had no matching rows. The run also exposed the cross-venue sampler defect: `POLYMARKET/trades` was launched with `KALSHI:PREDICTION_MARKET:FEDHIKE-26DEC31`. The batch is therefore recorded as RED and the P0 contract is not claimed green. See [/plans/archive/issues/prediction_smoke_checker_cross_venue_sampling_2026_08_21.md](/plans/archive/issues/prediction_smoke_checker_cross_venue_sampling_2026_08_21.md).


**2026-08-21 — slot 7 rerun (RED).** The generator still measured four current rows (`KALSHI`/`POLYMARKET` × `trades`/`book_snapshot_5`). Driver `pipeline-e2e-check-mtds-20260821-013334-741403` reached terminal `exit_code=1` at `2026-08-21T01:53:34Z`: 8 leg cells, 1 passed, 3 failed, and 4 explicitly skipped. `POLYMARKET/trades` force proved one test parquet and a manifest atom (`197` rows, `manifest_status=empty_confirmed`), but its skip leg was `ambiguous` because the skip signal was absent and the object signature changed. Both `KALSHI/trades` legs failed `no_parquet_under` for auto-selected day `2026-08-07`; both `book_snapshot_5` legs were honestly skipped as `live_only_data_type`. This rerun sampled a venue-correct POLYMARKET path, so it does not reproduce the prior cross-venue sample, but the four-row P0 gate remains RED. Evidence: `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-21/data_pipeline_e2e_check_mtds_2026_08_21_prediction.json` and matching `.md` report.


**2026-08-21 — slot 14 implementation and evidence.** Shipped `market-tick-data-service@4d45e5541a`: Prediction listing prefixes now include the requested `venue=` atom, and the sampler rejects mismatched path venues or canonical prediction IDs. The focused regression covers the POLYMARKET/KALSHI collision. The available terminal four-row rerun remained RED for KALSHI trades/canonical and live-only book snapshots, but every row had a venue-scoped terminal result; no false cross-venue sample remained.

**2026-08-21 — slot 14 exact generator-scoped rerun (RED, terminal).** Driver `pipeline-e2e-check-mtds-20260821-prediction-4d45e5` enumerated exactly four rows (`KALSHI`/`POLYMARKET` × `trades`/`book_snapshot_5`) and completed at `2026-08-21T06:15:48Z` with `EXIT_STATUS=1`: 12 leg cells, 0 passed, 8 failed, 0 ambiguous, and 4 explicitly skipped. The durable report records venue-scoped test-bucket paths for every force/skip result, live-only skip classification for both book snapshots, genuine capture/canonical checks for each row, and no cross-venue sample. Evidence: `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_prediction.md`; MTDS quality gate passed (`11,117 passed, 28 skipped, 1 xpassed`).

**2026-08-21 — slot 21 negative-control verification (GREEN).** Verified all three mechanisms named in the P0 gate with a negative control: (1) **source-scoped exemptions** — `unified-api-contracts`'s `test_venue_smoke_test_work_list.py` already exhaustively covers this; the full Databento-exemption enumeration (`test_databento_exemptions_are_source_scoped`) is tradfi-only, proving zero Prediction rows are exempted. (2) **canonical checks** — MTDS's `test_pipeline_e2e_prediction_canonical.py` already carries an extensive prediction-specific negative-control suite (`_assert_prediction_ids_canonical`: lowercase/whitespace/empty/underlying-leakage violations, plus a vacuous-zero-rows-is-a-failure control, not a silent pass). (3) **manifest atom / missing-capture checks** — `_verify_batch_shard` (the shared force/skip-leg verifier) has no asset-group branch in its pass/fail logic (verified by reading it end to end), but every existing negative control for it (`TestBatchManifestNegativeControl`) only ever instantiated a CEFI shard — closed that gap by adding `TestPredictionBatchManifestNegativeControl`, proving the missing-capture (`no_parquet_under`) and missing-manifest-atom (`manifest_status_invalid`) failure paths apply identically to a PREDICTION shard, not just assumed from genericity. The Gate ("an invalid path or missing capture exits non-zero") is confirmed both by these unit-level negative controls and by the real live E2E run already on record above (driver `pipeline-e2e-check-mtds-20260821-prediction-4d45e5`, `EXIT_STATUS=1`, terminal, RED on genuine missing/non-canonical prediction data). Shipped `market-tick-data-service@e47d14527b`; full `quality-gates.sh` green (11,121 passed, 0 failed, 28 skipped, 1 xpassed). Also fixed a same-day, pre-existing, unrelated stale sports-venue-count pin (generator-scoped sports 39→33) discovered blocking this shipment's quality-gates.sh — left behind by `unified-api-contracts@710db834`'s removal of 6 unwired odds_api bookmakers (operator ruling, `/plans/active/issues/sports_bookmaker_roster_classification_2026_08_21.md`); the matching `_SPORTS_MVP_SHARDS` pin was independently fixed by a concurrent session and reconciled identically with no residual diff. Shipping hit the known `orphan_reap` false-kill bug (`/plans/active/issues/agent_orchestrator_quickmerge_orphan_reap_kills_interactive_background_2026_08_20.md`) 3 times before the documented env-stripped-nohup workaround landed it — no new finding, matches that doc's existing P1 follow-ups.

**2026-08-22 — slot 26 testnet verdict per Prediction venue.** `VENUE_TO_ASSET_GROUP["prediction"]` (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:658-662`) declares exactly two venues — POLYMARKET and KALSHI — matching this batch's own four-row (venue × data_type) work list exactly; no third venue exists to omit.

| Venue | Testnet? | Detail |
| --- | --- | --- |
| KALSHI | **HAS-TESTNET** (credential gap open) | UAC `SourceCapability` declares it explicitly: `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_sports.py:140-157` — `source="kalshi"`, `supports_testnet=True`, `base_urls={"mainnet": "https://api.elections.kalshi.com", "testnet": "https://demo-api.kalshi.co"}`. The execution adapter carries the same demo host as a named constant (`execution-service/execution_service/sports_execution/adapters/exchanges/kalshi.py:100`, `KALSHI_DEMO_BASE = "https://demo-api.kalshi.co"`, injectable via the adapter's `base_url=` constructor param). **Already live-probed** (`execution-service/tests/sports_execution/unit/test_kalshi_adapter.py:454-461`, 2026-08-09): the demo host is reachable and responds, but the REAL provisioned production secrets (`kalshi-api-key-id`/`kalshi-private-key-pem`) were rejected there with HTTP 401 — Kalshi's demo requires its own separately-provisioned demo account + API key, which does not exist and is not self-provisionable from this session. Per operator ruling 2026-08-06 (`kalshi_execution_credential_secret_name_mismatch_2026_07_26.md`), touching the real mainnet exchange is explicitly disallowed regardless, so demo is the only intended live-verification surface. The credential gap is exactly this plan's own next todo's scope (below), not a new finding. |
| POLYMARKET | **NO-TESTNET — matching-engine simulation is the honest answer** | UAC `SourceCapability` declares it the other way: `_sports.py:222-239` — `source="polymarket"`, `supports_testnet=False`, `base_urls={"mainnet": "https://clob.polymarket.com"}` (no `"testnet"` key at all). No testnet/sandbox/Mumbai/Amoy reference exists anywhere in the execution-service, instruments-service, or MTDS Polymarket code (grepped this session); Polymarket is a live on-chain CLOB on Polygon mainnet with no official public testnet. The honest fallback already exists in this exact adapter, not the shared CeFi/DeFi `MatchingEngineExecutionProvider`: `execution-service/execution_service/sports_execution/adapters/exchanges/polymarket_clob.py` implements `simulate_order_fill()` (a pure greedy price/quantity crossing match against a REAL captured or live `PolymarketOrderBook` snapshot — zero network calls, zero signing) plus `PolymarketCLOBAdapter.paper_place_order()`, which builds the identical payload `place_order()` would POST and returns the simulated fill under a synthetic `paper-<uuid>` order id. |

**2/2 declared Prediction venues have a written verdict**: 1 has a real testnet with an open credential-provisioning gap (KALSHI, scoped to the next todo below), 1 requires — and already has — matching-engine simulation (POLYMARKET). No registry gap to close: unlike CeFi's `bitfinex`/`okx_swap`/`coinbase_cde` (which needed a new `SourceCapability` P2 follow-up), both Prediction venues already carry complete, correct `supports_testnet` declarations in `_sports.py` — no equivalent follow-up todo is needed here.

**2026-08-22 — slot 1 tracking + expected_unattempted gate proof.** Every failed/absent Prediction row was already
tracked with its source and data_type by the shared `ShardCheckResult`/`PipelineCheckReport` infra (`source` +
`capture_status` fields, `shard_label` carrying venue/data_type, both rendered in the report's status table) — no new
tracking mechanism was needed. What was missing was a proof that the todo's Gate actually holds for PREDICTION: added
`TestPredictionBatchManifestNegativeControl.test_expected_unattempted_row_never_reported_as_captured_no_parquet` and
`..._with_parquet` (`market-tick-data-service@b7c523f16c`), mirroring the existing sibling negative controls in that
class. Both prove `_verify_batch_shard` returns `status="failed"` (never `"passed"`) with `capture_status="expected_unattempted"`
correctly tracked when the per-VM manifest atom is `expected_unattempted` — one variant with no parquet written, one
with a parquet object present but the manifest atom still `expected_unattempted` (the launder-via-parquet case). Full
`quality-gates.sh` passed on the shipped SHA.

**2026-08-22 — slot 18 credential request filed.** Todo 3's gate ("every attempted path has a measured terminal result") is satisfied by the prior entry's table: KALSHI's 401 live-probe (2026-08-09) and POLYMARKET's no-testnet/simulation answer are both terminal. The remaining action this todo names — "file an operator credential request when a credential gap is confirmed" — is now done: `BLK-3d8c3d9e` (`POST /api/slots/18/blocked` on this task) requests operator provisioning of a separate Kalshi demo account + API key (the production secrets are confirmed rejected by the demo host and Kalshi's demo cannot be self-provisioned from this session), and `/plans/active/issues/kalshi_demo_testnet_credential_request_2026_08_22.md` tracks the ask per `/codex/02-data/external-data-always-available-rule.md`'s `BLOCKED-CREDENTIALS` taxonomy. No code change — this todo's scope was recording + escalating, both of which are complete; a genuine KALSHI-demo-verified smoke test is a follow-up gated on the operator's [ack].
