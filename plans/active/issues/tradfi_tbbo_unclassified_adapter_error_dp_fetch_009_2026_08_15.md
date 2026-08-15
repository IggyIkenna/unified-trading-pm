---
doc_type: issue
title: TradFi tbbo/NYSE+NASDAQ — 1584 fresh attempted_failed(UNCLASSIFIED_ADAPTER_ERROR) rows, DP-FETCH-009 page, capability-gate bypass suspected
summary: >-
  DP-FETCH-009 escalation agt-9b0feb paged on asset_group=tradfi data_type=tbbo (1584 of 15249 attempted, 10.4%,
  "Fresh"). Live read of the tradfi `_index/availability_index.parquet` confirms this is NOT the already-registered
  billing-gated-by-design pattern (`known_dead_cells_registry.py` covers tradfi/mbp_10 and tradfi/ohlcv_15m only): all
  1584 rows carry `error_reason=UNCLASSIFIED_ADAPTER_ERROR` (a value the codebase itself documents as "any
  record_failed callsite producing this reason in production is a bug in the calling adapter" —
  `unified_api_contracts/canonical/crosscutting/honest_coverage.py`), venues NYSE (1164) + NASDAQ (420), all
  `attempted_at` between 2026-08-15T13:12Z and 14:29Z (today, ~77-minute window — a single fresh run, not a static
  backlog), shard dates 2024-07-01/07-02, `source=databento`, `pipeline_mode=batch_databento`, `instrument_id` shape
  `NASDAQ:EQUITY:ABNB-USD` etc.

  Critically, `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`'s
  `VENUE_DATA_TYPE_CAPABILITIES["NYSE"]` / `["NASDAQ"]` do NOT declare `tbbo` at all (only `ohlcv_1m`/`ohlcv_1s`/
  `ohlcv_1h`) — the same structural gate the sibling issue doc
  `tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md` describes for CME (`get_expected_data_types_for_venue`
  intersects every fetch request against this list; `venue_fetch.py` never lets an undeclared data_type reach the
  Databento fetch call). If that gate is honored, tbbo for NYSE/NASDAQ should be UNREACHABLE by the normal orchestrator
  path — yet 1584 real fetch attempts happened today. This strongly suggests a bypass path (a manual/scratch
  script or a non-standard entrypoint) drove this backfill outside `venue_fetch.py`'s capability gate AND outside
  `sentinels.py`'s `classify_venue_error()` pipeline (which is why the error_reason is the generic
  UNCLASSIFIED_ADAPTER_ERROR fallback rather than a classified Databento code).

  Also matches the pre-existing operator ruling in `tradfi_massive_dual_source_2026_05_28.md` (archived): "Equity/ETF
  tick-level trades+tbbo — OPERATOR DECISION RESOLVED: NOT needed for TradFi MVP (connector must still implement)" —
  so this backfill activity is likely out-of-scope work regardless of the classification bug.

  A genuinely separate, smaller bug was also found and left unfixed here pending confirmation it's worth a scoped
  patch: `unified_api_contracts/canonical/crosscutting/errors/tradfi.py`'s `VENUE_ERRORS_TRADFI["databento"]` entries
  (DATABENTO_SUBSCRIPTION_GUARD / DATABENTO_LOOKBACK_EXCEEDED / etc.) are keyed by the PROVIDER string `"databento"`,
  but `engine/orchestrator/sentinels.py`'s Tier-2/Tier-3 emitters call `classify_venue_error(venue, code_token)` with
  the MARKET venue (`"NYSE"`, `"CME"`, etc.) as the first arg, not `"databento"` — so for ANY tradfi Databento venue,
  a genuine DATABENTO_* code always misses `VENUE_ERROR_MAP[venue.lower()]` and the venue-agnostic `internal` fallback
  bucket (which also has no DATABENTO_* entries), producing `classify_venue_error()->None` and a degraded
  `f"UNCLASSIFIED:{code_token}"` string (per `sentinels.py:672` Tier-3) rather than the intended classified code. This
  does NOT by itself explain the literal `UNCLASSIFIED_ADAPTER_ERROR` string in the alert (that string never appears
  live in `market-tick-data-service`'s `engine/orchestrator/`, `market_interface/adapters/tradfi/`, or
  `unified-trading-library`'s `manifest_writer/*` per an exhaustive grep + a dedicated Explore-agent trace — it only
  appears in two cefi-scoped one-off migration scripts, `_rebuild_cefi_cf11.py` and `canonicalize_mtds_index.py`,
  neither of which should ever touch the tradfi bucket), but it is a real, confirmed, separate classification-quality
  gap worth closing.
status: open
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags: [tradfi, tbbo, dp-fetch-009, unclassified-adapter-error, capability-gate, classify-venue-error, databento, honest-absence]
related:
  [
    /plans/active/issues/tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-08-15
author: agt-9b0feb (data_pipeline_failure escalation worker, slot-33)
source: ["DP-FETCH-009 escalation agt-9b0feb, asset_group=tradfi data_type=tbbo, 1584/15249 attempted_failed (10.4%)"]
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.48
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
last_updated: 2026-08-15
parent_epic: tradfi_master
priority: P1
---

# TradFi tbbo/NYSE+NASDAQ — fresh UNCLASSIFIED_ADAPTER_ERROR batch, DP-FETCH-009

## What I found

Live-verified via `deployment_service.data_pipeline_monitors.meta_targets.market_data_bucket("tradfi")`'s
`_index/availability_index.parquet` (GCS-streamed, column-projected, bounded via
`run-bounded-analysis.sh` — no ad-hoc full-corpus load):

- 1584 rows: `data_type=tbbo`, `capture_status=attempted_failed`, `error_reason=UNCLASSIFIED_ADAPTER_ERROR` (100% —
  zero other error_reason values in this set).
- `venue`: NYSE=1164, NASDAQ=420.
- `attempted_at`: min `2026-08-15T13:12:26.667735+00:00`, max `2026-08-15T14:29:16.804203+00:00` — a single ~77-minute
  run TODAY, not an aged static backlog (rules out the "just re-page the same old 14d-window backlog" pattern the
  cefi `(cefi, book_snapshot_5)` DP-FETCH-009 history in `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`
  repeatedly hit).
- `date` (shard date, i.e. what day's tick data was requested): 2024-07-01 / 2024-07-02 only — a narrow 2-day window
  backfill, not a broad multi-year sweep.
- `source=databento`, `pipeline_mode=batch_databento`.
- `instrument_id` sample: `NASDAQ:EQUITY:ABNB-USD`, `NASDAQ:EQUITY:CME-USD`, `NASDAQ:EQUITY:QQQ-USD`,
  `NASDAQ:EQUITY:SPY-USD`, `NASDAQ:EQUITY:COIN-USD`, etc. — real, plausible equity tickers, not garbage/test data.

## Why this is NOT the known billing-gated-by-design pattern

`deployment-service/deployment_service/data_pipeline_monitors/known_dead_cells_registry.py`'s `KNOWN_DEAD_CELLS`
already suppresses `("tradfi", "mbp_10")` (CME, 2026-07-15 operator decision) and `("tradfi", "ohlcv_15m")` — both
because their `attempted_failed` population is a frozen, non-growing historical residue with a documented root cause.
This tbbo batch is the OPPOSITE shape: 100% fresh (all rows within one run today), and the error_reason
(`UNCLASSIFIED_ADAPTER_ERROR`) is not one of the expected billing-guard codes
(`DATABENTO_SUBSCRIPTION_GUARD`/`DATABENTO_LOOKBACK_EXCEEDED`/`DATABENTO_PAYMENT_REQUIRED`) that
`market_tick_data_service/market_interface/adapters/tradfi/databento_adapter.py::_classify_databento_exception`
would produce for an entitlement rejection. Registering `("tradfi", "tbbo")` in `KNOWN_DEAD_CELLS` to silence the page
would be masking a genuinely fresh, unclassified failure — explicitly banned
(`unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` "never write an empty/placeholder... never mask a
real failure"). I did not do this.

## The capability-gate contradiction (the strongest lead)

`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`:

```python
"NASDAQ": {
    "ohlcv_1m": "2023-04-15",
    "ohlcv_1s": "2023-04-15",
    "ohlcv_1h": "2026-01-01",
},
"NYSE": {
    "ohlcv_1m": "2023-04-15",
    "ohlcv_1s": "2023-04-15",
    "ohlcv_1h": "2026-01-01",
},
```

`tbbo` is absent from both. Per the sibling issue doc
`tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md`'s verified finding for CME,
`get_expected_data_types_for_venue(venue)` reads `VENUE_DATA_TYPE_CAPABILITIES.get(venue).data_types` directly, and
`venue_fetch.py`'s per-shard dispatch intersects every fetch request against that list — so tbbo for NYSE/NASDAQ
should be structurally unreachable through the normal orchestrator dispatch path, exactly like CME's
trades/tbbo/mbp_10. This matches the archived operator ruling in `tradfi_massive_dual_source_2026_05_28.md`:
"Equity/ETF tick-level `trades`+`tbbo` — OPERATOR DECISION RESOLVED: NOT needed for TradFi MVP (connector must still
implement)".

Yet 1584 real Databento fetch attempts for exactly this (asset_group, data_type, venue) combination happened today.
**I was not able to identify, within this one-shot escalation's budget, which code path issued these fetches** — I
grepped + dispatched a dedicated Explore agent across `market_tick_data_service/engine/orchestrator/` (including both
`sentinels.py` Tier-2 AND Tier-3 emitters), `market_interface/adapters/tradfi/databento_*.py`,
`engine/orchestrator/known_dead_shard_gate.py`, and `unified-trading-library`'s `manifest_writer/*` +
`legacy_reason_classifier.py`, and could not find a live call site that both (a) writes the literal string
`UNCLASSIFIED_ADAPTER_ERROR` and (b) would fire for a per-instrument NYSE/NASDAQ tbbo shard. The literal string exists
in this codebase ONLY inside two `Lifecycle: oneoff` cefi-scoped migration scripts
(`market_tick_data_service/scripts/_rebuild_cefi_cf11.py`, `market_tick_data_service/scripts/canonicalize_mtds_index.py`)
— neither should ever run against the tradfi bucket, and their transform preserves `attempted_at` (so if either had
run against tradfi it should NOT produce today's fresh timestamps unless the underlying rows were also fresh today
from a genuinely separate write, which loops back to the same open question).

**Leading hypothesis**: a manual/scratch script or a non-standard entrypoint (not `venue_fetch.py`'s normal gated
dispatch, not `sentinels.py`'s Tier-2/3 `classify_venue_error()` pipeline) directly drove a Databento tbbo backfill
for these two venues today, with its own naive `except Exception: record_failed(error="UNCLASSIFIED_ADAPTER_ERROR")`
(or equivalent) — consistent with both the capability-gate bypass AND the non-classified error string. This is
plausible manual "let's see if equity tbbo actually works now" exploration ahead of formally re-scoping the MVP.

## A separate, confirmed, smaller bug (found along the way, NOT the direct cause of this alert)

`unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/tradfi.py`'s `VENUE_ERRORS_TRADFI` dict
keys its Databento-specific classifications (`DATABENTO_SUBSCRIPTION_GUARD`, `DATABENTO_LOOKBACK_EXCEEDED`,
`DATABENTO_PAYMENT_REQUIRED`, `DATABENTO_ENTITLEMENT`, plus generic `RATE_LIMIT`/`AUTH_FAILURE`/`SERVER_ERROR`/etc.)
under the literal provider key `"databento"` — matching the convention `databento_symbology.py:120` uses
(`classify_venue_error("databento", "TimeoutError")`). But `market_tick_data_service/engine/orchestrator/sentinels.py`
Tier-2 (`~line 604`) and Tier-3 (`~line 638`) both call `classify_venue_error(venue, code_token)` with the MARKET
venue (`"NYSE"`/`"CME"`/etc.), not `"databento"`. Since `classify_venue_error()`
(`unified_api_contracts/canonical/crosscutting/errors/__init__.py:51`) only checks `VENUE_ERROR_MAP[venue.lower()]`
then the venue-agnostic `internal` bucket, and NEITHER has NYSE/NASDAQ/CME-keyed entries for the Databento codes, any
genuinely-classified Databento failure reaching this path for a tradfi venue silently degrades to
`f"UNCLASSIFIED:{code_token}"` (Tier-3) or the raw `code_token` (Tier-2) instead of the intended classified reason.
This is real and worth fixing but is NOT itself sufficient to produce the exact literal `UNCLASSIFIED_ADAPTER_ERROR`
observed in the alert (it would produce `UNCLASSIFIED:DATABENTO_SUBSCRIPTION_GUARD` etc., a different string) — so I
left it unfixed here pending the root-cause trace below, to avoid shipping a change I can't tie to the actual symptom.

## Why it matters

- **Billing/API-call waste**: 1584 real Databento API calls for structurally out-of-scope (not-yet-MVP) equity tbbo
  data, if the capability gate really is being bypassed.
- **Alert noise**: DP-FETCH-009 will keep re-paging (30-min re-nag cooldown) until this cell either goes quiet or gets
  a deliberate disposition — and it must NOT be silenced via `KNOWN_DEAD_CELLS` without first confirming it's
  genuinely the by-design billing-gated pattern (it currently is not).
- **A capability-gate bypass, if confirmed, is a data-pipeline-correctness HARD RULE concern** (CLAUDE.md "Data
  pipeline correctness is the heartbeat") — any code path that can write `attempted_failed` rows for a data_type the
  registry says is out of scope, without going through the same `classify_venue_error()` contract every other adapter
  path uses, is a latent honest-absence/classification-integrity gap that could recur for other venues/data_types.

## Open work (tracked todos)

- [ ] [SCRIPT] P1. Identify the exact code path (script/CLI/handler) that issued the 1584 tbbo/NYSE+NASDAQ Databento
      fetch attempts on 2026-08-15 13:12-14:29 UTC for shard dates 2024-07-01/07-02 — check GCP Cloud Run/VM launch
      history + any interactive/manual invocation in that window, and grep `market-tick-data-service` +
      `deployment-service` for any tbbo/equity backfill entrypoint that does NOT route through
      `venue_fetch.py`'s `get_expected_data_types_for_venue` capability gate. (repos: market-tick-data-service,
      deployment-service)
- [ ] [SCRIPT] P1. Once the call site is found, route it through `classify_venue_error()` per the standard
      `record_failed` contract instead of a generic except-Exception fallback, and confirm it either honors
      `VENUE_DATA_TYPE_CAPABILITIES` (blocking tbbo for NYSE/NASDAQ, matching current MVP scope) or — if the operator
      has decided equity tbbo IS now in scope — file the corresponding registry + capability update as its own
      tracked change (not silently expanded via a bypass path). (repos: market-tick-data-service, unified-api-contracts)
- [ ] [SCRIPT] P2. Fix the `classify_venue_error(venue, code)` provider-vs-market-venue key mismatch for TradFi
      Databento venues: either alias `VENUE_ERRORS_TRADFI["databento"]`'s DATABENTO_* + generic HTTP-code entries
      under every Databento-backed tradfi market venue key, or change `sentinels.py`'s Tier-2/Tier-3 call sites to
      pass the actual data-provider key (`"databento"`) when the failure originated from a Databento adapter (needs a
      provider tag threaded through `failed_shards`/`failed_per_dt_by_venue`, since sentinels.py doesn't currently
      know which provider handled a given failed shard). (repos: unified-api-contracts, market-tick-data-service)
- [ ] [DESIGN] P2. Once the above is resolved, decide whether `("tradfi", "tbbo")` needs a `KNOWN_DEAD_CELLS`
      registry entry — only if the disposition is "structurally out of scope, expected to keep failing" (mirroring
      `("tradfi", "mbp_10")`); NOT if the bypass gets fixed and tbbo simply stops being attempted. (repos:
      deployment-service)
